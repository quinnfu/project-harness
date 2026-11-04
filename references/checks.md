# check.py checks

Computational checks using only the Python standard library: no LLM calls, no network, no project tests.
**ERROR** is used only for problems that are certain (blocks the commit); heuristics are always **WARN** (reminder only).
Any check can be turned off by ID in the profile's "Exemptions" table (a reason is required).

| ID | Check | Level | `--staged` | `--all` |
|---|---|---|---|---|
| P1 | `harness/profile.md` exists and a standard version can be parsed | ERROR | ✅ | ✅ |
| P2 | Paths in the role map exist (`file#heading` requires the heading) | ERROR | ✅ | ✅ |
| P3 | The profile's `Check version` matches this script's `VERSION` | WARN | — | ✅ |
| E1 | Root `AGENTS.md` exists | ERROR | ✅ | ✅ |
| E2 | `AGENTS.md` size: >200 lines or >16 KB is WARN; >32 KiB is ERROR | see left | root + staged | all |
| E3 | Root `AGENTS.md` has "Definition of done" and "Doc map" sections | ERROR | ✅ | ✅ |
| E4 | Every local location in the role map is linked from `AGENTS.md` | WARN | ✅ | ✅ |
| L1 | Relative Markdown links are valid (file + heading anchor) | ERROR | staged `.md`, plus links still pointing at files deleted/renamed in this commit | all `.md` |
| N1 | Model names / tool-specific names in instruction files (`AGENTS.md`, `.agents/skills/**/SKILL.md`) | WARN | staged | all |
| D1 | This commit adds/removes a top-level directory or changes build files without touching any doc | WARN | ✅ | — |
| X1 | Vendor-specific agent config exists | WARN | — | ✅ |
| S1 | (L2+) An active plan lacks Goal / Progress / Decisions / Next steps, or is not updated for 14 days | WARN | — | ✅ |

Notes:

- `--staged` reads file contents from the working tree (not the index snapshot); results may differ slightly with partial staging.
- Skipped paths: `.git`, `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.next`, `target`, `vendor`.
- Heading anchors follow GitHub rules (lowercase, punctuation removed, spaces become `-`, non-ASCII letters kept; duplicates get `-1`, `-2`).
- The profile parser accepts both English and Chinese keys (e.g. `Standard version` / `标准版本`, `Role map` / `角色映射`), as do the E3 and S1 heading checks.
- Exit code: 1 if there is any non-exempted ERROR; otherwise 0. `--json` gives machine-readable output.
