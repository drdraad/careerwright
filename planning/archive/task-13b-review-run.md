# Task 13b review, half B: the run, the store and the API

Reviewer: half B (run kind and workflow, worker composition, migration 0036, API routes, the
sealed snapshot, result storage). Branch `wt-13b`, 6c9e0a8..070aa89. I read in full:
`planning/solve_runs.py`, `planning/workflow.py`, `planning/solves.py`,
`planning/solve_records.py`, the `planning/store.py` diff, `r0036_route_solves.py`, the
`routes_planning.py` diff, the identity diffs (`records.py`, `runs.py`, `run_store.py`,
`failures.py`, `worker.py`), `careerwright/worker.py`, `vocabulary.ts`,
`tests/integration/test_route_solves.py`, `tests/domain/test_route_solve_records.py`, the
`worker_entry.py` and `test_planning_contract.py` diffs, and ADR 0016's amendment. Outside the
diff I made one check per named risk (listed with each finding). I ran no tests: reading
answered every doubt.

### Spec Compliance
- ✅ Spec compliant, with three rulings I agree with:
  - **Own workflow, not a `RunTask`.** `RunTask.call` takes a `Model` and every step of the
    model activity reserves spend and writes `model_attempts` (`identity/activity.py:110-130`),
    and the database forbids a model on a keyless kind. Following the acquisition's keyless
    precedent is the only way to meet "never a second call path" (ADR 0006). No model call
    path is added.
  - **DBOS `application_version` stays `careerwright-l0-1`.** ADR 0002 decision 9 ties the
    version to an existing workflow's step sequence, because DBOS replays in-flight workflows
    of the same version. No existing workflow's steps changed (`publish_outcome` is reused
    unchanged), and a new workflow has no in-flight runs under older code. No bump is needed.
  - **`SOLVE_LIMIT_REACHED` and `NO_ROUTE_IN_BOUNDED_MODEL` as result facts.** The spec lists
    them as envelope codes (section 18). It also says a truncated result *leads with the best
    trade-offs found*, which an error envelope can't carry. The register's API-02 row records
    this as a ruling. Snapshot at submission (ruling 4) is stronger than "when the run starts":
    it also protects a queued solve.
- ⚠️ Cannot verify from diff: the integration and acceptance runs (the implementer's; not
  re-run); the 86 MB, 2.4 s and 0.99 s figures; how the worker behaves under real concurrent
  load (see Important 1, which is from reading).

### Strengths
- The workflow carries the run ID only, and the integration test reads the DBOS journal to
  prove no snapshot, title or money is in it (`test_route_solves.py:233-242`).
- The activity follows the pinned pattern closely. The run row is locked first and only in
  `_prepare`. Access is re-checked before the snapshot is opened and again before storing.
  Failures are classified by class only. A store outage has one retry owner (the DBOS step),
  and a stored-then-crashed result is returned, never solved twice
  (`solve_runs.py:81-108, 141-159`).
- A crash is never a truncated result. An execution marks its predecessor's attempt
  `interrupted` and re-solves from the start, bounded at three attempts. This is tested with
  a real SIGKILL (`test_route_solves.py:396-415`).
- Lock order holds. The cancel poll is a plain read (`solve_runs.py:111-127`). `_store`
  takes no `FOR UPDATE` on the run. The API's `request_solve` locks the workspace first and
  takes no lock on an existing run row. Nothing waits in a cycle with `cancel_run`.
- Migration 0036 is forward-only. Its RLS gives the API insert and read on the solve and read
  on attempts and results, and gives the worker its own run only, with results gated by
  `authorised_run_workspace()`. Its CHECKs match the search's rules exactly: I checked each
  against `search.py:703-771`, and the archive and state counts can't exceed the caps because
  the limits are read before the append. A test drives the CHECKs with broken updates
  (`test_route_solves.py:435-474`).
- The solve identity is content-addressed. `input_version` hashes the inputs, caps, start,
  horizon, catalogue, variants and readiness versions (`compiler.py:380-408`), so a join can
  only join the same snapshot. Joins are scoped to the workspace and serialised by its lock.
- The receipt holds no result. Both the 202 and the 200 (join) answers are for an unsettled
  run, so `result` is null. The target title is already plaintext in `profile_versions`.
- R11 holds for what this task adds: codes, numbers, versions and the person's target title.
  Error details are codes (`no_options`, `planning_start_past`, the pack note's literals).

### Issues

#### Critical
None.

#### Important
1. **Two solves at once share one Python interpreter's CPU, so the largest realistic search
   stops at its wall-time limit when it would complete alone.**
   - Where: `identity/worker.py:60-67` starts every outbox entry at once with
     `DBOS.start_workflow`. DBOS runs each workflow in an unbounded thread pool (checked:
     `dbos/_dbos.py:636-641`, `max_workers` defaults to `sys.maxsize`). The search is
     CPU-bound pure Python on a wall clock (`solve_runs.py:172-174`, `rt.clock` is
     `time.monotonic`). CPython 3.12 runs one thread's bytecode at a time.
   - Why it matters: the product owner deferred the child process on Task 13a's measurement:
     the largest realistic L0 search takes about 26 s, against the 30 s limit
     (`task-13a-report.md:25-27`). That figure is for a solve running alone. With a second
     solve beside it (L0 has up to four targets), each gets about half the CPU. A 26 s search
     then stops at `wall_time_limit`. It is labelled `budget_truncated` and comes with
     narrowing advice: fewer concepts, one start, a shorter horizon. The label is honest. But
     the person would be told to drop options they didn't need to drop, and the same request
     made alone would have completed with exact layers. A separate process would have isolated
     the CPU. The in-worker replacement silently doesn't. Today's pack solves finish in
     milliseconds (every offering is set aside), so this bites once options become searchable
     (Task 12b).
   - Fix: run route solves one at a time. Either use a DBOS queue with concurrency 1 for
     `careerwright.route_solve`, or take a process-wide lock in the step before
     `search_archive`, so each search's 30 s starts when it actually runs. A waiting solve
     must still stop on cancel; the first `_evaluate` reads the cancel, so it will. Add a test
     that two solves asked together, each with a slow check, run one after the other, each
     with its own clock. Record the rule in ADR 0016 decision 12, or its known limits.

#### Minor
1. **A new request can join a solve the person has asked to stop.**
   - Where: `planning/store.py:187-196`. `unsettled_solve` matches `status IN ('queued',
     'running')` and ignores `run_cancellations`. A cancel only records a request; the run
     stays queued or running until the worker publishes it `cancelled`.
   - Effect: asking for the same solve straight after cancelling returns 200 with the doomed
     run, which then ends `cancelled`. The window is one worker pass (about 0.2 s) when the
     worker is up, but lasts as long as the worker is down.
   - Fix: add `AND NOT EXISTS (SELECT 1 FROM careerwright.run_cancellations c WHERE c.run_id =
     r.run_id)`, and a test (cancel with no worker running, ask again, expect 202 and a new
     run).
2. **A terminal run can keep an unfinished attempt.**
   - Where: `activity.publish` settles only `model_attempts` (`identity/activity.py:673`).
     So an attempt stays `outcome NULL, finished_at NULL` on a finished run when:
     - store-outage retries run out (`solve_runs.py:183-184`, `workflow.py:76`);
     - the worker loop publishes `cancelled` and the worker dies before the step's `_finish`;
     - `_prepare` returns `cancelled` after a crash, before `interrupt_solve_attempts` runs
       (`solve_runs.py:86-87` comes before `:99`);
     - an `IntegrityError` in `_store` rolls the attempt's end back.
   - Effect: nothing a person sees (`SolveOut.stage` is shown only while the run is running,
     `routes_planning.py:195-197`), but the table says "still running" for a finished solve.
   - Fix: settle open solve attempts as `interrupted` when the workflow publishes a terminal
     outcome, or interrupt before the cancelled return in `_prepare`.
3. **The expected version covers the planning inputs only.**
   - Where: `solves.py:104-108` checks `expected_inputs_version`. It then reads the
     profile's two caps and the capability evidence at their current versions, unrefused even
     if either moved since the person looked. The run pins `profile_version`
     (`solves.py:155`), so this can be detected afterwards, but `SolveOut` doesn't show the
     caps used.
   - This is ruling 7, disclosed. Question for Task 14: should the Routes chapter show the
     caps the snapshot read, or should the request also carry the profile version?
4. **The served result carries Careerwright-composed sentences in `Finding.reason`.**
   - Where: examples are "weekly availability is not stated", "the number or the exact amount
     of its payments is not stated" and "the deadline … has passed" (`checker.py:578, 647,
     860, 880, 891`). Task 13b is the first to serve them, through `SolveOut.result`
     (`routes_planning.py:192`).
   - This has precedent: `Fact.unknown` in `OptionsOut`, and the 12a review's note on
     `reason`. Task 14 must word findings from code, month and amount, and never show
     `reason`. Otherwise, replace the sentence reasons with codes.
5. **A result at the archive cap is one 86 MB sealed value.** It won't fail a request, a
   transaction or the worker now: there is no size CHECK, statement timeout or container
   memory limit, and the web proxy streams. But:
   - each GET decrypts, parses and re-serialises it in the API process. That is about 2.4 s
     of GIL-bound work, which stalls other API requests (`solves.py:192-200`);
   - master-key rotation loads every sealed output into one list
     (`run_store.py:494`, `cli.py:138`);
   - the family list repeats every route.
   Task 14 should page it and store or serve the families without repeating routes.
6. **Run-side paths with no test.** Three paths are untested:
   - the stored-then-crashed reuse path (`solve_runs.py:88-90`);
   - the three-attempt bound (`:100-101`);
   - access revoked while a solve runs (`:145-147`).

   No end-to-end test stores a `routes_found` result (concern 5): the round-trip with
   schedules is covered only at domain level (`test_route_solve_records.py:46-50`).
7. **Only the worker can open the snapshot** (concern 3): the API has `INSERT` but not
   `SELECT` on `run_inputs` (`r0005_interview_turns.py:62-68`). Decide before Task 14 how a
   chosen route's ledgers are recomputed on the same snapshot. A pack version can change in
   between, so recompiling from the stored versions won't reproduce it.
8. **`CLAUDE.md`'s planning layout line** doesn't yet name `planning.solves`,
   `planning.solve_runs` and `planning.workflow` (concern 4). The controller should add it at
   integration.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The run, store and API are sound. Workflows carry IDs only, a crash is never a
truncated result, a cancel stores nothing, the CHECKs repeat the search's rules, the lock order
holds and no result leaks into a receipt or journal. One Important remains: concurrent solves
share the worker's CPU and can turn a search that would complete into a truncated one with
needless narrowing advice. It is a small fix.
