"""Offline check of the exact request the qualification agent sends to Meta (no network)."""

import asyncio
import json
from typing import Any

import httpx2
import pytest
from openai import AsyncOpenAI
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.meta import MetaProvider

from spikes.meta.live_spike import META_BASE_URL, SCHEMA_LIMITS, SEARCH_LIMITS, qualification_agent


def captured_request(*, search: bool) -> tuple[str, dict[str, Any]]:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(
            401, json={"error": {"code": "invalid_api_key", "type": "authentication_error"}}
        )

    client = AsyncOpenAI(
        base_url=META_BASE_URL,
        api_key="offline-placeholder",
        max_retries=0,
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )
    model = OpenAIResponsesModel(
        "muse-spark-1.3-contributor", provider=MetaProvider(openai_client=client)
    )
    with pytest.raises(ModelHTTPError):
        asyncio.run(qualification_agent(model, search=search).run("synthetic prompt"))
    [request] = requests
    return f"{request.method} {request.url}", json.loads(request.content)


def test_schema_request_uses_strict_native_json_schema_and_bounded_output() -> None:
    target, body = captured_request(search=False)

    assert target == "POST https://api.meta.ai/v1/responses"
    text_format = body["text"]["format"]
    assert (text_format["type"], text_format["strict"]) == ("json_schema", True)
    assert text_format["name"] == "CareerSuggestion"
    assert body["reasoning"] == {"effort": "minimal"}
    assert body["max_output_tokens"] == SCHEMA_LIMITS.max_output_tokens
    assert "tools" not in body


def test_search_request_adds_only_metas_native_web_search_with_auto_tool_choice() -> None:
    _, body = captured_request(search=True)

    assert body["text"]["format"]["name"] == "SearchFindings"
    assert body["tools"] == [{"type": "web_search", "search_context_size": "low"}]
    assert body["tool_choice"] == "auto"  # Meta accepts no forced tool choice
    assert body["reasoning"] == {"effort": "low"}
    assert body["max_output_tokens"] == SEARCH_LIMITS.max_output_tokens
