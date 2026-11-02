# Task 14, backend half (14A): the Routes chapter's facts (worktree)

Careerwright L0, current process ruling ("How we build and review", `docs/plan/l0-sprint-tasks.md`):
a backend half may start before session W2 (words and looks only). Tasks 13b, 12c and 12b's
backend half (12bA: the checkpoint, supplied figures, added options, pack 0.4.0) are
integrated. The screens half (14B: the Routes chapter, the scatter, the Gantt, step cards,
motion) waits for session W2 and 12bB.

## Your tree
Worktree `/home/user/careerwright-wt/14a`, branch `wt-14a` (from the branch head; `var` linked).
Work and commit only there. Beside you in the main tree: a small test-only task hardening two
world journeys (`apps/web/e2e/world.spec.ts`). Rebase at the end (R15).

## Read first
`/home/user/careerwright/planning/env-cloud.md`, `implementer-contract.md`, your brief
`task-14-brief.md` (all of it), ADRs 0013 and 0016 as amended, `careerwright/planning/`
(search, layers, solves, solve_runs, checker, figures, the 12bA checkpoint), Task 13a's
report on the measured sizes (`planning/archive/task-13a-report.md`, "The answer for Task 13b"),
and session 2's H-13 record (`docs/reviews/session-2-answers.md`).

## Deliver (backend and API only; facts and codes, never sentences, R11)
1. The facts every part of the Routes chapter needs from real solver output, served by the
   API: per-target time-cost points with the cost definition, baseline, horizon, currency,
   bounds and coverage; F1-F3 layers with family grouping and named dominance reasons (as
   codes); one documented deterministic comparator rule (stated in ADR 0016); stress
   scenarios separately; view filtering that preserves ranks and explicit reranking; the
   monthly financial table, step cards' facts and the Gantt's dated actions; the paginated
   archive and a bounded projection. No rank, layer or affordability computed by the web.
2. The solve's stage checks (API-05): budget-qualified needs the confirmed limits; economic
   needs a horizon and a baseline.
3. Qualification facts: a route on an option not reviewed (added or researched) or on a
   person-supplied figure is qualified, with the reason as a code; a route longer than the
   24-month model is its own state ("longer than Careerwright can plan yet"), never no route,
   not feasible or impossible; a fee a tuition fee loan or Advanced Learner Loan pays shows as
   a loan to repay with its amount; a loan not yet approved makes the route conditional beside
   the one without it. Truncated coverage leads with "best trade-offs found" as a code, the
   instance size and the narrowing that would let it complete (13a's sizes).
   NO_ROUTE_IN_BOUNDED_MODEL only with complete coverage.
4. The four planning-model gaps (PLN-01 information-gathering and waiting actions; OPTN-04 the
   search and review step before an offer gate; PLN-04 a verification milestone after an
   assessed completion; OUT1-08 experience beyond an offering's own outcomes): for each, model
   it if it's small and needs no new run kind (the infrastructure is frozen for L0), or write
   it up as a proposed L0 deferral with its reasons for the product owner's yes (one plain
   line each in your report; don't record a deferral as approved).
5. H-13's misunderstandings: each one the API can help with (e.g. a plain-word code for every
   cost and condition, TRACE-01 and DIRECTAI kept apart) addressed or carried with a reason.
6. The pack's date and review states on every pack record in a route (R9).
7. Migration only if needed; the generated client; ADR 0016/0013 lines; register rows marked
   "backend; screens in 14B".

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH). Focused
integration runs under the lock with the build shim, one guarded command each (wait and retry
if held; never remove a lock you didn't take):
`export PATH=/tmp/ccr-shim:/opt/node24/bin:$PATH; L=/home/user/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /home/user/careerwright-wt/14a/backend && env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY uv run --locked pytest -m integration <files> > /tmp/14a-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN. Edit/Write only (generators fine), explicit
pathspecs, no web requests, no live calls, no subagents, never start Docker, never read
`.env` or print an environment value, never push. One paper file: your report. Commit
messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/home/user/careerwright/planning/task-14A-report.md`; reply with the short contract and head SHA.
