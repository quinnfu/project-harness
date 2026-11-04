# <Project name>

<One sentence: what this project is and who it is for.>

## Setup
<!-- Only non-standard steps; delete this section if there are none. Keep the line below when the harness check is installed. -->
- After cloning, run once: `git config core.hooksPath .githooks`

## Rules
<!-- Only the few rules agents most often break and that apply on every platform; link details to a conventions doc. No model names or tool-specific tool names. -->
- When a change affects structure, verification or conventions, update the docs the "Doc map" points to.
- A failed, skipped or unrun check means the task is unfinished: report it with evidence and the next step, never as done.

## Definition of done
<!-- What counts as "done". Verification that follows standard conventions (e.g. pytest, npm test) gets one line; spell out only the non-standard parts. Docs-only projects list manual checks. -->
- <e.g. Tests pass (standard convention); UI changes have been confirmed in a real browser.>

## Doc map
<!-- Keep in sync with the role map in harness/profile.md; list only what exists. -->
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Requirements: [docs/product/](docs/product/)
- Design: [docs/design/](docs/design/)
- Harness conventions: [harness/profile.md](harness/profile.md)
