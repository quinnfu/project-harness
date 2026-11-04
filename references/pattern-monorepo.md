# Pattern: monorepo / multi-package repository

Signals: `packages/`, `apps/`, `services/`; workspace config (`pnpm-workspace.yaml`, `workspaces` in `package.json`, Cargo workspace, `go.work`); several independent build files.

- **Structure**: the root `AGENTS.md` only routes (package responsibilities + links); each package may have its own `AGENTS.md` (most agents read the `AGENTS.md` files between the working directory and the root). Nested `AGENTS.md` files are size-checked too (E2).
- **Q1**: the root architecture doc covers dependencies and boundaries between packages; package internals go into each package's own docs.
- **Q2**: state whether verification runs from the root or the package directory, and how to verify only affected packages.
- **Q3**: the profile role map may list roles per package (e.g. "Requirements (web)", "Requirements (api)").
- **Q4**: common key rules — allowed dependency directions between packages, where shared code lives. Suggest enforcing with dependency-check tools where possible.
- **Q6**: focus on whether the package list matches the root docs (D1 warns when packages are added or removed).
