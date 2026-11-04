"""The interview turn as a run task, and the fixture interviewer as a model (adapter).

The task runs one Pydantic AI agent on whatever model the worker built for the run: Meta's
native provider for live workspaces, or the fixture interviewer for demo workspaces. Both
answer the same strict JSON schema (`NativeOutput`), and both outputs pass the same
deterministic check (`interview.check_turn`). A failed check is sent back once as a repair
request with the problems listed. On the final reply, one malformed optional change may
be dropped if the rest passes the full check; otherwise failure ends the run
`invalid_model_output`. The repair is the agent's output-retry budget, the only retry owner
for invalid output; the DBOS step retries only transient provider failures (ADR 0002
decision 7). A response cut off at its token limit ends the run at once
(`TruncationGuard`): never repaired.

The reply streams (spec section 4: stream natural conversation, commit only after complete
validation). `ReplyStream` reads the `reply` text out of the JSON as it arrives and hands it
to the activity's partial-reply sink, saying when it has ended; the proposals are never
streamed, and nothing streamed is a proposal. A repair request streams its reply afresh.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pydantic_core
from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import (
    AgentStreamEvent,
    ModelMessage,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    UserPromptPart,
)
from pydantic_ai.models import Model, ModelRequestContext
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

from careerwright.identity.activity import PartialSink, RepairBound, RunTask, TruncationGuard
from careerwright.identity.model_registry import FIXTURE_MODEL_ID, ModelMode
from careerwright.profile import interview
from careerwright.profile.document import FIELD_SPECS
from careerwright.profile.fixture_interviewer import fixture_turn
from careerwright.profile.interview import (
    CONTEXT_MARKER,
    MAX_OUTPUT_TOKENS,
    MAX_REQUESTS,
    InterviewProposal,
    InterviewTurnOutput,
    PromptContext,
    ProposalOrigin,
    TurnInput,
    render_prompt,
)
from careerwright.profile.safety import SUPPORT_TURN_INSTRUCTION

FIXTURE_STREAM_CHUNK = 32  # characters per delta the fixture interviewer streams


def _reply_so_far(text: str) -> tuple[str | None, bool]:
    """The `reply` in a prefix of the output JSON, and whether its string has closed."""
    try:
        partial = pydantic_core.from_json(text, allow_partial="trailing-strings")
        closed = pydantic_core.from_json(text, allow_partial=True)  # no unfinished strings
    except ValueError:
        return None, False  # not yet a JSON prefix that parses
    reply = partial.get("reply") if isinstance(partial, dict) else None
    if not isinstance(reply, str) or not reply:
        return None, False
    return reply, isinstance(closed, dict) and "reply" in closed


class ReplyStream(AbstractCapability[Any]):
    """Hands the reply so far to `sink` on every text event of the streamed JSON, so the
    sink can write the newest text when it is due, and once more with `complete=True` the
    moment the reply's string closes (the proposals may stream for a while after it)."""

    def __init__(self, sink: PartialSink) -> None:
        self._sink = sink
        self._text = ""
        self._ended = False

    async def before_model_request(
        self, ctx: RunContext[Any], request_context: ModelRequestContext
    ) -> ModelRequestContext:
        self._text, self._ended = "", False  # a repair request answers with a new reply
        return request_context

    async def on_event(self, ctx: RunContext[Any], *, event: AgentStreamEvent) -> None:
        if self._ended:
            return
        if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
            self._text = event.part.content
        elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
            self._text += event.delta.content_delta
        else:
            return
        reply, ended = _reply_so_far(self._text)
        if reply is not None:
            self._ended = ended
            self._sink(reply, complete=ended)


def run_interview_turn(
    model: Model, mode: ModelMode, raw_input: bytes | None, on_reply: PartialSink
) -> InterviewProposal:
    if raw_input is None:
        raise ValueError("an interview turn has a sealed input")
    context = TurnInput.model_validate_json(raw_input)
    origin = ProposalOrigin.FIXTURE if mode is ModelMode.FIXTURE else ProposalOrigin.MODEL
    agent = Agent(
        model,
        output_type=NativeOutput(InterviewTurnOutput),
        instructions=interview.instructions(context),
        retries={"tools": 0, "output": MAX_REQUESTS - 1},
        capabilities=[
            TruncationGuard(),
            RepairBound(interview.REPAIR_ALLOWANCE_TOKENS),
            ReplyStream(on_reply),
        ],
    )
    accepted: list[InterviewProposal] = []

    @agent.output_validator
    def _check(ctx: RunContext[None], output: InterviewTurnOutput) -> InterviewTurnOutput:
        proposal, problems = interview.check_turn(output, context, origin)
        if proposal is None and ctx.retry == MAX_REQUESTS - 1:
            # Drop one malformed optional claim only after the normal repair has failed.
            for index, update in enumerate(output.proposed_updates):
                if FIELD_SPECS[update.field.value].hard_constraint or not all(
                    problem.startswith(f"{update.field.value}:") for problem in problems
                ):
                    continue
                remaining = output.proposed_updates[:index] + output.proposed_updates[index + 1 :]
                candidate = output.model_copy(update={"proposed_updates": remaining})
                proposal, _ = interview.check_turn(candidate, context, origin)
                if proposal is not None:
                    break
        if proposal is None:
            raise ModelRetry(
                "The JSON object does not pass validation. Answer again with the whole object, "
                "fixing these problems:\n- " + "\n- ".join(problems)
            )
        accepted.append(proposal)
        return output

    asyncio.run(
        agent.run(
            render_prompt(context),
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
            model_settings={"max_tokens": MAX_OUTPUT_TOKENS},
        )
    )
    return accepted[-1]


INTERVIEW_TURN_TASK = RunTask(
    call=run_interview_turn,
    worst_case_nano_usd=interview.worst_case_nano_usd,
    has_input=True,
)


def _prompt_context(messages: list[ModelMessage]) -> PromptContext:
    """The fixture reads exactly the prompt a live model receives."""
    for message in reversed(messages):
        for part in getattr(message, "parts", ()):
            if (
                isinstance(part, UserPromptPart)
                and isinstance(part.content, str)
                and part.content.startswith(CONTEXT_MARKER)
            ):
                return PromptContext.model_validate_json(part.content[len(CONTEXT_MARKER) :])
    raise ValueError("the prompt has no context")


def _fixture_json(messages: list[ModelMessage], info: AgentInfo) -> str:
    smaller_step = SUPPORT_TURN_INSTRUCTION in (info.instructions or "")
    return fixture_turn(_prompt_context(messages), smaller_step=smaller_step).model_dump_json()


def fixture_interviewer_model() -> Model:
    """The deterministic demo interviewer behind Pydantic AI's model interface: no network,
    no key; it answers from the prompt's context with `fixture_turn`, following the
    smaller-step instruction when the turn's instructions carry it, whole or streamed in
    pieces like a provider."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        text = _fixture_json(messages, info)
        return ModelResponse(parts=[TextPart(text)], model_name=FIXTURE_MODEL_ID)

    async def stream(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str]:
        text = _fixture_json(messages, info)
        for start in range(0, len(text), FIXTURE_STREAM_CHUNK):
            yield text[start : start + FIXTURE_STREAM_CHUNK]

    return FunctionModel(respond, stream_function=stream, model_name=FIXTURE_MODEL_ID)
