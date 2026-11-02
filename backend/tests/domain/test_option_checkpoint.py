"""The Options chapter's review checkpoint, backend half (Task 12b; S5.3, S5.7; spec section 10,
"Option review checkpoint"; plan v1.5 and v1.6): for each option the facts the route search
lacks, named; the person's own figures filling only what is missing and qualifying every
route resting on them; options the person adds, `proposed` and dated with their source; entry
requirements beside the person's qualifications, an expected one never met; each age rule
beside its scheme, never applied; and the model's bounds never cut silently. P01's acceptance
at the domain level: with the missing facts supplied, computed routes; without, what is
missing named, never "no route". The person's figures are synthetic."""

import uuid
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from careerwright.capability.adverts import AdvertSpan
from careerwright.capability.commands import committed_data
from careerwright.capability.matrix import build_matrix
from careerwright.capability.skills import EntryStanding, PersonQualification
from careerwright.money import Money
from careerwright.planning.catalogue import (
    ActionKind,
    Catalogue,
    Citation,
    CitationBasis,
    EligibilityStatus,
    Fact,
    RecordState,
    SuppliedFact,
)
from careerwright.planning.checker import FindingCode, FindingKind, RouteQualification, check_route
from careerwright.planning.checkpoint import (
    entry_requirements,
    expected_entry,
    scope,
    target_checkpoint,
)
from careerwright.planning.compiler import PlanningInputs, ReadinessBasis, compile_input
from careerwright.planning.figures import (
    MissingFact,
    OfferingFigures,
    StartBasis,
    SuppliedStart,
    refused,
    variant_missing,
    with_figures,
)
from careerwright.planning.inputs import (
    BaselineInput,
    BaselineKind,
    ContinuationInput,
    PlanningInputsIn,
    SpendingCaps,
    VariantInputs,
    as_submitted,
    prepare,
    stamped,
    with_answers,
)
from careerwright.planning.own_options import (
    OWN_LABEL,
    OwnOptionInput,
    OwnWords,
    PastedText,
    beside,
    check_option,
    own_records,
    stamped_options,
)
from careerwright.planning.pack import pack_catalogue
from careerwright.planning.search import M0SearchLimits, Outcome, SearchResult, search_routes
from careerwright.profile.document import QualificationStatus
from tests.support.capability import self_report
from tests.support.planning import catalogue_of, option

DATA = committed_data()  # the reviewed school-leaver pack 0.4.0, reference 0.2.0 (Task 12b)
TARGET = "data-quality-analyst-manchester"
FULL_TIME = "offering:C01#full_time"
CONDITIONS = (
    "eligibility_area",
    "eligibility_age",
    "eligibility_earnings",
    "eligibility_no_other_funded_training",
)
ACTOR = uuid.UUID("00000000-0000-4000-8000-000000000001")
NOW = datetime(2026, 11, 1, 12, tzinfo=UTC)
CITED = Citation(basis=CitationBasis.PERSON, locator="planning inputs, version 1")
P01_CAPS = SpendingCaps(
    direct_spend_cap=Money(minor_units=150000, currency="GBP"),
    monthly_payment_cap=Money(minor_units=150000, currency="GBP"),
)


def gbp(minor: int) -> Money:
    return Money(minor_units=minor, currency="GBP")


def p01(**changes: object) -> PlanningInputsIn:
    """P01's figures (synthetic), every input a solve needs stated."""
    return PlanningInputsIn.model_validate(
        {
            "objective_basis": "economic",
            "baseline": BaselineInput(kind=BaselineKind.CURRENT_ROLE, net_income=gbp(200000)),
            "continuation": ContinuationInput(hours_per_week=30, net_income=gbp(200000)),
            "opening_cash": gbp(600000),
            "living_costs": gbp(100000),
            "reserve": gbp(50000),
            "weekly_availability": 40,
            "commitments": [],
            "existing_debts": [],
            "scenario_delay_months": 2,
            "work_rights": "held",
            **changes,
        }
    )


C01_FIGURES = OfferingFigures(
    offering_id=FULL_TIME,
    start=SuppliedStart(on=date(2027, 1, 4), basis=StartBasis.OWN_FIGURE),
    weekly_hours=9,
    cost=gbp(0),
)
C01_ANSWERS = VariantInputs(
    variant_id=FULL_TIME,
    condition_statuses={c: EligibilityStatus.CONFIRMED for c in CONDITIONS},
)


def data_target() -> Catalogue:
    return pack_catalogue(DATA.pack, TARGET)


def search(
    inputs: PlanningInputsIn, *, ready: bool, catalogue: Catalogue | None = None
) -> SearchResult:
    """The data target's route search on P01's figures; `ready`: synthetic evidence at each
    required row's level, so readiness is reached from the start."""
    target = next(t for t in DATA.pack.targets if t.target_id == TARGET)
    matrix = build_matrix(
        target.title,
        pack=DATA.pack,
        reference=DATA.reference,
        pack_target=target,
        occupation=None,
        exemplars=0,
        synthetic=True,
    )
    evidence = [
        self_report(r.subject, r.required_level, r.rubric.version_id)
        for r in matrix.rows
        if r.required and r.rubric is not None
    ]
    basis = ReadinessBasis(
        matrix=matrix,
        evidence=evidence if ready else [],
        statements=[],
        outcomes=list(DATA.outcomes),
        evidence_version=1,
    )
    document = stamped(inputs, previous=None, by=ACTOR, at=NOW)
    prepared = prepare(
        document,
        catalogue or data_target(),
        caps=P01_CAPS,
        planning_start=date(2026, 12, 1),
        horizon_months=24,
        synthetic=True,
        version=1,
    )
    return search_routes(compile_input(prepared.inputs, prepared.catalogue, readiness=basis))


# --- the facts the route search lacks ----------------------------------------------------


@pytest.mark.req("OPTN-13", "OPTN-11")
def test_the_checkpoint_names_for_each_pack_option_the_facts_the_search_lacks() -> None:
    catalogue = data_target()
    concepts = {c.concept_id: c for c in catalogue.concepts}
    offerings = {o.offering_id: o for o in catalogue.offerings}

    missing = {
        v.variant_id: variant_missing(
            concepts[offerings[v.offering_id].concept_id], offerings[v.offering_id], v
        )
        for v in catalogue.variants
    }

    # C01 states one exact length (10 weeks full time), so only its start is missing of its
    # dates; its fee is £0 only for an eligible learner, so its cost is unknown.
    assert missing[FULL_TIME] == [
        MissingFact.START_DATE,
        MissingFact.WEEKLY_HOURS,
        MissingFact.COST,
    ]
    # C04 states a typical duration (never a bound): its finish is missing even with a start.
    # Paid in full its cost is known; by instalments "from £69.52 a month", with no count, not.
    assert missing["offering:C04~pay-in-full"] == [
        MissingFact.START_DATE,
        MissingFact.FINISH_DATE,
        MissingFact.WEEKLY_HOURS,
    ]
    assert MissingFact.COST in missing["offering:C04~instalments"]


@pytest.mark.req("OPTN-13", "OPTN-09")
def test_a_supplied_figure_fills_only_a_missing_fact_and_is_labelled_the_person_s() -> None:
    c01 = next(o for o in data_target().offerings if o.offering_id == FULL_TIME)

    filled = with_figures(c01, C01_FIGURES, CITED)

    assert (filled.start, filled.finish) == (date(2027, 1, 4), date(2027, 3, 14))  # 10 weeks
    assert filled.weekly_hours == 9
    assert filled.supplied == [
        SuppliedFact.START_DATE,
        SuppliedFact.WEEKLY_HOURS,
        SuppliedFact.COST,
    ]  # the finish is the page's length from their start: not their figure
    [plan] = filled.payment_plans
    assert plan.unknown is None
    assert [(p.kind, p.amount, p.month_offset, p.cited) for p in plan.payments] == [
        ("fee", gbp(0), 0, CITED)
    ]
    assert "start" not in filled.unknown
    assert "weekly_hours" not in filled.unknown
    # A figure for a fact the page states is refused at the write, and never applied.
    c07 = next(
        o
        for o in pack_catalogue(DATA.pack, "it-support-technician-bristol").offerings
        if o.offering_id == "offering:C07"
    )
    restart = OfferingFigures(
        offering_id="offering:C07",
        start=SuppliedStart(on=date(2027, 2, 1), basis=StartBasis.OWN_FIGURE),
    )
    assert refused(c07, restart) == "not_missing"
    assert with_figures(c07, restart, CITED).start == date(2026, 11, 16)
    assert refused(c01, OfferingFigures(offering_id=FULL_TIME, finish=date(2027, 5, 1))) == (
        "not_missing"  # its length gives the finish from a start
    )


@pytest.mark.req("OPTN-13")
def test_a_stated_intake_is_chosen_only_from_the_months_its_page_states() -> None:
    c06 = next(
        o
        for o in pack_catalogue(DATA.pack, "bookkeeping-assistant-leeds").offerings
        if o.offering_id == "offering:C06"
    )
    stated = SuppliedStart(on=date(2026, 3, 1), basis=StartBasis.STATED_INTAKE)
    other = SuppliedStart(on=date(2027, 3, 1), basis=StartBasis.STATED_INTAKE)

    assert c06.stated_intakes == [date(2026, 2, 1), date(2026, 3, 1)]
    assert refused(c06, OfferingFigures(offering_id="offering:C06", start=stated)) is None
    assert refused(c06, OfferingFigures(offering_id="offering:C06", start=other)) == (
        "not_a_stated_intake"
    )
    # C06 states one year: the chosen intake gives its finish.
    filled = with_figures(c06, OfferingFigures(offering_id="offering:C06", start=stated), CITED)
    assert filled.finish == date(2027, 2, 28)


def test_figures_supply_something_and_never_a_finish_before_their_start() -> None:
    with pytest.raises(ValidationError, match="at least one fact"):
        OfferingFigures(offering_id=FULL_TIME)
    with pytest.raises(ValidationError, match="not before its start"):
        OfferingFigures(
            offering_id=FULL_TIME,
            start=SuppliedStart(on=date(2027, 2, 1), basis=StartBasis.OWN_FIGURE),
            finish=date(2027, 1, 1),
        )


# --- P01's acceptance, at the domain level -----------------------------------------------


@pytest.mark.req("OPTN-13", "OPTN-09", "OPT1-07", "OPTN-11")
def test_p01_with_the_missing_facts_supplied_gets_computed_routes_each_qualified() -> None:
    result = search(p01(offering_figures=[C01_FIGURES], variants=[C01_ANSWERS]), ready=True)

    assert result.outcome is Outcome.ROUTES_FOUND
    routes = {tuple(s.route): s for s in result.schedules}
    assert set(routes) == {(), (FULL_TIME,)}
    # The route through C01 rests on the person's figures: qualified, never unqualified.
    assert RouteQualification.SUPPLIED_FIGURES in routes[(FULL_TIME,)].qualifications
    assert RouteQualification.SUPPLIED_FIGURES not in routes[()].qualifications
    assert routes[(FULL_TIME,)].verdict.value == "affordable_and_feasible_with_qualifications"


@pytest.mark.req("OPTN-13", "OPT1-07")
def test_p01_without_the_missing_facts_names_what_is_missing_never_no_route() -> None:
    result = search(p01(), ready=True)

    assert result.outcome is not Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    set_aside = {s.variant_id: s for s in result.set_aside}
    assert set(set_aside) == {
        FULL_TIME,
        "offering:C01#part_time",
        "offering:C04~pay-in-full",
        "offering:C04~instalments",
    }
    assert {FindingCode.DATES_UNKNOWN, FindingCode.COST_UNKNOWN, FindingCode.WORKLOAD_UNKNOWN} <= (
        set(set_aside[FULL_TIME].unresolved)
    )
    # With no evidence the milestone is not assessable: unresolved, still never "no route".
    assert search(p01(), ready=False).outcome is Outcome.UNRESOLVED


# --- options the person adds -------------------------------------------------------------

PAGE = "Evening data course 🎓 Bright College. Starts 4 January 2027, £450 in full."
TEXT_ID = uuid.UUID("00000000-0000-4000-8000-00000000000a")


def added(**changes: object) -> OwnOptionInput:
    return OwnOptionInput.model_validate(
        {
            "option_id": "evening-course",
            "target": "Data quality analyst",
            "text_id": TEXT_ID,
            # "Bright College" sits after a two-unit emoji: UTF-16 offsets, as a browser counts.
            "title": OwnWords(span=AdvertSpan(start=0, end=19)),
            "provider": OwnWords(span=AdvertSpan(start=23, end=37)),
            "start": date(2027, 1, 4),
            "finish": date(2027, 3, 26),
            "weekly_hours": 6,
            "cost": gbp(45000),
            "cited": {"cost": AdvertSpan(start=62, end=66)},
            **changes,
        }
    )


TEXT = PastedText(PAGE, "a" * 64)


@pytest.mark.req("OPTN-03", "OPTN-08", "OPTN-09")
def test_an_added_option_is_the_person_s_proposed_dated_record_with_its_source() -> None:
    [option_] = stamped_options([added()], [], by=ACTOR, at=NOW)

    concept, offering, variant = own_records(option_, TEXT)

    assert check_option(added(), TEXT) is None
    assert (concept.title, concept.provider) == ("Evening data course", "Bright College")
    assert concept.added_by_person
    assert concept.review_state is RecordState.PROPOSED
    assert offering.review_state is RecordState.PROPOSED
    assert (concept.as_of, offering.as_of) == (NOW.date(), NOW.date())  # dated
    assert concept.cited is not None
    assert concept.cited.source_id == str(added().text_id)  # its source: their pasted text
    assert concept.cited.locator == "utf-16 offsets 0-19"
    [fee] = offering.payment_plans[0].payments
    assert fee.amount == gbp(45000)
    assert fee.cited.excerpt == "£450"
    assert variant.variant_id == "own:evening-course"
    # Unchanged, it keeps its date; changed, it is dated again.
    assert stamped_options([added()], [option_], by=ACTOR, at=datetime.now(UTC)) == [option_]
    [moved] = stamped_options([added(weekly_hours=7)], [option_], by=ACTOR, at=datetime.now(UTC))
    assert moved.recorded_at > NOW


@pytest.mark.req("OPTN-03")
def test_an_added_option_s_spans_must_fit_its_pasted_text() -> None:
    inside_the_emoji = added(title=OwnWords(span=AdvertSpan(start=0, end=21)))
    past_the_end = added(provider=OwnWords(span=AdvertSpan(start=70, end=200)))

    assert check_option(inside_the_emoji, TEXT) == "span_splits_character"
    assert check_option(past_the_end, TEXT) == "span_outside_text"
    assert check_option(added(), None) == "text_not_found"
    typed = added(text_id=None, title=OwnWords(typed="My course"), provider=None, cited={})
    assert check_option(typed, None) is None
    with pytest.raises(ValidationError, match="name the text"):
        added(text_id=None)
    with pytest.raises(ValidationError, match="typed or chosen"):
        OwnWords(typed="x", span=AdvertSpan(start=0, end=1))


@pytest.mark.req("OPTN-03", "OPTN-09", "BND1-07")
def test_a_route_through_an_added_option_is_qualified_and_one_outside_the_pack_is_its_own() -> None:
    [option_] = stamped_options([added()], [], by=ACTOR, at=NOW)
    merged = beside(data_target(), [option_], {TEXT_ID: TEXT})
    alone = beside(None, [option_], {TEXT_ID: TEXT})

    assert merged is not None
    assert alone is not None
    assert merged.label.name.endswith("0.4.0")  # the pack's label, its records beside it
    assert alone.label.name == OWN_LABEL
    assert alone.label.dated == NOW.date()
    assert beside(None, [], {}) is None  # nothing at all is never an empty catalogue
    result = search(p01(), ready=True, catalogue=merged)
    routes = {tuple(s.route): s for s in result.schedules}
    assert ("own:evening-course",) in routes
    qualifications = routes[("own:evening-course",)].qualifications
    assert RouteQualification.OWN_OPTIONS in qualifications
    assert RouteQualification.PROPOSED_RECORDS in qualifications


@pytest.mark.req("OPTN-03")
def test_an_added_option_with_nothing_given_stays_unknown_never_zero() -> None:
    bare = added(
        text_id=None,
        title=OwnWords(typed="A course"),
        provider=None,
        start=None,
        finish=None,
        weekly_hours=None,
        cost=None,
        cited={},
    )
    [option_] = stamped_options([bare], [], by=ACTOR, at=NOW)
    concept, offering, variant = own_records(option_, None)

    assert variant_missing(concept, offering, variant) == [
        MissingFact.START_DATE,
        MissingFact.FINISH_DATE,
        MissingFact.WEEKLY_HOURS,
        MissingFact.COST,
    ]
    assert offering.payment_plans[0].unknown == "not given yet"


def test_a_stored_document_round_trips_its_added_options_and_figures() -> None:
    submitted = p01(own_options=[added()], offering_figures=[C01_FIGURES], excluded_variants=["x"])
    document = stamped(submitted, previous=None, by=ACTOR, at=NOW)

    assert as_submitted(document) == submitted
    assert document.own_options[0].recorded_at == NOW


# --- entry requirements and qualifications (plan v1.6) -----------------------------------


def entry_case(met: bool | None) -> Catalogue:
    concept, offering, variant = option("t-level", start=date(2027, 9, 1), finish=date(2029, 7, 31))
    concept = concept.model_copy(
        update={"entry_requirements": [Fact(field="entry_requirement", value="GCSE maths")]}
    )
    variant = variant.model_copy(update={"entry_requirements_met": met})
    return catalogue_of((concept, offering, variant))


EXPECTED = [PersonQualification(name="GCSE maths", status=QualificationStatus.EXPECTED)]
ACHIEVED = [PersonQualification(name="GCSE maths", status=QualificationStatus.ACHIEVED)]
KEYS = {"GCSE maths": "gcse math"}


@pytest.mark.req("PROF-13", "OPTN-13")
def test_an_expected_qualification_reads_if_you_get_your_grades_and_is_never_met() -> None:
    catalogue = entry_case(met=True)  # the person says they meet it
    [concept] = catalogue.concepts

    [requirement] = entry_requirements(concept, EXPECTED, KEYS)
    expected = expected_entry(catalogue, EXPECTED, KEYS)
    answered = with_answers(catalogue, p01(), CITED, expected_entry=expected)

    assert [q.standing for q in requirement.qualifications] == [EntryStanding.EXPECTED_NOT_MET]
    assert expected == {concept.concept_id}
    assert answered.variants[0].entry_expected is True
    check = check_route(compile_input(prepare_inputs(), answered), ["t-level"])
    codes = {f.code: f.kind for f in check.findings}
    assert codes[FindingCode.ENTRY_REQUIREMENTS_EXPECTED] is FindingKind.UNRESOLVED
    assert check.feasibility.value == "unresolved"
    # Achieved, as the person states it: named beside it, and nothing forces it unresolved.
    assert expected_entry(catalogue, ACHIEVED, KEYS) == frozenset()


@pytest.mark.req("PROF-13")
def test_the_person_s_own_no_stays_its_own_finding_never_expected() -> None:
    catalogue = entry_case(met=False)
    answered = with_answers(
        catalogue, p01(), CITED, expected_entry=expected_entry(catalogue, EXPECTED, KEYS)
    )

    codes = {
        f.code for f in check_route(compile_input(prepare_inputs(), answered), ["t-level"]).findings
    }

    assert FindingCode.ENTRY_REQUIREMENTS_NOT_MET in codes
    assert FindingCode.ENTRY_REQUIREMENTS_EXPECTED not in codes


def prepare_inputs() -> PlanningInputs:
    """P01's figures on the monthly grid, for a constructed catalogue."""
    document = stamped(p01(), previous=None, by=ACTOR, at=NOW)
    return prepare(
        document,
        entry_case(None),
        caps=P01_CAPS,
        planning_start=date(2027, 1, 1),
        horizon_months=24,
        synthetic=True,
        version=1,
    ).inputs


# --- age rules, schemes and the checkpoint ------------------------------------------------


@pytest.mark.req("OPTN-15", "FUNDING-05")
def test_each_scheme_s_age_rule_is_beside_it_and_never_applied() -> None:
    catalogue = data_target()
    found = target_checkpoint(
        target_title="Data quality analyst",
        pack_target_id=TARGET,
        note=None,
        answered=catalogue,
        retained=catalogue,
        left_out=frozenset(),
        qualifications=[],
        keys={},
        limits=M0SearchLimits(),
    )

    schemes = {s.instrument_id: s for s in found.schemes}
    assert [(r.field, r.value, r.applied) for r in schemes["funding:F10"].age_rules] == [
        ("rule_age", {"minimum_age": 16, "on": "31 August 2026"}, False),
        ("rule_age_band", "under 19 on 31 August 2026", False),
        (
            "rule_age_exception",
            "19 or over: only if continuing a course started aged 16 to 18 (or with an EHC plan)",
            False,
        ),
    ]
    c01 = next(o for o in found.options if o.variant_id == FULL_TIME)
    assert [(r.field, r.applied) for r in c01.age_rules] == [("eligibility_age", False)]
    assert [c.status for c in c01.eligibility_conditions] == [None] * 4  # not answered
    assert found.reviewed_options == 0  # C01 and C04 are proposed: the target says so
    assert found.label is not None
    assert found.label.dated == date(2026, 11, 1)


@pytest.mark.req("OUT1-09", "OUT1-04")
def test_each_option_shows_its_planned_outcomes_with_the_person_s_decision_on_each() -> None:
    catalogue = data_target()
    found = target_checkpoint(
        target_title="Data quality analyst",
        pack_target_id=TARGET,
        note=None,
        answered=catalogue,
        retained=catalogue,
        left_out=frozenset(),
        qualifications=[],
        keys={},
        limits=M0SearchLimits(),
        outcomes=DATA.outcomes,
        decisions={"outcome:C01.1": "accept"},
    )

    # Both ways of taking C01 carry the course's outcomes (`Offering.outcomes_from`).
    for variant_id in (FULL_TIME, "offering:C01#part_time"):
        c01 = next(o for o in found.options if o.variant_id == variant_id)
        assert [(o.outcome_id, o.review_state.value, o.decision) for o in c01.outcomes] == [
            ("outcome:C01.1", "proposed", "accept"),
            ("outcome:C01.2", "proposed", None),
            ("outcome:C01.3", "proposed", None),
        ]


# --- never truncate silently --------------------------------------------------------------


@pytest.mark.req("OPTN-06", "LIMITS-05")
def test_over_24_options_or_two_starts_asks_to_retain_variants_with_the_counts() -> None:
    many = catalogue_of(*(option(f"o{n}") for n in range(25)))
    three_starts = catalogue_of(*(option(f"s{n}", concept="shared") for n in range(3)))
    limits = M0SearchLimits()

    over = scope(many, limits)
    starts = scope(three_starts, limits)

    assert (over.code, over.concepts, over.max_concepts) == ("retain_variants", 25, 24)
    assert (starts.code, starts.most_starts, starts.max_starts) == ("retain_variants", 3, 2)
    assert [(c.concept_id, c.starts) for c in starts.over_starts] == [("concept:shared", 3)]
    # Leaving options out (the person's choice) brings it inside the bounds.
    kept = with_answers(three_starts, p01(excluded_variants=["s2"]), CITED)
    assert scope(kept, limits).code is None
    assert [v.variant_id for v in kept.variants] == ["s0", "s1"]
    assert scope(None, limits).concepts == 0


# --- someone not working (plan v1.6) ------------------------------------------------------


@pytest.mark.req("OPTN-15")
def test_staying_in_education_and_not_working_are_stated_figures_never_unknown() -> None:
    # A school leaver living at home (synthetic): no job, no pay, no rent, a little saved.
    inputs = p01(
        baseline=BaselineInput(kind=BaselineKind.STAYING_IN_EDUCATION, net_income=gbp(0)),
        continuation=ContinuationInput(hours_per_week=0, net_income=gbp(0)),
        living_costs=gbp(0),
        opening_cash=gbp(60000),
        reserve=gbp(10000),
    )

    result = search(inputs, ready=True)

    assert result.blocking_inputs == []  # "0 hours, £0" is an answer, not a missing input
    assert result.starting_violations == []
    assert result.outcome is Outcome.ROUTES_FOUND
    [empty] = [s for s in result.schedules if s.route == []]
    assert empty.economic_cost is not None  # a known zero, stated: never an unknown
    assert empty.economic_cost.minor_units == 0


def test_an_option_kind_is_a_course_or_an_apprenticeship() -> None:
    with pytest.raises(ValidationError):
        added(kind=ActionKind.WORK)
