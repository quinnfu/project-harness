# project-harness

A **meta skill** that organizes any project, whatever its structure, so that any agent or model can cold-start on it without guessing — and keeps it that way with checks at commit time.

- It does not dictate a project layout. It only requires the structure to be **declared** (`harness/profile.md`) and **discoverable** (`AGENTS.md`).
- Harness only: entry points, indexes, how to verify, audits. It never writes requirements or design content and never touches business code.
- Built on open, cross-tool formats ([Agent Skills](https://agentskills.io), [AGENTS.md](https://agents.md)), so it works with any agent tool that supports Agent Skills.

## Install

```sh
git clone https://github.com/quinnfu/project-harness ~/.agents/skills/project-harness
```

If your tool does not read `~/.agents/skills`, clone into that tool's skills directory or add this path in its settings.

Update: `git -C ~/.agents/skills/project-harness pull`

## Usage

Invoke `/project-harness <mode>` in an agent chat:

| Mode | What it does |
|---|---|
| `audit` (default) | Read-only audit: cold-start questions Q1–Q6 plus computational checks, producing a gap report |
| `setup` | First-time setup or reorganization: plan → user confirmation → apply |
| `install-hook` | Copy `check.py` into the project and install the pre-commit check |
| `upgrade` | Upgrade a project whose `check.py` or standard version is behind the skill |

You can also run the checks directly, without an agent (Python ≥ 3.8, standard library only):

```sh
python scripts/check.py --all --root <repo>      # full audit
python harness/check.py --staged                 # inside a project: check staged changes (used by pre-commit)
python harness/check.py --all --json             # machine-readable output
```

## Layout

```
SKILL.md          entry point and workflow (read by the agent)
references/       principles, roles, check catalog, heuristics per project type
assets/           AGENTS.md and profile templates, pre-commit hook
scripts/check.py  computational checks (vendored into projects)
tests/            scenario regression tests for check.py
CHANGELOG.md      history of the standard version and the check version
AGENTS.md         how agents develop this repository (change workflow)
.githooks/        dev hooks for this repository
```

## Development

After cloning, enable the dev hooks once:

```sh
git config core.hooksPath .githooks
```

- `pre-commit` runs the regression tests (`python tests/run_tests.py`, requires git) when `scripts/`, `tests/` or `assets/` change, and blocks the commit if they fail.
- `post-commit` pushes the current branch to `origin`.

These hooks are for developing this skill only; the hook installed into projects is [assets/pre-commit](assets/pre-commit).

Changes go through pull requests. To have an agent make a change, open a chat in this repository and describe it; the agent follows the change workflow in [AGENTS.md](AGENTS.md): branch → edit → test → review → push → open a PR for you to merge.

See [CHANGELOG.md](CHANGELOG.md) for versioning rules and migration notes. When you change `check.py`, bump its `VERSION` and keep [references/checks.md](references/checks.md) in sync.

## References

- OpenAI Cookbook — [Iterating on development workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)
- OpenAI — [Harness engineering](https://openai.com/index/harness-engineering/)
- Anthropic — [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Birgitta Böckeler — [Harness engineering for coding agent users](https://martinfowler.com/articles/harness-engineering.html)

## License

[MIT](LICENSE)
