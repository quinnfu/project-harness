# Changelog

Two versions evolve independently:

- **Standard version** (integer): +1 when the meaning of principles, levels or roles changes. A project's profile records the standard version it follows; when upgrading, follow the migration notes below.
- **Check version** (semver, `VERSION` in `scripts/check.py`): new check → minor; fixes / message tweaks → patch; changed meaning of a check ID or incompatible profile format → major.

After changing this skill: append an entry here; if `check.py` changed, bump `VERSION` and run `python tests/run_tests.py` from the skill root (scenario regression tests; requires git). Projects see the difference the next time they run `upgrade` mode.

## Standard v1 · check 1.0.0 — 2026-11-04

- Initial release: cold-start questions Q1–Q6, levels L1–L3, role map, profile format.
- Principles: failed, skipped or unrun checks mean the task is unfinished (Q2, AGENTS.md template); plan progress distinguishes done from verified (Q5).
- check.py checks: P1 P2 P3 E1 E2 E3 E4 L1 N1 D1 X1 S1. The profile parser accepts English and Chinese keys.
