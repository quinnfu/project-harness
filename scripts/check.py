#!/usr/bin/env python3
"""project-harness check: fast, computational harness checks (stdlib only).

Usage:
  python harness/check.py --staged        # pre-commit
  python harness/check.py --all [--json]  # full audit
Check IDs are documented in the project-harness skill: references/checks.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote

VERSION = "1.0.0"
PROFILE = "harness/profile.md"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target", "vendor"}
AGENTS_WARN_LINES = 200
AGENTS_WARN_BYTES = 16 * 1024
AGENTS_MAX_BYTES = 32 * 1024
STALE_DAYS = 14
NA_VALUES = {"", "—", "-", "–", "不适用", "无", "n/a", "na", "none", "not applicable"}
DOC_SUFFIXES = {".md", ".mdx", ".rst", ".adoc"}
DEFAULT_NEUTRAL_TERMS = [
    "Claude", "GPT", "Gemini", "Opus", "Sonnet", "Haiku", "Copilot", "Codex", "Llama", "Qwen", "DeepSeek",
    "str_replace_editor", "apply_patch", "run_in_terminal", "replace_string_in_file",
]
BUILD_FILES = {
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "makefile", "justfile", "cargo.toml", "go.mod",
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "pnpm-workspace.yaml", "dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", "tox.ini", "noxfile.py",
}
VENDOR_PATHS = [
    ".github/copilot-instructions.md", ".github/instructions", "CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md",
    "GEMINI.md", ".cursorrules", ".cursor/rules", ".windsurfrules", ".vscode/mcp.json", ".hermes.md", "HERMES.md",
]
PLAN_SECTIONS = [("Goal", "goal", "目标"), ("Progress", "progress", "进度"), ("Decisions", "decision", "决策"),
                 ("Next steps", "next", "下一步")]


# ---------- helpers ----------

class Finding(dict):
    def __init__(self, cid, level, msg, file=None, line=None, fix=None):
        super().__init__(id=cid, level=level, msg=msg, file=file, line=line, fix=fix)


def git(root, *args):
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace")


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def rel(root, path):
    try:
        return Path(os.path.relpath(path, root)).as_posix()
    except ValueError:
        return Path(path).as_posix()


def skipped(relpath):
    return any(part in SKIP_DIRS for part in relpath.split("/"))


def iter_lines(text):
    """Yield (lineno, line) for lines outside fenced code blocks."""
    fence = None
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            mark = m.group(1)[0]
            if fence is None:
                fence = mark
                continue
            if fence == mark:
                fence = None
                continue
        if fence is None:
            yield i, line


def slugify(text):
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def heading_texts(text):
    out = []
    for _, line in iter_lines(text):
        m = re.match(r"^ {0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            out.append(m.group(1))
    return out


def anchors_of(text):
    seen, out = {}, set()
    for h in heading_texts(text):
        s = slugify(h)
        n = seen.get(s, 0)
        out.add(s if n == 0 else f"{s}-{n}")
        seen[s] = n + 1
    return out


INLINE_LINK = re.compile(r"\[(?:[^\]\\]|\\.)*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)")
REF_DEF = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


def links_of(text):
    """Yield (lineno, target) for markdown links outside code."""
    for no, line in iter_lines(text):
        line = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)
        for m in INLINE_LINK.finditer(line):
            yield no, m.group(1).strip("<>")
        m = REF_DEF.match(line)
        if m:
            yield no, m.group(1).strip("<>")


def resolve_link(root, src, target):
    """Return (abs_path or None, anchor) for a local link; None path means same file. Returns False for external."""
    if not target or SCHEME.match(target):
        return False
    path, _, anchor = target.partition("#")
    path = unquote(path.split("?", 1)[0])
    if not path:
        return None, unquote(anchor)
    base = Path(root) if path.startswith("/") else Path(src).parent
    return Path(os.path.normpath(base / path.lstrip("/"))), unquote(anchor)


def anchor_ok(text, anchor):
    if not anchor or re.fullmatch(r"L\d+(-L\d+)?", anchor):
        return True
    anchors = anchors_of(text)
    return anchor.lower() in anchors or slugify(anchor) in anchors


# ---------- profile ----------

def parse_table(lines):
    rows, started = [], False
    for line in lines:
        s = line.strip()
        if s.startswith("|"):
            started = True
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", s.strip("|"))]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
        elif started:
            break
    return rows[1:] if rows else []


def clean_cell(cell):
    cell = cell.strip().strip("`").strip()
    m = re.fullmatch(r"\[[^\]]*\]\(([^)]*)\)", cell)
    return m.group(1).strip() if m else cell


def parse_profile(text):
    sections, current = {"": []}, ""
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            current = m.group(1).strip().lower()
            sections[current] = []
        else:
            sections[current].append(line)

    def section(*names):
        for k, v in sections.items():
            if any(n in k for n in names):
                return v
        return []

    meta = {r[0].strip().lower(): r[1].strip() for r in parse_table(sections[""]) if len(r) >= 2}

    def meta_get(*keys):
        for k in keys:
            if meta.get(k):
                return meta[k]
        return None

    roles = [(r[0], clean_cell(r[1])) for r in parse_table(section("role", "角色映射")) if len(r) >= 2 and r[0]]
    exempt = set()
    for r in parse_table(section("exemption", "豁免")):
        if r and r[0]:
            exempt.update(x.strip().upper() for x in re.split(r"[,，、\s]+", r[0]) if x.strip())
    extra, allow = [], []
    for r in parse_table(section("neutral", "中立词表")):
        if len(r) >= 2:
            words = [w.strip() for w in re.split(r"[,，、]", r[1]) if w.strip()]
            kind = r[0].strip().lower()
            if kind in ("extra", "add", "额外"):
                extra += words
            elif kind in ("allow", "允许"):
                allow += words
    level_raw = meta_get("level", "级别") or "L1"
    m = re.search(r"\d", level_raw)
    return {
        "standard": meta_get("standard version", "standard", "标准版本"),
        "level": int(m.group(0)) if m else 1,
        "check_version": meta_get("check version", "check", "check 版本"),
        "roles": roles,
        "exempt": exempt,
        "extra_terms": extra,
        "allow_terms": allow,
    }


# ---------- checker ----------

class Checker:
    def __init__(self, root, staged):
        self.root = Path(root).resolve()
        self.staged = staged
        self.findings = []
        self.profile = None
        self._md_cache = None

    def add(self, *a, **k):
        self.findings.append(Finding(*a, **k))

    def p(self, relpath):
        return self.root / relpath

    def all_md(self):
        if self._md_cache is None:
            out = git(self.root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
            if out is not None:
                files = [f for f in out.split("\0") if f]
            else:
                files = []
                for d, dirs, names in os.walk(self.root):
                    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
                    files += [rel(self.root, Path(d) / n) for n in names]
            self._md_cache = sorted({f for f in files if f.lower().endswith(".md") and not skipped(f)
                                     and self.p(f).is_file()})
        return self._md_cache

    def staged_changes(self):
        out = git(self.root, "diff", "--cached", "--name-status", "-M", "-z")
        if out is None:
            return []
        parts, changes, i = out.split("\0"), [], 0
        while i < len(parts) and parts[i]:
            status = parts[i][0]
            if status in "RC":
                changes.append((status, parts[i + 1], parts[i + 2]))
                i += 3
            else:
                changes.append((status, parts[i + 1], parts[i + 1]))
                i += 2
        return changes

    # --- P ---
    def check_profile(self):
        text = read(self.p(PROFILE))
        if text is None:
            self.add("P1", "ERROR", f"missing {PROFILE}", PROFILE,
                     fix="run the project-harness skill (setup mode), or copy its assets/profile.md and fill it in")
            return
        self.profile = parse_profile(text)
        if not self.profile["standard"]:
            self.add("P1", "ERROR", "cannot parse 'Standard version' from the profile", PROFILE,
                     fix="add a row to the first table: | Standard version | 1 |")
        for role, loc in self.profile["roles"]:
            if loc.strip().lower() in NA_VALUES or SCHEME.match(loc):
                continue
            path, _, anchor = loc.partition("#")
            target = self.p(path.strip("/"))
            if not target.exists() or (path.endswith("/") and not target.is_dir()):
                self.add("P2", "ERROR", f"location mapped for role '{role}' does not exist: {loc}", PROFILE,
                         fix="fix the profile's role map or add content at that location; write '—' for unneeded roles")
            elif anchor and target.is_file() and not anchor_ok(read(target) or "", anchor):
                self.add("P2", "ERROR", f"heading mapped for role '{role}' does not exist: {loc}", PROFILE,
                         fix=f"add the heading to {path}, or fix the #anchor in the mapping")
        if not self.staged and self.profile["check_version"] and self.profile["check_version"] != VERSION:
            self.add("P3", "WARN", f"profile check version {self.profile['check_version']} differs from script {VERSION}",
                     PROFILE, fix="update 'Check version' in the profile, or upgrade the script via project-harness upgrade mode")

    # --- E ---
    def check_entry(self, changes):
        agents = self.p("AGENTS.md")
        text = read(agents)
        if text is None:
            self.add("E1", "ERROR", "missing AGENTS.md at the repository root", "AGENTS.md",
                     fix="run the project-harness skill (setup mode), or draft one from its assets/AGENTS.md")
        if self.staged:
            targets = {"AGENTS.md"} | {n for s, _, n in changes if s != "D" and Path(n).name == "AGENTS.md"}
        else:
            targets = {f for f in self.all_md() if Path(f).name == "AGENTS.md"}
        for f in sorted(targets):
            t = read(self.p(f))
            if t is None:
                continue
            size, lines = len(t.encode("utf-8")), t.count("\n") + 1
            if size > AGENTS_MAX_BYTES:
                self.add("E2", "ERROR", f"{f} is {size} bytes, over {AGENTS_MAX_BYTES} (some agents truncate it)", f,
                         fix="move details into docs listed in the doc map; keep only routing and key rules in AGENTS.md")
            elif lines > AGENTS_WARN_LINES or size > AGENTS_WARN_BYTES:
                self.add("E2", "WARN", f"{f} has {lines} lines / {size} bytes, over the recommended size "
                                       f"({AGENTS_WARN_LINES} lines / 16 KB)", f,
                         fix="AGENTS.md is loaded on every turn; push details down into linked docs")
        if text is None:
            return
        heads = [h.strip().lower() for h in heading_texts(text)]
        if not any("完成定义" in h or "definition of done" in h or h == "done" for h in heads):
            self.add("E3", "ERROR", "AGENTS.md has no 'Definition of done' section", "AGENTS.md",
                     fix="add '## Definition of done': what counts as done and how to verify (standard conventions in one line)")
        if not any("文档地图" in h or "doc map" in h or "documentation map" in h or "docs map" in h
                   or h in ("map", "docs", "documentation") for h in heads):
            self.add("E3", "ERROR", "AGENTS.md has no 'Doc map' section", "AGENTS.md",
                     fix="add '## Doc map' linking to every location in the profile's role map")
        if self.profile:
            linked = set()
            for _, tgt in links_of(text):
                r = resolve_link(self.root, agents, tgt)
                if r and r[0] is not None:
                    linked.add(rel(self.root, r[0]).rstrip("/").lower())
            for role, loc in self.profile["roles"]:
                path = loc.partition("#")[0].strip("/")
                if loc.strip().lower() in NA_VALUES or SCHEME.match(loc) or path.lower() == "agents.md":
                    continue
                if path.lower() not in linked:
                    self.add("E4", "WARN", f"role '{role}' ({loc}) is not linked from AGENTS.md", "AGENTS.md",
                             fix=f"add a link to {loc} in the 'Doc map' section")

    # --- L1 ---
    def check_links_in(self, f, only_targets=None):
        src = self.p(f)
        text = read(src)
        if text is None:
            return
        for no, tgt in links_of(text):
            r = resolve_link(self.root, src, tgt)
            if r is False:
                continue
            path, anchor = r
            if path is None:
                if not anchor_ok(text, anchor):
                    self.add("L1", "ERROR", f"anchor not found in this file: #{anchor}", f, no,
                             fix="fix the anchor or add the heading")
                continue
            rp = rel(self.root, path)
            if only_targets is not None:
                if rp in only_targets:
                    new = only_targets[rp]
                    hint = (f"the file was renamed to {new}; change the link to "
                            f"{Path(os.path.relpath(self.p(new), src.parent)).as_posix()}") if new \
                        else "the file was deleted; remove or replace the link"
                    self.add("L1", "ERROR", f"link points to a file deleted/renamed in this commit: {tgt}", f, no,
                             fix=hint)
                continue
            if not path.exists():
                self.add("L1", "ERROR", f"link target does not exist: {tgt}", f, no,
                         fix="fix the path or remove the dead link")
            elif anchor and path.is_file() and path.suffix.lower() == ".md" and not anchor_ok(read(path) or "", anchor):
                self.add("L1", "ERROR", f"heading anchor not found: {tgt}", f, no,
                         fix=f"check the headings in {rp} and fix the #anchor")

    def check_links(self, changes):
        if not self.staged:
            for f in self.all_md():
                self.check_links_in(f)
            return
        checked = set()
        for s, _, new in changes:
            if s != "D" and new.lower().endswith(".md") and self.p(new).is_file():
                self.check_links_in(new)
                checked.add(new)
        gone = {old: (new if s == "R" else None) for s, old, new in changes if s in "DR"}
        gone = {k: v for k, v in gone.items() if not self.p(k).exists()}
        if gone:
            for f in self.all_md():
                if f not in checked:
                    self.check_links_in(f, only_targets=gone)

    # --- N1 ---
    def check_neutral(self, changes):
        terms = list(DEFAULT_NEUTRAL_TERMS)
        allow = set()
        if self.profile:
            terms += self.profile["extra_terms"]
            allow = {a.lower() for a in self.profile["allow_terms"]}
        terms = [t for t in terms if t.lower() not in allow]
        if not terms:
            return
        pattern = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(t) for t in terms) + r")(?![A-Za-z_])",
                             re.IGNORECASE)

        def is_instruction(f):
            return Path(f).name == "AGENTS.md" or (f.startswith(".agents/skills/") and Path(f).name == "SKILL.md")

        files = ([n for s, _, n in changes if s != "D" and is_instruction(n)] if self.staged
                 else [f for f in self.all_md() if is_instruction(f)])
        for f in files:
            text = read(self.p(f))
            if text is None:
                continue
            for no, line in enumerate(text.splitlines(), 1):
                m = pattern.search(line)
                if m:
                    self.add("N1", "WARN", f"model or tool-specific name in instructions: {m.group(1)}", f, no,
                             fix="describe the intended outcome without naming a model/tool; if truly needed, "
                                 "add it to 'Allow' in the profile's neutral terms")

    # --- D1 ---
    def check_drift(self, changes):
        if not self.staged or not changes:
            return
        head = git(self.root, "ls-tree", "--name-only", "-z", "HEAD")
        if head is None:
            return
        head_tops = {x for x in head.split("\0") if x}
        reasons, doc_touched = [], False
        for s, old, new in changes:
            for path, st in ((old, "D" if s == "R" else s), (new, "A" if s == "R" else s)):
                if Path(path).suffix.lower() in DOC_SUFFIXES:
                    doc_touched = True
                top = path.split("/")[0]
                if "/" in path:
                    if st in "AC" and top not in head_tops:
                        reasons.append(f"new top-level directory {top}/")
                    elif st == "D" and top in head_tops and not self.p(top).exists():
                        reasons.append(f"removed top-level directory {top}/")
                name = Path(path).name.lower()
                if (name in BUILD_FILES or name.startswith("dockerfile") or path.startswith(".github/workflows/")
                        or name.endswith((".csproj", ".sln"))):
                    reasons.append(f"changed build/CI file {path}")
        reasons = list(dict.fromkeys(reasons))
        if reasons and not doc_touched:
            self.add("D1", "WARN", "structure may have changed but no doc was touched in this commit: "
                     + "; ".join(reasons[:5]),
                     fix="check whether the architecture doc or AGENTS.md (Definition of done / Setup) needs updating; "
                         "ignore if not")

    # --- X1 ---
    def check_vendor(self):
        if self.staged:
            return
        for v in VENDOR_PATHS:
            if self.p(v).exists():
                self.add("X1", "WARN", f"vendor-specific agent config found: {v}", v,
                         fix="move generic content into AGENTS.md or other open-standard locations (see the "
                             "portability-config skill); if it must stay, exempt X1 in the profile")

    # --- S1 ---
    def check_plans(self):
        if self.staged or not self.profile or self.profile["level"] < 2:
            return
        for role, loc in self.profile["roles"]:
            if not ("计划" in role or "plan" in role.lower()):
                continue
            if loc.strip().lower() in NA_VALUES or SCHEME.match(loc):
                continue
            base = self.p(loc.partition("#")[0].strip("/"))
            if base.is_file():
                files = [base]
            elif base.is_dir():
                active = base / "active"
                files = sorted((active if active.is_dir() else base).rglob("*.md"))
                files = [f for f in files if f.name.lower() not in ("readme.md", "index.md")]
            else:
                continue
            for f in files:
                rf = rel(self.root, f)
                heads = [h.lower() for h in heading_texts(read(f) or "")]
                missing = [name for name, en, zh in PLAN_SECTIONS if not any(en in h or zh in h for h in heads)]
                if missing:
                    self.add("S1", "WARN", f"plan is missing sections: {', '.join(missing)}", rf,
                             fix="a plan needs at least Goal / Progress / Decisions / Next steps; "
                                 "mark progress items as done or verified")
                ts = git(self.root, "log", "-1", "--format=%ct", "--", rf)
                if ts and ts.strip().isdigit() and time.time() - int(ts.strip()) > STALE_DAYS * 86400:
                    self.add("S1", "WARN", f"active plan not updated for over {STALE_DAYS} days", rf,
                             fix="update progress; move finished or abandoned plans to done/")

    def run(self):
        changes = self.staged_changes() if self.staged else []
        self.check_profile()
        self.check_entry(changes)
        self.check_links(changes)
        self.check_neutral(changes)
        self.check_drift(changes)
        self.check_vendor()
        self.check_plans()
        exempt = self.profile["exempt"] if self.profile else set()
        kept = [f for f in self.findings if f["id"] not in exempt]
        return kept, len(self.findings) - len(kept)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="project-harness computational checks")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="only checks relevant to staged changes (pre-commit)")
    mode.add_argument("--all", action="store_true", help="full audit (default)")
    ap.add_argument("--root", help="repository root (default: git top-level or cwd)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--version", action="version", version=VERSION)
    args = ap.parse_args(argv)

    root = args.root
    if not root:
        top = git(os.getcwd(), "rev-parse", "--show-toplevel")
        root = top.strip() if top else os.getcwd()
    findings, exempted = Checker(root, args.staged).run()
    errors = sum(f["level"] == "ERROR" for f in findings)
    warns = len(findings) - errors
    mode_name = "staged" if args.staged else "all"

    if args.json:
        print(json.dumps({"version": VERSION, "mode": mode_name, "root": str(Path(root).resolve()), "errors": errors,
                          "warnings": warns, "exempted": exempted, "findings": findings}, ensure_ascii=False, indent=2))
    else:
        for f in sorted(findings, key=lambda x: (x["level"] != "ERROR", x["id"], x["file"] or "", x["line"] or 0)):
            loc = f["file"] or ""
            if f["line"]:
                loc += f":{f['line']}"
            print(f"[{f['level']}] {f['id']} {loc + ' ' if loc else ''}{f['msg']}")
            if f["fix"]:
                print(f"        fix: {f['fix']}")
        summary = f"harness check v{VERSION} ({mode_name}): {errors} error, {warns} warning"
        if exempted:
            summary += f", {exempted} exempted"
        if errors and args.staged:
            summary += " -> commit blocked"
        print(summary)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
