"""Bounded Meta search discovery (S3.2; SEC-05, ACQ-06, MODEL-08): the model gets a target
and a city only, proposes candidate pages, and deterministic code keeps what may be fetched
and says which the search really returned. One request, no repair. Offline: a fake provider
answers with Meta-shaped native search parts."""

import json
from typing import Any

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    NativeToolCallPart,
    NativeToolReturnPart,
    TextPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from careerwright.evidence.search import (
    INSTRUCTIONS,
    JOB_SEARCH,
    ROLE_SEARCH,
    SearchEmptyReason,
    SearchInput,
    SearchOutput,
    SearchProposal,
    bounded_worst_case_nano_usd,
    check_search,
    exceeded_bound,
    prompt_bytes,
    refused_hosts,
    render_prompt,
    worst_case_nano_usd,
)
from careerwright.evidence.search_agent import SOURCE_SEARCH_TASK, run_search, searched
from careerwright.identity.activity import measured_usage
from careerwright.identity.failures import BoundExceededError, FailureClass, classify_failure
from careerwright.identity.model_registry import ModelMode
from tests.support.fake_models import SEARCHED, search_parts

CONTEXT = SearchInput(profile_version=4, target="Data quality analyst", city="Manchester")


def ignore(text: str, *, complete: bool) -> None:
    """A partial-reply sink that keeps nothing."""


def output(*urls: str) -> SearchOutput:
    return SearchOutput.model_validate({"candidates": [{"url": u, "title": "T"} for u in urls]})


@pytest.mark.req("SEC-05")
def test_the_model_is_told_the_target_and_city_and_nothing_else() -> None:
    sent = json.loads(render_prompt(CONTEXT).partition("\n")[2])

    assert sent == {"role": "Data quality analyst", "city": "Manchester", "country": "England"}
    assert prompt_bytes(CONTEXT) <= JOB_SEARCH.max_prompt_bytes


@pytest.mark.req("ACQ-06", "ACQ-01")
def test_only_fetchable_permitted_candidates_are_kept_and_grounding_is_recorded() -> None:
    proposal = check_search(
        output(
            "https://careers.northwind.example/jobs/1",
            "https://careers.northwind.example/jobs/1/",  # the same page again
            "https://jobs.board.example/ad/9",
            "https://www.linkedin.com/jobs/view/1",
            "http://10.0.0.2/jobs",
            "javascript:alert(1)",
        ),
        CONTEXT,
        sources={"https://careers.northwind.example/jobs/1"},
        queries=["data quality analyst jobs Manchester"],
    )

    assert [(c.url, c.grounded) for c in proposal.candidates] == [
        ("https://careers.northwind.example/jobs/1", True),
        ("https://careers.northwind.example/jobs/1/", True),
        ("https://jobs.board.example/ad/9", False),
    ]
    assert [e.reason for e in proposal.excluded] == [
        "source_not_permitted",
        "address_not_allowed",
        "scheme_not_allowed",
    ]
    # A refused URL is never kept as a URL (it could be `javascript:`): its host, as text.
    assert [(e.url, e.refused_host) for e in proposal.excluded] == [
        ("https://www.linkedin.com/jobs/view/1", None),
        (None, "10.0.0.2"),
        (None, None),
    ]
    assert proposal.queries == ["data quality analyst jobs Manchester"]
    assert proposal.sources_seen == 1
    assert proposal.source_hosts == ["careers.northwind.example"]
    assert proposal.empty_reason is None


def test_candidates_past_the_limit_are_excluded_not_kept() -> None:
    urls = [f"https://jobs.board.example/ad/{n}" for n in range(JOB_SEARCH.max_candidates + 2)]

    proposal = check_search(output(*urls), CONTEXT, sources=set(), queries=[])

    assert len(proposal.candidates) == JOB_SEARCH.max_candidates == 8
    assert [e.reason for e in proposal.excluded] == ["over_the_limit"] * 2


@pytest.mark.req("ACQ-01")
def test_a_proposal_sealed_with_a_raw_url_is_never_served_with_it() -> None:
    # Re-review A N-3: a proposal sealed before the URL rule held `javascript:` in `url`.
    sealed = json.dumps(
        {
            "target": "Data quality analyst",
            "city": "Manchester",
            "candidates": [],
            "excluded": [
                {"url": "javascript:alert(1)", "reason": "scheme_not_allowed"},
                {"url": "http://10.0.0.2/jobs", "reason": "address_not_allowed"},
                {"url": "HTTPS://Uk.LinkedIn.com/jobs/1", "reason": "source_not_permitted"},
            ],
            "queries": [],
            "sources_seen": 0,
        }
    )

    proposal = SearchProposal.model_validate_json(sealed)

    assert [(e.url, e.refused_host) for e in proposal.excluded] == [
        (None, None),
        (None, "10.0.0.2"),
        ("https://uk.linkedin.com/jobs/1", None),
    ]


@pytest.mark.req("STATE-02")
@pytest.mark.parametrize(
    ("proposed", "sources", "reason"),
    [
        ((), set(), SearchEmptyReason.SEARCH_RETURNED_NOTHING),
        ((), {"https://jobs.board.example/list"}, SearchEmptyReason.NO_CANDIDATE_PROPOSED),
        (("https://uk.linkedin.com/jobs/view/1",), set(), SearchEmptyReason.ALL_EXCLUDED),
    ],
    ids=["nothing returned", "nothing proposed", "everything excluded"],
)
def test_a_search_with_no_candidate_says_why_and_never_that_there_is_no_vacancy(
    proposed: tuple[str, ...], sources: set[str], reason: SearchEmptyReason
) -> None:
    proposal = check_search(output(*proposed), CONTEXT, sources=sources, queries=["q"])

    assert proposal.candidates == []
    assert proposal.empty_reason is reason


@pytest.mark.req("MODEL-08")
def test_the_prompt_names_exactly_the_hosts_the_manifest_refuses() -> None:
    hosts = refused_hosts()

    assert hosts == ["adzuna.co.uk", "api.adzuna.com", "indeed.co.uk", "indeed.com", "linkedin.com"]
    assert all(host in INSTRUCTIONS for host in hosts)
    assert "sign-in" not in INSTRUCTIONS  # no open-ended class of sites
    assert "individual job posting" in INSTRUCTIONS


class Provider:
    def __init__(self, parts: list[Any], usage: RequestUsage | None = None) -> None:
        self.parts = parts
        self.usage = usage
        self.settings: list[Any] = []
        self.native_tools: list[Any] = []
        self.requests = 0

    def model(self) -> FunctionModel:
        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            self.requests += 1
            self.settings.append(info.model_settings)
            self.native_tools.extend(info.model_request_parameters.native_tools)
            if self.usage is None:
                return ModelResponse(parts=self.parts)
            return ModelResponse(parts=self.parts, usage=self.usage)

        return FunctionModel(respond)


@pytest.mark.req("MODEL-08", "JOB-08")
@pytest.mark.parametrize(
    ("usage", "bound"),
    [
        (
            RequestUsage(
                input_tokens=20_000, output_tokens=300, details={"web_search_requests": 9}
            ),
            "web_searches",
        ),
        (
            RequestUsage(
                input_tokens=ROLE_SEARCH.max_input_tokens() + 1,
                output_tokens=300,
                details={"web_search_requests": 2},
            ),
            "input_tokens",
        ),
    ],
    ids=["a ninth search", "more input than reserved"],
)
def test_a_search_past_its_reserved_bounds_is_named_for_the_activity_to_refuse(
    usage: RequestUsage, bound: str
) -> None:
    # Review B I4, N4: Meta runs the searches inside the one request, so its own measured
    # usage is the check, applied by the activity on every path (`RunTask.exceeded_bound`).
    # The bound is the run kind's one reservation, role research's deeper search (eight
    # tool calls), whichever purpose the search had.
    provider = Provider(search_parts(request(), "SENTINEL"), usage)

    with capture_run_messages() as messages:
        run_search(
            provider.model(), ModelMode.CONTRIBUTOR, CONTEXT.model_dump_json().encode(), ignore
        )
    measured, _, _ = measured_usage(messages)

    assert measured is not None
    assert SOURCE_SEARCH_TASK.exceeded_bound is exceeded_bound
    assert exceeded_bound(measured) == bound
    classified = classify_failure(BoundExceededError(bound))
    assert (classified.failure, classified.label) == (
        FailureClass.BOUND_EXCEEDED,
        f"bound_exceeded:{bound}",
    )


@pytest.mark.req("MODEL-08")
def test_a_search_within_its_bounds_is_accepted() -> None:
    usage = RequestUsage(input_tokens=20_000, output_tokens=300, details={"web_search_requests": 2})
    provider = Provider(search_parts(request(), "SENTINEL"), usage)

    proposal = run_search(
        provider.model(), ModelMode.CONTRIBUTOR, CONTEXT.model_dump_json().encode(), ignore
    )

    assert proposal.candidates


def request() -> dict[str, object]:
    loaded: dict[str, object] = json.loads(render_prompt(CONTEXT).partition("\n")[2])
    return loaded


@pytest.mark.req("ACQ-03", "MODEL-08")
def test_a_search_is_one_request_with_its_tool_calls_bounded_and_sources_asked_for() -> None:
    provider = Provider(search_parts(request(), "SENTINEL"))

    with capture_run_messages() as messages:
        proposal = run_search(
            provider.model(), ModelMode.CONTRIBUTOR, CONTEXT.model_dump_json().encode(), ignore
        )

    assert provider.requests == 1
    [settings] = provider.settings
    assert settings["extra_body"] == {"max_tool_calls": 2}
    assert settings["max_tokens"] == 1_500
    assert settings["openai_include_web_search_sources"] is True
    # A job search keeps its own settings (role research's deeper search is its own).
    [tool] = provider.native_tools
    assert (tool.kind, tool.search_context_size) == ("web_search", "low")
    assert [(c.url, c.grounded) for c in proposal.candidates] == [
        (SEARCHED, True),
        ("https://jobs.board.example/ad/9", False),
    ]
    assert proposal.queries == ["Data quality analyst jobs Manchester"]
    assert searched(messages)[0] == [SEARCHED]  # in the search's own order


@pytest.mark.req("MODEL-08")
def test_an_unusable_answer_ends_the_run_without_a_repair_request() -> None:
    provider = Provider([TextPart('{"candidates": "not a list"}')])

    with capture_run_messages() as messages, pytest.raises(UnexpectedModelBehavior) as raised:
        run_search(
            provider.model(), ModelMode.CONTRIBUTOR, CONTEXT.model_dump_json().encode(), ignore
        )

    assert classify_failure(raised.value).failure is FailureClass.INVALID_MODEL_OUTPUT
    assert provider.requests == 1  # a repair would pay for every search again
    assert len([m for m in messages if isinstance(m, ModelRequest)]) == 1


@pytest.mark.req("STATE-02", "ACQ-06")
@pytest.mark.parametrize("status", [None, "failed", "in_progress"])
def test_an_empty_answer_without_a_completed_search_is_a_failure(status: str | None) -> None:
    parts: list[Any] = [TextPart('{"candidates": []}')]
    if status is not None:
        parts[:0] = [
            NativeToolCallPart(
                tool_name="web_search", tool_call_id="ws_1", args={"query": "nursing Leeds"}
            ),
            NativeToolReturnPart(
                tool_name="web_search",
                tool_call_id="ws_1",
                content={"status": status, "sources": []},
            ),
        ]
    provider = Provider(parts)

    with pytest.raises(UnexpectedModelBehavior) as raised:
        run_search(
            provider.model(), ModelMode.CONTRIBUTOR, CONTEXT.model_dump_json().encode(), ignore
        )

    assert classify_failure(raised.value).failure is FailureClass.INVALID_MODEL_OUTPUT
    assert provider.requests == 1


@pytest.mark.req("STATE-02", "ACQ-06")
def test_a_completed_search_that_returned_no_page_can_be_an_empty_success() -> None:
    provider = Provider(
        [
            NativeToolCallPart(
                tool_name="web_search", tool_call_id="ws_1", args={"query": "nursing Leeds"}
            ),
            NativeToolReturnPart(
                tool_name="web_search",
                tool_call_id="ws_1",
                content={"status": "completed", "sources": []},
            ),
            TextPart('{"candidates": []}'),
        ]
    )

    proposal = run_search(
        provider.model(), ModelMode.CONTRIBUTOR, CONTEXT.model_dump_json().encode(), ignore
    )

    assert proposal.empty_reason is SearchEmptyReason.SEARCH_RETURNED_NOTHING
    assert proposal.queries == ["nursing Leeds"]
    assert provider.requests == 1


@pytest.mark.req("STATE-02", "ACQ-06")
def test_a_failed_search_is_not_hidden_by_another_completed_search() -> None:
    parts = search_parts(request(), "")
    parts.insert(
        -1,
        NativeToolReturnPart(
            tool_name="web_search", tool_call_id="ws_2", content={"status": "failed"}
        ),
    )
    provider = Provider(parts)

    with pytest.raises(UnexpectedModelBehavior):
        run_search(
            provider.model(), ModelMode.CONTRIBUTOR, CONTEXT.model_dump_json().encode(), ignore
        )

    assert provider.requests == 1


@pytest.mark.req("MODEL-08")
def test_an_attempt_reserves_its_one_request_with_every_tool_call_at_its_bounds() -> None:
    # One run kind, one reservation (no new run kind): role research's search is the larger in
    # every bound, so it is the kind's worst case, priced from the registry.
    # Role research: input 2,500 + 500 + 8 x 12,000 = 99,000 tokens; output 4,000; 8 searches
    # at $2.50/1,000 (one price whatever the search context).
    # Contributor: 99,000 x 100 + 4,000 x 200 + 8 x 2,500,000 = 30,700,000 nano-USD ($0.031).
    # Standard: 99,000 x 1,250 + 4,000 x 4,250 + 20,000,000 = 160,750,000 ($0.161): three
    # DBOS attempts fit the default $0.50 run limit.
    # Muse Wonder: 99,000 x 4,000 + 4,000 x 20,000 + 20,000,000 = 496,000,000 ($0.496):
    # three fit the session's $1.60 run cap.
    for bound in ("max_tool_calls", "max_candidates", "max_prompt_bytes", "max_output_tokens"):
        assert getattr(ROLE_SEARCH, bound) >= getattr(JOB_SEARCH, bound), bound
    assert worst_case_nano_usd("muse-spark-1.3-contributor") == 30_700_000
    assert worst_case_nano_usd("muse-spark-1.3") == 160_750_000
    assert worst_case_nano_usd("muse-wonder-1.0") == 496_000_000
    assert 3 * worst_case_nano_usd("muse-spark-1.3") <= 500_000_000
    # A job search alone, at its own bounds: 2,500 + 500 + 2 x 12,000 = 27,000 in, 1,500 out,
    # 2 searches: $0.008 on the test model, $0.045 on Standard.
    assert bounded_worst_case_nano_usd("muse-spark-1.3-contributor", JOB_SEARCH) == 8_000_000
    assert bounded_worst_case_nano_usd("muse-spark-1.3", JOB_SEARCH) == 45_125_000
