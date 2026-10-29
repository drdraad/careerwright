"""Planning inputs built from the M0 fixture pack (TRACE-01, P01, P03) and small constructed
cases, every one labelled synthetic. The fixture adapter states what the fixture leaves
implicit: wages arrive late in the month (the pack's validator assumes it; hand check H5).
Nothing here enters the product."""

from datetime import date
from typing import Literal

from nessa.capability.readiness import ReadinessState
from nessa.money import Money
from nessa.planning.catalogue import (
    ActionConcept,
    ActionKind,
    AwardState,
    Catalogue,
    CatalogueLabel,
    Citation,
    CitationBasis,
    EligibilityStatus,
    InstrumentKind,
    OfferGate,
    Offering,
    Payment,
    PaymentPlan,
    RecordState,
    Recurring,
    Support,
    Variant,
    Wage,
    WorkPattern,
    WorkPatternKind,
)
from nessa.planning.compiler import (
    Baseline,
    Continuation,
    PlanningInputs,
    ReadinessBasis,
    ReceiptTiming,
)
from tests.support.capability import fixture, trace_evidence, trace_matrix, trace_outcomes

TRACE = "fixtures/m0/worked_trace.json"
FIXTURE = Citation(basis=CitationBasis.FIXTURE, locator=TRACE)
CONSTRUCTED = Citation(basis=CitationBasis.FIXTURE, locator="constructed test case")
COURSES = ("A", "B", "C", "D", "E")
CONDITIONAL = ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION
DELAY_MONTHS = 2  # a constructed stress case; TRACE-01 has no condition for it to move


def gbp(minor: int) -> Money:
    return Money(minor_units=minor, currency="GBP")


def trace_inputs(**changes: object) -> PlanningInputs:
    trace = fixture("worked_trace.json")
    p01 = fixture("personas/P01.json")
    action = trace["catalogue"]["actions"][0]
    inputs = PlanningInputs(
        planning_start=date.fromisoformat(trace["planning_start"]),
        horizon_months=trace["comparison_horizon_months"],
        objective_basis="economic",
        baseline=Baseline(
            label="staying in the current role",
            net_income_by_month=trace["baseline_income_by_month_minor"],
            cited=FIXTURE,
        ),
        continuation=Continuation(
            label="returning to the current role at its pay",
            hours_per_week=action["weekly_work_after_completion"],
            net_income_by_month=trace["baseline_income_by_month_minor"],
            cited=FIXTURE,
        ),
        wage_timing=ReceiptTiming.LATER,  # every fixture wage arrives late in the month
        opening_cash_minor=trace["opening_cash_minor"],
        living_outgoings_by_month=trace["living_outgoings_by_month_minor"],
        reserve_minor=trace["minimum_reserve_minor"],
        direct_spend_cap_minor=p01["direct_spend_cap_minor"],
        monthly_payment_cap_minor=p01["monthly_payment_cap_minor"],
        weekly_availability_by_month=[trace["available_weekly_hours_envelope"]]
        * trace["comparison_horizon_months"],
        initial_gates=trace["initial_completed_gates"],
        scenario_delay_months=DELAY_MONTHS,
        synthetic=True,
    )
    return inputs.model_copy(update=changes) if changes else inputs


def _pattern(action: dict[str, object], continuation_hours: int) -> WorkPattern:
    hours = action["weekly_work_envelope_while_active"]
    assert isinstance(hours, int)
    active = action["intakes"][0]["active_months"]  # type: ignore[index]
    income = action["scenario_net_income_by_month_minor"][active[0] - 1]  # type: ignore[index]
    kind = (
        WorkPatternKind.TEMPORARY_STUDY_BREAK
        if hours == 0
        else WorkPatternKind.RETAIN_WORK
        if hours == continuation_hours
        else WorkPatternKind.REDUCED_HOURS
    )
    return WorkPattern(kind=kind, hours_per_week=hours, net_income=gbp(income), cited=FIXTURE)


def trace_catalogue(**study_hours: int) -> Catalogue:
    """TRACE-01's five courses, one offering and one approved work pattern each. A letter in
    `study_hours` overrides that course's weekly study envelope (a known-bad variant)."""
    trace = fixture("worked_trace.json")
    concepts, offerings, variants = [], [], []
    for action in trace["catalogue"]["actions"]:
        letter = action["id"].rsplit(":", 1)[-1]
        intake = action["intakes"][0]
        concepts.append(
            ActionConcept(
                concept_id=action["id"],
                kind=ActionKind.LEARNING,
                title=f"Synthetic course {letter}",
                provider=action["provider_id"],
                review_state=RecordState(action["review_state"]),
                exclusive_group=action["exclusive_group"],
                synthetic=True,
                cited=FIXTURE,
            )
        )
        payments = [
            Payment(kind="fee", amount=gbp(amount), month_offset=n, cited=FIXTURE)
            for n, amount in enumerate(action["fees_by_month_minor"])
            if amount
        ]
        offerings.append(
            Offering(
                offering_id=intake["id"],
                concept_id=action["id"],
                review_state=RecordState(action["review_state"]),
                start=date.fromisoformat(intake["start_date"]),
                finish=date.fromisoformat(intake["finish_date"]),
                weekly_hours=study_hours.get(letter, action["weekly_study_envelope"]),
                payment_plans=[PaymentPlan(plan_id="as-stated", payments=payments)],
                prerequisites=action["prerequisites"],
                synthetic=True,
                cited=FIXTURE,
            )
        )
        variants.append(
            Variant(
                variant_id=f"TRACE-01/{letter}",
                offering_id=intake["id"],
                plan_id="as-stated",
                work_pattern=_pattern(action, action["weekly_work_after_completion"]),
            )
        )
    return Catalogue(
        label=CatalogueLabel(name="TRACE-01", dated=date(2027, 1, 1), synthetic=True),
        concepts=concepts,
        offerings=offerings,
        variants=variants,
    )


def trace_readiness() -> ReadinessBasis:
    outcomes = [o for letter in COURSES for o in trace_outcomes(f"fixture:course:{letter}")]
    return ReadinessBasis(
        matrix=trace_matrix(),
        evidence=trace_evidence(),
        statements=[],
        outcomes=outcomes,
        evidence_version=1,
    )


def trace_route(letter: str) -> dict[str, object]:
    route: dict[str, object] = next(
        r for r in fixture("worked_trace.json")["routes"] if r["id"] == letter
    )
    return route


# Constructed cases: a person and options written for one rule each (synthetic).

START = date(2027, 1, 1)
# A stated limit far above anything a constructed case spends: the case is about another
# rule. An unknown limit is never a pass, so a case leaves a limit unknown only on purpose.
UNTESTED_LIMIT = 100_000_000


def person(
    *,
    horizon: int = 1,
    opening: int = 0,
    living: int = 0,
    reserve: int | None = 0,
    pay: int = 0,
    hours: int = 0,
    availability: int | None = 40,
    baseline: int | None = None,
    objective: str = "direct_spending",
    timing: ReceiptTiming = ReceiptTiming.LATER,
    **limits: object,
) -> PlanningInputs:
    """A synthetic person: `pay` and `hours` are the continuation's, a month and a week."""
    return PlanningInputs.model_validate(
        {
            "planning_start": START,
            "horizon_months": horizon,
            "objective_basis": objective,
            "baseline": (
                None
                if baseline is None
                else Baseline(
                    label="staying in the current role",
                    net_income_by_month=[baseline] * horizon,
                    cited=CONSTRUCTED,
                )
            ),
            "continuation": Continuation(
                label="the current role, unchanged",
                hours_per_week=hours,
                net_income_by_month=[pay] * horizon,
                cited=CONSTRUCTED,
            ),
            "wage_timing": timing,
            "opening_cash_minor": opening,
            "living_outgoings_by_month": [living] * horizon,
            "reserve_minor": reserve,
            "direct_spend_cap_minor": limits.pop("direct_cap", UNTESTED_LIMIT),
            "monthly_payment_cap_minor": limits.pop("monthly_cap", UNTESTED_LIMIT),
            "weekly_availability_by_month": None
            if availability is None
            else [availability] * horizon,
            "scenario_delay_months": DELAY_MONTHS,
            "synthetic": True,
            **limits,
        }
    )


def option(
    name: str,
    *,
    start: date | None = START,
    finish: date | None = date(2027, 1, 31),
    hours: int | None = 0,
    payments: tuple[tuple[int, int], ...] = (),
    due: tuple[tuple[date, int], ...] = (),
    kind: ActionKind = ActionKind.LEARNING,
    state: RecordState = RecordState.ACCEPTED_ASSUMPTION,
    pattern: WorkPattern | None = None,
    wage: int | None = None,
    supports: tuple[Support, ...] = (),
    offer: OfferGate | None = None,
    unknown_cost: str | None = None,
    recurring: Recurring | None = None,
    synthetic: bool = True,
    group: str | None = None,
    **offering: object,
) -> tuple[ActionConcept, Offering, Variant]:
    """One concept with one offering and one variant. `payments` are (month offset, amount)."""
    plan = PaymentPlan(
        plan_id="plan",
        payments=[
            *(
                Payment(kind="fee", amount=gbp(a), month_offset=n, cited=CONSTRUCTED)
                for n, a in payments
            ),
            *(Payment(kind="fee", amount=gbp(a), due=d, cited=CONSTRUCTED) for d, a in due),
        ],
        recurring=recurring,
        unknown=unknown_cost,
    )
    concept = ActionConcept(
        concept_id=f"concept:{name}",
        kind=kind,
        title=name,
        provider=None,
        review_state=state,
        exclusive_group=group,
        synthetic=synthetic,
        cited=CONSTRUCTED,
    )
    dated = Offering.model_validate(
        {
            "offering_id": f"offering:{name}",
            "concept_id": concept.concept_id,
            "review_state": state,
            "start": start,
            "finish": finish,
            "weekly_hours": hours,
            "payment_plans": [plan],
            "offer_gate": offer,
            "synthetic": synthetic,
            "cited": CONSTRUCTED,
            **offering,
        }
    )
    variant = Variant(
        variant_id=name,
        offering_id=dated.offering_id,
        plan_id="plan",
        work_pattern=pattern,
        wage=Wage(net_income=gbp(wage), cited=CONSTRUCTED) if wage is not None else None,
        supports=list(supports),
    )
    return concept, dated, variant


def catalogue_of(*options: tuple[ActionConcept, Offering, Variant]) -> Catalogue:
    return Catalogue(
        label=CatalogueLabel(name="constructed", dated=START, synthetic=True),
        concepts=[c for c, _, _ in options],
        offerings=[o for _, o, _ in options],
        variants=[v for _, _, v in options],
    )


def support(
    *,
    paid_to: Literal["provider", "person"] = "person",
    amount: int | None = None,
    month: int | None = 0,
    eligibility: EligibilityStatus = EligibilityStatus.CONFIRMED,
    award: AwardState = AwardState.APPROVED,
    assumed: bool = False,
    early: bool = False,
    kind: InstrumentKind = InstrumentKind.GRANT,
    state: RecordState = RecordState.ACCEPTED_ASSUMPTION,
) -> Support:
    return Support(
        instrument_id="funding:constructed",
        kind=kind,
        covers_fees_in_full=amount is None,
        amount=gbp(amount) if amount is not None else None,
        paid_to=paid_to,
        paid_month_offset=month if paid_to == "person" else None,
        proven_before_outflows=early,
        eligibility=eligibility,
        award=award,
        assumed=assumed,
        review_state=state,
        cited=CONSTRUCTED,
    )


def pattern(kind: WorkPatternKind, hours: int, pay: int) -> WorkPattern:
    return WorkPattern(kind=kind, hours_per_week=hours, net_income=gbp(pay), cited=CONSTRUCTED)
