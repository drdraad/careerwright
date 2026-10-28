"""A deterministic stand-in for Meta (ported from the Sprint 0 spike), so crash and retry tests
cost nothing and run offline. Its failure modes deliberately echo part of the key in the
provider error, the worst realistic case for what could leak into a journal or log.

It answers whichever schema the agent asks for: the connection check, or an interview turn
(a proposal for the current message, citing it). Interview failure modes cover the
contract tests: invalid output once (repaired) or always, a refusal, and truncation.
"""

import hashlib
import itertools
import json
import time
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path

from pydantic import SecretStr
from pydantic_ai.exceptions import ModelConnectionError, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

FAKE_MODEL_NAME = "fake-function-model"
CONTEXT_MARKER = "Context (JSON):\n"


class FakeFailure(StrEnum):
    AUTH_ECHO = "auth_echo"
    RATE_LIMIT_ONCE = "rate_limit_once"
    ALWAYS_UNAVAILABLE = "always_unavailable"
    CONNECTION_ERROR = "connection_error"
    UNEXPECTED_ERROR = "unexpected_error"
    INCONSISTENT_USAGE = "inconsistent_usage"  # more cached than total input tokens
    INVALID_ONCE = "invalid_once"  # an interview output citing no message, then a valid one
    INVALID_ALWAYS = "invalid_always"
    REFUSAL = "refusal"  # the provider's content filter answers with a refusal
    TRUNCATED = "truncated"  # the output stops at its token limit, mid-JSON


def key_fingerprint(api_key: SecretStr | None) -> str:
    if api_key is None:
        return "no-key"
    return hashlib.sha256(api_key.get_secret_value().encode()).hexdigest()[:16]


def _context(messages: list[ModelMessage]) -> dict[str, object] | None:
    for message in messages:
        for part in getattr(message, "parts", ()):
            content = part.content if isinstance(part, UserPromptPart) else None
            if isinstance(content, str) and content.startswith(CONTEXT_MARKER):
                loaded: dict[str, object] = json.loads(content[len(CONTEXT_MARKER) :])
                return loaded
    return None


def interview_answer(
    context: dict[str, object], sentinel: str, *, valid: bool
) -> dict[str, object]:
    """A proposal for the current message: a stated city and an inferred spending limit."""
    current = str(context["current_message"])
    return {
        "reply": f"Thanks for telling me. {sentinel}".strip(),
        "proposed_updates": [
            {
                "field": "cities",
                "state": "provided",
                "text": None,
                "items": ["Leeds"],
                "basis": "stated",
                "message_refs": [current if valid else "m999"],
                "reason": "You said you could work in Leeds.",
            },
            {
                "field": "direct_spend_cap",
                "state": "provided",
                "text": "1500",
                "items": None,
                "basis": "inferred",
                "message_refs": [current],
                "reason": "You mentioned about 1,500 pounds.",
            },
        ],
        "next_question": "How many hours a week could you give to learning?",
        "missing_critical_fields": ["weekly_study_hours"],
        "ready_for_review": True,
    }


def fake_model_builder(
    *,
    delay_s: float = 0.0,
    failure: FakeFailure | None = None,
    output_sentinel: str = "",
    call_log: Path | None = None,
) -> Callable[[str, SecretStr | None], Model]:
    """`call_log`, if given, gets one line per request the moment it "reaches the provider"."""
    calls = itertools.count()

    def build(model_id: str, api_key: SecretStr | None) -> Model:
        echoed = api_key.get_secret_value()[:20] if api_key else ""

        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            call = next(calls)
            if call_log is not None:
                with call_log.open("a", encoding="utf-8") as log:
                    log.write(f"call {call}\n")
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
            if failure is FakeFailure.REFUSAL:
                return ModelResponse(
                    parts=[],
                    model_name=FAKE_MODEL_NAME,
                    finish_reason="content_filter",
                    provider_details={"refusal": f"I can't help with that {output_sentinel}"},
                )
            context = _context(messages)
            if context is not None:
                valid = not (
                    failure is FakeFailure.INVALID_ALWAYS
                    or (failure is FakeFailure.INVALID_ONCE and call == 0)
                )
                text = json.dumps(interview_answer(context, output_sentinel, valid=valid))
            else:
                title = f"Workforce Training Coordinator {output_sentinel}".strip()
                text = json.dumps(
                    {
                        "suggested_title": title,
                        # Which key the activity opened, without revealing it.
                        "reason": f"key fingerprint {key_fingerprint(api_key)}",
                    }
                )
            if failure is FakeFailure.TRUNCATED:
                return ModelResponse(
                    parts=[TextPart(text[: len(text) // 2])],
                    model_name=FAKE_MODEL_NAME,
                    finish_reason="length",
                )
            response = ModelResponse(parts=[TextPart(text)], model_name=FAKE_MODEL_NAME)
            if failure is FakeFailure.INCONSISTENT_USAGE:
                response.usage = RequestUsage(input_tokens=5, cache_read_tokens=9, output_tokens=7)
            return response

        return FunctionModel(respond, model_name=FAKE_MODEL_NAME)

    return build
