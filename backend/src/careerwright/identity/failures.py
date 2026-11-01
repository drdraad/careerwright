"""Typed, message-free failure classification for the bounded model activity (ADR 0002).

Every exception is classified from its type and HTTP status alone and its message is
discarded, because provider errors can echo the key and ours can quote private input. Each
transient class has one retry owner, and they never overlap: a transient provider failure
becomes a label-only exception for the DBOS step, which owns provider retries; a store
failure is retried by the activity itself within its store budget. Everything else is a
terminal failure class recorded on the run.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from pydantic_ai.exceptions import (
    ContentFilterError,
    ModelConnectionError,
    ModelHTTPError,
    ModelRequestTimeout,
    ModelTimeoutError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)

from careerwright.db import StoreUnavailableError

TRANSIENT_STATUSES = frozenset({429, 500, 503})
STORE_LABEL = "transient_store"  # the activity retries it within its own store budget


class FailureClass(StrEnum):
    ACCESS_REVOKED = "access_revoked"
    CREDENTIAL_UNAVAILABLE = "credential_unavailable"
    MODEL_NOT_PERMITTED = "model_not_permitted"
    BUDGET_EXCEEDED = "budget_exceeded"
    PROVIDER_AUTHENTICATION = "provider_authentication"
    PROVIDER_BILLING = "provider_billing"
    PROVIDER_PERMISSION = "provider_permission"
    PROVIDER_REQUEST_REJECTED = "provider_request_rejected"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    INVALID_MODEL_OUTPUT = "invalid_model_output"  # still invalid after the bounded repair
    MODEL_REFUSED = "model_refused"  # the provider's content filter refused to answer
    OUTPUT_TRUNCATED = "output_truncated"  # the output hit its token limit: never used
    # The call went past a bound its reservation assumed (more searches or input tokens than
    # it reserved for): its actual cost is booked and its output never used.
    BOUND_EXCEEDED = "bound_exceeded"
    APP_STORE_UNAVAILABLE = "app_store_unavailable"
    # An acquisition run whose every source failed, or was refused by policy (Task 7A): never
    # an empty success ("no vacancies"), and the attempts say which and why.
    RETRIEVAL_FAILED = "retrieval_failed"
    SOURCE_BLOCKED = "source_blocked"
    # A route solve whose rank stage reached its own limit before it finished (Task 13b): no
    # result claims ranks it lacks, so none is kept.
    RANK_LIMIT_REACHED = "rank_limit_reached"
    UNKNOWN_FAILURE = "unknown_failure"


_STATUS_FAILURES = {
    401: FailureClass.PROVIDER_AUTHENTICATION,
    402: FailureClass.PROVIDER_BILLING,
    403: FailureClass.PROVIDER_PERMISSION,
}


class OutputTruncatedError(Exception):
    """A response stopped at its token limit; raised before anything parses or repairs it."""


class BoundExceededError(Exception):
    """A completed call used more than its reservation assumed. Carries the bound's name."""

    def __init__(self, bound: str) -> None:
        super().__init__(f"bound exceeded ({bound})")
        self.bound = bound


class TransientProviderError(Exception):
    """Retryable provider failure. Carries a type-derived label only, never provider text."""

    def __init__(self, label: str) -> None:
        super().__init__(f"transient provider failure ({label})")
        self.label = label


class LabelledError(Exception):
    """Any other failure leaving a DBOS step: its classification label, never its message."""

    def __init__(self, label: str) -> None:
        super().__init__(f"step failed ({label})")
        self.label = label


@dataclass(frozen=True)
class Classified:
    """How an attempt failed, derived only from the exception's type and HTTP status."""

    label: str  # recorded as the attempt outcome
    failure: FailureClass | None  # None: transient, so the DBOS step retries


def terminal(failure: FailureClass) -> Classified:
    return Classified(failure.value, failure)


def classify_failure(error: BaseException) -> Classified:
    # Order matters: ModelTimeoutError is a ModelConnectionError, and every provider error is
    # a ModelAPIError; anything unrecognised is an unknown failure, named by class only.
    if isinstance(error, ModelHTTPError):
        if error.status_code in TRANSIENT_STATUSES:
            return Classified(f"transient_{error.status_code}", None)
        return terminal(
            _STATUS_FAILURES.get(error.status_code, FailureClass.PROVIDER_REQUEST_REJECTED)
        )
    if isinstance(error, ModelTimeoutError):
        return Classified("transient_timeout", None)
    if isinstance(error, ModelConnectionError):
        return Classified("transient_connection", None)
    if isinstance(error, ModelRequestTimeout):
        return Classified("transient_request_timeout", None)
    if isinstance(error, ContentFilterError):  # an UnexpectedModelBehavior: test it first
        return terminal(FailureClass.MODEL_REFUSED)
    if isinstance(error, OutputTruncatedError):
        return terminal(FailureClass.OUTPUT_TRUNCATED)
    if isinstance(error, BoundExceededError):
        return Classified(
            f"{FailureClass.BOUND_EXCEEDED.value}:{error.bound}", FailureClass.BOUND_EXCEEDED
        )
    if isinstance(error, UsageLimitExceeded | UnexpectedModelBehavior):
        return terminal(FailureClass.INVALID_MODEL_OUTPUT)
    if isinstance(error, StoreUnavailableError):
        return Classified(STORE_LABEL, None)
    return Classified(
        f"{FailureClass.UNKNOWN_FAILURE.value}:{type(error).__name__}", FailureClass.UNKNOWN_FAILURE
    )


def classify_exhausted(errors: Sequence[BaseException]) -> FailureClass:
    """The failure class once the step's retries are spent, from the last attempt's cause."""
    if not errors:
        return FailureClass.UNKNOWN_FAILURE
    if isinstance(errors[-1], TransientProviderError):
        return FailureClass.PROVIDER_UNAVAILABLE
    return FailureClass.UNKNOWN_FAILURE


def recorded_failure(label: str | None) -> FailureClass | None:
    """The terminal failure class an attempt's recorded outcome names, if it names one
    (`unknown_failure:<class>` included); transient and success labels name none."""
    try:
        return FailureClass((label or "").partition(":")[0])
    except ValueError:
        return None
