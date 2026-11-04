"""Scenario tests for project-harness check.py (run from skill root: python tests/run_tests.py).

The GOOD_* fixtures are deliberately in Chinese to cover the parser's Chinese-key compatibility;
t_templates_pass covers the shipped English templates.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE.parent / "scripts" / "check.py"
ASSETS = HERE.parent / "assets"
PY = sys.executable
failures = []


def sh(root, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root,
                          capture_output=True, text=True, encoding="utf-8")


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run(root, *flags):
    r = subprocess.run([PY, str(CHECK), "--json", *flags], cwd=root, capture_output=True, text=True, encoding="utf-8")
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise AssertionError(f"bad output rc={r.returncode}\nstdout={r.stdout}\nstderr={r.stderr}")
    return r.returncode, data


def ids(data, level=None):
    return sorted({f["id"] for f in data["findings"] if level is None or f["level"] == level})


def expect(name, cond, data=None):
    if cond:
        print(f"PASS {name}")
    else:
        failures.append(name)
        print(f"FAIL {name}")
        if data is not None:
            print(json.dumps(data["findings"], ensure_ascii=False, indent=1))


GOOD_AGENTS = """# Demo

示例项目。

## 规则
- 改动影响结构时同步更新文档。

## 完成定义
- 测试通过（pytest）。

## 文档地图
- 架构：[ARCHITECTURE.md](ARCHITECTURE.md)
- 需求：[docs/product/](docs/product/)
- 概述：[README 的架构节](README.md#架构-概览)
- Harness：[harness/profile.md](harness/profile.md)
"""

GOOD_PROFILE = """# Harness Profile

| 项 | 值 |
|---|---|
| 标准版本 | 1 |
| 级别 | L1 |
| check 版本 | 1.0.0 |

## 角色映射

| 角色 | 位置 | 备注 |
|---|---|---|
| 入口 | AGENTS.md | |
| 架构 | `ARCHITECTURE.md` | |
| 需求 | docs/product/ | |
| 概览 | README.md#架构 概览 | |
| 计划 | — | |

## 豁免

| 检查 | 原因 |
|---|---|

## 中立词表

| 类型 | 词 |
|---|---|
| 额外 | |
| 允许 | |
"""


def make_good(root):
    sh(root, "init", "-q")
    write(root, "AGENTS.md", GOOD_AGENTS)
    write(root, "harness/profile.md", GOOD_PROFILE)
    write(root, "ARCHITECTURE.md", "# 架构\n\n见 [需求](docs/product/login.md#登录-流程)。\n")
    write(root, "README.md", "# Demo\n\n## 架构 概览\n\n文字\n")
    write(root, "docs/product/login.md", "# 登录\n\n## 登录 流程\n\n```md\n[忽略](not-exist.md)\n```\n")
    write(root, "src/app.py", "print('hi')\n")
    sh(root, "add", "-A")
    sh(root, "commit", "-q", "-m", "init")


def case(fn):
    d = tempfile.mkdtemp(prefix="harness-test-")
    try:
        fn(d)
    except AssertionError as e:
        failures.append(fn.__name__)
        print(f"FAIL {fn.__name__}: {e}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


@case
def t_good_all(d):
    make_good(d)
    rc, data = run(d, "--all")
    expect("good project --all: no findings, rc 0", rc == 0 and not data["findings"], data)


@case
def t_good_staged_empty(d):
    make_good(d)
    rc, data = run(d, "--staged")
    expect("good project --staged with nothing staged: rc 0", rc == 0 and not data["findings"], data)


@case
def t_missing_profile_and_agents(d):
    sh(d, "init", "-q")
    write(d, "README.md", "# x\n")
    rc, data = run(d, "--all")
    expect("missing profile/AGENTS: P1+E1 errors, rc 1", rc == 1 and {"P1", "E1"} <= set(ids(data, "ERROR")), data)


@case
def t_missing_sections_and_role(d):
    make_good(d)
    write(d, "AGENTS.md", "# Demo\n\n## 规则\n- x\n")
    write(d, "harness/profile.md", GOOD_PROFILE.replace("docs/product/", "docs/nope/"))
    rc, data = run(d, "--all")
    e3 = [f for f in data["findings"] if f["id"] == "E3"]
    expect("E3 both sections missing", len(e3) == 2, data)
    expect("P2 missing role path", "P2" in ids(data, "ERROR"), data)
    expect("E4 roles not linked", "E4" in ids(data, "WARN"), data)


@case
def t_bad_anchor_in_profile(d):
    make_good(d)
    write(d, "harness/profile.md", GOOD_PROFILE.replace("README.md#架构 概览", "README.md#不存在"))
    rc, data = run(d, "--all")
    expect("P2 missing anchor", any(f["id"] == "P2" and "heading" in f["msg"] for f in data["findings"]), data)


@case
def t_broken_links(d):
    make_good(d)
    write(d, "docs/product/a.md", "# A\n\n[x](../../missing.md) [y](login.md#不存在) [ok](login.md#登录-流程)"
                                   " `[code](nope.md)` [web](https://example.com) [self](#a)\n")
    rc, data = run(d, "--all")
    l1 = [f for f in data["findings"] if f["id"] == "L1"]
    expect("L1 finds exactly missing file + bad anchor", rc == 1 and len(l1) == 2, data)


@case
def t_staged_rename_breaks_link(d):
    make_good(d)
    sh(d, "mv", "docs/product/login.md", "docs/product/signin.md")
    rc, data = run(d, "--staged")
    l1 = [f for f in data["findings"] if f["id"] == "L1"]
    expect("staged rename: L1 error in unstaged referrer with rename hint",
           rc == 1 and any("signin.md" in (f["fix"] or "") and f["file"] == "ARCHITECTURE.md" for f in l1), data)


@case
def t_staged_new_md_broken(d):
    make_good(d)
    write(d, "docs/product/new.md", "# New\n\n[bad](gone.md)\n")
    sh(d, "add", "docs/product/new.md")
    rc, data = run(d, "--staged")
    expect("staged new md with broken link -> L1 error", rc == 1 and "L1" in ids(data, "ERROR"), data)


@case
def t_drift(d):
    make_good(d)
    write(d, "workers/job.py", "x=1\n")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    sh(d, "add", "-A")
    rc, data = run(d, "--staged")
    d1 = [f for f in data["findings"] if f["id"] == "D1"]
    expect("D1 warns on new top dir + build file, rc 0",
           rc == 0 and d1 and "workers/" in d1[0]["msg"] and "pyproject.toml" in d1[0]["msg"], data)
    write(d, "ARCHITECTURE.md", "# 架构\n\nworkers/ 负责后台任务。见 [需求](docs/product/login.md#登录-流程)。\n")
    sh(d, "add", "-A")
    rc, data = run(d, "--staged")
    expect("D1 silent when docs also changed", "D1" not in ids(data), data)


@case
def t_neutral_and_exempt(d):
    make_good(d)
    write(d, "AGENTS.md", GOOD_AGENTS + "\n- 使用 Claude 时请用 apply_patch。\n")
    write(d, ".agents/skills/x/SKILL.md", "---\nname: x\n---\nGPT-5 only\n")
    rc, data = run(d, "--all")
    n1 = [f for f in data["findings"] if f["id"] == "N1"]
    expect("N1 warns in AGENTS.md and SKILL.md", len({f["file"] for f in n1}) == 2 and rc == 0, data)
    write(d, "harness/profile.md", GOOD_PROFILE.replace("| 允许 | |", "| 允许 | Claude, apply_patch, GPT |"))
    rc, data = run(d, "--all")
    expect("N1 allow list suppresses", "N1" not in ids(data), data)
    write(d, "harness/profile.md", GOOD_PROFILE.replace("|---|---|\n\n## 中立词表", "|---|---|\n| N1 | 测试 |\n\n## 中立词表"))
    rc, data = run(d, "--all")
    expect("N1 exemption suppresses + counted", "N1" not in ids(data) and data["exempted"] == 2, data)


@case
def t_size_and_vendor(d):
    make_good(d)
    write(d, "AGENTS.md", GOOD_AGENTS + "\n".join(f"- 行 {i}" for i in range(220)))
    write(d, "CLAUDE.md", "x\n")
    write(d, "pkg/AGENTS.md", "x" * (33 * 1024))
    rc, data = run(d, "--all")
    e2 = {(f["file"], f["level"]) for f in data["findings"] if f["id"] == "E2"}
    expect("E2 warn root, error nested >32KiB", ("AGENTS.md", "WARN") in e2 and ("pkg/AGENTS.md", "ERROR") in e2, data)
    expect("X1 vendor warn", "X1" in ids(data, "WARN"), data)


@case
def t_plans_l2(d):
    make_good(d)
    p = GOOD_PROFILE.replace("| L1 |", "| L2 |").replace("| 计划 | — | |", "| 计划 | harness/plans/ | |")
    write(d, "harness/profile.md", p)
    write(d, "AGENTS.md", GOOD_AGENTS + "- 计划：[harness/plans/](harness/plans/)\n")
    write(d, "harness/plans/active/a.md", "# A\n## 目标\n## 进度\n")
    write(d, "harness/plans/active/b.md", "# B\n## Goal\n## Progress\n## Decisions\n## Next steps\n")
    rc, data = run(d, "--all")
    s1 = [f for f in data["findings"] if f["id"] == "S1"]
    expect("S1 flags only incomplete plan", len(s1) == 1 and s1[0]["file"].endswith("a.md"), data)


@case
def t_version_mismatch(d):
    make_good(d)
    write(d, "harness/profile.md", GOOD_PROFILE.replace("1.0.0", "0.9.0"))
    rc, data = run(d, "--all")
    expect("P3 version mismatch warn", "P3" in ids(data, "WARN"), data)


@case
def t_templates_pass(d):
    """The shipped English templates, filled minimally, must pass and keep the parser in sync."""
    sh(d, "init", "-q")
    write(d, "AGENTS.md", (ASSETS / "AGENTS.md").read_text(encoding="utf-8"))
    write(d, "harness/profile.md", (ASSETS / "profile.md").read_text(encoding="utf-8"))
    write(d, "ARCHITECTURE.md", "# Architecture\n")
    write(d, "docs/product/a.md", "# A\n")
    write(d, "docs/design/b.md", "# B\n")
    rc, data = run(d, "--all")
    expect("asset templates: no findings", rc == 0 and not data["findings"], data)
    p = (ASSETS / "profile.md").read_text(encoding="utf-8")
    p = p.replace("| L1 |", "| L2 |").replace("| Plans | — | Not needed at L1 |", "| Plans | harness/plans/ | |")
    p = p.replace("| Check | Reason |\n|---|---|", "| Check | Reason |\n|---|---|\n| E4 | test |")
    write(d, "harness/profile.md", p)
    write(d, "harness/plans/active/x.md", "# X\n## Goal\n## Progress\n## Next steps\n")
    rc, data = run(d, "--all")
    s1 = [f for f in data["findings"] if f["id"] == "S1"]
    expect("English profile: L2 + plans role + exemption parsed",
           len(s1) == 1 and "Decisions" in s1[0]["msg"] and data["exempted"] == 1 and "E4" not in ids(data), data)


@case
def t_text_output_and_hook(d):
    make_good(d)
    (Path(d) / "harness").mkdir(exist_ok=True)
    shutil.copy(CHECK, Path(d) / "harness" / "check.py")
    (Path(d) / ".githooks").mkdir()
    shutil.copy(ASSETS / "pre-commit", Path(d) / ".githooks" / "pre-commit")
    sh(d, "config", "core.hooksPath", ".githooks")
    sh(d, "add", "-A")
    sh(d, "commit", "-q", "-m", "install")
    write(d, "docs/product/bad.md", "# Bad\n\n[x](nope.md)\n")
    sh(d, "add", "-A")
    r = sh(d, "commit", "-m", "bad")
    out = r.stdout + r.stderr
    if "Python 3.8+ not found" in out:
        print("SKIP hook: no python on hook PATH (fail-open message shown)")
        return
    expect("pre-commit hook blocks commit with L1 error",
           r.returncode != 0 and "[ERROR] L1" in out and "commit blocked" in out, None)
    if r.returncode == 0:
        print(out)


print(f"\n{len(failures)} failure(s)" + (": " + ", ".join(failures) if failures else ""))
sys.exit(1 if failures else 0)
