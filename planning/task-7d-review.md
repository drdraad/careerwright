# Task 7d review: the cancellation lock order

Package: `review-84dc858..37b2eeb.diff`. It has two commits (`c75b877`, `37b2eeb`), five files and 337 lines, read in one pass. I read the brief's Task 7d section and its Global Constraints and rulings, then the report (as unverified claims), then the diff. I read code outside the diff only for the five named risks below. HEAD is `37b2eeb` and the working tree is clean. I modified nothing and made no live calls. I did not run the test or the suites (see risk 1 for why).

### Spec Compliance
- ✅ Spec compliant. Each deliverable in the brief is present:
  - **A concurrent regression test that reproduces the deadlock, run red.** It uses two connections, a cancel against a worker writing an event, and is parametrised for an ordinary run and for an acquisition with two started extraction runs (`backend/tests/integration/test_page_extraction.py:669-743`).
  - **One lock order, with the cancellation lock first and no retry loop** (`backend/src/nessa/identity/runs.py:343-362`).
  - **ADR 0009 corrected.** Decision 15 gains a *Lock order* bullet, and the open item is rewritten (`docs/adr/0009-evidence-acquisition.md:456-487`, `:568-575`).
  - **DUR-05 updated**, with the lock pattern removed from its open items (`docs/requirements-register.md:562`). I confirmed no other register row names the pattern.
  - **`application_version` kept** as `nessa-l0-1` (`backend/src/nessa/identity/worker.py:30`). No step sequence changed: only the order of statements inside one API transaction.
  - **No other test changed.** The diff only adds a test.
- **Interpretation, accepted.** The brief says "with the cancellation lock first". The implementer reads this as "first wherever it is taken": the cancel and a model-readable recording take it, and the worker's `FOR UPDATE` transactions do not. That matches decision 15's existing wording ("each as its first lock"). Report ruling 1 also shows that the other reading would need the cascade to take every started run's lock too. No issue.
- ⚠️ Cannot verify from the diff:
  - `make check` and `make acceptance` exit 0.
  - RED in 10 of 10 cases over 5 sessions, GREEN in 20 of 20 over 10 sessions, and the PostgreSQL `deadlock detected` log lines.
  - The focused cancel run (15 passed).

  I did confirm one part of this: the acceptance run started on `15f0d4b`, which differs from `37b2eeb` only in `docs/adr/0009-evidence-acquisition.md` (`git diff --stat 15f0d4b 37b2eeb`). So that evidence applies to the final code.

#### Named risks (one focused check each)

**Risk 1: does the test reproduce the real deadlock, and would it fail on the old code? Yes, by reading.**

Checked: the test, its helpers (`_lock_waits` at `:570-577`, `_cancel`, `_unread_acquisition`, `_attempt`, `_submit_as_worker`, `_worker_engine`), and `cancel_run` at `84dc858`.

- **The worker's side.** Under the worker role (`run_transaction` on the worker's own settings), it:
  - locks the run's row `FOR UPDATE` (`:702`);
  - marks the run running;
  - starts the cancel;
  - waits until `pg_stat_activity` shows the cancel's `run_cancellations` INSERT waiting on `transactionid`, which is its foreign-key check waiting for the worker's row lock (`:706-710`);
  - writes `run.state_changed`, which runs `UPDATE nessa.workspaces` (`:711-717`).
- **On the old code the deadlock is deterministic.**
  - The old cancel took `visible_workspace(lock=True)` before its requests.
  - At that point the worker held no workspace lock (`mark_running` touches only `runs`), so the cancel got the workspace's row.
  - The cancel then blocked at the key share on the run's row, which satisfies the `wait_for`.
  - The worker's `UPDATE nessa.workspaces` then blocked on the cancel's `FOR UPDATE`.
  - The cancel waited first, so its deadlock check fires first and it aborts. `40P01` becomes `OperationalError`, then `StoreUnavailableError` (`nessa/db.py:64-68`), then 503. The test's `assert answer.status_code == 202` fails.
  - If PostgreSQL chose the worker instead, its `with run_transaction` raises and the test still fails.
- **The cascade case** deadlocks the same way at the last started run, which the worker holds.
- **The test cannot pass vacuously.** If the cancel never waits at the run's row, `wait_for` times out. If the thread dies, `[answer] = answers` fails. No worker process runs in the `scenario` fixture, so nothing else races.
- **The old code's failure is unconfirmed by execution.** The deadlock record in the report (INSERT `run_cancellations` against `UPDATE nessa.workspaces`, "while locking tuple … in relation runs") matches this mechanism exactly. Running the old code would mean changing the working tree, and I had no doubt about HEAD that the implementer's 10 green runs do not already answer.

**Risk 2: one lock order on every path that can meet a cancel. It holds.**

I checked every place a run's row is locked `FOR UPDATE` in `backend/src/nessa` (grep for `lock=True`, `FOR UPDATE` and `lock_started_runs`). There are exactly four, and each is its transaction's first lock (`set_config` takes none), with that run's events after it:

- `activity._prepare` (`identity/activity.py:403`, event at `:411`);
- `activity.publish` (`:663`, event at `:682`);
- `acquisition.acquire_target`'s first transaction (`evidence/acquisition.py:879`, event at `:897`);
- `publish_acquisition` (`:1006`), whose terminal state and event go through `publish` in a transaction of its own.

The other paths:

- **Settle and extraction acceptance** (`activity._settle` at `:587` and `record_extraction` at `evidence/extraction_runs.py:181-207`) take no run row `FOR UPDATE`. They take a key share on their own run (the output) and then the recording lock and events. Nothing the cancel holds blocks them.
- **The acquisition's recording** (`acquisition.py:941-978`):
  - It takes the cancellation lock first when the page is model-readable (`:947`), before `lock_workspace_records` (`:950`). `nessa.submit_page_extraction` takes it again, re-entrantly (`r0023_cancel_started_runs.py:62`).
  - It never locks a run's row `FOR UPDATE`.
  - Its key share on the acquisition's row comes after the workspace's key share. That is harmless because a key share conflicts only with `FOR UPDATE`. The holder of that lock (`publish` from `act_on_cancellations`) then needs only `FOR NO KEY UPDATE` or `KEY SHARE` on the workspace's row, which do not conflict with the recording's key share.
- **Reconciliation** (`activity.reconcile`, `:700`) reads without locking and then calls `publish`.
- **The worker-side cancellation** (`identity/worker.py:71-92`) calls `activity.publish`, then updates `run_cancellations.signalled_at` in a system transaction, which takes no run or workspace row lock.
- **SQL functions.** No function or migration takes `FOR UPDATE` on `runs` or `workspaces`. The `r0023` backfill and `r0001`'s actor lock are unrelated.
- **Writes that would take `FOR UPDATE`.** No runtime UPDATE of `runs` changes a key column, and the only DELETE of runs is setup's `reset-demo` cascade.

The cancel's new order is: cancellation lock, a non-locking visibility read (`runs.py:344`, same `workspace_not_found` answer, because the API policy on `workspaces` applies to every command), key shares on the runs' rows through the requests (`:359`), then the workspace's row `FOR UPDATE` (`:360`) and the events (`:361-362`).

**The cascade** (`runs.py:350`, `:358`) takes key shares on the acquisition and on each unsettled started run in `created_at` order, before the workspace's row. Each worker transaction holds at most one run's row `FOR UPDATE`, as its first lock, so the order among the runs cannot close a cycle.

- If a worker's `_prepare(E1)` waits for the cancel's key share on E1, it holds nothing while it waits.
- Two cancels (an acquisition and one of its extraction runs) can meet at a `run_cancellations` `ON CONFLICT` insert. The one that waits holds only its own cancellation lock and key shares. `run_cancellations` refers to `runs` only, not to `workspaces`, so neither holds the workspace's row while waiting.

**Risk 3: no retry loop, and no change to what a cancel answers. No retry loop: confirmed. The answer is unchanged except in one race (Minor 1).**

- There is no retry loop anywhere in the diff.
- Unchanged:
  - the 202 body construction (`runs.py:363`, `:368`; `api/routes_runs.py:89-97`);
  - the order of `run.cancel_requested` events;
  - the receipts;
  - the NOT_FOUND and RUN_FINISHED paths.
- Changed: the run and its started runs are now read before the cancel can wait at a run's row. A worker's terminal publish that is in flight when the cancel reads therefore yields 202, where the old code answered 409 `RUN_FINISHED` (if the worker's event was already written) or deadlocked (if not). Details in Minor 1.

**Risk 4: ADR 0009 decision 15, the closed open item and DUR-05. The core is accurate; three phrases are inexact (Minor 2).**

Accurate:
- the four `FOR UPDATE` sites, each as its first lock;
- that the cancel records its requests before it locks the workspace's row;
- that the two later key-share kinds close no cycle;
- that API commands referring to complete runs follow the workspace's row (`decide_turn`'s sources; a slate explanation's discovery, whose proposal exists only for a `complete` run, `profile/exploration.py:309-313`);
- that the worker writes no event for a complete run it publishes again;
- the open item's history and `application_version`.

DUR-05 is accurate: it stays `planned` because T13b owns the solver process, the evidence names the test, and the open list drops the pattern. Its "on every one of 10 tries" is the report's figure, which I could not verify.

**Risk 5: is the proposed CLAUDE.md lock-order sentence true of the code? No.**

The clause "then a run's row before its workspace's row" is not true of every transaction:
- A model-readable recording takes the workspace's row (the document's and new run's key shares) before the acquisition's row (`page_extractions.acquisition_run_id`, `started_by_run`).
- `submit_explanation` and `decide_turn` lock the workspace's row `FOR UPDATE` and then take key shares on complete runs' rows (`profile/exploration.py:728` and onward).

The two rules after the colon are true and are the ones that prevent the cycle.

Exact correction: replace the proposed sentence with

> Lock order (ADR 0009 decision 15): a run's cancellation lock first (the cancel; a model-readable recording, before `lock_workspace_records`). Only the worker locks a run's row `FOR UPDATE`, and only as its transaction's first lock; a cancel records its requests (key shares on the runs' rows) before it locks the workspace's row.

### Strengths
- **The fix is the smallest one that removes the inversion.** It moves one lock call and splits one loop. It fixes the order where it was inverted, the one API transaction that held the workspace's row and then waited for a run's row, and does not add a lock to every worker transaction. The events, their order and the answer's construction are kept.
- **Visibility checks keep their answers.** The non-locking `visible_workspace` before the reads keeps `workspace_not_found` distinct from `NOT_FOUND`. A locked read and a plain read see the same rows under the `api_owner` policy.
- **The regression test is deterministic and hard to fool.** It waits on the exact lock the deadlock needs (`transactionid` at the `run_cancellations` INSERT), uses the worker role and the worker's own adapters, covers the cascade, and asserts the cancel's answer, every recorded request, and the worker's committed state and event.
- **The docstrings match the code.** The `cancel_run` and `lock_started_runs` docstrings now state the order and why.
- **The report is checkable.** It shows red before green, with the PostgreSQL deadlock record, and states the "checked by reading" claims precisely enough to check. Every one I checked held.

### Issues

#### Critical
None.

#### Important
None.

#### Minor

**1. In one race, a cancel now answers 202 where it answered 409.**

`backend/src/nessa/identity/runs.py:347-368`.

**What.** The cancel reads the run and its unsettled started runs (`:347`, `:350`) and builds `asked` from those reads (`:358`). Only then can it wait, at a request's key share (`:359`).

Suppose the worker's terminal `publish` for one of those runs is in flight: it holds the row `FOR UPDATE` (`activity.py:663`), with or without its event written. Then:
- the cancel reads the run as `queued` or `running`;
- it waits at that run's row while the worker commits the terminal state;
- it records the request, writes `run.cancel_requested`, re-reads the run as `complete` or `failed` (`:363`);
- it answers 202 with that terminal status and the same run in `cancellation_requested`.

The old code locked the workspace's row first. When the worker's event was already written, that lock waited for the worker's commit, so the old cancel read the run as finished and answered 409 `RUN_FINISHED`; when it was not, the old code deadlocked.

**Why it matters.** It contradicts four published or recorded statements:
- the route's published description: "A finished run with none is `RUN_FINISHED`" (`api/routes_runs.py:82-87`);
- the field's description: "the run itself while it is queued or running … Each ends `cancelled`" (`api/schemas.py:345-349`);
- decision 15: "the run itself while unsettled" (`docs/adr/0009-evidence-acquisition.md:453`);
- the report's statement that the answer is unchanged.

It is a behaviour change made by this diff, not a hardening. Its effect is small:
- The window is one worker transaction, a few milliseconds.
- `finish_run` still records one terminal state.
- A request against a run that later finished was already reachable.
- No UI calls cancel before Task 8.

**Fix**, either of:
- After `visible_workspace(tx, workspace_id, lock=True)`, re-read the asked runs. If the run and every started run have settled, raise `RUN_FINISHED`; the transaction then rolls back its requests and writes no receipt. Otherwise, name and write events only for those still unsettled.
- State the race as accepted in the `cancel_run` docstring and in decision 15: "a run that settles while the cancel waits for its row is still named; its request changes nothing".

**2. Three phrases in ADR 0009's *Lock order* bullet and open item are inexact.**

`docs/adr/0009-evidence-acquisition.md:465`, `:476-478`, `:468`, `:572`.

**What, and the correction for each:**

(a) `:465` says the cancel's "cancellation lock and key shares, which the worker never waits for". The worker does wait for them:
- a worker's `FOR UPDATE` on a run's row waits for the cancel's key share on that row (in the cascade, the cancel holds E1's key share while it waits for E2);
- a model-readable recording waits for the cancellation lock.

This is harmless only because each is its transaction's first lock. Write: "which the worker waits for only as its transaction's first lock, holding nothing".

(b) `:476-478` names only `started_by_run` as the recording's key share on the acquisition's row. The `page_extractions` link takes one too, through `acquisition_run_id` (`migrations/versions/r0021_page_extraction.py:64-65`), whether or not a run is started (`evidence/extraction_runs.py:150`, `:160`). Write: "takes one on the acquisition's row (its `page_extractions` link and, when it starts a run, `started_by_run`)".

(c) `:468` and `:572` say "PostgreSQL ended the cancel". PostgreSQL ends whichever transaction's deadlock check finds the cycle. In the reproduction that was the cancel, because it waited first; it could equally be the worker's, which its retry owner then repeats. The original item said "ends one". Write: "ended one of them (in the reproduction, the cancel)".

Optional (d): "`FOR UPDATE` on a run's row … only by the worker … at run time" (`:458-461`). A DELETE of a run's row takes the same lock. Today that is only setup's `reset-demo` cascade (`identity/store.py:158-163`), but the workspace deletion in T15 (DUR-06) will do the same. One clause would carry the order to that task.

**Why it matters.** The brief asks the ADR to "say exactly what holds", and later tasks will extend these transactions from this text.

**3. No automated guard on the worker side of the order.**

`backend/tests/integration/test_page_extraction.py:700-717`; `docs/adr/0009-evidence-acquisition.md:458-462`.

**What.** The fix depends on one invariant: a run's row is locked `FOR UPDATE` only as its transaction's first lock. The ADR records this as checked by reading. The regression test writes the worker's order by hand (`run_store.run(lock=True)`, then `append_event`) instead of running `_prepare` or `publish`.

**Why it matters.** Suppose a future worker transaction inserts a row that refers to the workspace, or writes an event, before `run_store.run(tx, …, lock=True)`. That would bring the deadlock back, and this test would stay green.

**Fix (optional).** Add a check that each `lock=True` call on a run is its transaction's first statement, or a gated test through the real `publish`. This is a hardening that no failing check or Global Constraint requires: it belongs on the final-review list (R12).

### Assessment
**Spec compliance:** ✅ Spec compliant
**Task quality:** Approved
**Reasoning:** The cancel now takes its key shares on runs' rows before the workspace's row. Every worker transaction that locks a run's row `FOR UPDATE` does so as its first lock, so the cycle is gone for an ordinary run and for the cascade. There is no retry loop, and the regression test reproduces the deadlock deterministically. What remains is one narrow change to the answer in a race (202 where 409 was answered) and some imprecise ADR wording, all Minor. Issue counts: Critical 0, Important 0, Minor 3. Risk 5: No; the corrected sentence is given under risk 5.
