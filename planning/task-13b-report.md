# Task 13b report: the route search as a run, bounded and ranked (Sprint 6b)

- Status: DONE_WITH_CONCERNS (concerns at the end).
- Worktree `/Users/darianraad/Code/careerpathoptimizer-wt/13b`, branch `wt-13b`, rebased onto
  `l0-local-release` at `6c9e0a8` (Task 6d slice A's fix round). Head:
  `070aa890911dabc56560cdd5da1052a04220b6bc`.
- Commits (`41f67a3..070aa89`):
  - `41f67a3` The route search in two stages, a cancel check, the efficient layering and the
    50,000-point benchmark (domain).
  - `0a8095c` The route search as a run: run kind, migration 0036, snapshot, workflow, worker,
    API, regenerated client, the new failure class's words.
  - `146209f` ADR 0016's Task 13b amendment and `docs/reviews/sprint-6.md` (6a and 6b).
  - `070aa89` Register (last commit, after the rebase).

## What I built

Scope as the product owner settled it on 31 October 2026: no disk-backed archive, checkpoints
or resume, and no child process (spec section 22). Everything else on the card is built.

**The search, in two stages** (`planning/search.py`, `planning/layers.py`):
- `search_archive`: the search stage. It runs under the M0 limits exactly as Task 13a measured
  them. The 30 s clock covers this stage only (`elapsed_ms`).
- `rank_archive`: the rank stage. It runs on its own clock (`rank_ms`) under its own limit,
  `RANK_SECONDS = 5`, checked before each of its four passes (layers, schedules, families,
  equal points). Reaching the limit raises `RankLimitReachedError`, so no result claims ranks
  it lacks. `search_routes` runs both stages (13a's callers are unchanged).
- A cancel check (`cancelled`) is read before each candidate and before each rank pass. A
  cancelled search raises `SearchCancelledError` and never returns a result.
- `layers.rank`: the efficient two-objective layering, one sort and one pass. Each layer keeps
  its tail; a point's layer is the first whose tail does not dominate it. 13a's `peel` stays as
  the reference it is qualified against.
- `check_scope` is now public, so the API refuses a beyond-bounds catalogue before any run.
- The search's `Coverage` enum is renamed `SearchCoverage` (the spec's `search_coverage`). It
  collided in OpenAPI with the acquisition's `Coverage` once both were served.

**The search as a run** (one keyless run kind with its own workflow):
- `identity`: `RunKind.ROUTE_SOLVE`; `KEYLESS_KINDS` includes it. `OUTBOUND_KINDS` (the
  acquisition only) names the keyless kinds that demo mode refuses, so demo workspaces may
  solve. `submit_keyless_run` now takes a pinned profile version and a sealed input. Also new:
  `FailureClass.RANK_LIMIT_REACHED`, `run_store.ROUTE_SOLVE_WORKFLOW`, and that workflow added
  to the errored-workflow reconciler.
- `planning/solve_records.py` (pure): `SolveSnapshot`, the sealed input (the `MonthlyInput`, the
  limits and the rank limit); `solve_identity`; the stage and attempt-outcome enums; the records.
- `planning/solves.py` (API side): `request_solve` locks the workspace and checks the planning
  inputs version the person saw. It then compiles the snapshot: the stored inputs through
  `prepare`, the profile's caps, the target's pack options, and the readiness basis with the
  person's outcome decisions. Next it checks scope, joins an unsettled solve with the same
  `solve_id` (200), or seals the snapshot into a new run (202). `solve_view` reads a solve.
- `planning/solve_runs.py` (worker side, one bounded activity), in order:
  - cancelled → stop;
  - an output already stored → return it;
  - mark running;
  - mark each unfinished attempt `interrupted`;
  - fail after three attempts;
  - re-check access;
  - open the snapshot and record an attempt;
  - search, record stage `ranking`, rank;
  - store the sealed output and the facts row, and finish the attempt, in one transaction.
  A store outage is transient: the DBOS step re-runs the activity, which solves again. The
  cancel request is polled at most every 0.2 s.
- `planning/workflow.py` (DBOS adapter, added to the architecture test's `ADAPTERS`): the step
  `careerwright.bounded_route_solve`, then the shared `careerwright.publish_outcome`. It is
  composed in `careerwright/worker.py`.
- `planning/store.py` (still planning's only SQL): the solve, its attempts and its result.
- Migration `r0036_route_solves.py`:
  - the run constraints extended (kind, no model, a pinned profile version, the outbox
    workflow name);
  - `route_solves`: the request, its versions and every limit, with CHECKs;
  - `route_solve_attempts`: stage and outcome;
  - `route_solve_results`: the facts, with CHECKs that repeat the search's rules;
  - row-level security and grants for the API (records, reads) and the worker (its own run).
- API (`routes_planning.py`): `POST /v1/workspaces/{id}/planning/solves` (an Idempotency-Key
  through `run_idempotent`) and `GET .../planning/solves/{run_id}` (`SolveOut`: the run, the
  request facts, `stage` while running, `attempts`, `code`, and `result` only when complete).
  Cancel is the existing `POST .../runs/{id}/cancel`.
- Web: the regenerated client, and words for `rank_limit_reached` in `FAILURE_CLASS`. The type
  checker requires them because the map is exhaustive. The web shows them only once Task 14
  shows a solve.
- `tools/rank_benchmark.py`: the 50,000-point benchmark.
- `docs/adr/0016-route-search-core.md`: the amendment, decisions 12 to 20.
- `docs/reviews/sprint-6.md`: 6a and 6b.
- `docs/requirements-register.md`: the rows below.

## Rulings (each costs little if wrong)

1. **No `RunTask`.** The brief says "one `RunTask` composed in the worker". But `RunTask` is the
   model activity's per-kind call: every step of that activity needs a model ID, a key, spend
   and `model_attempts` rows, and a database CHECK forbids a model ID on a keyless kind. So the
   solve follows the acquisition's precedent instead: a keyless kind with its own workflow,
   composed in `careerwright/worker.py`. It shares the run record, outbox, events, cancellation
   and publication. There is no second model-call path. Existing workflows' steps are
   unchanged, so `application_version` stays `careerwright-l0-1`.
2. **The rank stage has its own named limit** (`RANK_SECONDS = 5`), not time inside the 30 s.
   Giving ranking part of the search's 30 seconds would stop searches earlier than Task 13a
   measured. Reaching the limit fails the run `rank_limit_reached` (a new failure class) and
   keeps no result. It is far from binding: 0.99 s at the 50,000 cap.
3. **SOLVE_LIMIT_REACHED is a fact, not an error.** It is the `code` on a stopped search's
   result, beside its stop reason, instance size and narrowings. `NO_ROUTE_IN_BOUNDED_MODEL`
   is the code on a complete no-route result. The spec treats truncation as the normal state,
   so an error envelope would contradict it. "Best trade-offs found" is the web's words for
   `routes_found` (Task 14).
4. **The snapshot is taken when the solve is asked for** (the run's start) and sealed into it.
   The worker reads nothing else. This also keeps the exact input a chosen route's ledgers
   need.
5. **A target with no pack options is refused** (`VALIDATION_FAILED`, reason `no_options`). It is
   never searched over an empty catalogue into "no route".
6. **The planning start is a month**, this month or later; the horizon is 1 to 24. Both come
   from the request: Task 12a stores inputs horizon-free.
7. **The expected version is the planning inputs version.** The profile version is pinned on
   the run and the capability version recorded on the solve.
8. **Crash bound:** at most three attempts per run, then `unknown_failure`, since what killed
   the worker is not known.
9. **Demo workspaces may solve**: the solve needs no route out.

## Checks

On `0a8095c` (code), rebased onto `6c9e0a8`. The later commits change documents only.

- `make check`: exit 0, after the rebase.
  - Backend: ruff format and lint clean, mypy clean (354 files), 1,687 passed (371
    deselected), the fixture validator passed.
  - Web: client drift check passed, Biome clean (139 files), `tsc` clean, Vitest 379 tests in
    37 files.
  - Before the rebase it was also exit 0 (1,685 fast backend tests then).
- `make acceptance`: exit 0. Taken under the lock in one guarded command (it waited for the
  lock, ran, then removed the lock).
  - 371 integration and stack tests passed (8 min 34 s), the ten in `test_route_solves.py`
    among them.
  - The Storybook build completed.
  - 56 Playwright tests passed (6.8 min).
- Focused integration runs before that, each under the lock in one guarded command:
  `test_route_solves.py` 9 of 9, then the mutation run below.
- `uv run --locked python -m tools.rank_benchmark`:

  | Shape (50,000 points) | Efficient (s) | Peeling (s) | Equal |
  |---|---:|---:|---|
  | random | 0.026 | 0.052 | yes |
  | front | 0.005 | 0.012 | yes |
  | chain | 0.011 | 0.029 | yes |
  | equal | 0.008 | 0.005 | yes |
  | ties | 0.039 | 0.068 | yes |

  - The rank stage on a real 50,000-schedule archive took 988 ms (1,115 ms on a second run).
    The search took 42 s to fill the archive on a frozen clock.
  - That result is 86 MB of JSON (50,000 families, 320 equal points) and reads back in 2.4 s.

TDD evidence:
- **Efficient layering.** RED: `ImportError: cannot import name 'rank'`. GREEN: 9 passed. A
  mutant that let equal points dominate each other was caught by the property test.
- **Rank stage and cancellation.** RED: `ImportError: cannot import name 'RANK_SECONDS'`.
  GREEN: 64 passed (search, layers, pack).
- **Snapshot round-trip.** The test failed on real code with
  `ValidationError ... matrix.rows.0.required Extra inputs are not permitted`: a matrix row's
  derived `required` field does not read back. Fixed with `SolveSnapshot.sealed_text()`
  (`exclude_computed_fields`). GREEN.
- **The run side.** Its tests were written after the code, so there is no RED for those
  modules. As evidence I patched in two defects and ran them against a real worker:
  - a cancel poll that never reads the request: the attempt ended `'succeeded'`, not
    `'cancelled'`;
  - no interrupting of unfinished attempts: `[None, 'succeeded']`, not
    `['interrupted', 'succeeded']`.
  Both tests failed as they should. Both defects were reverted, and the reverted file was
  checked.

Live calls: none. Cost £0.

## Changed test inputs or assertions (disclosed)

- `test_route_search.py::test_a_complete_run_on_the_same_input_reproduces_the_same_result` now
  excludes `rank_ms` beside `elapsed_ms` (`TIMES`). The new field is the rank stage's time.
- `test_route_search.py`, `test_route_search_pack.py`, `test_route_oracle.py`: `Coverage` is
  now `SearchCoverage` (the rename); no assertion changed.
- `test_extraction.py::test_the_database_holds_extraction_labels_and_the_cap_to_the_code_s`
  reads run kinds from the latest migration that sets them, now `r0036`, not `r0031` (as its
  comment says).
- `tests/api/test_planning_contract.py::test_every_amount_the_options_serve_is_money` gains the
  case `SolveOut`.
- `tests/support/worker_entry.py` gains these test-only faults, configured like the existing
  ones:
  - `crash_at=mid_solve`;
  - `solve_check_delay_s`;
  - `solve_clock_jump` (`search` or `ranking`).
- Added tests:
  - `test_route_layers.py` (3);
  - `test_route_search.py` (5);
  - `test_route_oracle.py` (1 property);
  - `tests/tools/test_rank_benchmark.py` (3 tests, 7 cases);
  - `test_route_solve_records.py` (3);
  - `test_planning_contract.py` (1);
  - `tests/integration/test_route_solves.py` (10).

## Register

- Verified: OPT1-04, OPT1-05, OPT1-06, OPT1-07, OPT1-10, OPT1-11, OPT1-12, LIMITS-01 to
  LIMITS-05, STATE-03.
- Task 13b part recorded, the row still planned:
  - OPT1-03 and OPT1-09: their deferred parts;
  - LIMITS-06: its L0 form verified;
  - OPT1-15: Tasks 14 and 15;
  - DUR-05: only "a model request already sent is not interrupted" remains open, and every
    owner's part is now done, so the controller may close it;
  - DUR-07: research's snapshot;
  - API-02: the other codes.
- Section 7 gains the search's two L0 deferrals.

## Concerns

1. **The rank stage's limit has a new failure class.** The web's exhaustive map required words
   for it in `vocabulary.ts`, which Task 6d is also editing. The two edits did not overlap at
   the rebase.
2. **Results at the archive cap are large.** One is 86 MB of JSON, sealed into one
   `run_outputs` row and served whole by the GET. Realistic L0 results, P01's limits included,
   hold about a thousand schedules or fewer, but Task 14 should page. The family list repeats
   every route.
3. **Only the worker can open the snapshot.** The API seals it and has no grant to read it
   back. Task 14 will need a way to recompute a chosen route's ledgers on the same snapshot.
4. **`CLAUDE.md`'s planning layout line is now incomplete.** I left it alone because the main
   tree edits it. Suggested addition: "and route solves as runs (`planning.solves`,
   `planning.solve_runs`, `planning.workflow`, ADR 0016's Task 13b amendment)".
5. **Real pack solves end `unresolved`.** Every pack offering lacks a fact the search needs, so
   the integration tests' complete results show no route and `layers_exact` true. Truncation
   is tested through a worker whose clock jumps. Routes found end to end are covered at the
   domain level only, until Task 12b lets the person supply the missing facts.
6. **Edit discipline.** Two non-content operations used the shell:
   - the migration file's rename to 0036 (`mv`, after its content was edited with Edit);
   - an empty `cat >>` append that changed nothing.
   Every source change used Edit or Write, or the project's formatter and generator.

## Paths a reviewer can skip

`apps/web/src/generated/` (the regenerated client).

## Fix round 1

- Status: DONE_WITH_CONCERNS (concerns at the end of this section).
- Fix base `070aa89`. Rebased onto `l0-local-release` at `f7f0e4d` (Task 3b integrated).
  Head: `99a8992f39296b162ecf991390ab27320a630800`.
- Commits, in order:
  - `b85f8dc`: the narrowings from the stop reason; the deep replay test; a stopped search
    with routes and its code; the benchmark's "one run";
  - `c8d9243`: refactor: the cancel read injected behind a context manager (no behaviour
    change);
  - `19fa282`: the cancel read on a thread of its own;
  - `0e24115`: no finding's `reason` serialized; the regenerated client;
  - `e7116b2`: one solve at a time; no join to a cancelled solve; attempts settled at
    publication; the run-side tests;
  - `0a41a4a`, `98fe787`: ADR 0016;
  - `fa3c843`: attempt outcome comments;
  - `f496309`: a solve cancelled while it waits; two tests' register tags;
  - `7d169db`: the Sprint 6 review's checks;
  - `99a8992`: the register (last).
- No other migration took 0036, so it keeps its number. It is unchanged in this round.
- DBOS `application_version` stays `careerwright-l0-1`. One solve at a time is a lock in the
  activity, not a DBOS queue, so no workflow's step sequence changed (ADR 0016 decision 22).
- The original register commit (`6eb5fde`, was `070aa89`) is still mid-branch, where the
  original implementer put it. This round's register edits are the last commit. The rebase
  left the register without conflicts.

### Each finding, its fix and its test

1. **Search half, Important 1: the narrowings.**
   - Fix: `_narrowings(size, stop)` names them from the stop reason, as ruled:
     - the state or archive limit: fewer concepts, or one start;
     - the time limit: those two and a shorter horizon.
   - Each is named only where the instance can still take it: a dimension already at one is
     never named. `Narrowing`'s description now says they are what could help, never a
     promise. ADR 0016 decision 21; decision 8 points to it.
   - Tests (`test_route_search.py`):
     - `test_a_state_or_archive_limit_names_fewer_concepts_or_one_start_never_a_shorter_horizon`
       (both limits);
     - `test_the_time_limit_names_a_shorter_horizon_beside_fewer_concepts_and_one_start`;
     - `test_a_narrowing_the_instance_is_already_at_is_never_named`.
   - RED: the state and archive cases failed with `Left contains one more item:
     <Narrowing.SHORTER_HORIZON>` (2 failed, 2 passed). The time-limit and "already at one"
     cases held already and now guard the rule.
   - GREEN: 72 passed across the search, oracle, pack and contract files.
2. **Run half, Important 1: two solves at once.**
   - Ruling: a process-wide lock in `solve_runs.execute` (`_ONE_AT_A_TIME`), taken before
     `_prepare`. While a solve waits, its run stays `queued` and records no attempt, and its
     clocks start only when it runs. It reads the cancel while it waits and leaves on one.
   - Why not a DBOS queue: DBOS 3.3's queues are registered in its system database at
     launch, and using one would change the outbox's dispatch. L0 runs one worker process.
   - Known limit (ADR 0016 decision 22): a second worker process would need a queue. At
     shutdown a waiting solve never starts, because since Task 3b the worker ends its process
     as soon as DBOS is destroyed.
   - Test: `test_route_solves.py::test_two_solves_asked_together_run_one_at_a_time_each_on_its_own_clock`.
     Two different solves, a worker with 0.5 s checks. It checks that:
     - while one searches, the other is `queued` with no attempt;
     - the later attempt starts after the earlier one ends;
     - the later solve's stored `search_ms` fits inside its own attempt.
   - RED: `assert [] == ['queued']` (both started at once). GREEN: passed.
   - Added after the acceptance run: `test_a_solve_cancelled_while_it_waits_its_turn_never_runs`.
     It ends `cancelled` with no attempt while the other still searches. It passes, but would
     also pass without the wait's own cancel check, because `_prepare` refuses a cancelled
     run. It guards the behaviour, not the early exit from the wait.
3. **Run half, Minor 1: a request joining a cancelled solve.**
   - Fix: `store.unsettled_solve` skips a run with a recorded cancellation. ADR 0016
     decision 14.
   - Test: `test_a_solve_asked_for_again_after_its_cancel_is_a_new_run`. With no worker:
     cancel, ask again, expect 202 and a new run. It then cancels the new run, so no later
     test's worker starts it.
   - RED: the second request answered 200 with the cancelled, still queued run. GREEN:
     passed.
4. **Run half, Minor 2: unfinished attempts on a finished run.**
   - Fix: `identity.activity.publish` calls a per-kind settler from
     `ActivityRuntime.settle_attempts` inside its own transaction.
     - The default is empty, and identity still imports nothing of planning.
     - `careerwright.worker` composes
       `SETTLE_ATTEMPTS = {ROUTE_SOLVE: solve_runs.settle_attempts}`, and the test worker
       composes the same mapping.
   - An unfinished attempt ends `cancelled` on a cancelled run, else `interrupted`. So a
     normal cancel, where the worker loop publishes before the search's next check, still
     reads `cancelled`.
   - `store.interrupt_solve_attempts` became
     `end_unfinished_solve_attempts(tx, run_id, outcome)`.
   - Lock order: `publish` still locks the run row first. The solve's own transactions never
     wait on the run row while they hold an attempt row, so there is no cycle. ADR 0016
     decision 15.
   - Tests, one per path the review listed (all four GREEN):
     - the worker loop publishes `cancelled` and the worker dies before the step's end:
       `test_a_cancel_published_as_the_worker_dies_leaves_no_attempt_unfinished` (10 s
       checks; SIGKILL as soon as the run reads `cancelled`). RED:
       `assert None == 'cancelled'`.
     - `_prepare` returns `cancelled` after a crash:
       `test_a_solve_cancelled_after_a_crash_leaves_no_attempt_unfinished`. RED:
       `assert [None] == ['cancelled']`.
     - the store-outage retries run out:
       `test_a_solve_whose_store_stays_away_fails_and_leaves_no_attempt_unfinished` (the
       worker's role cut for 15 s mid-search). RED:
       `(None, False) == ('interrupted', True)`.
     - the store transaction rolls the attempt's end back:
       `test_a_solve_whose_result_cannot_be_stored_fails_and_leaves_no_attempt_unfinished`
       (new test-only fault `solve_store_fails`). RED: `[None] == ['interrupted']`.
5. **Run half, Minor 4 (R11): no sentence Careerwright composed is served.**
   - Fix: `Finding.reason` is now `Field(default=None, exclude=True)`.
     - It stays the checker's note in memory; the search's prerequisite rule still reads it.
     - It is never serialized, so it is neither sealed nor served, and the OpenAPI schema no
       longer has it.
     - Client regenerated. ADR 0016 decision 20.
   - Why not an API-only result model: it would mean redeclaring the 33-field `SearchResult`
     and the 13-field `Schedule`, or overriding their list fields with type ignores. The only
     place a `Finding` is serialized is the sealed solve result, and that exists to be served.
   - Test: `tests/api/test_planning_contract.py::test_a_served_solve_result_carries_no_sentence_careerwright_composed`.
     It checks that:
     - no schema reachable from `SolveOut.result` has `reason`;
     - the sealed JSON of a blocking `limit_unknown` is exactly its code and facts;
     - the finding in memory keeps `direct_spend_cap`.
   - RED: `assert ['Finding'] == []`. GREEN: passed. The end-to-end routes test also checks
     that the served result has no `reason` key anywhere.
   - Disclosed: my first version of this test imported an API-side converter, which I then
     dropped (its RED was an `ImportError`). I rewrote the test before writing any fix and
     took its RED again, as above.
6. **Run half, Minor 6: run paths with no test.** All new, in `test_route_solves.py`. Each
   passes on the old code too: these were gaps, not defects.
   - `test_a_result_stored_before_a_crash_is_published_and_never_solved_again` (new crash
     point `after_solve_stored`). One attempt, `succeeded`; the run completes with the stored
     output; one results row.
   - `test_a_solve_whose_worker_keeps_crashing_fails_after_three_attempts`. Three
     `mid_solve` crashes, then a normal worker: the run fails `unknown_failure`, the attempts
     are `interrupted` three times, and nothing is stored.
   - `test_access_revoked_while_a_solve_runs_fails_it_and_stores_nothing`. A fresh person,
     revoked mid-search: the run fails `access_revoked`, the attempt is `failed`, and nothing
     is stored.
   - `test_a_solve_that_finds_routes_stores_and_serves_them_with_their_schedules`.
     - The person records synthetic evidence at the required level for the Data quality
       analyst's three required rows, so the empty route reaches readiness at once.
     - The solve is stored and served `routes_found`, complete, with `layers_exact`.
     - It has one schedule (route `[]`, 0 months, layer 1, its family listed), and the
       pack's offerings are still set aside.
     - The facts row says `routes_found`, archived 1.
7. **Search half, Minor 1: the cancel read on the search's clock.**
   - Fix: `solve_runs.cancel_watch`. A daemon thread reads the request every 0.2 s and sets
     a `threading.Event`; the search's check reads only the event.
     - A failed read is never a cancel. It is logged by class, once per run of failures, and
       tried again.
     - One watch spans the whole execution, the wait for a turn included. ADR 0016
       decision 19.
   - I made a refactor commit first (the read injected behind a context manager, the same
     inline read), so the tests could fail on the old behaviour.
   - Tests (new file `tests/domain/test_route_solve_runs.py`):
     - `test_a_slow_store_is_never_charged_to_the_search_s_clock` (each read takes 1.5 s;
       the search's limit is 1 s);
     - `test_a_cancel_the_watch_reads_stops_the_search_at_its_next_check`;
     - `test_a_failed_read_is_never_a_cancel_and_the_watch_reads_again`.
   - RED, against the refactor:
     - the slow-store test failed with `RankLimitReachedError`. That is worse than the review
       said: the inline read charged each slow read to the search's clock, which stopped at
       its time limit, and then to the rank stage's, which failed the run;
     - the failed-read test timed out waiting for a background read.
   - GREEN: 3 passed in 0.9 s.
8. **Search half, Minor 2: two test gaps.** Both pass on the old code.
   - `test_route_search.py::test_a_state_limited_run_replays_exactly_and_keeps_every_schedule_it_met`.
     **Changed test input (disclosed):** it used the A to I fixture, which has only singles.
     It now uses four free courses `c0..c3` with `max_states=9`, stopped past the singles
     inside c0's pairs. It asserts:
     - the hand-worked archive: `c0`, `c1`, `c2`, `c3`, `c0 c1`, `c0 c1 c2`, `c0 c1 c2 c3`,
       `c0 c1 c3`;
     - five unexplored branches;
     - the replay;
     - that it is a prefix of the complete run's 15 schedules.
   - `test_planning_contract.py::test_a_solve_s_code_names_a_stopped_search_or_a_proven_no_route_and_nothing_else`
     gains a stopped search that found routes (`max_states=2`: the £5 course archived),
     carrying `SOLVE_LIMIT_REACHED`. The nothing-found case now asserts its outcome too.
9. **Search half, Minor 3: the benchmark's "best of three".**
   - Fix: the docstring and the table's heading say the layerings are the best of three and
     the rank stage at the cap is one run. ADR 0016's consequences say the same.
   - Test: `test_the_table_names_each_shape_and_the_rank_stage_beside_its_limit` gains that
     line.
   - RED: the assertion failed on `...; best of 3.`. GREEN: 7 passed.
   - Re-run with `--points-only`: both layerings agree on all five shapes, each under 0.05 s.

Also changed:
- `AttemptOutcome`'s comments name every way an attempt is interrupted or cancelled.
- The Sprint 6 review: its narrowing line, accepted limits and checks.
- ADR 0016: decisions 8, 14, 15, 19 and 20 amended; 21 and 22 added.

### Changed test inputs or assertions (disclosed)

- The replay test's input (item 8, above).
- `test_planning_contract.py`:
  - `_solved` now takes `direct_cap: int | None`, for item 5;
  - the nothing-found case's outcome assertion is added;
  - one new case and one new test (items 5 and 8).
- `test_rank_benchmark.py`: one assertion added (item 9).
- `tests/support/worker_entry.py`:
  - test-only fault points `after_solve_stored` (a crash) and `solve_store_fails` (not a
    crash);
  - its runtime takes `settle_attempts=SETTLE_ATTEMPTS`.
- `test_route_solves.py`:
  - new helpers `no_reason_anywhere` and `Person.ready_for_the_target`, and the new tests
    above. No existing assertion in it changed.
  - An isolation fix, found on my first GREEN run. The "asked again after a cancel" test left
    a fresh queued solve. The next test's worker (one solve at a time, 10 s checks) ran it
    first, so that test's own solve timed out. The test now cancels the run it leaves.
- Register tags: the slow-store and two-solves tests are tagged OPT1-04 and LIMITS-02, the
  rows that cite them.

### Commands and output

- Focused domain and API runs, as above, with `uv run --locked pytest <files> -q`.
- Integration, each under the acceptance lock in one guarded command
  (`mkdir <lock> && { uv run --locked pytest -m integration tests/integration/test_route_solves.py ...; rmdir <lock>; }`):
  - RED run on the old code with the new tests: 6 failed (the six behaviour tests above),
    14 passed (67.8 s). A second run of four of them with `--tb=line` captured the messages
    quoted above;
  - first GREEN run: 19 passed, 1 failed (the isolation fault above);
  - after the fix: 20 passed (67.9 s);
  - after the last test and the tag change: 21 passed (74.8 s).
- After the rebase:
  - `make check`: exit 0. Backend: ruff format and lint clean, mypy clean (360 files), 1,740
    passed (390 deselected), the fixture validator passed. Web: the generated API client
    matches the backend's OpenAPI document; Biome checked 146 files; `tsc` clean; Vitest 391
    tests in 40 files.
  - `make acceptance`, once, under the lock in one guarded command: exit 0. 407 integration
    and stack tests passed (9 min 42 s), the 20 in `test_route_solves.py` among them; the
    Storybook build completed; 56 Playwright tests passed (9.3 min). It passed first time, so
    no second run was needed.
  - After acceptance I added one test and changed two tests' tags (test code only). So:
    - `test_route_solves.py` again under the lock: 21 passed;
    - `make check` again: exit 0, 1,740 passed (391 deselected), Vitest 391.
  - The commits after that change documents only.
- Live calls: none. Cost £0.

### Register (the last commit)

Fix round 1 evidence was added to these rows:
- OPT1-03: a result stored before a crash, the three-attempt bound, a new run after a cancel;
- OPT1-04: one solve at a time, and the cancel read off the clock;
- OPT1-05: attempts settled however a run ends, and access revoked mid-solve;
- OPT1-06: a `routes_found` result stored and served end to end;
- OPT1-07: no finding's `reason` sealed or served;
- OPT1-15: the narrowings from the stop reason, and a stopped search with routes and its code;
- LIMITS-01: the deep replay;
- LIMITS-02: another solve or a slow store never charged to the 30 seconds;
- DUR-05: the cancel thread, a new run after a cancel, cancels during a crash or while
  waiting.

No row's status changed.

### Concerns

1. **The sealed result no longer holds findings' reasons either** (item 5). Some reasons
   carried identifiers: the gate a prerequisite needs, which limit is unknown, a scheme's ID.
   If Task 14 needs one, it should become a typed field of its own. ADR 0016's known limits
   say so.
2. **One solve at a time is per worker process.** A second worker process would need a DBOS
   queue (ADR 0016 decision 22).
3. **Edit discipline.** I used `git checkout --theirs` on two generated files during the
   rebase, to clear their conflict markers before regenerating them with `pnpm run
   generate`. I used `git reset --soft HEAD~1` once, on my own unpushed register commit, so
   that a late ADR correction could come before it and the register stays last. Every source
   change used Edit or Write, or the project's formatter and generator.

Paths a reviewer can skip: `apps/web/src/generated/`.

## Rebase onto 21a397d

- `wt-13b` is rebased onto `l0-local-release` at `21a397d` (Task 6d slice B). New head:
  `29072d11b93dd821717a70c44e490fd0db907aa8`.
- **Migration renumbered, as R15 says.** Task 6d slice B's `r0036_uk_titles.py` took 0036,
  so this task's migration is now `r0037_route_solves.py`: revision `0037`, `down_revision`
  `"0036"`.
  - Its content is otherwise unchanged. The rename was a `git mv`; the revision lines were
    edited with Edit.
  - The one other reference was `tests/domain/test_extraction.py`, which reads the run kinds
    from that migration; it now imports `r0037`.
  - The migration tests read the head from Alembic, which now has one head, 0037.
  - Commit `80586cf`. The earlier commits still name the file 0036, so the history between
    the rebase point and `80586cf` has two 0036 revisions.
- **Conflicts.**
  - The generated client conflicted once, at the first run-kind commit. I took one side to
    clear the markers, then ran `pnpm run generate`.
  - `vocabulary.ts` merged without conflict. Its diff against `21a397d` is only this task's
    `rank_limit_reached` entry, so all of Task 6d's words are kept.
  - The register merged without conflict. Its diff against `21a397d` touches only this
    task's rows (and section 7's search deferrals), none of which Task 6d changed.
  - The register commit is still last (`29072d1`). I moved my own unpushed register commit
    after the renumber with `git reset --soft HEAD~1`.
- No other changes.
- **Checks on the new head:**
  - `make check`: exit 0. Backend: ruff and mypy clean (363 files), 1,750 passed (399
    deselected), the fixture validator passed. Web: the client matches the OpenAPI document;
    Biome checked 149 files; `tsc` clean; Vitest 408 tests in 41 files.
  - `make acceptance`, once, under the lock in one guarded command: exit 0. 416 integration
    and stack tests passed (9 min 42 s), `test_migrations.py`'s 9 and `test_route_solves.py`'s
    21 among them. The Storybook build completed, and 58 Playwright tests passed (7.0 min).
- Live calls: none.
