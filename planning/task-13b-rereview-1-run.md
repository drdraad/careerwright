# Task 13b re-review 1, half B: the run, the store and the API

Scope: fix round 1 (6eb5fde..99a8992 on `wt-13b`, rebased onto f7f0e4d), fix-list items 2 to 6.
I read the run-side diffs in full: `solve_runs.py`, `store.py`, `solves.py`, `solve_records.py`,
`identity/activity.py`, `careerwright/worker.py`, `checker.py`'s `Finding`, `worker_entry.py`,
the new tests in `test_route_solves.py`, `test_route_solve_runs.py` and
`test_planning_contract.py`, and ADR 0016's amendments. Outside the diff I made one check per
named risk: shutdown in `identity/worker.py`, the one worker service in `compose.yaml`, the
`needs` list in `planning/inputs.py`, and where a `Finding` can reach the served result in
`search.py`. I ran no tests.

### Spec Compliance
- ✅ Spec compliant. Items 2 to 6 are each addressed as ruled. Two of the implementer's
  decisions hold:
  - **A lock, not a DBOS queue.** The ruling allowed either. A lock changes no workflow's step
    sequence and no dispatch, so `application_version` correctly stays `careerwright-l0-1`.
  - **One at a time per worker process only.** That is enough for L0: `compose.yaml:112` runs
    one worker service, and Docker stops the old container before it starts the new one.
    ADR 0016 decision 22 records that a second process would need a queue.
- ⚠️ Cannot verify from diff: the integration and acceptance runs (the implementer's, not
  re-run).

### Each item

**Item 2 (Important 1): two solves at once. Addressed.**
- Where:
  - `solve_runs.py:66` holds a process-wide `_ONE_AT_A_TIME` lock.
  - `solve_runs.py:246-265`: `execute` takes its turn before `_prepare`. So a waiting run
    stays `queued`, records no attempt, and its search and rank clocks start only once it
    runs (`_Search.__init__` reads the clock).
  - Test: `test_route_solves.py:562`. Its real guard is "the other is queued with no attempt"
    and "the later attempt starts after the earlier ends". The `search_ms` check is weak but
    harmless.
- New-breakage checks, all clean:
  - **A waiting solve and a cancel.** The watch thread sets the event within one poll, and
    `_take_turn` re-reads it every 0.2 s (`:248-250`). The step then returns `cancelled`
    without ever taking the lock. If that early exit were missing, the worker loop would
    still publish the run `cancelled`, and `_prepare` would refuse it once it got the lock.
  - **Shutdown while waiting.** `identity/worker.py` calls `os._exit(0)` after
    `DBOS.destroy()`, so waiting threads die with the process. A waiting run is still
    `queued` with no attempt, and DBOS recovers it on the next start. The running solve's
    attempt is marked `interrupted` by the next execution, or by publication.
  - **Exception safety.** The lock is released in `finally`. The cancelled-wait path never
    acquired it.
  - **Lock order.** The threading lock is held only around `_prepare` and `_solve`, never
    around publication. No database lock is held while waiting for it.

**Item 3 (Minor 1): a new request joining a cancelled solve. Addressed.**
- `store.py:187-200` skips a run with a recorded cancellation. The API role can read
  `run_cancellations` under its workspace policy (`r0013_evidence_acquisition.py:73-77`).
- Test: `test_route_solves.py:613`.

**Item 4 (Minor 2): unfinished attempts on a finished run. Addressed.**
- Where:
  - `identity/activity.py:87, 154, 680-682` call a per-kind settler inside `publish`'s
    transaction. Identity still imports nothing of planning.
  - `solve_runs.py:167-176` is the settler: `cancelled` on a cancelled run, else
    `interrupted`.
  - `careerwright/worker.py:74-77, 137` composes it; so does the test worker.
  - It covers the workflow's publish, the worker loop's cancel and the reconciler, which all
    use one runtime.
- Tests: `:632`, `:650`, `:667`, `:689`, one per path I listed.
- Lock order, checked:
  - `publish` locks the run row first, then the attempt rows.
  - `_ranking` and `_finish` touch only the attempt row.
  - `_store` takes its run-row key share (the output's foreign key) before any attempt-row
    lock.
  - So nothing waits in a cycle.
- One harmless race: if the worker loop publishes `cancelled` while `_store` is committing,
  the attempt can read `cancelled` with a results row beside it. The run stays cancelled and
  no result is served. That matches DUR-05's "a step under way finishes, its result is kept,
  the run stays cancelled".

**Item 5 (Minor 4, R11): no composed sentence served. Addressed.**
- `checker.py:173` marks `reason` as `exclude=True`. No API serializes a `Finding` except
  through `SolveOut`, and the client no longer has the field.
- Tests: `test_planning_contract.py` (the schema walk and a sealed `limit_unknown`), and
  `no_reason_anywhere` in the end-to-end routes test.

The coordinator asked whether the stored result loses an identifier Task 14 needs. It loses
two, not the three the report and ADR name:
- Only findings on the empty route and on archived schedules reach the result. A single
  option's findings are reduced to codes in `set_aside`. A route with a violation or an
  unknown is never archived.
- So the gate, the scheme ID, the exclusive group and the concept never reached the served
  result.
- The two that did, and are now lost:
  - **Which limit is unknown.** `LIMIT_UNKNOWN` in `blocking_inputs` (`checker.py:1019`) can
    appear up to three times: direct-spend cap, monthly payment cap, reserve. The copies now
    read identically.
  - **Which debts' repayments are above the cap.** `REPAYMENTS_ABOVE_PAYMENT_CAP` in
    `starting_violations` (`checker.py:1034-1043`) keeps its month, amount and limit, but
    loses the debt IDs.

**Ruling suggestion: a Task 14 typed field, not a defect now.**
- No person sees a solve yet.
- The planning-inputs view already names each unstated limit with its effect, for the current
  version (`inputs.py:381-383`).
- Solves are cheap to recompute, and L0 has no released results to preserve.
- But Task 14's dispatch should require typed fields, such as `limit_name` and `debt_ids`,
  before the Routes chapter words `blocking_inputs` or `starting_violations` from a stored
  result. Today's served list can show "a limit is unknown" up to three times, with no way to
  say which.

**Item 6 (Minor 6): untested run paths. Addressed.** Tests: `test_route_solves.py:460`
(stored, then a crash), `:481` (three attempts), `:503` (access revoked mid-solve) and `:527`
(`routes_found`, stored and served with its schedule).

### Issues

#### Critical
None.

#### Important
None.

#### Minor
1. **The solve slot isn't first come, first served** (`solve_runs.py:248`).
   `Lock.acquire(timeout=…)` in a loop has no queue order. A solve asked later can run
   first, and in principle a waiter can be overtaken repeatedly. With L0's four targets at
   most this is harmless. If Task 14 shows a waiting position, it can't promise an order.
2. **The ADR and report overstate what the excluded `reason` lost.** ADR 0016's known limits
   and report concern 1 name "the gate a prerequisite needs, which limit is unknown, a
   scheme's ID". Only "which limit is unknown" and "which debts" reached the served result
   (above). Correct the sentence so Task 14 adds the right two fields.
3. **`test_route_solve_records.py:46-50` ("a stored result reads back exactly") is now true
   only by accident.** The trace instance has no served finding with a `reason`. A result
   whose `blocking_inputs` hold `limit_unknown` no longer reads back equal, because the
   in-memory `reason` is dropped. Use such an input and compare excluding `reason`, or state
   the documented loss in the test.
4. **`test_route_solves.py:590` (a cancel while waiting) doesn't show that the step leaves
   its wait early.** The implementer disclosed this: the worker loop publishes the run
   `cancelled` either way. To guard the early exit, also check that the waiting workflow's
   DBOS status, or its step output, ended while the other solve still runs.

### Assessment
**Task quality:** Approved (run half)
**Reasoning:** Each fix-list item for this half is addressed with a test that fails without
it. The changed code adds no new lock-order, shutdown or cancel hazard. The two identifiers
the excluded `reason` drops (which limit is unknown, which debts) should be typed fields that
Task 14's dispatch requires. That is not a defect today.
