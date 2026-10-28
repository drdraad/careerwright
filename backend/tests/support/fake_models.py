"""A deterministic stand-in for Meta (ported from the Sprint 0 spike), so crash and retry tests
cost nothing and run offline. Its failure modes deliberately echo part of the key in the
provider error, the worst realistic case for what could leak into a journal or log."""

import hashlib
import itertools
import json
import time
from collections.abc import Callable
from enum import StrEnum

from pydantic import SecretStr
from pydantic_ai.exceptions import ModelConnectionError, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel

FAKE_MODEL_NAME = "fake-function-model"


class FakeFailure(StrEnum):
    AUTH_ECHO = "auth_echo"
    RATE_LIMIT_ONCE = "rate_limit_once"
    ALWAYS_UNAVAILABLE = "always_unavailable"
    CONNECTION_ERROR = "connection_error"
    UNEXPECTED_ERROR = "unexpected_error"


def key_fingerprint(api_key: SecretStr) -> str:
    return hashlib.sha256(api_key.get_secret_value().encode()).hexdigest()[:16]


def fake_model_builder(
    *, delay_s: float = 0.0, failure: FakeFailure | None = None, output_sentinel: str = ""
) -> Callable[[str, SecretStr], Model]:
    calls = itertools.count()

    def build(model_id: str, api_key: SecretStr) -> Model:
        echoed = api_key.get_secret_value()[:20]

        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            call = next(calls)
            time.sleep(delay_s)
            if failure is FakeFailure.AUTH_ECHO:
                body = {"code": "invalid_api_key", "message": f"Incorrect API key {echoed}..."}
                raise ModelHTTPError(401, model_id, body)
            if failure is FakeFailure.RATE_LIMIT_ONCE and call == 0:
                raise ModelHTTPError(429, model_id, {"message": f"Slow down, key {echoed}"})
            if failure is FakeFailure.ALWAYS_UNAVAILABLE:
                raise ModelHTTPError(503, model_id, {"message": f"Unavailable for {echoed}"})
            if failure is FakeFailure.CONNECTION_ERROR:
                raise ModelConnectionError(model_id, f"reset talking as {echoed}", phase="read")
            if failure is FakeFailure.UNEXPECTED_ERROR:
                raise RuntimeError(f"bug handling {echoed} for {output_sentinel}")
            answer = {
                "suggested_title": f"Workforce Training Coordinator {output_sentinel}".strip(),
                # Which key the activity opened, without revealing it.
                "reason": f"key fingerprint {key_fingerprint(api_key)}",
            }
            return ModelResponse(parts=[TextPart(json.dumps(answer))], model_name=FAKE_MODEL_NAME)

        return FunctionModel(respond, model_name=FAKE_MODEL_NAME)

    return build
