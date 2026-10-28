"""The written explanation as a run task, and the fixture explainer as a model (adapter).

The task runs one Pydantic AI agent on whatever model the worker built for the run: Meta's
native provider for live workspaces, or the fixture explainer for demo workspaces. Both
answer the same strict JSON schema (`NativeOutput`) and pass the same deterministic check
(`slate_explanation.check_explanation`); a failed check is sent back once as a repair
request, and a second failure ends the run `invalid_model_output`, as for a discovery. A
response cut off at its token limit ends the run at once. Nothing streams.
"""

import asyncio

from pydantic_ai import Agent, ModelRetry, NativeOutput
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

from nessa.identity.activity import PartialSink, RepairBound, RunTask, TruncationGuard
from nessa.identity.model_registry import FIXTURE_EXPLAINER_MODEL_ID, ModelMode
from nessa.profile import slate_explanation
from nessa.profile.fixture_explainer import fixture_explanation, prompt_context
from nessa.profile.interview import ProposalOrigin
from nessa.profile.slate_explanation import (
    CONTEXT_MARKER,
    INSTRUCTIONS,
    MAX_OUTPUT_TOKENS,
    MAX_REQUESTS,
    REPAIR_ALLOWANCE_TOKENS,
    ExplanationInput,
    ExplanationOutput,
    SlateExplanation,
    render_prompt,
)


def run_explanation(
    model: Model, mode: ModelMode, raw_input: bytes | None, _sink: PartialSink
) -> SlateExplanation:
    if raw_input is None:
        raise ValueError("an explanation has a sealed input")
    context = ExplanationInput.model_validate_json(raw_input)
    origin = ProposalOrigin.FIXTURE if mode is ModelMode.FIXTURE else ProposalOrigin.MODEL
    agent = Agent(
        model,
        output_type=NativeOutput(ExplanationOutput),
        instructions=INSTRUCTIONS,
        retries={"tools": 0, "output": MAX_REQUESTS - 1},
        capabilities=[TruncationGuard(), RepairBound(REPAIR_ALLOWANCE_TOKENS)],
    )
    accepted: list[SlateExplanation] = []

    @agent.output_validator
    def _check(output: ExplanationOutput) -> ExplanationOutput:
        written, problems = slate_explanation.check_explanation(output, context, origin)
        if written is None:
            raise ModelRetry(slate_explanation.repair_message(problems))
        accepted.append(written)
        return output

    asyncio.run(
        agent.run(
            render_prompt(context),
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
            model_settings={"max_tokens": MAX_OUTPUT_TOKENS},
        )
    )
    return accepted[-1]


SLATE_EXPLANATION_TASK = RunTask(
    call=run_explanation,
    worst_case_nano_usd=slate_explanation.worst_case_nano_usd,
    has_input=True,
)


def _prompt(messages: list[ModelMessage]) -> str:
    for message in reversed(messages):
        for part in getattr(message, "parts", ()):
            if (
                isinstance(part, UserPromptPart)
                and isinstance(part.content, str)
                and part.content.startswith(CONTEXT_MARKER)
            ):
                return part.content
    raise ValueError("the prompt has no explanation context")


def fixture_explainer_model() -> Model:
    """The deterministic demo explainer behind Pydantic AI's model interface: no network, no
    key; it answers from the prompt with `fixture_explanation`."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        output = fixture_explanation(prompt_context(_prompt(messages)))
        return ModelResponse(
            parts=[TextPart(output.model_dump_json())], model_name=FIXTURE_EXPLAINER_MODEL_ID
        )

    return FunctionModel(respond, model_name=FIXTURE_EXPLAINER_MODEL_ID)
