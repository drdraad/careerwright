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
   and PostgreSQL 16.15, as locked in `backend/uv.lock`. Bumping either re-runs the
   integration suite in `backend/spikes/durable/test_durability.py`, or its successor in
   `make acceptance`.
2. **Separate databases, non-owner runtime roles.** The DBOS system database and the
   application database are separate databases. The application database is authoritative;
   DBOS state is execution bookkeeping. Each database is owned by a migration role that only
   setup uses: it runs Alembic migrations and DBOS's schema migrations
   (`run_dbos_database_migrations`). The API and workers connect as **non-owner** runtime
   roles with only the grants they need, and launch DBOS with `run_migrations=False`. An
   owner bypasses row-level security, so a runtime connection as owner would break Global
   Constraint 7. The spike connects as each database's owner. That is a spike shortcut and
   not part of this decision; Task 3 implements and tests the role split.
3. **Portable JSON journal.** Configure `DBOSConfig(serializer=DBOSPortableJSONSerializer())`.
   The journal is then plain JSON: inspectable without unpickling database content, and
   unable to hold an object such as a provider client or `SecretStr`.
4. **Workflows carry identifiers only.** Workflow arguments are run IDs. Step and workflow
   results are references plus a status: `{"status": "succeeded", "output_id": ...}` or
   `{"status": "failed", "failure_class": ...}`.
5. **One bounded activity per model task.** The activity is a DBOS step that:
   1. records an attempt row (the spend-reconciliation record) before any provider call;
   2. checks that the credential belongs to the run's workspace and is not revoked, then
      opens the sealed private payload and the sealed credential just in time (AES-256-GCM,
      with record kind, workspace ID and record ID as associated data). This is a
      consistency check, not actor authorisation. The spike has no actors. Checking that
      the requesting actor owns the workspace, both in the submitting command and again
      inside the activity under a non-owner role, is Sprint 1 work (Task 3);
   3. runs a plain Pydantic AI agent, **without** `DBOSDurability`, on the native Meta
      provider: `NativeOutput` schema mode, `request_limit=1`, output retries 0, OpenAI
      client `max_retries=0`;
   4. persists the validated output sealed, idempotently (one accepted output per run; a
      re-executed activity reuses the first one and never overwrites it);
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
7. **One retry owner: the DBOS step.** `retries_allowed=True`, `max_attempts=3`, and
   `should_retry` accepts only `TransientProviderError`. Client and agent retries are off.
   When retries are exhausted, the workflow publishes `failed/provider_unavailable`, never
   an empty success. Exceptions outside the activity's control (for example, the
   application database being down while the attempt row or the outcome is written)
   still escape the step and leave the workflow in DBOS `ERROR`, with the run `queued`.
   Detecting and reconciling such runs belongs to the Sprint 1 run lifecycle (Task 3).
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
  deletion were not exercised. They belong to the run-lifecycle and deletion work in Sprints
  1, 3 and 8. The journal holds only identifiers, but the spec still requires workflow-history
  rows to be deleted under the deletion policy.
- DBOS logs the value when serialization fails (`Error serializing object: ...`). The
  portable serializer and the identifier-only contract make that path unreachable for valid
  code. Treat any serialization error as a defect.
- At launch DBOS prints a Conductor console URL. The spike configured no Conductor key and
  did not check outbound traffic. Demo mode's "no outbound requests" check (Sprint 1) must
  include the worker.
- Pydantic AI's DBOS page says DBOS cannot select non-retryable exceptions. DBOS 3.3.0 does,
  through `should_retry`, and this composition relies on it.
- Carried forward to Task 3: a crash after the output is saved re-calls the model and loses
  the first attempt's usage. The activity should check for an accepted output before calling
  the model, and record usage in the same transaction as the accept.
