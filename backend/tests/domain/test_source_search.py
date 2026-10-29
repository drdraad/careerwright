"""Bounded Meta search discovery (S3.2; SEC-05, ACQ-06, MODEL-08): the model gets a target
and a city only, proposes candidate pages, and deterministic code keeps what may be fetched
and says which the search really returned. One request, no repair. Offline: a fake provider
answers with Meta-shaped native search parts."""

import json
from typing import Any

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from nessa.evidence.search import (
    MAX_CANDIDATES,
    MAX_PROMPT_BYTES,
    SearchInput,
    SearchOutput,
    check_search,
    prompt_bytes,
    render_prompt,
    worst_case_nano_usd,
)
from nessa.evidence.search_agent import run_search, searched
from nessa.identity.failures import FailureClass, classify_failure
from nessa.identity.model_registry import ModelMode
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
    assert prompt_bytes(CONTEXT) <= MAX_PROMPT_BYTES


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
    assert proposal.queries == ["data quality analyst jobs Manchester"]
    assert proposal.sources_seen == 1


def test_candidates_past_the_limit_are_excluded_not_kept() -> None:
    urls = [f"https://jobs.board.example/ad/{n}" for n in range(MAX_CANDIDATES + 2)]

    proposal = check_search(output(*urls), CONTEXT, sources=set(), queries=[])

    assert len(proposal.candidates) == MAX_CANDIDATES
    assert [e.reason for e in proposal.excluded] == ["over_the_limit"] * 2


def test_an_empty_answer_is_a_valid_search_that_found_nothing() -> None:
    proposal = check_search(output(), CONTEXT, sources=set(), queries=["q"])

    assert proposal.candidates == []
    assert proposal.excluded == []


class Provider:
    def __init__(self, parts: list[Any]) -> None:
        self.parts = parts
        self.settings: list[Any] = []
        self.requests = 0

    def model(self) -> FunctionModel:
        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            self.requests += 1
            self.settings.append(info.model_settings)
            return ModelResponse(parts=self.parts)

        return FunctionModel(respond)


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
    assert settings["openai_include_web_search_sources"] is True
    assert [(c.url, c.grounded) for c in proposal.candidates] == [
        (SEARCHED, True),
        ("https://jobs.board.example/ad/9", False),
    ]
    assert proposal.queries == ["Data quality analyst jobs Manchester"]
    assert searched(messages)[0] == {SEARCHED}


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


@pytest.mark.req("MODEL-08")
def test_an_attempt_reserves_its_one_request_with_every_tool_call_at_its_bounds() -> None:
    # Input 2,500 + 500 + 2 x 12,000 = 27,000 tokens; output 1,500; 2 searches at $2.50/1,000.
    # Contributor: 27,000 x 100 + 1,500 x 200 + 2 x 2,500,000 = 8,000,000 nano-USD ($0.008).
    # Standard: 27,000 x 1,250 + 1,500 x 4,250 + 5,000,000 = 45,125,000 ($0.045): three DBOS
    # attempts fit the default $0.15 run limit.
    assert worst_case_nano_usd("muse-spark-1.3-contributor") == 8_000_000
    assert worst_case_nano_usd("muse-spark-1.3") == 45_125_000
    assert 3 * worst_case_nano_usd("muse-spark-1.3") <= 150_000_000
