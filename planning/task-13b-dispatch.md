# Task 13b: the route search as a run, bounded and ranked (backend), in a worktree

Careerwright L0. Task 13a built the route search core (`planning/search.py`, ADR 0016) and its
independent oracle. Task 12a stored the person's planning inputs. This task makes the search
something a person can start: a durable run with its caps, exact stop reasons, a separate rank
stage, cancellation, honest truncation, and the 50,000-point ranking benchmark. It has no
interface: Task 14 builds the Routes chapter on it.

## The product owner's scope decision (binding, 31 October 2026)
L0 leaves out the disk-backed archive with its checkpoints and resume, and the separate
cancellable child process. Your card (in the brief) already says so, under "Settled", and the
specification's revision record (section 22, "L0 deferrals") is the authority. So:
- The archive of every distinct feasible schedule encountered, dominated ones included, is
  kept in memory under the caps. Never evict a candidate to fit memory.
- A crashed solve is a failed run, started again under a new attempt ID, never a truncated
  result.
- A cancel reaches the search at its next check, inside the worker.
- The 50,000-point ranking benchmark stays, and so do the caps, their exact stop reasons, the
  separate rank stage and the truncation wording.

## Your tree
- Worktree: `/Users/darianraad/Code/careerpathoptimizer-wt/13b`, branch `wt-13b`, from
  `l0-local-release` at 38f9998. Work and commit only there. Never touch `l0-local-release` or
  the main tree.
- It is set up: `backend/.venv`, `apps/web/node_modules`, the `docs/design` dependencies, and
  `var` (a link to the main tree's datasets, excluded from git).
- Running beside you: in the main tree, Task 6d slice A's fix round (profile and catalogue;
  it adds migration 0035). Waiting to integrate: Task 3b (live sessions; API schemas, the
  register). At your rebase follow R15: renumber your migration if another took the number,
  regenerate the client, and edit the register only in your last commit.

## Read first
1. `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`,
   all of it, especially "Parallel work" and the acceptance lock.
2. Your brief, `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-13b-brief.md`.
   It is your requirements. Read the Sprint 6b card in `docs/plan/development-plan.md` with it
   (its sizing paragraph is settled as above).
3. Task 13a's report, `task-13a-report.md` in the same folder: "The answer for Task 13b" (the
   measured sizes) and what it built. Its review's deferred minor M3 is yours: the ranking
   runs outside the 30-second clock today.
4. What you build on:
   - ADR 0016 (the route search) and ADR 0013 (planning, as amended by Task 12a);
   - `backend/src/careerwright/planning/` (`search.py`, `checker.py`, `layers.py`,
     `inputs.py`, `store.py`, `commands.py`);
   - `backend/tests/support/route_oracle.py` (the independent oracle);
   - `careerwright/identity/activity.py` with `workflow.py` (the pinned durable-activity
     pattern; one `RunTask` per run kind, composed in `careerwright/worker.py`);
   - the existing cancel path and its lock order (`CLAUDE.md`, ADR 0009 decision 15).

## Decisions that bind you
1. **The solve is a run kind**, one `RunTask` composed in the worker, never a second call path
   (ADR 0006). The workflow carries IDs only. It calls no model and needs no key. If the
   workflow's step sequence must change, change DBOS `application_version` as `CLAUDE.md`
   says, and say so in your report; otherwise it stays `careerwright-l0-1`.
2. **Candidate evaluation stays pure:** no network, model or database access inside the
   search (OPT1-09's tested part must still pass).
3. **The rank stage is separate and observable,** with its own time inside the budget or its
   own named limit; decide which, state it in ADR 0016, and test it (13a's M3).
4. **The efficient two-objective layering** equals Task 13a's iterative peeling on every
   instance that completes. Pareto layers are over the full archive, dominated schedules
   included; equal points don't dominate each other.
5. **Truncation never reads as "no route".** A truncated result leads with "Best trade-offs
   found" as a code the web words, with the instance size and the narrowing Task 13a's sizes
   suggest. `NO_ROUTE_IN_BOUNDED_MODEL` needs complete coverage. Unknown inputs leave a route
   unresolved, never passed.
6. **The solve reads the person's stored inputs** (Task 12a) as an immutable snapshot taken
   when the run starts; a later edit can't change an in-flight solve.
7. **R11, facts not sentences:** the API returns codes and numbers, never sentences. New error
   codes are `CareerwrightError` codes; add their words to `vocabulary.ts` only if the web
   shows them now (it doesn't yet: Task 14).
8. Every consequential write takes an expected version and an `Idempotency-Key` through
   `run_idempotent`; row-level security via `actor_transaction` and `run_transaction`.

## Docker
After a machine restart the Docker daemon was down. The controller has asked the product owner
to start it. Integration tests and `make acceptance` need it.
- Check with `docker info >/dev/null 2>&1`. If it's down, build and run the fast checks first,
  then try again later. Never start Docker yourself and never open an app or window.
- If it's still down at the end, report "integration and acceptance not run: Docker down".

## Hard rules
- Edit/Write for source changes. The project's own generators are fine (`pnpm run
  generate`); no scripts that rewrite files.
- Stage explicit paths. Never stage `var`, `answers-2.md` or `esco_research.txt`.
- No live model calls, no web requests, no Docker pull, no headed browser.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`, and leave every running stack alone.
- No subagents. Never push. pnpm only, never npm or npx.
- Migrations are forward-only, with row-level security and CHECKs that repeat the domain
  rules.
- Disclose every changed test input or assertion, with why.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Checks
- RED before GREEN for each behaviour.
- `make check` before your final commit, and again after the rebase.
- `make acceptance` once at the end, under the lock, in one guarded command.
- Write `docs/reviews/sprint-6.md`, covering 6a and 6b, as the card says.

## Report
Write the full report to
`/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-13b-report.md`.
Then reply with only the short contract and your branch head SHA.
