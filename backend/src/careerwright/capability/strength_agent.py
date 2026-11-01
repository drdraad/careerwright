"""The overlooked strength as a run task, and the demo's fixture model (adapter).

One Pydantic AI agent on whatever model the worker built for the run: Meta's native provider
for live workspaces, or the fixture model for demo workspaces. Both answer the same strict
JSON schema (`NativeOutput`) and pass the same deterministic check
(`strength.check_strength`); a failed check is sent back once as a repair request, and a
second failure ends the run `invalid_model_output`. A response cut off at its token limit
ends the run at once. Nothing streams.
"""

import asyncio

from pydantic_ai import Agent, ModelRetry, NativeOutput
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

from careerwright.capability import strength
from careerwright.capability.strength import (
    CONTEXT_MARKER,
    INSTRUCTIONS,
    MAX_OUTPUT_TOKENS,
    MAX_REQUESTS,
    REPAIR_ALLOWANCE_TOKENS,
    OverlookedStrength,
    PromptStrengthContext,
    StrengthInput,
    StrengthOutput,
    fixture_strength,
    render_prompt,
)
from careerwright.identity.activity import PartialSink, RepairBound, RunTask, TruncationGuard
from careerwright.identity.model_registry import FIXTURE_STRENGTH_MODEL_ID, ModelMode
from careerwright.profile.interview import ProposalOrigin


def run_strength(
    model: Model, mode: ModelMode, raw_input: bytes | None, _sink: PartialSink
) -> OverlookedStrength:
    if raw_input is None:
        raise ValueError("a strength run has a sealed input")
    context = StrengthInput.model_validate_json(raw_input)
    origin = ProposalOrigin.FIXTURE if mode is ModelMode.FIXTURE else ProposalOrigin.MODEL
    agent = Agent(
        model,
        output_type=NativeOutput(StrengthOutput),
        instructions=INSTRUCTIONS,
        retries={"tools": 0, "output": MAX_REQUESTS - 1},
        capabilities=[TruncationGuard(), RepairBound(REPAIR_ALLOWANCE_TOKENS)],
    )
    accepted: list[OverlookedStrength] = []

    @agent.output_validator
    def _check(output: StrengthOutput) -> StrengthOutput:
        checked, problems = strength.check_strength(output, context, origin)
        if checked is None:
            raise ModelRetry(strength.strength_repair(problems))
        accepted.append(checked)
        return output

    asyncio.run(
        agent.run(
            render_prompt(context),
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
            model_settings={"max_tokens": MAX_OUTPUT_TOKENS},
        )
    )
    return accepted[-1]


STRENGTH_PROPOSAL_TASK = RunTask(
    call=run_strength,
    worst_case_nano_usd=strength.worst_case_nano_usd,
    has_input=True,
)


def _prompt(messages: list[ModelMessage]) -> PromptStrengthContext:
    for message in reversed(messages):
        for part in getattr(message, "parts", ()):
            if (
                isinstance(part, UserPromptPart)
                and isinstance(part.content, str)
                and part.content.startswith(CONTEXT_MARKER)
            ):
                return PromptStrengthContext.model_validate_json(
                    part.content[len(CONTEXT_MARKER) :]
                )
    raise ValueError("the prompt has no strength context")


def fixture_strength_model() -> Model:
    """The demo's deterministic strength finder behind Pydantic AI's model interface: no
    network, no key; it answers from the prompt with `fixture_strength`."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        output = fixture_strength(_prompt(messages))
        return ModelResponse(
            parts=[TextPart(output.model_dump_json())], model_name=FIXTURE_STRENGTH_MODEL_ID
        )

    return FunctionModel(respond, model_name=FIXTURE_STRENGTH_MODEL_ID)
