"""The pinned composition: a DBOS workflow over identifiers, one bounded model activity.

The workflow and its journal see only run IDs and output references. The activity (a DBOS
step) opens the sealed payload and credential just in time, runs a plain Pydantic AI agent
without the DBOS durability capability, persists the validated output sealed, and returns
a reference. Every failure leaves the step as a typed, message-free value: a terminal
failure class, or a transient error that the DBOS step (the single retry owner) retries.
"""

import logging
import os
import signal
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from dbos import DBOS
from dbos import error as dbos_error
from pydantic import BaseModel, SecretStr
from pydantic_ai import Agent, NativeOutput, capture_run_messages
from pydantic_ai.exceptions import (
    ModelConnectionError,
    ModelHTTPError,
    ModelRequestTimeout,
    ModelTimeoutError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model
from pydantic_ai.usage import UsageLimits

from spikes.durable.store import AppStore, AttemptUsage, CredentialUnavailableError

ACTIVITY_MAX_ATTEMPTS = 3
TRANSIENT_STATUSES = frozenset({429, 500, 503})

Outcome = dict[str, str]

_log = logging.getLogger(__name__)


class ProfileProposal(BaseModel):
    """What the model proposes from private text; committing it is the application's job."""

    proposed_title: str
    evidence_quote: str


class FailureClass(StrEnum):
    CREDENTIAL_UNAVAILABLE = "credential_unavailable"
    PROVIDER_AUTHENTICATION = "provider_authentication"
    PROVIDER_BILLING = "provider_billing"
    PROVIDER_PERMISSION = "provider_permission"
    PROVIDER_REQUEST_REJECTED = "provider_request_rejected"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    INVALID_MODEL_OUTPUT = "invalid_model_output"
    UNKNOWN_FAILURE = "unknown_failure"


_STATUS_FAILURES = {
    401: FailureClass.PROVIDER_AUTHENTICATION,
    402: FailureClass.PROVIDER_BILLING,
    403: FailureClass.PROVIDER_PERMISSION,
}


class TransientProviderError(Exception):
    """Retryable provider failure. Carries a type-derived label only, never provider text."""

    def __init__(self, label: str) -> None:
        super().__init__(f"transient provider failure ({label})")


@dataclass(frozen=True)
class Classified:
    """How an attempt failed, derived only from the exception's type and HTTP status."""

    label: str  # recorded as the attempt outcome
    failure: FailureClass | None  # None: transient, so the DBOS step retries


def _terminal(failure: FailureClass) -> Classified:
    return Classified(failure.value, failure)


def classify_failure(error: Exception) -> Classified:
    # Order matters: ModelTimeoutError is a ModelConnectionError, and every provider error is
    # a ModelAPIError; anything unrecognised is an unknown failure, named by class only.
    if isinstance(error, ModelHTTPError):
        if error.status_code in TRANSIENT_STATUSES:
            return Classified(f"transient_{error.status_code}", None)
        return _terminal(
            _STATUS_FAILURES.get(error.status_code, FailureClass.PROVIDER_REQUEST_REJECTED)
        )
    if isinstance(error, ModelTimeoutError):
        return Classified("transient_timeout", None)
    if isinstance(error, ModelConnectionError):
        return Classified("transient_connection", None)
    if isinstance(error, ModelRequestTimeout):
        return Classified("transient_request_timeout", None)
    if isinstance(error, UsageLimitExceeded | UnexpectedModelBehavior):
        return _terminal(FailureClass.INVALID_MODEL_OUTPUT)
    return Classified(
        f"{FailureClass.UNKNOWN_FAILURE.value}:{type(error).__name__}",
        FailureClass.UNKNOWN_FAILURE,
    )


@dataclass(frozen=True)
class ActivityRuntime:
    """Composition-root dependencies for the activity (set once per worker process)."""

    store: AppStore
    model_id: str
    build_model: Callable[[SecretStr], Model]
    crash_point: str | None = None


_runtime: ActivityRuntime | None = None


def configure(runtime: ActivityRuntime) -> None:
    global _runtime
    _runtime = runtime


def _rt() -> ActivityRuntime:
    if _runtime is None:
        raise RuntimeError("workflow runtime is not configured")
    return _runtime


def _crash_if(point: str) -> None:
    # Test hook: a real SIGKILL at a named point, so recovery is exercised, not simulated.
    if _rt().crash_point == point:
        os.kill(os.getpid(), signal.SIGKILL)


def _usage(messages: list[ModelMessage]) -> AttemptUsage | None:
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    if not responses:
        return None
    return AttemptUsage(
        input_tokens=sum(r.usage.input_tokens for r in responses),
        cached_input_tokens=sum(r.usage.cache_read_tokens for r in responses),
        output_tokens=sum(r.usage.output_tokens for r in responses),
        reasoning_tokens=sum(r.usage.details.get("reasoning_tokens", 0) for r in responses),
        web_search_queries=sum(r.usage.details.get("web_search_requests", 0) for r in responses),
        provider_response_id=responses[-1].provider_response_id,
    )


def _failed(failure: FailureClass) -> Outcome:
    return {"status": "failed", "failure_class": failure.value}


@dataclass(frozen=True)
class _AttemptEnd:
    label: str  # recorded as the attempt outcome
    outcome: Outcome | None  # None: transient, raise for the DBOS step to retry
    usage: AttemptUsage | None = None


def _ended(classified: Classified, usage: AttemptUsage | None) -> _AttemptEnd:
    outcome = None if classified.failure is None else _failed(classified.failure)
    return _AttemptEnd(classified.label, outcome, usage)


def _attempt(rt: ActivityRuntime, run_id: str) -> _AttemptEnd:
    try:
        inputs = rt.store.resolve_activity_inputs(run_id)
    except CredentialUnavailableError:
        return _ended(_terminal(FailureClass.CREDENTIAL_UNAVAILABLE), None)

    agent = Agent(
        rt.build_model(inputs.api_key),
        output_type=NativeOutput(ProfileProposal),
        instructions=(
            "Propose one job title for this synthetic person and quote the sentence of their "
            "text that supports it. Answer only with the requested JSON."
        ),
        retries=0,
    )
    with capture_run_messages() as messages:
        try:
            result = agent.run_sync(inputs.private_text, usage_limits=UsageLimits(request_limit=1))
        except Exception as error:
            # Classify inside the handler but act outside it: anything raised later would
            # otherwise chain this exception, provider text included, as its context.
            classified: Classified | None = classify_failure(error)
        else:
            classified = None
    if classified is not None:
        return _ended(classified, _usage(messages))

    _crash_if("before_output_persisted")
    accepted = rt.store.accept_output(run_id, inputs.workspace_id, result.output.model_dump_json())
    _crash_if("after_output_persisted")
    label = "succeeded" if accepted.newly_accepted else "reused_accepted"
    return _AttemptEnd(
        label, {"status": "succeeded", "output_id": accepted.output_id}, _usage(messages)
    )


def _is_transient(error: BaseException) -> bool:
    return isinstance(error, TransientProviderError)


@DBOS.step(
    name="nessa_spike.bounded_model_activity",
    retries_allowed=True,
    max_attempts=ACTIVITY_MAX_ATTEMPTS,
    interval_seconds=0.2,
    should_retry=_is_transient,
)
def bounded_model_activity(run_id: str) -> Outcome:
    rt = _rt()
    attempt_id = rt.store.begin_attempt(run_id, rt.model_id)
    try:
        end = _attempt(rt, run_id)
    except Exception as error:
        # Store, crypto or programming failure. Keep the class name only: the message could
        # quote private input, provider text or a key.
        end = _ended(classify_failure(error), None)
        _log.warning("bounded activity failed: run_id=%s outcome=%s", run_id, end.label)
    rt.store.finish_attempt(attempt_id, end.label, end.usage)
    if end.outcome is None:
        # Raised outside any handler, so no provider exception rides along as context into
        # DBOS's step-error record or its retry log.
        raise TransientProviderError(end.label)
    return end.outcome


@DBOS.step(name="nessa_spike.publish_outcome")
def publish_outcome(run_id: str, outcome: Outcome) -> None:
    _rt().store.complete_run(run_id, outcome)


@DBOS.workflow(name="nessa_spike.profile_run")
def profile_run_workflow(run_id: str) -> Outcome:
    try:
        outcome = bounded_model_activity(run_id)
    except dbos_error.DBOSMaxStepRetriesExceeded:
        outcome = _failed(FailureClass.PROVIDER_UNAVAILABLE)
    publish_outcome(run_id, outcome)
    return outcome
