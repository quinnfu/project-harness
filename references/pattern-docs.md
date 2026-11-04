# Pattern: docs-only repository

Signals: mostly Markdown/text; no executable code, or only docs-site build config (`mkdocs.yml`, `docusaurus.config.*`).

- **Q1**: the entry point states who the docs are for, how directories are organized, and naming conventions.
- **Q2**: **N/A** without executable code; note it in the profile exemptions. If there is a docs-site build, a successful build can serve as verification.
- **Q3**: the docs are the knowledge; what matters is the index (`AGENTS.md` doc map or per-directory `index.md`) and valid links.
- **Q4**: common key rules — glossary, writing style, file naming, where images live.
- **Q6**: focus on dead links, duplicated content and stale pages. check.py's L1 link check is the main sensor.
