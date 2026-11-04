# Harness principles (standard v1)

harness = guides (help the agent get it right beforehand) + sensors (let the agent correct itself afterwards).
This standard does not dictate project structure. It only requires that **a brand-new agent, identical across any model, can answer the questions below after entering the project without guessing**, and that the locations of the answers are recorded in `harness/profile.md` and can be checked.

## Levels

| Level | Requirements | For |
|---|---|---|
| L1 | Q1, Q2, Q3, Q4, Q6 | The starting point for every project |
| L2 | L1 + Q5 (cross-session plans and log) | Work that often spans sessions or is handed off between models |
| L3 | L2 + periodic audits + turning frequent problems into mechanical checks | Long-lived, multi-person or high agent throughput |

## Cold-start questions

Each has: goal · probe · anti-patterns · fixes (by priority) · related checks.

### Q1 What is this project and how is it structured?

- **Goal**: within a minute, state the project's purpose, the responsibility of the main directories, and where the entry points are.
- **Probe**: read only `AGENTS.md` and its direct links; write a 3-sentence overview and a directory responsibility table; compare with the actual directories.
- **Anti-patterns**: `AGENTS.md` as an encyclopedia (> 200 lines); architecture that exists only in someone's head; README that disagrees with the directories.
- **Fixes**: existing architecture description → map it in the profile and link it from `AGENTS.md`; none → write a minimal `ARCHITECTURE.md` (directory responsibility table + key dependency directions).
- **Checks**: E1, E2, E3, P2.

### Q2 How do I verify a change?

- **Goal**: the agent knows, without guessing, how to confirm nothing is broken — and what counts as done.
- **Probe**: try to find and (when safe) run the verification; note whether guessing was needed or it got stuck.
- **Principle**: when standard conventions apply (`pytest`, `npm test`, `cargo test`…) **don't write them down**; write only what is non-standard: prerequisites (services, environment variables), special flags, trade-offs for slow tests, manual verification steps. Docs-only projects: N/A.
- **Principle**: a failed, skipped or unrun check means the task is **unfinished**. Report it with evidence and the next step; never report it as done. Hitting a retry or iteration limit is not completion either.
- **Anti-patterns**: restating obvious commands; verification that depends on word-of-mouth setup steps; no definition of "done"; reporting "done" when checks failed or were never run.
- **Fixes**: state how to verify in the "Definition of done" section of `AGENTS.md` (standard conventions in one line); put non-standard details there or in a linked doc; keep the rule "failed or unrun checks = unfinished" in `AGENTS.md`.
- **Checks**: E3 (Definition of done exists).

### Q3 Where are requirements, design and decisions?

- **Goal**: knowledge lives in the repository, in fixed locations, reachable from `AGENTS.md`.
- **Probe**: for each role (see roles.md) find the actual location; check that it is one hop from the doc map in `AGENTS.md`.
- **Anti-patterns**: key decisions only in chat history or a tool's private memory; scattered docs without an index; dead links.
- **Fixes**: map existing locations → add indexes / fix links → `git mv` into place if needed → create new only last.
- **Checks**: P1, P2, E4, L1.

### Q4 Which conventions must not be violated?

- **Goal**: key rules are in `AGENTS.md` (briefly) or a linked conventions doc; whatever can be enforced mechanically already is.
- **Probe**: list the rules findable in docs; judge whether each could be enforced by a linter, test or script.
- **Anti-patterns**: prose requirements for things a machine could check (formatting, import order); rules naming models or tool-specific tool names; contradictory rules.
- **Fixes**: mechanically checkable → suggest adding to linter/tests (list in the report, don't add unilaterally); reword as model-neutral outcomes (e.g. "run X after editing files" instead of "use the edit tool").
- **Checks**: N1.

### Q5 Where are we, and what's next? (L2)

- **Goal**: work can continue after switching sessions or models.
- **Probe**: read the plans and log roles; can you state the in-flight tasks, current progress, next step, and key decisions made?
- **Anti-patterns**: progress only in session context; finished plans never archived; logs rewritten instead of appended; progress that counts implemented tasks as if they were proven to work.
- **Fixes**: each plan file has at least the sections Goal / Progress / Decisions / Next steps (Markdown). In Progress, mark each item as **done** (implemented) or **verified** (with evidence: test, command output or manual check) — "8 of 10 done" says nothing about whether it works. Logs are append-only; move finished plans to `done/`.
- **Checks**: S1.

### Q6 Are the docs still accurate? Any redundancy?

- **Goal**: docs agree with code; each fact is written in one place; nothing is stale.
- **Probe**: spot-check that paths, commands and module names mentioned in docs exist; look for paragraphs describing the same fact; look for statements contradicting code.
- **Anti-patterns**: the same command written in 3 files; docs describing deleted modules; structural changes never reflected in docs.
- **Fixes**: keep one copy and link to it from elsewhere; put contradictions and stale content in the report for the user to decide; keep a rule in `AGENTS.md`: "when a change affects structure, verification or conventions, update the docs the doc map points to".
- **Checks**: L1, D1, X1.

## How to run the cold-start probe

1. If the environment can start a **sub-agent with a fresh context**, give it Q1–Q6 (per level) and require: answer only from repository files, cite `file:line` for every answer, say "cannot determine" instead of guessing.
2. Otherwise answer yourself under the same rules, and **do not use project knowledge already present in this conversation**.
3. Compare answers with reality: wrong answers, missing answers and guesses are all gaps.

## Closing the loop

The same problem showing up twice, in audits or day-to-day development → upgrade the harness: add docs/rules, or propose a mechanical check. Record the upgrade in the "Changes" section of the project's `harness/profile.md` or wherever the team agrees.
