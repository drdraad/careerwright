# Review: Task 13b, the route search as a run (backend)

You review one task of Careerwright L0, in one of two halves (your half is named in your
prompt). It was built in the worktree branch `wt-13b`, rebased onto `l0-local-release` at
6c9e0a8: commits 6c9e0a8..070aa89. It makes the route search something a person can start: a
durable, keyless run kind (`route_solve`) with its own DBOS workflow, caps and exact stop
reasons, a separate rank stage under its own limit, cancellation at the search's next check,
an efficient two-objective layering, and a 50,000-point ranking benchmark. Every route a person
will ever compare rests on this. Grade first what would tell a person something false: a route
feasible when it isn't, "no route" when the search was cut short, a layer wrong, a known figure
where one is unknown.

## The product owner's scope decision (binding)
L0 leaves out the disk-backed archive with checkpoints and resume, and the separate child
process (the specification's section 22, "L0 deferrals"; the card's "Settled" note). The
archive is kept in memory under the caps; a crashed solve is a failed run, started again,
never a truncated result; a cancel reaches the search at its next check. Don't report their
absence as a finding. Do report anything that breaks what replaces them.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration and the
   R11 carve-out.
2. The brief, `task-13b-brief.md`, and the dispatch, `task-13b-dispatch.md` (its "Decisions
   that bind you" are the controller's rulings).
3. The implementer's report (unverified claims), `task-13b-report.md`. Judge its rulings and
   concerns:
   - the solve has its own workflow instead of a `RunTask` (RunTask is model-only; the
     database forbids a model on a keyless kind), and DBOS `application_version` is unchanged.
     `CLAUDE.md` says to change it when a workflow's step sequence changes: does a new
     workflow need it?
   - the rank stage's own 5-second limit and the new failure class `rank_limit_reached`;
   - `SOLVE_LIMIT_REACHED` and `NO_ROUTE_IN_BOUNDED_MODEL` as facts in the result, not errors;
   - words added to `vocabulary.ts` for the new failure class;
   - a result at the archive cap is 86 MB of JSON;
   - only the worker can open the sealed snapshot.
4. The diff, `.superpowers/sdd/l0-sprint-tasks/review-6c9e0a8..070aa89.diff` (4,114 lines;
   generated client and lockfiles excluded). Read your half's files in full, the rest as
   needed.
5. As needed: ADR 0016 (amended in the diff), ADR 0013, ADR 0006, the spec's section 12 (OPT-1)
   and section 17 (durable execution), and `CLAUDE.md`'s invariants.

## Half A: the search, the rank stage and the truth of the result
- `planning/search.py`, `planning/layers.py` (or wherever the layering lives), the benchmark,
  the oracle and the property tests.
- Is the efficient layering equal to Task 13a's iterative peeling on every instance that
  completes, with the full archive, dominated schedules included, and equal points not
  dominating each other? Is the property test strong enough to catch a wrong layer?
- Are the caps (30 s, 1,000,000 states, 50,000 feasible) and their exact stop reasons right,
  with no candidate silently lost before a cap stops the run?
- Does a truncated result never read as "no route"? Does `NO_ROUTE_IN_BOUNDED_MODEL` need
  complete coverage? Do unknown inputs leave a route unresolved, never passed?
- Is the rank stage's time accounted honestly (Task 13a's deferred M3: ranking was outside the
  30-second clock)?
- Does the cancel check stop the search promptly without recording a cancelled run as a
  truncated success?

## Half B: the run, the store and the API
- The run kind and its workflow, the worker composition, migration 0036, the API routes, the
  sealed snapshot and the result storage.
- Workflows carry IDs only; one bounded activity re-checks access; failures are classified
  from type and status with the message discarded; each transient failure class has one
  retry owner.
- The snapshot: taken at submission, sealed, immutable for the solve; a later edit can't
  change an in-flight solve. Expected version and `Idempotency-Key` through `run_idempotent`;
  the solve identity joins a solve under way rather than starting a second.
- Attempts and restarts: a crash leaves the attempt interrupted, a restart replaces it, a
  crash is never a truncated success.
- Cancel: the lock order in `CLAUDE.md` (ADR 0009 decision 15).
- Migration 0036: forward-only, row-level security, CHECKs that repeat the domain rules.
- The API returns codes and numbers only (R11); errors are `CareerwrightError` codes, never
  echoing input. A command's receipt holds no model output (there is none here: check
  nothing private leaks into a plaintext receipt).
- The 86 MB result: is it stored and served in a way that can fail a request, a transaction or
  the worker's memory now, before Task 14 pages it?

## Rules
- Read the branch with `git show wt-13b:<path>`. The worktree is at
  `/Users/darianraad/Code/careerpathoptimizer-wt/13b`; read only.
- Read-only everywhere. Implementers work in the main tree and in `careerpathoptimizer-wt/3b`.
- `make check` and `make acceptance` passed (the implementer's runs); don't re-run suites. One
  focused fast test is fine for a specific doubt
  (`cd /Users/darianraad/Code/careerpathoptimizer-wt/13b/backend && uv run --locked pytest <path>`).
  No integration or stack tests: they need the shared lock.
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`.

## Output
Write your review to `.superpowers/sdd/l0-sprint-tasks/task-13b-review-<half>.md` (`<half>` is
`search` for half A, `run` for half B), in the contract's format. Then reply with at most 10
lines: counts by severity, each Critical or Important item in one line, and the path.
