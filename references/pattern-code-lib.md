# Pattern: library / CLI tool

Signals: `pyproject.toml`, `package.json` (no frontend framework), `Cargo.toml`, `go.mod`, `setup.py`; a `src/` or package directory; a `tests/` directory.

- **Q1**: the architecture doc should cover where the public API lives, internal module layering and dependency direction; for a CLI, where the entry commands are defined.
- **Q2**: mostly standard conventions (`pytest`, `cargo test`, `go test ./...`, `npm test`) — don't write them down. Write only: required optional dependencies/extras, slow-test markers, tests needing network or external services, whether type checking/lint is part of "done".
- **Q3**: design decisions often live in `docs/`, ADRs or PR descriptions; suggest moving key decisions from PR descriptions into the design role.
- **Q4**: common key rules — public API compatibility, versioning/changelog rules, no new runtime dependencies. Suggest enforcing with linters/type checks where possible.
- **Q6**: focus on whether README example code still runs and API names in docs still exist.
