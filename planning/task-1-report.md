# Task 1 report: Sprint 0 technical spike and contracts (S0.1–S0.4)

Status: **DONE_WITH_CONCERNS**. All S0.1–S0.4 deliverables are implemented and verified by
execution. The concerns are a product-owner decision (ADR 0003) and two documented
limitations; none is a blocker.

Commits on `l0-local-release` (base `324b2ab`):

- `e32fb12` Add backend scaffold and budget-capped Meta qualification spike
- `6c31ed7` Prove DBOS durability and journal privacy against PostgreSQL 16
- `805cc32` Log failed live calls and harden spike stack cleanup
- `b44acca` Record Sprint 0 scope, durability and model decisions with evidence

## What I implemented

### Scaffolding

- `backend/pyproject.toml`, `uv.lock` and `.python-version`: a uv project for Python 3.12
  with exact pins. Tooling is Ruff (lint and format), mypy strict with the pydantic plugin as
  the single type checker, and pytest with `filterwarnings=error`.
- `backend/src/nessa/`: an empty typed package. The task says no feature modules yet.
- `.env.example`: `META_API_KEY` (left blank), `NESSA_META_TEST_MODEL` and
  `NESSA_META_PRODUCTION_MODEL`.

### S0.1

- `docs/adr/0001-l0-scope.md`: the L0 overrides of M0.
- `docs/dependencies.md`: the pins plus image digests. PostgreSQL 16.15, Python 3.12.16,
  Node 24.22.1, pnpm 10.33.2 and the Firebase Auth emulator were each executed on arm64.
  Not-yet-introduced dependencies have an owner and a disposition.
- `backend/spikes/firebase_emulator/`: Dockerfile and `firebase.json` for the arm64 Auth
  emulator check.

### S0.2 (`backend/spikes/meta/`)

- `pricing.py`: Meta prices as integer nano-USD per token, with a published-source citation.
- `budget.py`: the hard caps (calls, production-model calls, worst-case cost).
- `ledger.py`: an append-only JSONL ledger that renders `docs/evidence/live-usage.md`.
- `settings.py`: the key arrives as a `SecretStr` from `.env`. Model IDs are configuration,
  and a Contributor production model is rejected.
- `live_spike.py`: the CLI. Its checks are `invalid-key`, `list-models`, `schema`, `stream`,
  `search` and `stream-search`, plus `--production-model`.
- Model choice is recorded in `docs/adr/0003-meta-model-selection.md`, which is provisional.

### S0.3/S0.4 (`backend/spikes/durable/`)

- Infrastructure: `compose.yaml` (project and volume `nessa-spike`, port 127.0.0.1:55432)
  and `initdb/10-roles.sh` (separate app and DBOS databases with their own roles).
- `sealing.py`: AES-256-GCM with record context as associated data, and versioned keys.
- `store.py`: the app database. It holds sealed payloads and credentials, runs, the outbox,
  attempt/usage rows and an idempotent accepted output.
- `workflow.py`: the pinned composition, an identifier-only workflow with one bounded
  activity, a typed and message-free error boundary, and the DBOS step as the single retry
  owner.
- `worker.py`: launches DBOS, recovers workflows and drains the outbox.
- `models.py`: the Meta builder and a deterministic fake model with key-echoing failure
  modes.
- `leak_scan.py`: scans plain text, base64/pickle and bytea-hex for 12-character key
  fragments and sentinels.
- `stack.py`: Docker and worker lifecycle, plus inspection helpers.
- `capability_probe.py`: the negative control (`DBOSDurability`).
- `test_durability.py`: 9 integration scenarios.
- `live_run.py`: the real key inside the activity, plus an invalid key.
- The composition is recorded in `docs/adr/0002-durable-execution.md`.

### Evidence documents

- `docs/evidence/sprint-0-spike.md`: exit evidence.
- `docs/evidence/live-usage.md` and `.jsonl`: per-call cost rows with a running total.

## Rulings (and why)

1. **Spike versus production code.** All spike code is under `backend/spikes/`, and
   `src/nessa` stays empty, as the brief requires. The budget, ledger and pricing modules are
   reusable. The task that implements `make live-smoke` should *move* them into the
   identity/execution module rather than duplicate them. Cost if wrong: a later move.
2. **Type checker: mypy strict.** It is pure Python and has the pydantic plugin.
3. **Test model: `muse-spark-1.3-contributor`.** It is the cheapest Meta model that passed
   schema, streaming and search, and it is the same release as production. Because Meta may
   train on Contributor traffic, it is restricted to synthetic or public inputs. ADR 0003 is
   marked provisional under R6. Fallback: set `NESSA_META_TEST_MODEL=muse-spark-1.3`.
4. **Production model: `muse-spark-1.3` (Standard)**, as the plan states. Wonder is M1, so
   no escalation.
5. **`DBOSDurability` is not used in L0.** The negative control showed it journals the
   private model output. Instead, one bounded activity (a DBOS step) runs a plain agent. The
   cost is coarser recovery: a crash re-runs the whole model call.
6. **Global portable JSON serializer for DBOS.** It avoids pickle and makes the journal
   inspectable and structurally limited to plain values.
7. **One retry owner, the DBOS step** (`should_retry` for 429/500/503 only). OpenAI client
   retries are 0 and agent output retries are 0.
8. **Costs in integer nano-USD.** Meta bills in USD, and every rate is then an exact integer.
   The product's GBP minor-unit money rule is unaffected.
9. **Free calls count against the call cap.** The two kinds are invalid-key calls and model
   listing. They are recorded at $0 because the charge is determinable: an unauthenticated
   request identifies no team to bill, and model listing has no billable unit on the pricing
   page. Calls that fail or raise without usage are recorded as `unknown`, and the budget
   commits their full reservation.
10. **Search billing.** The ledger counts `search` actions. Each search call also made one
    `open_page` action, and Meta does not document whether those are billed. I report an
    upper bound rather than claim either.
11. **`httpx2` replaces `httpx`.** OpenAI 3.40 and Pydantic AI already use httpx2, so the
    spike no longer pulls a second HTTP client.
12. **pnpm stays 10.33.2**, the host version, although 12.15.0 is upstream. Upgrading would
    be an unrequested package-manager change.
13. **Spike database on 127.0.0.1:55432.** 5432 and 5434 are taken by other projects.
    Passwords are generated per run and passed through the environment. The volume is
    removed after every run, which also destroys the sealed real key.

## Tests and checks run (final tree)

From `backend/`:

- `uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest`
  - 25 files formatted, all checks passed.
  - mypy: no issues in 25 source files.
  - **39 passed, 9 deselected in 0.53 s.** The deselected 9 are the integration tests.
- `uv run pytest -m integration spikes/durable -v -s`
  - **9 passed in about 19 s**, on PostgreSQL 16.15 in Docker with real worker processes and
    SIGKILL.
  - The negative control printed
    `capability probe findings: [('dbos.operation_outputs', 'private text')]`.
- Mutation check: I removed `from None` from the transient re-raise. The transient test then
  failed with `Finding(location='worker.log', needle_label='credential', match='fragment')`.
  I restored the line. (A first attempt at this mutation did not apply because the formatter
  had joined the lines, so its pass was discarded and I redid it.)
- arm64 container checks:
  - `postgres --version` gave 16.15 on aarch64.
  - `uv sync --frozen --no-dev` in `python:3.12.16-slim-bookworm` gave aarch64, the pinned
    versions and psycopg's binary implementation.
  - The Firebase emulator image reported ready, issued `alg: none` tokens, and has no Java.
- A secret scan of every tracked and pending text file (45) for 12-character fragments of
  the real key found nothing.

### TDD evidence (domain-ish logic)

- Pricing, budget and ledger: RED was 3 collection errors (`ModuleNotFoundError:
  spikes.meta.pricing`). GREEN was 21 passed and 1 failed. The failing case was my hand
  arithmetic in the test ($0.0255); the correct value is $0.026: 10,000 × $1.25/M +
  2,000 × $4.25/M + 2 × $0.0025. I corrected the expectation, not the code, and then had 22
  passed.
- Sealing and leak scan: RED was 2 collection errors. GREEN was 13 passed.
- Leak scan bytea-hex view: RED was 1 failed. GREEN was 6 passed.
- Ledger failed-outcome rendering (self-review fix): RED was 1 failed on
  `failed (ConnectError)`. GREEN followed.
- Not TDD: `test_live_spike_guard.py` (the logging of a raising call, and a refused call
  never being sent) was written after the fix. The integration scenarios are spike evidence,
  not TDD.

## Live calls (R5): 11 calls, 2 on the production model; estimated $0.019677

The per-call table is in `docs/evidence/live-usage.md`, priced from
https://dev.meta.ai/docs/pricing-rate-limits as checked on 2026-10-27.

| # | What | Model | Cost |
|---|---|---|---|
| 1 | invalid key (401) | contributor | $0 |
| 2 | model listing | n/a | $0 |
| 3 | schema | contributor | $0.000067 |
| 4 | streaming schema | contributor | $0.000055 |
| 5 | search + schema | contributor | $0.003538 |
| 6 | schema | **muse-spark-1.3** | $0.000813 |
| 7 | streaming + search + schema | **muse-spark-1.3** | $0.015123 |
| 8 | inside the DBOS activity, real key | contributor | $0.000045 |
| 9 | invalid key inside the DBOS activity | contributor | $0 |
| 10 | inside the DBOS activity, real key (rerun) | contributor | $0.000037 |
| 11 | invalid key inside the DBOS activity (rerun) | contributor | $0 |

- Upper bound if Meta bills `open_page` actions: $0.024677.
- Remaining credit is not exposed by a documented API (dashboard only).
- Calls 10–11 were a deliberate rerun. The first live scan (calls 8–9) gave a false positive
  because the invalid key's public prefix `nessa-spike-` matched DBOS's application version
  `nessa-spike-1`. I reproduced the cause offline and fixed the needle (a prefix-free random
  key). The rerun scanned clean. Neither run had any finding for the real key or the private
  text.

## Blocked, not run, concerns

- **Product-owner decision:** the Contributor test model (ADR 0003, provisional). Its
  privacy implication is that Meta may train on test prompts. Synthetic or public data only.
- **Not run:**
  - amd64 images (manifests only).
  - DBOS workflow cancellation and deletion of workflow history.
  - Outbound-traffic isolation of the DBOS worker and the Firebase emulator in demo mode.
    DBOS prints a Conductor URL, and `firebase-tools` may check for updates.
  - Async step timeouts.
  - Refusal, truncation and timeout tests for the Meta adapter (Sprint 2).
- **Not rerun:** `live_run.py` moved `stack.start` inside the cleanup `try` after its live
  runs. Nothing else in the run path changed. I skipped the rerun to save live calls.
- **Concern:** Pydantic AI 2.x is moving fast. 2.59 to 2.62 shipped in 6 days, and 2.62.0
  was published on the check date. ADR 0002 makes the integration suite the gate for bumps.
- **Concern:** with the bounded-activity composition, a crash mid-call repeats the provider
  call, so duplicate spend is possible. Each attempt is recorded for reconciliation, and
  exactly-once calls are not claimed.
- **Note:** host Python is 3.12.12 and the container is 3.12.16; uv 0.9.18 cannot fetch
  newer builds.
- **Note:** `docs/requirements-register.md` does not exist yet (Task 2), so no register rows
  were updated. The starter-kit `CLAUDE.md` adoption is also Task 2.
- **Docker state:** the spike container, volume (`nessa-spike-pgdata`) and emulator image
  were all removed. Pulled base images remain in the cache. The user's other containers were
  not touched.

## Paths a reviewer can skip or skim

- `backend/uv.lock` (generated lockfile).
- `docs/evidence/live-usage.jsonl` (machine ledger) and `docs/evidence/live-usage.md`
  (rendered from the JSONL; do not hand-edit).

---

# Fix report: round 1

No live Meta calls were made in this round; the ledger is unchanged at 11 calls,
$0.019677. Everything below was verified with the fake model, unit tests and the
PostgreSQL 16 integration suite.

## Changes per finding

**I1. Untyped failures and stuck runs.** File: `backend/spikes/durable/workflow.py`.
- New `classify_failure(error) -> Classified(label, failure)` maps exceptions from type and
  HTTP status only:
  - HTTP 429/500/503, `ModelTimeoutError`, `ModelConnectionError` and `ModelRequestTimeout`
    are transient;
  - 401/402/403 are authentication/billing/permission;
  - any other HTTP status is `provider_request_rejected`;
  - `UsageLimitExceeded` and `UnexpectedModelBehavior` are `invalid_model_output`;
  - anything else is `unknown_failure:<ClassName>`.
- The activity classifies inside the handler and acts outside it. `finish_attempt` and the
  `TransientProviderError` re-raise run after the handler, so no provider exception is
  chained as `__context__`. The old code had a second latent leak here: `finish_attempt`
  ran inside `except ModelHTTPError`.
- A catch-all around the whole attempt (store, crypto, bugs) finishes the attempt row as
  `unknown_failure:<Class>`, logs only the run ID and that label, and returns
  `failed/unknown_failure`.
- `TransientProviderError` now carries only its label.
- `models.py` has new fake failure modes, `connection_error` and `unexpected_error`. Their
  messages echo the key, and the unexpected error's also quotes the private input.
- `docs/adr/0002-durable-execution.md` decisions 6–7 are rewritten with the full mapping.
  They also note that an application-database outage during the activity still leaves a
  DBOS `ERROR` workflow (reconciliation belongs to the Task 3 run lifecycle).

**I2. Live calls dropped from the ledger.** File: `backend/spikes/durable/live_run.py`.
- The orchestration is now `run_live_check(spike, ledger, ...)` on an already-started
  stack. Its `finally` kills any running worker, then `ledger_attempts` appends one row per
  activity attempt *before* the caller removes the stack.
- If the attempt rows cannot be read (`psycopg.Error`), it appends the worst case:
  `ACTIVITY_MAX_ATTEMPTS` "possible call" rows per run. Paid rows have unknown cost with
  the reservation committed; invalid-key rows are $0.
- An unpriced model gives an unknown cost rather than a crash.

**I3. Production cap follows the model.**
- New `MetaSettings.is_production_model(model_id)`.
- `live_spike.py` derives `is_production` from the model ID for the invalid-key and
  structured checks.
- `live_run.py` reserves production calls when the worker model is the production model,
  and sets `is_production_model` per attempt row.
- ADR 0003's cost-discipline text now states that direct calls are checked one by one,
  that durable-worker calls are batch pre-authorised before the worker starts, and that a
  Standard test model counts against the production cap.

**I4. ADR 0002 roles.**
- Decision 2 now pins migration/owner roles for setup only. Runtime API and worker processes
  use non-owner roles, with DBOS launched as `run_migrations=False` after
  `run_dbos_database_migrations`. This satisfies Global Constraint 7, since owners bypass
  RLS. The spike's owner connections are labelled a spike shortcut, and Task 3 implements
  the split.
- Decision 5.2 is now described as a credential/workspace consistency check. Actor ownership
  checks are deferred to Sprint 1 (Task 3).
- Spike code is unchanged for I4.

**I5. Evidence fixes.**
- (a) Live scan wording, in ADR 0002 and `sprint-0-spike.md`, is narrowed: no 12-character
  key fragment and no sentinel, explicitly *not* "no private text". `live_run.py` now also
  scans for the opened output strings and 24-character windows of the private text; it has
  not been re-run live. The integration suite gained the 24-character private-text window
  needle, used with the fake model.
- (b) Search facts. Call 7 is `search` + `open_page`. Call 5's action types and `tool_usage`
  for any search call were not captured; the only raw body captured is call 6 (no search).
  Corrected in ADR 0003, `sprint-0-spike.md` and the generated `live-usage.md` header, which
  was regenerated (the JSONL is unchanged).
- (c) The evidence states that ledger rows 3–5 came from an earlier `live_spike.py`
  revision. The mock-transport check is now committed as
  `backend/spikes/meta/test_request_shape.py`. It drives the factored-out
  `qualification_agent` through `MetaProvider` over `httpx2.MockTransport` and asserts the
  URL, strict `json_schema`, reasoning effort, `max_output_tokens`, the `web_search` tool
  and `tool_choice: auto`.
- (d) ADR 0003 gains a table for `muse-image-1.0`, `muse-voice-transcribe-1.0` and
  `sam-3.1`: capabilities, endpoints, prices and limits from the pricing and models pages
  checked 2026-10-27; context limits marked "not published"; marked "listed, not called".
- (e) The Firebase emulator was published with `-p 127.0.0.1:59099:9099` (loopback only).
  This is recorded in the evidence and `docs/dependencies.md`, and the Dockerfile comment
  states the rule. `firebase.json` binds `0.0.0.0` only inside the container.

**Cheap fixes.**
- Minor 6: `initdb/10-roles.sh` reads the passwords with `\getenv` inside psql, with no
  `-v` arguments.
- Minor 8: the mid-activity test waits for the dispatch mark with `wait_for` instead of
  asserting it immediately.
- Minor 9: ADR 0001's planning row now quotes plan section 1 verbatim in the L0 column
  ("At most 24 action concepts, two reviewed starts per concept, ...") and spec section 1 in
  the M0 column.

**Found during this round.**
- **Outbox pollution.** The negative-control test left its run's outbox entry undispatched.
  The probe handles that run itself, so a later worker dispatched it. The new I2 test caught
  this (DB attempts {18, 19, 20} against ledgered {19, 20}). Fixes: the negative control
  marks its entry dispatched, and the I2 test scopes its assertion to its own runs (outbox
  IDs above the pre-test maximum).
- **Intermittent worker shutdown hang** (one in 19 full-suite runs, the 9th).
  - What happened: after recovery, the mid-activity scenario's restarted worker completed
    the run correctly, then did not exit within 30 s of SIGTERM and logged nothing. The old
    `Worker.stop()` raised `TimeoutExpired` and left the process running: orphan pid 81552,
    killed by hand. Docker was then clean.
  - Cause: not determined, and not reproduced in 6 isolated or 10 full-suite repetitions.
  - Leading hypothesis: `DBOS.destroy()` blocks in `_cleanup_connections()` while the
    notification listener is blocked in a timeout-free `notifies()`.
  - Fixes: `Worker.stop()` now kills on timeout and raises `WorkerShutdownTimeoutError`
    naming the log. The scenario fixture kills its workers at teardown. The worker logs
    `worker stopping` and `worker stopped` around `DBOS.destroy()`, so a recurrence shows
    which side hangs.
  - Follow-up: `make stop` (Task 3) must bound shutdown and fall back to SIGKILL. This is
    recorded in `sprint-0-spike.md`.

## Tests and evidence

- TDD, failure mapping (`test_failure_mapping.py`, 16 cases). RED: `ImportError: cannot
  import name 'Classified'`. GREEN: 16 passed.
- I1 reproduction against the pre-fix `workflow.py` (from `git show HEAD`): both new
  scenarios failed with `TimeoutError: timed out after 60.0s waiting for run`, the runs
  stuck in `queued`. With the fix, both pass.
- I2 mutation: when ledgering ran only on the success path, the new integration test failed
  (`set() == {1, 2}`). With the fix, it passes.
- New fast tests: `test_live_ledger.py` (fallback rows; production cap for production-model
  attempts), `test_settings.py` (the cap follows the model ID; Contributor production model
  rejected; unit settings never read `.env`) and `test_request_shape.py`.
- Final commands, from `backend/`:
  - `uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q`
    → 29 files formatted, all checks passed, mypy clean on 29 files, **63 passed,
    12 deselected**. Output is clean without `PYDANTIC_AI_NO_BANNER`.
  - `uv run pytest -m integration spikes/durable -v` → **12 passed**, about 31.7 s, on
    **10 of 10** full runs after the final code change. Over the whole task, 18 of 19 full
    runs passed; the exception is the one shutdown-hang run described above.
- Docker after the runs: no `nessa-spike` containers or volumes, and no stray worker
  processes.

## Not run in this round

- No live calls. `live_run.py` (now `run_live_check`) and the rewritten activity have not
  been run against Meta.
- The ledger row from the new "raised call" path and the fallback path is unit-tested only.

## Carried forward to Task 3 (deferred by the controller)

- Minor 4: a crash after the output is saved re-calls the model and loses the first
  attempt's usage. Check for an accepted output first, and record usage atomically with the
  accept.
- Minor 7: split the model factory/policy out of the CLI module (`live_spike.py`).
- From this round: the role split (ADR 0002 decision 2), actor ownership checks,
  reconciliation of DBOS `ERROR` workflows, and a bounded `make stop` with a SIGKILL
  fallback.

## Round 1 commits

- `95b3183` Close review findings in the durable and Meta spikes (code and tests)
- `2bb36e5` Correct Sprint 0 ADRs and evidence after review (docs)

The worktree is clean except for an untracked `.claude/scheduled_tasks.lock` (a harness
file, not created by this task, and not committed). The final secret scan of 49 tracked
and pending text files for 12-character fragments of the real Meta key found nothing.
