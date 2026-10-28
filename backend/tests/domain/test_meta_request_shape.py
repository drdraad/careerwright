"""Offline check of the exact request the connection check sends to Meta (no network).
Ported from the Sprint 0 spike; it drives the product's model factory and agent."""

import json
from typing import Any

import httpx2
import pytest
from pydantic import SecretStr
from pydantic_ai.exceptions import ModelHTTPError

from nessa.identity import connection_check
from nessa.identity.activity import connection_check_agent, run_connection_check
from nessa.identity.meta import meta_model


def captured_request() -> tuple[str, dict[str, Any], str]:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(
            401, json={"error": {"code": "invalid_api_key", "type": "authentication_error"}}
        )

    model = meta_model(
        "muse-spark-1.3-contributor",
        SecretStr("offline-placeholder-key"),
        max_output_tokens=connection_check.LIMITS.max_output_tokens,
        effort="minimal",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )
    with pytest.raises(ModelHTTPError):
        run_connection_check(connection_check_agent(model))
    [request] = requests
    return (
        f"{request.method} {request.url}",
        json.loads(request.content),
        request.headers["authorization"],
    )


def test_the_request_goes_to_meta_with_strict_native_json_schema_and_bounded_output() -> None:
    target, body, authorization = captured_request()

    assert target == "POST https://api.meta.ai/v1/responses"
    text_format = body["text"]["format"]
    assert (text_format["type"], text_format["strict"]) == ("json_schema", True)
    assert text_format["name"] == "ConnectionCheckResult"
    assert body["reasoning"] == {"effort": "minimal"}
    assert body["max_output_tokens"] == connection_check.LIMITS.max_output_tokens
    assert "tools" not in body
    assert authorization == "Bearer offline-placeholder-key"


def test_the_prompt_carries_no_workspace_data() -> None:
    _, body, _ = captured_request()

    assert "Synthetic test persona (not a real person)" in json.dumps(body)
