"""The bounded model activity: one provider call for one run, with everything checked first.

ADR 0002's pattern, as product code. The workflow carries only the run ID. This activity,
under the worker role and row-level security scoped to that run:
1. ends at once if the run already has an accepted output (a crash after acceptance never
   re-calls the model, and the first call's usage is already recorded with it);
2. re-checks that the requester still owns the workspace and is invited, that the pinned
   model is allowed for the workspace's data (Contributor only for synthetic), that an
   unrevoked key exists, and reserves the call's worst-case cost within the spend limits;
3. records the attempt (the reservation) before the call, then opens the sealed key just in
   time and calls Meta with a plain Pydantic AI agent: no durability capability, no retries;
4. stores the validated output sealed and the usage on the attempt in one transaction.

Every exception is classified from its type alone and its message discarded. Classification
happens inside the handler; the caller raises outside it, so no provider exception rides
along as context into DBOS's step-error record or retry log.
"""

import asyncio
import hashlib
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from pydantic import SecretStr
from pydantic_ai import Agent, NativeOutput, capture_run_messages
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model
from pydantic_ai.usage import UsageLimits

from nessa.db import Engine, run_transaction
from nessa.identity import connection_check, credential_store, run_store, store
from nessa.identity.connection_check import ConnectionCheckResult
from nessa.identity.credentials import credential_context
from nessa.identity.failures import Classified, FailureClass, classify_failure, terminal
from nessa.identity.keyring import Keyring, SealedValue
from nessa.identity.model_registry import ModelMode, Usage, estimate_cost_nano_usd, model_entry
from nessa.identity.records import EventKind, Run
from nessa.identity.runs import output_context
from nessa.identity.spend import SpendState, period_start, refused_scope
from nessa.vocabulary import WorkState

Outcome = dict[str, str]
ModelBuilder = Callable[[str, SecretStr], Model]
_log = logging.getLogger("nessa.activity")


@dataclass(frozen=True)
class ActivityRuntime:
    """Composition-root dependencies, set once per worker process."""

    engine: Engine
    keyring: Keyring
    build_model: ModelBuilder
    clock: Callable[[], datetime]


@dataclass(frozen=True)
class ActivityEnd:
    label: str  # the attempt's recorded outcome
    outcome: Outcome | None  # None: transient; the DBOS step retries


@dataclass(frozen=True)
class _Ready:
    run: Run
    attempt_id: int
    credential_id: uuid.UUID
    sealed_key: SealedValue


@dataclass(frozen=True)
class _CallResult:
    output: ConnectionCheckResult | None
    classified: Classified | None
    usage: Usage | None
    reasoning_tokens: int | None
    response_id: str | None


def succeeded(output_id: uuid.UUID) -> Outcome:
    return {"status": WorkState.COMPLETE.value, "output_id": str(output_id)}


def failed(failure: FailureClass) -> Outcome:
    status = (
        WorkState.PROVIDER_UNAVAILABLE
        if failure is FailureClass.PROVIDER_UNAVAILABLE
        else WorkState.FAILED
    )
    return {"status": status.value, "failure_class": failure.value}


def connection_check_agent(model: Model) -> Agent[None, ConnectionCheckResult]:
    return Agent(
        model,
        output_type=NativeOutput(ConnectionCheckResult),
        instructions=connection_check.INSTRUCTIONS,
        retries=0,
    )


def run_connection_check(agent: Agent[None, ConnectionCheckResult]) -> ConnectionCheckResult:
    """One bounded request on a fresh event loop (the step runs on a DBOS worker thread)."""
    result = asyncio.run(
        agent.run(connection_check.PROMPT, usage_limits=UsageLimits(request_limit=1))
    )
    return result.output


def _ended(classified: Classified) -> ActivityEnd:
    return ActivityEnd(
        classified.label, None if classified.failure is None else failed(classified.failure)
    )


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
        if run_store.authorised_workspace(tx) != run.workspace_id:
            return refuse(FailureClass.ACCESS_REVOKED)
        if model_entry(run.model_id).mode is ModelMode.CONTRIBUTOR and not run.synthetic:
            return refuse(FailureClass.MODEL_NOT_PERMITTED)
        key = credential_store.sealed_active_credential(tx, run.workspace_id)
        if key is None:
            return refuse(FailureClass.CREDENTIAL_UNAVAILABLE)
        run_store.lock_spend(tx, run.workspace_id)
        limits = credential_store.spend_limits(tx, run.workspace_id)
        worst_case = connection_check.worst_case_nano_usd(run.model_id)
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
    return _Ready(run, attempt_id, key[0], key[1])


def _usage(messages: list[ModelMessage]) -> tuple[Usage | None, int | None, str | None]:
    responses = [m for m in messages if isinstance(m, ModelResponse)]
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


def _call(rt: ActivityRuntime, ready: _Ready) -> _CallResult:
    with capture_run_messages() as messages:
        try:
            api_key = SecretStr(
                rt.keyring.open(
                    ready.sealed_key,
                    credential_context(ready.run.workspace_id, ready.credential_id),
                ).decode()
            )
            output = run_connection_check(
                connection_check_agent(rt.build_model(ready.run.model_id, api_key))
            )
        except Exception as error:
            # Classify inside the handler but act outside it (see the module docstring).
            classified: Classified | None = classify_failure(error)
            output = None
        else:
            classified = None
    usage, reasoning, response_id = _usage(messages)
    return _CallResult(output, classified, usage, reasoning, response_id)


def _settle(rt: ActivityRuntime, ready: _Ready, call: _CallResult) -> ActivityEnd:
    cost = estimate_cost_nano_usd(ready.run.model_id, call.usage) if call.usage else None
    # No reported usage: the request may still have been billed, so the cost stays unknown.
    spend_state = SpendState.RECONCILED if cost is not None else SpendState.UNKNOWN
    with run_transaction(rt.engine, ready.run.run_id) as tx:
        if call.output is None:
            classified = call.classified or terminal(FailureClass.UNKNOWN_FAILURE)
            end = _ended(classified)
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
        )
    return end


def execute(rt: ActivityRuntime, run_id: uuid.UUID) -> ActivityEnd:
    """Never raises: every failure becomes a label and, unless transient, an outcome."""
    try:
        prepared = _prepare(rt, run_id)
    except Exception as error:
        end = _ended(classify_failure(error))
    else:
        if isinstance(prepared, ActivityEnd):
            end = prepared
        else:
            call = _call(rt, prepared)
            try:
                end = _settle(rt, prepared, call)
            except Exception as error:
                # The call happened but its result could not be stored. The attempt stays
                # unfinished; the retry marks it interrupted with an unknown cost.
                end = _ended(classify_failure(error))
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
