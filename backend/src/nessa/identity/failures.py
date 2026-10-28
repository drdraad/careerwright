"""Typed, message-free failure classification for the bounded model activity (ADR 0002).

Every exception is classified from its type and HTTP status alone and its message is
discarded, because provider errors can echo the key and ours can quote private input. A
transient failure becomes a label-only exception for the DBOS step, the single retry owner;
everything else is a terminal failure class recorded on the run.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from pydantic_ai.exceptions import (
    ModelConnectionError,
    ModelHTTPError,
    ModelRequestTimeout,
    ModelTimeoutError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)

from nessa.db import StoreUnavailableError

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
    INVALID_MODEL_OUTPUT = "invalid_model_output"
    APP_STORE_UNAVAILABLE = "app_store_unavailable"
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
