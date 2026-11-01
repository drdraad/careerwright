# Task 7d re-review 1: fix round 1 (Minors 1 and 2)

This re-review covers review Minors 1 and 2, as ruled in `task-7d-fix-round-1.md`. Minor 3 is parked and was not reviewed.

What I read:
- the rulings;
- the "Fix round 1" section of `task-7d-report.md`, treated as unverified claims;
- `review-37b2eeb..5b33f6b.diff` (3 commits, 4 files, 500 lines), read in one pass.

HEAD is `5b33f6b` and the working tree is clean. For one focused check per item, I read code outside the diff:
- `identity/receipts.py:53-87` (the 409 path);
- `api/envelope.py:39`;
- the `command_receipts` columns (`r0003_final_revocation_workspace_receipts.py:50-59`);
- every reader of `cancel_requested_at`;
- the `34c643e` refactor on its own.

I ran nothing and changed nothing, and made no live calls. `make check` and `make acceptance` passing on `5b33f6b` is the implementer's claim and is not verified here.

## Verdicts

| # | Item | Verdict | Where |
|---|---|---|---|
| 1 | 409 `RUN_FINISHED` kept when every asked run settles, with no request or receipt left | **Fixed** | `backend/src/nessa/identity/runs.py:370-387` |
| 2 | A partly settled cascade names only the unsettled runs | **Fixed** | `runs.py:380-387` |
| 3 | New race tests are deterministic and would fail on `37b2eeb` | **Fixed** | `backend/tests/integration/test_page_extraction.py:683-711`, `:786-838` |
| 4 | The refactor (`34c643e`) changed no test's expectation | **Fixed** (no change) | `test_page_extraction.py:716-760` |
| 5a | ADR (a): "which the worker waits for only as its transaction's first lock, holding nothing" | **Fixed** | `docs/adr/0009-evidence-acquisition.md:467-468` |
| 5b | ADR (b): the `page_extractions` link and `started_by_run` | **Fixed** | `:486-488` |
| 5c | ADR (c): "ended one of them (in the reproduction, the cancel)" | **Fixed** | `:470-471`, `:583-585` |
| 5d | ADR (d): a DELETE of a run's row takes the same lock | **Fixed** | `:462-464` |
| 5e | Decision 15's new re-read text, the open item and DUR-05 | **Fixed** | `:478-484`, `:586`; `docs/requirements-register.md:562` |

### 1. 409 kept when everything settles: fixed

**The new order** (`runs.py:370-387`):
- the first check is unchanged in effect (`asked = _unsettled(tx, run)`; `if not asked`, then `RUN_FINISHED`);
- then the requests;
- then `visible_workspace(lock=True)`;
- then the run and its unsettled started runs are re-read (`:380`), and `named` keeps the asked runs still unsettled (`:381`);
- if none is left, `RUN_FINISHED` is raised with the re-read run's status (`:382-383`);
- events are written only for named runs whose request this cancel recorded (`:384-386`).

**Why the 409 leaves nothing behind.** The raise happens inside `run_idempotent`'s `actor_transaction` (`receipts.py:62-66`), before `write_receipt`, so the requests roll back and no receipt is written. The `except` branch re-reads, finds no receipt and re-raises (`:80-87`), and `RUN_FINISHED` maps to 409 (`envelope.py:39`). The events are written after the check, so the 409 path writes none.

**Why the re-read is stable.** There are two kinds of named run:
- A run whose request this cancel recorded: the request's key share is held until commit, so a new terminal publish, which takes that row `FOR UPDATE` first, cannot settle it.
- A run whose request already existed (`ON CONFLICT DO NOTHING` inserts nothing, takes no key share and does not wait): its terminal publish writes an event, which needs the workspace's row. This cancel already holds that row `FOR UPDATE`.
  - If the publish's event was written first, the lock waited for it to commit, and the re-read sees the run as settled.
  - Otherwise the publish cannot commit until this cancel has.

Either way the cancel is serialised before any terminal state it reports as unsettled. No new lock is taken: the re-read is plain SELECTs.

### 2. Partly settled cascade: fixed

`named` filters `asked` by the re-read unsettled set, in `asked` order (`:381`). A run that settled while the cancel waited is neither named nor given an event. When the run itself has settled and only started runs remain, the answer is 202 naming only those, which is the published contract (`api/routes_runs.py:82-87`).

The test (`:822-838`) asserts 202 with `[acquisition, first]` and events for those two only.

### 3. Race tests: fixed (deterministic, and red on `37b2eeb` by reading)

**Why they are deterministic.** `_cancel_while_the_worker_holds` (`:683-711`) works like this:
- a worker-role transaction takes the held run's row `FOR UPDATE` and writes nothing;
- it starts the cancel and waits until the cancel's `run_cancellations` INSERT waits on `transactionid` (`:703`);
- only then does it make `_publish_failed` (`finish_run` failed plus its event, `:763-774`) and commit.

So the cancel's first read always sees the run unsettled, and the terminal state always commits while the cancel waits. No worker process runs in the fixture.

**Why they would fail on `37b2eeb`.** At `37b2eeb`, `cancel_run` answered from its first read:
- In both 409 cases it would answer 202 naming the run (`a_run`) or the last started run (`a_finished_acquisition`), which fails `assert answer.status_code == 409` (`:809`).
- In the naming case it would name `[acquisition, first, settling]`, which fails `:834`.

This matches the report's RED output (9 of 9 over 3 sessions; not verified here).

**The assertions mean something.**
- `command_receipts.workspace_id` is NOT NULL (r0003 `:58`), and a 202 would store `command = 'cancel_run'` with the workspace, so the empty-receipt check (`:815-819`) is not vacuous.
- The `a_finished_acquisition` setup marks the acquisition and the other started run `failed` with owner SQL that meets every CHECK. That is acceptable as fixture setup: the race under test is the last started run's settle.

### 4. Refactor: fixed, no expectation changed

`34c643e` touches only `test_page_extraction.py`. Its only changed assertion line is `assert run_store.mark_running(...)`, which moved into `_start_running` (`:716-722`), now written under the lock after the wait, as `_prepare` writes it. Every assertion of the deadlock test is unchanged (`:746-760`).

The move does not weaken the test:
- On the pre-7d code the cancel still holds the workspace's row while it waits at the run's row, and the worker's `UPDATE nessa.workspaces` still closes the cycle.
- On the fixed code the cancel's first read still sees `queued`.
- The N1 test is untouched.

### 5. ADR 0009 and the register: fixed

- **(a), (b) and (c)** now carry the corrections verbatim.
  - (b) is scoped to "a model-readable page's recording", which is right: `start_extraction` returns before writing a link otherwise.
  - The open item's added clause, "an ended worker transaction is repeated by its retry owner", is true: the store budget covers `_prepare` and `_settle`, the DBOS step covers `publish` and `acquire_target`, and the worker loop's next pass covers `act_on_cancellations`.
- **(d)** is exact as a statement and follows the ruling.
- **The new decision 15 text** (`:478-484`) states exactly what the code does: re-read after the workspace's row, not named, no event, 409 with requests rolled back and no receipt. It names both tests.
- **DUR-05** adds the fix-round-1 evidence and stays `planned` (T13b).

Note, not counted as an issue: the report's T15 observation that a multi-run deletion also needs a consistent order among the runs' rows lives only in the report. ADR (d)'s "keep this order" covers it if T15 reads it as taking every run's cancellation lock first. If the controller wants T15 to see that sentence, it belongs in T15's carry-forward.

## The implementer's concern: a settled run's request can stay recorded while another run is named

It changes no cancel answer.
- The status code and `cancellation_requested` come from `named`.
- A later cancel of the settled run is still `RUN_FINISHED`, because it is terminal and not in the unsettled set.
- A later cancel of the acquisition reads `_unsettled`, which ignores the request.

It changes no run's terminal state, output, spend or event stream.
- The worker's `act_on_cancellations` publishes it `cancelled`. `finish_run` records nothing for a terminal run, and no event follows: `mark_partial_stopped` matches only a `streaming` partial, which the first publish already stopped or deleted.
- The worker's other readers of `cancel_requested_at` act only before a run is terminal: `activity.py:406`, `acquisition.py:883` and `:1009`, `extraction_runs.py:145`. For a terminal run they matter only on a DBOS re-execution after its publish, where the run stays terminal either way.

It does change state that can be seen:
- a `run_cancellations` row for the settled run, later `signalled_at`;
- the settled run's `cancel_requested_at` in every run view (`GET .../runs/{id}`, the list, and the 202 body's `run` when the settled run is the cancelled run itself), with no `run.cancel_requested` event;
- one `DBOS.cancel_workflow` call on a finished workflow.

For that run, the field's description ("the run ends `cancelled` once the worker has stopped it", `api/schemas.py:304-307`) is then not true. The same state was already reachable before Task 7d, whenever a run finished after a cancel had been recorded. No UI reads the field yet. Removing the row would need a DELETE grant for `nessa_api` (it has SELECT and INSERT only) or savepoints around each request. Neither is warranted.

Verdict: acceptable, not an issue. Optional: add to decision 15's re-read sentence that "its request stays recorded and changes nothing".

## Regressions and new issues

None found.
- **Lock order:** no new lock, and the re-read happens after the workspace's row, so the order is unchanged.
- **Unchanged answers:**
  - the first `RUN_FINISHED` condition;
  - the order of the events;
  - "asking twice changes nothing, and names the same runs": a repeat cancel inserts nothing, re-reads the run as unsettled, names it and writes no event;
  - the receipt.
- **The `cancel_run` and `Cancellation` docstrings** are now both true (`runs.py:316-318`, `:357-361`).

New issues: Critical 0, Important 0, Minor 0.
