"""The route checker: one fixed candidate route on the immutable monthly input, in one of the
fixed scenarios (spec section 12, TIME-1, FIN-1, "Hard feasibility constraints" and
"Uncertainty and conditional plans"; S5.4-S5.6). Pure and deterministic: no SQL, no network,
no model, so the route search (Task 13a) can call it for every candidate.

What it reports, kept apart (Global Constraint 6):

- **Violations**, each named on its own: the direct-spend cap, the monthly payment cap, the
  monthly deficit cap and the reserve are four different limits, and the workload envelope
  and a session clash are two. Every one found is listed, never only the first. A violation
  is a conservative rejection by this monthly model, never a claim that the person cannot
  afford a real schedule.
- **Unresolved findings:** unknown dates, cost or timetable, a same-month application ("not
  resolved by this monthly model", never "ineligible"), a missing baseline. Unknown never
  passes and is never zero.
- **Ledgers and objectives:** the direct-spend, income-difference, liquidity and debt ledgers;
  months to the modelled application-readiness milestone, which the capability model decides;
  direct and economic cost.
- **Qualifications and conditions:** proposed records, accepted assumptions, synthetic data,
  and the conditions a route rests on (an offer to accept, an award to approve), each with a
  blocking verification. Only a route with none is "affordable and feasible" unqualified
  (OPTN-09).

Scenarios (S5.6): `base` assumes each condition happens as planned; `delay` moves every
conditional offer and award `scenario_delay_months` later; `no_award` drops every award not
already approved; `no_offer` drops every activity behind an offer not already accepted, so
its wages and its experience go together. No adaptive policy is optimised and no hiring
probability is invented.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from careerwright.capability.readiness import Assessment, Qualification, ReadinessState, assess
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.money import Money, SignedMoney
from careerwright.planning.catalogue import RecordState, Support, WorkPattern
from careerwright.planning.compiler import CompiledVariant, MonthlyInput, ReceiptTiming
from careerwright.planning.ledgers import (
    DebtLedger,
    DirectLedger,
    DirectMonth,
    IncomeLedger,
    IncomeMonth,
    Ledgers,
    Liability,
    LiquidityMonth,
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
    }
)


class Finding(StrictModel):
    code: FindingCode
    kind: FindingKind
    month: str | None = None  # None: whatever month it falls in
    variant_id: str | None = None
    amount: int | None = None
    limit: int | None = None
    unit: Literal["minor_units", "hours_per_week"] | None = None
    reason: str | None = None  # the gate, or why a value is unknown


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
    READINESS_NOT_ASSESSED = "readiness_not_assessed"


class Condition(StrictModel):
    """What the route rests on that has not happened, with its blocking verification."""

    kind: Literal["offer", "award"]
    variant_id: str
    instrument_id: str | None
    verification: Literal["confirm_offer_accepted", "verify_funding_award"]


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
        self.conditions: list[Condition] = []

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
        for timeline in self.present:
            self._costs(timeline)
        self._gates()
        income, hours = self._income_and_hours()
        self._workload(hours)
        income_ledger = self._income_ledger(income)
        direct = self._direct_ledger()
        cash = liquidity(
            self.monthly.months,
            opening_minor=self.inputs.opening_cash_minor,
            reserve_minor=self.inputs.reserve_minor,
            early=self.months.early,
            later=self.months.later,
            living=self.inputs.living_outgoings_by_month,
            payments=self.months.payments,
            debt_service=self.debt_service,
            complete=self.costs_known
            and self.receipts_known
            and all(t.placed for t in self.present),
        )
        self._caps(income_ledger, cash.months)
        readiness_state, readiness_qualifications, ready_at = self._readiness()
        economic = (
            direct.total_minor + income_ledger.difference_minor
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
                min(m.lower_bound_minor for m in cash.months) if complete_cash else None
            ),
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
            self.costs_known = False
            self.add(
                FindingCode.COST_UNKNOWN, variant_id=variant.variant_id, reason=variant.cost_unknown
            )
        due = self._due(timeline)
        if variant.recurring is not None and not (waived or variant.recurring.total_minor):
            self.costs_known = False
            self.add(
                FindingCode.COST_UNKNOWN,
                variant_id=variant.variant_id,
                reason="the number or the exact amount of its payments is not stated",
            )
            self._single_payment(variant.recurring.amount.minor_units, variant.variant_id)
        fees = 0
        for index, kind, amount, when in sorted(due, key=lambda d: (d[0] is None, d[0] or 0)):
            covered = 0
            for cover in covers if kind != "extra" else []:
                if not self._covered(timeline, index, cover.offset):
                    continue
                owed = amount - covered
                take = owed if cover.support.covers_fees_in_full else min(cover.left, owed)
                covered += take
                cover.left -= take
            paid = amount - covered
            fees += paid if kind != "extra" else 0
            if index is None:
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
                fees = max(0, fees - support.amount_minor)

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
        the least any month's debt repayments add (spec section 12: P_m + R_m <= M_m)."""
        cap = self.inputs.monthly_payment_cap_minor
        total = amount + min(self.debt_service, default=0)
        if cap is not None and total > cap:
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

    def _income_ledger(self, income: list[int]) -> IncomeLedger:
        baseline = self.inputs.baseline
        complete = all(
            t.placed or (t.variant.work_pattern is None and t.variant.wage is None)
            for t in self.present
        )
        months = [
            IncomeMonth(
                month=self.label(n + 1),
                baseline_minor=baseline.net_income_by_month[n] if baseline else None,
                route_minor=pay,
                difference_minor=baseline.net_income_by_month[n] - pay if baseline else None,
            )
            for n, pay in enumerate(income)
        ]
        difference = (
            sum(m.difference_minor or 0 for m in months)
            if baseline is not None and complete
            else None
        )
        return IncomeLedger(
            baseline_label=baseline.label if baseline else None,
            continuation_label=self.inputs.continuation.label,
            months=months,
            complete=complete,
            difference_minor=difference,
        )

    def _direct_ledger(self) -> DirectLedger:
        months = [
            DirectMonth(
                month=self.label(n + 1),
                payments_minor=self.months.payments[n],
                paid_to_provider_minor=self.months.to_provider[n],
                support_minor=self.months.support[n],
            )
            for n in range(self.horizon)
        ]
        paid = (
            sum(self.months.payments)
            + sum(item.amount_minor for item in self.beyond)
            + sum(item.amount_minor for item in self.unscheduled)
        )
        total = paid - sum(self.months.support) - self.support_outside
        return DirectLedger(
            months=months,
            beyond_horizon=self.beyond,
            unscheduled=self.unscheduled,
            before_start=self.before_start,
            complete=self.costs_known,
            total_minor=max(0, total) if self.costs_known else None,
        )

    def _caps(self, income: IncomeLedger, cash: list[LiquidityMonth]) -> None:
        inputs = self.inputs
        # The known part only: an unknown cost can only add to it, so exceeding a cap on the
        # known part is a violation whatever the rest turns out to be.
        known = (
            sum(self.months.payments)
            + sum(i.amount_minor for i in self.beyond)
            + sum(i.amount_minor for i in self.unscheduled)
            - sum(self.months.support)
            - self.support_outside
        )
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
            # Spec section 12: P_m + R_m <= M_m, every repayment included (ADR 0013 decision 6).
            outgoing = amount + self.debt_service[n]
            if cap is not None and outgoing > cap:
                self.add(
                    FindingCode.MONTHLY_PAYMENT_CAP,
                    month=self.label(n + 1),
                    amount=outgoing,
                    limit=cap,
                    unit="minor_units",
                )
        deficit_cap = inputs.monthly_deficit_cap_minor
        if deficit_cap is not None:
            if inputs.baseline is None:
                self.add(FindingCode.BASELINE_MISSING, reason="the deficit cap needs a baseline")
            else:
                for n, row in enumerate(income.months):
                    deficit = (
                        self.months.payments[n]
                        - self.months.support[n]
                        + (row.difference_minor or 0)
                    )
                    if deficit > deficit_cap:
                        self.add(
                            FindingCode.MONTHLY_DEFICIT_CAP,
                            month=row.month,
                            amount=deficit,
                            limit=deficit_cap,
                            unit="minor_units",
                        )
        reserve = inputs.reserve_minor
        if reserve is not None and self.receipts_known and all(t.placed for t in self.present):
            for cash_month in cash:
                if cash_month.lower_bound_minor < reserve:
                    self.add(
                        FindingCode.RESERVE,
                        month=cash_month.month,
                        amount=cash_month.lower_bound_minor,
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
        if self.monthly.readiness is None:
            found.append(RouteQualification.READINESS_NOT_ASSESSED)
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
