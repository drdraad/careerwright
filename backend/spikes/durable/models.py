"""Model builders for the activity: the real Meta provider, or a deterministic fake.

The fake stands in for Meta in crash/retry tests so they cost nothing and run offline. Its
failure modes deliberately echo part of the credential in the provider error body, the worst
realistic case for what could leak into a journal or log.
"""

import itertools
import json
import time
from collections.abc import Callable
from enum import StrEnum

from pydantic import SecretStr
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel

from spikes.meta.live_spike import SCHEMA_LIMITS, meta_model, model_settings

FAKE_MODEL_ID = "fake-function-model"
FAKE_TITLE = "Workforce Training Coordinator"

ModelBuilder = Callable[[SecretStr], Model]


class FakeFailure(StrEnum):
    AUTH_ECHO = "auth_echo"
    RATE_LIMIT_ONCE = "rate_limit_once"
    ALWAYS_UNAVAILABLE = "always_unavailable"


def _prompt_text(messages: list[ModelMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                    return part.content
    raise ValueError("no user prompt")


def fake_model_builder(*, delay_s: float = 0.0, failure: FakeFailure | None = None) -> ModelBuilder:
    calls = itertools.count()

    def build(api_key: SecretStr) -> Model:
        echoed = api_key.get_secret_value()[:20]

        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            call = next(calls)
            time.sleep(delay_s)
            if failure is FakeFailure.AUTH_ECHO:
                body = {"code": "invalid_api_key", "message": f"Incorrect API key {echoed}..."}
                raise ModelHTTPError(
                    401, FAKE_MODEL_ID, body, provider_error_code="invalid_api_key"
                )
            if failure is FakeFailure.RATE_LIMIT_ONCE and call == 0:
                body = {"code": "rate_limit_exceeded", "message": f"Slow down, key {echoed}"}
                raise ModelHTTPError(429, FAKE_MODEL_ID, body, provider_error_code="rate_limit")
            if failure is FakeFailure.ALWAYS_UNAVAILABLE:
                body = {"code": "backend_unavailable", "message": f"Unavailable for {echoed}"}
                raise ModelHTTPError(503, FAKE_MODEL_ID, body, provider_error_code="unavailable")
            quote = _prompt_text(messages).splitlines()[0]
            answer = json.dumps({"proposed_title": FAKE_TITLE, "evidence_quote": quote})
            return ModelResponse(parts=[TextPart(answer)], model_name=FAKE_MODEL_ID)

        return FunctionModel(respond, model_name=FAKE_MODEL_ID)

    return build


def meta_model_builder(model_id: str) -> ModelBuilder:
    def build(api_key: SecretStr) -> Model:
        return meta_model(
            model_id,
            api_key.get_secret_value(),
            settings=model_settings(SCHEMA_LIMITS, effort="minimal"),
        )

    return build
