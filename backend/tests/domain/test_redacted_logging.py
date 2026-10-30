"""Logs hold record IDs and error classes; secrets and exception text never reach them (SEC-04)."""

import io
import json
import logging
from collections.abc import Iterator

import pytest

from careerwright.logs import JsonFormatter, register_secret

JWT = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1aWQtYWRhIn0."
SECRET = "pg-password-6f0c1a9e"


@pytest.fixture
def capture() -> Iterator[tuple[logging.Logger, io.StringIO]]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter(service="test"))
    logger = logging.getLogger("careerwright.test.redaction")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    yield logger, stream
    logger.removeHandler(handler)


def records(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


@pytest.mark.req("SEC-04")
def test_tokens_bearer_headers_and_url_passwords_are_scrubbed(
    capture: tuple[logging.Logger, io.StringIO],
) -> None:
    logger, stream = capture

    logger.info(
        "auth header Bearer %s for postgresql://careerwright_api:hunter22@postgres/app", JWT
    )

    [line] = records(stream)
    assert JWT not in stream.getvalue()
    assert "hunter22" not in stream.getvalue()
    assert "Bearer [redacted]" in str(line["msg"])
    assert "careerwright_api:[redacted]@postgres" in str(line["msg"])


@pytest.mark.req("SEC-04")
def test_registered_process_secrets_are_scrubbed(
    capture: tuple[logging.Logger, io.StringIO],
) -> None:
    logger, stream = capture
    register_secret(SECRET)

    logger.warning("connecting with %s", SECRET)

    assert SECRET not in stream.getvalue()
    assert "[redacted]" in stream.getvalue()


@pytest.mark.req("SEC-04")
def test_exceptions_are_logged_by_class_and_frames_without_their_message(
    capture: tuple[logging.Logger, io.StringIO],
) -> None:
    logger, stream = capture

    def fail() -> None:
        raise RuntimeError("provider echoed sk-live-0123456789abcdef and the CV text")

    try:
        fail()
    except RuntimeError:
        logger.exception("request failed")

    [line] = records(stream)
    assert "sk-live-0123456789abcdef" not in stream.getvalue()
    assert line["error_class"] == "RuntimeError"
    assert "in fail" in str(line["stack"])


def test_extra_identifiers_are_kept_as_fields(capture: tuple[logging.Logger, io.StringIO]) -> None:
    logger, stream = capture

    logger.info("run finished", extra={"run_id": "r-1", "workspace_id": "w-1", "outcome": "x"})

    [line] = records(stream)
    assert (line["run_id"], line["workspace_id"], line["outcome"]) == ("r-1", "w-1", "x")
    assert line["service"] == "test"
