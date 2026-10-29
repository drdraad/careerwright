"""The immutable monthly input (spec section 12, TIME-1 and FIN-1; S5.4). Pure: no SQL, no
network, no model.

`compile_input` puts the person's confirmed planning inputs and a catalogue's variants on one
monthly grid, once, before any route is checked:

- each placed variant's touched months (every month a dated activity touches is reserved),
  the month from which what it grants is usable (the next month boundary), its payments by
  month and the payments beyond the horizon (contractual liabilities, kept with their dates);
- its maximum weekly load and fixed sessions, or the fact that no timetable is stated;
- the person's commitments counted once: the current job's hours come from the variant's
  confirmed work pattern or from the continuation scenario, never both, and care or commute
  hours are a load, never also a cut in availability.

A variant whose start or finish is unknown is not placed: its date-free facts (its total
cost, any single payment, its weekly load) are kept, and every check that needs its months is
unresolved, never passed. The input is versioned by its content (`input_version`), so a
route result names exactly what it was computed from.
"""

import hashlib
import json
from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nessa.capability.evidence import RequirementStatement, SkillEvidence
from nessa.capability.matrix import Matrix
from nessa.capability.outcomes import PlannedOutcome
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.money import Minor
from nessa.planning.catalogue import (
    ActionKind,
    Catalogue,
    CatalogueLabel,
    Citation,
    Hours,
    OfferGate,
    PaymentPlan,
    RecordState,
    Recurring,
    Session,
    Support,
    Wage,
    WorkPattern,
)
from nessa.planning.months import MAX_HORIZON_MONTHS, Month, grid, touched, usable_from


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReceiptTiming(StrEnum):
    """When the person's pay arrives in a month (TIME-1 prefunding). Only a receipt proven to
    arrive before the month's outflows may pay for them; anything else, the default, counts
    from the next month's opening balance."""

    BEFORE_OUTFLOWS = "before_outflows"
    LATER = "later"


class Baseline(StrictModel):
    """The confirmed counterfactual (FIN1-11): staying in the current role, continuing a job
    search or another the person confirms, never assumed to be staying put."""

    label: str
    net_income_by_month: list[Minor]
    cited: Citation


class Continuation(StrictModel):
    """The common scenario every route returns to and runs on where it changes nothing: the
    person's work hours and take-home pay (FIN-1). Never an invented target wage (ECON-05)."""

    label: str
    hours_per_week: Hours
    net_income_by_month: list[Minor]
    cited: Citation


class Commitment(StrictModel):
    """A fixed weekly commitment counted in every month's load: care, commute, a second job."""

    label: str
    hours_per_week: Hours
    cited: Citation


class ExistingDebt(StrictModel):
    """Existing debt is a fixed commitment (spec section 10): its repayments are outflows."""

    debt_id: str
    monthly_repayment_minor: Minor
    balance_minor: Minor | None = None
    annual_interest_bps: Annotated[int, Field(ge=0)] | None = None  # basis points a year
    cited: Citation


class PlanningInputs(StrictModel):
    """The person's confirmed planning inputs for one comparison: one start, horizon,
    currency, baseline and continuation for every route (FIN1-12). Unknown is None, never 0."""

    currency: Literal["GBP"] = "GBP"
    planning_start: date
    horizon_months: Annotated[int, Field(ge=1, le=MAX_HORIZON_MONTHS)]
    objective_basis: Literal["economic", "direct_spending"]
    baseline: Baseline | None  # None: missing, so the economic comparison is unresolved
    continuation: Continuation
    wage_timing: ReceiptTiming = ReceiptTiming.LATER
    opening_cash_minor: Minor
    living_outgoings_by_month: list[Minor]
    # The three hard limits: None is unknown, an unresolved finding, never "no limit".
    reserve_minor: Minor | None
    direct_spend_cap_minor: Minor | None
    monthly_payment_cap_minor: Minor | None
    # A separately named limit on the monthly incremental deficit against the baseline:
    # payments, less support received, plus income lost (spec section 12; provisional, R6).
    monthly_deficit_cap_minor: Minor | None = None
    economic_cost_cap_minor: int | None = None  # an optional preference, never a hard cap
    weekly_availability_by_month: list[Hours] | None  # the minimum weekly hours in each month
    commitments: list[Commitment] = Field(default_factory=list)
    existing_debts: list[ExistingDebt] = Field(default_factory=list)
    initial_gates: list[str] = Field(default_factory=list)  # verified in the initial state
    # How much later the delay scenario moves every conditional offer and award: declared once
    # for the comparison, so every route meets the same stress case (PLN-08).
    scenario_delay_months: Annotated[int, Field(ge=1, le=MAX_HORIZON_MONTHS)]
    synthetic: bool

    @model_validator(mode="after")
    def _one_horizon(self) -> Self:
        series = {
            "living_outgoings_by_month": self.living_outgoings_by_month,
            "continuation": self.continuation.net_income_by_month,
            **({"baseline": self.baseline.net_income_by_month} if self.baseline else {}),
            **(
                {"weekly_availability_by_month": self.weekly_availability_by_month}
                if self.weekly_availability_by_month is not None
                else {}
            ),
        }
        wrong = sorted(
            name for name, values in series.items() if len(values) != self.horizon_months
        )
        if wrong:
            raise ValueError(f"not one value a month of the horizon: {', '.join(wrong)}")
        return self


class ReadinessBasis(StrictModel):
    """What the capability model assesses readiness from: the readiness milestone of a route
    is computed there, never by the planning code (RDY-1)."""

    matrix: Matrix
    evidence: list[SkillEvidence]
    statements: list[RequirementStatement]
    outcomes: list[PlannedOutcome]
    evidence_version: int


class CompiledPayment(StrictModel):
    kind: Literal["fee", "instalment", "extra"]
    amount_minor: Minor
    offset: int | None  # months from the variant's start month; None with a due date
    due: date | None
    cited: Citation


class CompiledVariant(StrictModel):
    variant_id: str
    concept_id: str
    offering_id: str
    outcome_offering_id: str  # the offering the capability model's outcomes name
    kind: ActionKind
    exclusive_group: str | None
    review_states: list[RecordState]  # its concept's, offering's and supports'
    synthetic: bool
    placed: bool
    unplaced: list[str]  # why it cannot be put on the grid
    start_date: date | None
    finish_date: date | None
    start_index: int | None  # 1 is the planning start's month
    finish_index: int | None
    usable_index: int | None  # the month from which what it grants is usable
    active: list[int]  # the touched months, by index; beyond the horizon too
    weekly_hours: Hours | None
    sessions: list[Session]
    cost_unknown: str | None  # why its payments are not known
    payments: list[CompiledPayment]
    recurring: Recurring | None
    supports: list[Support]
    work_pattern: WorkPattern | None
    wage: Wage | None
    offer_gate: OfferGate | None
    prerequisites: list[str]  # the application gate among them, where one is needed
    grants: list[str]
    application_deadline: date | None
    application_gate: str | None
    entry_unconfirmed: bool  # stated entry requirements the person has not confirmed

    @property
    def conditional_offer(self) -> bool:
        return self.offer_gate is not None and not self.offer_gate.accepted


class MonthlyInput(StrictModel):
    """One comparison's immutable input: change anything and it is a new version."""

    input_version: str
    months: list[str]
    inputs: PlanningInputs
    label: CatalogueLabel
    variants: list[CompiledVariant]
    readiness: ReadinessBasis | None

    @property
    def start(self) -> Month:
        return Month.parse(self.months[0])

    def month_label(self, index: int) -> str:
        return str(self.start.plus(index - 1))

    def variant(self, variant_id: str) -> CompiledVariant:
        found = next((v for v in self.variants if v.variant_id == variant_id), None)
        if found is None:
            raise NessaError(
                ErrorCode.VALIDATION_FAILED,
                "That option is not in this comparison's input.",
                stage=ErrorStage.PLANNING,
                details={"reason": "unknown_variant"},
            )
        return found


def _plan(catalogue: Catalogue, offering_id: str, plan_id: str | None) -> PaymentPlan | None:
    offering = next(o for o in catalogue.offerings if o.offering_id == offering_id)
    if plan_id is not None:
        return offering.plan(plan_id)
    if len(offering.payment_plans) > 1:
        raise ValueError(f"{offering_id} has several payment plans: a variant chooses one")
    return offering.payment_plans[0] if offering.payment_plans else None


def compile_input(
    inputs: PlanningInputs, catalogue: Catalogue, *, readiness: ReadinessBasis | None = None
) -> MonthlyInput:
    start = Month.of(inputs.planning_start)
    months = [str(m) for m in grid(start, inputs.horizon_months)]
    concepts = {c.concept_id: c for c in catalogue.concepts}
    offerings = {o.offering_id: o for o in catalogue.offerings}
    compiled = []
    for variant in catalogue.variants:
        offering = offerings[variant.offering_id]
        concept = concepts[offering.concept_id]
        plan = _plan(catalogue, offering.offering_id, variant.plan_id)
        unplaced = [
            offering.unknown.get(name, f"no {name} date is stated")
            for name, value in (("start", offering.start), ("finish", offering.finish))
            if value is None
        ]
        placed = not unplaced
        start_index: int | None = None
        finish_index: int | None = None
        usable_index: int | None = None
        active: list[int] = []
        if offering.start is not None and offering.finish is not None:
            if offering.finish < offering.start:
                raise ValueError(f"{offering.offering_id} finishes before it starts")
            # TIME-1's own rules (`months`): every touched month, usable from the next boundary.
            active = [m.months_after(start) + 1 for m in touched(offering.start, offering.finish)]
            start_index, finish_index = active[0], active[-1]
            usable_index = usable_from(offering.finish).months_after(start) + 1
        if plan is None:
            cost_unknown: str | None = offering.unknown.get("fee", "no payment plan is stated")
        else:
            cost_unknown = plan.unknown
        compiled.append(
            CompiledVariant(
                variant_id=variant.variant_id,
                concept_id=concept.concept_id,
                offering_id=offering.offering_id,
                outcome_offering_id=offering.outcomes_from or offering.offering_id,
                kind=concept.kind,
                exclusive_group=concept.exclusive_group,
                review_states=[
                    concept.review_state,
                    offering.review_state,
                    *(s.review_state for s in variant.supports),
                ],
                synthetic=concept.synthetic or offering.synthetic,
                placed=placed,
                unplaced=unplaced,
                start_date=offering.start,
                finish_date=offering.finish,
                start_index=start_index,
                finish_index=finish_index,
                usable_index=usable_index,
                active=active,
                weekly_hours=offering.weekly_hours,
                sessions=offering.sessions,
                cost_unknown=cost_unknown,
                payments=[
                    CompiledPayment(
                        kind=p.kind,
                        amount_minor=p.amount.minor_units,
                        offset=p.month_offset,
                        due=p.due,
                        cited=p.cited,
                    )
                    for p in (plan.payments if plan is not None else [])
                ],
                recurring=plan.recurring if plan is not None else None,
                supports=variant.supports,
                work_pattern=variant.work_pattern,
                wage=variant.wage,
                offer_gate=offering.offer_gate,
                prerequisites=[
                    *offering.prerequisites,
                    *(
                        [offering.application_gate]
                        if offering.application_gate is not None
                        and offering.application_gate not in offering.prerequisites
                        else []
                    ),
                ],
                grants=offering.grants,
                application_deadline=offering.application_deadline,
                application_gate=offering.application_gate,
                entry_unconfirmed=bool(concept.entry_requirements)
                and variant.entry_requirements_met is not True,
            )
        )
    return MonthlyInput(
        input_version=_version(inputs, catalogue.label, compiled, readiness),
        months=months,
        inputs=inputs,
        label=catalogue.label,
        variants=compiled,
        readiness=readiness,
    )


def _version(
    inputs: PlanningInputs,
    label: CatalogueLabel,
    variants: list[CompiledVariant],
    readiness: ReadinessBasis | None,
) -> str:
    readiness_key = (
        None
        if readiness is None
        else {
            "matrix": readiness.matrix.matrix_version,
            "definition": readiness.matrix.definition_version,
            "evidence": readiness.evidence_version,
            "outcomes": sorted(
                (o.outcome_id, o.review_state.value, o.level_on_completion)
                for o in readiness.outcomes
            ),
        }
    )
    payload = {
        "inputs": inputs.model_dump(mode="json"),
        "label": label.model_dump(mode="json"),
        "variants": [v.model_dump(mode="json") for v in variants],
        "readiness": readiness_key,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"monthly-input:{digest[:16]}"
