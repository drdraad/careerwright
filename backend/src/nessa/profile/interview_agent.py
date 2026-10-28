"""The interview turn as a run task, and the fixture interviewer as a model (adapter).

The task runs one Pydantic AI agent on whatever model the worker built for the run: Meta's
native provider for live workspaces, or the fixture interviewer for demo workspaces. Both
answer the same strict JSON schema (`NativeOutput`), and both outputs pass the same
deterministic check (`interview.check_turn`). A failed check is sent back once as a repair
request with the problems listed; a second failure ends the run `invalid_model_output`.
That repair is the agent's output-retry budget, the only retry owner for invalid output;
the DBOS step retries only transient provider failures (ADR 0002 decision 7).
"""

import asyncio

from pydantic_ai import Agent, ModelRetry, NativeOutput
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

from nessa.identity.activity import RunTask
from nessa.identity.model_registry import FIXTURE_MODEL_ID, ModelMode
from nessa.profile import interview
from nessa.profile.fixture_interviewer import fixture_turn
from nessa.profile.interview import (
    CONTEXT_MARKER,
    INSTRUCTIONS,
    MAX_OUTPUT_TOKENS,
    MAX_REQUESTS,
    InterviewProposal,
    InterviewTurnOutput,
    PromptContext,
    ProposalOrigin,
    TurnInput,
    render_prompt,
)


def run_interview_turn(model: Model, mode: ModelMode, raw_input: bytes | None) -> InterviewProposal:
    if raw_input is None:
        raise ValueError("an interview turn has a sealed input")
    context = TurnInput.model_validate_json(raw_input)
    origin = ProposalOrigin.FIXTURE if mode is ModelMode.FIXTURE else ProposalOrigin.MODEL
    agent = Agent(
        model,
        output_type=NativeOutput(InterviewTurnOutput),
        instructions=INSTRUCTIONS,
        retries={"tools": 0, "output": MAX_REQUESTS - 1},
    )
    accepted: list[InterviewProposal] = []

    @agent.output_validator
    def _check(output: InterviewTurnOutput) -> InterviewTurnOutput:
        proposal, problems = interview.check_turn(output, context, origin)
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


def fixture_interviewer_model() -> Model:
    """The deterministic demo interviewer behind Pydantic AI's model interface: no network,
    no key; it answers from the prompt's context with `fixture_turn`."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        output = fixture_turn(_prompt_context(messages))
        return ModelResponse(
            parts=[TextPart(output.model_dump_json())], model_name=FIXTURE_MODEL_ID
        )

    return FunctionModel(respond, model_name=FIXTURE_MODEL_ID)
