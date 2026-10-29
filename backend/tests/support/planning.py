"""Planning inputs built from the M0 fixture pack (TRACE-01, P01, P03) and small constructed
cases, every one labelled synthetic. The fixture adapter states what the fixture leaves
implicit: wages arrive late in the month (the pack's validator assumes it; hand check H5).
Nothing here enters the product."""

from datetime import date

from nessa.capability.readiness import ReadinessState
from nessa.planning.catalogue import (
    ActionConcept,
    ActionKind,
    Basis,
    Catalogue,
    CatalogueLabel,
    Citation,
    Offering,
    Payment,
    PaymentPlan,
    RecordState,
    Variant,
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
FIXTURE = Citation(basis=Basis.FIXTURE, locator=TRACE)
CONSTRUCTED = Citation(basis=Basis.FIXTURE, locator="constructed test case")
COURSES = ("A", "B", "C", "D", "E")
CONDITIONAL = ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION
DELAY_MONTHS = 2  # a constructed stress case; TRACE-01 has no condition for it to move


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
    return WorkPattern(kind=kind, hours_per_week=hours, net_income_minor=income, cited=FIXTURE)


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
            Payment(kind="fee", amount_minor=amount, month_offset=n, cited=FIXTURE)
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
