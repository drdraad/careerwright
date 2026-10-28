"""A deterministic stand-in for Meta (ported from the Sprint 0 spike), so crash and retry tests
cost nothing and run offline. Its failure modes deliberately echo part of the key in the
provider error, the worst realistic case for what could leak into a journal or log.

It answers whichever schema the agent asks for: the connection check, an interview turn
(a proposal for the current message, citing it), a discovery or a slate explanation,
non-streamed or streamed in small chunks (interview turns stream their reply). Interview
failure modes cover the contract tests: invalid output once (repaired) or always, a complete
but schema-invalid object, a refusal, truncation, a repair request that fails without usage,
and a stream cut off part-way.
"""

import asyncio
import hashlib
import itertools
import json
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import SecretStr
from pydantic_ai.exceptions import ModelConnectionError, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import Model, StreamedResponse
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from nessa.profile.safety import SUPPORT_TURN_INSTRUCTION

FAKE_MODEL_NAME = "fake-function-model"
CONTEXT_MARKER = "Context (JSON):\n"
STREAM_CHUNK = 24  # characters per streamed delta
PROPOSALS_KEY = '"proposed_updates"'
PAUSE_S = 4.0  # PAUSE_AFTER_REPLY: long enough for a test to read the stored partial
SMALLER_STEP_MARK = " One small step at a time."  # the reply's end under the instruction


class FakeFailure(StrEnum):
    AUTH_ECHO = "auth_echo"
    RATE_LIMIT_ONCE = "rate_limit_once"
    ALWAYS_UNAVAILABLE = "always_unavailable"
    CONNECTION_ERROR = "connection_error"
    UNEXPECTED_ERROR = "unexpected_error"
    INCONSISTENT_USAGE = "inconsistent_usage"  # more cached than total input tokens
    INVALID_ONCE = "invalid_once"  # an interview output citing no message, then a valid one
    INVALID_ALWAYS = "invalid_always"
    SCHEMA_INVALID_ALWAYS = "schema_invalid_always"  # complete JSON, wrong type for a field
    INVALID_THEN_UNAVAILABLE = "invalid_then_unavailable"  # every repair request gets a 503
    REFUSAL = "refusal"  # the provider's content filter answers with a refusal
    TRUNCATED = "truncated"  # the output stops at its token limit, mid-JSON
    CUT_MID_STREAM = "cut_mid_stream"  # the stream breaks after part of the reply
    PAUSE_AFTER_REPLY = "pause_after_reply"  # the reply streams, then a pause, then the rest


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


DISCOVERY_MARKER = "Discovery context (JSON):\n"


def _discovery_context(messages: list[ModelMessage]) -> dict[str, object] | None:
    for message in messages:
        for part in getattr(message, "parts", ()):
            content = part.content if isinstance(part, UserPromptPart) else None
            if isinstance(content, str) and content.startswith(DISCOVERY_MARKER):
                loaded: dict[str, object] = json.loads(content[len(DISCOVERY_MARKER) :])
                return loaded
    return None


def discovery_answer(
    context: dict[str, object], sentinel: str, *, valid: bool
) -> dict[str, object]:
    """Every answer text as a query (an invalid answer cites a text never given), and one
    title hypothesis ESCO cannot hold, carrying the sentinel."""
    answers = context["answers"]
    assert isinstance(answers, list)
    texts = [str(a["text"]) for a in answers if 3 <= len(str(a["text"])) <= 80][:8]
    return {
        "queries": [
            {
                "text": text,
                "channel": "tasks",
                "based_on": [text if valid else "something never said"],
            }
            for text in texts
        ],
        "hypotheses": [{"title": f"{sentinel} orbital gardener".strip(), "based_on": texts[:1]}],
    }


EXPLANATION_MARKER = "Explanation context (JSON):\n"


def _explanation_context(messages: list[ModelMessage]) -> dict[str, object] | None:
    for message in messages:
        for part in getattr(message, "parts", ()):
            content = part.content if isinstance(part, UserPromptPart) else None
            if isinstance(content, str) and content.startswith(EXPLANATION_MARKER):
                loaded: dict[str, object] = json.loads(content[len(EXPLANATION_MARKER) :])
                return loaded
    return None


def explanation_answer(
    context: dict[str, object], sentinel: str, *, valid: bool
) -> dict[str, object]:
    """One claim per occupation carrying the sentinel, quoting the person's first answer
    (an invalid answer quotes something never said) and the occupation's title."""
    answers = context["answers"]
    occupations = context["occupations"]
    assert isinstance(answers, dict)
    assert isinstance(occupations, list)
    first = next(str(text) for texts in answers.values() for text in texts)
    return {
        "explanations": [
            {
                "occupation": occupation["ref"],
                "claims": [
                    {
                        "text": f"{sentinel} What you told Nessa matches how ESCO describes "
                        "this work.".strip(),
                        "quotes": [
                            {"source": "answer", "text": first if valid else "never said this"},
                            {"source": "esco", "text": occupation["title"]},
                        ],
                    }
                ],
            }
            for occupation in occupations
        ]
    }


def interview_answer(
    context: dict[str, object], sentinel: str, *, valid: bool, smaller_step: bool = False
) -> dict[str, object]:
    """A proposal for the current message: a stated city and an inferred spending limit.
    When the instructions carry the smaller-step instruction (`smaller_step`), the reply
    ends with `SMALLER_STEP_MARK`, so a test can see the instruction arrived; the next
    question is kept, as a model ignoring the instruction would, for the server to drop.

    The reply starts with `sentinel`, so even the first streamed pieces of it carry the
    sentinel into the partial store, where leak scans must find it sealed."""
    current = str(context["current_message"])
    messages = context.get("messages")
    text = (
        next((str(m["text"]) for m in messages if m["ref"] == current), "")
        if isinstance(messages, list)
        else ""
    )
    salary = (
        [
            {
                "field": "minimum_salary",
                "state": "provided",
                "text": "26000 per year",
                "items": None,
                "basis": "stated",
                "message_refs": [current],
                "reason": "You gave the least you would earn.",
            }
        ]
        if "26,000 a year" in text
        else []
    )
    return {
        "reply": (
            f"{sentinel} Thanks for telling me. I have noted where you could work and roughly "
            "what you could spend, for you to review." + (SMALLER_STEP_MARK if smaller_step else "")
        ).strip(),
        "proposed_updates": [
            *salary,
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


@dataclass
class _Ending:
    """How the response being streamed ends: what a provider reports after its last delta."""

    finish_reason: Any = None
    provider_details: dict[str, Any] | None = None
    break_after: int | None = None  # deltas sent before the connection breaks
    pause_after_reply: bool = False  # PAUSE_S between the reply and the proposals


class _StreamingFunctionModel(FunctionModel):
    """A `FunctionModel` whose streamed responses can end the way a provider's do: with a
    finish reason, provider details or a broken connection."""

    def __init__(self, respond: Callable[..., ModelResponse], ending: _Ending) -> None:
        self._respond = respond
        self._ending = ending
        super().__init__(respond, stream_function=self._stream, model_name=FAKE_MODEL_NAME)

    async def _stream(self, messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str]:
        response = self._respond(messages, info)  # raises for request-level failures
        self._ending.finish_reason = response.finish_reason
        self._ending.provider_details = response.provider_details
        text = "".join(p.content for p in response.parts if isinstance(p, TextPart))
        split = text.find(PROPOSALS_KEY) if self._ending.pause_after_reply else -1
        parts = [text[:split], text[split:]] if split > 0 else [text]
        index = 0
        for number, part in enumerate(parts):
            if number:
                await asyncio.sleep(PAUSE_S)  # the model is still working on the proposals
            chunks = [part[i : i + STREAM_CHUNK] for i in range(0, len(part), STREAM_CHUNK)]
            for chunk in chunks or [""]:
                if self._ending.break_after is not None and index == self._ending.break_after:
                    raise ModelConnectionError(FAKE_MODEL_NAME, "stream broken", phase="read")
                index += 1
                yield chunk

    @asynccontextmanager
    async def request_stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[StreamedResponse]:
        async with super().request_stream(*args, **kwargs) as streamed:
            # The stream function has started (its first item is peeked), so the ending is set.
            streamed.finish_reason = self._ending.finish_reason
            streamed.provider_details = self._ending.provider_details
            yield streamed


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
        ending = _Ending()

        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            call = next(calls)
            if call_log is not None:
                with call_log.open("a", encoding="utf-8") as log:
                    log.write(f"call {call}\n")
            time.sleep(delay_s)
            ending.break_after = None
            ending.pause_after_reply = failure is FakeFailure.PAUSE_AFTER_REPLY
            if failure is FakeFailure.AUTH_ECHO:
                body = {"code": "invalid_api_key", "message": f"Incorrect API key {echoed}..."}
                raise ModelHTTPError(401, model_id, body)
            if failure is FakeFailure.RATE_LIMIT_ONCE and call == 0:
                raise ModelHTTPError(429, model_id, {"message": f"Slow down, key {echoed}"})
            if failure is FakeFailure.ALWAYS_UNAVAILABLE or (
                failure is FakeFailure.INVALID_THEN_UNAVAILABLE and call % 2 == 1
            ):
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
            found = _discovery_context(messages)
            explaining = _explanation_context(messages)
            invalid = failure in (
                FakeFailure.INVALID_ALWAYS,
                FakeFailure.INVALID_THEN_UNAVAILABLE,
            ) or (failure is FakeFailure.INVALID_ONCE and call == 0)
            if explaining is not None:
                answer = explanation_answer(explaining, output_sentinel, valid=not invalid)
                text = json.dumps(answer)
            elif found is not None:
                text = json.dumps(discovery_answer(found, output_sentinel, valid=not invalid))
            elif context is not None:
                valid = not (
                    failure in (FakeFailure.INVALID_ALWAYS, FakeFailure.INVALID_THEN_UNAVAILABLE)
                    or (failure is FakeFailure.INVALID_ONCE and call == 0)
                )
                smaller_step = SUPPORT_TURN_INSTRUCTION in (info.instructions or "")
                answer = interview_answer(
                    context, output_sentinel, valid=valid, smaller_step=smaller_step
                )
                if failure is FakeFailure.SCHEMA_INVALID_ALWAYS:
                    answer["ready_for_review"] = "yes"  # complete JSON, wrong type
                    del answer["missing_critical_fields"]
                if failure is FakeFailure.CUT_MID_STREAM:
                    ending.break_after = 3
                text = json.dumps(answer)
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

        return _StreamingFunctionModel(respond, ending)

    return build
