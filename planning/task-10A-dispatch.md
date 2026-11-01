# Task 10, backend half (10A): the Skills chapter's facts (worktree, R17)

Careerwright L0. The product owner adopted pipelining (rule R17, `docs/plan/l0-sprint-tasks.md`):
a task's backend half may start before session W2, which judges words and looks only. This is
Task 10's backend half. The screens half (10B: the Skills chapter itself, the question flow
UI, deleting `spikes/world`, session W2's outcome in `sprint-w.md`) waits for session W2.

## Your tree
Worktree `/home/user/careerwright-wt/10a`, branch `wt-10a` (the controller creates it from
the branch head; `var` linked). Beside you: the acceptance fix in the main tree (tests,
entrypoint, compose, role research's worker path) and Task 7f's fix round in another worktree
(the option pack 0.3.0). Never touch their files. Rebase onto
`claude/confident-ramanujan-ux3saw` at the end (R15: renumber a clashing migration,
regenerate the client, register last).

## Read first
`/home/user/careerwright/planning/env-cloud.md`, `implementer-contract.md`, your brief
`task-10-brief.md` (all of it: the backend half delivers the facts every screen part needs),
ADR 0012 (capability) and its amendments, ADR 0015, `careerwright/capability/`
(readiness, gaps, the question graph, evidence, matrices), the stored target record (Task
6d), the saved answers' qualifications (Task 6f), and the option pack's course outcomes
(Task 7c).

## Deliver (backend and API only; facts and codes, never sentences, R11)
1. A per-target Skills view in the API: what the target's occupation lists (ESCO's, with the
   person's "not part of my job" marks; outside ESCO the chosen closest occupation, or none);
   the person's chosen advert spans (up to three per target, MAP1-01: a command to store
   their selection of spans, with an expected version and an `Idempotency-Key`; no model
   run); the evidence questions shared across targets; readiness where a reviewed rubric
   exists, else an explicit `not_assessed` state with what it asks, never a readiness result;
   the "usual in your role, not confirmed yet" display state for the person's own role's
   ESCO skills, absent (never empty) when there is no role; the person's qualifications as
   entry facts beside the requirements that name them (expected never met; achieved follows
   the gate rules; nothing finds a person ineligible). Every derived result carries its
   `matrix_version` and `definition_version`. The pack's date and review state on every pack
   record shown.
2. Direct edits and chat proposals through the same commands (ADR 0006).
3. The false-positive readiness mappings for the ten course pages reviewed individually in
   tests; any unsupported consequential outcome blocks the affected route.
4. Migration if needed (forward-only, CHECKs, row-level security); the generated client.
5. The card's acceptance at the API level (a target outside the pack → `not_assessed`;
   "not part of my job" never evidence; expected qualification never met; no role → no
   "usual in your role" state).
6. ADR 0012 amendment lines; register rows for the backend parts, marked "backend; screens
   in 10B".

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH). Don't run
integration or acceptance (the controller runs it per batch). Edit/Write only (generators
fine), explicit pathspecs, no web requests, no live calls, no subagents, never start Docker,
never read `.env` or print an environment value, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/home/user/careerwright/planning/task-10A-report.md`; reply with the short contract and your
head SHA.
