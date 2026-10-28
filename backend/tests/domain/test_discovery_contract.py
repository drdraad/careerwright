"""The discovery contract (S2.4; REC-1, DIV-1): the model turns the confirmed profile into
search queries and a few title hypotheses; deterministic code checks that every query rests
on the person's own answers and carries no inference about them. Semantic checks only."""

import json
import uuid
from typing import Any

import pytest

from nessa.profile.discovery import (
    INSTRUCTIONS,
    MAX_HYPOTHESES,
    MAX_PROMPT_BYTES,
    MAX_QUERIES,
    SCHEMA_ALLOWANCE_TOKENS,
    DiscoveryInput,
    DiscoveryOutput,
    EvidenceItem,
    QueryChannel,
    check_discovery,
    evidence_of,
    prompt_bytes,
    render_prompt,
    worst_case_nano_usd,
)
from nessa.profile.document import FIELD_NAMES, ProfileInput, apply_profile_input, empty_profile
from nessa.profile.exploration import release_note, with_article
from nessa.profile.fixture_discovery import fixture_queries, prompt_context
from nessa.profile.interview import ProfileField, ProposalOrigin

SOURCE = uuid.UUID("00000000-0000-4000-8000-0000000000aa")


def document(**fields: Any) -> Any:
    values: dict[str, Any] = {name: {"state": "unasked"} for name in FIELD_NAMES}
    values.update({k: {"state": "provided", "value": v} for k, v in fields.items()})
    return apply_profile_input(empty_profile(), ProfileInput.model_validate(values), SOURCE)


P02 = document(
    enjoyed_tasks=["repairing physical objects", "working outdoors"],
    work_style=["practical", "small team"],
    cities=["Leeds", "Manchester"],
    weekly_study_hours=12,
)


def context(doc: Any = P02) -> DiscoveryInput:
    return DiscoveryInput(profile_version=3, evidence=evidence_of(doc))


def query(text: str, channel: str = "tasks", *based_on: str) -> dict[str, Any]:
    return {"text": text, "channel": channel, "based_on": list(based_on) or ["working outdoors"]}


def output(*queries: dict[str, Any], hypotheses: list[dict[str, Any]] | None = None) -> Any:
    return DiscoveryOutput.model_validate(
        {"queries": list(queries), "hypotheses": hypotheses or []}
    )


def problems(out: DiscoveryOutput, ctx: DiscoveryInput | None = None) -> list[str]:
    proposal, found = check_discovery(out, ctx or context(), ProposalOrigin.MODEL)
    assert (proposal is None) == bool(found)
    return found


@pytest.mark.req("REC1-01", "DIV1-10")
def test_the_evidence_is_the_confirmed_answers_that_describe_work_and_nothing_else() -> None:
    evidence = evidence_of(P02)

    assert [(item.field, item.text) for item in evidence] == [
        (ProfileField.ENJOYED_TASKS, "repairing physical objects"),
        (ProfileField.ENJOYED_TASKS, "working outdoors"),
        (ProfileField.WORK_STYLE, "practical"),
        (ProfileField.WORK_STYLE, "small team"),
    ]  # no cities, hours, money or name: they are limits, not descriptions of work
    prompt = render_prompt(context())
    assert "Leeds" not in prompt
    assert "12" not in prompt


@pytest.mark.req("DIV1-02", "DIV1-10", "TEST1-10")
def test_a_valid_output_becomes_queries_that_cite_the_answers_they_come_from() -> None:
    out = output(
        query("machinery repair", "tasks", "repairing physical objects"),
        query("outdoor maintenance work", "environment", "working outdoors", "practical"),
        query("agricultural equipment", "less_familiar", "repairing physical objects"),
        hypotheses=[{"title": "Wind turbine technician", "based_on": ["working outdoors"]}],
    )

    proposal, found = check_discovery(out, context(), ProposalOrigin.MODEL)

    assert found == []
    assert proposal is not None
    assert [q.query_id for q in proposal.queries] == ["q1", "q2", "q3"]
    assert proposal.queries[1].channel is QueryChannel.ENVIRONMENT
    assert [(e.field, e.text) for e in proposal.queries[1].based_on] == [
        (ProfileField.ENJOYED_TASKS, "working outdoors"),
        (ProfileField.WORK_STYLE, "practical"),
    ]
    assert proposal.hypotheses[0].title == "Wind turbine technician"  # still a hypothesis
    assert proposal.profile_version == 3


def test_an_occupation_gets_the_article_its_sound_needs() -> None:
    # Task 6 review A-M14: "a administrative assistant".
    assert with_article("administrative assistant") == "an administrative assistant"
    assert with_article("bicycle mechanic") == "a bicycle mechanic"
    assert with_article("ICT help desk agent") == "an ICT help desk agent"
    assert with_article("university lecturer") == "a university lecturer"
    assert with_article("hour-glass maker") == "an hour-glass maker"


@pytest.mark.req("TAX1-01", "DIV1-04")
def test_the_searches_record_the_release_they_were_chosen_for_and_a_change_is_said() -> None:
    # Task 6 review A-M9: the slate is recomputed on each read, against the held release.
    pinned = context().model_copy(update={"release": "esco-v1.2.1-en-csv"})
    out = output(query("machinery repair", "tasks", "repairing physical objects"))

    proposal, _ = check_discovery(out, pinned, ProposalOrigin.MODEL)

    assert proposal is not None
    assert proposal.release == "esco-v1.2.1-en-csv"
    assert release_note("esco-v1.2.1-en-csv", "esco-v1.2.1-en-csv") is None
    assert release_note(None, "esco-v1.2.1-en-csv") is None  # chosen before it was recorded
    note = release_note("esco-v1.2.1-en-csv", "esco-v1.3.0-en-csv")
    assert note is not None
    assert "esco-v1.3.0-en-csv" in note


@pytest.mark.req("REC1-06", "DIV1-04")
def test_a_query_resting_on_something_the_person_never_said_is_refused() -> None:
    found = problems(output(query("forestry", "tasks", "loves trees")))

    assert any("based_on" in problem for problem in found)


@pytest.mark.req("REC1-09", "REC1-02")
@pytest.mark.parametrize(
    "text",
    ["jobs for older women", "work suited to ADHD", "roles for an ISTP", "female engineer"],
)
def test_a_query_using_demographics_health_or_a_type_the_person_never_gave_is_refused(
    text: str,
) -> None:
    assert any("did not mention" in p for p in problems(output(query(text))))


def test_bounds_duplicates_and_empty_output_are_problems() -> None:
    many = [query(f"repair work {n}") for n in range(MAX_QUERIES + 1)]
    hypotheses = [{"title": f"Title {n}", "based_on": ["working outdoors"]} for n in range(4)]

    assert problems(output(*many))
    assert problems(output(query("Repair work"), query("repair  work")))
    assert problems(output())
    assert problems(output(query("x")))  # too short to search
    assert len(hypotheses) > MAX_HYPOTHESES
    assert problems(output(query("repair work"), hypotheses=hypotheses))


@pytest.mark.req("DIV1-10")
def test_the_fixture_proposer_reads_the_live_prompt_and_passes_the_same_check() -> None:
    ctx = context()

    out = fixture_queries(prompt_context(render_prompt(ctx)))
    proposal, found = check_discovery(out, ctx, ProposalOrigin.FIXTURE)

    assert found == []
    assert proposal is not None
    assert {q.text for q in proposal.queries} >= {"repairing physical objects", "working outdoors"}
    channels = {q.channel for q in proposal.queries}
    assert QueryChannel.ENVIRONMENT in channels  # the work style informs the search
    assert fixture_queries(prompt_context(render_prompt(ctx))) == out  # deterministic


def test_the_prompt_and_schema_fit_the_bounds_the_reservation_assumes() -> None:
    long_items = [f"{'a' * 100} {n}" for n in range(8)]
    busy = document(
        current_role="Warehouse shift supervisor",
        target_titles=["Data quality analyst", "Facilities technician", "Gardener"],
        enjoyed_tasks=long_items,
        confident_tasks=long_items,
        evidenced_tasks=long_items,
        work_style=long_items,
    )
    assert prompt_bytes(context(busy)) <= MAX_PROMPT_BYTES
    schema = json.dumps(DiscoveryOutput.model_json_schema())
    assert len(schema.encode()) <= SCHEMA_ALLOWANCE_TOKENS
    for keyword in ("minLength", "maxLength", "maxItems", "minItems", "pattern", "format"):
        assert keyword not in schema
    assert "never use it to exclude" in INSTRUCTIONS


@pytest.mark.req("MODEL-08")
def test_an_attempt_reserves_both_requests_at_their_bounds() -> None:
    # Input bound 8,000 + 1,500 + 1,500 + 1,000 = 12,000 tokens, output 1,500, two requests.
    # Contributor: (12,000 x 100 + 1,500 x 200) x 2 = 3,000,000 nano-USD ($0.003).
    # Standard: (12,000 x 1,250 + 1,500 x 4,250) x 2 = 42,750,000 nano-USD ($0.04275).
    assert worst_case_nano_usd("muse-spark-1.3-contributor") == 3_000_000
    assert worst_case_nano_usd("muse-spark-1.3") == 42_750_000
    assert worst_case_nano_usd("nessa-fixture-discovery-1") == 0


def test_evidence_items_are_plain_answer_texts() -> None:
    item = EvidenceItem(field=ProfileField.CURRENT_ROLE, text="Shift supervisor")

    assert item.model_dump() == {"field": "current_role", "text": "Shift supervisor"}
