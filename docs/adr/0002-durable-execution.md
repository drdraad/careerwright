# ADR 0002: Durable execution with DBOS and Pydantic AI

- Status: Accepted (Sprint 0 spike evidence, `docs/evidence/sprint-0-spike.md`)
- Date: 2026-10-27
- Requirements: ARC-1 and Durable execution (spec section 17), section 19, plan S0.3/S0.4

## Context

DBOS is the committed workflow engine and Pydantic AI the LLM framework. The specification
requires that workflow histories hold identifiers and small encrypted references, never raw
API keys, CVs or web pages, and that one layer owns each retry budget. The plan warns:
"Do not assume attaching a durability capability automatically satisfies privacy or
recovery."

Pydantic AI offers a capability, `DBOSDurability`, that runs each model request as a DBOS
step inside a user-written `@DBOS.workflow`. (The older `DBOSAgent` wrapper is deprecated
and is removed in v3.) DBOS stores workflow inputs, workflow outputs and every step output
or error in its system database. By default it pickles them; it also logs step exceptions
with tracebacks when it retries.

The spike measured what each composition journals, against real PostgreSQL 16.15 and real
worker processes killed with SIGKILL.

## Decision

Pin this composition for every workflow that touches private data or a credential:

1. **Versions.** `dbos==3.3.0` and `pydantic-ai-slim[openai,dbos]==2.62.0` on Python 3.12
   and PostgreSQL 16.15, as locked in `backend/uv.lock`. Bumping either re-runs
   `make acceptance` (since Task 3 the durable suite is
   `backend/tests/integration/test_durable_runs.py` and its neighbours; the spike suite was
   retired).
2. **Separate databases, non-owner runtime roles.** The DBOS system database and the
   application database are separate databases. The application database is authoritative;
   DBOS state is execution bookkeeping. Each database is owned by a migration role that only
   setup uses: it runs Alembic migrations and DBOS's schema migrations
   (`run_dbos_database_migrations`). The API and workers connect as **non-owner** runtime
   roles with only the grants they need, and launch DBOS with `run_migrations=False`. An
   owner bypasses row-level security, so a runtime connection as owner would break Global
   Constraint 7. The spike connected as each database's owner (a spike shortcut). Task 3
   implemented and tested the role split: `nessa_migrator` and `nessa_dbos_owner` for setup,
   `nessa_api`, `nessa_worker` and `nessa_dbos_runtime` at runtime (ADR 0004 decision 5).
3. **Portable JSON journal.** Configure `DBOSConfig(serializer=DBOSPortableJSONSerializer())`.
   The journal is then plain JSON: inspectable without unpickling database content, and
   unable to hold an object such as a provider client or `SecretStr`.
4. **Workflows carry identifiers only.** Workflow arguments are run IDs. Step and workflow
   results are references plus a status: `{"status": "succeeded", "output_id": ...}` or
   `{"status": "failed", "failure_class": ...}`. (Since Task 3 the status values are the
   shared state vocabulary: `complete`, `failed` or `provider_unavailable`.)
5. **One bounded activity per model task.** The activity is a DBOS step that:
   1. records an attempt row (the spend-reconciliation record) before any provider call;
   2. checks that the credential belongs to the run's workspace and is not revoked, then
      opens the sealed private payload and the sealed credential just in time (AES-256-GCM,
      with record kind, workspace ID and record ID as associated data). This is a
      consistency check, not actor authorisation. Since Task 3 the submitting command and
      the activity both check that the requesting actor still owns the workspace and is
      invited, the activity under the non-owner worker role with row-level security scoped
      to the run (ADR 0004 decision 5); the activity also first reuses an existing accepted
      output and reserves spend before the call (ADR 0004 decision 10);
   3. runs a plain Pydantic AI agent, **without** `DBOSDurability`, on the native Meta
      provider: `NativeOutput` schema mode, `request_limit=1`, output retries 0, OpenAI
      client `max_retries=0`. (Amended by ADR 0006 decision 9 for interview turns: one
      validation repair, so `request_limit=2` and output retries 1, the repair owned by the
      agent's output-retry budget and reserved within the attempt; the DBOS step still
      retries only transient provider failures.);
   4. persists the validated output sealed, idempotently (one accepted output per run; a
      re-executed activity reuses the first one and never overwrites it, and likewise
      returns a terminal failure an earlier execution already recorded);
   5. records usage on the attempt row and returns the reference.
6. **Typed, message-free error boundary.** Every exception inside the activity is
   classified from its type and HTTP status alone (`classify_failure`); its message is
   discarded.

   | Raised inside the activity | Classified as |
   |---|---|
   | `ModelHTTPError` 429, 500, 503 | transient (`transient_<status>`) |
   | `ModelTimeoutError`, `ModelConnectionError`, `ModelRequestTimeout` | transient (`transient_timeout`, `transient_connection`, `transient_request_timeout`) |
   | `ModelHTTPError` 401 / 402 / 403 | `provider_authentication` / `provider_billing` / `provider_permission` |
   | any other `ModelHTTPError` status (including 504) | `provider_request_rejected` |
   | `UsageLimitExceeded`, `UnexpectedModelBehavior` | `invalid_model_output` |
   | `CredentialUnavailableError` (revoked, or another workspace's) | `credential_unavailable` |
   | anything else: store, crypto, a bug, or an unrecognised `ModelAPIError` | `unknown_failure`; the attempt row records `unknown_failure:<ClassName>`, and a log line carries only the run ID and that label |

   The classification happens inside the handler. Everything after it (finishing the
   attempt row, re-raising) happens outside the handler. Anything raised later therefore
   carries no provider exception as `__context__`, which DBOS would otherwise store and log
   with its traceback. A transient failure leaves the step as a `TransientProviderError`
   that carries only its label. Terminal failures leave as a `failed/<class>` outcome.
   Evidence:
   - A mutation test: raising the transient error inside the handler without `from None`
     put a credential fragment into the worker log.
   - A reproduction against the pre-fix activity: a connection error or an unexpected
     error left the run stuck in `queued`.
   - By DBOS's code, the raw exception text would then be stored in the step and workflow
     error records and logged with its traceback. That journal was not inspected in the
     reproduction.
7. **One retry owner per failure class.** The DBOS step owns provider transients; the
   activity's store budget owns store transients; they never overlap. For the step,
   `retries_allowed=True`, `max_attempts=3`, and `should_retry` accepts only
   `TransientProviderError`. Client and agent retries are off.
   When retries are exhausted, the workflow publishes `failed/provider_unavailable`, never
   an empty success. Exceptions outside the activity's control (for example, the
   application database being down while the attempt row or the outcome is written)
   still escape the step and leave the workflow in DBOS `ERROR`, with the run `queued`.
   Task 3 closed this (ADR 0004 decision 11). The activity retries its own store work
   within a separate 60-second budget, keeping a paid call's result, and past it ends
   `failed/app_store_unavailable` without a step retry, because a retry would call the
   model again; so `should_retry` still accepts only `TransientProviderError`. Publication
   retries through an outage. Acceptance tests:
   `test_a_short_app_database_outage_mid_call_keeps_the_paid_result` and
   `test_an_outage_longer_than_the_store_budget_ends_in_a_typed_terminal_state`. A workflow
   that still ends in DBOS `ERROR` is reconciled from the application's own records: the
   accepted output if there is one, otherwise the recorded failure or `unknown_failure`.
   That path is tested separately by simulating the `ERROR` state
   (`test_the_reconciler_publishes_an_errored_workflow_s_accepted_output`). Transient
   provider exhaustion publishes the run state `provider_unavailable` with that failure
   class.
8. **Transactional outbox.** The domain write and its outbox row commit in one application
   transaction. The dispatcher starts the workflow with `SetWorkflowID(outbox.workflow_id)`
   and then marks the row dispatched. Dispatch is at least once; the workflow ID makes the
   start exactly once (a replay returns the existing workflow).
9. **Pinned application version.** `application_version` is set explicitly per release.
   DBOS recovers only PENDING workflows of the same executor and version. Changing a
   workflow's step sequence needs a new version and a drain of in-flight workflows.
10. **`DBOSDurability` is not used in L0.** The negative control showed it journals the
    model's response, which is private derived content, in `dbos.operation_outputs`.
    Adopting it later needs a new ADR with an encrypting payload codec and its own leak
    tests.

Recovery granularity is the whole activity. A crash during the provider call re-executes
the call, so duplicate spend is possible. Every attempt is recorded for reconciliation, and
exactly-once model calls are not claimed.

## Evidence (Sprint 0)

Task 3 retired the spike code (it remains in git history at `ff449da`) and re-established
every scenario below against the product modules in `make acceptance`
(`backend/tests/integration/test_durable_runs.py`, `test_worker_boundaries.py` and
`test_leak_negative_control.py`); the live check is now `make live-smoke` (ledger row 12).
The Sprint 0 record follows unchanged.

`uv run pytest -m integration spikes/durable -v`: 12 passed. Each scenario ends with a scan
of every row in both databases and of every worker log. The needles are the credential
(any 12-character fragment), the private-text sentinels, and any 24-character window of the
private text. The scan reads plain text, base64/pickle and bytea-hex views:

| Scenario | Result |
|---|---|
| SIGKILL during the model call; restarted worker recovers through DBOS | one accepted output; attempts `[unfinished, succeeded]`; workflow `SUCCESS` |
| SIGKILL after the output is persisted, before the step result is recorded | the accepted row is byte-for-byte unchanged; second attempt `reused_accepted` |
| SIGKILL after `start_workflow`, before the outbox mark; outbox replayed | one workflow for the run, one output, entry marked |
| Completed outbox entry re-delivered | no new attempt, output or workflow |
| HTTP 429 once (provider body echoes the key) | retried by the DBOS step only; success; nothing leaked |
| HTTP 503 every time | three attempts; `failed/provider_unavailable`; no output |
| HTTP 401 whose body echoes 20 characters of the key | `failed/provider_authentication`; nothing leaked |
| Connection error every time (message echoes the key) | three `transient_connection` attempts; `failed/provider_unavailable`; nothing leaked |
| Unexpected `RuntimeError` quoting the key and the private input | `failed/unknown_failure`; attempt `unknown_failure:RuntimeError`; no step error journalled; nothing leaked |
| Credential revoked before dispatch | `failed/credential_unavailable`; no model call |
| Negative control: `DBOSDurability` inside a workflow | scan **finds** the private output in `dbos.operation_outputs` |
| Live-check orchestration (fake model) times out mid-call | every activity attempt is still in the ledger, with unknown cost and its reservation committed |

The two error scenarios were reproduced against the pre-fix activity first: both runs stayed
`queued` until the 60 s timeout.

Live check (`uv run python -m spikes.durable.live_run`, ledger calls 10–11). The real Meta
key was sealed into the credential store and opened only inside the activity; the test
model returned a typed `ProfileProposal`. An unissued key ended as
`failed/provider_authentication`. The scan found no 12-character fragment of either key and
no occurrence of the private-text sentinel in any row of either database or in the worker
log. That run's needles did not include the model's opened output strings or windows of the
private text, and the real output did not contain the sentinel. So the run proves no key
leaked and no sentinel leaked; it does not prove that no private text leaked. The current
`live_run.py` adds both needles, but it has not been re-run live.

## Consequences and follow-ups

- Step `timeout_seconds` works only for async steps. The activity is a sync step bounded by
  the HTTP client timeout (120 s). Revisit if activities become async.
- Workflow cancellation (`DBOS.cancel_workflow`) and deletion of workflow history on account
  deletion were not exercised. Task 3 did not implement them either (no cancel command yet;
  DUR-05 and DUR-06 stay open for the run-lifecycle, solver and deletion work in Sprints 3,
  6 and 8). The journal holds only identifiers, but the spec still requires workflow-history
  rows to be deleted under the deletion policy.
- DBOS logs the value when serialization fails (`Error serializing object: ...`). The
  portable serializer and the identifier-only contract make that path unreachable for valid
  code. Treat any serialization error as a defect.
- At launch DBOS prints a Conductor console URL. No Conductor key is configured. Task 3's
  demo-mode probe covers the worker: it has no route out (ADR 0004 decision 1).
- Pydantic AI's DBOS page says DBOS cannot select non-retryable exceptions. DBOS 3.3.0 does,
  through `should_retry`, and this composition relies on it.
- Resolved in Task 3 (carry-forward M4): the activity checks for an accepted output before
  anything else and records the call's usage in the same transaction as the accept, so a
  crash after acceptance neither re-calls the model nor loses the first attempt's usage
  (`test_a_crash_after_acceptance_never_calls_the_model_again_and_keeps_the_usage`). The
  same holds on the failure branch: a crash after a terminal failure is recorded publishes
  that failure on re-execution with a `reused_failure` attempt and no second call
  (`test_a_crash_after_a_recorded_failure_returns_it_without_a_second_call`).
- Task 3 runs the agent with `asyncio.run(agent.run(...))` on the DBOS step thread instead
  of `run_sync`, which calls the deprecated `asyncio.get_event_loop()`.
- The Sprint 0 shutdown hang (1 in 19 runs) was not reproduced. Shutdown is now bounded: the
  worker destroys DBOS under a 10 s watchdog that exits the process, and Compose kills it
  after a 15 s grace; DBOS recovers in-flight work on the next start.
