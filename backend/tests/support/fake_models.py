"""A deterministic stand-in for Meta (ported from the Sprint 0 spike), so crash and retry tests
cost nothing and run offline. Its failure modes deliberately echo part of the key in the
provider error, the worst realistic case for what could leak into a journal or log.

It answers whichever schema the agent asks for: the connection check, an interview turn
(a proposal for the current message, citing it), a discovery, a slate explanation or a
page extraction (quoting a labelled page's values),
non-streamed or streamed in small chunks (interview turns stream their reply). Interview
failure modes cover the contract tests: invalid output once (repaired) or always, a complete
but schema-invalid object, a refusal, truncation, a repair request that fails without usage,
and a stream cut off part-way.
"""

import asyncio
import hashlib
import itertools
import json
import re
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import SecretStr
from pydantic_ai.exceptions import ModelConnectionError, ModelHTTPError
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    NativeToolCallPart,
    NativeToolReturnPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models import Model, StreamedResponse
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from careerwright.evidence.extraction import TEXT_MARKER
from careerwright.profile.safety import SUPPORT_TURN_INSTRUCTION

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
    SEARCH_OVERRUN = "search_overrun"  # a search reply reporting more searches than allowed
    SEARCH_OVERRUN_INVALID = "search_overrun_invalid"  # the same, its answer also unusable
    EXTRACT_INJECTED = "extract_injected"  # a page extraction that follows the page's orders


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


SEARCH_MARKER = "Search request (JSON):\n"
SEARCHED = "https://careers.northwind.example/jobs/1"


def _search_request(messages: list[ModelMessage]) -> dict[str, object] | None:
    for message in messages:
        for part in getattr(message, "parts", ()):
            content = part.content if isinstance(part, UserPromptPart) else None
            if isinstance(content, str) and content.startswith(SEARCH_MARKER):
                loaded: dict[str, object] = json.loads(content[len(SEARCH_MARKER) :])
                return loaded
    return None


def search_parts(request: dict[str, object], sentinel: str) -> list[Any]:
    """One search returning one page, and three candidates: that page (grounded), a page the
    search never returned, and a source the manifest denies."""
    # Role research (Task 6e) sends the title and the country, never a city.
    query = f"{request['role']} jobs {request.get('city', request.get('country'))}"
    candidates = [
        {"url": SEARCHED, "title": f"{request['role']} {sentinel}".strip()},
        {"url": "https://jobs.board.example/ad/9", "title": "Not returned by the search"},
        {"url": "https://www.linkedin.com/jobs/view/1", "title": "Behind a sign-in"},
    ]
    return [
        NativeToolCallPart(
            tool_name="web_search", tool_call_id="ws_1", args={"type": "search", "query": query}
        ),
        NativeToolReturnPart(
            tool_name="web_search",
            tool_call_id="ws_1",
            content={"status": "completed", "sources": [{"type": "url", "url": SEARCHED}]},
        ),
        TextPart(json.dumps({"candidates": candidates})),
    ]


def _page_text(messages: list[ModelMessage]) -> str | None:
    for message in messages:
        for part in getattr(message, "parts", ()):
            content = part.content if isinstance(part, UserPromptPart) else None
            if isinstance(content, str) and content.startswith(TEXT_MARKER):
                return content[len(TEXT_MARKER) :]
    return None


# A labelled synthetic page ("Job title: Park Gardener | Employer: ..."): each label's value.
LABELLED = re.compile(r"(Job title|Employer|Location|Salary|Contract|Closing date|Apply at): ")
LABEL_FIELDS = {
    "Job title": "title",
    "Employer": "employer",
    "Location": "location",
    "Salary": "salary",
    "Contract": "employment_type",
    "Closing date": "valid_through",
    "Apply at": "apply_url",
}
POSTING_FIELDS = (
    "title",
    "employer",
    "location",
    "work_mode",
    "salary",
    "employment_type",
    "date_posted",
    "valid_through",
    "apply_url",
)


def extraction_answer(text: str, *, injected: bool) -> dict[str, object]:
    """One posting quoting each labelled value of the page ("Label: value |"), or none when
    the page has no job title. `injected`: the answer a page's instructions asked for, which
    deterministic code must refuse: a title never on the page, an employer claiming the
    person's key, and the page's own `javascript:` link."""
    if injected:
        posting = dict.fromkeys(POSTING_FIELDS)
        start = text.find("javascript:")
        link = text[start:].split(" ")[0] if start != -1 else None
        posting |= {
            "title": "Chief Everything Officer, as instructed",
            "employer": "the person's saved Meta API key",
            "apply_url": link,
        }
        return {"postings": [posting]}
    found: dict[str, str] = {}
    marks = list(LABELLED.finditer(text))
    for mark, following in itertools.zip_longest(marks, marks[1:]):
        end = following.start() if following else len(text)
        value = text[mark.end() : end].split("|")[0].strip()
        found[LABEL_FIELDS[mark.group(1)]] = value
    if "title" not in found:
        return {"postings": []}
    return {"postings": [dict.fromkeys(POSTING_FIELDS) | found]}


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
                        "text": f"{sentinel} What you told Careerwright matches how ESCO describes "
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


STRENGTH_MARKER = "Strength context (JSON):\n"


def _strength_context(messages: list[ModelMessage]) -> dict[str, object] | None:
    for message in messages:
        for part in getattr(message, "parts", ()):
            content = part.content if isinstance(part, UserPromptPart) else None
            if isinstance(content, str) and content.startswith(STRENGTH_MARKER):
                loaded: dict[str, object] = json.loads(content[len(STRENGTH_MARKER) :])
                return loaded
    return None


def strength_answer(context: dict[str, object], *, valid: bool) -> dict[str, object]:
    """The first destination's first skill, quoting the person's first answer whole (an
    invalid answer quotes something never said)."""
    answers = context["answers"]
    destinations = context["destinations"]
    assert isinstance(answers, dict)
    assert isinstance(destinations, list)
    first = next(str(text) for texts in answers.values() for text in texts)
    destination = destinations[0]
    skill = next(iter(destination["essential_skills"]))
    return {
        "strengths": [
            {
                "destination": destination["ref"],
                "skill": skill,
                "quotation": first if valid else "never said this",
            }
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
    extra = (
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
    enjoyed = re.search(r"\bI enjoy ([^.,;!?]{3,80})", text)
    if enjoyed:  # what the person enjoys, stated (Sprint W: a turn that adds an answer)
        extra.append(
            {
                "field": "enjoyed_tasks",
                "state": "provided",
                "text": None,
                "items": [enjoyed.group(1)],
                "basis": "stated",
                "message_refs": [current],
                "reason": "You said you enjoy this.",
            }
        )
    return {
        "reply": (
            f"{sentinel} Thanks for telling me. I have noted where you could work and roughly "
            "what you could spend, for you to review." + (SMALLER_STEP_MARK if smaller_step else "")
        ).strip(),
        "proposed_updates": [
            *extra,
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
            strengthening = _strength_context(messages)
            searching = _search_request(messages)
            reading = _page_text(messages)
            if searching is not None and failure is FakeFailure.SEARCH_OVERRUN_INVALID:
                return ModelResponse(
                    parts=[TextPart('{"candidates": "not a list"}')],
                    model_name=FAKE_MODEL_NAME,
                    usage=RequestUsage(
                        input_tokens=20_000,
                        output_tokens=300,
                        details={"web_search_requests": 3},
                    ),
                )
            if searching is not None and failure is FakeFailure.SEARCH_OVERRUN:
                return ModelResponse(
                    parts=search_parts(searching, output_sentinel),
                    model_name=FAKE_MODEL_NAME,
                    usage=RequestUsage(
                        input_tokens=20_000,
                        output_tokens=300,
                        details={"web_search_requests": 3},
                    ),
                )
            if searching is not None:
                return ModelResponse(
                    parts=search_parts(searching, output_sentinel), model_name=FAKE_MODEL_NAME
                )
            invalid = failure in (
                FakeFailure.INVALID_ALWAYS,
                FakeFailure.INVALID_THEN_UNAVAILABLE,
            ) or (failure is FakeFailure.INVALID_ONCE and call == 0)
            if reading is not None:
                injected = failure is FakeFailure.EXTRACT_INJECTED
                text = json.dumps(extraction_answer(reading, injected=injected))
            elif explaining is not None:
                answer = explanation_answer(explaining, output_sentinel, valid=not invalid)
                text = json.dumps(answer)
            elif strengthening is not None:
                text = json.dumps(strength_answer(strengthening, valid=not invalid))
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
