# Role map

Project knowledge is organized by **role**, not by fixed directories. Each role's actual location is written in the "Role map" table of `harness/profile.md`.
Default locations are used only when nothing matching exists in the project and the role is actually needed.

Overall convention: **knowledge** (what the system is and should be; long-lived) goes in `docs/`; **process** (how agents work and where they are; volatile) goes in `harness/`.

| Role | Default location | Common existing locations | Level | Notes |
|---|---|---|---|---|
| Entry | `AGENTS.md` | — | L1 required | Fixed, cross-tool standard; a router, ≤200 lines |
| Architecture | `ARCHITECTURE.md` | `README.md#architecture`, `docs/architecture.md`, `docs/design.md` | L1 | Directory responsibilities, key dependency directions |
| Requirements | `docs/product/` | `specs/`, `spec.md`, `PRD.md`, `requirements.md`, issue links | Map if present | User-written requirements are filed here |
| Design | `docs/design/` | `adr/`, `rfcs/`, `docs/decisions/` | Map if present | Designs, decision records, core beliefs |
| References | `docs/references/` | `vendor-docs/`, `*-llms.txt` | Optional | Condensed third-party library/API references |
| Generated | `docs/generated/` | — | Optional | Script-generated docs (e.g. schemas); never hand-edited |
| Plans | `harness/plans/` (with `active/`, `done/`) | `.plans/`, `PLANS.md`, `Plans.md`, `harness/build/` | L2 | Cross-session execution plans |
| Log | `harness/log.md` | `CHANGELOG.md`, `harness/build-log.md` | L2 | Append-only progress record |
| Tech debt | `harness/tech-debt.md` | issue labels | L2 | Known problems |

## Location syntax in the profile

| Location | Meaning | check.py behavior |
|---|---|---|
| `docs/product/` | Directory | Checks the directory exists |
| `ARCHITECTURE.md` | File | Checks the file exists |
| `README.md#architecture` | A section in a file | Checks the file exists and has the heading |
| `https://…` | External location (e.g. issue tracker) | Skipped |
| `—` / empty / `N/A` | Not needed in this project | Skipped |

You can add custom roles (e.g. "Runbook"); check.py checks their locations the same way. A role whose name contains "plan" triggers the L2 S1 check.
