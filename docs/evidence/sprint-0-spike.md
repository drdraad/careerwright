# Sprint 0 spike: exit evidence (S0.1–S0.4)

> Task 3 (Sprint 1) retired `backend/spikes/` after promoting it into `backend/src/nessa`
> and `backend/tools`. The commands and paths below are historical (git `ff449da`); their
> scenarios now run against the product code in `make acceptance`, and the live check is
> `make live-smoke` (ADR 0002, ADR 0004).

- Date: 2026-10-27. Branch `l0-local-release`, from base `324b2ab`.
- Machine: macOS arm64, Docker 29.1.2 (aarch64 engine), uv 0.9.18, Python 3.12.12 (uv-managed).
- Scope: S0.1 to S0.4 of the Sprint 0 card. S0.5 (fixtures and hand checks), S0.6 (corpus
  manifest, register, design references) and the Sprint 0 review belong to Task 2.

## Exit evidence status

| Card exit evidence (S0.1–S0.4 part) | Status | Where |
|---|---|---|
| A real call succeeds with a typed response | **Passed.** Test model: ledger calls 3, 4, 5, 8, 10. Production `muse-spark-1.3` (Standard): calls 6 and 7 | `live-usage.md`; S0.2 below |
| An invalid key fails visibly | **Passed.** Direct call: 401 `ModelAuthenticationError` (call 1). Through the durable activity: `failed/provider_authentication` (calls 9, 11) | S0.2, S0.4 |
| Worker recovery does not corrupt the accepted result | **Passed.** SIGKILL mid-call and after persistence; accepted row unchanged | S0.3 |
| Persisted state contains no credential | **Passed.** Full scans of both databases and the worker logs, with the real key | S0.4 |
| Every unknown dependency has a named owner and disposition | **Passed for the S0.1 scope** | `docs/dependencies.md` |
| If live access is blocked, the spike is blocked | Not blocked. The key, Standard entitlement and the test model all work | S0.2 |
| TRACE-01 arithmetic and five persona expectations committed | **Passed** in Task 2 (S0.5): hand-checked, with findings. Agent-performed; domain-reviewer sign-off (H-07) not run — requires human | `docs/evidence/fixture-hand-check.md` |

## S0.1 Scope and dependency matrix

- `docs/adr/0001-l0-scope.md` records the plan's section 1 L0 overrides against M0.
- `docs/dependencies.md` gives exact pins and image digests. Each runtime was executed on
  arm64:
  - `postgres:16.15-bookworm@sha256:d81f7b51…bcb0` reports `postgres (PostgreSQL) 16.15
    (Debian 16.15-1.pgdg12+2)`, `aarch64`, and runs the whole DBOS suite.
  - `python:3.12.16-slim-bookworm@sha256:6dd8b6da…9753`: `uv sync --frozen --no-dev`
    gives `aarch64 3.12.16`, `pydantic-ai-slim 2.62.0`, `dbos 3.3.0`,
    `psycopg-binary 3.3.6`, and `psycopg impl: binary`.
  - `node:24.22.1-bookworm-slim@sha256:55fb5f5a…d205` with `pnpm@10.33.2` and
    `firebase-tools@15.34.1`: `{"authEmulator":{"ready":true,...}}`. `accounts:signUp`
    returns an ID token with header `{"alg": "none", "typ": "JWT"}`,
    `iss: https://securetoken.google.com/demo-nessa`, and an empty signature. The container
    has no Java: `command -v java` finds nothing. The container was started with
    `docker run -p 127.0.0.1:59099:9099`, so the emulator was reachable from host loopback
    only. `firebase.json` binds `0.0.0.0` inside the container's network namespace so that
    the published port reaches it. The Dockerfile records the loopback-only publish rule.
- amd64 has registry manifests only and was not executed.

## S0.2 Meta model qualification (Pydantic AI native Meta provider)

Docs checked on 2026-10-27, before any call:
<https://dev.meta.ai/docs/models>, <https://dev.meta.ai/docs/pricing-rate-limits>,
<https://dev.meta.ai/docs/structured-output>, <https://dev.meta.ai/docs/search-grounding>,
<https://dev.meta.ai/docs/error-handling>,
<https://dev.meta.ai/docs/api-reference/responses/schemas>,
<https://pydantic.dev/docs/ai/models/meta/>. I also read the installed sources:
`pydantic_ai/providers/meta.py` and `profiles/meta.py`. The Meta profile sets
`supports_json_schema_output=True`, `supports_forced_tool_choice=False` and
`supported_native_tools={WebSearchTool}`.

Request shape: `POST https://api.meta.ai/v1/responses` with `text.format` set to
`{"type": "json_schema", "strict": true, ...}`, `reasoning.effort`, `max_output_tokens`,
`tools: [{"type": "web_search", "search_context_size": "low"}]` and `tool_choice: "auto"`.
Before any billable call, I checked this offline with an uncommitted mock-transport script.
That check is now committed as `backend/spikes/meta/test_request_shape.py`. It drives the
same qualification agent (`qualification_agent`) through Pydantic AI's Meta provider over an
`httpx2.MockTransport` and asserts the body.

Calls, in order (`uv run python -m spikes.meta.live_spike <check> [--production-model]`):

| # | Check | Model | Result |
|---|---|---|---|
| 1 | invalid key (free) | test | `ModelAuthenticationError`, `status_code: 401 ... body: {'code': 'invalid_api_key', 'message': 'Unauthorized', ... 'type': 'authentication_error'}`; no key fragment echoed |
| 2 | `GET /v1/models` (free) | n/a | 9 models; both Spark 1.3 variants are listed (all `created: 0`) |
| 3 | schema | test | `CareerSuggestion` validated; 157 in / 254 out (208 reasoning); $0.0000665 |
| 4 | streaming schema | test | 5 partial validated outputs, first at 2.43 s, done at 2.81 s; usage reported on the stream |
| 5 | search + schema | test | 2 `web_search_call` items (action types not captured); Pydantic AI counted 1 billed search; validated `SearchFindings` with `https://www.gov.uk/advanced-learner-loan`; 9,993 in (1,107 cached) / 737 out |
| 6 | schema | **production** | validated; Meta raw `usage` `{input 157, cached 0, output 145, reasoning 89}` matches Pydantic AI exactly; `tool_usage` absent from this one captured raw body (not a search call) |
| 7 | streaming + search + schema | **production** | 4 partial outputs; actions `search` and `open_page`; validated, same GOV.UK URL; 9,434 in / 482 out |

Rows 3–5 came from an earlier revision of `live_spike.py`. Raw-usage capture and
action-type recording were added after call 5, so for those rows the raw `usage` and
`tool_usage` fields and the search action types were not captured. The agent, model
settings and provider path were otherwise the same.

Hand checks of the cost formula:
- Call 3: 157 × $0.10/M + 254 × $0.20/M = $0.0000665.
- Call 6: 157 × $1.25/M + 145 × $4.25/M = $0.0008125.
- Call 7: (9,434 − 1,107) × $1.25/M + 1,107 × $0.15/M + 482 × $4.25/M + 1 × $0.0025 = $0.0151233.

The ledger matches all three.

Decision (ADR 0003, provisional; the product owner must confirm the Contributor test
model):
- Production model: `muse-spark-1.3` (Standard).
- Test model: `muse-spark-1.3-contributor`, for synthetic or public inputs only.

The structured-output result, stated precisely: the schema is enforced by Meta through
`text.format` (strict) and validated again by Pydantic. Structural validity does not make
a statement true. The search evidence shows that a search happened and that a real GOV.UK
URL came back; it does not show claim-to-span grounding, which is a Sprint 3 task.

## S0.3 DBOS workflow against local PostgreSQL 16

Composition and rationale: `docs/adr/0002-durable-execution.md`. Code is under
`backend/spikes/durable/`. Command (from `backend/`):

```text
$ uv run pytest -m integration spikes/durable -v -s      # final tree after fix round 1
test_worker_killed_mid_activity_recovers_to_one_accepted_output PASSED
test_worker_killed_after_output_persisted_keeps_first_accepted_output PASSED
test_outbox_replay_after_dispatch_crash_starts_one_workflow PASSED
test_replaying_a_completed_outbox_entry_has_no_effect PASSED
test_transient_provider_error_is_retried_by_the_dbos_step_only PASSED
test_exhausted_retries_fail_visibly_not_as_empty_success PASSED
test_provider_error_echoing_the_key_is_not_journalled PASSED
test_connection_errors_are_retried_then_fail_visibly PASSED
test_unexpected_error_fails_typed_without_its_message PASSED
test_revoked_credential_stops_before_any_model_call PASSED
test_negative_control_durability_capability_journals_private_output
  capability probe findings: [('dbos.operation_outputs', 'private text'),
                              ('dbos.operation_outputs', 'private text window')]  PASSED
test_live_check_ledgers_every_attempt_even_when_the_run_fails PASSED
12 passed, 32 deselected in 31.79s
```

Across 19 full-suite runs in total, one failed intermittently; see "Blocked, not run, or
limited". The 10 runs after the final code change all passed.

What these establish:

- **Kill and restart.** Worker A is SIGKILLed while the model call sleeps. Before the kill,
  the test asserts the outbox entry was already marked dispatched, so worker B can finish
  the run only through DBOS recovery. The DBOS status is `PENDING` after the kill and
  `SUCCESS` after B. Attempts are `[unfinished, succeeded]`, with exactly one accepted
  output.
- **Kill after persistence.** The accepted row (ID, hash, `created_at`, ciphertext) is
  identical after recovery. The second attempt is `reused_accepted`.
- **Outbox replay.** The worker is SIGKILLed after `start_workflow` but before marking the
  outbox entry. After restart there is one workflow for the run, one output, and the entry
  is marked. Re-delivering a completed entry changes nothing.
- **Fail-visible paths.**
  - HTTP 429 once: the DBOS step retries and the run succeeds.
  - HTTP 503 every time: 3 attempts, then `failed/provider_unavailable` with no output.
  - Connection error every time: 3 `transient_connection` attempts, then
    `failed/provider_unavailable`.
  - Unexpected `RuntimeError`: `failed/unknown_failure`. The attempt row holds
    `unknown_failure:RuntimeError`, and no step error is journalled.
  - Revoked credential: `failed/credential_unavailable` with no model call.

  Against the pre-fix activity, the connection-error and unexpected-error scenarios both
  timed out with the run stuck in `queued` (`TimeoutError: timed out after 60.0s waiting for
  run`). That reproduces review finding I1; the fix makes them pass.
- **Live calls are ledgered even when the durable live run fails.**
  `test_live_check_ledgers_every_attempt_even_when_the_run_fails` drives the live-check
  orchestration (`run_live_check`) with the fake model and a 10 s timeout while calls are in
  flight. Every activity attempt still reaches the ledger, with unknown cost and its
  reservation committed. Mutation check: when ledgering ran only on the success path, the
  test failed (`set() == {1, 2}`). If the attempt rows cannot be read at all,
  `test_live_ledger.py` shows the worst case being ledgered instead.

Persisted workflow arguments and results, from the live run with the real key
(`uv run python -m spikes.durable.live_run`, first run, ledger calls 8–9):

```text
== real-key run: {'status': 'succeeded', 'failure_class': None, 'output_id': '7153ab9f-a05a-4a41-b657-fe3487ae70b3'}
dbos.workflow_status: [{'status': 'SUCCESS', 'name': 'nessa_spike.profile_run', 'serialization': 'portable_json', 'recovery_attempts': 1}]
dbos.workflow_input: [{'inputs': '{"namedArgs":{},"positionalArgs":["ff6f1b94-95bb-43cb-a43c-092537178961"]}'}]
dbos.workflow_output: [{'output': '{"status":"succeeded","output_id":"7153ab9f-a05a-4a41-b657-fe3487ae70b3"}', 'error': None}]
dbos.operation_outputs: [{'function_id': 1, 'function_name': 'nessa_spike.bounded_model_activity', 'output': '{"status":"succeeded","output_id":"7153ab9f-a05a-4a41-b657-fe3487ae70b3"}', 'error': None},
                         {'function_id': 2, 'function_name': 'nessa_spike.publish_outcome', 'output': 'null', 'error': None}]
validated output (opened from sealed store): {'proposed_title': 'Warehouse Shift Supervisor', 'evidence_quote': 'I supervise warehouse shifts in Leeds and enjoy training new starters.'}
== invalid-key run: {'status': 'failed', 'failure_class': 'provider_authentication', 'output_id': None}
dbos.workflow_output: [{'output': '{"status":"failed","failure_class":"provider_authentication"}', 'error': None}]
```

The journal holds the run ID, the status and the output reference. The model's private
quote exists only sealed in the application database.

## S0.4 Durable boundary: no credential or private payload journalled

- **Detector.** `spikes/durable/leak_scan.py` (unit-tested) reads every row of every user
  table in the DBOS and application databases (`row_to_json`) and every worker log. It
  searches the plain text, base64 (which catches pickled values) and Postgres bytea hex. The
  credential needle matches any 12-character fragment. The private-text needles match the
  per-test sentinels and any 24-character window of the private text.
- **Negative control.** Pydantic AI's `DBOSDurability` inside a workflow puts the private
  model output into `dbos.operation_outputs`, and the scan finds it. So a clean scan means
  something. The prompt-only sentinel (never echoed by the model) and the credential were
  not found there: the capability journals what the model returns, not the prompt or the key.
- **Mutation check.** I removed `from None` from the transient-error re-raise in
  `workflow.py`. `test_transient_provider_error_is_retried_by_the_dbos_step_only` then
  failed with `Finding(location='worker.log', needle_label='credential', match='fragment')`:
  DBOS's retry warning had logged the chained provider exception. I restored the line and
  the test passes.
- **Live run with the real key**, ledger calls 10–11:
  `leak scan: 24 rows/logs scanned, findings: []` across 23 rows in the two databases plus
  the worker log. The needles were the real Meta key (12-character fragments), the invalid
  key (12-character fragments) and the private-text **sentinel**. The real output did not
  contain the sentinel, and that run did not scan for the opened output strings or for
  windows of the private text. So it shows that neither key leaked and the sentinel did not
  leak; it does not show that no private text leaked. The current `live_run.py` adds both
  needles (opened output strings and 24-character private-text windows), but it has **not
  been re-run live**. The integration suite does use the window needle, with the fake model.
- **First live run, a false positive (calls 8–9).** That scan reported 4 fragment findings,
  all for the *invalid* key. They were in `dbos.workflow_status`, in
  `dbos.application_versions` and in the worker log. Cause: the invalid key began with the
  public prefix `nessa-spike-` (12 characters), and that string occurs in DBOS's application
  version `nessa-spike-1`. Even the real-key run's `workflow_status` row was flagged, and
  that row never saw the invalid key. I reproduced the cause offline (a scan of
  `"nessa-spike-1"` against that needle gives one finding; a prefix-free needle gives none).
  I changed the invalid key to a prefix-free random token and reran, which produced calls
  10–11 and the clean scan above. Neither run had any finding for the real key or the
  private-text sentinel.

## Live usage (R5)

- 11 calls, 2 of them on the production model, against caps of 15 and 5.
- Estimated $0.019677 before tax.
- Calls 5 and 7 each had one `web_search_call` item that Pydantic AI did not count as a
  billed search. In call 7 it was an `open_page` action; call 5's action types were not
  captured. Whether Meta reports a `tool_usage` count on search calls was not captured
  either. Meta does not document whether such actions are billed, so the upper bound is
  $0.024677.
- No live calls were made in fix round 1.
- Remaining credit is not exposed by a documented API.
- Full table: `docs/evidence/live-usage.md`; machine ledger: `docs/evidence/live-usage.jsonl`.

## Blocked, not run, or limited

- amd64 images: manifests only, not executed.
- Workflow cancellation, deletion of workflow history, demo-mode outbound-traffic isolation
  of the DBOS worker and the emulator (`firebase-tools` update checks), and step timeouts
  were not exercised. Owners are listed in ADR 0002 and `docs/dependencies.md`.
- Refusal, truncation and timeout contract tests for the Meta adapter: Sprint 2 (spec
  section 16).
- `spikes/durable/live_run.py` changed after its live runs, and the changed version has
  **not been re-run live**:
  - `stack.start` moved inside the cleanup `try`;
  - in fix round 1, the orchestration moved into `run_live_check`, which ledgers every
    attempt in `finally`;
  - the production cap now follows the model ID;
  - the output-string and private-text-window needles were added.

  The new orchestration is exercised offline by the integration suite, with the fake model.
- The activity in `workflow.py` was rewritten in fix round 1 (the I1 error boundary). The
  live calls 8–11 ran the earlier version. Its success and 401 paths behave the same, and
  the fake-model suite covers the new branches.
- **Intermittent worker shutdown hang.** One of 19 full-suite runs (the 9th) failed
  `test_worker_killed_mid_activity_recovers_to_one_accepted_output` at the end. The
  restarted worker had already completed the recovered run, and the accepted output was
  correct. But it did not exit within 30 s of SIGTERM, and it logged nothing after
  `worker ready`. Two readings fit:
  - `DBOS.destroy()` blocks before its join loop. Its `_cleanup_connections()` closes the
    notification listener's connection under DBOS's lock, while that listener is blocked
    in a timeout-free `notifies()`.
  - The main loop never reached `destroy()`.

  The cause was not determined. It did not recur in 6 isolated repetitions of the scenario
  or in 10 full-suite repetitions. On that run the harness left the worker running (killed by hand
  afterwards). Fix round 1 changed this:
  - `Worker.stop()` now kills on timeout and raises `WorkerShutdownTimeoutError`;
  - every test kills its workers at teardown;
  - the worker logs `worker stopping` and `worker stopped` around `DBOS.destroy()`, so a
    recurrence shows which side hangs.

  For L0, `make stop` must bound shutdown and fall back to SIGKILL (DBOS recovery covers
  in-flight work). Owner: Task 3.
- Human decision outstanding: Contributor mode for the test model (ADR 0003, R6).

## Reproduce

```bash
cd backend
uv sync
uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest   # fast, offline
uv run pytest -m integration spikes/durable -v     # Docker; starts and removes nessa-spike
uv run python -m spikes.meta.live_spike invalid-key   # free; others cost money (see ledger)
uv run python -m spikes.durable.live_run              # 1 billable test-model call, 1 free call
```

Live commands refuse to run once this task's caps are reached. The budget scope is
`task-1-sprint-0` in `spikes/meta/live_spike.py`.
