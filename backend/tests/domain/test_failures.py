"""Failures are classified from exception type and HTTP status alone; the message is discarded
(ADR 0002 decision 6). Ported from the Sprint 0 spike."""

import pytest
from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelConnectionError,
    ModelHTTPError,
    ModelRequestTimeout,
    ModelTimeoutError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)

from careerwright.db import StoreUnavailableError
from careerwright.identity.failures import (
    Classified,
    FailureClass,
    TransientProviderError,
    classify_exhausted,
    classify_failure,
    recorded_failure,
)

KEY_LIKE_TEXT = "sk-spike-0123456789abcdef"


@pytest.mark.req("ARC1-07")
@pytest.mark.parametrize("status", [429, 500, 503])
def test_retryable_http_statuses_are_transient(status: int) -> None:
    error = ModelHTTPError(status, "m", {"message": KEY_LIKE_TEXT})

    assert classify_failure(error) == Classified(f"transient_{status}", None)


@pytest.mark.req("ARC1-07")
@pytest.mark.parametrize(
    ("status", "failure"),
    [
        (401, FailureClass.PROVIDER_AUTHENTICATION),
        (402, FailureClass.PROVIDER_BILLING),
        (403, FailureClass.PROVIDER_PERMISSION),
        (400, FailureClass.PROVIDER_REQUEST_REJECTED),
        (404, FailureClass.PROVIDER_REQUEST_REJECTED),
        (504, FailureClass.PROVIDER_REQUEST_REJECTED),
    ],
)
def test_terminal_http_statuses_map_to_typed_failures(status: int, failure: FailureClass) -> None:
    error = ModelHTTPError(status, "m", {"message": KEY_LIKE_TEXT})

    assert classify_failure(error) == Classified(failure.value, failure)


def test_connection_failure_and_timeouts_are_transient() -> None:
    assert classify_failure(
        ModelConnectionError("m", f"reset ({KEY_LIKE_TEXT})", phase="read")
    ) == Classified("transient_connection", None)
    assert classify_failure(
        ModelTimeoutError("m", f"timed out ({KEY_LIKE_TEXT})", phase="read")
    ) == Classified("transient_timeout", None)
    assert classify_failure(ModelRequestTimeout("m", 120.0)) == Classified(
        "transient_request_timeout", None
    )


@pytest.mark.parametrize(
    "error",
    [UsageLimitExceeded(f"second request {KEY_LIKE_TEXT}"), UnexpectedModelBehavior(KEY_LIKE_TEXT)],
)
def test_unusable_model_output_is_invalid_model_output(error: Exception) -> None:
    assert classify_failure(error) == Classified(
        FailureClass.INVALID_MODEL_OUTPUT.value, FailureClass.INVALID_MODEL_OUTPUT
    )


@pytest.mark.req("DUR-08")
def test_a_store_outage_is_transient_so_the_activity_retries_it() -> None:
    assert classify_failure(StoreUnavailableError()) == Classified("transient_store", None)


@pytest.mark.parametrize(
    "error",
    [RuntimeError(f"boom {KEY_LIKE_TEXT}"), ModelAPIError("m", f"stream error {KEY_LIKE_TEXT}")],
)
def test_anything_else_is_unknown_failure_labelled_by_class_only(error: Exception) -> None:
    classified = classify_failure(error)

    assert classified == Classified(
        f"unknown_failure:{type(error).__name__}", FailureClass.UNKNOWN_FAILURE
    )
    assert KEY_LIKE_TEXT not in classified.label


@pytest.mark.req("ARC1-07")
def test_exhausted_retries_name_what_was_unavailable_never_success() -> None:
    # Only provider failures reach the step's retries; the activity rides out store outages.
    assert classify_exhausted([TransientProviderError("transient_503")]) is (
        FailureClass.PROVIDER_UNAVAILABLE
    )
    assert classify_exhausted([]) is FailureClass.UNKNOWN_FAILURE


def test_transient_errors_carry_only_their_label() -> None:
    assert (
        str(TransientProviderError("transient_503")) == "transient provider failure (transient_503)"
    )


@pytest.mark.req("DUR-02")
@pytest.mark.parametrize(
    ("label", "failure"),
    [
        ("provider_authentication", FailureClass.PROVIDER_AUTHENTICATION),
        ("budget_exceeded", FailureClass.BUDGET_EXCEEDED),
        ("unknown_failure:ValueError", FailureClass.UNKNOWN_FAILURE),
        ("transient_429", None),
        ("transient_store", None),
        ("interrupted", None),
        ("succeeded", None),
        ("reused_accepted", None),
        ("reused_failure", None),
        (None, None),
    ],
)
def test_only_terminal_attempt_outcomes_name_a_recorded_failure(
    label: str | None, failure: FailureClass | None
) -> None:
    assert recorded_failure(label) is failure
