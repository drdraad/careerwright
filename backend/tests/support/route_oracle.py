"""An independent Cartesian-product oracle and an independently written route checker, for
tiny search instances (spec section 12: "Correctness tests compare this DFS against a simple
independent Cartesian-product oracle on tiny instances"; S6.6; OPT1-08). Test code only.

It shares no code with what it checks: nothing from `careerwright.planning.search`, `layers`,
`families`, `checker`, `ledgers` or `months`, no helper and no constant. It reads only the
input data types (`MonthlyInput` and the records in it, their raw fields rather than their
convenience properties) and asks the capability model for readiness, which planning code never
decides (RDY-1). Every rule is written again from the specification and ADR 0013, plainly and
slowly: every combination of the catalogue, one route at a time, month by month, no pruning.
It reads the base scenario only, as the search does.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from itertools import product
from typing import Literal

from careerwright.capability.readiness import ReadinessState, assess
from careerwright.planning.catalogue import (
    ActionKind,
    AwardState,
    EligibilityStatus,
    Session,
    Support,
)
from careerwright.planning.compiler import (
    CompiledVariant,
    MonthlyInput,
    ReceiptTiming,
    WorkRights,
)

MOST_ACTIONS = 6  # spec section 12: at most six selected actions
# Spec section 12: at most one conditional bridge-role transition, that is one job or
# apprenticeship the route moves into behind an offer the person has not yet accepted.
MOST_OFFERS_TO_AWAIT = 1
REACHED = frozenset(
    {
        ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION,
        ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS,
    }
)
NOT_YET_KNOWN = frozenset({ReadinessState.NOT_YET_ASSESSED, ReadinessState.INSUFFICIENT_COVERAGE})

Status = Literal["feasible", "not_feasible", "unresolved"]
Route = frozenset[str]


@dataclass(frozen=True)
class Checked:
    status: Status
    months: int | None  # to the readiness milestone; None when not reached
    cost: int | None  # the comparison's cost: economic, or direct only
    readiness: ReadinessState | None  # the last state the route reaches


@dataclass(frozen=True)
class Solved:
    checks: dict[Route, Checked]
    archive: dict[Route, tuple[int, int]]  # feasible and at the milestone: (months, cost)
    layers: dict[Route, int]  # every archived route's layer, however deep
    without_milestone: int
    # Some route is unresolved, a feasible route's readiness is not yet known, an input is not
    # stated, or an option has an unknown of its own and no breach of its own: then "no route"
    # would be a guess, because knowing the unknown might change the answer.
    something_unknown: bool


class Oracle:
    def __init__(self, monthly: MonthlyInput) -> None:
        self.monthly = monthly
        self.by_id = {v.variant_id: v for v in monthly.variants}
        self.assessed: dict[frozenset[str] | None, ReadinessState] = {}

    def routes(self) -> Iterator[Route]:
        """Every combination: for each concept, nothing or one of its variants; then the
        model's bounds (six actions, one per exclusive group, one bridge role)."""
        concepts: dict[str, list[CompiledVariant]] = {}
        for variant in self.monthly.variants:
            concepts.setdefault(variant.concept_id, []).append(variant)
        for picks in product(*([None, *vs] for vs in concepts.values())):
            chosen = [v for v in picks if v is not None]
            groups = [v.exclusive_group for v in chosen if v.exclusive_group is not None]
            bridges = [v for v in chosen if v.kind is ActionKind.WORK]
            if (
                len(chosen) <= MOST_ACTIONS
                and len(groups) == len(set(groups))
                and len(bridges) <= 1
            ):
                yield frozenset(v.variant_id for v in chosen)

    def solve(self) -> Solved:
        checks = {route: self.check(route) for route in self.routes()}
        archive = {
            route: (c.months, c.cost)
            for route, c in checks.items()
            if c.status == "feasible" and c.months is not None and c.cost is not None
        }
        return Solved(
            checks=checks,
            archive=archive,
            layers=_layers(archive),
            without_milestone=sum(
                c.status == "feasible" and c.months is None for c in checks.values()
            ),
            something_unknown=self._inputs_unknown()
            or any(self._unknown_alone(v) for v in self.monthly.variants)
            or any(
                c.status == "unresolved"
                or (c.status == "feasible" and c.months is None and c.readiness in NOT_YET_KNOWN)
                for c in checks.values()
            ),
        )

    def _inputs_unknown(self) -> bool:
        """A hard limit, the weekly availability, or a baseline the comparison needs is not
        stated, or the person is not known to hold the right to work (no visa or sponsorship
        is checked here, so a "no" is not known either way)."""
        inputs = self.monthly.inputs
        limits = (inputs.direct_spend_cap_minor, inputs.monthly_payment_cap_minor)
        needs_baseline = (
            inputs.objective_basis == "economic" or inputs.monthly_deficit_cap_minor is not None
        )
        return (
            None in limits
            or inputs.reserve_minor is None
            or inputs.weekly_availability_by_month is None
            or (needs_baseline and inputs.baseline is None)
            or inputs.work_rights is not WorkRights.HELD
        )

    def _unknown_alone(self, v: CompiledVariant) -> bool:
        """The option has an unknown of its own (its dates, cost, weekly hours or entry
        requirements, the person's "no" to them, a payment before the start, an unconfirmed
        eligibility condition of its fee, or supports not confirmed to stack) and breaks nothing
        that would rule out every route containing it whatever the unknown turns out to be (its
        own spend above a cap, a start before the planning start, a deadline already passed)."""
        inputs = self.monthly.inputs
        alone = _RouteCheck(self, [v])
        alone._money(v)  # its own payments and support, and any single payment above the cap
        horizon = alone._each_month()
        unknown = (
            not _placed(v)
            or v.entry_unconfirmed
            or v.entry_not_met
            or not alone.costs_known
            or (v.weekly_hours is None and any(_active(v, m) for m in horizon))
        )
        direct_cap, monthly_cap = inputs.direct_spend_cap_minor, inputs.monthly_payment_cap_minor
        breach = (
            alone.broken
            or (_placed(v) and v.start_index is not None and v.start_index < 1)
            or (
                v.application_deadline is not None
                and v.application_gate is not None
                and v.application_gate not in inputs.initial_gates
                and v.application_deadline < inputs.planning_start
            )
            or (direct_cap is not None and alone.direct > direct_cap)
            or (
                monthly_cap is not None
                and any(alone.payments[m] + alone.debt[m] > monthly_cap for m in horizon)
            )
        )
        return unknown and not breach

    def check(self, route: Route) -> Checked:
        return _RouteCheck(self, [self.by_id[v] for v in sorted(route)]).run()

    def readiness(self, completed: frozenset[str] | None) -> ReadinessState:
        if completed not in self.assessed:
            basis = self.monthly.readiness
            if basis is None:
                raise ValueError("the oracle needs a readiness basis")
            self.assessed[completed] = assess(
                basis.matrix,
                evidence=basis.evidence,
                statements=basis.statements,
                outcomes=basis.outcomes,
                evidence_version=basis.evidence_version,
                completed=completed,
            ).state
        return self.assessed[completed]


def _layers(archive: dict[Route, tuple[int, int]]) -> dict[Route, int]:
    """A route's layer: one more than the deepest layer of any route better on one objective
    and no worse on the other (a longest chain, rather than peeling)."""
    depth: dict[Route, int] = {}
    for route in sorted(archive, key=lambda r: archive[r]):
        months, cost = archive[route]
        better = [
            depth[other]
            for other in depth
            if archive[other][0] <= months
            and archive[other][1] <= cost
            and archive[other] != (months, cost)
        ]
        depth[route] = 1 + max(better, default=0)
    return depth


def _counted(support: Support) -> bool:
    """In the base scenario: an approved award, or an award the person assumes for this route
    that is not refused and for which they are or may be eligible."""
    if support.award is AwardState.APPROVED:
        return True
    return (
        support.assumed
        and support.award is not AwardState.REFUSED
        and support.eligibility
        in (EligibilityStatus.CONFIRMED, EligibilityStatus.POTENTIALLY_ELIGIBLE)
    )


def _overlap(a: Session, b: Session) -> bool:
    return a.weekday == b.weekday and a.starts < b.ends and b.starts < a.ends


class _RouteCheck:
    """One route, base scenario. Lists are indexed by month number, 1 to the horizon."""

    def __init__(self, oracle: Oracle, chosen: list[CompiledVariant]) -> None:
        self.oracle = oracle
        self.inputs = oracle.monthly.inputs
        self.months = self.inputs.horizon_months
        self.chosen = chosen
        self.broken = False  # a violation: not feasible in this model
        self.unknown = False  # unresolved, where nothing is broken
        self.payments = [0] * (self.months + 1)
        self.support = [0] * (self.months + 1)
        self.early = [0] * (self.months + 1)
        self.late = [0] * (self.months + 1)
        self.income = [0] * (self.months + 1)
        self.hours = [0] * (self.months + 1)
        self.direct = 0  # the known part of direct cost
        self.costs_known = True
        self.debt = self._debt()

    def run(self) -> Checked:
        if self.inputs.work_rights is not WorkRights.HELD:
            self.unknown = True
        awaiting = [v for v in self.chosen if v.offer_gate and not v.offer_gate.accepted]
        if len(awaiting) > MOST_OFFERS_TO_AWAIT:
            self.broken = True
        for v in self.chosen:
            if v.start_date is None or v.finish_date is None:
                self.unknown = True
            elif v.start_index is not None and v.start_index < 1:
                self.broken = True
            if v.entry_unconfirmed or v.entry_not_met:  # a "no" is never "ineligible"
                self.unknown = True
        for v in self.chosen:
            self._money(v)
        self._prerequisites()
        self._pay_and_hours()
        self._workload()
        income_known = all(
            _placed(v) or (v.work_pattern is None and v.wage is None) for v in self.chosen
        )
        self._limits()
        baseline = self.inputs.baseline
        difference = None
        if baseline is not None and income_known:
            difference = sum(
                baseline.net_income_by_month[m - 1] - self.income[m] for m in self._each_month()
            )
        direct = max(0, self.direct) if self.costs_known else None
        economic = direct + difference if direct is not None and difference is not None else None
        if self.inputs.objective_basis == "economic" and baseline is None:
            self.unknown = True
        cost = economic if self.inputs.objective_basis == "economic" else direct
        months, readiness = self._readiness()
        status: Status = (
            "not_feasible" if self.broken else "unresolved" if self.unknown else "feasible"
        )
        return Checked(status=status, months=months, cost=cost, readiness=readiness)

    def _each_month(self) -> range:
        return range(1, self.months + 1)

    def _month_number(self, day: date) -> int:
        start = self.inputs.planning_start
        return (day.year - start.year) * 12 + day.month - start.month + 1

    def _debt(self) -> list[int]:
        service = [0] * (self.months + 1)
        for debt in self.inputs.existing_debts:
            balance, rate = debt.balance_minor, debt.annual_interest_bps
            for m in self._each_month():
                if balance is None or rate is None:
                    service[m] += debt.monthly_repayment_minor
                    continue
                whole, part = divmod(balance * rate, 12 * 10_000)
                interest = whole + (1 if 2 * part >= 12 * 10_000 else 0)  # half up
                paid = min(debt.monthly_repayment_minor, balance + interest)
                service[m] += paid
                balance = balance + interest - paid
        return service

    def _too_much_at_once(self, amount: int) -> None:
        """A payment whose month is unknown is above the monthly cap in any month if it is
        above it with the smallest month's debt repayments."""
        cap = self.inputs.monthly_payment_cap_minor
        least = min(self.debt[1:], default=0)
        if cap is not None and amount + least > cap:
            self.broken = True

    def _money(self, v: CompiledVariant) -> None:
        counted = [s for s in v.supports if _counted(s)]
        to_provider = [s for s in counted if s.paid_to == "provider"]
        waived = any(s.covers_fees_in_full for s in to_provider)
        if v.cost_unknown is not None and not waived:
            self.costs_known = False
            self.unknown = True
        recurring = v.recurring
        recurring_total = None
        if recurring is not None and recurring.count is not None and not recurring.at_least:
            recurring_total = recurring.amount.minor_units * recurring.count
        if recurring is not None and not (waived or recurring_total):
            self.costs_known = False
            self.unknown = True
            self._too_much_at_once(recurring.amount.minor_units)
        # A fee the page states for an eligible learner is the person's only once they have
        # confirmed every condition; a fee not stated at all is already unknown.
        fee_stated = v.cost_unknown is None and (recurring is None or bool(recurring_total))
        if fee_stated and not waived and v.unconfirmed_conditions:
            self.costs_known = False
            self.unknown = True
        # Two schemes are never assumed to stack.
        if len(counted) >= 2 and not v.stacking_confirmed:
            self.costs_known = False
            self.unknown = True
        due: list[tuple[int | None, str, int]] = []
        for payment in v.payments:
            if payment.due is not None:
                month: int | None = self._month_number(payment.due)
            elif _placed(v) and payment.offset is not None and v.start_index is not None:
                month = v.start_index + payment.offset
            else:
                month = None
            due.append((month, payment.kind, payment.amount_minor))
        if recurring is not None and recurring_total and recurring.count is not None:
            for n in range(recurring.count):
                month = v.start_index + n if _placed(v) and v.start_index is not None else None
                due.append((month, "instalment", recurring.amount.minor_units))
        left = [s.amount.minor_units if s.amount is not None else 0 for s in to_provider]
        fees = 0
        for month, kind, amount in sorted(due, key=lambda d: (d[0] is None, d[0] or 0)):
            covered = 0
            if kind != "extra":
                for n, s in enumerate(to_provider):
                    owed = amount - covered
                    take = owed if s.covers_fees_in_full else min(left[n], owed)
                    covered += take
                    left[n] -= take
            paid = amount - covered
            if kind != "extra":
                fees += paid
            if month is None:
                self.direct += paid
                self._too_much_at_once(paid)
            elif month > self.months:
                self.direct += paid
            elif month < 1:
                self.costs_known = False  # whether it was paid is not known
                self.unknown = True
            else:
                self.payments[month] += paid
                self.direct += paid
        for s in counted:
            if s.paid_to != "person":
                continue
            amount = s.amount.minor_units if s.amount is not None else 0
            applied = min(amount, fees)
            month = (
                v.start_index + (s.paid_month_offset or 0)
                if _placed(v) and v.start_index is not None
                else None
            )
            if month is not None and 1 <= month <= self.months:
                if s.award is AwardState.APPROVED and s.proven_before_outflows:
                    self.early[month] += amount
                else:
                    self.late[month] += amount
                self.support[month] += applied
            self.direct -= applied
            fees = max(0, fees - amount)

    def _prerequisites(self) -> None:
        start = self.inputs.planning_start
        initial = set(self.inputs.initial_gates)
        for v in self.chosen:
            if not _placed(v) or v.start_index is None:
                continue
            for gate in v.prerequisites:
                if gate in initial:
                    continue
                givers = [w for w in self.chosen if w is not v and gate in w.grants]
                if any(not _placed(w) for w in givers):
                    continue
                if not any(
                    w.usable_index is not None and w.usable_index <= v.start_index for w in givers
                ):
                    self.broken = True
            deadline, admission = v.application_deadline, v.application_gate
            if deadline is None or admission is None or admission in initial:
                continue
            if deadline < start:
                self.broken = True
                continue
            finished = [
                (w.finish_date.year, w.finish_date.month)
                for w in self.chosen
                if _placed(w) and w.finish_date is not None and admission in w.grants
            ]
            closing = (deadline.year, deadline.month)
            if finished and not any(f < closing for f in finished):
                if closing in finished:
                    self.unknown = True  # the deadline's own month: not resolved by this model
                else:
                    self.broken = True

    def _pay_and_hours(self) -> None:
        continuation = self.inputs.continuation
        for m in self._each_month():
            active = [v for v in self.chosen if _active(v, m)]
            patterns = [v.work_pattern for v in active if v.work_pattern is not None]
            kinds = {(p.kind, p.hours_per_week, p.net_income.minor_units) for p in patterns}
            if len(kinds) > 1:
                self.broken = True
            if patterns:
                job_pay, job_hours = patterns[0].net_income.minor_units, patterns[0].hours_per_week
            else:
                job_pay = continuation.net_income_by_month[m - 1]
                job_hours = continuation.hours_per_week
            self._receive(m, job_pay, self.inputs.wage_timing)
            self.income[m] = job_pay
            self.hours[m] = job_hours
            for v in active:
                if v.wage is None:
                    continue
                amount = v.wage.net_income.minor_units
                awaiting = v.offer_gate is not None and not v.offer_gate.accepted
                self._receive(
                    m, amount, ReceiptTiming.LATER if awaiting else self.inputs.wage_timing
                )
                self.income[m] += amount

    def _receive(self, month: int, amount: int, timing: ReceiptTiming) -> None:
        if timing is ReceiptTiming.BEFORE_OUTFLOWS:
            self.early[month] += amount
        else:
            self.late[month] += amount

    def _workload(self) -> None:
        available = self.inputs.weekly_availability_by_month
        if available is None:
            self.unknown = True
            return  # as the checker: nothing else about time is checked without it
        fixed = sum(c.hours_per_week for c in self.inputs.commitments)
        for m in self._each_month():
            active = [v for v in self.chosen if _active(v, m)]
            load = self.hours[m] + fixed + sum(v.weekly_hours or 0 for v in active)
            if load > available[m - 1]:
                self.broken = True
            elif any(v.weekly_hours is None for v in active):
                self.unknown = True
        for v in self.chosen:
            if _placed(v):
                continue
            if v.weekly_hours is None:
                self.unknown = True
                continue
            job = (
                v.work_pattern.hours_per_week
                if v.work_pattern is not None
                else self.inputs.continuation.hours_per_week
            )
            if v.weekly_hours + job + fixed > max(available):
                self.broken = True
        timed = [v for v in self.chosen if _placed(v) and v.sessions]
        for n, first in enumerate(timed):
            for second in timed[n + 1 :]:
                together = any(_active(first, m) and _active(second, m) for m in self._each_month())
                clash = any(_overlap(a, b) for a in first.sessions for b in second.sessions)
                if together and clash:
                    self.broken = True

    def _limits(self) -> None:
        inputs = self.inputs
        if None in (
            inputs.direct_spend_cap_minor,
            inputs.monthly_payment_cap_minor,
            inputs.reserve_minor,
        ):
            self.unknown = True
        if (
            inputs.direct_spend_cap_minor is not None
            and self.direct > inputs.direct_spend_cap_minor
        ):
            self.broken = True
        cap = inputs.monthly_payment_cap_minor
        if cap is not None and any(
            self.payments[m] + self.debt[m] > cap for m in self._each_month()
        ):
            self.broken = True
        deficit_cap = inputs.monthly_deficit_cap_minor
        if deficit_cap is not None:
            if inputs.baseline is None:
                self.unknown = True
            else:
                for m in self._each_month():
                    lost = inputs.baseline.net_income_by_month[m - 1] - self.income[m]
                    if self.payments[m] - self.support[m] + lost > deficit_cap:
                        self.broken = True
        receipts_known = all(
            _placed(v)
            or (
                v.work_pattern is None
                and v.wage is None
                and not any(s.paid_to == "person" for s in v.supports)
            )
            for v in self.chosen
        )
        reserve = inputs.reserve_minor
        if reserve is None or not receipts_known or not all(_placed(v) for v in self.chosen):
            return
        balance = inputs.opening_cash_minor
        for m in self._each_month():
            out = inputs.living_outgoings_by_month[m - 1] + self.payments[m] + self.debt[m]
            lowest = balance + self.early[m] - out
            if lowest < reserve:
                self.broken = True
            balance = lowest + self.late[m]

    def _readiness(self) -> tuple[int | None, ReadinessState | None]:
        state = self.oracle.readiness(None)
        if state is ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS:
            return 0, state
        seen: frozenset[str] = frozenset()
        for boundary in range(1, self.months + 2):
            done = frozenset(
                v.outcome_offering_id
                for v in self.chosen
                if _placed(v) and v.usable_index is not None and v.usable_index <= boundary
            )
            if done == seen:
                continue
            seen = done
            state = self.oracle.readiness(done)
            if state in REACHED:
                return boundary - 1, state
        return None, state


def _placed(v: CompiledVariant) -> bool:
    return v.start_date is not None and v.finish_date is not None


def _active(v: CompiledVariant, month: int) -> bool:
    if not _placed(v) or v.start_index is None or v.finish_index is None:
        return False
    return v.start_index <= month <= v.finish_index
