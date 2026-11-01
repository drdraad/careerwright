# Task 3 review, half B: runs, failures, model choice, spend, live smoke, tooling, docs

Scope: `review-ff449da..d4f8728-B-runs-tooling.diff`, read in five passes: the spike deletions,
`identity/{activity,failures,meta,model_choice,model_registry,run_store,runs,spend,
spend_limits,worker,workflow}.py`, the tests and support code, `tools/`, and the docs. I
opened files outside the diff only for the named risks listed below. I ran no suites. The
only command I executed was `make -n live-smoke` (a dry run; nothing ran and no Meta call
was made). I did not read `.env`.

### Spec Compliance
- ❌ Issues found: R5 says every live call must be ledgered, and `make live-smoke` can miss
  one. It reads the attempt rows while the worker is still running, so a retry that starts
  after the poll deadline reaches Meta without being ledgered (`backend/tools/live_smoke.py:49,249`,
  `:261-273`; see I1). Every other brief item in this half is delivered:
  - the command contract (`Makefile:1-48`);
  - run IDs and a transactional outbox (`run_store.py:55-80`);
  - server-side spend reservation;
  - the worker boundary checks;
  - demo egress blocking, verified by `tests/stack`;
  - fast `make check`, and `make acceptance` on real PostgreSQL 16 and DBOS.
- Named-risk checks (what I checked, and the result):
  - **ADR 0002 pattern holds.** The journal carries the run ID only, and the test asserts
    `positionalArgs == [run_id]` (`tests/integration/durable.py:98-110`). The
    sealed key is opened only inside `_call` (`activity.py:193-211`), after `_prepare` has
    committed the reservation. Errors are classified by type and status, with only class
    names kept (`failures.py`). Retries happen in exactly one place, the DBOS step: the
    client has `max_retries=0`, the agent `retries=0`, and `request_limit=1`. One gap:
    `_call` is not inside `execute`'s try block (see M3).
  - **Carry-forward M4 (crash after accept).** Fixed. `accepted_output` is checked before
    any call (`activity.py:142`). Usage and the output commit in one transaction
    (`_settle`, `:215-245`). `test_a_crash_after_acceptance_never_calls_the_model_again_and_keeps_the_usage`
    covers it with a real SIGKILL.
  - **Carry-forward ADR 0002 decision 7 (database down during begin/finish).** Fixed.
    `_transaction` maps `OperationalError`/`InterfaceError` to `StoreUnavailableError`
    (`src/nessa/db.py:57-69`, opened for this check). `execute` catches errors from
    `_prepare` and `_settle`, and they become `transient_store`. Exhaustion ends the run
    `failed/app_store_unavailable`. Tested by `test_an_app_database_outage_mid_run_ends_in_a_typed_terminal_state`.
  - **Carry-forward M7 (factory and policy out of the CLI).** Done: `identity/meta.py`,
    `spend.py`, `model_choice.py`, `model_registry.py`.
  - **Bounded `make stop`.**
    - `compose stop --timeout 10` runs under a 90 s subprocess timeout, with
      `compose kill` (30 s) as the fallback (`tools/stack.py:98-106`).
    - The worker has a 10 s `os._exit` watchdog (`worker.py:128-133`).
    - Compose sets no restart policy (`compose.yaml`, opened for this check).
  - **Spend reservation is atomic.**
    - `pg_advisory_xact_lock` is taken per workspace before the sum and the insert, in
      the same READ COMMITTED transaction (`run_store.py:244-263`, `activity.py:155-176`).
    - The worker's read policy on `model_attempts` covers the whole workspace
      (`r0002...py:225-226`, opened for this check), so the monthly sum sees other runs.
    - Unknown cost keeps the reservation (`_COMMITTED`, `run_store.py:30-33`).
    - After a crash, a held attempt becomes `interrupted/unknown` on re-execution and on
      publish (`run_store.py:155-166`).
  - **Production cap follows the model ID, not a flag.** `authorise` refuses when the test
    model *is* the production model unless the flag is given (`live_smoke.py:72-82`). The
    ledger marks a production call by model ID (`:142`, `:174`). The flag spelling has a
    trap (M2).
  - **The Contributor test model is refused for non-synthetic data.** Three layers enforce
    it:
    - `for_workspace` always pins the Standard model for non-synthetic workspaces
      (`model_choice.py:43-46`);
    - `assert_model_permitted` checks again at submission;
    - the activity refuses it (`activity.py:150-151`), and the database CHECK rejects it.

    `synthetic` has no default, so the client must choose it explicitly
    (`identity/workspaces.py:25`, opened for this check). Non-synthetic data always gets
    the production model.
  - **`make live-smoke`.**
    - Calls are capped at 3 (the step's attempts); the worst case per invocation is
      ≤ $0.10.
    - The key travels in the API body, never as a command argument.
    - Attempts are ledgered with tokens and cost, and an unknown cost stays unknown.
    - I recomputed the running total from the JSONL: 19,707,014 nano-USD = $0.019707.
      It matches.
    - Live calls are absent from `make check` (addopts exclude integration and stack)
      and from `make acceptance` (fake models; the live-mode stack test has no key and
      no runs).
    - Gaps: I1 (ledger race) and M2 (flag spelling).
  - **Stack isolation.**
    - The projects are `nessa-l0`, `-test`, `-stacktest` and `-smoke`. `-p` overrides the
      `name:`. Volumes and networks have no explicit names, so they are prefixed by project.
    - `down --volumes` is scoped to the test, stacktest and smoke projects. Nothing
      references `agentsolve-*` or `eigenprompt-*`.
    - `reset-demo` deletes only the fixture workspace; the stack test checks that another
      workspace is kept.
  - **Spike retirement.**
    - Retained:
      - all ten durability and failure scenarios (`test_durable_runs.py`);
      - sealing (`tests/domain/test_keyring.py`);
      - the leak-scan unit tests;
      - the DBOSDurability negative control (`tests/integration/test_leak_negative_control.py`,
        opened for this check);
      - the failure mapping and the request shape.
    - Not retained: the spike's end-to-end check that in-flight attempts are ledgered when
      the live run fails (`spikes/durable/test_durability.py::test_live_check_ledgers_every_attempt_even_when_the_run_fails`).
      Only the helpers are unit-tested now (see I1).
    - No live code imports `spikes.`; the remaining mentions are labelled historical.
  - **Docs honesty.**
    - No human gate is claimed.
    - The TODO(Task 3) markers in CLAUDE.md are replaced by commands that exist
      (`Makefile`).
    - Closed register rows are backed by named tests, with two inconsistencies (M6).
    - Stale references remain (M7).
  - **DUR-05 and the reconciler.**
    - Cancellation is not in the brief or in the S1.1–S1.3 card text. It appears only as a
      register owner assignment (`docs/requirements-register.md:548`, owners T3 and T13).
      Not required; it was honestly left `planned`.
    - The DBOS-`ERROR` reconciler is not required either. DUR-08's required behaviour (a
      typed terminal state) is tested without it. But the untested code has a wrong
      branch (M1).
- ⚠️ Cannot verify from diff (these live in half A):
  - API routes, OpenAPI enums, 202 + `Location`, the SSE resume (`nessa/api/*`).
  - Migrations r0001 and r0002, the RLS policies, `contributor_models_only_for_synthetic_data`,
    the composite FK. I opened only the `model_attempts` worker policy.
  - Keyring and credential sealing, rotate/revoke, owner-only key files, reseal
    (`identity/keyring.py`, `credentials.py`, `credential_store.py`).
  - Identity: firebase-admin verification, invitations, `resolve_actor`.
  - The edge relay, the Host/Origin guard, the loopback and internal network in
    `compose.yaml`. I opened it only for project, volume, restart and model variables.
  - Profiles, expected-version writes, source references, seed contents.
  - Redacted logging (`nessa/logs.py`).
  - Fresh and populated migration acceptance; key redaction across errors, database
    history and exports; refusal of an unauthorised origin; fail-closed config.

### Strengths
- **The activity is shaped well.** `_prepare` runs in one run-scoped transaction:
  - it interrupts stale attempts and reuses an accepted output first;
  - it re-checks access, model and key;
  - it reserves spend under a lock.

  Then the call runs outside any transaction, and `_settle` writes the output and usage
  atomically. Unknown costs stay unknown at every step.
- **The workflow wiring is tidy.** Provider transients and store transients are separate,
  label-only exception types. `classify_exhausted` names what was unavailable, so a run
  never ends as an empty success.
- **The tests exercise real behaviour.**
  - Real worker processes and real SIGKILL crash points.
  - A leak scan in every scenario covers both databases and the logs: key fragments, the
    profile sentinel and the output sentinel.
  - A database outage is injected by locking out the worker role.
  - The concurrent-reservation test uses overlapping calls.
- **Stack tooling is bounded and isolated.** Every docker call has a timeout. Each
  purpose has its own project, ports and `NESSA_HOME`. The egress probes have a positive
  control.
- **The ledger is arithmetically correct.** It marks unknown cost explicitly. The smoke
  falls back to "every possible call" when the attempt rows cannot be read.

### Issues
#### Critical
None.

#### Important
- **I1: the live-smoke ledger can miss a real Meta call.**
  - Where: `backend/tools/live_smoke.py:49` (`RUN_TIMEOUT_S = 240`), `:249` and `:261-273`, read
    with `backend/src/nessa/identity/meta.py:19` (`REQUEST_TIMEOUT_S = 120`) and
    `workflow.py:27,53`.
  - What happens: a run can take 3 × 120 s plus 1 s and 2 s of backoff, about 363 s. The
    poll gives up at 240 s. Then the `finally` block reads the attempt rows *while the
    worker is still running*, and only afterwards calls `stack.down()`. If Meta is slow,
    attempt 3 starts about 243 s in: around the moment the rows are read (after the export
    and the leak scan). That request reaches Meta and is never ledgered.
  - Coverage: the spike's end-to-end "ledgers every attempt even when the run fails" test
    was retired without a successor. Only the pure helpers are tested
    (`tests/tools/test_live_smoke.py`).
  - Why it matters: R5 requires every live call to be ledgered with its cost. The commit
    message ("Ledger every live-smoke attempt") and the register (MODEL-09 `verified`)
    claim this guarantee.
  - Fix:
    - In the `finally` block, stop the worker first (`stack.stop(("worker",))`), then call
      `_all_attempts`, then `down`. Optionally also set `RUN_TIMEOUT_S` above
      `MAX_CALLS × REQUEST_TIMEOUT_S` plus the backoff.
    - Belt and braces: set the smoke workspace's run limit to
      `MAX_CALLS × connection_check.worst_case_nano_usd(model)`. The product's durable
      reservation then enforces the 3-call cap too, not only DBOS's per-execution retry
      count.

#### Minor
- **M1: the DBOS-`ERROR` reconciler can mark a successful run failed, and it spins on
  failure** (`backend/src/nessa/identity/worker.py:76-87`, `:116-126`).
  - It publishes `failed/unknown_failure` for *every* errored workflow. The one realistic
    trigger is a `complete` outcome whose publication exhausted about 34 min of retries.
    That run has an accepted output, and it would be marked failed.
  - It re-lists and re-publishes every errored workflow forever, a list that only grows.
  - If `publish` raises, `next_reconcile` is not advanced. Reconciliation then retries
    every 0.2 s and the heartbeat stops.
  - It is untested, as the report admits. ADR 0002 line 102 cites the outage test in the
    same parenthesis, which reads as if the reconciler were tested.
  - Fix:
    - If `run_store.accepted_output` exists, publish `succeeded(output)`.
    - Advance `next_reconcile` before the call, or in a `finally`.
    - Skip runs that are already terminal.
- **M2: `make live-smoke PRODUCTION=0` uses the production model** (`Makefile:39`).
  `$(if $(PRODUCTION),…)` treats any non-empty value as true. `make -n live-smoke PRODUCTION=0`
  prints `--production-model`. The cost stays capped (about $0.041), but R5 asks for an
  explicit opt-in. Fix: `$(if $(filter 1,$(PRODUCTION)),--production-model,)`.
- **M3: `execute` can raise despite "Never raises"** (`backend/src/nessa/identity/activity.py:248-266`).
  `call = _call(rt, prepared)` is outside both try blocks. `_usage` (`:211`) builds
  `Usage(...)`, whose `__post_init__` raises `ValueError` on inconsistent provider counts.
  That would escape as a non-transient step error: the workflow goes to `ERROR` and the
  output of a call that succeeded is lost. Fix: compute usage inside `_call`'s try, or put
  `_call` inside `execute`'s try.
- **M4: a crash after a terminal *failure* is recorded re-calls the model**
  (`activity.py:142-176`). Only an accepted output is reused. If the worker dies after
  `_settle` commits a terminal failure (for example a billed `invalid_model_output`) but
  before DBOS records the step, re-execution reserves and calls again. The same gap as M4,
  on the failure branch. Fix: when a finished attempt with a terminal failure class
  exists, return that failure.
- **M5: a store outage gets the same 3-attempt budget as provider errors**
  (`workflow.py:27,50-55`). A database restart longer than about 3 s fails every
  in-flight run, including runs whose paid call already succeeded. The outage test passes
  because it accepts that. Consider a longer, separate retry budget for `transient_store`.
- **M6: the register breaks its own closing rule** (`docs/requirements-register.md:34`
  says a shared row whose other owners are open stays `planned`).
  - BND1-11 (T3, T4; line 93) is `verified` while noting "T4 must add the web container".
  - MODEL-02 (T3, T5; line 531) is `verified` although T5 still owns part of it.
  - Fix: mark them `planned` with the Task 3 part recorded, as was done for the other
    shared rows.
- **M7: stale or non-working references.**
  - `backend/src/nessa/identity/model_registry.py:6` cites
    `nessa.identity.runs.select_run_model`, which does not exist.
  - `backend/tools/localenv.py:75` says "Step 2 is `make reseal-credentials`"; no such
    target exists.
  - `docs/runbook.md:49-52`: the reseal step `docker compose -p nessa-l0 run --rm migrate …`
    fails on `${NESSA_HOME:?run make setup}` unless `NESSA_HOME` is exported. It is not in
    `.env.example`.
  - Fix: correct the references. Either add a `make reseal-credentials` target or prefix
    the runbook command with `NESSA_HOME=…`.
- **M8: after rotation the leak scan stops looking for the old key**
  (`backend/tests/integration/test_durable_runs.py:320`). The comment says "too", but the
  assignment replaces the old needle. Fix: scan for both keys.
- **M9: one test's name claims more than it asserts**
  (`backend/tests/domain/test_meta_request_shape.py:56-59`).
  `test_the_prompt_carries_no_workspace_data` only asserts that the fixed prompt is
  present. Assert that the request input equals `connection_check.PROMPT` (plus the
  instructions) and nothing else, or rename the test.
- **M10: dead helper.** `backend/tests/support/infra.py:241` `emulator_reachable` has no
  callers.
- **M11: the "offline" acceptance suite opens real outbound connections**
  (`backend/tests/stack/test_local_stack.py:114,121`). The edge positive control and the
  live-mode worker probe connect to `1.1.1.1:443` and resolve `example.com`. The tests
  still pass offline, because only the host-listener result is asserted there, so the
  public probe adds no evidence on those paths. Consider dropping it from the
  edge/live-mode probes, or using a TEST-NET address.
- **M12 (note): the ledger no longer has a cumulative budget.** The spike's ledger
  `spent()` scope cap (15 calls) was removed (`backend/tools/usage_ledger.py`). Each
  `make live-smoke` is capped, but invocations are unlimited. This is documented in
  `live-usage.md`. If the controller wants a sprint-level cap, restore a scope budget
  check in `authorise`.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The durable-run core is sound and well tested:
- the ADR 0002 pattern holds;
- the M4, decision 7 and M7 carry-forwards are closed;
- spend reservation is atomic;
- the Contributor ruling is enforced at three layers.

One R5 gap needs fixing before MODEL-09 can stay `verified`: the live smoke reads its
attempt rows while the worker can still call Meta. The Minors are cheap and worth fixing
alongside it, especially M1 to M3.
