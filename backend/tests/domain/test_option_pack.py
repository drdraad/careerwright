"""The England option pack's format and checks (OPTN-08, OPTN-10; ADR 0011). The pack
under test here is a small in-memory one built from synthetic-looking but non-fixture
values: each test breaks one rule and expects its named problem."""

import copy
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from nessa.catalogue.option_pack import (
    PINS,
    OptionPackError,
    ReviewState,
    check_pack,
    dump_pack,
    load_pack,
    pack_path,
    parse_pack,
    schema,
)

SHA = "a" * 64
MANIFEST = Path(__file__).resolve().parents[3] / "corpus" / "manifest.json"


def minimal() -> dict[str, Any]:
    """One target, one job page with one requirement, one course page with an option, an
    offering and an outcome, and one funding page with an instrument: every record
    proposed, every value cited."""
    return {
        "pack": "nessa-england-option-pack",
        "format_version": 1,
        "pack_version": "0.0.1",
        "dated": "2026-10-29",
        "jurisdiction": "GB-ENG",
        "currency": "GBP",
        "synthetic": False,
        "label_review": "not run - requires human domain reviewer",
        "notes": [],
        "targets": [
            {
                "target_id": "t",
                "persona": "P01",
                "title": "Data quality analyst",
                "city": "Manchester",
            }
        ],
        "skills": [
            {"skill_id": "pack:t:querying", "target_id": "t", "label": "Querying", "kind": "skill"}
        ],
        "sources": [
            source("J01", "job_posting"),
            source("C01", "course_page"),
            source("F01", "funding_page"),
        ],
        "claims": [
            claim("J01.title", "J01", "title", "Data Quality Analyst"),
            claim(
                "J01.salary",
                "J01",
                "salary",
                {
                    "currency": "GBP",
                    "minimum_minor_units": 3104900,
                    "maximum_minor_units": 3779600,
                    "period": "year",
                    "basis": "advertised",
                },
            ),
            claim("J01.r1", "J01", "requirement", "Proficiency in SQL"),
            claim("C01.title", "C01", "title", "Certificate in Data"),
            claim("C01.fee_total", "C01", "fee_total", {"currency": "GBP", "minor_units": 126500}),
            claim("C01.o1", "C01", "syllabus", "including using SQL."),
            claim("F01.programme", "F01", "programme", "Free courses for jobs"),
            claim("F01.rule_age", "F01", "rule_age", {"minimum_age": 19}),
        ],
        "job_postings": [
            {
                **record("job:J01"),
                "source_id": "J01",
                "target_id": "t",
                "vacancy_id": "vacancy:J01",
                "title": "J01.title",
                "employer": {"unknown": "not named"},
                "advertiser": {"unknown": "not stated"},
                "location": {"unknown": "not stated"},
                "work_mode": {"unknown": "not stated"},
                "salary": "J01.salary",
                "date_posted": {"unknown": "not stated"},
                "valid_through": {"unknown": "not stated"},
                "employment_type": {"unknown": "not stated"},
                "description_kind": {"unknown": "not stated"},
                "status": {"unknown": "not stated"},
                "requirement_ids": ["req:J01.1"],
            }
        ],
        "skill_requirements": [
            {
                **record("req:J01.1"),
                "job_posting_id": "job:J01",
                "target_id": "t",
                "skill_id": "pack:t:querying",
                "text": "J01.r1",
                "kind": "skill",
                "importance": "essential",
                "gate": None,
                "required_level": None,
            }
        ],
        "learning_options": [
            {
                **record("option:C01"),
                "source_id": "C01",
                "target_ids": ["t"],
                "title": "C01.title",
                "provider": {"unknown": "not named"},
                "credential": {"unknown": "not stated"},
                "awarding_body": {"unknown": "not stated"},
                "recognising_body": {"unknown": "not stated"},
                "level": {"unknown": "not stated"},
                "delivery_mode": {"unknown": "not stated"},
                "assessment": {"unknown": "not described"},
                "entry_requirements": [],
            }
        ],
        "offerings": [
            {
                **record("offering:C01"),
                "option_id": "option:C01",
                "intake": {"unknown": "no start date"},
                "application_deadline": {"unknown": "none stated"},
                "duration": {"unknown": "not stated"},
                "schedule": {"unknown": "not stated"},
                "fee_total": "C01.fee_total",
                "instalment": {"unknown": "none offered"},
                "wage": {"unknown": "not an apprenticeship"},
                "location": {"unknown": "not stated"},
                "extra_costs": [],
                "funding_conditions": [],
            }
        ],
        "outcomes": [
            {
                **record("outcome:C01.1"),
                "offering_id": "offering:C01",
                "skill_id": "pack:t:querying",
                "level_on_completion": None,
                "evidence_kind": "topic_mention",
                "confidence": "unsupported",
                "source_span": "C01.o1",
                "rubric_version": None,
                "claim_state": "planned_conditional",
            }
        ],
        "funding_instruments": [
            {
                **record("funding:F01"),
                "source_ids": ["F01"],
                "programme": "F01.programme",
                "jurisdiction": "GB-ENG",
                "instrument_kind": "fee_waiver",
                "eligible_costs": {"unknown": "not stated"},
                "rules": ["F01.rule_age"],
                "timing": {"unknown": "not stated"},
                "repayment": {"unknown": "not a loan"},
                "exclusions": [],
                "award_state": "not_assessed",
                "published_on": {"unknown": "not stated"},
                "rules_updated_on": {"unknown": "not stated"},
            }
        ],
    }


def source(source_id: str, kind: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "kind": kind,
        "route": "fetch",
        "url": f"https://www.gov.uk/{source_id.lower()}",
        "final_url": f"https://www.gov.uk/{source_id.lower()}",
        "retrieved_at": "2026-10-29T10:00:00+00:00",
        "http_status": 200,
        "content_type": "text/html",
        "sha256": SHA,
        "rights_class": "govuk",
        "rights_status": "govuk: OGL (read 2026-10-29)",
        "retention": "body",
        "template_family": f"family-{kind}",
        "split": "development",
        "advert_pointer": None,
    }


def claim(claim_id: str, source_id: str, field: str, value: object) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "source_id": source_id,
        "field": field,
        "value": value,
        "span": {"start": 10, "end": 20, "pointer": None},
        "excerpt": "an excerpt",
    }


def record(record_id: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "review_state": "proposed",
        "review": None,
        "as_of": "2026-10-29",
        "facts": [],
    }


def problems(data: dict[str, Any]) -> list[str]:
    return check_pack(parse_pack(data))


@pytest.mark.req("OPTN-10")
def test_a_pack_whose_every_value_is_cited_and_every_record_proposed_has_no_problem() -> None:
    assert problems(minimal()) == []


@pytest.mark.req("OPTN-10")
def test_a_field_citing_a_claim_that_does_not_exist_is_a_problem() -> None:
    data = minimal()
    data["job_postings"][0]["title"] = "J01.missing"

    assert "job:J01.title cites J01.missing, which is not a claim" in problems(data)


@pytest.mark.req("OPTN-10")
def test_a_record_citing_another_source_s_claim_is_a_problem() -> None:
    data = minimal()
    data["job_postings"][0]["title"] = "C01.title"

    found = problems(data)

    assert "job:J01.title cites C01.title, from C01, not from its own source" in found
    assert "claim J01.title is cited by no record" in found  # and its own title is orphaned


@pytest.mark.req("OPTN-10")
@pytest.mark.parametrize(
    "value",
    [
        {"currency": "GBP", "minor_units": 1265.0},
        {"currency": "GBP", "minor_units": -1},
        {"currency": "EUR", "minor_units": 1},
        {"currency": "GBP", "minor_units": 126500, "for": "the course"},
        "£1,265",
    ],
    ids=["float", "negative", "currency", "extra key", "text"],
)
def test_money_is_integer_gbp_minor_units_and_never_negative(value: object) -> None:
    data = minimal()
    data["claims"][4]["value"] = value

    assert problems(data) == ["C01.fee_total is not money"]


@pytest.mark.req("OPTN-10")
def test_a_salary_whose_maximum_is_below_its_minimum_is_a_problem() -> None:
    data = minimal()
    data["claims"][1]["value"]["maximum_minor_units"] = 100

    assert problems(data) == ["J01.salary is not pay"]


@pytest.mark.req("OPTN-10")
@pytest.mark.parametrize(
    ("claim_field", "value", "problem"),
    [
        ("duration", {"typical_months": "6-8"}, "C01.duration is not duration"),
        ("duration", [{"unit": "months", "minimum": "6-8", "maximum": 8, "mode": None}], None),
        ("duration", [{"unit": "months", "minimum": 8, "maximum": 6, "mode": None}], None),
        ("intake", "16 November 2026", "C01.duration is not date"),
        ("schedule", "part time", "C01.duration is not schedule"),
    ],
    ids=["a string range", "a text bound", "a reversed range", "a date in words", "text"],
)
def test_a_value_has_the_one_shape_its_field_declares(
    claim_field: str, value: object, problem: str | None
) -> None:
    data = minimal()
    data["claims"].append(claim("C01.duration", "C01", claim_field, value))
    data["offerings"][0]["duration"] = "C01.duration"

    found = problems(data)

    assert (problem or "C01.duration is not duration") in found


@pytest.mark.req("OPTN-10")
def test_a_record_field_checks_the_shape_of_the_claim_it_cites_whatever_the_claim_is_called() -> (
    None
):
    # Reproduced in 0.1.0 before its re-cut: an offering's intake cited a list of past months
    # held under another field name, so no date check saw it.
    data = minimal()
    data["claims"].append(claim("C01.intakes_stated", "C01", "intakes_stated", ["2026-02"]))
    data["offerings"][0]["intake"] = "C01.intakes_stated"

    assert problems(data) == ["offering:C01.intake cites C01.intakes_stated, which is not date"]


@pytest.mark.req("OPTN-10")
@pytest.mark.parametrize(
    ("value", "problem"),
    [
        ("2026-11-27T23:59:59+00:00", None),
        ("2026-12-31", None),
        ("2026-11-27T23:59:59", "J01.valid_through is not deadline"),  # no UTC offset
        ("27 November 2026", "J01.valid_through is not deadline"),
    ],
    ids=["datetime", "date", "naive", "words"],
)
def test_a_deadline_is_an_iso_date_or_a_datetime_with_its_offset(
    value: str, problem: str | None
) -> None:
    data = minimal()
    data["claims"].append(claim("J01.valid_through", "J01", "valid_through", value))
    data["job_postings"][0]["valid_through"] = "J01.valid_through"

    assert problems(data) == ([problem] if problem else [])


@pytest.mark.req("OPTN-10")
def test_a_structured_value_under_a_text_field_is_a_problem() -> None:
    data = minimal()
    data["claims"][0]["value"] = {"title": "Data Quality Analyst"}

    assert problems(data) == ["J01.title is not text"]


@pytest.mark.req("OUT1-10")
@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"level_on_completion": 2}, "outcome:C01.1 has a level without a rubric version"),
        (
            {"level_on_completion": 2, "rubric_version": "r1"},
            "outcome:C01.1 is unsupported, so its level must be null",
        ),
        (
            {"level_on_completion": 2, "rubric_version": "r1", "confidence": "provisional"},
            "outcome:C01.1 is a topic mention, so its level must be null",
        ),
    ],
    ids=["no rubric", "unsupported", "topic mention"],
)
def test_an_unsupported_outcome_level_stays_null(change: dict[str, object], problem: str) -> None:
    data = minimal()
    data["outcomes"][0].update(change)

    assert problems(data) == [problem]


@pytest.mark.req("OPTN-10")
def test_a_reviewed_record_names_its_reviewer_date_and_session() -> None:
    data = minimal()
    data["job_postings"][0]["review_state"] = "reviewed"

    assert problems(data) == ["job:J01 is reviewed without a review record"]

    data["job_postings"][0]["review"] = {
        "reviewer": "product owner",
        "decided_on": "2026-11-05",
        "session": "session 2",
        "decision": "accepted",
    }
    assert problems(data) == []


@pytest.mark.req("OPTN-08")
@pytest.mark.parametrize(
    ("path", "value", "problem"),
    [
        (("claims", 0, "value"), "fixture:registration", "J01.title holds a fixture: identifier"),
        (
            ("sources", 0, "url"),
            "https://careers.northwind.example/jobs/1",
            "J01 is not a real public page (careers.northwind.example)",
        ),
    ],
    ids=["fixture id", "example host"],
)
def test_nothing_synthetic_enters_the_pack(
    path: tuple[str, int, str], value: str, problem: str
) -> None:
    data = minimal()
    data[path[0]][path[1]][path[2]] = value

    assert problem in problems(data)


@pytest.mark.req("OPTN-08")
def test_a_pack_that_says_it_is_synthetic_does_not_parse() -> None:
    data = minimal()
    data["synthetic"] = True

    with pytest.raises(OptionPackError, match="synthetic"):
        parse_pack(data)


@pytest.mark.req("TEST1-09")
def test_one_template_family_in_both_splits_is_a_problem() -> None:
    data = minimal()
    data["sources"][1]["template_family"] = "family-job_posting"
    data["sources"][1]["split"] = "holdout"

    assert problems(data) == ["template family family-job_posting is in both splits"]


@pytest.mark.req("OPTN-10")
@pytest.mark.parametrize(
    ("span", "problem"),
    [
        ({"start": None, "end": None, "pointer": "/results/0"}, "J01.title: a fetched page"),
        ({"start": 20, "end": 10, "pointer": None}, "a span ends after it starts"),
    ],
    ids=["pointer on a page", "reversed"],
)
def test_a_page_claim_cites_offsets_that_end_after_they_start(
    span: dict[str, object], problem: str
) -> None:
    data = minimal()
    data["claims"][0]["span"] = span

    try:
        found = problems(data)
    except OptionPackError as error:
        found = [str(error)]
    assert any(problem in p for p in found)


@pytest.mark.req("OPTN-10")
def test_a_claim_no_record_uses_is_a_problem() -> None:
    data = minimal()
    data["claims"].append(claim("J01.extra", "J01", "pay_band", "Band 5"))

    assert problems(data) == ["claim J01.extra is cited by no record"]


@pytest.mark.req("OPTN-10")
def test_a_pack_whose_bytes_are_not_its_pin_does_not_load() -> None:
    with pytest.raises(OptionPackError, match="pinned bytes"):
        load_pack("0.1.0", pins={"0.1.0": "0" * 64})
    with pytest.raises(OptionPackError, match="no committed"):
        load_pack("9.9.9")


@pytest.mark.req("OPTN-10", "OPTN-08", "TEST1-09")
def test_the_committed_pack_loads_with_every_record_proposed_and_dated() -> None:
    pack = load_pack("0.1.0")

    assert pack.dated == date(2026, 10, 29)
    kinds = Counter(s.kind.value for s in pack.sources)
    assert kinds == {"job_posting": 20, "course_page": 10, "funding_page": 3}
    records = list(pack.records())
    assert {r.review_state for r in records} == {ReviewState.PROPOSED}
    assert all(r.as_of <= pack.dated for r in records)
    assert {t.persona for t in pack.targets} == {"P01", "P03", "P04", "P05"}  # P02: none
    # Every planned outcome is conditional and, with no rubric yet, has no level (OUT-1).
    assert all(o.level_on_completion is None for o in pack.outcomes)


@pytest.mark.req("TEST1-09", "OPTN-10")
def test_the_corpus_manifest_and_the_pack_record_the_same_pages_and_labels() -> None:
    pack = load_pack("0.1.0")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    slots = {s["id"]: s for s in manifest["slots"]}
    claims_by_slot: dict[str, list[str]] = {}
    for c in pack.claims:
        claims_by_slot.setdefault(c.source_id, []).append(c.claim_id)

    assert manifest["option_pack"]["sha256"] == PINS["0.1.0"]
    assert set(slots) == {s.source_id for s in pack.sources}
    for source in pack.sources:
        slot = slots[source.source_id]
        assert slot["status"] == "collected"
        for key in ("url", "sha256", "rights_status", "template_family", "retention"):
            assert slot[key] == getattr(source, key), (source.source_id, key)
        assert slot["split"] == source.split.value
        assert datetime.fromisoformat(slot["retrieved_at"]) == source.retrieved_at
        assert slot["labels"]["claims"] == claims_by_slot[source.source_id]
        assert slot["label_review"].startswith("not run")


@pytest.mark.req("OPTN-10")
def test_the_format_exports_a_json_schema_that_states_every_value_shape() -> None:
    exported = schema()

    assert exported["title"] == "Pack"
    assert "claims" in exported["properties"]
    shapes = exported["x-value-shapes"]
    assert {"money", "pay", "date", "deadline", "duration", "schedule", "instalment"} <= set(shapes)
    assert exported["x-record-field-shapes"]["Offering.duration"] == "duration"
    assert exported["x-claim-field-shapes"]["valid_through"] == "deadline"


@pytest.mark.req("OPTN-10")
def test_every_committed_version_is_written_in_the_format_s_own_canonical_form() -> None:
    for version in PINS:
        text = pack_path(version).read_text(encoding="utf-8")

        assert dump_pack(load_pack(version)) == text


@pytest.mark.req("OPTN-10")
def test_identifiers_are_unique() -> None:
    data = minimal()
    data["claims"].append(copy.deepcopy(data["claims"][0]))

    with pytest.raises(OptionPackError, match=r"J01\.title"):
        parse_pack(data)
