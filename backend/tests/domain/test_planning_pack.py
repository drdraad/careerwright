"""The option pack's LearningOption, Offering and FundingInstrument records load through the
planning catalogue (S5.1, S5.2; ADR 0011 consequences): concepts apart from dated offerings,
the composite apprenticeship, payment plans as the pages state them, every consequential
field cited beside its span or unknown with the page's reason, and every record `proposed`
as the pack has it (OPTN-09, R9)."""

from datetime import date

import pytest

from careerwright.catalogue.option_pack import load_pack
from careerwright.planning.catalogue import (
    ActionConcept,
    ActionKind,
    Catalogue,
    CitationBasis,
    Fact,
    FundingInstrument,
    InstrumentKind,
    Offering,
    RecordState,
    Variant,
)
from careerwright.planning.pack import pack_catalogue

PACK = load_pack("0.1.0")
TARGETS = [t.target_id for t in PACK.targets]
P01 = "data-quality-analyst-manchester"


def catalogue(target_id: str) -> Catalogue:
    return pack_catalogue(PACK, target_id)


def offering(found: Catalogue, offering_id: str) -> Offering:
    return next(o for o in found.offerings if o.offering_id == offering_id)


def fact(facts: list[Fact], field: str) -> Fact:
    return next(f for f in facts if f.field == field)


@pytest.mark.req("OPTN-01", "OPTN-10")
@pytest.mark.parametrize("target_id", TARGETS)
def test_each_target_s_options_load_as_concepts_apart_from_their_dated_offerings(
    target_id: str,
) -> None:
    found = catalogue(target_id)
    options = [o for o in PACK.learning_options if target_id in o.target_ids]

    assert sorted(c.concept_id for c in found.concepts) == sorted(o.record_id for o in options)
    concepts = {c.concept_id for c in found.concepts}
    assert all(o.concept_id in concepts for o in found.offerings)
    assert found.label.name == "nessa-england-option-pack 0.1.0"
    assert found.label.dated == PACK.dated
    assert not found.label.synthetic
    # Every record stays as the pack has it: proposed, dated by its evidence, never synthetic.
    records: list[ActionConcept | Offering | FundingInstrument] = [
        *found.concepts,
        *found.offerings,
        *found.instruments,
    ]
    assert {r.review_state for r in records} == {RecordState.PROPOSED}
    assert all(r.as_of == date(2026, 10, 29) for r in records)
    assert not any(c.synthetic for c in found.concepts)
    assert not any(o.synthetic for o in found.offerings)


@pytest.mark.req("OPTN-01", "TIME1-01", "TIME-04")
def test_an_offering_keeps_its_stated_dates_and_a_finish_only_from_an_exact_duration() -> None:
    it = catalogue("it-support-technician-bristol")
    nurse = catalogue("registered-nurse-manchester")
    books = catalogue("bookkeeping-assistant-leeds")

    c07 = offering(it, "offering:C07")  # 16 November 2026, 12 weeks
    assert (c07.start, c07.finish) == (date(2026, 11, 16), date(2027, 2, 7))
    c08 = offering(nurse, "offering:C08")  # September 2027, the month only
    assert c08.start == date(2027, 9, 1)
    intake = fact(c08.facts, "intake")
    assert intake.value == "2027-09"
    assert intake.note is not None
    assert "month only" in intake.note
    c09 = offering(books, "offering:C09")  # 4 January 2027 for 18 months
    assert (c09.start, c09.finish) == (date(2027, 1, 4), date(2028, 7, 3))
    # Typical is never a bound, hours give no pace, and two stated durations disagree.
    c04 = offering(catalogue(P01), "offering:C04")
    assert c04.finish is None
    assert "typical" in c04.unknown["finish"]
    assert offering(nurse, "offering:C03").finish is None
    assert offering(books, "offering:C02").finish is None


@pytest.mark.req("OPTN-01", "TIME1-04")
def test_each_way_of_taking_a_course_is_its_own_offering_with_its_own_outcomes() -> None:
    found = catalogue(P01)
    c01 = [o for o in found.offerings if o.concept_id == "option:C01"]

    assert [o.offering_id for o in c01] == [
        "offering:C01#full_time",
        "offering:C01#part_time",
    ]
    assert all(o.outcomes_from == "offering:C01" for o in c01)
    stated = PACK.claim("C01.duration").value
    assert isinstance(stated, list)
    assert [fact(o.facts, "duration").value for o in c01] == [[part] for part in stated]
    assert all(o.weekly_hours is None for o in c01)  # no weekly hours or timetable stated


@pytest.mark.req("OPTN-01", "FIN1-02")
def test_payment_plans_are_what_the_pages_state_and_unknown_is_never_zero() -> None:
    c04 = offering(catalogue(P01), "offering:C04")
    full, instalments = c04.payment_plans

    assert [(p.kind, p.amount.minor_units, p.month_offset) for p in full.payments] == [
        ("fee", 299500, 0)
    ]
    assert full.payments[0].cited.claim_id == "C04.fee_total"
    assert instalments.recurring is not None
    assert (instalments.recurring.amount.minor_units, instalments.recurring.at_least) == (
        6952,
        True,
    )
    assert instalments.recurring.count is None
    assert instalments.recurring.total_minor is None
    c01 = offering(catalogue(P01), "offering:C01#full_time")
    [unknown] = c01.payment_plans
    assert unknown.payments == []
    assert unknown.unknown is not None
    assert "not eligible" in unknown.unknown  # the claim's own reading of "fully funded"
    c10 = offering(catalogue("it-support-technician-bristol"), "offering:C10")
    [c10_full] = c10.payment_plans  # three payments, their amounts not stated: no plan
    assert [(p.kind, p.amount.minor_units) for p in c10_full.payments] == [("fee", 29500)]
    assert c10_full.unknown is not None
    assert "exam" in c10_full.unknown
    c03 = offering(catalogue("registered-nurse-manchester"), "offering:C03")
    assert [(p.kind, p.amount.minor_units) for p in c03.payment_plans[0].payments] == [
        ("fee", 1900),
        ("extra", 1399),
    ]


@pytest.mark.req("OPTN-02", "OPTN-04", "FIN1-04")
def test_an_apprenticeship_is_one_composite_action_with_its_wage_hours_and_training() -> None:
    found = catalogue("bookkeeping-assistant-leeds")
    [concept] = [c for c in found.concepts if c.concept_id == "option:C09"]
    c09 = offering(found, "offering:C09")

    assert concept.kind is ActionKind.APPRENTICESHIP
    assert [o.offering_id for o in found.offerings if o.concept_id == "option:C09"] == [
        "offering:C09"
    ]
    assert c09.weekly_hours == 35  # its work and its training, one envelope
    assert c09.offer_gate is not None
    assert not c09.offer_gate.accepted  # wages and experience only from an accepted offer
    assert c09.application_deadline == date(2026, 11, 30)
    assert c09.application_gate == "admission:offering:C09"
    wage = fact(c09.facts, "wage")
    assert wage.value == PACK.claim("C09.wage").value  # advertised gross: never a net income
    assert wage.cited is not None
    assert wage.cited.claim_id == "C09.wage"
    assert fact(concept.facts, "credential").value == (
        "AAT Level 3 Diploma in Accounting (within the apprenticeship)"
    )


@pytest.mark.req("OPTN-01", "TEST1-14")
@pytest.mark.parametrize("target_id", TARGETS)
def test_every_consequential_field_is_cited_beside_its_span_or_says_why_it_is_unknown(
    target_id: str,
) -> None:
    found = catalogue(target_id)
    claims = {c.claim_id: c for c in PACK.claims}
    sources = {s.source_id: s for s in PACK.sources}
    facts = [f for o in found.offerings for f in o.facts]
    facts += [f for c in found.concepts for f in c.facts]

    for item in facts:
        if item.unknown is not None and item.cited is None:
            continue  # the pack's own reason, with no span to cite
        assert item.cited is not None
        assert item.cited.basis is CitationBasis.SOURCE
        claim = claims[item.cited.claim_id or ""]
        assert item.cited.excerpt == claim.excerpt
        assert item.cited.source_hash == sources[claim.source_id].sha256
        assert item.cited.locator is not None
    names = {f.field for o in found.offerings for f in o.facts}
    assert {"intake", "duration", "schedule", "fee_total", "instalment"} <= names


@pytest.mark.req("OPTN-05")
def test_a_provider_s_employment_outcome_marketing_stays_an_unverified_claim() -> None:
    [concept] = [c for c in catalogue(P01).concepts if c.concept_id == "option:C04"]
    claim = fact(concept.facts, "provider_outcome_claim")

    assert claim.value == "98% of students secure a role upon graduation"
    assert claim.note is not None
    assert "unverified" in claim.note


@pytest.mark.req("FUNDING-04", "FUNDING-05", "OPTN-10")
def test_the_funding_pages_load_as_instruments_never_as_a_person_s_award() -> None:
    found = catalogue(P01)
    kinds = {i.instrument_id: i.kind for i in found.instruments}

    assert kinds == {
        "funding:F01": InstrumentKind.FEE_WAIVER,
        "funding:F02": InstrumentKind.LOAN,  # information to verify, never planned
        "funding:F03": InstrumentKind.PROGRAMME,
    }
    f01 = next(i for i in found.instruments if i.instrument_id == "funding:F01")
    assert {r.field for r in f01.rules} >= {"rule_age", "rule_earnings"}
    assert all(r.cited is not None for r in f01.rules)
    c01 = offering(found, "offering:C01#full_time")
    assert {f.field for f in c01.facts} >= {"funding_route", "eligibility_earnings"}
    assert all(v.supports == [] for v in found.variants)  # no status without the person


@pytest.mark.req("OPTN-03", "OPTN-09")
def test_what_the_person_has_not_confirmed_is_served_as_not_yet_confirmed() -> None:
    found = catalogue("bookkeeping-assistant-leeds")  # C02, C05, C06, C09 state entry rules

    # Unknown is never ineligible: no person has said whether they meet the requirements.
    assert {v.entry_requirements_met for v in found.variants} == {None}
    properties = Variant.model_json_schema()["properties"]
    assert "none confirmed yet" in properties["supports"]["description"]
    assert "not yet confirmed" in properties["entry_requirements_met"]["description"]
