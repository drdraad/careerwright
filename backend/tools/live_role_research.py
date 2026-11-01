"""`make live-role-research`: Task 6e's acceptance run of "Research this role" (ADR 0015
decision 2; ADR 0009 decision 12, amendment; ruling R5), budget-capped and ledgered.

One role-research search on the test model, in this process, through the product's own task
code and bound check (`run_search` on a `RoleSearchInput`: the title and "England", nothing
else), for a synthetic test title (no person's data; `--title`, `TITLE=`). Then up to five of
its candidate pages (`role_research.pages_to_read`) are read through the restricted
acquisition worker's own code in this process (`acquire_page`: the URL checks, the source
manifest, robots.txt, pacing, redaction; each page's class from the manifest), and the title
is checked on each by the product's own corroboration code (`check_title`, `corroborate`).
No model reads a page. The one provider request is ledgered in its own scope
(`live-role-research`: at most 3 requests and $0.10 worst case in all, the test model only),
whatever happens, with what the search proposed and what the pages showed in the row's notes
(hosts, classes, whether each page uses the title, the verdict; hosts only, never a URL or a
page's words). The page reads call no model and cost nothing; they are counted in the notes.
Then the requests sent, the result and the row are scanned for the key.

The key is read from the repository's gitignored `.env` into a `SecretStr`, never a command
argument and never printed. Run from `backend/`: `uv run --locked python -m tools.live_role_research
[--title "..."]`.
"""

import argparse
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import SecretStr
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelRequest
from pydantic_ai.models import Model

from careerwright.evidence import search
from careerwright.evidence.acquire import AcquisitionResult, Pacer, acquire_page
from careerwright.evidence.corroboration import PageEvidence, check_title, corroborate
from careerwright.evidence.fetcher import Fetcher
from careerwright.evidence.records import AttemptStatus
from careerwright.evidence.role_research import pages_to_read
from careerwright.evidence.search_agent import run_search
from careerwright.evidence.sources import load_manifest
from careerwright.identity.activity import PartialWriter, measured_usage
from careerwright.identity.failures import BoundExceededError, classify_failure
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.model_registry import ModelMode, estimate_cost_nano_usd, format_usd
from tools.leak_scan import Needle, scan
from tools.live_smoke import (
    RESPONSES_ENDPOINT,
    ScopeBudget,
    SmokeKind,
    SmokeSettings,
    _call_in_process,
    _search_model,
    authorise,
    search_notes,
)
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry

ROLE_SCOPE = "live-role-research"
ROLE_BUDGET = ScopeBudget(ROLE_SCOPE, 3, 0, 100_000_000)
# A synthetic test title (no person's data): one no list Careerwright holds is expected to
# hold, so research is what would find it. The controller may choose another with TITLE=.
DEFAULT_TITLE = "Biodiversity net gain officer"
ROLE_RESEARCH = SmokeKind(
    "role_research",
    1,
    search.MAX_REQUESTS,
    search.worst_case_nano_usd,
    "role research in process: one search told only a synthetic title and England (the "
    "product's own task code and bound check), then up to five of its pages read through "
    "the guarded fetcher and the title checked on each by code (no model reads a page)",
)

Reader = Callable[[str], AcquisitionResult]


def _reader() -> Reader:
    fetcher = Fetcher(user_agent=load_manifest().user_agent)  # production: no extra origins
    pacer = Pacer()
    return lambda url: acquire_page(fetcher, pacer, url, now=datetime.now(UTC), read_text=True)


def page_notes(title: str, results: list[AcquisitionResult]) -> dict[str, Any]:
    """What the row records of the pages read: hosts, classes, outcomes and the verdict; never
    a URL or a page's words."""
    evidence = [
        PageEvidence(
            ref=str(n),
            host=r.provider,
            rights_class=r.rights_class,
            check=check_title(title, r.role_text or "", r.copies, provider=r.provider),
        )
        for n, r in enumerate(results)
        if r.status is AttemptStatus.SUCCEEDED
    ]
    result = corroborate(evidence)
    group_of = {ref: n for n, group in enumerate(result.groups, start=1) for ref in group}
    checked = {e.ref: e.check.verified for e in evidence}
    return {
        "pages": [
            {
                "host": r.provider,
                "status": r.status.value,
                "reason": r.reason,
                "rights_class": r.rights_class.value if r.rights_class else None,
                "title_verified": checked.get(str(n)),
                "source": group_of.get(str(n)),
            }
            for n, r in enumerate(results)
        ],
        "verdict": result.verdict.value,
        "reason": result.reason.value if result.reason else None,
        "sources": result.sources,
        "official": result.official,
    }


def research_role(
    settings: SmokeSettings,
    ledger: Ledger,
    *,
    title: str = DEFAULT_TITLE,
    build: Callable[[str, SecretStr], Model] | None = None,
    read: Reader | None = None,
) -> int:
    """`build` replaces Meta and `read` the guarded fetcher in tests only."""
    models = ModelChoice.configure(settings.meta_test_model, settings.meta_production_model, "test")
    context = search.RoleSearchInput(title=" ".join(title.split()))
    with ledger.exclusive():
        model_id, worst_case = authorise(
            models,
            production=False,
            budget=ROLE_BUDGET,
            spent=ledger.spent(ROLE_SCOPE),
            kind=ROLE_RESEARCH,
        )
        print(
            f"role research ({ROLE_RESEARCH.name}): model {model_id} (test); 1 request, worst "
            f"case {format_usd(worst_case)}; title {context.title!r} (synthetic)",
            flush=True,
        )
        model = (build or _search_model)(model_id, settings.api_key)
        done = _call_in_process(
            lambda: run_search(
                model,
                ModelMode.CONTRIBUTOR,
                context.model_dump_json().encode(),
                PartialWriter(lambda text: None),
            )
        )
        usage, reasoning, response_id = measured_usage(done.messages)
        outcome = done.outcome
        bound = search.exceeded_bound(usage) if usage else None
        if bound is not None:  # the activity's own check (`SOURCE_SEARCH_TASK.exceeded_bound`)
            outcome = classify_failure(BoundExceededError(bound)).label
        proposal = (
            done.output
            if outcome == "succeeded" and isinstance(done.output, search.SearchProposal)
            else None
        )
        notes: dict[str, Any] = {"title": context.title, "synthetic": True}
        if proposal is not None:
            notes |= search_notes(proposal.model_dump(mode="json"))
            notes["prompt_version"] = search.ROLE_PROMPT_VERSION
            reader = read or _reader()
            notes |= page_notes(context.title, [reader(url) for url in pages_to_read(proposal)])
        record = ledger.append(
            LiveCallEntry(
                budget_scope=ROLE_SCOPE,
                purpose=ROLE_RESEARCH.purpose,
                http_requests=max(1, sum(isinstance(m, ModelRequest) for m in done.messages)),
                model_id=model_id,
                is_production_model=False,
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.OK if outcome == "succeeded" else CallOutcome.FAILED,
                reserved_nano_usd=worst_case,
                estimated_cost_nano_usd=estimate_cost_nano_usd(model_id, usage) if usage else None,
                error_type=None if outcome == "succeeded" else outcome,
                input_tokens=usage.input_tokens if usage else None,
                cached_input_tokens=usage.cached_input_tokens if usage else None,
                output_tokens=usage.output_tokens if usage else None,
                reasoning_tokens=reasoning,
                web_search_queries=usage.web_search_queries if usage else None,
                provider_response_id=response_id,
                notes=json.dumps(notes),
            )
        )
        ledger.write_markdown()
        cells = [
            ("requests sent", ModelMessagesTypeAdapter.dump_json(done.messages).decode()),
            ("result", proposal.model_dump_json() if proposal else ""),
            (f"ledger row {record.seq}", record.model_dump_json()),
        ]
        key = Needle("Meta key", settings.api_key.get_secret_value(), fragment_length=12)
        findings = scan(cells, [key])
    print(
        f"outcome {outcome}; verdict {notes.get('verdict')}; sources {notes.get('sources')}; "
        f"pages {len(notes.get('pages', []))}; ledger row {record.seq}; {len(cells)} cells "
        f"scanned, {len(findings)} findings",
        flush=True,
    )
    return 0 if outcome == "succeeded" and not findings else 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default=DEFAULT_TITLE, help="a synthetic test title")
    args = parser.parse_args(argv)
    sys.exit(research_role(SmokeSettings(), Ledger(), title=args.title))


if __name__ == "__main__":
    main()
