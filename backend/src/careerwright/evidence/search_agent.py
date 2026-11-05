"""The source search as a run task (adapter; ADR 0003: search is Meta's own, through
`NativeTool(WebSearchTool(...))`, never the `WebSearch` capability whose local fallback would
reach another provider).

One request on whatever model the worker built for the run: strict JSON output
(`NativeOutput`), the purpose's search context and tool calls asked of the Responses API
(`search.SearchBounds`: a job search `low` and two, role research `medium` and eight), the
search's sources included so each candidate's grounding can be checked, and no repair
(`search.MAX_REQUESTS`). A response cut off at its token limit ends the run
(`TruncationGuard`). Demo workspaces never search (a database CHECK), so there is no fixture
model for this kind.
"""

import asyncio
from collections.abc import Sequence
from typing import Any

from pydantic_ai import Agent, NativeOutput, RunContext
from pydantic_ai.capabilities import AbstractCapability, NativeTool
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    NativeToolCallPart,
    NativeToolReturnPart,
)
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from pydantic_ai.native_tools import WebSearchTool, WebSearchUserLocation
from pydantic_ai.usage import UsageLimits

from careerwright.evidence import search
from careerwright.evidence.search import (
    INSTRUCTIONS,
    MAX_REQUESTS,
    OPTION_INSTRUCTIONS,
    ROLE_INSTRUCTIONS,
    OptionSearchInput,
    RoleSearchInput,
    SearchOutput,
    SearchProposal,
    bounds_for,
    render_option_prompt,
    render_prompt,
    render_role_prompt,
)
from careerwright.identity.activity import PartialSink, RunTask, TruncationGuard
from careerwright.identity.model_registry import ModelMode


def searched(messages: list[ModelMessage]) -> tuple[list[str], list[str]]:
    """(URLs the search returned or opened, each once, in the order the search gave them; the
    queries it ran), from the native tool parts of the run's responses."""
    sources: list[str] = []
    queries: list[str] = []
    completed = False
    for message in messages:
        if not isinstance(message, ModelResponse):
            continue
        for part in message.parts:
            if isinstance(part, NativeToolReturnPart) and part.tool_name == "web_search":
                if not isinstance(part.content, dict) or part.content.get("status") != "completed":
                    raise UnexpectedModelBehavior("The native web search did not complete.")
                completed = True
                listed: Any = part.content.get("sources")
                for source in listed if isinstance(listed, list) else []:
                    if isinstance(source, dict) and isinstance(source.get("url"), str):
                        sources.append(source["url"])
            elif isinstance(part, NativeToolCallPart) and part.tool_name == "web_search":
                args: Any = part.args if isinstance(part.args, dict) else {}
                if isinstance(args.get("query"), str):
                    queries.append(args["query"][:200])
                if isinstance(args.get("url"), str):  # an open-page action
                    sources.append(args["url"])
    if not completed:
        raise UnexpectedModelBehavior("The reply has no completed native web search.")
    return list(dict.fromkeys(sources)), queries


def run_search(
    model: Model,
    mode: ModelMode,
    raw_input: bytes | None,
    _sink: PartialSink,
    *,
    max_tool_calls: int | None = None,
    observe: Sequence[AbstractCapability[Any]] = (),
) -> SearchProposal:
    """`max_tool_calls` is None in the product (the purpose's own); only the live
    qualification of the bound (`tools.live_smoke --search-bound`) asks for one. `observe` is
    empty in the product; a model's live qualification (`tools.live_smoke --wonder`) passes a
    stream probe, which makes the one request stream."""
    if raw_input is None:
        raise ValueError("a source search has a sealed input")
    context = search.sealed_search_input(raw_input)
    # Role research (Task 6e) is one bounded request with its own instructions and its own
    # deeper search, told only the title and England.
    if isinstance(context, RoleSearchInput):
        instructions, prompt = ROLE_INSTRUCTIONS, render_role_prompt(context)
    elif isinstance(context, OptionSearchInput):
        instructions, prompt = OPTION_INSTRUCTIONS, render_option_prompt(context)
    else:
        instructions, prompt = INSTRUCTIONS, render_prompt(context)
    bounds = bounds_for(context)
    agent = Agent(
        model,
        output_type=NativeOutput(SearchOutput),
        instructions=instructions,
        retries={"tools": 0, "output": 0},
        capabilities=[
            TruncationGuard(),
            NativeTool(
                WebSearchTool(
                    search_context_size=bounds.context_size,
                    user_location=WebSearchUserLocation(country="GB"),
                )
            ),
            *observe,
        ],
    )
    accepted: list[SearchProposal] = []

    @agent.output_validator
    def _check(ctx: RunContext[None], output: SearchOutput) -> SearchOutput:
        sources, queries = searched(ctx.messages)
        accepted.append(search.check_search(output, context, sources=sources, queries=queries))
        return output

    settings = OpenAIResponsesModelSettings(
        max_tokens=bounds.max_output_tokens,
        openai_include_web_search_sources=True,
        extra_body={
            "max_tool_calls": bounds.max_tool_calls if max_tool_calls is None else max_tool_calls
        },
    )
    asyncio.run(
        agent.run(
            prompt,
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
            model_settings=settings,
        )
    )
    return accepted[-1]


SOURCE_SEARCH_TASK = RunTask(
    call=run_search,
    worst_case_nano_usd=search.worst_case_nano_usd,
    has_input=True,
    # Meta runs the searches inside the one request, so `request_limit` cannot bound them:
    # the activity holds the captured usage to the reservation's bounds on every path, a
    # reply that also failed included (review B N4).
    exceeded_bound=search.exceeded_bound,
)
