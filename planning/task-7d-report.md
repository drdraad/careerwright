# Task 7d report: the cancellation lock order

BASE 84dc858, branch `l0-local-release`. Commits:

- `c75b877` Record a cancel's requests before locking the workspace's row (Task 7d): the fix
  and its regression test.
- `37b2eeb` State the cancellation lock order exactly in ADR 0009 and the register (Task 7d).

No live calls (R5: none to ledger). DBOS `application_version` stays `nessa-l0-1`: no
workflow's step sequence changed (only the order of statements inside the API's cancel
transaction).

## What was wrong (reproduced first)

`identity.runs.cancel_run` took the run's cancellation lock, then locked the workspace's row
`FOR UPDATE`, then recorded each request (`run_cancellations`, whose foreign key takes a
key-share lock on the run's row) and wrote its event. A worker transaction locks a run's row
`FOR UPDATE` as its first lock and then writes the run's event, which updates the workspace's
row (`activity._prepare`, `activity.publish`, `acquisition.acquire_target`'s first
transaction, `acquisition.publish_acquisition` through `publish`). The cancel then waited for
the run's row while holding the workspace's row, and the worker waited for the workspace's
row while holding the run's row. PostgreSQL ended the cancel with `deadlock detected`
(40P01), which `nessa.db` maps to `StoreUnavailableError`, answered `503 STORE_UNAVAILABLE`.
The acquisition cascade asks for up to five more runs, each another chance.

## What changed

- `backend/src/nessa/identity/runs.py` `cancel_run`: lock order is now the cancellation lock,
  then the runs' rows, then the workspace's row. It checks the workspace is visible without
  locking it (same `workspace_not_found` answer as before), reads the run and its unsettled
  started runs as before, records every request first, then locks the workspace's row
  (`visible_workspace(..., lock=True)`, the command convention kept, now after the run rows)
  and writes the `run.cancel_requested` events for the requests it recorded, in the same
  order as before. Answer, receipts, events and `cancellation_requested` are unchanged. The
  docstring states the order and why.
- `backend/src/nessa/identity/run_store.py` `lock_started_runs`: docstring now says the
  cancel takes it before any run's row or the workspace's row.
- `backend/tests/integration/test_page_extraction.py`: new
  `test_a_cancel_while_the_worker_writes_a_run_s_event_ends_without_a_store_error`
  (`DUR-05`), parametrised `a_run` (a connection-check run) and `an_acquisition` (an
  acquisition with two started extraction runs; the worker holds the last one). Two
  connections: a worker-role transaction (`run_transaction` as `nessa_worker`, the worker's
  own adapters) locks the run's row and marks it running, as `_prepare` opens; the API's
  cancel runs in a thread; once `pg_stat_activity` shows the cancel's `run_cancellations`
  insert waiting on a transaction lock, the worker's transaction writes the run's event and
  commits. Asserts: the cancel answers 202 naming every run asked for, every request is
  recorded, and the worker's transaction committed with its `running` event.
- `docs/adr/0009-evidence-acquisition.md`: decision 15 gains a *Lock order* bullet stating
  exactly what holds (below), and the cancellation bullet says the cancel takes the
  cancellation lock before any run's row; the open item is rewritten as fixed by Task 7d.
- `docs/requirements-register.md` DUR-05: Task 7d evidence added; the lock pattern removed
  from its open items. DUR-05 stays `planned` (the solver's child process is T13b). No other
  row named the pattern.

## Rulings

1. **Reorder the cancel; do not make the worker take the cancellation lock.** The inversion
   is in one place: the cancel is the only transaction that takes the workspace's row and
   then waits for a run's row held `FOR UPDATE`. Every worker transaction that locks a run's
   row `FOR UPDATE` already does it as its first lock (all four call sites checked), so "a
   run's row before its workspace's row" is the order the worker keeps; the cancel now
   keeps it too. The alternative (every worker transaction takes the run's cancellation lock
   first, and the cascade's cancel takes each started run's lock too) touches every worker
   transaction and would still leave the row order inverted. No retry loop was added.
2. **Keep the cancel's `FOR UPDATE` on the workspace's row, after the requests.** Every
   consequential command locks its workspace's row; the cancel still does, before its events
   and receipt. Dropping it would also move where the fix-round-4 N1 test sees the cancel
   wait (it waits for `FOR UPDATE`), and that test passes unchanged with the lock moved.
3. **The worker side of the regression test is the worker's own transaction shape, not
   `activity.publish` behind a gate.** Gating `publish` needs a third connection and a
   fabricated unfinished attempt or partial. The test runs the worker's adapters under the
   worker role in the worker's order (run's row, then the event), which is exactly the
   pattern the review and ADR describe, and is deterministic: it cannot pass without the
   cancel actually waiting at the run's row (its `wait_for`), and it fails on every try
   before the change.
4. **Test placement:** beside the N1 cancel test in `test_page_extraction.py`, which already
   has the scenario with a stored key, the cascade helpers (`_unread_acquisition`,
   `_attempt`, `_submit_as_worker`), `_cancel`, `_lock_waits` and `_worker_engine`.

## Exactly what holds (ADR 0009 decision 15, *Lock order*)

- The run's cancellation lock is the first lock of each transaction that takes it (the
  cancel; an acquisition's recording whose page is model-readable, before
  `lock_workspace_records`).
- `FOR UPDATE` on a run's row, the only lock a key share on it waits for at run time, is
  taken only by the worker, as its transaction's first lock; that run's events come after.
- The cancel takes its key shares on the runs' rows before it locks the workspace's row.
- Two kinds of key share on a run's row come after the workspace's row and close no cycle:
  a recording that starts an extraction run (the acquisition's row, after its document's key
  share on the workspace's row and before its events: a key share does not block the
  `FOR UPDATE` holder's own locks on the workspace's row), and API commands that refer to a
  complete run after locking the workspace's row (`decide_turn`'s source references,
  a slate explanation's discovery): the worker writes no event for a complete run.
- Checked by reading: the cancel is the only API path that takes a key share on an
  unfinished run's row it did not just insert; no worker transaction touches the workspace's row before locking a
  run's row `FOR UPDATE`; `nessa.workspaces` is written only by `append_event`, rename and
  `get_workspace(lock=True)`; no SQL function locks a run's or workspace's row.

## Checks run

TDD evidence (the regression test, before the change, at BASE code plus the new test):

```
uv run --locked pytest -m integration "tests/integration/test_page_extraction.py::test_a_cancel_while_the_worker_writes_a_run_s_event_ends_without_a_store_error"
```

- RED, 5 separate sessions: `2 failed` each (10/10 cases), every one
  `assert 503 == 202` with body `{"error":{"code":"STORE_UNAVAILABLE",...}}`. The test
  stack's PostgreSQL log (followed into the scratchpad during each run) shows
  `ERROR: deadlock detected` twice per session (10 in all), e.g.

  ```
  ERROR:  deadlock detected
  DETAIL:  Process 150 waits for ShareLock on transaction 923; blocked by process 151.
          Process 151 waits for ShareLock on transaction 925; blocked by process 150.
          Process 150: INSERT INTO nessa.run_cancellations (run_id, workspace_id, requested_by) VALUES ($1, $2, $3) ON CONFLICT (run_id) DO NOTHING
          Process 151: UPDATE nessa.workspaces SET last_event_seq = last_event_seq + 1 WHERE workspace_id = $1 RETURNING last_event_seq
  CONTEXT:  while locking tuple (0,1) in relation "runs"
  ```

- GREEN, 10 separate sessions after the change: `2 passed` each (20/20 cases), 0
  `deadlock detected` lines in any session's PostgreSQL log.

Focused regression run after the change (every cancel test, N1 included, unchanged):

```
uv run --locked pytest -m integration tests/integration/test_page_extraction.py tests/integration/test_durable_runs.py tests/integration/test_receipts.py tests/integration/test_acquisition.py -k cancel
```
`15 passed, 63 deselected in 33.65s`.

`make check` (on the final code): exit 0. Ruff format (265 files already formatted), Ruff
lint (all checks passed), mypy (no issues in 265 source files), fast pytest `1231 passed,
276 deselected`, fixture validator `passed`, web: generated-client drift, Biome, `tsc`,
Vitest `25 files, 212 tests passed`.

`make acceptance` (run once, at the end): exit 0. Integration and stack
`276 passed, 1231 deselected in 455.12s` (the two new cases included), Storybook build
completed, Playwright `28 passed (2.3m)`. It started on `15f0d4b`; the only later change is
ADR 0009 wording folded into the docs commit (`37b2eeb`), and no test reads the ADRs or the
register, so the run applies to the final code. The log's one warning is Node's
`NO_COLOR`/`FORCE_COLOR` notice from the Playwright runner, not from this change.

No test changed its expectation; no assertion was weakened; no snapshot or generated file
changed.

## Not run / concerns

- The worker side of the regression test is the worker's adapters in the worker's order,
  not a call of `activity.publish` itself (ruling 3). The real worker paths it stands for
  were checked by reading: each takes the run's row as its first lock.
- Human-only gates: none apply to this task.
- (Superseded in fix round 1 by the reviewer's sentence, below.) Proposed CLAUDE.md wording (not edited). Current: "Lock order: a run's cancellation lock
  first, then `lock_workspace_records`, then rows." Proposed: "Lock order: a run's
  cancellation lock first (the cancel; a model-readable recording, before
  `lock_workspace_records`), then a run's row before its workspace's row: the worker locks a
  run's row `FOR UPDATE` only as its transaction's first lock, and a cancel records its
  requests before it locks the workspace's row (ADR 0009 decision 15)." Why: "then rows"
  left the order among rows open, which is where the deadlock was; and an extraction's
  accepting transaction takes a key share on its own run's row (its output) before
  `lock_workspace_records`, so "the recording lock, then rows" was not literally true
  (harmless: key shares do not wait for each other).

## Paths a reviewer can skip

None generated or vendored.

---

# Fix round 1 (FIX_BASE 37b2eeb)

Review: Spec ✅, Approved, 3 Minors. Controller rulings in `task-7d-fix-round-1.md`.
Commits:

- `34c643e` Share the two-connection cancel harness in the extraction tests: a refactor
  only, made before the fix and green (the deadlock test and N1: 3 passed).
- `851648e` Keep RUN_FINISHED when a cancel's runs settle while it waits (Minor 1): the fix
  and its tests.
- `5b33f6b` Correct ADR 0009's lock-order wording to exactly what holds (Minor 2), with the
  register.

No live calls. DBOS `application_version` stays `nessa-l0-1`: no workflow's step sequence
changed. Minor 3 is parked for the final review, as ruled; nothing was done for it.

## Minor 1: the 409 `RUN_FINISHED` contract in the settle race

- `backend/src/nessa/identity/runs.py` `cancel_run`, the reviewer's first option:
  - After `visible_workspace(tx, workspace_id, lock=True)` the cancel reads the run again
    and its unsettled started runs again (`_unsettled`).
  - It names only the asked runs that are still unsettled, in the same order as before. It
    writes `run.cancel_requested` only for those whose request it recorded now, as before.
  - If none is left unsettled, it raises `RUN_FINISHED` (`_run_finished`, the same message
    and `details.status` as the first check, now for the re-read run). The transaction rolls
    back its requests, and `run_idempotent` writes no receipt.
  - The first check is unchanged in effect: `not asked` is the old condition (run terminal
    and no unsettled started run).
- Why the re-read is enough: each request the cancel records holds a key share on its run's
  row until the cancel commits. A terminal publish takes that row `FOR UPDATE` first, so it
  cannot settle a newly asked run between the re-read and the commit.
- Not changed, as ruled: a request already recorded for a run that settled while the cancel
  waited stays recorded when another run is still named. Its later publication as
  `cancelled` records nothing, as for any request against a run that later finished. The
  ruling asked only to name, and write events for, the runs still unsettled.

Tests in `backend/tests/integration/test_page_extraction.py`. Two connections through
`_cancel_while_the_worker_holds`: a worker-role transaction holds the run's row as
`activity.publish` does, waits until the cancel's request waits for that row, then commits
the run `failed` with its event, as `publish` writes it (`_publish_failed`).

- `test_a_cancel_whose_runs_all_settle_while_it_waits_is_run_finished` has two cases:
  - `a_run`: a connection-check run;
  - `a_finished_acquisition`: a failed acquisition whose last unsettled started run
    settles.
  - Both assert 409 `RUN_FINISHED` with `details == {"status": "failed"}`; no
    `run_cancellations` row, `cancel_run` receipt or `run.cancel_requested` event in the
    workspace; and the worker's publish committed (`failed`).
- `test_a_cancel_names_only_the_runs_still_unsettled_once_it_has_waited`: one of an
  acquisition's two started runs settles while the cancel waits.
  - It asserts 202 with `cancellation_requested == [acquisition, other run]` and events
    for those two only.

TDD evidence:

```
uv run --locked pytest -m integration tests/integration/test_page_extraction.py -k "settle_while_it_waits or still_unsettled_once [or writes_a_run_s_event]"
```

- **RED** at `34c643e` (new tests, old `cancel_run`), 3 sessions: `3 failed` each (9 of 9).
  - The two 409 cases got `assert 202 == 409`; the cascade's body names the settled run in
    `cancellation_requested`.
  - The naming case got `[acquisition, other] != [acquisition, other, settled]`.
- **GREEN** after the change, 5 sessions with the deadlock test included: `5 passed` each
  (25 of 25).
- All cancel and settle integration tests (`-k "cancel or settle"` over
  `test_page_extraction.py`, `test_durable_runs.py`, `test_receipts.py` and
  `test_acquisition.py`): `18 passed, 63 deselected`, N1 included, unchanged.

## Minor 2: ADR 0009 wording, (a) to (d)

`docs/adr/0009-evidence-acquisition.md`, decision 15 *Lock order* and the open item:

- (a) "which the worker never waits for" became "which the worker waits for only as its
  transaction's first lock, holding nothing".
- (b) The recording's key share on the acquisition's row now names both sources: "its
  `page_extractions` link and, when it starts a run, `started_by_run`". It is stated for a
  model-readable page's recording, since the link is written whether or not a run starts.
- (c) "PostgreSQL ended the cancel" became "ended one of them (in the reproduction, the
  cancel)". The open item adds that an ended worker transaction is repeated by its retry
  owner.
- (d) Added: "a DELETE of a run's row takes the same lock, so T15's workspace deletion
  (DUR-06) must keep this order too (today only setup's `reset-demo` deletes runs, through
  the workspace's cascade)".
- Also recorded, because decision 15 publishes the behaviour: the re-read after the
  workspace's row, with both new tests named. The open item says the cancel re-reads.
- `docs/requirements-register.md` DUR-05: the fix-round-1 evidence and both tests added;
  the row stays `planned` (T13b).

Note for T15, not done here: deleting several runs' rows can still meet a cascade cancel that
holds key shares on several of them. "Keep this order" there also means a consistent order
among the runs' rows, for example the cancellation lock first, or the cancel's own
`created_at` order.

## CLAUDE.md proposal (the reviewer's sentence, replacing mine; not edited)

> Lock order (ADR 0009 decision 15): a run's cancellation lock first (the cancel; a
> model-readable recording, before `lock_workspace_records`). Only the worker locks a run's
> row `FOR UPDATE`, and only as its transaction's first lock; a cancel records its requests
> (key shares on the runs' rows) before it locks the workspace's row.

This replaces "Lock order: a run's cancellation lock first, then `lock_workspace_records`,
then rows." in the evidence invariant.

## Checks (fix round 1, final code `5b33f6b`)

- `make check`: exit 0.
  - Ruff format: 265 files already formatted. Ruff lint passed. mypy: no issues in 265
    source files.
  - Fast pytest: `1231 passed, 279 deselected`. Fixture validator: `passed`.
  - Web: drift, Biome, `tsc`, Vitest `25 files, 212 tests passed`. No warnings in the log.
- `make acceptance`, run once on `5b33f6b`: exit 0.
  - Integration and stack: `279 passed, 1231 deselected in 448.09s`, the three new cases
    included.
  - Storybook build completed. Playwright `28 passed (2.3m)`.
  - The one warning is Node's `NO_COLOR`/`FORCE_COLOR` notice from the Playwright runner, as
    before.
- No test changed its expectation. The refactor kept the deadlock test's assertions, and
  moved its `mark_running` into the write it makes under the lock, as `_prepare` does. No
  assertion was weakened.
