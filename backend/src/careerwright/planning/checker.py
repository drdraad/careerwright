"""The route checker: one fixed candidate route on the immutable monthly input, in one of the
fixed scenarios (spec section 12, TIME-1, FIN-1, "Hard feasibility constraints" and
"Uncertainty and conditional plans"; S5.4-S5.6). Pure and deterministic: no SQL, no network,
no model, so the route search (Task 13a) can call it for every candidate.

What it reports, kept apart (Global Constraint 6):

- **Violations**, each named on its own: the direct-spend cap, the monthly payment cap, the
  monthly deficit cap and the reserve are four different limits, and the workload envelope
  and a session clash are two; existing repayments alone above the payment cap are named as
  the repayments, and more than one conditional job transition and two schemes recorded as
  exclusive are each their own. Every one found is listed, never only the first. A violation
  is a conservative rejection by this monthly model, never a claim that the person cannot
  afford a real schedule.
- **Unresolved findings:** unknown dates, cost or timetable, a same-month application ("not
  resolved by this monthly model", never "ineligible"), a missing baseline; and what waits on
  the person (Task 12a): work rights not known to be held, an eligibility condition of a stated
  fee, the stacking of two supports or one scheme paying for two options not confirmed, and
  their own "no" to an entry requirement; and (Task 12b) an entry requirement met only by a
  qualification they expect, "if you get your grades". Unknown never passes and is never zero.
- **Ledgers and objectives:** the direct-spend, income-difference, liquidity and debt ledgers;
  months to the modelled application-readiness milestone, which the capability model decides;
  direct and economic cost.
- **Qualifications and conditions:** proposed records, accepted assumptions, synthetic data,
  and the conditions a route rests on (an offer to accept, an award to approve, a place to
  win by applying in time, a tuition fee loan to be approved), each with a blocking
  verification; and (Task 12b) a figure the person supplied or an option they added. Only a
  route with none is "affordable and feasible" unqualified (OPTN-09).
- **A tuition fee loan paid straight to the provider** (Task 12c; spec section 22): the fee
  it pays is in neither the cash ledger, nor direct spending, nor the monthly payment cap's
  payments, and is never support or a receipt; the route carries it as a loan to repay
  (`loans_to_repay`: its amount and month, its repayment unknown). The economic cost still
  counts that fee once, because the loan is repaid (spec section 12: loan principal is a
  liquidity source, not a discount). Every other loan stays information.

Scenarios (S5.6): `base` assumes each condition happens as planned; `delay` moves every
conditional offer, award and tuition fee loan `scenario_delay_months` later; `no_award` drops
every award and tuition fee loan not already approved (the route where the person pays);
`no_offer` drops every activity behind an offer not already accepted, so its wages and its
experience go together. No adaptive policy is optimised and no hiring
probability is invented.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.capability.readiness import Assessment, Qualification, ReadinessState, assess
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.money import Money, SignedMoney
from careerwright.planning.catalogue import FeeLoanKind, RecordState, Support, WorkPattern
from careerwright.planning.compiler import (
    CompiledVariant,
    MonthlyInput,
    ReceiptTiming,
    WorkRights,
)
from careerwright.planning.ledgers import (
    DebtLedger,
    DirectLedger,
    DirectMonth,
    IncomeLedger,
    IncomeMonth,
    Ledgers,
    Liability,
    LoanToRepay,
    balances,
    debt,
    liquidity,
)
from careerwright.planning.months import ApplicationTiming, Month, application_timing

MAX_SELECTED_ACTIONS = 6  # M0SearchLimits.max_selected_actions (spec section 18)
READY = frozenset(
    {
        ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION,
        ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS,
    }
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Scenario(StrEnum):
    BASE = "base"
    DELAY = "delay"
    NO_AWARD = "no_award"
    NO_OFFER = "no_offer"


class FindingKind(StrEnum):
    VIOLATION = "violation"
    UNRESOLVED = "unresolved"
    PREFERENCE = "preference"  # an optional preference unmet, never a hard limit


class FindingCode(StrEnum):
    DIRECT_SPEND_CAP = "direct_spend_cap"
    MONTHLY_PAYMENT_CAP = "monthly_payment_cap"
    MONTHLY_DEFICIT_CAP = "monthly_deficit_cap"
    RESERVE = "reserve"
    WORKLOAD = "workload"
    SESSION_CLASH = "session_clash"
    PREREQUISITE_NOT_USABLE = "prerequisite_not_usable"
    APPLICATION_TOO_LATE = "application_too_late"
    STARTS_BEFORE_PLANNING = "starts_before_planning"
    ONE_START_PER_CONCEPT = "one_start_per_concept"
    EXCLUSIVE_GROUP = "exclusive_group"
    CONFLICTING_WORK_PATTERNS = "conflicting_work_patterns"
    COARSE_MODEL_UNRESOLVED = "coarse_model_unresolved"
    DATES_UNKNOWN = "dates_unknown"
    COST_UNKNOWN = "cost_unknown"
    WORKLOAD_UNKNOWN = "workload_unknown"
    ENTRY_REQUIREMENTS_UNCONFIRMED = "entry_requirements_unconfirmed"
    BASELINE_MISSING = "baseline_missing"
    # A hard limit the person has not stated (its name is the reason): never a pass.
    LIMIT_UNKNOWN = "limit_unknown"
    # A payment due before the planning start: whether it was paid is not known.
    PAYMENT_BEFORE_START = "payment_before_start"
    ECONOMIC_COST_CAP = "economic_cost_cap"
    # Task 12a (ADR 0013, amendment of 2026-10-31).
    # The person's own "no" to the stated entry requirements; its next action is to check
    # whether the provider accepts equivalent experience. Never ineligible.
    ENTRY_REQUIREMENTS_NOT_MET = "entry_requirements_not_met"
    # An eligibility condition of the stated fee the person has not confirmed (the reason).
    ELIGIBILITY_UNCONFIRMED = "eligibility_unconfirmed"
    # More than one support counted on one variant, its stacking not confirmed (spec section
    # 10: never assume two schemes stack; exclusivity and eligible-cost caps likewise).
    STACKING_UNCONFIRMED = "stacking_unconfirmed"
    WORK_RIGHTS_UNKNOWN = "work_rights_unknown"
    WORK_RIGHTS_NOT_HELD = "work_rights_not_held"  # this model checks no visa or sponsorship
    # Existing debt repayments alone above the monthly payment cap: the reason names them.
    REPAYMENTS_ABOVE_PAYMENT_CAP = "repayments_above_payment_cap"
    # More than one conditional job transition (a job or apprenticeship behind an offer not yet
    # accepted): spec section 12 allows one.
    JOB_TRANSITIONS = "job_transitions"
    # Fix round 1 (review 12a, Important 2). One scheme counted on more than one option of the
    # route before the person confirms it pays for each (the reason names it); its next
    # action is to confirm the scheme covers both.
    SCHEME_SHARED_UNCONFIRMED = "scheme_shared_unconfirmed"
    # Two schemes a record states may not be combined, both counted in the route (the reason
    # names them).
    EXCLUSIVE_SCHEMES = "exclusive_schemes"
    # Task 12c (spec section 22). A tuition fee loan paid straight to the provider counts in
    # this scenario but its amount is not stated: what the person pays is not known, never £0.
    LOAN_AMOUNT_UNKNOWN = "loan_amount_unknown"
    # Task 12b (plan v1.6). A stated entry requirement named only by a qualification the person
    # expects: met only if they get their grades, so unresolved until they confirm the result.
    ENTRY_REQUIREMENTS_EXPECTED = "entry_requirements_expected"


_UNRESOLVED = frozenset(
    {
        FindingCode.COARSE_MODEL_UNRESOLVED,
        FindingCode.DATES_UNKNOWN,
        FindingCode.COST_UNKNOWN,
        FindingCode.WORKLOAD_UNKNOWN,
        FindingCode.ENTRY_REQUIREMENTS_UNCONFIRMED,
        FindingCode.BASELINE_MISSING,
        FindingCode.LIMIT_UNKNOWN,
        FindingCode.PAYMENT_BEFORE_START,
        FindingCode.ENTRY_REQUIREMENTS_NOT_MET,
        FindingCode.ELIGIBILITY_UNCONFIRMED,
        FindingCode.STACKING_UNCONFIRMED,
        FindingCode.WORK_RIGHTS_UNKNOWN,
        FindingCode.WORK_RIGHTS_NOT_HELD,
        FindingCode.SCHEME_SHARED_UNCONFIRMED,
        FindingCode.LOAN_AMOUNT_UNKNOWN,
        FindingCode.ENTRY_REQUIREMENTS_EXPECTED,
    }
)
MOST_JOB_TRANSITIONS = 1  # spec section 12: at most one conditional bridge-role transition


class Finding(StrictModel):
    code: FindingCode
    kind: FindingKind
    month: str | None = None  # None: whatever month it falls in
    variant_id: str | None = None
    amount: int | None = None
    limit: int | None = None
    unit: Literal["minor_units", "hours_per_week"] | None = None
    # The gate, or why a value is unknown: the checker's working note, read in memory (the
    # search's prerequisite rule). Never serialized, so never sealed or served: a finding goes
    # out as its code and facts, and the web words it (R11, Task 13b's fix round 1).
    reason: str | None = Field(default=None, exclude=True)


class Feasibility(StrEnum):
    FEASIBLE = "feasible"
    NOT_FEASIBLE_IN_MODEL = "not_feasible_in_this_model"
    UNRESOLVED = "unresolved"


class Verdict(StrEnum):
    # Nothing qualifies it: every record reviewed, no condition, no synthetic input and an
    # unqualified readiness. M0 matrices are always provisional, so L0 never reaches it.
    AFFORDABLE_AND_FEASIBLE = "affordable_and_feasible"
    QUALIFIED = "affordable_and_feasible_with_qualifications"
    READINESS_NOT_REACHED = "readiness_not_reached_in_this_model"
    UNRESOLVED = "unresolved"
    NOT_FEASIBLE_IN_MODEL = "not_feasible_in_this_model"


class RouteQualification(StrEnum):
    PROPOSED_RECORDS = "proposed_records"
    ACCEPTED_ASSUMPTIONS = "accepted_assumptions"
    SYNTHETIC = "synthetic"
    CONDITIONAL_OFFER = "conditional_offer"
    CONDITIONAL_AWARD = "conditional_award"
    CONDITIONAL_APPLICATION = "conditional_application"
    CONDITIONAL_LOAN = "conditional_loan"  # a tuition fee loan not yet approved (Task 12c)
    READINESS_NOT_ASSESSED = "readiness_not_assessed"
    # Task 12b: it rests on a figure the person supplied (not reviewed), or on an option they
    # added themselves (their own record, never reviewed).
    SUPPLIED_FIGURES = "supplied_figures"
    OWN_OPTIONS = "own_options"


class Condition(StrictModel):
    """What the route rests on that has not happened, with its blocking verification: an
    offer to accept, an award to approve, a place to win by applying in time (an application
    the route itself does not hold, with no admission recorded), or a tuition fee loan to be
    approved (never an award: a loan is never support)."""

    kind: Literal["offer", "award", "application", "loan"]
    variant_id: str
    instrument_id: str | None
    verification: Literal[
        "confirm_offer_accepted",
        "verify_funding_award",
        "confirm_admission",
        "confirm_loan_approved",
    ]


class RouteCheck(StrictModel):
    input_version: str
    route: list[str]
    scenario: Scenario
    objective_basis: Literal["economic", "direct_spending"]
    horizon_months: int
    feasibility: Feasibility
    verdict: Verdict
    findings: list[Finding]
    # The route's own qualifications, then every one its readiness carries, by name: a
    # qualified readiness never gives an unqualified verdict (R9; ADR 0013 decision 10).
    qualifications: list[RouteQualification | Qualification]
    conditions: list[Condition]
    readiness_state: ReadinessState | None
    readiness_qualifications: list[Qualification]
    readiness_month: str | None  # the month boundary from which the milestone is reached
    months_to_readiness: int | None  # None: not reached in this model
    direct_cost: Money | None  # None: some cost is unknown, never 0
    income_change: SignedMoney | None  # the route's pay less the baseline's
    economic_cost: SignedMoney | None  # direct cost plus lost pay; negative is possible
    objective_cost: SignedMoney | None  # the comparison's cost: economic or direct only
    peak_monthly_payment: Money | None
    minimum_prefunded_cash: SignedMoney | None  # the lowest monthly lower bound
    # What a tuition fee loan paid straight to the provider pays, by month: a loan to repay
    # later, in neither the cash ledger nor direct spending (spec section 22; Task 12c).
    loans_to_repay: list[LoanToRepay]
    ledgers: Ledgers


class RouteEvaluation(StrictModel):
    """A fixed route under every declared scenario, the same set for every route (PLN-08)."""

    input_version: str
    route: list[str]
    delay_months: int
    checks: list[RouteCheck]

    def scenario(self, scenario: Scenario) -> RouteCheck:
        return next(c for c in self.checks if c.scenario is scenario)


def evaluate_route(monthly: MonthlyInput, route: Sequence[str]) -> RouteEvaluation:
    return RouteEvaluation(
        input_version=monthly.input_version,
        route=list(route),
        delay_months=monthly.inputs.scenario_delay_months,
        checks=[check_route(monthly, route, scenario) for scenario in Scenario],
    )


def _index(index: int | None) -> int:
    if index is None:
        raise ValueError("an unplaced variant has no months")
    return index


@dataclass
class _Timeline:
    """A present variant in one scenario: its months shifted by any delay."""

    variant: CompiledVariant
    shift: int

    @property
    def placed(self) -> bool:
        return self.variant.placed

    @property
    def start(self) -> int:
        return _index(self.variant.start_index) + self.shift

    @property
    def finish(self) -> int:
        return _index(self.variant.finish_index) + self.shift

    @property
    def usable(self) -> int:
        """The month from which what it grants is usable: the compiler's `usable_from`."""
        return _index(self.variant.usable_index) + self.shift

    def active(self, month: int) -> bool:
        return self.placed and self.start <= month <= self.finish


@dataclass
class _Cover:
    """Support paid to the provider: from which month it covers, and what of it is left."""

    offset: int
    support: Support
    left: int


@dataclass
class _Lender:
    """A tuition fee loan counted in this scenario: from which month of the variant it pays,
    and what of it is left. With its amount unknown (`left` None) it pays every fee in the
    known part: the least the person could pay, so a limit broken even then is broken."""

    offset: int
    conditional: bool
    left: int | None
    lent: dict[int | None, int] = field(default_factory=dict)  # by month index; None: unknown

    def lendable(self, owed: int) -> int:
        return owed if self.left is None else min(self.left, owed)

    def lend(self, index: int | None, owed: int) -> int:
        take = self.lendable(owed)
        if self.left is not None:
            self.left -= take
        if take:
            self.lent[index] = self.lent.get(index, 0) + take
        return take


@dataclass
class _Months:
    """Per-month amounts over the horizon, index 0 is the first month."""

    horizon: int
    payments: list[int] = field(init=False)
    to_provider: list[int] = field(init=False)
    support: list[int] = field(init=False)
    early: list[int] = field(init=False)
    later: list[int] = field(init=False)

    def __post_init__(self) -> None:
        self.payments = [0] * self.horizon
        self.to_provider = [0] * self.horizon
        self.support = [0] * self.horizon
        self.early = [0] * self.horizon
        self.later = [0] * self.horizon

    def within(self, index: int | None) -> bool:
        return index is not None and 1 <= index <= self.horizon


def _counts(support: Support, scenario: Scenario) -> bool:
    if support.confirmed:
        return True
    return support.conditional and scenario is not Scenario.NO_AWARD


def check_route(
    monthly: MonthlyInput, route: Sequence[str], scenario: Scenario = Scenario.BASE
) -> RouteCheck:
    return _Check(monthly, list(route), scenario).result()


class _Check:
    def __init__(self, monthly: MonthlyInput, route: list[str], scenario: Scenario) -> None:
        if len(set(route)) != len(route):
            raise CareerwrightError(
                ErrorCode.VALIDATION_FAILED,
                "A route names an option once.",
                stage=ErrorStage.PLANNING,
                details={"reason": "repeated_variant"},
            )
        if len(route) > MAX_SELECTED_ACTIONS:
            raise CareerwrightError(
                ErrorCode.MODEL_SCOPE_EXCEEDED,
                f"A route selects at most {MAX_SELECTED_ACTIONS} actions in this model.",
                stage=ErrorStage.PLANNING,
                details={"limit": MAX_SELECTED_ACTIONS},
            )
        self.monthly = monthly
        self.inputs = monthly.inputs
        self.route = route
        self.scenario = scenario
        self.horizon = monthly.inputs.horizon_months
        self.selected = [monthly.variant(v) for v in route]
        delay = monthly.inputs.scenario_delay_months
        self.present = [
            _Timeline(v, delay if scenario is Scenario.DELAY and v.conditional_offer else 0)
            for v in self.selected
            if not (scenario is Scenario.NO_OFFER and v.conditional_offer)
        ]
        self.findings: list[Finding] = []
        self.months = _Months(self.horizon)
        self.beyond: list[Liability] = []
        self.unscheduled: list[Liability] = []
        self.before_start: list[Liability] = []
        self.debts, self.debt_service = self._debts()
        self.costs_known = True
        # Every payment's amount and month is known, so each month's row is exact (a payment
        # before the start leaves the total unknown but the rows exact).
        self.payments_known = True
        self.support_outside = 0  # person-paid support received outside the horizon's months
        # A variant with no months can still bring pay or support: then the cash ledger is
        # not known, and a low month is not reported as a violation.
        self.receipts_known = all(
            t.placed
            or (
                t.variant.work_pattern is None
                and t.variant.wage is None
                and not any(s.paid_to == "person" for s in t.variant.supports)
            )
            for t in self.present
        )
        # For display only (review 12a, Important 1): a support paid to the person that may not
        # be combined with another still counts in the checks (the most cash the person could
        # have, so a reserve breach there is real), but no month shows it as a known receipt.
        self.receipts_shown = True
        self.conditions: list[Condition] = []
        self.loans: list[LoanToRepay] = []
        self.lent = 0  # what tuition fee loans paid: in the economic cost only
        # Support paid to the person set against a fee a loan paid: the economic cost only.
        self.support_beside_loans = 0

    def add(self, code: FindingCode, **values: object) -> None:
        kind = (
            FindingKind.UNRESOLVED
            if code in _UNRESOLVED
            else FindingKind.PREFERENCE
            if code is FindingCode.ECONOMIC_COST_CAP
            else FindingKind.VIOLATION
        )
        self.findings.append(Finding.model_validate({"code": code, "kind": kind, **values}))

    def label(self, index: int) -> str:
        return self.monthly.month_label(index)

    def result(self) -> RouteCheck:
        self._selection()
        self._work_rights()
        for timeline in self.present:
            self._costs(timeline)
        self._schemes()
        self._gates()
        income, hours = self._income_and_hours()
        self._workload(hours)
        income_ledger, lost = self._income_ledger(income)
        direct = self._direct_ledger()
        bounds = balances(
            self.inputs.opening_cash_minor,
            early=self.months.early,
            later=self.months.later,
            outflows=[
                living + paid + service
                for living, paid, service in zip(
                    self.inputs.living_outgoings_by_month,
                    self.months.payments,
                    self.debt_service,
                    strict=True,
                )
            ],
        )
        cash = liquidity(
            self.monthly.months,
            bounds,
            reserve_minor=self.inputs.reserve_minor,
            early=self.months.early,
            later=self.months.later,
            living=self.inputs.living_outgoings_by_month,
            payments=self.months.payments,
            debt_service=self.debt_service,
            payments_known=self.costs_known and self.payments_known,
            receipts_known=self.receipts_known and self.receipts_shown,
            complete=self.costs_known
            and self.receipts_known
            and all(t.placed for t in self.present),
        )
        self._caps(lost, bounds)
        readiness_state, readiness_qualifications, ready_at = self._readiness()
        # The economic cost counts a fee a tuition fee loan pays, once: the loan is repaid
        # later, so it moves when the person pays, never what the change costs (spec section
        # 12: loan principal is a liquidity source, not a discount; ADR 0013, Task 12c).
        economic = (
            max(0, self._net_paid() + self.lent - self.support_beside_loans)
            + income_ledger.difference_minor
            if direct.total_minor is not None and income_ledger.difference_minor is not None
            else None
        )
        if self.inputs.objective_basis == "economic" and self.inputs.baseline is None:
            self.add(FindingCode.BASELINE_MISSING)
        cap = self.inputs.economic_cost_cap_minor
        if cap is not None and economic is not None and economic > cap:
            self.add(FindingCode.ECONOMIC_COST_CAP, amount=economic, limit=cap, unit="minor_units")
        objective = economic if self.inputs.objective_basis == "economic" else direct.total_minor
        qualifications = self._qualifications(readiness_qualifications)
        feasibility = self._feasibility()
        complete_cash = cash.complete
        return RouteCheck(
            input_version=self.monthly.input_version,
            route=self.route,
            scenario=self.scenario,
            objective_basis=self.inputs.objective_basis,
            horizon_months=self.horizon,
            feasibility=feasibility,
            verdict=self._verdict(feasibility, qualifications, ready_at),
            findings=self.findings,
            qualifications=qualifications,
            conditions=self.conditions,
            readiness_state=readiness_state,
            readiness_qualifications=readiness_qualifications,
            readiness_month=self.label(ready_at) if ready_at is not None else None,
            months_to_readiness=ready_at - 1 if ready_at is not None else None,
            direct_cost=_money(direct.total_minor),
            income_change=_signed(
                -income_ledger.difference_minor
                if income_ledger.difference_minor is not None
                else None
            ),
            economic_cost=_signed(economic),
            objective_cost=_signed(objective),
            peak_monthly_payment=_money(
                max(self.months.payments) if complete_cash and self.months.payments else None
            ),
            minimum_prefunded_cash=_signed(
                min(lower for _, lower, _ in bounds) if complete_cash and bounds else None
            ),
            loans_to_repay=self.loans,
            ledgers=Ledgers(direct=direct, income=income_ledger, liquidity=cash, debts=self.debts),
        )

    # The selection and the gates (spec section 12, "Decision variables and prerequisites").

    def _selection(self) -> None:
        concepts: dict[str, int] = {}
        groups: dict[str, set[str]] = {}
        for variant in self.selected:
            concepts[variant.concept_id] = concepts.get(variant.concept_id, 0) + 1
            if variant.exclusive_group is not None:
                groups.setdefault(variant.exclusive_group, set()).add(variant.concept_id)
        for concept, count in sorted(concepts.items()):
            if count > 1:
                self.add(FindingCode.ONE_START_PER_CONCEPT, reason=concept)
        for group, members in sorted(groups.items()):
            if len(members) > 1:
                self.add(FindingCode.EXCLUSIVE_GROUP, reason=group)
        # A job or an apprenticeship behind an offer not yet accepted is a conditional job
        # transition, whatever the scenario; an accepted offer is the starting position.
        transitions = sum(v.conditional_offer for v in self.selected)
        if transitions > MOST_JOB_TRANSITIONS:
            self.add(FindingCode.JOB_TRANSITIONS, amount=transitions, limit=MOST_JOB_TRANSITIONS)
        for timeline in self.present:
            variant = timeline.variant
            if not variant.placed:
                self.add(
                    FindingCode.DATES_UNKNOWN,
                    variant_id=variant.variant_id,
                    reason="; ".join(variant.unplaced),
                )
            elif timeline.start < 1:
                self.add(FindingCode.STARTS_BEFORE_PLANNING, variant_id=variant.variant_id)
            if variant.entry_unconfirmed:
                self.add(FindingCode.ENTRY_REQUIREMENTS_UNCONFIRMED, variant_id=variant.variant_id)
            if variant.entry_not_met:
                self.add(FindingCode.ENTRY_REQUIREMENTS_NOT_MET, variant_id=variant.variant_id)
            if variant.entry_expected:
                self.add(FindingCode.ENTRY_REQUIREMENTS_EXPECTED, variant_id=variant.variant_id)

    def _work_rights(self) -> None:
        """Every route needs the right to work; this model checks no visa or sponsorship."""
        rights = self.inputs.work_rights
        if rights is WorkRights.UNKNOWN:
            self.add(FindingCode.WORK_RIGHTS_UNKNOWN)
        elif rights is WorkRights.NOT_HELD:
            self.add(FindingCode.WORK_RIGHTS_NOT_HELD)

    def _gates(self) -> None:
        initial = set(self.inputs.initial_gates)
        for timeline in self.present:
            variant = timeline.variant
            if not variant.placed:
                continue
            for gate in variant.prerequisites:
                if gate in initial:
                    continue
                givers = [t for t in self.present if t is not timeline and gate in t.variant.grants]
                if not givers and gate == variant.application_gate:
                    # No application in the route and no admission recorded: the route rests
                    # on applying in time, a condition, never "not feasible" (the controller's
                    # C09 ruling). A deadline already passed is still a violation.
                    self.conditions.append(
                        Condition(
                            kind="application",
                            variant_id=variant.variant_id,
                            instrument_id=None,
                            verification="confirm_admission",
                        )
                    )
                    continue
                if any(t.placed and t.usable <= timeline.start for t in givers):
                    continue
                if any(not t.placed for t in givers):
                    continue  # its own dates are unknown, already unresolved
                self.add(
                    FindingCode.PREREQUISITE_NOT_USABLE,
                    month=self.label(timeline.start),
                    variant_id=variant.variant_id,
                    reason=gate,
                )
            self._application(timeline, initial)

    def _application(self, timeline: _Timeline, initial: set[str]) -> None:
        variant = timeline.variant
        deadline, gate = variant.application_deadline, variant.application_gate
        if deadline is None or gate is None or gate in initial:
            return  # no deadline, or a completed application verified in the initial state
        if deadline < self.inputs.planning_start:
            self.add(
                FindingCode.APPLICATION_TOO_LATE,
                variant_id=variant.variant_id,
                reason=f"the deadline {deadline.isoformat()} has passed",
            )
            return
        timings = [
            application_timing(Month.parse(self.label(t.finish)), deadline)
            for t in self.present
            if t.placed and gate in t.variant.grants
        ]
        if not timings or ApplicationTiming.IN_TIME in timings:
            return  # no application selected: the prerequisite check reports it
        if ApplicationTiming.SAME_MONTH in timings:
            self.add(
                FindingCode.COARSE_MODEL_UNRESOLVED,
                month=str(Month.of(deadline)),
                variant_id=variant.variant_id,
                reason=f"its application completes in the deadline's month ({deadline})",
            )
        else:
            self.add(
                FindingCode.APPLICATION_TOO_LATE,
                variant_id=variant.variant_id,
                reason=f"its application completes after {deadline.isoformat()}",
            )

    # Money: payments, support and receipts (FIN1-02, FIN1-10).

    def _costs(self, timeline: _Timeline) -> None:
        variant = timeline.variant
        counted = [s for s in variant.supports if _counts(s, self.scenario)]
        for support in counted:
            if support.conditional:
                self.conditions.append(
                    Condition(
                        kind="award",
                        variant_id=variant.variant_id,
                        instrument_id=support.instrument_id,
                        verification="verify_funding_award",
                    )
                )
        if variant.conditional_offer:
            self.conditions.append(
                Condition(
                    kind="offer",
                    variant_id=variant.variant_id,
                    instrument_id=None,
                    verification="confirm_offer_accepted",
                )
            )
        # Support paid to the provider covers what falls due once the award is made: from the
        # start or, for a conditional award in the delay scenario, that many months later, so
        # the person pays whatever falls due before it arrives (ADR 0013 decision 9).
        covers = [
            _Cover(self._award_offset(s), s, s.amount_minor)
            for s in counted
            if s.paid_to == "provider"
        ]
        waived = any(c.support.covers_fees_in_full and c.offset == 0 for c in covers)
        if variant.cost_unknown is not None and not waived:
            self._unknown_payments()
            self.add(
                FindingCode.COST_UNKNOWN, variant_id=variant.variant_id, reason=variant.cost_unknown
            )
        loan = self._loan(timeline)
        due = self._due(timeline)
        recurring = variant.recurring
        if recurring is not None and not (waived or recurring.total_minor):
            self._unknown_payments()
            self.add(
                FindingCode.COST_UNKNOWN,
                variant_id=variant.variant_id,
                reason="the number or the exact amount of its payments is not stated",
            )
            # The least the person pays of one instalment: a loan paying from the start may
            # pay it, up to its amount (all of it, while its amount is unknown).
            instalment = recurring.amount.minor_units
            lendable = loan.lendable(instalment) if loan is not None and loan.offset == 0 else 0
            self._single_payment(instalment - lendable, variant.variant_id)
        # A stated fee that is an eligible learner's: while a condition is unconfirmed, the
        # stated payments stay a lower bound for the limits (funding never raises a price),
        # and the cost itself is not known. Where no fee is stated, its cost is the unknown.
        stated = variant.cost_unknown is None and (recurring is None or bool(recurring.total_minor))
        if stated and not waived and variant.unconfirmed_conditions:
            self._unknown_payments()
            for condition in variant.unconfirmed_conditions:
                self.add(
                    FindingCode.ELIGIBILITY_UNCONFIRMED,
                    variant_id=variant.variant_id,
                    reason=condition,
                )
        # Never assume two schemes stack (spec section 10): every counted support still reduces
        # the known part, the least the person could pay, so a limit broken even with all of
        # them is broken; whether they combine is unresolved until the person confirms it.
        if len(counted) > 1 and not variant.stacking_confirmed:
            self._unknown_support(counted)
            self.add(FindingCode.STACKING_UNCONFIRMED, variant_id=variant.variant_id)
        fees = gross = 0
        for index, kind, amount, when in sorted(due, key=lambda d: (d[0] is None, d[0] or 0)):
            covered = 0
            for cover in covers if kind != "extra" else []:
                if not self._covered(timeline, index, cover.offset):
                    continue
                owed = amount - covered
                take = owed if cover.support.covers_fees_in_full else min(cover.left, owed)
                covered += take
                cover.left -= take
            # A tuition fee loan pays what support leaves of a fee, never an extra cost: the
            # provider is paid, so it is neither the person's payment nor a receipt.
            lent = 0
            if loan is not None and kind != "extra" and self._covered(timeline, index, loan.offset):
                lent = loan.lend(index, amount - covered)
            paid = amount - covered - lent
            # Support paid to the person lowers the fees the person pays, so an option's own
            # direct spending never goes below £0 (search rule 3; review 12c, Critical 1). The
            # economic cost sets it against the whole fee, whoever pays it (`gross`).
            fees += paid if kind != "extra" else 0
            gross += paid + lent if kind != "extra" else 0
            if index is None:
                self.payments_known = False  # it could fall in any month
                self.unscheduled.append(
                    Liability(variant_id=variant.variant_id, due=None, amount_minor=paid)
                )
                self._single_payment(paid, variant.variant_id)
            elif index > self.horizon:
                self.beyond.append(
                    Liability(
                        variant_id=variant.variant_id, due=self.label(index), amount_minor=paid
                    )
                )
            elif index < 1:
                self._before_start(variant.variant_id, when or self.label(index), paid)
            else:
                self.months.payments[index - 1] += paid
                self.months.to_provider[index - 1] += covered
        for support in counted:
            if support.paid_to == "person":
                self._receipt(timeline, support, fees)
                # What the support lowers of the fee a loan paid: the economic cost only.
                self.support_beside_loans += min(support.amount_minor, gross) - min(
                    support.amount_minor, fees
                )
                fees = max(0, fees - support.amount_minor)
                gross = max(0, gross - support.amount_minor)
        if loan is not None:
            self._to_repay(variant, loan)

    def _loan(self, timeline: _Timeline) -> "_Lender | None":
        """The variant's tuition fee loan, if it counts in this scenario, as a conditional award
        would (ADR 0013 decisions 5 and 9): approved, in every scenario; not yet approved, the
        route rests on it in the base and delay scenarios only, and in the delay one it pays
        only the fees due `scenario_delay_months` or more after the variant starts."""
        variant = timeline.variant
        loan = variant.tuition_fee_loan
        if loan is None or not (
            loan.confirmed or (loan.conditional and self.scenario is not Scenario.NO_AWARD)
        ):
            return None
        if loan.amount is None:
            self._unknown_payments()
            self.add(FindingCode.LOAN_AMOUNT_UNKNOWN, variant_id=variant.variant_id)
        delayed = self.scenario is Scenario.DELAY and loan.conditional
        return _Lender(
            offset=self.inputs.scenario_delay_months if delayed else 0,
            conditional=loan.conditional,
            left=loan.amount.minor_units if loan.amount is not None else None,
        )

    def _to_repay(self, variant: CompiledVariant, loan: "_Lender") -> None:
        """What the loan paid, as a loan to repay: by the month each fee falls due, or, while
        its amount is unknown, one entry with neither amount nor month (never £0). A loan not
        yet approved makes the route rest on it only where it pays something or its amount is
        unknown: one that pays nothing changes nothing (review 12c, Minor 1)."""
        variant_id = variant.variant_id
        stated = variant.tuition_fee_loan
        kind = stated.kind if stated is not None else FeeLoanKind.TUITION_FEE_LOAN
        self.lent += sum(loan.lent.values())
        if loan.conditional and (loan.left is None or loan.lent):
            self.conditions.append(
                Condition(
                    kind="loan",
                    variant_id=variant_id,
                    instrument_id=None,
                    verification="confirm_loan_approved",
                )
            )
        if loan.left is None:
            self.loans.append(
                LoanToRepay(
                    variant_id=variant_id,
                    kind=kind,
                    due=None,
                    amount=None,
                    conditional=loan.conditional,
                )
            )
            return
        for index, amount in sorted(loan.lent.items(), key=lambda i: (i[0] is None, i[0] or 0)):
            self.loans.append(
                LoanToRepay(
                    variant_id=variant_id,
                    kind=kind,
                    due=self.label(index) if index is not None else None,
                    amount=_money(amount),
                    conditional=loan.conditional,
                )
            )

    def _unknown_payments(self) -> None:
        """Some payment's amount is not known: neither the total nor any month's row is."""
        self.costs_known = False
        self.payments_known = False

    def _unknown_support(self, supports: Iterable[Support]) -> None:
        """Supports that may not all apply: what the person pays is not known, and nor is any
        month's receipts where one of them is paid to the person."""
        self._unknown_payments()
        if any(s.paid_to == "person" for s in supports):
            self.receipts_shown = False

    def _schemes(self) -> None:
        """One scheme on several options, and schemes recorded as exclusive (review 12a,
        Important 2): only the supports that count in this scenario."""
        options: dict[str, list[str]] = {}
        supports: dict[str, list[Support]] = {}
        for timeline in self.present:
            for support in timeline.variant.supports:
                if not _counts(support, self.scenario):
                    continue
                named = options.setdefault(support.instrument_id, [])
                if timeline.variant.variant_id not in named:
                    named.append(timeline.variant.variant_id)
                supports.setdefault(support.instrument_id, []).append(support)
        shared = set(self.inputs.shared_schemes)
        for instrument, variants in sorted(options.items()):
            if len(variants) > 1 and instrument not in shared:
                self._unknown_support(supports[instrument])
                self.add(FindingCode.SCHEME_SHARED_UNCONFIRMED, reason=instrument)
        exclusions = self.monthly.scheme_exclusions
        counted = sorted(options)
        for n, first in enumerate(counted):
            for second in counted[n + 1 :]:
                if second in exclusions.get(first, []) or first in exclusions.get(second, []):
                    self.add(FindingCode.EXCLUSIVE_SCHEMES, reason=f"{first}, {second}")

    def _award_offset(self, support: Support) -> int:
        """Months after the variant's start at which an award is made."""
        delayed = self.scenario is Scenario.DELAY and support.conditional
        return self.inputs.scenario_delay_months if delayed else 0

    @staticmethod
    def _covered(timeline: _Timeline, index: int | None, offset: int) -> bool:
        if offset == 0:
            return True
        # A delayed award covers only a payment known to fall due after it arrives.
        return index is not None and timeline.placed and index >= timeline.start + offset

    def _before_start(self, variant_id: str, due: str, amount: int) -> None:
        """Due before the planning start: never dropped, and whether it was paid is never
        guessed, so the direct cost is unknown until the person says."""
        self.costs_known = False
        self.before_start.append(Liability(variant_id=variant_id, due=due, amount_minor=amount))
        self.add(
            FindingCode.PAYMENT_BEFORE_START,
            variant_id=variant_id,
            amount=amount,
            unit="minor_units",
            reason=f"due {due}, before the planning start {self.inputs.planning_start}",
        )

    def _due(self, timeline: _Timeline) -> list[tuple[int | None, str, int, str | None]]:
        """Each payment's month index, kind, amount and stated due date."""
        variant = timeline.variant
        start = self.monthly.start
        due: list[tuple[int | None, str, int, str | None]] = []
        for payment in variant.payments:
            if payment.due is not None:
                index: int | None = Month.of(payment.due).months_after(start) + 1 + timeline.shift
            elif variant.placed and payment.offset is not None:
                index = timeline.start + payment.offset
            else:
                index = None
            stated = payment.due.isoformat() if payment.due is not None else None
            due.append((index, payment.kind, payment.amount_minor, stated))
        recurring = variant.recurring
        if recurring is not None and recurring.total_minor and recurring.count:
            for n in range(recurring.count):
                index = timeline.start + n if variant.placed else None
                due.append((index, "instalment", recurring.amount.minor_units, None))
        return due

    def _single_payment(self, amount: int, variant_id: str) -> None:
        """A payment whose month is unknown still exceeds the monthly cap in any month, with
        the least any month's debt repayments add (spec section 12: P_m + R_m <= M_m). Where
        those repayments alone already exceed it, they are named instead, never the option."""
        cap = self.inputs.monthly_payment_cap_minor
        least = min(self.debt_service, default=0)
        total = amount + least
        if cap is not None and least <= cap < total:
            self.add(
                FindingCode.MONTHLY_PAYMENT_CAP,
                variant_id=variant_id,
                amount=total,
                limit=cap,
                unit="minor_units",
            )

    def _receipt(self, timeline: _Timeline, support: Support, fees: int) -> None:
        """Support paid to the person: a receipt in its month, and direct cost less it, once.
        Unconfirmed support is never proven early, so it never pays for an earlier outflow."""
        amount = support.amount_minor or 0
        offset = support.paid_month_offset or 0
        delayed = self.scenario is Scenario.DELAY and support.conditional
        shift = self.inputs.scenario_delay_months if delayed else 0
        index = timeline.start + offset + shift if timeline.placed else None
        applied = min(amount, fees)
        if index is not None and self.months.within(index):
            if support.confirmed and support.proven_before_outflows:
                self.months.early[index - 1] += amount
            else:
                self.months.later[index - 1] += amount
            self.months.support[index - 1] += applied
        else:
            self.support_outside += applied  # no month in the horizon: direct cost only

    # Income and hours (FIN-1, TIME-1 workload).

    def _income_and_hours(self) -> tuple[list[int], list[int]]:
        income, hours = [], []
        continuation = self.inputs.continuation
        for month in range(1, self.horizon + 1):
            patterns = [
                t.variant.work_pattern
                for t in self.present
                if t.active(month) and t.variant.work_pattern is not None
            ]
            job: WorkPattern | None = patterns[0] if patterns else None
            if len({(p.kind, p.hours_per_week, p.net_income) for p in patterns}) > 1:
                self.add(FindingCode.CONFLICTING_WORK_PATTERNS, month=self.label(month))
            pay = job.net_income.minor_units if job else continuation.net_income_by_month[month - 1]
            self._pay(month, pay, self.inputs.wage_timing)
            total = pay
            for timeline in self.present:
                wage = timeline.variant.wage
                if wage is None or not timeline.active(month):
                    continue
                total += wage.net_income.minor_units
                timing = (
                    ReceiptTiming.LATER
                    if timeline.variant.conditional_offer
                    else self.inputs.wage_timing
                )
                self._pay(month, wage.net_income.minor_units, timing)
            income.append(total)
            hours.append(job.hours_per_week if job else continuation.hours_per_week)
        return income, hours

    def _pay(self, month: int, amount: int, timing: ReceiptTiming) -> None:
        if timing is ReceiptTiming.BEFORE_OUTFLOWS:
            self.months.early[month - 1] += amount
        else:
            self.months.later[month - 1] += amount

    def _workload(self, job_hours: list[int]) -> None:
        availability = self.inputs.weekly_availability_by_month
        if availability is None:
            self.add(FindingCode.WORKLOAD_UNKNOWN, reason="weekly availability is not stated")
            return
        fixed = sum(c.hours_per_week for c in self.inputs.commitments)
        for month in range(1, self.horizon + 1):
            active = [t for t in self.present if t.active(month)]
            known = job_hours[month - 1] + fixed
            known += sum(t.variant.weekly_hours or 0 for t in active)
            limit = availability[month - 1]
            if known > limit:
                self.add(
                    FindingCode.WORKLOAD,
                    month=self.label(month),
                    amount=known,
                    limit=limit,
                    unit="hours_per_week",
                )
            elif any(t.variant.weekly_hours is None for t in active):
                self.add(
                    FindingCode.WORKLOAD_UNKNOWN,
                    month=self.label(month),
                    reason="a timetable assumption must be confirmed",
                )
        for timeline in self.present:
            hours = timeline.variant.weekly_hours
            pattern = timeline.variant.work_pattern
            if timeline.placed:
                continue
            if hours is None:
                self.add(
                    FindingCode.WORKLOAD_UNKNOWN,
                    variant_id=timeline.variant.variant_id,
                    reason="no weekly hours or timetable are stated",
                )
                continue
            job = pattern.hours_per_week if pattern else self.inputs.continuation.hours_per_week
            if hours + job + fixed > max(availability):
                self.add(
                    FindingCode.WORKLOAD,
                    variant_id=timeline.variant.variant_id,
                    amount=hours + job + fixed,
                    limit=max(availability),
                    unit="hours_per_week",
                )
        self._clashes()

    def _clashes(self) -> None:
        placed = [t for t in self.present if t.placed and t.variant.sessions]
        for n, first in enumerate(placed):
            for second in placed[n + 1 :]:
                common = [
                    m for m in range(1, self.horizon + 1) if first.active(m) and second.active(m)
                ]
                clash = any(
                    a.overlaps(b) for a in first.variant.sessions for b in second.variant.sessions
                )
                if common and clash:
                    self.add(
                        FindingCode.SESSION_CLASH,
                        month=self.label(common[0]),
                        variant_id=second.variant.variant_id,
                        reason=first.variant.variant_id,
                    )

    def _debts(self) -> tuple[list[DebtLedger], list[int]]:
        ledgers: list[DebtLedger] = []
        service = [0] * self.horizon
        for existing in self.inputs.existing_debts:
            ledger, paid = debt(
                existing.debt_id,
                self.monthly.months,
                balance_minor=existing.balance_minor,
                annual_bps=existing.annual_interest_bps,
                repayment_minor=existing.monthly_repayment_minor,
            )
            ledgers.append(ledger)
            service = [a + b for a, b in zip(service, paid, strict=True)]
        return ledgers, service

    # Ledgers and limits (S5.5).

    def _income_ledger(self, income: list[int]) -> tuple[IncomeLedger, list[int]]:
        """The income ledger, and each month's known pay lost against the baseline (0 without
        one) for the deficit cap. Pay from an option with no months could fall in any month,
        so then no month's route income is shown."""
        baseline = self.inputs.baseline
        complete = all(
            t.placed or (t.variant.work_pattern is None and t.variant.wage is None)
            for t in self.present
        )
        lost = [
            baseline.net_income_by_month[n] - pay if baseline else 0 for n, pay in enumerate(income)
        ]
        months = [
            IncomeMonth(
                month=self.label(n + 1),
                baseline_minor=baseline.net_income_by_month[n] if baseline else None,
                route_minor=pay if complete else None,
                difference_minor=lost[n] if baseline and complete else None,
            )
            for n, pay in enumerate(income)
        ]
        difference = sum(lost) if baseline is not None and complete else None
        ledger = IncomeLedger(
            baseline_label=baseline.label if baseline else None,
            continuation_label=self.inputs.continuation.label,
            months=months,
            complete=complete,
            difference_minor=difference,
        )
        return ledger, lost

    def _direct_ledger(self) -> DirectLedger:
        known = self.payments_known  # else a month's figures would be partial ones
        months = [
            DirectMonth(
                month=self.label(n + 1),
                payments_minor=self.months.payments[n] if known else None,
                paid_to_provider_minor=self.months.to_provider[n] if known else None,
                support_minor=self.months.support[n] if known else None,
            )
            for n in range(self.horizon)
        ]
        total = self._net_paid()
        return DirectLedger(
            months=months,
            beyond_horizon=self.beyond,
            unscheduled=self.unscheduled,
            before_start=self.before_start,
            complete=self.costs_known,
            total_minor=max(0, total) if self.costs_known else None,
        )

    def _net_paid(self) -> int:
        """What the person pays, every month, after the horizon and with no month yet, less the
        support paid to them that counts against it: possibly below zero. A fee a tuition fee
        loan pays is not in it."""
        return (
            sum(self.months.payments)
            + sum(i.amount_minor for i in self.beyond)
            + sum(i.amount_minor for i in self.unscheduled)
            - sum(self.months.support)
            - self.support_outside
        )

    def _caps(self, lost: list[int], bounds: list[tuple[int, int, int]]) -> None:
        inputs = self.inputs
        # The known part only: an unknown cost can only add to it, so exceeding a cap on the
        # known part is a violation whatever the rest turns out to be.
        known = self._net_paid()
        # An unknown hard limit is never a pass (review I2): the deficit cap applies only when
        # the person sets one, and the economic-cost cap is a preference, so neither is here.
        for name, value in (
            ("direct_spend_cap", inputs.direct_spend_cap_minor),
            ("monthly_payment_cap", inputs.monthly_payment_cap_minor),
            ("reserve", inputs.reserve_minor),
        ):
            if value is None:
                self.add(FindingCode.LIMIT_UNKNOWN, reason=name)
        if inputs.direct_spend_cap_minor is not None and known > inputs.direct_spend_cap_minor:
            self.add(
                FindingCode.DIRECT_SPEND_CAP,
                amount=known,
                limit=inputs.direct_spend_cap_minor,
                unit="minor_units",
            )
        cap = inputs.monthly_payment_cap_minor
        for n, amount in enumerate(self.months.payments):
            # Spec section 12: P_m + R_m <= M_m, every repayment included (ADR 0013 decision 6;
            # session 2, D15 yes). Repayments alone above it are named as the repayments.
            repaying = self.debt_service[n]
            if cap is not None and repaying > cap:
                self.add(
                    FindingCode.REPAYMENTS_ABOVE_PAYMENT_CAP,
                    month=self.label(n + 1),
                    amount=repaying,
                    limit=cap,
                    unit="minor_units",
                    reason=", ".join(
                        d.debt_id for d in self.debts if d.months[n].repayment_minor > 0
                    ),
                )
            elif cap is not None and amount + repaying > cap:
                self.add(
                    FindingCode.MONTHLY_PAYMENT_CAP,
                    month=self.label(n + 1),
                    amount=amount + repaying,
                    limit=cap,
                    unit="minor_units",
                )
        deficit_cap = inputs.monthly_deficit_cap_minor
        if deficit_cap is not None:
            if inputs.baseline is None:
                self.add(FindingCode.BASELINE_MISSING, reason="the deficit cap needs a baseline")
            else:
                for n, pay_lost in enumerate(lost):
                    deficit = self.months.payments[n] - self.months.support[n] + pay_lost
                    if deficit > deficit_cap:
                        self.add(
                            FindingCode.MONTHLY_DEFICIT_CAP,
                            month=self.label(n + 1),
                            amount=deficit,
                            limit=deficit_cap,
                            unit="minor_units",
                        )
        reserve = inputs.reserve_minor
        if reserve is not None and self.receipts_known and all(t.placed for t in self.present):
            # The known part: an unknown payment can only lower a month's bound further.
            for n, (_, lower, _) in enumerate(bounds):
                if lower < reserve:
                    self.add(
                        FindingCode.RESERVE,
                        month=self.label(n + 1),
                        amount=lower,
                        limit=reserve,
                        unit="minor_units",
                    )

    # Readiness: the capability model decides it (RDY-1); this only asks it month by month.

    def _readiness(self) -> tuple[ReadinessState | None, list[Qualification], int | None]:
        basis = self.monthly.readiness
        if basis is None:
            return None, [], None

        def at(completed: frozenset[str] | None) -> Assessment:
            return assess(
                basis.matrix,
                evidence=basis.evidence,
                statements=basis.statements,
                outcomes=basis.outcomes,
                evidence_version=basis.evidence_version,
                completed=completed,
            )

        current = at(None)
        if current.state is ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS:
            return current.state, current.qualifications, 1
        placed = [t for t in self.present if t.placed]
        boundaries = sorted({t.usable for t in placed if t.usable <= self.horizon + 1})
        last = current
        for boundary in boundaries:
            done = frozenset(t.variant.outcome_offering_id for t in placed if t.usable <= boundary)
            last = at(done)
            if last.state in READY:
                return last.state, last.qualifications, boundary
        return last.state, last.qualifications, None

    def _qualifications(
        self, readiness: list[Qualification]
    ) -> list[RouteQualification | Qualification]:
        states = {s for v in self.selected for s in v.review_states}
        found: list[RouteQualification | Qualification] = []
        if RecordState.PROPOSED in states:
            found.append(RouteQualification.PROPOSED_RECORDS)
        if RecordState.ACCEPTED_ASSUMPTION in states:
            found.append(RouteQualification.ACCEPTED_ASSUMPTIONS)
        if self.inputs.synthetic or any(v.synthetic for v in self.selected):
            found.append(RouteQualification.SYNTHETIC)
        if any(c.kind == "offer" for c in self.conditions):
            found.append(RouteQualification.CONDITIONAL_OFFER)
        if any(c.kind == "award" for c in self.conditions):
            found.append(RouteQualification.CONDITIONAL_AWARD)
        if any(c.kind == "application" for c in self.conditions):
            found.append(RouteQualification.CONDITIONAL_APPLICATION)
        if any(c.kind == "loan" for c in self.conditions):
            found.append(RouteQualification.CONDITIONAL_LOAN)
        if self.monthly.readiness is None:
            found.append(RouteQualification.READINESS_NOT_ASSESSED)
        if any(v.supplied for v in self.selected):
            found.append(RouteQualification.SUPPLIED_FIGURES)
        if any(v.added_by_person for v in self.selected):
            found.append(RouteQualification.OWN_OPTIONS)
        # Every qualification readiness carries, by name, the provisional matrix included: in
        # L0 a route resting on the pack reads qualified (R9; ADR 0013 decision 10). A name
        # both lists share ("proposed_records") is listed once.
        found += [q for q in readiness if q.value not in {f.value for f in found}]
        return found

    def _feasibility(self) -> Feasibility:
        kinds = {f.kind for f in self.findings}
        if FindingKind.VIOLATION in kinds:
            return Feasibility.NOT_FEASIBLE_IN_MODEL
        if FindingKind.UNRESOLVED in kinds:
            return Feasibility.UNRESOLVED
        return Feasibility.FEASIBLE

    def _verdict(
        self,
        feasibility: Feasibility,
        qualifications: list[RouteQualification | Qualification],
        ready_at: int | None,
    ) -> Verdict:
        if feasibility is Feasibility.NOT_FEASIBLE_IN_MODEL:
            return Verdict.NOT_FEASIBLE_IN_MODEL
        if feasibility is Feasibility.UNRESOLVED:
            return Verdict.UNRESOLVED
        if self.monthly.readiness is not None and ready_at is None:
            return Verdict.READINESS_NOT_REACHED
        return Verdict.QUALIFIED if qualifications else Verdict.AFFORDABLE_AND_FEASIBLE


def _money(minor: int | None) -> Money | None:
    return None if minor is None else Money(minor_units=minor, currency="GBP")


def _signed(minor: int | None) -> SignedMoney | None:
    return None if minor is None else SignedMoney(minor_units=minor, currency="GBP")
