# Task 3 report: Sprint 1 backend (S1.1–S1.3): local platform, persistence, identity, secrets

- Branch `l0-local-release`, base `ff449da`. Commits `a31fd42..d4f8728` (5).
- Status: **DONE_WITH_CONCERNS** (concerns in section 7; none blocks Task 4).

| Commit | Subject |
|---|---|
| `a31fd42` | Add the local platform: identity, versioned profiles and loopback stack |
| `2556aef` | Add encrypted keys, durable model runs and spend reservation |
| `85bbe41` | Ledger every live-smoke attempt, or every possible call if unreadable |
| `86ba7db` | Record the first make live-smoke run in the usage ledger |
| `d4f8728` | Document the local platform and close the Task 3 register rows |

## 1 What was implemented

### Command contract and stack (S1.1)
- `Makefile`: `setup`, `dev`, `demo`, `check`, `acceptance`, `live-smoke`, `stop`,
  `reset-demo` (+ `status`). Logic in `backend/tools/` (`setup.py`, `localenv.py`,
  `stack.py`, `live_smoke.py`); every docker call has a timeout.
- `compose.yaml` (project `nessa-l0`; ports API 58000, emulator 59099, PostgreSQL 56432,
  web 53000, all 127.0.0.1): PostgreSQL 16.15 (digest-pinned), Firebase Auth emulator
  (`docker/auth/`, promoted from the spike Dockerfile, deterministic seed imported on every
  start: `ada@`/`ben@` invited, `uninvited@nessa.test` not), one-shot `migrate`
  (`nessa.cli setup-database`: Alembic, DBOS schema with runtime-role grants, seed), API
  (uvicorn factory), DBOS worker, `edge` relay, and the Next.js slot (`web`, Compose
  profile, builds `apps/web` when Task 4 adds it). Health checks on every service.
- **Egress block:** every service is on an `internal: true` network. Measured on this
  machine: such networks block egress but also stop port publishing, and a no-NAT bridge
  does not block egress on Docker Desktop. So `nessa.edge` (stdlib TCP relay, tested) is
  the only container also on a normal bridge and publishes fixed routes on 127.0.0.1.
  `compose.live.yaml` (`make dev`) gives the worker alone an egress network.
- Secrets: `make setup` creates `NESSA_HOME` (default `~/.nessa/l0`, refused inside the
  repository): six generated PostgreSQL passwords and master key `v1`, dirs 0700, files
  0600, never overwritten. Mounted as Compose secrets / read-only key directory.
- Fail-closed config (`nessa/config.py`): `NESSA_ENVIRONMENT` must be `local`, a `demo-`
  project, local emulator host, local allowed hosts, exact loopback origins, passwordless
  DB URLs, owner-only key files; the API and worker also validate the model choice.
- Deterministic seeding (`nessa/seed.py`): two invited actors (uuid5 IDs) and the fixture
  workspace "P01 demo (synthetic)" built from `fixtures/m0/personas/P01.json` (source pinned
  by path + SHA-256; fields the fixture lacks stay `unasked`). `reset-demo` recreates only
  it, keeping its ID and continuing event numbers.

### Persistence, versions, envelopes, outbox, ownership (S1.2)
- Alembic (forward-only, hand-written SQL): `r0001` (actors/invitations, workspaces with
  data mode and immutable synthetic label, append-only profile versions, source references,
  commit-ordered events, idempotency receipts; RLS for `nessa_api`), `r0002` (sealed
  credentials, spend limits, runs pinned to model + data mode, transactional outbox,
  model attempts = spend reservation/reconciliation, sealed run outputs; RLS for
  `nessa_worker`, scoped by `nessa.run_id`).
- Roles (initdb from secret files): `nessa_migrator`/`nessa_dbos_owner` (setup only),
  `nessa_api`, `nessa_worker`, `nessa_dbos_runtime` (runtime; non-owner, no BYPASSRLS).
- API v1 (FastAPI 0.162.0): `/v1/me`; workspaces (create, list with cursor, get, rename
  with expected version); profile (get, PUT with expected version, versions, sources);
  credentials (store with consent, rotate, revoke, list); spend (get, set limits); runs
  (POST 202 + `Location`, get, list); events (JSON page and resumable SSE with
  `Last-Event-ID`); export (paged through every row; credential metadata only). Typed
  envelope `{code, message, retryable, stage, correlation_id, details}`; validation errors
  never echo input. Host/Origin guard; JSON access log (paths only).
- Identity: firebase-admin `verify_id_token(check_revoked=True)` against the emulator, then
  an active invitation by verified email bound to the UID at first sign-in
  (`nessa.resolve_actor`, SECURITY DEFINER).
- Profile document (Sprint 1 subset: name, role, ≤3 cities, ≤3 targets, weekly study
  hours, two `Money` caps), each field with a field state (`unasked`/`provided`/`unknown`/
  `skipped`/`prefer_not_to_say`) and a server-assigned source reference. Version 0 = never
  saved. A fourth city/target is `LIMIT_EXCEEDED`.

### Keys, master key, spend, logging (S1.3)
- Keyring promoted from `spikes/durable/sealing.py` with versioned key files and
  owner-only checks; credentials sealed at once with record-bound associated data; API role
  cannot select nonce/ciphertext. Master-key rotation: `tools.localenv
  --rotate-master-key` then `nessa.cli reseal-credentials` (tested).
- Bounded activity (`nessa/identity/activity.py`, promoted from `spikes/durable/workflow.py`)
  under the worker role: reuse accepted output first (M4), re-check access, model mode vs
  synthetic label, active key, reserve worst-case spend under an advisory lock, record the
  attempt, open the key just in time, call Meta (`nessa/identity/meta.py`, factory split out
  of the spike CLI: M7), store the sealed output and usage in one transaction (M4).
  DBOS workflow (`workflow.py`): one retry owner; store outages are a label-only transient;
  exhaustion publishes `provider_unavailable` or `failed/app_store_unavailable`; publication
  retries ~34 min; DBOS-`ERROR` reconciler. Worker (`worker.py`): DBOS with
  `run_migrations=False` and portable JSON, outbox dispatch, heartbeat health check,
  10 s shutdown watchdog (bounded stop).
- Spend (`spend.py`, `spend_limits.py`): integer nano-USD, per-run and per-UTC-month limits
  (defaults $0.10 / $1.00, configurable), submission pre-check, binding reservation in the
  worker, unknown cost keeps the reservation.
- Redacted logging (`nessa/logs.py`): exception messages dropped, tokens/URL passwords/
  process secrets scrubbed, DBOS and uvicorn routed through it.
- Contributor ruling enforced in code (non-synthetic runs pinned to Standard; activity
  refusal) and in the database (`contributor_models_only_for_synthetic_data` CHECK, with a
  composite FK holding the run's label equal to its workspace's).

### Spike retirement and docs
- `backend/spikes/` deleted after promotion. Product → `backend/src/nessa`; verification
  tooling → `backend/tools/leak_scan.py`, `usage_ledger.py` and `backend/tests/support/`
  (fake model, worker entry with SIGKILL crash points, capability-probe negative control).
- Docs: ADR 0004 (new), ADR 0002/0003 updated, `docs/dependencies.md`, `docs/runbook.md`
  (new), `CLAUDE.md` (TODO(Task 3) markers replaced), register rows, a pointer in
  `docs/evidence/sprint-0-spike.md`.

## 2 Rulings (simplest reading that keeps every Global Constraint)

1. **Module layout.** `nessa/identity` is the plan's "Identity and execution" module
   (access, workspaces, keys, runs, spend); `nessa/profile` is "Profile and exploration";
   `nessa/api` is the HTTP adapter; kernel modules (`config`, `db`, `errors`, `logs`,
   `money`, `vocabulary`, `edge`, `seed`, `cli`) are shared. Vendor/SQL imports only in the
   adapters listed in `tests/architecture/test_boundaries.py`.
2. **Where the spikes went.** Product behaviour into `src/nessa`; test and evidence tooling
   (leak scanner, R5 ledger, stack harness, fakes) into `tools/` and `tests/support/`, so
   test code does not ship in the image. The spike's stream/search qualification CLI was
   not kept (Sprint 0 evidence; in git at `ff449da`).
3. **Egress block via internal network + edge relay** (measurements above). ADR 0004.
4. **Identity via firebase-admin** (the dependency matrix's Task 3 choice; spec names the
   Admin SDK revocation check). Emulator tokens are unsigned, so local processes can mint
   them: local-only identity, documented.
5. **Sprint 1's model run is a connection check** (spec §16 "check availability at key
   setup"): fixed synthetic prompt, no workspace data, so the whole chain is proven without
   sending a profile anywhere. Later run kinds reuse the activity.
6. **Spend unit is nano-USD** (Meta bills USD; integer, never float); GBP minor units stay
   the product money unit.
7. **Live smoke = one run, at most 3 attempts (= MAX_CALLS)**, so the "≤3 live calls" cap
   holds even with retries; no separate invalid-key call (the 401 path is covered offline
   with a key-echoing fake, and live in Sprint 0).
8. **Revocation and rotation act at call time**: the worker resolves the workspace's active
   key, not one pinned on the run.
9. **Live-vacancy workspaces are refused** (`MODE_NOT_SUPPORTED`) until Adzuna exists;
   demo workspaces never take keys or call models; the demo runtime refuses model runs.
10. **Another actor's workspace is 404, not 403** (existence not disclosed).
11. **Forward-only migrations** (restore from backup instead of downgrade).
12. **Strict schema kept**: Pydantic AI drops `strict: true` when string length keywords
    exist, so `ConnectionCheckResult` validates lengths in a validator.
13. **`asyncio.run(agent.run())` instead of `run_sync`**, which calls the deprecated
    `asyncio.get_event_loop()` (fails under warnings-as-errors).
14. **DBOS LISTEN/NOTIFY kept** (changing it needs private DBOS API); the Sprint 0 hang is
    bounded by the watchdog and Compose grace instead.
15. **`make acceptance` rebuilds images** (cached) so containers run the checked-out code.

## 3 Checks run (final tree, `d4f8728`)

| Command | Result |
|---|---|
| `make check` | ruff format: 109 files formatted; ruff: all passed; mypy strict: no issues in 109 files; pytest: **153 passed**, 89 deselected; fixture validator `"status": "passed"`. 2.2 s wall (mypy cache warm) |
| `make acceptance` | **89 passed** in 96.9 s (integration 79 on real PostgreSQL 16.15 + DBOS 3.3.0 + emulator; stack 10 on the real Compose stack). Also passed on `2556aef` (96 s) |
| Command contract by hand (2026-10-28, default `NESSA_HOME`) | `make setup` created `~/.nessa/l0` (0700/0600) and built images; `make demo` 8 s, `/readyz` ready, foreign Host → 400, Ada read the fixture profile through the published ports, a run in demo → `MODEL_UNAVAILABLE`; `make reset-demo` ok; `make dev` 6 s; `make stop` 1.1 s, all stopped, volume kept |
| Mutation check | adding `import sqlalchemy` to `nessa/profile/document.py` made the vendor-boundary test fail; restored |

Acceptance coverage highlights: all twelve Sprint 0 durability scenarios against product
code (SIGKILL mid-call → `[interrupted/unknown, succeeded]`; after acceptance → no second
call, usage kept; after dispatch → one workflow; replay; 429; 503; 401 echo; connection;
unexpected error; revoked key; DBOSDurability negative control) each with a leak scan of
both databases and worker logs (key fragments, profile and output sentinels); rotation
while queued uses the new key; revoked access hides the key from the worker; worker RLS
per run; concurrent reservations stay within the limit; app-DB outage → typed terminal
state; Contributor refused at API and database; populated `0001` upgrade loses nothing;
master-key reseal; identity (uninvited, revoked token, revoked invitation, unverified
email, rebinding); cross-workspace isolation on every endpoint incl. SSE; unauthorised
local origin cannot change anything; demo egress blocked (API, worker, emulator,
PostgreSQL) with an edge positive control; live mode gives only the worker a route out;
profile survives a full stop/start; reset-demo is scoped; unsafe config refused in the
real container.

TDD evidence (test written first, RED, then GREEN): profile document (RED: module
missing → 17 passed), keyring (RED → 16), redacted logging (RED → 4), edge relay (RED → 8),
failure classification (RED → 17), spend policy (RED → 12), model choice (RED → 5).
Bugs found by tests first: PL/pgSQL `found` shadowing `FOUND` (identity test RED → fixed
→ 7 passed); NO ACTION FK firing mid-cascade in `reset-demo` (stack test RED → CASCADE →
GREEN); schema not strict (request-shape test RED → validator → GREEN); revocation within
the token's issue second (test helper fixed); DBOS logs bypassing redaction (seen in a
worker log; the stack test now asserts the redacted form).

## 4 Live calls (R5)

| Ledger # | Command | Model | Outcome | Tokens in/out (reasoning) | Cost |
|---|---|---|---|---|---|
| 12 | `make live-smoke` (once) | `muse-spark-1.3-contributor` (test, Contributor, synthetic workspace) | ok: run `complete`, typed output; leak scan of 40 rows/logs/responses clean | 114 / 93 (62) | $0.000030 (114 × $0.10/M + 93 × $0.20/M) |

One live call in total (cap 3). No production-model call. Running total $0.019707
(upper bound $0.024707 with the Sprint 0 search items). Remaining credit: not exposed by
any documented API. Prices: https://dev.meta.ai/docs/pricing-rate-limits (2026-10-27).

## 5 Register

Verified with tests (rows marked in `docs/requirements-register.md`): BND1-03, BND1-10,
BND1-11 (backend services), BND1-13, BND1-14, ARC1-01, ARC1-05, ARC1-06, ARC1-07, ARC1-08,
ARC1-09, TEST1-12, VERSIONS-01, VERSIONS-03 (profiles), MODEL-02, MODEL-05, MODEL-09,
DUR-01, DUR-02, DUR-04, DUR-08, API-01, SEC-01, SEC-02, SEC-03. Shared rows kept `planned`
with the Task 3 part recorded: BND1-12, ARC1-10, ARC1-11, STATE-01, STATE-07, MODEL-04,
MODEL-06, MODEL-07, MODEL-08, DUR-03, API-02, API-03, API-04, SEC-04, SEC-07.
**Not done: DUR-05** (cancellation).

## 6 For Task 4

- Contract: `GET http://127.0.0.1:58000/openapi.json`; request rules in `docs/runbook.md`
  (bearer token, `Origin`, `Idempotency-Key`, `expected_version`, 202 + `Location`, SSE
  with `Last-Event-ID` and `event: reauthenticate`). Every enum is in the schema once.
- Compose `web` slot: profile `web`, build `./apps/web`, `NESSA_API_INTERNAL_URL`, port
  53000 relayed by the edge; the API already accepts `http://127.0.0.1:53000` and
  `http://localhost:53000`, and `api:8000` as a Host. Add the web container to the demo
  egress probe and extend the lockfile check to the JS lock.

## 7 Blocked, not run, concerns

- **DUR-05 run cancellation not implemented** (register owner T3, T13; not among the brief's
  deliverables). The `cancelled` state exists; a cancel command, DBOS cancellation and
  reaching the in-flight call are open. Recommend a run-lifecycle owner before Sprint 3.
- The DBOS-`ERROR` reconciler is implemented but no test reaches it (needs >30 min outage).
- Not run: amd64; Linux hosts (Compose file secrets are bind mounts; owner-only files may be
  unreadable by container users there); backup/restore (SEC-07, T16); workflow-history
  deletion (DUR-06); browser-side checks (T4).
- The emulator lets any local process mint tokens for any account (unsigned): accepted by
  design for L0, documented (ADR 0001, 0004). The PostgreSQL superuser is reachable on
  127.0.0.1:56432 with the generated password from `NESSA_HOME`.
- `firebase-admin` brings ~30 transitive packages (Google client stack, grpcio); only
  `firebase_admin.auth` is used. Licence notes for new packages not written (SEC-07).
- The API process holds the master key (it seals keys and opens run outputs); its database
  role cannot read credential ciphertext, which is the boundary that keeps keys from it.
- `make acceptance` needs the base images cached (first build needs network).
- The default dev stack (`nessa-l0`, stopped) and `~/.nessa/l0` remain from exercising the
  commands, as `make stop` intends. Remove with `docker compose -p nessa-l0 down -v` and
  deleting `~/.nessa/l0` if unwanted.
- Not claimed: any human gate (R2). No visual or UI work in this task.

## 8 Paths a reviewer can skip

`backend/uv.lock` (lockfile); `docker/auth/seed/auth_export/accounts.json` (generated
emulator seed; demo passwords are non-secret test credentials); `docs/evidence/live-usage.md`
(generated from the JSONL); the deleted `backend/spikes/` tree.

---

# Fix round 1 (FIX_BASE `d4f8728`)

- Fix list: `task-3-fix-round-1.md`; findings in `task-3-review-A.md` (A-) and
  `task-3-review-B.md` (B-). Every listed item is fixed. No live Meta call was made.
- Commits `d4f8728..12a016e` (6), on `l0-local-release`, not pushed.

| Commit | Subject | Findings |
|---|---|---|
| `d60938a` | Reseal every sealed record, make revocations final, scope receipts | A-I1, A-M2, A-M3, A-M8, A-M9, A-M10, B-M2 |
| `8d44d49` | Keep the request boundary closed: pinned edge targets, client check, fail-closed scopes | A-M1, A-M4, A-M5, A-M6, A-M7, A-M11, B-M11 |
| `1a8e006` | Never lose a paid result or re-call after a crash; reconcile from the run's records | B-M1, B-M3, B-M4, B-M5 |
| `037d793` | Ledger every live-smoke call: stop the worker first, cap each budget scope | B-I1, B-M12 |
| `808669b` | Install the auth emulator from a committed pnpm lockfile | A-M12 |
| `12a016e` | Dedupe response conversions, tighten tests, and bring the docs in line | A-M13, A-M14, A-M15, B-M6, B-M7, B-M8, B-M9, B-M10, licence notes |

"RED" below means the covering test was run against the unfixed code and failed for the
reported behaviour; "mutation" means the fix was removed temporarily, the test failed,
and the fix was restored. All commands ran from `backend/` unless shown otherwise.

## Must-fix

### A-I1: master-key rotation reseals everything the master key seals
- Change: `nessa.cli reseal` (renamed from `reseal-credentials`) reseals credentials and
  run outputs, then scans `information_schema` for every `nessa` table with a
  `key_version` column and raises `ResealIncompleteError` if any row is still on an older
  version. `tools/stack.py rotate-master-key` adds `v<N+1>`, restarts the API and worker
  (`compose restart`, so the mode is kept), waits for health, then reseals. New
  `make rotate-master-key` and `make reseal`; the runbook procedure uses them
  (`docs/runbook.md`, "Keys and secrets"); ADR 0004 decision 8 updated.
- Tests: `tests/integration/test_master_key_rotation.py` (now seals a run output too,
  deletes `v1.key` after the reseal and opens every output and key; a table with a
  `key_version` column the reseal does not know makes it fail);
  `tests/stack/test_local_stack.py::test_master_key_rotation_reloads_the_running_api_reseals_and_keeps_demo_offline`.
- RED: against `d4f8728` the rewritten module did not import (`ImportError: cannot import
  name 'ResealIncompleteError' from 'nessa.cli'`), so its RED is structural, not
  behavioural; the review's reproduction (outputs unreadable after `v1.key` is retired) is
  what the test now asserts.
- GREEN: with the commit's other new tests, `46 passed in 12.16s`; the stack test
  `1 passed, 10 deselected in 15.57s`.

### B-I1: the live smoke ledgers every call
- Change (`tools/live_smoke.py`): `smoke()` stops the worker in its `finally` before it
  reads the attempts, then ledgers every attempt of the smoke workspace. `RUN_TIMEOUT_S`
  is derived from the worst case: 3 x `REQUEST_TIMEOUT_S` (120 s) + backoff (1 s + 2 s) +
  the activity's 60 s store budget + 60 s, i.e. 483 s. The smoke workspace's run and
  period limits are set to the invocation's worst case (`PUT /spend/limits`), so the
  product's own reservation also refuses a fourth call. The orchestration takes a
  `SmokeTarget`: `StackTarget` for the isolated Compose stack, and in tests the
  integration stack with a fake-model worker.
- Test: `tests/integration/test_live_smoke_ledger.py::test_every_call_the_worker_made_is_ledgered_even_after_the_poll_gave_up`
  (fake model fails every call and logs each one; the poll gives up after 0.5 s; the test
  then waits 6 s, the time a slow teardown leaves for retries; ledger rows >= calls made).
  Plus `tests/tools/test_live_smoke.py::test_the_smoke_waits_out_the_run_s_worst_case`.
- Mutation: with the `stop_worker()` line removed, `uv run --locked pytest -q -m integration tests/integration/test_live_smoke_ledger.py`
  failed: `assert 1 >= 3` (1 row ledgered, 3 calls made). Restored: `1 passed in 20.72s`.

### B-M1: the DBOS-`ERROR` reconciler
- Change: `activity.reconcile()` publishes `succeeded(output)` when an accepted output
  exists, otherwise the recorded terminal failure, otherwise `unknown_failure`; it skips
  runs that are already terminal and never calls the model. `worker.loop_pass()` advances
  `next_reconcile` before reconciling, so a failing pass waits its 60 s interval and the
  heartbeat continues. ADR 0002 decision 7 and ADR 0004 decision 11 now name the tests
  and say the `ERROR` state is simulated.
- Tests: `tests/integration/test_durable_runs.py::test_the_reconciler_publishes_an_errored_workflow_s_accepted_output`
  (a completed run is set back to `running` and its DBOS workflow to `ERROR`; a new worker
  reconciles it to `complete` with the same output and no new attempt);
  `tests/domain/test_worker_loop.py`.
- RED: the integration test failed: `('failed', ..., 'unknown_failure') == ('complete', ...)`;
  the loop test failed (no `loop_pass`; the old loop retried every 0.2 s).

### B-M2: only `PRODUCTION=1` selects the production model
- Change: `Makefile` uses `$(if $(filter 1,$(PRODUCTION)),--production-model,)`.
- Test: `tests/tools/test_live_smoke.py::test_only_production_equals_one_opts_in_to_the_production_model`
  (`make -n live-smoke PRODUCTION=` for `1`, `0`, `false`, `yes` and empty).
- Evidence: after the change, a dry run printed the flag for `PRODUCTION=1` only (`0`,
  `false`, `yes` and empty: nothing). Not run RED here; the review's dry run had shown
  `PRODUCTION=0` printing the flag.

### B-M3: `execute()` never raises
- Change (`identity/activity.py`): usage is built inside `_call`'s guarded path. Counts
  the registry rejects (more cached than input tokens) end the attempt
  `unknown_failure:ValueError` with spend `unknown`; the whole of `execute` is guarded.
- Test: `test_durable_runs.py::test_inconsistent_provider_usage_fails_typed_with_an_unknown_cost`
  (new fake mode `inconsistent_usage`).
- RED: the run stayed `running` (`TimeoutError: timed out after 60.0s waiting for run`).

### B-M4: a crash after a recorded terminal failure does not call again
- Change: `_prepare` returns a terminal failure an earlier execution recorded, with a
  `reused_failure` attempt (no reservation), as it already did for an accepted output.
  `failures.recorded_failure()` maps attempt labels to failure classes. The test crash
  point is renamed `after_settle` (it fires after either outcome is committed).
- Tests: `test_durable_runs.py::test_a_crash_after_a_recorded_failure_returns_it_without_a_second_call`;
  `tests/domain/test_failures.py::test_only_terminal_attempt_outcomes_name_a_recorded_failure`.
- RED: the second attempt was a new paid call: `('provider_authentication', 'unknown', 809600) == ('reused_failure', 'none', 0)`.

### B-M5: a separate store budget, so a short restart keeps the paid result
- Change: the activity retries its own transactions (prepare, then settle) with backoff
  for `ActivityRuntime.store_retry_budget_s` (60 s in the product; the test worker reads
  `NESSA_TEST_STORE_RETRY_BUDGET_S`), keeping the call's result in memory. Past the budget
  the run fails `app_store_unavailable` with no step retry, because a step retry would call
  the model again. The DBOS step now retries only `TransientProviderError`;
  `AppStoreUnavailableError` and its `classify_exhausted` branch are removed (behaviour
  change: store failures no longer reach the step's retries).
- Tests (`test_worker_boundaries.py`): `test_a_short_app_database_outage_mid_call_keeps_the_paid_result`
  (12 s lockout during the call; the run completes on that one attempt, `succeeded`/`reconciled`);
  `test_an_outage_longer_than_the_store_budget_ends_in_a_typed_terminal_state`
  (budget 2 s; `failed/app_store_unavailable`, the attempt `interrupted`/`unknown`).
  `test_failures.py` lost its `AppStoreUnavailableError` assertions with the class.
- RED: the short-outage test failed: `('failed', 'app_store_unavailable') == ('complete', None)`.
- Covering run for B-M1/M3/M4/M5: `uv run --locked pytest -q -m integration tests/integration/test_durable_runs.py tests/integration/test_worker_boundaries.py`
  -> `23 passed in 85.47s`.

### B-M6: register closing rule
- Change: BND1-11 and MODEL-02 are `planned`, with the Task 3 part recorded as verified
  and the open part named (`docs/requirements-register.md`).

### B-M7: stale references
- Change: `model_registry.py` now cites `nessa.identity.model_choice` and the activity's
  re-check; `tools/localenv.py` cites `make rotate-master-key` / `make reseal`; the runbook
  rotation step is `make rotate-master-key`, which needs no exported `NESSA_HOME`.

### B-M8: the leak scan after rotation looks for both keys
- Change: `Scenario.retired_keys` (`tests/integration/durable.py`); the rotation test adds
  the replaced key before swapping in the new one, and the scan checks both.
- Test: `test_durable_runs.py::test_rotating_the_key_while_a_run_is_queued_uses_the_new_key`.

### B-M12: cumulative per-scope live-call cap
- Change: `Ledger.spent(scope)` returns calls, production calls and committed cost (known
  costs plus the full reservation of every unknown one). `authorise()` refuses before
  anything starts once the next invocation would exceed the scope's cap. Defaults
  (`SmokeSettings`): scope `live-smoke`, 9 calls, 3 production calls, $0.30; configurable
  through `NESSA_LIVE_SMOKE_SCOPE`, `_MAX_CALLS`, `_MAX_PRODUCTION_CALLS` and
  `_MAX_COST_NANO_USD`. The scope has 1 call ($0.00003) so far.
- Tests: `tests/tools/test_live_smoke.py::test_the_scope_s_cumulative_budget_refuses_once_the_next_invocation_would_breach_it`
  (3 cases), `tests/tools/test_usage_ledger.py::test_a_scope_s_spend_counts_its_calls_and_every_unknown_cost_at_its_reservation`.
- Mutation: with the three scope checks removed, `pytest tests/tools/test_live_smoke.py -k cumulative`
  -> `3 failed`. Restored: `uv run --locked pytest -q tests/tools` -> `26 passed`.
- Also: `Ledger.write_markdown()` now writes next to its own ledger, so tests can never
  overwrite `docs/evidence/live-usage.md`. The real table was regenerated: only its header
  text changed (the budget note).

### A-M1: the edge never follows outside DNS
- Change: new `nessa.localnet` reads the kernel route table: the internal subnets are the
  connected routes on interfaces without a default route. The edge resolves a target but
  connects only to an address inside those subnets. It logs `edge refused web:3000: ...`
  otherwise, and it refuses to start if no internal network is found.
- Tests: `tests/domain/test_localnet.py`, `tests/domain/test_edge_forwarder.py`;
  `tests/stack/test_local_stack.py::test_the_edge_relays_only_into_the_internal_network_and_refuses_an_absent_target`
  (the edge's and the API's computed networks equal `docker network inspect`; a connection
  to the web slot, whose target is absent in Task 3, is closed unanswered and logged).
- RED: the domain tests failed (module missing); GREEN `19 passed`. The stack probe was
  written with the fix and was not run against the old edge.
- GREEN: `uv run --locked pytest -q -m stack tests/stack/test_local_stack.py -k "edge or demo_mode or live_mode or only_the_edge"` -> `4 passed in 23.62s`.

### A-M2: revocations are final in the database
- Change: migration `r0003`: a BEFORE UPDATE trigger
  (`credential_revocation_is_final`) refuses clearing `revoked_at`/`revoked_by` or changing
  a set `replaced_by`; CHECK `replacements_are_revoked`.
- Test: `tests/integration/test_credentials.py::test_the_database_keeps_a_revocation_final_even_for_the_api_role`.

### A-M3: role-level isolation over the 0002 tables
- Test: `tests/integration/test_isolation.py`, parametrized over `EXECUTION_TABLES`. It
  passed at once: the policies were right; this was a coverage gap.

### A-M8: rotating or revoking a revoked key
- Change: new `CREDENTIAL_REVOKED` (409) for rotate and revoke of a revoked key.
- Test: `tests/integration/test_credentials.py::test_rotating_or_revoking_a_revoked_key_is_a_distinct_conflict`.

### A-M9: validation details never echo client keys
- Change: for `extra_forbidden` errors, `envelope._location()` replaces the client-chosen
  last segment with `<unexpected field>`.
- Test: `tests/integration/test_request_guard.py::test_validation_errors_never_echo_client_supplied_field_names`.

### A-M10: receipts belong to their workspace
- Change: migration `r0003` adds `command_receipts.workspace_id` with ON DELETE CASCADE
  and an index. It backfills from the stored response, deletes unattributable rows, sets
  NOT NULL, and tightens the API policy WITH CHECK to visible workspaces.
  `CommandResult(status, response, workspace_id)` carries it.
- Tests: `tests/integration/test_receipts.py::test_every_receipt_names_its_workspace_and_goes_when_the_workspace_goes`
  and `::test_reset_demo_removes_the_fixture_workspaces_receipts`; `test_migrations.py` populated upgrade (attributable receipt kept,
  unattributable dropped).
- RED for d60938a's behaviour tests: `5 failed, 37 passed` (both receipt tests, both
  credential tests, the validation-echo test), plus the rotation module's import error.
  GREEN: `46 passed`; then migrations + isolation `19 passed in 10.78s`; fast suite
  `158 passed`.

### A-M11: no client outside the machine
- Change: `RequestGuard` refuses (403 `CLIENT_NOT_ALLOWED`) any client whose address is
  outside loopback and the API's own internal subnet (`ApiDependencies.client_networks`,
  `local_networks()` at the composition root). A non-IP or missing client is refused too.
- Test: `tests/api/test_guard_and_envelope.py::test_a_client_outside_loopback_and_the_internal_network_is_refused`
  (192.168.1.20, 10.1.2.3, 8.8.8.8, `testclient`).

### A-M12: emulator image from a lockfile
- Change: `docker/auth/package.json` (firebase-tools 15.34.1) and `pnpm-lock.yaml`
  (pnpm 10.33.2, 575 packages); the Dockerfile runs `pnpm install --frozen-lockfile --prod`.
- Check: `docker build docker/auth` succeeded on arm64; the image started `healthy` with
  `--network none`; `firebase --version` printed `15.34.1`; the temporary image was
  removed. `make acceptance` rebuilt and used it.

## Cheap fixes

- **A-M4 / A-M5 / A-M6** (`api/guard.py`, `api/envelope.py`): WebSocket scopes are closed
  with 1008, and only `lifespan` passes through. Framework errors take a code from their
  status (404 `NOT_FOUND`, 405 `METHOD_NOT_ALLOWED`, other 4xx `REQUEST_REJECTED`). The
  guard catches unexpected exceptions: it logs the class and frames, and sends
  `INTERNAL_ERROR` with the correlation ID; the access log records 500. Test:
  `tests/api/test_guard_and_envelope.py`. RED: `7 failed`; GREEN: `10 passed` (now 9
  after one empty test was removed).
- **A-M7**: the stream re-verifies its token with `check_revoked` every `REVERIFY_S` (60 s)
  and ends with `event: stream_ended` / `UNAUTHENTICATED`. Test:
  `tests/integration/test_events.py::test_the_stream_ends_once_the_firebase_token_is_revoked`.
  RED: the stream kept sending keep-alives after revocation; GREEN `3 passed`.
- **A-M13**: `ProfileOut.of_version`, one `routes_runs.run_out`, and a public base class
  `ResponseModel`; export imports nothing private. Covered by the existing profile,
  run and export integration tests.
- **A-M14**: ADR 0004 decision 7 records the expected-version rule: the first run kind
  that reads the profile must take and pin the profile version.
- **A-M15**: the runbook's new "Upgrades and backups" section says migrations are
  forward-only and backup/restore is not implemented (SEC-07); r0001/r0002 docstrings
  point there instead of at a backup that does not exist.
- **B-M9**: `test_the_prompt_carries_no_workspace_data` asserts the request's
  `instructions` and `input` are exactly `INSTRUCTIONS` and `[PROMPT]`, and that the body
  has no other keys. `2 passed`.
- **B-M10**: `emulator_reachable` and its now-unused `urllib.error` import deleted.
- **B-M11**: stack probes use TEST-NET `192.0.2.1` instead of `1.1.1.1`; the edge control
  and the live-mode probes check the host listener only. The demo-mode API and worker
  probe still asks its resolver for `example.com`: that is the DNS-egress evidence, and
  in demo mode those containers have no route out.
- **Licence notes**: `docs/dependencies.md` lists the licences of firebase-admin and the
  34 packages in its tree (Apache-2.0, BSD, MIT, MIT-0, PSF-2.0, MPL-2.0 for certifi).
  SEC-07 records it. This is not a legal review.

## Final checks (tree `12a016e`)

- `make check` (repository root): `117 files already formatted`; ruff `All checks passed!`;
  mypy `Success: no issues found in 117 source files`; pytest
  `195 passed, 109 deselected in 1.45s`; fixture validator `"status": "passed"`.
- `make acceptance` (repository root), run once on the final tree:
  `109 passed, 195 deselected in 154.12s (0:02:34)`, exit 0. Every integration module and
  `tests/stack/test_local_stack.py` (12 tests) passed; the test projects
  (`nessa-l0-test`, `nessa-l0-stacktest`) were removed afterwards.
- The dev stack (`nessa-l0`) was not started this round and is stopped; no `nessa`
  container is running.
- No live Meta call; `docs/evidence/live-usage.jsonl` is unchanged (only the generated
  Markdown header changed).

## Concerns left after this round
- RED evidence is weaker for some items:
  - A-I1: structural only (an import error).
  - B-M2: not run RED here (the review's dry run is the RED).
  - A-M1: the stack probe was not run against the old edge (the domain tests were RED).
  - B-I1 and B-M12: shown RED by mutation.
- Intentional behaviour changes:
  - Store failures are no longer retried by the DBOS step; the activity's 60 s budget
    replaces those retries, and `AppStoreUnavailableError` is gone.
  - Inconsistent provider usage now fails the run `unknown_failure`, with the output not
    accepted and the cost unknown.
  - Rotating or revoking a revoked key is 409 `CREDENTIAL_REVOKED` instead of 404.
  - Framework 405s are `METHOD_NOT_ALLOWED`.
  - Clients outside loopback and the internal subnet get 403.
- The reconciler still lists every DBOS `ERROR` workflow each pass. Terminal runs cost one
  lookup each and are never republished. Errored workflows are not pruned.
- B-M11: the demo-mode API and worker probes still ask their resolver for `example.com`;
  that lookup is the DNS-egress evidence.
- `tools.localenv --rotate-master-key` still exists. It adds a key without resealing. The
  runbook no longer mentions it; `make rotate-master-key` is the documented path.
- r0001 and r0002 changed in their docstrings only, with no SQL change.
- The licence notes are metadata-based, not a legal review (rights review: not run,
  requires a human).

---

# Fix round 2 (FIX_BASE `12a016e`)

- Source: `task-3-rereview-1.md` (round 1 approved; new Minors N1–N7). All seven are
  fixed, except one line of N2 in `CLAUDE.md` that this round cannot change (below). No
  live Meta call was made.
- Commits `12a016e..a56c206` (4), on `l0-local-release`, not pushed.

| Commit | Subject | Findings |
|---|---|---|
| `4d1051f` | Ledger every possible call when the worker will not stop; lock the ledger | N1, N6, N7 (smoke part) |
| `0a59a46` | One master-key rotation path; reseal reloads the running API and worker first | N3 |
| `e6b2cd6` | Serve internal-subnet clients only when the API container opts in | N4 |
| `a56c206` | Bound edge name resolution, correct retry-owner and receipt claims, add a policy test | N2, N5, N7 |

Commands ran from `backend/` unless shown otherwise.

### N1: a failing worker stop no longer skips the ledger
- Change (`tools/live_smoke.py`):
  - `smoke()` catches any failure of `target.stop_worker()`, then still reads and ledgers
    the workspace's attempts (`ledger_workspace_calls`).
  - If the worker was not confirmed stopped, it also ledgers every further call the
    workspace's spend limits allow (up to `MAX_CALLS` in all) as possible calls with an
    unknown cost. Their purpose reads "worker not confirmed stopped".
  - It then raises `WorkerNotStoppedError`, after the ledger is written and before
    `smoke_stack` tears the stack down.
  - The leak scan now runs after the stop, so it sees every log line.
  - `StackTarget.stop_worker()` confirms the worker is gone (`stack.running()`), because
    `Stack.stop` falls back to an unchecked `kill`.
- Test: `tests/integration/test_live_smoke_ledger.py::test_a_worker_that_cannot_be_stopped_still_leaves_every_possible_call_ledgered`.
  An `UnstoppableTarget`'s stop raises and the fake-model worker keeps calling. The test
  then expects `MAX_CALLS` ledger rows, at least as many as the calls made.
- RED: `uv run --locked pytest -q -m integration tests/integration/test_live_smoke_ledger.py`
  gave `RuntimeError: docker compose stop failed (1)` (nothing ledgered), `1 failed, 1 passed`.
  GREEN: `2 passed in 29.85s`.

### N2: one retry owner per failure class
- Change:
  - ADR 0002 decision 7's heading now reads "One retry owner per failure class": the DBOS
    step owns provider transients, the activity's store budget owns store transients, and
    they never overlap.
  - The `identity/failures.py` docstring says the same.
- Not changed: `CLAUDE.md:31-32` still says "the DBOS step is the only retry owner". My
  instructions do not let an agent's message authorise edits to `CLAUDE.md`, so this line
  needs the user. Suggested text: "each transient failure class has one retry owner: the
  DBOS step for provider failures, the activity's store budget for store failures."

### N3: one rotation path; `make reseal` reloads first
- Change:
  - `tools.stack.reseal()` restarts a running API and worker (`compose restart`, mode
    kept) and waits for health before it moves any record to the newest key.
    `rotate_master_key()` is now "add a version, then reseal".
  - `tools.localenv --rotate-master-key` is removed.
  - Runbook and ADR 0004 decision 8 updated, including that a worker restart recovers an
    in-flight run, whose call may be made again within its reservation.
- Test: `tests/stack/test_local_stack.py::test_reseal_after_an_interrupted_rotation_reloads_the_running_api_first`.
  It adds a key version without restarting (the interrupted rotation), runs `reseal`, then
  stores a key through the running API. Every credential must be on the newest version.
- RED: `uv run --locked pytest -q -m stack tests/stack/test_local_stack.py -k rotation`
  failed with `assert {2, 3} == {3}` (the stale API sealed with v2). GREEN: `2 passed`.

### N4: internal-subnet clients only by explicit container configuration
- Change:
  - `localnet.client_networks(internal=...)` returns loopback only, unless
    `NESSA_API_INTERNAL_NETWORK_CLIENTS` (new `ApiSettings.internal_network_clients`,
    default false) is set. `compose.yaml` sets it for the API container only.
  - If it is enabled but no internal network is found, it fails closed (`RuntimeError`).
  - The API command adds `--no-proxy-headers`.
  - ADR 0004 decision 2 now states what is enforced; the localnet docstring is corrected.
- Tests:
  - `tests/domain/test_localnet.py::test_the_api_serves_loopback_only_unless_its_container_says_otherwise`
    and `::test_enabling_internal_clients_without_an_internal_network_fails_closed`;
  - `tests/domain/test_config.py` (default false; opt-in);
  - the stack probe now computes the running API's networks from its own settings and
    compares them with `docker network inspect`.
- RED:
  - The new tests did not import (`client_networks` missing).
  - The behaviour was reproduced directly: before the change, the composition root's
    `local_networks()` on a Linux-host route table served
    `['127.0.0.0/8', '::1/128', '172.17.0.0/16']` (docker0).
- GREEN:
  - fast suite `199 passed`;
  - `uv run --locked pytest -q -m stack tests/stack/test_local_stack.py -k "edge or only_the_edge or rotation"`
    gave `4 passed` (the API stayed reachable through the edge with `--no-proxy-headers`).

### N5: receipt claims and the WITH CHECK negative test
- Change: r0003's docstring now names the receipts its backfill drops (run submission,
  credential and spend-limit). It says that a retried pre-upgrade run submission would
  create a second run, accepted because no released install exists. The migration SQL is
  unchanged; join-based attribution was not done.
- Test: `tests/integration/test_receipts.py::test_the_api_role_cannot_file_a_receipt_under_another_actor_s_workspace`.
  As `nessa_api` with Ben's identity set, a receipt for his own workspace is accepted and
  one naming Ada's workspace raises `InsufficientPrivilege` (row-level security).
- Coverage only: the policy was already right, so the test passed at once (`3 passed in 7.92s`).

### N6: one live invocation holds the ledger
- Change:
  - `Ledger.exclusive()` takes a non-blocking exclusive `flock` on the ledger file.
  - `run_smoke` holds it from `authorise` through the stack's teardown and the final
    append.
  - A concurrent invocation raises `LedgerBusyError` (a `SystemExit`) before its stack
    starts.
- Tests:
  - `tests/tools/test_usage_ledger.py::test_one_live_invocation_holds_the_ledger_at_a_time`;
  - `tests/tools/test_live_smoke.py::test_a_concurrent_smoke_refuses_before_its_stack_starts`.
    It replaces the Docker stack with a stub that fails the test if it starts.
- RED:
  - First, `AttributeError: 'Ledger' object has no attribute 'exclusive'` (2 failed).
  - With the lock implemented but not yet held by `run_smoke`, the concurrent smoke
    reached its stack: `AssertionError: the smoke stack must not start`.
  - GREEN: `uv run --locked pytest -q tests/tools` gave `28 passed`; now 27, after the
    self-referential test was removed.

### N7: polish
- Edge resolution timeout:
  - Change: `edge._internal_address` bounds `getaddrinfo` with `CONNECT_TIMEOUT_S`; a
    timeout is a refusal.
  - Test: `tests/domain/test_edge_forwarder.py::test_a_resolver_that_never_answers_releases_the_client_connection`
    (the loop's `getaddrinfo` patched to never answer, timeout 0.2 s).
  - RED: the client waited the full 10 s (`TimeoutError`, `1 failed in 10.10s`).
    GREEN: `11 passed in 0.59s`.
- Run deadline: `RUN_TIMEOUT_S` now counts both store budgets per attempt
  (3 x (120 + 2 x 60) + 3 + 60 = 783 s). The comment says ledger completeness does not
  depend on it.
- `test_the_smoke_waits_out_the_run_s_worst_case` (it compared the constant with its own
  formula) is deleted.
- `tests/domain/test_worker_loop.py` (it monkeypatched the worker's own functions) is
  deleted. The reconciler is covered by
  `test_the_reconciler_publishes_an_errored_workflow_s_accepted_output`. The register's
  DUR-08 row no longer cites the deleted file.

## Final checks (tree `a56c206`)

- `make check` (repository root): `116 files already formatted`; ruff `All checks passed!`;
  mypy `Success: no issues found in 116 source files`; pytest
  `199 passed, 112 deselected in 1.85s`; fixture validator `"status": "passed"`.
- `make acceptance` (repository root), run once on the final tree:
  `112 passed, 199 deselected in 167.67s (0:02:47)`, exit 0. That includes both smoke-ledger
  tests, all 3 receipt tests and 13 stack tests. The test projects were removed afterwards.
- The dev stack (`nessa-l0`) was not started and is stopped; no `nessa` container runs.
- No live Meta call; `docs/evidence/live-usage.*` unchanged this round.

## Concerns left after round 2
- `CLAUDE.md:31-32` still states the old retry-owner principle. It needs the user's edit
  (N2; suggested text above).
- Weaker evidence:
  - N5's negative test is coverage only (the policy was already correct).
  - N4's new tests failed only structurally; the behaviour was reproduced by a direct
    call instead.
- N5: receipts are still dropped rather than attributed through joins (docstring
  corrected instead), acceptable before any release.
- Intentional changes:
  - The API is loopback-only unless `NESSA_API_INTERNAL_NETWORK_CLIENTS` is set (compose
    sets it).
  - `make reseal` now restarts a running API and worker.
  - `tools.localenv --rotate-master-key` no longer exists.
  - `make live-smoke` refuses while another invocation holds the ledger, and fails with
    `WorkerNotStoppedError` after ledgering if the worker cannot be confirmed stopped.

---

# Fix round 3 (FIX_BASE `a56c206`)

- Source: `task-3-rereview-2.md`, section "New issues" (round 2 approved; `CLAUDE.md:31-32`
  is left with the user). M1–M3 fixed in one commit, `eb70b6a` ("Ledger before honouring
  Ctrl-C, keep the leak scan on a failed stop, bound attempts"), on `l0-local-release`,
  not pushed. No live Meta call. Only `backend/tools/live_smoke.py` and its tests changed.

### M1: Ctrl-C during the worker stop still ledgers first
- Change:
  - `smoke()`'s `finally` catches `BaseException` around `target.stop_worker()`. Any
    exception, a `KeyboardInterrupt` included, marks the worker not stopped.
  - The attempts and every further possible call are then ledgered and the Markdown is
    written, before the interrupt is re-raised and `smoke_stack` tears the stack down.
- Test: `tests/integration/test_live_smoke_ledger.py::test_a_worker_that_cannot_be_stopped_still_leaves_every_possible_call_ledgered`,
  now parametrized over `RuntimeError` (expects `WorkerNotStoppedError`) and
  `KeyboardInterrupt` (expects it re-raised). Both expect `MAX_CALLS` ledger rows.
- RED (`uv run --locked pytest -q -m integration tests/integration/test_live_smoke_ledger.py -k "cannot_be_stopped and KeyboardInterrupt"`):
  `assert 0 == 3` (nothing ledgered), `1 failed`.

### M2: a failed stop still gets its leak scan
- Change: the leak scan runs after the ledger whether or not the stop succeeded. Its
  result is printed, and `WorkerNotStoppedError` carries `leak scan findings: [...]`.
- Test: the same test's `RuntimeError` case asserts that the output contains `leak scan: `
  and that the error message carries the findings.
- RED: the output was only `run ...: running` and `ledger rows appended: [1, 2, 3]` (no
  scan).

### M3: the possible-call bound is checked, not assumed
- Change (`tools/live_smoke.py`):
  - `assert_attempt_bound(spend, per_attempt)` runs right after the smoke workspace's
    limits are stored and before the key is. It computes
    `min(run_limit, period_limit) // per-attempt reservation` from the API's response and
    raises `CapExceededError` if that exceeds `MAX_CALLS`.
  - Possible-call rows now use the product's own per-attempt reservation
    (`connection_check.worst_case_nano_usd(model_id)`) instead of `worst_case // MAX_CALLS`.
  - The smoke fails if the submitted run uses a model other than the one priced.
  - The docstring states the premise: an attempt keeps its full reservation unless it
    reports usage, which only a run's final attempt does.
- Tests: `tests/tools/test_live_smoke.py::test_the_smoke_workspace_limits_allow_at_most_max_calls_attempts`
  (3 cases, the tighter limit binds) and
  `::test_limits_that_would_allow_a_fourth_attempt_stop_the_smoke_before_its_key_is_stored`.
- RED: structural only (`assert_attempt_bound` did not exist; collection error).

### Checks (tree `eb70b6a`)
- Focused:
  - `uv run --locked pytest -q tests/tools` gave `31 passed in 0.61s`.
  - `uv run --locked pytest -q -m integration tests/integration/test_live_smoke_ledger.py`
    gave `3 passed in 39.49s`.
- `make check` (repository root):
  - `116 files already formatted`; ruff `All checks passed!`;
  - mypy `Success: no issues found in 116 source files`;
  - pytest `203 passed, 113 deselected in 1.87s`; fixture validator `"status": "passed"`.
- `make acceptance`, run because `live_smoke` is exercised by
  `test_live_smoke_ledger.py`: `113 passed, 203 deselected in 174.04s (0:02:54)`, exit 0.
  The test projects were removed; no `nessa` container is running, and the dev stack is
  stopped.

### Concerns
- M3's tests failed only structurally (the function was new). M1 and M2 had behavioural
  RED.
- New refusals:
  - The smoke stops before storing the key if the stored limits allow more than
    `MAX_CALLS` attempts, or if the run's model differs from the priced one.
  - A Ctrl-C during the stop is re-raised after the ledger write (it replaces any earlier
    exception from the run).
