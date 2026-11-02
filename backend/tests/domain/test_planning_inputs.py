"""The person's planning inputs as they are stored, and as the monthly model reads them (Task
12a; ADR 0013 decision 11 and its amendment of 2026-10-31; ADR 0012 decision 11). Every input
is the person's own: unknown money is null, never 0; a missing input a solve needs is named,
never filled; an unasked limit leaves every route unresolved; and an answer about an option
reaches only that option's variant."""

import uuid
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from careerwright.capability.commands import committed_data
from careerwright.capability.outcomes import EvidenceKind, OutcomeReview, Provenance
from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.money import Money
from careerwright.planning.catalogue import (
    ActionKind,
    AwardState,
    Catalogue,
    CitationBasis,
    EligibilityStatus,
    Fact,
    InstrumentKind,
    OfferGate,
    RecordState,
    WorkPatternKind,
)
from careerwright.planning.checker import Feasibility, FindingCode, RouteCheck, check_route
from careerwright.planning.compiler import WorkRights, compile_input
from careerwright.planning.inputs import (
    BaselineInput,
    BaselineKind,
    CommitmentInput,
    CommitmentKind,
    ContinuationInput,
    DebtInput,
    NeededInput,
    NeedEffect,
    OutcomeDecisionInput,
    PlanningInputsIn,
    Prepared,
    RemoteWork,
    SpendingCaps,
    SupportInput,
    TuitionFeeLoanInput,
    VariantInputs,
    WorkPatternInput,
    decided_outcomes,
    needs,
    prepare,
    refused_decision,
    stamped,
)
from tests.support.planning import START, catalogue_of, option

ACTOR = uuid.UUID("00000000-0000-4000-8000-000000000001")
OTHER = uuid.UUID("00000000-0000-4000-8000-000000000002")
NOW = datetime(2026, 10, 31, 12, tzinfo=UTC)
LATER = datetime(2026, 11, 2, tzinfo=UTC)


def gbp(minor: int) -> Money:
    return Money(minor_units=minor, currency="GBP")


P01_CAPS = SpendingCaps(direct_spend_cap=gbp(150000), monthly_payment_cap=gbp(150000))
UNASKED_CAPS = SpendingCaps(direct_spend_cap=None, monthly_payment_cap=None)
BLOCKS, UNRESOLVED = NeedEffect.BLOCKS_A_SOLVE, NeedEffect.LEAVES_EVERY_ROUTE_UNRESOLVED


def complete(**changes: object) -> PlanningInputsIn:
    """P01's figures, every input stated (synthetic)."""
    inputs = PlanningInputsIn(
        objective_basis="economic",
        baseline=BaselineInput(kind=BaselineKind.CURRENT_ROLE, net_income=gbp(200000)),
        continuation=ContinuationInput(hours_per_week=30, net_income=gbp(200000)),
        opening_cash=gbp(600000),
        living_costs=gbp(100000),
        reserve=gbp(50000),
        weekly_availability=40,
        commitments=[CommitmentInput(kind=CommitmentKind.CARE, hours_per_week=4)],
        existing_debts=[DebtInput(monthly_repayment=gbp(5000))],
        scenario_delay_months=2,
        work_rights=WorkRights.HELD,
    )
    return inputs.model_copy(update=changes) if changes else inputs


def ready(
    document: PlanningInputsIn,
    catalogue: Catalogue | None = None,
    caps: SpendingCaps = P01_CAPS,
) -> Prepared:
    return prepare(
        stamped(document, previous=None, by=ACTOR, at=NOW),
        catalogue if catalogue is not None else catalogue_of(),
        caps=caps,
        planning_start=START,
        horizon_months=3,
        synthetic=True,
        version=1,
    )


def checked(prepared: Prepared, route: list[str]) -> RouteCheck:
    return check_route(compile_input(prepared.inputs, prepared.catalogue), route)


@pytest.mark.req("PLN-11", "API-05")
def test_nothing_stated_needs_every_input_and_a_solve_is_refused_naming_them() -> None:
    empty = PlanningInputsIn()

    assert [(n.input, n.effect) for n in needs(empty, UNASKED_CAPS)] == [
        (NeededInput.OBJECTIVE_BASIS, BLOCKS),
        (NeededInput.CONTINUATION, BLOCKS),
        (NeededInput.OPENING_CASH, BLOCKS),
        (NeededInput.LIVING_COSTS, BLOCKS),
        (NeededInput.COMMITMENTS, BLOCKS),
        (NeededInput.EXISTING_DEBTS, BLOCKS),
        (NeededInput.SCENARIO_DELAY_MONTHS, BLOCKS),
        # The solve's stage checks (API-05, Task 14): a budget-qualified solve needs both
        # confirmed limits.
        (NeededInput.DIRECT_SPEND_CAP, BLOCKS),
        (NeededInput.MONTHLY_PAYMENT_CAP, BLOCKS),
        (NeededInput.RESERVE, UNRESOLVED),
        (NeededInput.WEEKLY_AVAILABILITY, UNRESOLVED),
        (NeededInput.WORK_RIGHTS, UNRESOLVED),
    ]
    with pytest.raises(CareerwrightError) as refused:
        ready(empty)
    assert refused.value.code is ErrorCode.VALIDATION_FAILED
    assert refused.value.details == {
        "reason": "inputs_missing",
        "missing": [
            "objective_basis",
            "continuation",
            "opening_cash",
            "living_costs",
            "commitments",
            "existing_debts",
            "scenario_delay_months",
        ],
    }
    # Every money input not yet stated is null, never £0.
    assert all(
        getattr(empty, name) is None
        for name in ("opening_cash", "living_costs", "reserve", "monthly_deficit_cap")
    )


@pytest.mark.req("PLN-11", "FIN1-11", "API-05")
def test_the_stated_inputs_read_as_the_monthly_input_one_value_a_month() -> None:
    inputs = ready(complete()).inputs

    assert needs(complete(), P01_CAPS) == []
    assert (inputs.planning_start, inputs.horizon_months) == (START, 3)
    assert inputs.objective_basis == "economic"
    assert inputs.baseline is not None
    assert inputs.baseline.net_income_by_month == [200000] * 3
    assert inputs.baseline.cited.basis is CitationBasis.PERSON
    assert inputs.continuation.net_income_by_month == [200000] * 3
    assert inputs.continuation.hours_per_week == 30
    assert inputs.opening_cash_minor == 600000
    assert inputs.living_outgoings_by_month == [100000] * 3
    assert inputs.reserve_minor == 50000
    # The two spending caps are the profile's own answers (one record, PROF-04).
    assert (inputs.direct_spend_cap_minor, inputs.monthly_payment_cap_minor) == (150000, 150000)
    assert inputs.monthly_deficit_cap_minor is None  # none set: no deficit limit
    assert inputs.weekly_availability_by_month == [40] * 3
    assert [(c.label, c.hours_per_week) for c in inputs.commitments] == [("care", 4)]
    assert [(d.debt_id, d.monthly_repayment_minor) for d in inputs.existing_debts] == [
        ("debt:1", 5000)
    ]
    assert inputs.scenario_delay_months == 2
    assert inputs.work_rights is WorkRights.HELD
    # "No debts" is an answer: the empty list. Not asked is null, and blocks the solve.
    assert ready(complete(existing_debts=[])).inputs.existing_debts == []
    unasked = needs(complete(existing_debts=None), P01_CAPS)
    assert [(n.input, n.effect) for n in unasked] == [(NeededInput.EXISTING_DEBTS, BLOCKS)]
    # The baseline is needed for the economic comparison only (FIN1-07: never a silent switch).
    direct = complete(objective_basis="direct_spending", baseline=None)
    assert needs(direct, P01_CAPS) == []
    # The solve's stage check (API-05, Task 14): an economic solve needs its baseline (the
    # horizon is part of every solve request), so a solve is refused naming it.
    economic = needs(complete(baseline=None), P01_CAPS)
    assert [(n.input, n.effect) for n in economic] == [(NeededInput.BASELINE, BLOCKS)]
    # A deficit cap under direct spending reads the baseline too, but is no economic solve.
    deficit = complete(objective_basis="direct_spending", baseline=None, monthly_deficit_cap=gbp(1))
    assert [(n.input, n.effect) for n in needs(deficit, P01_CAPS)] == [
        (NeededInput.BASELINE, UNRESOLVED)
    ]


@pytest.mark.req("API-05")
@pytest.mark.parametrize(
    ("caps", "changes", "missing"),
    [
        (SpendingCaps(None, P01_CAPS.monthly_payment_cap), {}, ["direct_spend_cap"]),
        (SpendingCaps(P01_CAPS.direct_spend_cap, None), {}, ["monthly_payment_cap"]),
        (UNASKED_CAPS, {}, ["direct_spend_cap", "monthly_payment_cap"]),
        (P01_CAPS, {"baseline": None}, ["baseline"]),
    ],
)
def test_a_solve_without_its_stage_s_inputs_is_refused_naming_them(
    caps: SpendingCaps, changes: dict[str, object], missing: list[str]
) -> None:
    with pytest.raises(CareerwrightError) as refused:
        ready(complete(**changes), caps=caps)

    assert refused.value.code is ErrorCode.VALIDATION_FAILED
    assert refused.value.details == {"reason": "inputs_missing", "missing": missing}


@pytest.mark.req("PLN-11", "FIN1-06", "API-05")
@pytest.mark.parametrize(
    ("unset", "unstated"),
    [
        ("direct_spend_cap_minor", "direct_spend_cap"),
        ("monthly_payment_cap_minor", "monthly_payment_cap"),
        ("reserve_minor", "reserve"),
    ],
)
def test_an_unasked_limit_leaves_a_route_unresolved(unset: str, unstated: str) -> None:
    """The checker's own rule, beside the solve's stage checks: a monthly input without a hard
    limit leaves a route unresolved, never passed."""
    course = catalogue_of(option("course", payments=((0, 1000),)))
    prepared = ready(complete(), course)
    inputs = prepared.inputs.model_copy(update={unset: None})
    result = check_route(compile_input(inputs, prepared.catalogue), ["course"])

    assert [(f.code, f.reason) for f in result.findings] == [(FindingCode.LIMIT_UNKNOWN, unstated)]
    assert result.feasibility is Feasibility.UNRESOLVED


@pytest.mark.req("BND1-04", "PLN-11", "PLN-06")
@pytest.mark.parametrize("rights", [None, WorkRights.UNKNOWN])
def test_work_rights_not_stated_never_read_as_ineligible(rights: WorkRights | None) -> None:
    document = complete(work_rights=rights)
    prepared = ready(document, catalogue_of(option("course")))
    result = checked(prepared, ["course"])

    assert prepared.inputs.work_rights is WorkRights.UNKNOWN
    assert [n.input for n in needs(document, P01_CAPS)] == [NeededInput.WORK_RIGHTS]
    assert [f.code for f in result.findings] == [FindingCode.WORK_RIGHTS_UNKNOWN]
    assert result.feasibility is Feasibility.UNRESOLVED  # never "not feasible", never ineligible


@pytest.mark.req("BND1-05", "PLN-11")
def test_remote_working_names_an_england_employer_and_its_timezone_never_a_city() -> None:
    remote = RemoteWork(works_remotely=True, employment_country="GB-ENG", timezone="Europe/London")

    assert complete(remote_work=remote).remote_work == remote
    assert RemoteWork(works_remotely=False).employment_country is None
    assert "city" not in RemoteWork.model_fields  # remote work never takes a city slot
    with pytest.raises(ValidationError):
        RemoteWork(works_remotely=True)  # remote work names its employer's country and zone
    with pytest.raises(ValidationError):
        RemoteWork.model_validate(
            {"works_remotely": True, "employment_country": "US", "timezone": "America/New_York"}
        )
    with pytest.raises(ValidationError):
        RemoteWork(works_remotely=False, employment_country="GB-ENG", timezone="Europe/London")


def grant(**changes: object) -> SupportInput:
    return SupportInput.model_validate(
        {
            "instrument_id": "funding:employer",
            "kind": InstrumentKind.EMPLOYER_SUPPORT,
            "amount": gbp(30000),
            "paid_to": "provider",
            "eligibility": EligibilityStatus.CONFIRMED,
            "award": AwardState.APPROVED,
            **changes,
        }
    )


@pytest.mark.req("PLN-11", "PLN-06", "OPTN-03")
def test_the_person_s_answers_about_an_option_reach_its_variant_and_two_supports_wait() -> None:
    reduced = WorkPatternInput(
        kind=WorkPatternKind.REDUCED_HOURS, hours_per_week=20, net_income=gbp(150000)
    )
    conditions = [Fact(field="eligibility_age", value={"minimum_age": 19})]
    course = option("course", payments=((0, 60000),), eligibility_conditions=conditions)
    answers = VariantInputs(
        variant_id="course",
        work_pattern=reduced,
        supports=[grant(), grant(instrument_id="funding:bursary", kind=InstrumentKind.BURSARY)],
        entry_requirements_met=True,
        condition_statuses={"eligibility_age": EligibilityStatus.CONFIRMED},
    )
    prepared = ready(complete(variants=[answers]), catalogue_of(course))
    [variant] = prepared.catalogue.variants
    result = checked(prepared, ["course"])

    assert variant.work_pattern is not None
    assert (variant.work_pattern.kind, variant.work_pattern.hours_per_week) == (
        WorkPatternKind.REDUCED_HOURS,
        20,
    )
    assert variant.work_pattern.cited.basis is CitationBasis.PERSON
    assert variant.wage is None
    assert variant.entry_requirements_met is True
    assert variant.condition_statuses == {"eligibility_age": EligibilityStatus.CONFIRMED}
    # A support the person states is their assumption, never a reviewed record.
    assert {s.review_state for s in variant.supports} == {RecordState.ACCEPTED_ASSUMPTION}
    assert [f.code for f in result.findings] == [FindingCode.STACKING_UNCONFIRMED]
    assert result.feasibility is Feasibility.UNRESOLVED
    stacked = answers.model_copy(update={"stacking_confirmed": True})
    again = checked(ready(complete(variants=[stacked]), catalogue_of(course)), ["course"])
    assert again.feasibility is Feasibility.FEASIBLE
    # An answer names its own option only: another option keeps none of it.
    both = ready(complete(variants=[answers]), catalogue_of(course, option("other")))
    untouched = next(v for v in both.catalogue.variants if v.variant_id == "other")
    assert (untouched.work_pattern, untouched.supports) == (None, [])


@pytest.mark.req("PLN-11", "PLN-06", "FUNDING-05")
def test_a_scheme_the_person_confirms_pays_for_several_options_names_one_of_their_supports() -> (
    None
):
    first = VariantInputs(variant_id="first", supports=[grant()])
    second = VariantInputs(variant_id="second", supports=[grant()])
    stated = complete(variants=[first, second], shared_schemes=["funding:employer"])
    courses = catalogue_of(
        option("first", payments=((0, 50000),)), option("second", payments=((0, 50000),))
    )

    assert ready(stated, courses).inputs.shared_schemes == ["funding:employer"]
    assert checked(ready(stated, courses), ["first", "second"]).feasibility is (
        Feasibility.FEASIBLE
    )
    unconfirmed = checked(ready(complete(variants=[first, second]), courses), ["first", "second"])
    assert [f.code for f in unconfirmed.findings] == [FindingCode.SCHEME_SHARED_UNCONFIRMED]
    with pytest.raises(ValidationError):
        PlanningInputsIn(variants=[first], shared_schemes=["funding:elsewhere"])  # no support
    with pytest.raises(ValidationError):
        PlanningInputsIn(variants=[first], shared_schemes=["funding:employer"] * 2)


@pytest.mark.req("PLN-11", "FUNDING-06")
def test_a_tuition_fee_loan_the_person_states_reaches_its_option_as_their_assumption() -> None:
    stated = TuitionFeeLoanInput(
        amount=gbp(925000), eligibility=EligibilityStatus.CONFIRMED, application=AwardState.APPLIED
    )
    answers = VariantInputs(variant_id="degree", tuition_fee_loan=stated)
    courses = catalogue_of(option("degree", payments=((0, 925000),)), option("other"))

    prepared = ready(complete(variants=[answers]), courses)
    loan = next(v for v in prepared.catalogue.variants if v.variant_id == "degree").tuition_fee_loan
    other = next(v for v in prepared.catalogue.variants if v.variant_id == "other")
    result = checked(prepared, ["degree"])

    assert loan is not None
    assert (loan.amount, loan.eligibility, loan.application) == (
        gbp(925000),
        EligibilityStatus.CONFIRMED,
        AwardState.APPLIED,
    )
    assert loan.review_state is RecordState.ACCEPTED_ASSUMPTION  # never a reviewed record
    assert loan.cited.basis is CitationBasis.PERSON
    assert other.tuition_fee_loan is None
    assert [c.verification for c in result.conditions] == ["confirm_loan_approved"]
    unstated = TuitionFeeLoanInput(
        eligibility=EligibilityStatus.CONFIRMED, application=AwardState.APPROVED
    )
    assert unstated.amount is None  # not stated: unknown, never £0


@pytest.mark.req("PLN-11", "FUNDING-04", "FUNDING-05")
def test_a_support_follows_the_funding_rules_and_a_loan_is_never_one() -> None:
    with pytest.raises(ValidationError):
        grant(kind=InstrumentKind.LOAN)  # information to verify, never support
    with pytest.raises(ValidationError):
        grant(eligibility=EligibilityStatus.POTENTIALLY_ELIGIBLE)  # approved needs confirmed
    with pytest.raises(ValidationError):
        grant(paid_to="person")  # paid to the person: in which month
    assert grant(amount=None, covers_fees_in_full=True).covers_fees_in_full


@pytest.mark.req("PLN-11", "TIME1-03", "PLN-05")
def test_a_recorded_admission_or_offer_is_the_starting_position_and_without_it_a_condition() -> (
    None
):
    # Review 13a (C09): an apprenticeship behind its application deadline and its offer.
    apprenticeship = option(
        "apprenticeship",
        start=date(2027, 2, 1),
        finish=date(2027, 2, 28),
        kind=ActionKind.APPRENTICESHIP,
        wage=100000,
        offer=OfferGate(accepted=False),
        application_deadline=date(2027, 1, 20),
        application_gate="admission:offering:apprenticeship",
    )
    catalogue = catalogue_of(apprenticeship)

    without = ready(complete(), catalogue)
    held = ready(complete(admissions=["offering:apprenticeship"]), catalogue)

    assert without.inputs.initial_gates == []
    # Without a recorded place or offer, the route rests on both, as conditions: never "not
    # feasible" (fix round 1, the controller's C09 ruling).
    as_stated = checked(without, ["apprenticeship"])
    assert as_stated.findings == []
    assert [(c.kind, c.verification) for c in as_stated.conditions] == [
        ("offer", "confirm_offer_accepted"),
        ("application", "confirm_admission"),
    ]
    assert as_stated.feasibility is Feasibility.FEASIBLE
    assert held.inputs.initial_gates == ["admission:offering:apprenticeship"]
    [offering] = held.catalogue.offerings
    assert offering.offer_gate == OfferGate(accepted=True)
    admitted = checked(held, ["apprenticeship"])
    assert admitted.feasibility is Feasibility.FEASIBLE
    assert admitted.conditions == []


@pytest.mark.req("OUT1-03", "OUT1-11", "PLN-11")
def test_an_accepted_mapping_is_the_person_s_assumption_and_an_override_stands_beside_it() -> None:
    outcomes = list(committed_data().outcomes)
    decisions = stamped(
        PlanningInputsIn(
            outcome_decisions=[
                OutcomeDecisionInput(outcome_id="outcome:C01.1", decision="accept"),
                OutcomeDecisionInput(
                    outcome_id="outcome:C01.2",
                    decision="override",
                    evidence_kind=EvidenceKind.EXAM,
                    level_on_completion=2,
                    rubric_version="rubric:constructed",
                    reason="the course's final exam covers validation",
                ),
            ]
        ),
        previous=None,
        by=ACTOR,
        at=NOW,
    ).outcome_decisions

    decided = {o.outcome_id: o for o in decided_outcomes(outcomes, decisions)}
    provider = {o.outcome_id: o for o in outcomes}

    accepted = decided["outcome:C01.1"]
    assert (accepted.review_state, accepted.provenance) == (
        OutcomeReview.ACCEPTED_ASSUMPTION,
        Provenance.PROVIDER_CLAIM,
    )
    assert accepted.level_on_completion == provider["outcome:C01.1"].level_on_completion
    assert accepted.assumption is not None
    assert (accepted.assumption.recorded_by, accepted.assumption.recorded_at) == (ACTOR, NOW)
    override = decided["outcome:C01.2#override"]
    assert (override.provenance, override.review_state, override.overrides) == (
        Provenance.USER_OVERRIDE,
        OutcomeReview.ACCEPTED_ASSUMPTION,
        "outcome:C01.2",
    )
    assert decided["outcome:C01.2"] == provider["outcome:C01.2"]  # unchanged beside it
    assert len(decided) == len(outcomes) + 1


@pytest.mark.req("OUT1-03", "OUT1-01", "PLN-11")
def test_a_decision_the_outcome_contract_refuses_is_named_never_stored() -> None:
    outcomes = list(committed_data().outcomes)

    def refusal(decision: OutcomeDecisionInput) -> str | None:
        document = stamped(
            PlanningInputsIn(outcome_decisions=[decision]), previous=None, by=ACTOR, at=NOW
        )
        return refused_decision(outcomes, document.outcome_decisions)

    # "Introduction to SQL" never gives a level: a topic mention keeps none, even overridden.
    mention = OutcomeDecisionInput(
        outcome_id="outcome:C01.1",
        decision="override",
        evidence_kind=EvidenceKind.TOPIC_MENTION,
        level_on_completion=2,
        rubric_version="rubric:constructed",
        reason="I think it teaches enough",
    )
    assert refusal(mention) == "override_not_supported"
    assert refusal(OutcomeDecisionInput(outcome_id="outcome:none", decision="accept")) == (
        "unknown_outcome"
    )
    assert refusal(OutcomeDecisionInput(outcome_id="outcome:C01.1", decision="accept")) is None


@pytest.mark.req("OUT1-03", "PLN-11")
def test_a_decision_keeps_when_and_by_whom_it_was_first_made() -> None:
    accept = OutcomeDecisionInput(outcome_id="outcome:C01.1", decision="accept")
    override = OutcomeDecisionInput(
        outcome_id="outcome:C01.1",
        decision="override",
        evidence_kind=EvidenceKind.EXAM,
        reason="an exam",
    )
    first = stamped(PlanningInputsIn(outcome_decisions=[accept]), previous=None, by=ACTOR, at=NOW)

    kept = stamped(
        PlanningInputsIn(outcome_decisions=[accept], reserve=gbp(1)),
        previous=first,
        by=OTHER,
        at=LATER,
    )
    changed = stamped(
        PlanningInputsIn(outcome_decisions=[override]), previous=first, by=OTHER, at=LATER
    )

    assert [(d.recorded_by, d.recorded_at) for d in kept.outcome_decisions] == [(ACTOR, NOW)]
    assert [(d.recorded_by, d.recorded_at) for d in changed.outcome_decisions] == [(OTHER, LATER)]


@pytest.mark.req("PLN-11")
def test_an_input_is_one_answer_each() -> None:
    accept = OutcomeDecisionInput(outcome_id="o", decision="accept")
    with pytest.raises(ValidationError):
        PlanningInputsIn(variants=[VariantInputs(variant_id="a"), VariantInputs(variant_id="a")])
    with pytest.raises(ValidationError):
        PlanningInputsIn(admissions=["offering:a", "offering:a"])
    with pytest.raises(ValidationError):
        PlanningInputsIn(outcome_decisions=[accept, accept])
    with pytest.raises(ValidationError):
        OutcomeDecisionInput(outcome_id="o", decision="override")  # an override says what
    with pytest.raises(ValidationError):
        OutcomeDecisionInput(outcome_id="o", decision="accept", level_on_completion=2)
    with pytest.raises(ValidationError):
        PlanningInputsIn(scenario_delay_months=0)
    with pytest.raises(ValidationError):
        PlanningInputsIn(weekly_availability=169)
