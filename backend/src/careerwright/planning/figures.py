"""The person's own figures for the facts the route search lacks (Task 12b; S5.3; ADR 0013's
Task 12b amendment). Pure: no SQL, no network, no model.

In the reviewed option pack every offering lacks at least one fact the route search needs: a
start date, a finish, a cost or weekly hours (Task 13a). The person may supply each one for an
offering as their own figure, or choose one of the intake months its page states as its start.
A figure only fills a fact the offering lacks: a stated, cited fact always wins, so a figure
never overrides a page. A supplied start with the page's one exact length gives the finish.
Every supplied fact is named on the offering (`Offering.supplied`), so a route resting on one
is qualified, never an unqualified "affordable and feasible" (OPTN-09).

A supplied cost is the whole of what the person will pay for the offering, due in its first
month, the rule for a total with no stated schedule (session 2, D12 yes).
"""

from datetime import date
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careerwright.money import Money
from careerwright.planning.catalogue import (
    ActionConcept,
    Citation,
    EligibilityStatus,
    Hours,
    Offering,
    Payment,
    PaymentPlan,
    SuppliedFact,
    Variant,
)
from careerwright.planning.pack import WHOLE_FEE_DUE, finish_from

Identifier = Annotated[str, Field(min_length=1, max_length=200)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MissingFact(StrEnum):
    """A fact the route search needs for an option that is not known yet: what the checkpoint
    names for each option (OPTN-13)."""

    START_DATE = "start_date"
    FINISH_DATE = "finish_date"  # still unknown with a start: no exact length is stated
    COST = "cost"
    WEEKLY_HOURS = "weekly_hours"
    ENTRY_CONFIRMATION = "entry_confirmation"  # stated entry requirements not yet answered
    # An eligibility condition of its stated fee the person has not confirmed (Task 12a).
    ELIGIBILITY_CONFIRMATION = "eligibility_confirmation"


class StartBasis(StrEnum):
    OWN_FIGURE = "own_figure"  # a date the person gives
    STATED_INTAKE = "stated_intake"  # one of the intake months the page states, chosen


class SuppliedStart(StrictModel):
    on: date
    basis: StartBasis


class OfferingFigures(StrictModel):
    """The person's own figures for one offering: theirs, not reviewed. Null: not supplied."""

    offering_id: Identifier
    start: SuppliedStart | None = None
    finish: date | None = None
    weekly_hours: Hours | None = None
    cost: Money | None = Field(
        default=None,
        description="The whole of what the person will pay for it, due in its first month.",
    )

    @model_validator(mode="after")
    def _something_in_order(self) -> Self:
        stated = (self.start, self.finish, self.weekly_hours, self.cost)
        if all(value is None for value in stated):
            raise ValueError("figures for an offering supply at least one fact")
        if self.start is not None and self.finish is not None and self.finish < self.start.on:
            raise ValueError("a finish is not before its start")
        return self


def cost_known(plan: PaymentPlan) -> bool:
    """Every payment of the plan is known: no unknown part, and any recurring payments have
    their number and an exact amount (`Recurring.total_minor`)."""
    return plan.unknown is None and (
        plan.recurring is None or plan.recurring.total_minor is not None
    )


def offering_missing(offering: Offering) -> list[MissingFact]:
    """The offering's own facts the search lacks, apart from any one payment plan's cost."""
    found = []
    if offering.start is None:
        found.append(MissingFact.START_DATE)
    if offering.finish is None and offering.duration is None:
        found.append(MissingFact.FINISH_DATE)
    if offering.weekly_hours is None:
        found.append(MissingFact.WEEKLY_HOURS)
    return found


def variant_missing(
    concept: ActionConcept, offering: Offering, variant: Variant
) -> list[MissingFact]:
    """Every fact the route search lacks for one option, in the order a person meets them."""
    found = offering_missing(offering)
    plan = offering.plan(variant.plan_id) if variant.plan_id is not None else None
    if plan is None and len(offering.payment_plans) == 1:
        plan = offering.payment_plans[0]
    if plan is None or not cost_known(plan):
        found.append(MissingFact.COST)
    if concept.entry_requirements and variant.entry_requirements_met is None:
        found.append(MissingFact.ENTRY_CONFIRMATION)
    unconfirmed = [
        c
        for c in offering.eligibility_conditions
        if variant.condition_statuses.get(c.field) is not EligibilityStatus.CONFIRMED
    ]
    if unconfirmed and plan is not None and cost_known(plan):
        found.append(MissingFact.ELIGIBILITY_CONFIRMATION)
    return found


def refused(offering: Offering, figures: OfferingFigures) -> str | None:
    """Why figures cannot stand for this offering, or None: a figure for a fact the offering
    states, or a stated intake its page does not list."""
    start = figures.start
    if start is not None and offering.start is not None:
        return "not_missing"
    intake = start is not None and start.basis is StartBasis.STATED_INTAKE
    if intake and start is not None and start.on not in offering.stated_intakes:
        return "not_a_stated_intake"
    if figures.finish is not None and (offering.finish is not None or offering.duration):
        return "not_missing"
    if figures.weekly_hours is not None and offering.weekly_hours is not None:
        return "not_missing"
    plans = offering.payment_plans
    if figures.cost is not None and plans and all(cost_known(p) for p in plans):
        return "not_missing"
    return None


def with_figures(offering: Offering, figures: OfferingFigures, cited: Citation) -> Offering:
    """The offering with the person's figures in each fact it lacks, each named in
    `supplied`. A figure for a fact the offering states is left out: the page wins (a stored
    figure kept from before a newer pack stated the fact). Dates that would not fit (a finish
    before the start) stay unknown."""
    supplied = list(offering.supplied)
    unknown = dict(offering.unknown)
    start, finish = offering.start, offering.finish
    if start is None and figures.start is not None:
        start = figures.start.on
        supplied.append(SuppliedFact.START_DATE)
        unknown.pop("start", None)
    if finish is None and start is not None and offering.duration is not None:
        finish = finish_from(start, offering.duration)
        unknown.pop("finish", None)
    elif finish is None and figures.finish is not None:
        finish = figures.finish
        supplied.append(SuppliedFact.FINISH_DATE)
        unknown.pop("finish", None)
    if start is not None and finish is not None and finish < start:
        start, finish = offering.start, offering.finish
        supplied = [s for s in supplied if s not in DATES]
        unknown = {**dict(offering.unknown), "finish": "the dates given do not fit"}
    hours = offering.weekly_hours
    if hours is None and figures.weekly_hours is not None:
        hours = figures.weekly_hours
        supplied.append(SuppliedFact.WEEKLY_HOURS)
        unknown.pop("weekly_hours", None)
    plans = list(offering.payment_plans)
    if figures.cost is not None and not (plans and all(cost_known(p) for p in plans)):
        whole = Payment(kind="fee", amount=figures.cost, month_offset=WHOLE_FEE_DUE, cited=cited)
        plans = [
            p if cost_known(p) else PaymentPlan(plan_id=p.plan_id, label=p.label, payments=[whole])
            for p in plans
        ] or [PaymentPlan(plan_id="as-stated", payments=[whole])]
        supplied.append(SuppliedFact.COST)
    return offering.model_copy(
        update={
            "start": start,
            "finish": finish,
            "weekly_hours": hours,
            "unknown": unknown,
            "payment_plans": plans,
            "supplied": supplied,
        }
    )


DATES = frozenset({SuppliedFact.START_DATE, SuppliedFact.FINISH_DATE})
