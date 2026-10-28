"""The bounded model activity: one provider call for one run, with everything checked first.

ADR 0002's pattern, as product code, for every run kind (`RunTask`). The workflow carries
only the run ID. This activity, under the worker role and row-level security scoped to
that run:
1. ends at once if the run already has an accepted output or a recorded terminal failure
   (a crash after either never re-calls the model, and the first call's usage is already
   recorded with it);
2. re-checks that the requester still owns the workspace and is invited, that the pinned
   model is allowed for the workspace's data (Contributor only for synthetic, the fixture
   interviewer only for demo), that an unrevoked key exists, and reserves the attempt's
   worst-case cost within the spend limits;
3. records the attempt (the reservation) before the call, then opens the sealed input and
   the sealed key just in time and runs the kind's task: a plain Pydantic AI agent, no
   durability capability, no transport retries, at most the task's requests (a validation
   repair is one more request, owned by the agent's output-retry budget, never the step's);
4. stores the validated output sealed and the usage on the attempt in one transaction.

While a task's reply streams, the reply so far is sealed into the run's partial store
(`run_partials`; its status events carry the run ID and a sequence only). The validated
output supersedes it in the transaction that stores the output; a failed attempt marks it
stopped, in a savepoint that can never abort the attempt's settlement. A partial reply is
never validated, never a result, and never applied.

Its own database work is retried through an outage for `store_retry_budget_s`, keeping a
paid call's result in memory; past that budget the run fails `app_store_unavailable`,
because a DBOS step retry would call the model again.

Every exception is classified from its type alone and its message discarded; an output cut
off at its token limit is `output_truncated` (from the typed finish reason), never parsed
or repaired (`TruncationGuard`, on every task's agent).
Classification happens inside the handler; the caller raises outside it, so no provider
exception rides along as context into DBOS's step-error record or retry log.
"""

import asyncio
import hashlib
import logging
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, SecretStr
from pydantic_ai import Agent, NativeOutput, RunContext, capture_run_messages
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from pydantic_ai.models import Model, ModelRequestContext
from pydantic_ai.usage import UsageLimits

from nessa.db import Engine, StoreUnavailableError, Tx, in_savepoint, run_transaction
from nessa.identity import connection_check, credential_store, run_store, store
from nessa.identity.connection_check import ConnectionCheckResult
from nessa.identity.credentials import credential_context
from nessa.identity.failures import (
    STORE_LABEL,
    Classified,
    FailureClass,
    OutputTruncatedError,
    classify_failure,
    recorded_failure,
    terminal,
)
from nessa.identity.keyring import Keyring, SealedValue
from nessa.identity.model_registry import ModelMode, Usage, estimate_cost_nano_usd, model_entry
from nessa.identity.records import EventKind, PartialCompleteness, Run, RunKind
from nessa.identity.runs import end_partial, input_context, output_context, record_partial
from nessa.identity.spend import SpendState, period_start, refused_scope
from nessa.vocabulary import DataMode, WorkState

Outcome = dict[str, str]
# A model for a model ID; the key is None for the fixture interviewer, which needs none.
ModelBuilder = Callable[[str, SecretStr | None], Model]


# Where a task sends the natural-language reply so far while the output streams.
class PartialSink(Protocol):
    """Takes the reply so far each time the stream moves; `complete` once the reply ends."""

    def __call__(self, text: str, *, complete: bool) -> None: ...


# How long the activity keeps retrying its own database work (the attempt row, the result)
# through an outage before the run fails `app_store_unavailable`.
STORE_RETRY_BUDGET_S = 60.0
STORE_RETRY_FIRST_DELAY_S = 0.5
STORE_RETRY_MAX_DELAY_S = 8.0
# At most one partial-reply write (and status event) per interval while a reply streams.
PARTIAL_WRITE_INTERVAL_S = 0.25
_log = logging.getLogger("nessa.activity")


@dataclass(frozen=True)
class RunTask:
    """How the activity runs one kind of run.

    `call` gets the model, its privacy mode, the run's opened input (None for a kind
    without one) and a sink for the streamed reply so far (a kind that streams nothing
    ignores it), and returns the validated output to seal, or raises.
    `worst_case_nano_usd` bounds one attempt's cost (every request it may send) for a
    model ID."""

    call: Callable[[Model, ModelMode, bytes | None, PartialSink], BaseModel]
    worst_case_nano_usd: Callable[[str], int]
    has_input: bool


@dataclass(frozen=True)
class ActivityRuntime:
    """Composition-root dependencies, set once per worker process."""

    engine: Engine
    keyring: Keyring
    build_model: ModelBuilder
    clock: Callable[[], datetime]
    tasks: Mapping[RunKind, RunTask]
    store_retry_budget_s: float = STORE_RETRY_BUDGET_S


@dataclass(frozen=True)
class ActivityEnd:
    label: str  # the attempt's recorded outcome
    outcome: Outcome | None  # None: transient; the DBOS step retries


@dataclass(frozen=True)
class _Ready:
    run: Run
    mode: ModelMode
    attempt_id: int
    credential_id: uuid.UUID | None
    sealed_key: SealedValue | None
    sealed_input: SealedValue | None


@dataclass(frozen=True)
class _CallResult:
    output: BaseModel | None
    classified: Classified | None
    usage: Usage | None
    reasoning_tokens: int | None
    response_id: str | None
    requests_sent: int
    responses: int  # that reported usage
    partial: str | None  # the reply so far, if the task streamed one


class PartialWriter:
    """A streamed reply's writes: the first piece at once, then the newest text at most once
    per `interval_s` (on any later stream event, so the end of a burst is not dropped), and
    the whole reply as soon as it ends, whatever the interval.

    Streaming is for responsiveness only. A write that fails stops this attempt's streaming
    and never fails or retries the call (a retry would pay again); settling the attempt
    records the latest reply as superseded or stopped either way."""

    def __init__(
        self,
        write: Callable[[str], None],
        *,
        clock: Callable[[], float] = time.monotonic,
        interval_s: float = PARTIAL_WRITE_INTERVAL_S,
    ) -> None:
        self._write = write
        self._clock = clock
        self._interval_s = interval_s
        self._written: str | None = None
        self._written_at: float | None = None
        self._stopped = False
        self.latest: str | None = None

    def __call__(self, text: str, *, complete: bool) -> None:
        self.latest = text
        if self._stopped or text == self._written:
            return
        now = self._clock()
        due = self._written_at is None or now - self._written_at >= self._interval_s
        if not (complete or due):
            return
        self._written, self._written_at = text, now
        try:
            self._write(text)
        except Exception as error:
            self._stopped = True
            _log.warning("partial reply not written", extra={"error_class": type(error).__name__})


def _write_partial(rt: ActivityRuntime, run: Run, text: str) -> None:
    with run_transaction(rt.engine, run.run_id) as tx:
        record_partial(tx, rt.keyring, run, text, PartialCompleteness.STREAMING)


def _end_partial(tx: Tx, keyring: Keyring, run: Run, latest: str | None) -> None:
    """Mark the run's partial stopped without ever aborting the transaction around it (the
    attempt's settlement): when the worker may no longer write it (access revoked mid-call),
    or anything else refuses the write, the savepoint is rolled back and the failure logged."""
    refused = in_savepoint(tx, lambda: end_partial(tx, keyring, run, latest))
    if refused is not None:
        _log.warning(
            "partial reply not marked stopped",
            extra={"run_id": str(run.run_id), "error_class": refused},
        )


def succeeded(output_id: uuid.UUID) -> Outcome:
    return {"status": WorkState.COMPLETE.value, "output_id": str(output_id)}


def failed(failure: FailureClass) -> Outcome:
    status = (
        WorkState.PROVIDER_UNAVAILABLE
        if failure is FailureClass.PROVIDER_UNAVAILABLE
        else WorkState.FAILED
    )
    return {"status": status.value, "failure_class": failure.value}


class TruncationGuard(AbstractCapability[Any]):
    """Ends the run the moment a response stops at its token limit: a cut-off output is
    never parsed and never sent back for repair (which would spend a second request).

    The response is kept in the run's history first, so its reported usage is booked."""

    async def after_model_request(
        self,
        ctx: RunContext[Any],
        *,
        request_context: ModelRequestContext,
        response: ModelResponse,
    ) -> ModelResponse:
        if response.finish_reason == "length":
            ctx.messages.append(response)
            raise OutputTruncatedError
        return response


def connection_check_agent(model: Model) -> Agent[None, ConnectionCheckResult]:
    return Agent(
        model,
        output_type=NativeOutput(ConnectionCheckResult),
        instructions=connection_check.INSTRUCTIONS,
        retries=0,
        capabilities=[TruncationGuard()],
    )


def run_connection_check(agent: Agent[None, ConnectionCheckResult]) -> ConnectionCheckResult:
    """One bounded request on a fresh event loop (the step runs on a DBOS worker thread)."""
    result = asyncio.run(
        agent.run(connection_check.PROMPT, usage_limits=UsageLimits(request_limit=1))
    )
    return result.output


CONNECTION_CHECK_TASK = RunTask(
    call=lambda model, mode, _input, _sink: run_connection_check(connection_check_agent(model)),
    worst_case_nano_usd=connection_check.worst_case_nano_usd,
    has_input=False,
)


def _ended(classified: Classified) -> ActivityEnd:
    return ActivityEnd(
        classified.label, None if classified.failure is None else failed(classified.failure)
    )


def _recorded_failure(tx: Tx, run_id: uuid.UUID) -> FailureClass | None:
    for attempt in run_store.attempts(tx, run_id):
        failure = recorded_failure(attempt.outcome)
        if failure is not None:
            return failure
    return None


def model_refusal(run: Run, mode: ModelMode) -> FailureClass | None:
    """Defence in depth for the submission rule and the database CHECKs: Contributor only for
    synthetic data, the fixture interviewer only for demo workspaces and vice versa."""
    if mode is ModelMode.CONTRIBUTOR and not run.synthetic:
        return FailureClass.MODEL_NOT_PERMITTED
    if (mode is ModelMode.FIXTURE) != (run.data_mode is DataMode.DEMO):
        return FailureClass.MODEL_NOT_PERMITTED
    return None


def _prepare(rt: ActivityRuntime, run_id: uuid.UUID) -> _Ready | ActivityEnd:
    now = rt.clock()
    with run_transaction(rt.engine, run_id) as tx:
        run = run_store.run(tx, run_id, lock=True)
        if run is None:
            return _ended(terminal(FailureClass.UNKNOWN_FAILURE))
        if run_store.mark_running(tx, run_id):
            store.append_event(
                tx,
                run.workspace_id,
                EventKind.RUN_STATE_CHANGED,
                str(run_id),
                state=WorkState.RUNNING,
            )
        run_store.interrupt_unfinished_attempts(tx, run_id)
        period = period_start(now)

        def refuse(failure: FailureClass) -> ActivityEnd:
            run_store.insert_attempt(
                tx, run=run, period=period, spend_state=SpendState.NONE, outcome=failure.value
            )
            return _ended(terminal(failure))

        existing = run_store.accepted_output(tx, run_id)
        if existing is not None:
            run_store.insert_attempt(
                tx, run=run, period=period, spend_state=SpendState.NONE, outcome="reused_accepted"
            )
            return ActivityEnd("reused_accepted", succeeded(existing))
        recorded = _recorded_failure(tx, run_id)
        if recorded is not None:
            run_store.insert_attempt(
                tx, run=run, period=period, spend_state=SpendState.NONE, outcome="reused_failure"
            )
            return ActivityEnd("reused_failure", failed(recorded))
        if run_store.authorised_workspace(tx) != run.workspace_id:
            return refuse(FailureClass.ACCESS_REVOKED)
        task = rt.tasks.get(run.kind)
        if task is None:
            return refuse(FailureClass.UNKNOWN_FAILURE)
        mode = model_entry(run.model_id).mode
        refusal = model_refusal(run, mode)
        if refusal is not None:
            return refuse(refusal)
        sealed_input = run_store.sealed_input(tx, run_id) if task.has_input else None
        if task.has_input and sealed_input is None:
            return refuse(FailureClass.UNKNOWN_FAILURE)
        if mode is ModelMode.FIXTURE:
            # No provider, key or charge: the attempt still records that it ran.
            attempt_id = run_store.insert_attempt(
                tx, run=run, period=period, spend_state=SpendState.NONE
            )
            return _Ready(run, mode, attempt_id, None, None, sealed_input)
        key = credential_store.sealed_active_credential(tx, run.workspace_id)
        if key is None:
            return refuse(FailureClass.CREDENTIAL_UNAVAILABLE)
        run_store.lock_spend(tx, run.workspace_id)
        limits = credential_store.spend_limits(tx, run.workspace_id)
        worst_case = task.worst_case_nano_usd(run.model_id)
        period_committed, run_committed = run_store.committed_spend(
            tx, run.workspace_id, run_id, period
        )
        if limits is None or refused_scope(
            limits[0],
            period_committed=period_committed,
            run_committed=run_committed,
            worst_case=worst_case,
        ):
            return refuse(FailureClass.BUDGET_EXCEEDED)
        attempt_id = run_store.insert_attempt(
            tx,
            run=run,
            period=period,
            spend_state=SpendState.HELD,
            reserved_nano_usd=worst_case,
            credential_id=key[0],
        )
    return _Ready(run, mode, attempt_id, key[0], key[1], sealed_input)


def _measured(messages: list[ModelMessage]) -> list[ModelResponse]:
    """The complete responses that reported usage. A streamed request that fails still
    leaves a response in the history: with no usage if it failed at once, or `interrupted`
    with the usage counted so far if the stream broke part-way. Either may have been billed
    in full, so neither counts: the attempt's cost is unknown, never a partial sum."""
    return [
        m
        for m in messages
        if isinstance(m, ModelResponse) and m.state != "interrupted" and m.usage.has_values()
    ]


def _usage(messages: list[ModelMessage]) -> tuple[Usage | None, int | None, str | None]:
    responses = _measured(messages)
    if not responses:
        return None, None, None
    usage = Usage(
        input_tokens=sum(r.usage.input_tokens for r in responses),
        cached_input_tokens=sum(r.usage.cache_read_tokens for r in responses),
        output_tokens=sum(r.usage.output_tokens for r in responses),
        web_search_queries=sum(r.usage.details.get("web_search_requests", 0) for r in responses),
    )
    reasoning = sum(r.usage.details.get("reasoning_tokens", 0) for r in responses)
    return usage, reasoning, responses[-1].provider_response_id


def _truncated(messages: list[ModelMessage]) -> bool:
    """The last response stopped at its token limit: whatever it holds is incomplete."""
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    return bool(responses) and responses[-1].finish_reason == "length"


def _open(rt: ActivityRuntime, ready: _Ready) -> tuple[SecretStr | None, bytes | None]:
    run = ready.run
    api_key = None
    if ready.sealed_key is not None and ready.credential_id is not None:
        api_key = SecretStr(
            rt.keyring.open(
                ready.sealed_key, credential_context(run.workspace_id, ready.credential_id)
            ).decode()
        )
    opened = None
    if ready.sealed_input is not None:
        opened = rt.keyring.open(ready.sealed_input, input_context(run.workspace_id, run.run_id))
    return api_key, opened


def _call(rt: ActivityRuntime, ready: _Ready) -> _CallResult:
    task = rt.tasks[ready.run.kind]
    partial = PartialWriter(lambda text: _write_partial(rt, ready.run, text))
    with capture_run_messages() as messages:
        try:
            api_key, opened = _open(rt, ready)
            output: BaseModel | None = task.call(
                rt.build_model(ready.run.model_id, api_key), ready.mode, opened, partial
            )
        except Exception as error:
            # Classify inside the handler but act outside it (see the module docstring).
            classified: Classified | None = classify_failure(error)
            output = None
        else:
            classified = None
            # Every task's agent stops at a cut-off response (`TruncationGuard`); this keeps
            # the rule for any task: an output cut off at its limit is never accepted.
            if _truncated(messages):
                classified, output = terminal(FailureClass.OUTPUT_TRUNCATED), None
        requests = sum(isinstance(m, ModelRequest) for m in messages)
        responses = len(_measured(messages))
        if ready.mode is ModelMode.FIXTURE:
            return _CallResult(
                output, classified, None, None, None, requests, responses, partial.latest
            )
        try:
            usage, reasoning, response_id = _usage(messages)
        except ValueError as error:
            # Counts the registry rejects (more cached than input tokens): the provider's own
            # report is inconsistent, so the cost is unknown and the output is not accepted.
            classified = classified or classify_failure(error)
            output, usage, reasoning, response_id = None, None, None, None
    return _CallResult(
        output, classified, usage, reasoning, response_id, requests, responses, partial.latest
    )


def _spend(ready: _Ready, call: _CallResult) -> tuple[SpendState, int | None]:
    """The attempt's spend state and cost (None: unknown)."""
    if ready.mode is ModelMode.FIXTURE:
        return SpendState.NONE, 0  # no provider call was made
    # A request with no reported usage may still have been billed, so the cost stays unknown
    # and the whole reservation stays committed, even when an earlier request reported usage.
    if call.usage is None or call.responses < call.requests_sent:
        return SpendState.UNKNOWN, None
    return SpendState.RECONCILED, estimate_cost_nano_usd(ready.run.model_id, call.usage)


def _settle(rt: ActivityRuntime, ready: _Ready, call: _CallResult) -> ActivityEnd:
    spend_state, cost = _spend(ready, call)
    with run_transaction(rt.engine, ready.run.run_id) as tx:
        if call.output is None:
            classified = call.classified or terminal(FailureClass.UNKNOWN_FAILURE)
            end = _ended(classified)
            _end_partial(tx, rt.keyring, ready.run, call.partial)  # never a result
        else:
            output_id = uuid.uuid4()
            body = call.output.model_dump_json().encode()
            accepted, newly = run_store.insert_output(
                tx,
                output_id=output_id,
                run=ready.run,
                sealed=rt.keyring.seal(body, output_context(ready.run.workspace_id, output_id)),
                content_sha256=hashlib.sha256(body).hexdigest(),
            )
            end = ActivityEnd("succeeded" if newly else "reused_accepted", succeeded(accepted))
            run_store.delete_partial(tx, ready.run.run_id)  # superseded by the validated output
        # Usage is recorded in the same transaction as the accepted output (carry-forward M4).
        run_store.finish_attempt(
            tx,
            ready.attempt_id,
            outcome=end.label,
            usage=call.usage,
            reasoning_tokens=call.reasoning_tokens,
            provider_response_id=call.response_id,
            cost_nano_usd=cost,
            spend_state=spend_state,
            requests_sent=call.requests_sent,
        )
    return end


def _retrying_store[T](rt: ActivityRuntime, operation: Callable[[], T]) -> T:
    """Run one transaction, retrying a store failure with backoff until the budget is spent."""
    deadline = time.monotonic() + rt.store_retry_budget_s
    delay = STORE_RETRY_FIRST_DELAY_S
    while True:
        try:
            return operation()
        except StoreUnavailableError:
            if time.monotonic() + delay > deadline:
                raise
        time.sleep(delay)
        delay = min(delay * 2, STORE_RETRY_MAX_DELAY_S)


def _attempt(rt: ActivityRuntime, run_id: uuid.UUID) -> ActivityEnd:
    prepared = _retrying_store(rt, lambda: _prepare(rt, run_id))
    if isinstance(prepared, ActivityEnd):
        return prepared
    call = _call(rt, prepared)
    # If storing never succeeds, the attempt stays unfinished and publication settles it as
    # an unknown charge (the call may have been billed).
    return _retrying_store(rt, lambda: _settle(rt, prepared, call))


def execute(rt: ActivityRuntime, run_id: uuid.UUID) -> ActivityEnd:
    """Never raises: every failure becomes a label and, unless transient, an outcome."""
    try:
        end = _attempt(rt, run_id)
    except Exception as error:
        classified = classify_failure(error)
        if classified.label == STORE_LABEL:  # the store budget is spent: terminal
            classified = terminal(FailureClass.APP_STORE_UNAVAILABLE)
        end = _ended(classified)
    _log.info("activity attempt finished", extra={"run_id": str(run_id), "outcome": end.label})
    return end


def publish(rt: ActivityRuntime, run_id: uuid.UUID, outcome: Outcome) -> None:
    """Record the run's terminal state and its event, once."""
    status = WorkState(outcome["status"])
    with run_transaction(rt.engine, run_id) as tx:
        run = run_store.run(tx, run_id, lock=True)
        if run is None:
            return
        # A call whose result could not be stored (the database went away) is settled as an
        # unknown charge, never left looking in flight after the run has ended.
        run_store.interrupt_unfinished_attempts(tx, run_id)
        if status is not WorkState.COMPLETE:  # a crash can leave a partial still streaming
            _end_partial(tx, rt.keyring, run, None)
        output = outcome.get("output_id")
        if run_store.finish_run(
            tx,
            run_id,
            status,
            output_id=uuid.UUID(output) if output else None,
            failure=outcome.get("failure_class"),
        ):
            detail = (
                {"failure_class": outcome["failure_class"]} if "failure_class" in outcome else {}
            )
            store.append_event(
                tx,
                run.workspace_id,
                EventKind.RUN_STATE_CHANGED,
                str(run_id),
                state=status,
                detail=detail,
            )


def reconcile(rt: ActivityRuntime, run_id: uuid.UUID) -> bool:
    """Publish the outcome of a run whose workflow ended in DBOS `ERROR`, from the run's own
    records: its accepted output, else its recorded failure, else `unknown_failure`. A run
    that is already terminal is left alone. Never calls the model. Returns whether it
    published."""
    with run_transaction(rt.engine, run_id) as tx:
        run = run_store.run(tx, run_id)
        if run is None or run.status not in (WorkState.QUEUED, WorkState.RUNNING):
            return False
        output = run_store.accepted_output(tx, run_id)
        failure = _recorded_failure(tx, run_id) or FailureClass.UNKNOWN_FAILURE
    publish(rt, run_id, succeeded(output) if output is not None else failed(failure))
    return True
