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

from spikes.durable.workflow import Classified, FailureClass, classify_failure

KEY_LIKE_TEXT = "sk-spike-0123456789abcdef"


@pytest.mark.parametrize("status", [429, 500, 503])
def test_retryable_http_statuses_are_transient(status: int) -> None:
    error = ModelHTTPError(status, "m", {"message": KEY_LIKE_TEXT})

    assert classify_failure(error) == Classified(f"transient_{status}", None)


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


def test_connection_failure_is_transient() -> None:
    error = ModelConnectionError("m", f"connection reset ({KEY_LIKE_TEXT})", phase="read")

    assert classify_failure(error) == Classified("transient_connection", None)


def test_transport_timeout_is_transient() -> None:
    error = ModelTimeoutError("m", f"timed out ({KEY_LIKE_TEXT})", phase="read")

    assert classify_failure(error) == Classified("transient_timeout", None)


def test_request_deadline_is_transient() -> None:
    assert classify_failure(ModelRequestTimeout("m", 120.0)) == Classified(
        "transient_request_timeout", None
    )


@pytest.mark.parametrize(
    "error",
    [
        UsageLimitExceeded(f"needed a second request {KEY_LIKE_TEXT}"),
        UnexpectedModelBehavior(KEY_LIKE_TEXT),
    ],
)
def test_unusable_model_output_is_invalid_model_output(error: Exception) -> None:
    assert classify_failure(error) == Classified(
        FailureClass.INVALID_MODEL_OUTPUT.value, FailureClass.INVALID_MODEL_OUTPUT
    )


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
