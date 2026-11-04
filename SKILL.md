---
name: project-harness
description: 'Meta skill that organizes and audits a project against the harness standard so any agent or model can understand, verify and hand off the work. Use when: setting up or reorganizing a project harness, AGENTS.md, docs/ and harness/ structure; filing user-written requirements or design docs into place; checking whether a project follows harness principles (compliance audit, cold-start probe, doc drift); installing or upgrading the commit-time harness check (check.py / pre-commit). Keywords: harness, AGENTS.md, project structure, audit, drift, handoff, cold start. Not for: writing requirements/design content, cross-platform agent config (use portability-config).'
argument-hint: '[audit | setup | install-hook | upgrade]'
---

# Project Harness

Bring a project to a state where **any agent, on any model, can pick it up from a cold start without guessing**, and keep that state continuously checkable.

- Harness only: structure, entry point, indexes, how to verify, audits. **Never write requirements/design content; never change business code.**
- Does not dictate what a project looks like. It only requires the structure to be **declared** (`harness/profile.md`) and **discoverable** (`AGENTS.md`).
- Language: write reports and new docs in the user's or the project's language; keep file names and check IDs as they are.

## Core concepts

| Concept | Description | Details |
|---|---|---|
| Cold-start questions Q1–Q6 | The principles: can a fresh agent answer "what is it / how to verify / where is knowledge / rules / progress / are docs accurate" | [principles.md](./references/principles.md) |
| Role map | Entry, architecture, requirements, design, plans… mapped to **actual locations** in the project | [roles.md](./references/roles.md) |
| Profile | `harness/profile.md`: standard version, level, role map, exemptions | [profile.md](./assets/profile.md) |
| Computational checks | `check.py`: fast checks at commit time | [checks.md](./references/checks.md) |
| Levels | L1 entry + verification + knowledge index; L2 + cross-session plans/log; L3 + periodic audits | [principles.md](./references/principles.md) |

## Modes

Choose by user intent (when unsure, run `audit` first):

- **audit** (default): read-only audit producing a gap report.
- **setup**: first-time setup or reorganization (audit → plan → user confirms → apply).
- **install-hook**: copy `check.py` into the project and install the pre-commit check.
- **upgrade**: upgrade when the project's `harness/check.py` or profile standard version is behind this skill.

## Workflow

1. **Read the profile**: if `harness/profile.md` exists it is authoritative; otherwise treat this as first time.
2. **Reconnaissance (read-only)**: directory structure, language/build system, executable entry points, existing docs and agent instruction files. Decide the project type (may be several) and read only the matching heuristics:
   [Library/CLI](./references/pattern-code-lib.md) · [Web app](./references/pattern-web-app.md) · [Data/scripts](./references/pattern-data.md) · [Docs only](./references/pattern-docs.md) · [Monorepo](./references/pattern-monorepo.md)
3. **Computational checks**: run `python <this skill dir>/scripts/check.py --all --root <repo>` (if installed in the project: `python harness/check.py --all`).
4. **Cold-start probe**: answer Q1–Q6 following the method in [principles.md](./references/principles.md). Every answer must cite file evidence; anything unanswerable or requiring a guess is a gap.
5. **Gap report**: merge the results of 3 and 4 into the report format below. `audit` mode stops here.
6. **Plan**: list changes in the order "map what exists → move / add indexes → create new only last". **Wait for user confirmation.**
7. **Apply**: follow the change rules below; start from the [AGENTS.md skeleton](./assets/AGENTS.md) and [profile skeleton](./assets/profile.md) and fill only sections that have content.
8. **Verify**: run `check.py --all` again; it must report no ERROR. Update "Last audit" in the profile.

### install-hook

1. Copy [check.py](./scripts/check.py) → `<repo>/harness/check.py`; copy [pre-commit](./assets/pre-commit) → `<repo>/.githooks/pre-commit`.
2. Run `git config core.hooksPath .githooks`; add this command to the setup notes in `AGENTS.md` or README (needed once per clone).
3. Record the `Check version` in the profile.

### upgrade

Compare the `VERSION` of `<repo>/harness/check.py` with [./scripts/check.py](./scripts/check.py), and the profile's "Standard version" with [CHANGELOG.md](./CHANGELOG.md). List the changes per the CHANGELOG migration notes; apply after user confirmation.

## Change rules

- Touch only harness files: `AGENTS.md`, architecture docs, `docs/`, `harness/`, `.agents/skills/`, `.githooks/`.
- Move with `git mv`; change structure only (locations, file names, indexes, links), **never the meaning of docs**. Rewriting content (e.g. distilling rules from a design doc into `AGENTS.md`) requires consent first.
- Occam's razor: no empty directories; no unneeded checks; don't restate what standard conventions already make discoverable (e.g. `pytest`, `npm test`).
- Keep `AGENTS.md` a router of ≤200 lines; push details down into mapped docs.
- Contradictions, stale content, docs disagreeing with code: put them in the report; do not fix them unilaterally.
- Vendor-specific config (`.github/copilot-instructions.md`, `CLAUDE.md`, `.cursorrules`, `.vscode/mcp.json`, …): report only and suggest portability-config.

## Report format

```markdown
## Harness audit — <project> · standard v<N> · target L<N>
Project type: <…>
| Question | Result | Evidence / gap |
|---|---|---|
| Q1 What is it | ✅ / ❌ / N/A | <file:line or what is missing> |
Computational checks: <n> ERROR, <n> WARN (list each)
AGENTS.md size: <lines> lines, ~<tokens> tokens
Suggested changes (by priority): 1. … 2. …
```
