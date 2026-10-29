"""Page extraction as a run task (adapter; ADR 0009 decision 13; fix round 2, rulings 10-13).

One Pydantic AI agent on whatever Meta model the worker built for the run, with the
workspace's own key: strict JSON output (`NativeOutput`), no tools of any kind (the agent can
only answer the schema), at most `extraction.MAX_REQUESTS` requests (an answer that fails
the schema is sent back once, within the repair bound), and a response cut off at its token
limit ends the run (`TruncationGuard`). A quote that is not a span of the text is never
repaired: `extraction.check_extraction` drops it. Demo workspaces never extract (a database
CHECK), so there is no fixture model for this kind.

The run's output is the checked `ExtractionProposal`; `extraction_runs.record_extraction`
records its postings in the transaction that accepts it, and the run's sealed input (the
page's text) is erased once the run is terminal.
"""

import asyncio

from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models import Model
from pydantic_ai.usage import UsageLimits

from nessa.evidence import extraction, extraction_runs
from nessa.evidence.extraction import (
    INSTRUCTIONS,
    MAX_OUTPUT_TOKENS,
    MAX_REQUESTS,
    REPAIR_ALLOWANCE_TOKENS,
    ExtractionInput,
    ExtractionOutput,
    ExtractionProposal,
    render_prompt,
)
from nessa.identity.activity import PartialSink, RepairBound, RunTask, TruncationGuard
from nessa.identity.model_registry import ModelMode


def extraction_agent(model: Model) -> Agent[None, ExtractionOutput]:
    """No tools and no tool-using capability: only the output schema."""
    return Agent(
        model,
        output_type=NativeOutput(ExtractionOutput),
        instructions=INSTRUCTIONS,
        retries={"tools": 0, "output": MAX_REQUESTS - 1},
        capabilities=[TruncationGuard(), RepairBound(REPAIR_ALLOWANCE_TOKENS)],
    )


def run_extraction(
    model: Model, mode: ModelMode, raw_input: bytes | None, _sink: PartialSink
) -> ExtractionProposal:
    if raw_input is None:
        raise ValueError("a page extraction has a sealed input")
    if mode is ModelMode.FIXTURE:
        raise ValueError("a page extraction never runs on a fixture model")
    context = ExtractionInput.model_validate_json(raw_input)
    result = asyncio.run(
        extraction_agent(model).run(
            render_prompt(context),
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
            model_settings={"max_tokens": MAX_OUTPUT_TOKENS},
        )
    )
    return extraction.check_extraction(result.output, context)


PAGE_EXTRACTION_TASK = RunTask(
    call=run_extraction,
    worst_case_nano_usd=extraction.worst_case_nano_usd,
    has_input=True,
    record=extraction_runs.record_extraction,
    erases_input=True,
)
