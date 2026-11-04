# project-harness

Source repository of the `project-harness` skill. The skill entry point is [SKILL.md](SKILL.md); this file is about developing the skill itself.

## Setup
- After cloning, run once: `git config core.hooksPath .githooks` (requires git and Python ≥ 3.8 or `uv`).

## Rules
- Occam's razor: add a rule, file or check only when it removes a real failure; prefer deleting to adding.
- Neutral and open: no model or vendor-specific tool names in the standard, templates or check messages.
- Keep in sync: SKILL.md ↔ references/ ↔ assets/ ↔ scripts/check.py ↔ references/checks.md ↔ CHANGELOG.md.
- check.py stays stdlib-only and Python 3.8 compatible; ERROR only for certain problems, heuristics are WARN.
- A failed, skipped or unrun check means the task is unfinished: report it, never as done.
- Never commit to `main`, never force-push, never merge your own pull request.

## Change workflow
1. `git switch main && git pull --ff-only && git switch -c agent/<short-slug>`
2. Make only the requested change. If check.py behavior changes: test first, bump `VERSION`, update references/checks.md and "Check version" in assets/profile.md.
3. Add a CHANGELOG.md entry when the standard, templates or check.py change.
4. Run `python tests/run_tests.py`; it must pass.
5. Review `git diff main...HEAD` in a fresh context (a sub-agent if available) against the Rules. Fix blocking findings, then repeat step 4.
6. Commit; the post-commit hook pushes the branch (otherwise `git push -u origin HEAD`).
7. Open a pull request against `main` (what and why, test result, review findings). Without hosting tooling, give the user `https://github.com/quinnfu/project-harness/compare/main...<branch>?expand=1`.
8. Report the pull request link; the user reviews and merges.

## Definition of done
- Tests pass, review findings are resolved or explained, and a pull request is open.
