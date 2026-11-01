# Task 3 re-review 1 (fix round 1: `d4f8728..12a016e`)

Scoped re-review: confirm each fix-list finding, adjudicate the implementer's declared
changes, and look for regressions in the fix diff. This is not a fresh full review.

Method:
- Read the fix list, both original reviews, the fix report ("Fix round 1"), then the
  6,253-line diff in nine passes. The working tree is at `12a016e`.
- I treated the report as unverified claims. Verdicts below come from reading the code and
  the tests' assertions.
- No suite or focused test was run, no live call was made, and `.env` was not read.
- Files outside the diff were opened only for a named risk (one check each):
  - `backend/tools/stack.py:76-108`: what happens to the ledger when `stop_worker` fails.
  - `compose.yaml:74`, `backend/uv.lock:1419` and uvicorn 0.54.0 `config.py:225,363`: can
    proxy headers spoof the client address?
  - `r0001...py:160-162`: the receipt policy that r0003 alters.
  - `api/schemas.py` `RunOut` and `CredentialOut`: which receipts r0003's backfill drops.
  - `identity/run_store.py` `insert_output` and `finish_attempt`: is a retried settle
    idempotent?
  - `CLAUDE.md:27-32` and `identity/failures.py:1-7`: the retry-owner wording.
  - `docker/auth/pnpm-lock.yaml:1-12`: the lockfile importer pin.
  - `tools/localenv.py:1-100`: the remaining `--rotate-master-key` path.

## Finding verdicts

30 findings: **30 Fixed, 0 Partially fixed, 0 Not fixed.** "Would fail on old" judges
whether the covering test's assertions fail against `d4f8728` behaviour.

| ID | Verdict | Evidence (fix) | Covering test; would it fail on old? |
|---|---|---|---|
| A-I1 | Fixed | `src/nessa/cli.py:103` `reseal` reseals credentials **and** run outputs in one transaction. `cli.py:83` scans every `nessa` table with a `key_version` column and raises `ResealIncompleteError` (`cli.py:63`). `tools/stack.py:151-160` `rotate_master_key` adds the key, restarts api and worker, waits healthy, then reseals. `Makefile:51-55` adds `make rotate-master-key` / `make reseal`. `docs/runbook.md:17,51-56` and ADR 0004:100 updated. | `tests/integration/test_master_key_rotation.py:77`: it seals two outputs, reseals, deletes `v1.key` (`:112`) and asserts every output is `key_version == 2` and opens (`:123`). The old code never touched `run_outputs`, so this fails. `:135` (a forgotten sealed table blocks success). Stack: `test_local_stack.py:344`. |
| B-I1 | Fixed | `tools/live_smoke.py:339` stops the worker before `_workspace_attempts` (`:341`). `RUN_TIMEOUT_S` comes from the worst case (`:65-70`). The workspace run and period limits are set to the invocation worst case (`:313`). | `tests/integration/test_live_smoke_ledger.py:66`: a real worker process and a fake model that logs each call; the poll gives up after 0.5 s; asserts `ledger rows >= calls made`. Mutation evidence: with the stop removed, `1 >= 3` fails. Yes. (A new Minor below covers a failure path.) |
| B-M1 | Fixed | `identity/activity.py:355` `reconcile` publishes the accepted output, else the recorded failure, else `unknown_failure`, and skips terminal runs. `worker.py:101` `loop_pass` advances `next_reconcile` before reconciling. ADR 0002:101-111 and ADR 0004:124 name the tests and say the `ERROR` state is simulated. | `test_durable_runs.py:193` (ERROR simulated; expects `complete` with the same output and one attempt): the old code published `failed/unknown_failure`, so yes. `tests/domain/test_worker_loop.py:15`: no `loop_pass` existed before. |
| B-M2 | Fixed | `Makefile:43` uses `$(filter 1,$(PRODUCTION))`. | `tests/tools/test_live_smoke.py:55` runs `make -n` for `1/0/false/yes/""`. `PRODUCTION=0` printed the flag before, so yes. |
| B-M3 | Fixed | `activity.py:246` builds usage inside `_call`'s guarded path; `execute` (`:311`) wraps all of `_attempt`. | `test_durable_runs.py:167` (fake `INCONSISTENT_USAGE`): expects `failed/unknown_failure`, attempt `unknown_failure:ValueError`/`unknown`, workflow `SUCCESS`. The old run stayed `running`, so yes. |
| B-M4 | Fixed | `activity.py:175` returns a recorded terminal failure with a `reused_failure` attempt (no reservation). `failures.py` `recorded_failure`. | `test_durable_runs.py:138`: the second attempt must be `reused_failure`/`none`/0. Before, it was a new paid call, so yes. `test_failures.py:125`: every transient and success label maps to None. |
| B-M5 | Fixed | `activity.py:287-309`: a store budget of 60 s (`:62`) wraps prepare and settle separately; the call result is held in memory; past the budget the run fails `app_store_unavailable`. `workflow.py:46` retries only `TransientProviderError`. | `test_worker_boundaries.py:205` (12 s lockout mid-call: `complete`, one `succeeded`/`reconciled` attempt). Before, this ended `failed/app_store_unavailable`, so yes. `:229` (budget 2 s: a typed terminal state). See the adjudication below. |
| B-M6 | Fixed | `docs/requirements-register.md:93` (BND1-11) and `:531` (MODEL-02) are `planned`, with the T3 part recorded and the open part named. | Doc. |
| B-M7 | Fixed | `model_registry.py:6` cites `model_choice`; `tools/localenv.py:75` cites the real targets; the runbook rotation is `make rotate-master-key` (`runbook.md:51`), so no `NESSA_HOME` export is needed. | Doc. (The `--rotate-master-key` flag is adjudicated separately.) |
| B-M8 | Fixed | `tests/integration/durable.py:32,121`: `retired_keys` are scanned too. | `test_durable_runs.py:390` (`:410` appends the replaced key). A test fix. |
| B-M12 | Fixed | `tools/usage_ledger.py:67` `spent(scope)`: unknown cost counts at its reservation. `live_smoke.py:132-150` checks calls, production calls and cost. Defaults are 9 / 3 / $0.30 (`:89-96`) and can be set through `NESSA_LIVE_SMOKE_*`. Checked at `:419-421`, before the stack starts. | `test_live_smoke.py:87` (3 cases) and `test_usage_ledger.py:74`. Mutation evidence: `3 failed`. Yes. Not atomic: see the adjudication. |
| A-M1 | Fixed | `edge.py:59` resolves the target and connects only to an address inside the internal subnets (`localnet.py:26`). It logs a refusal (`:84`) and refuses to start without an internal network (`:128`). | `test_edge_forwarder.py:107`: a target resolving outside the allowed network is never contacted. The old edge connected, so yes. `:114`. Stack: `test_local_stack.py:299` (computed subnets equal `docker network inspect`; the absent `web` is refused and logged). |
| A-M2 | Fixed | `r0003...py:24-44`: a BEFORE UPDATE trigger plus CHECK `replacements_are_revoked`. | `test_credentials.py:125`, run as `pg_api` with `actor=ADA`: clearing a revocation, back-dating it and changing `replaced_by` each raise. `pg_api` held UPDATE on those columns before, so yes. |
| A-M3 | Fixed | (coverage only) | `test_isolation.py:136`, parametrized over the six execution tables, with owner ≥ 1 and other actor / no actor = 0. It could not fail on old code (the policies were already right), which is acceptable for a coverage gap. |
| A-M8 | Fixed | `identity/credentials.py:99` `_active` returns 409 `CREDENTIAL_REVOKED` for rotate and revoke. | `test_credentials.py:157` (409 for both; an unknown ID is still 404). The old code gave 404 / a 200 no-op, so yes. |
| A-M9 | Fixed | `api/envelope.py:81-90`: for `extra_forbidden`, the last `loc` part becomes `<unexpected field>`. I grepped the request models: none has free-keyed dict fields, which pydantic would also echo in `loc`. | `test_request_guard.py:105`. The key was echoed before, so yes. |
| A-M10 | Fixed | `r0003...py:46-60`: `workspace_id` FK `ON DELETE CASCADE`, backfill, NOT NULL, index, and WITH CHECK limited to visible workspaces. `receipts.py` `CommandResult` carries the workspace ID. | `test_receipts.py:25` (written through the API as `nessa_api`, cascade on delete), `:45` (reset-demo) and `test_migrations.py:98` (populated upgrade). Yes. (A new Minor below covers the backfill.) |
| A-M11 | Fixed | `api/guard.py:47-53` refuses 403 `CLIENT_NOT_ALLOWED` for any client outside `client_networks`. `main.py` passes `local_networks()`. | `tests/api/test_guard_and_envelope.py:75` (LAN, private, public, non-IP). These were served before, so yes. See the adjudication. |
| A-M12 | Fixed | `docker/auth/Dockerfile:15` runs `pnpm install --frozen-lockfile --prod` from the committed `package.json` (exact `15.34.1`) and `pnpm-lock.yaml` (v9.0, importer specifier `15.34.1`). | Build evidence only (report). Not re-run. |
| A-M4 | Fixed | `guard.py:94-100`: only `lifespan` passes; websockets are closed with 1008. | `test_guard_and_envelope.py:90`. Yes. |
| A-M5 | Fixed | `envelope.py:125` `framework_error` gives 404 / 405 / other 4xx / 5xx codes. | `test_guard_and_envelope.py:104`. Yes. |
| A-M6 | Fixed | `guard.py:120-128`: the guard catches inside `ServerErrorMiddleware`, logs the class and frames, and sends `INTERNAL_ERROR` through `send_with_id`; it re-raises if the response has started. | `test_guard_and_envelope.py:112` checks the header equals the body's correlation ID, the access log shows 500, and the secret is not echoed. Yes. |
| A-M7 | Fixed | `routes_events.py:37,104-113` re-verifies the token every 60 s; on a `NessaError` it ends with `stream_ended`. | `test_events.py:65`. The old stream kept sending heartbeats, so yes. |
| A-M13 | Fixed | `schemas.py:31` `ResponseModel`, `:101` `of_version`, `routes_runs.py:25` `run_out`. Export imports nothing private. | Existing profile, run and export tests. |
| A-M14 | Fixed | ADR 0004:87-94 records the expected-version rule. | Doc. |
| A-M15 | Fixed | `runbook.md:58-63`; r0001 and r0002 docstrings. | Doc. |
| B-M9 | Fixed | | `test_meta_request_shape.py:56` asserts the exact `instructions`, the `input` and the body key set. |
| B-M10 | Fixed | `emulator_reachable` and its unused import are removed. A grep finds no callers. | n/a |
| B-M11 | Fixed | The stack probes use TEST-NET `192.0.2.1`; the edge control and the live-mode probes check only the host listener. The demo-mode `example.com` lookup is kept as DNS-egress evidence, which is justified. | `test_local_stack.py:174,200`. |
| Licence notes | Fixed | `docs/dependencies.md:66-79`, labelled "Not a legal review". | Doc. |

## Adjudications

### Database-outage retries inside the activity (vs ADR 0002 "the DBOS step is the only retry owner")

**Sound.**
- The two retry owners cover disjoint failure classes, so they never compound:
  - the step retries only `TransientProviderError` (`workflow.py:46`);
  - the activity retries only `StoreUnavailableError` (`activity.py:287-298`).
- A store failure that outlives the budget is turned into a terminal
  `app_store_unavailable` *inside* `execute` (`activity.py:311-322`). It never reaches the
  step's retry logic, and `STORE_LABEL` can no longer leave the activity as a transient.
- Bounds:
  - each transaction gets at most 60 s, with backoff capped at 8 s;
  - `_call` runs exactly once per `execute`;
  - at most 3 step executions per run, so at most 3 paid calls per execution, as before;
  - shutdown is still bounded by the 10 s `os._exit` watchdog.
- No re-call of the paid model:
  - the result is held in memory across settle retries;
  - past the budget, no step retry happens;
  - a lost commit acknowledgement on settle is idempotent: `insert_output` resolves the
    unique violation to the existing output.
- A crash during the store-retry window still re-calls on recovery. That is the
  pre-existing crash-mid-call semantics, capped by the reservation, and strictly better
  than before, when the step re-ran the whole activity up to 3 times.
- Journal: still IDs-only. The step output is `{status, output_id | failure_class}`, and
  errors carry labels only.

**ADR honesty:**
- The body of ADR 0002 decision 7 (`:101-111`) describes the change accurately.
- But three statements of the old principle remain stale (new Minor N2):
  - the decision's heading still reads "One retry owner: the DBOS step" (`docs/adr/0002-durable-execution.md:94`);
  - the repository contract still says "the DBOS step is the only retry owner"
    (`CLAUDE.md:31-32`);
  - `identity/failures.py:5` still calls the step "the single retry owner" for every
    transient failure.

### `tools.localenv --rotate-master-key` beside `make rotate-master-key`

**Not dangerous on its own, but a redundant parallel path. Remove it.**
- It only adds `v<N+1>`. Every key version is still on disk, and `load_keyring` loads them
  all, so nothing is stranded.
- Stranding needs a deleted old key file. The only documented point at which deletion is
  allowed is after `make rotate-master-key` or `make reseal` succeeds, and `reseal` now
  refuses success while any row is stale.
- Old habits fail loudly: `nessa.cli reseal-credentials` no longer exists (`cli.py`
  subcommand `reseal`).
- The real hazard is a combination (new Minor N3):
  - The user runs `localenv --rotate-master-key`, or `make rotate-master-key` fails after
    adding the key but before the restart.
  - Then the user runs `make reseal`, as the runbook advises for an interrupted rotation
    (`runbook.md:18,54-55`).
  - Reseal moves every record to `v<N+1>`. The running API and worker loaded their keyring
    at startup without that version.
  - Until they restart, `GET /runs` and export return 500, and the worker fails runs with
    `unknown_failure:MasterKeyError`.
  - No data is lost.
- The flag is still advertised in the module docstring (`tools/localenv.py:8`), and it
  contradicts the repository's no-parallel-paths rule.
- Fix:
  - delete the flag (`localenv.py:8,93-98`);
  - have `tools.stack reseal` restart api and worker first, or refuse to reseal while
    they run with an older keyring.

### New 403 for clients outside loopback and the internal subnet

**It cannot lock out the Compose path, and headers cannot spoof it.**
- Legitimate paths:
  - The edge connects from its own internal-subnet address.
  - The API's `client_networks` is loopback plus the subnets from its own route table
    (`localnet.py:36`, from `main.py`).
  - `test_local_stack.py:299` asserts that the API's computed networks equal
    `docker network inspect`, and every stack test reaches the API through the edge.
  - The health check comes from 127.0.0.1 (`compose.yaml:92`).
  - T4's `web` container will sit on the same internal network.
- Spoofing:
  - The client address comes from `scope["client"]`, which uvicorn sets from the socket
    peer.
  - uvicorn 0.54.0 has `proxy_headers=True` by default, but trusts `X-Forwarded-For`
    only from `FORWARDED_ALLOW_IPS`, default `127.0.0.1,::1` (uvicorn `config.py:363`).
    The compose command sets neither (`compose.yaml:74`).
  - The edge's peer address is not trusted, so forwarded headers relayed through it are
    ignored. Host is not consulted for this check.
  - Only a process already on the API container's loopback could rewrite its own address.
- Fail-closed cases: a missing client and a non-IP client (`testclient`) are refused. An
  IPv4-mapped IPv6 peer would be refused too.
- Residual hardening is in new Minor N4: run on a Linux host rather than in a container,
  and pin `--no-proxy-headers`.

### Revocation-final trigger and r0003 receipts migration

**Correct, tested as the runtime role, forward-only documented, with one untested
policy.**
- The trigger (`r0003...py:24-41`):
  - it refuses any change to `revoked_at` or `revoked_by` once revoked, and any change to
    a set `replaced_by`;
  - `replacements_are_revoked` (`:42-43`) forbids a replacement link on a live key;
  - the API role cannot drop or disable it, because it does not own the table.
- Reseal's UPDATE of sealed columns on revoked rows passes the trigger: the rotation test
  seeds revoked credentials (`test_master_key_rotation.py:77`).
- `test_credentials.py:125` runs every refusal as `pg_api` with RLS in force, which shows
  the rows were visible and the trigger, not RLS, refused.
- Receipts:
  - an FK with cascade, a backfill, NOT NULL, an index;
  - the WITH CHECK subquery is evaluated under the API role's workspace policy;
  - the positive path runs as `nessa_api` through the API, with cascade and reset-demo
    covered.
- Not tested: a negative WITH CHECK case as `pg_api` (a receipt naming another actor's
  workspace). Folded into N5.
- Forward-only: the docstring, `downgrade()` raises, and `runbook.md:58-63`.

### Per-scope cumulative live-call cap

**Enforced before any call, tested offline, configurable, conservative. Not atomic.**
- `run_smoke` checks the cap through `authorise(..., spent=ledger.spent(scope))`
  (`live_smoke.py:419-421`) before `smoke_stack` builds anything (`:427`), so the check
  runs before the key is stored.
- Unknown costs count their full reservation (`usage_ledger.py:67-77`).
- Defaults are 9 calls, 3 production and $0.30 (`live_smoke.py:89-96`); the scope has 1
  call so far.
- Tested offline: `test_live_smoke.py:87`, `test_usage_ledger.py:74`.
  `SmokeSettings(_env_file=None)` with a dummy key, so `.env` is not read.
- Not atomic with the ledger. It reads and checks at the start and appends at the end,
  with no lock (new Minor N6).

## New issues in the fix diff

### Critical
None.

### Important
None.

### Minor
- **N1: a failing worker stop skips the R5 ledger entirely.**
  - Where: `backend/tools/live_smoke.py:338-350` with `tools/stack.py:87-88,104-107`.
  - What happens:
    - `target.stop_worker()` is the first statement of `smoke()`'s `finally`.
    - `Stack.stop` raises `RuntimeError` when `compose stop` exits non-zero
      (`compose(check=True)`).
    - That exception aborts the `finally` before any ledger row is written.
    - `smoke_stack`'s `finally` then runs `stack.down()`, which removes the volumes, so
      the attempt rows are gone.
  - Result: calls that reached Meta are never ledgered, and the stack is torn down.
  - Related gaps:
    - On `TimeoutExpired`, `compose kill` runs with `check=False` and nothing confirms the
      worker is dead.
    - The leak scan (`:336`) runs before the worker stops, so logs written after it are
      not scanned.
  - Fix:
    - wrap the stop;
    - if the worker cannot be confirmed stopped, still read the attempts *and* fall back to
      `ledger_possible_calls`;
    - scan the logs after the stop.
- **N2: the retry-owner principle is stated three ways, and two are now wrong.**
  - Where: `docs/adr/0002-durable-execution.md:94` (heading), `CLAUDE.md:31-32`,
    `backend/src/nessa/identity/failures.py:5`.
  - Fix: one owner per failure class. The DBOS step owns provider transients; the
    activity's store budget owns store transients; they never overlap.
- **N3: the parallel master-key path, and a `make reseal` that does not reload.**
  - Where: `backend/tools/localenv.py:8,93-98` and `backend/tools/stack.py:145-148`.
  - See the adjudication above.
  - Also: rotation now restarts the worker, so an in-flight call is recovered and may be
    made again (reservation-capped). The runbook does not say so (`runbook.md:17`).
- **N4: the client check overclaims when the API runs on a Linux host.**
  - Where: `backend/src/nessa/localnet.py:1-7,36-42`, and ADR 0004 decision 2 ("even if
    the API were started on a public interface").
  - What: outside a container, every directly connected subnet on an interface with no
    default route counts as internal: `docker0`, libvirt, a VPN, a second NIC.
  - Effect: clients on those subnets pass the check. On macOS (no `/proc/net/route`) the
    check is loopback-only, which is correct.
  - Fix: enable the internal subnets only by explicit container configuration and use
    loopback-only otherwise.
  - Optionally: add `--no-proxy-headers` to `compose.yaml:74`, so a future
    `FORWARDED_ALLOW_IPS` can never let `X-Forwarded-For` set the client address.
- **N5: the receipt backfill drops receipts it could have attributed, and one claim is
  false.**
  - Where: `backend/src/nessa/migrations/versions/r0003_final_revocation_workspace_receipts.py:8-10,48-53`.
  - What is dropped: every receipt whose response lacks `workspace_id`. That is all
    submit-run, credential and spend-limit receipts: `RunOut`, `CredentialOut` and
    `SpendOut` carry no workspace ID. Joining on `run_id` or `credential_id` would have
    attributed them.
  - What is false: "every command checks its version or state first". Run submission
    carries no expected version (ADR 0004 decision 7), so a client retry of a pre-upgrade
    submission with the same key creates a second run.
  - Impact: negligible before release.
  - Fix:
    - attribute through joins, or correct the docstring;
    - add a `pg_api` negative test for the new WITH CHECK.
- **N6: the per-scope cap is check-then-append without a lock.**
  - Where: `backend/tools/live_smoke.py:419-421`, `tools/usage_ledger.py`.
  - What: two concurrent `make live-smoke` runs both pass `authorise`. They share project
    `nessa-l0-smoke`, so the second's `stack.down()` tears down the first, which then
    ledgers 3 possible calls.
  - Overshoot: at most one invocation (3 calls, ≤ $0.10).
  - Fix: an exclusive `flock` on the ledger, held from `authorise` to the final append.
- **N7: polish.**
  - `edge.py:59-75`: `getaddrinfo` has no timeout (`CONNECT_TIMEOUT_S` bounds only the
    connect), so a slow resolver holds client connections.
  - `live_smoke.py:63-70`: the "worst case" comment omits the per-attempt
    prepare and settle store budgets (about 723 s, not 483 s). This is not load-bearing
    now that the worker is stopped first.
  - `test_live_smoke.py:99` asserts the constant against its own formula.
  - `tests/domain/test_worker_loop.py:22-24` monkeypatches the worker's own functions.
    Behaviour is covered by `test_durable_runs.py:193`.

## Assessment
**Task quality:** Approved

**Reasoning:** All 30 listed findings are fixed. Every behavioural fix has a covering test
whose assertions fail on the `d4f8728` behaviour, with A-M3 the stated coverage-only
exception. The declared design changes (the activity-owned store budget, the client check,
the trigger and receipts migration, the scope cap) are sound. The new issues are Minor.
N1, a robustness gap in the R5 ledger on a docker-failure path, and N3, a reseal that does
not reload the running processes, are the two worth fixing next.
