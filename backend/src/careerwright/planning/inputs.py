"""The person's planning inputs, as they are stored and confirmed (Task 12a; ADR 0013 decision
11 and its amendment of 2026-10-31; ADR 0012 decision 11; spec sections 1, 3, 10 and 12). Pure:
no SQL, no network, no model. The commands that store them are `planning.commands`.

Every input here is the person's own answer, confirmed by their direct entry; a model never
fills one. Not yet stated is null (never 0, never "none"), and a list's empty value is an
answer: "no debts" is `[]`, not asked is null.

- **Horizon-free.** Money and hours are stated once a month or a week; `prepare` lays them on
  the comparison's grid for its start and horizon, one value a month (a known limit: a figure
  that changes within the horizon is not modelled).
- **What a solve needs** (`needs`): an input without which no route can be checked blocks a
  solve and is named; an unstated hard limit, availability, a baseline the economic comparison
  needs, or work rights not stated leaves every route unresolved instead (ADR 0013 decision 6).
- **The two spending caps stay the profile's** (one record, set only by the person, PROF-04):
  `prepare` takes them as `SpendingCaps`. The reserve and the deficit cap are here.
- **Work rights and remote working live here** (ADR 0013 amendment): the person's
  circumstances for the plan, never inferred from a city, and remote work never takes a city.
- **Per option** (`VariantInputs`): the work pattern, take-home wage, funding statuses (each
  support, whether they stack, each eligibility condition of the stated fee), a tuition fee
  loan paid straight to the provider (Task 12c: a loan to repay, never support) and the entry
  confirmation. A place or an accepted offer the person holds (`admissions`) is the starting
  position: its application gate is verified and its offer accepted.
- **Outcome decisions** (ADR 0012 decision 11): accepting a provisional mapping makes it the
  person's assumption; an override stands beside the provider's record, never replacing it.
"""

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from careerwright.capability.outcomes import EvidenceKind, PlannedOutcome, accept, user_override
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.money import Money
from careerwright.planning.catalogue import (
    AwardState,
    Catalogue,
    Citation,
    CitationBasis,
    EligibilityStatus,
    FeeLoanKind,
    Hours,
    InstrumentKind,
    RecordState,
    Support,
    TuitionFeeLoan,
    Wage,
    WorkPattern,
    WorkPatternKind,
)
from careerwright.planning.compiler import (
    Baseline,
    Commitment,
    Continuation,
    ExistingDebt,
    PlanningInputs,
    WorkRights,
)
from careerwright.planning.figures import OfferingFigures, with_figures
from careerwright.planning.months import MAX_HORIZON_MONTHS
from careerwright.planning.own_options import OwnOption, OwnOptionInput, stamped_options
from careerwright.planning.own_options import as_input as option_input

INPUTS_SCHEMA_VERSION: Literal["1"] = "1"
CONTINUATION_LABEL = "continuation"
MAX_SUPPORTS = 4  # supports confirmed on one option: more is never a real case in L0
MAX_LISTED = 50  # commitments, debts, options, admissions and outcome decisions, each
MAX_OWN_OPTIONS = 24  # options a person adds, across their targets: the M0 concept bound
MAX_EXCLUDED = 200  # options left out of the search, across every target
Identifier = Annotated[str, Field(min_length=1, max_length=200)]
Reason = Annotated[str, Field(min_length=1, max_length=400)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BaselineKind(StrEnum):
    """The confirmed counterfactual (FIN1-11): never assumed to be staying put."""

    CURRENT_ROLE = "current_role"
    JOB_SEARCH = "job_search"
    # Plan v1.6 (a school leaver): carrying on in school or college; with no job, its pay is
    # the person's own "0 hours, £0", a stated figure, never an unknown read as zero.
    STAYING_IN_EDUCATION = "staying_in_education"
    OTHER = "other"


class BaselineInput(StrictModel):
    kind: BaselineKind
    net_income: Money = Field(description="Take-home pay a month in the baseline.")


class ContinuationInput(StrictModel):
    """The common work and pay every route returns to (FIN-1): never a target wage."""

    hours_per_week: Hours
    net_income: Money = Field(description="Take-home pay a month.")


class CommitmentKind(StrEnum):
    CARE = "care"
    COMMUTE = "commute"
    SECOND_JOB = "second_job"
    OTHER = "other"


class CommitmentInput(StrictModel):
    kind: CommitmentKind
    hours_per_week: Hours


class DebtInput(StrictModel):
    """An existing debt: a fixed commitment whose repayments are outflows (spec section 10)."""

    monthly_repayment: Money
    balance: Money | None = None
    annual_interest_bps: Annotated[int, Field(ge=0, le=100_000)] | None = Field(
        default=None, description="Interest a year in basis points: 1,990 is 19.9%."
    )


class RemoteWork(StrictModel):
    """Whether the person works remotely, and for an employer in which country and timezone.
    L0 plans England-based work only (spec section 1, BND1-05), so a remote employer is in
    England; another country is outside the supported slice and refused. It is never read
    from a city and never takes a city slot."""

    works_remotely: bool
    employment_country: Literal["GB-ENG"] | None = None
    timezone: Literal["Europe/London"] | None = None

    @model_validator(mode="after")
    def _named_when_remote(self) -> Self:
        named = self.employment_country is not None and self.timezone is not None
        unnamed = self.employment_country is None and self.timezone is None
        if (self.works_remotely and not named) or (not self.works_remotely and not unnamed):
            raise ValueError("remote work names its employer's country and timezone, only then")
        return self


class WorkPatternInput(StrictModel):
    kind: WorkPatternKind
    hours_per_week: Hours
    net_income: Money = Field(description="Take-home pay a month while the option is active.")


class SupportInput(StrictModel):
    """One support the person confirms for an option, with its status: the funding rules of
    `planning.catalogue.Support` (non-repayable only, an approval needs confirmed eligibility)."""

    instrument_id: Identifier
    kind: InstrumentKind
    covers_fees_in_full: bool = False
    amount: Money | None = None
    paid_to: Literal["provider", "person"]
    paid_month_offset: Annotated[int, Field(ge=0, le=MAX_HORIZON_MONTHS)] | None = None
    proven_before_outflows: bool = False
    eligibility: EligibilityStatus
    award: AwardState
    assumed: bool = Field(
        default=False, description="An explicitly conditional award: 'if funding is approved'."
    )

    @model_validator(mode="after")
    def _a_support(self) -> Self:
        self.support(Citation(basis=CitationBasis.PERSON))  # the same rules, raised here
        return self

    def support(self, cited: Citation) -> Support:
        """As the planning model reads it: the person's assumption, never a reviewed record."""
        return Support(
            **self.model_dump(), review_state=RecordState.ACCEPTED_ASSUMPTION, cited=cited
        )


class TuitionFeeLoanInput(StrictModel):
    """A fee loan paid straight to the provider, as the person states it for one option (spec
    section 22, 2026-11-01): which loan (a tuition fee loan, or an Advanced Learner Loan by the
    product owner's provisional yes), its amount and its funding statuses (ADR 0013 decision
    5). The rules of `planning.catalogue.TuitionFeeLoan`: an approval needs confirmed
    eligibility. Never support: a maintenance loan or any other loan is refused."""

    kind: FeeLoanKind = Field(
        default=FeeLoanKind.TUITION_FEE_LOAN,
        description="Which loan: a tuition fee loan unless the person says otherwise.",
    )
    amount: Money | None = Field(default=None, description="Null: not known, never £0.")
    eligibility: EligibilityStatus
    application: AwardState

    @model_validator(mode="after")
    def _a_loan(self) -> Self:
        self.loan(Citation(basis=CitationBasis.PERSON))  # the same rules, raised here
        return self

    def loan(self, cited: Citation) -> TuitionFeeLoan:
        """As the planning model reads it: the person's assumption, never a reviewed record."""
        return TuitionFeeLoan(
            **self.model_dump(), review_state=RecordState.ACCEPTED_ASSUMPTION, cited=cited
        )


class VariantInputs(StrictModel):
    """What the person confirmed for one option (a variant of the planning catalogue)."""

    variant_id: Identifier
    work_pattern: WorkPatternInput | None = None
    wage: Money | None = Field(default=None, description="Take-home wage a month, confirmed.")
    supports: list[SupportInput] = Field(default_factory=list, max_length=MAX_SUPPORTS)
    stacking_confirmed: bool = Field(
        default=False,
        description="The supports may be combined: neither excludes the other and together "
        "they stay within each one's eligible costs.",
    )
    tuition_fee_loan: TuitionFeeLoanInput | None = Field(
        default=None,
        description="A tuition fee loan paid straight to the provider: a loan to repay later, "
        "never support. Null: none stated.",
    )
    entry_requirements_met: bool | None = Field(
        default=None, description="Null: not yet answered. False: the person's own no."
    )
    condition_statuses: dict[Identifier, EligibilityStatus] = Field(
        default_factory=dict,
        description="The person's status for each eligibility condition of the stated fee, by "
        "the condition's field: only `confirmed` meets one.",
    )


class OutcomeDecisionInput(StrictModel):
    """Accept a provisional outcome mapping as a modelling assumption, or override it."""

    outcome_id: Identifier
    decision: Literal["accept", "override"]
    evidence_kind: EvidenceKind | None = None
    level_on_completion: Annotated[int, Field(ge=0, le=4)] | None = None
    rubric_version: Identifier | None = None
    reason: Reason | None = None

    @model_validator(mode="after")
    def _says_what(self) -> Self:
        corrected = (self.evidence_kind, self.level_on_completion, self.rubric_version)
        if self.decision == "accept" and (any(v is not None for v in corrected) or self.reason):
            raise ValueError("accepting a mapping changes nothing in it")
        if self.decision == "override" and (self.evidence_kind is None or self.reason is None):
            raise ValueError("an override states its evidence kind and why")
        return self


class OutcomeDecision(OutcomeDecisionInput):
    """A stored decision: who made it and when, kept while it is unchanged."""

    recorded_by: uuid.UUID
    recorded_at: datetime


class StatedInputs(StrictModel):
    """Every input except the outcome decisions. Null is not yet stated."""

    objective_basis: Literal["economic", "direct_spending"] | None = None
    baseline: BaselineInput | None = None
    continuation: ContinuationInput | None = None
    opening_cash: Money | None = None
    living_costs: Money | None = Field(default=None, description="Committed outgoings a month.")
    reserve: Money | None = Field(default=None, description="The minimum cash to keep.")
    monthly_deficit_cap: Money | None = Field(
        default=None,
        description="Optional: payments less support received plus pay lost, in any month.",
    )
    weekly_availability: Hours | None = Field(
        default=None,
        description="The hours a week the person can give to work, study and commitments.",
    )
    commitments: list[CommitmentInput] | None = Field(default=None, max_length=MAX_LISTED)
    existing_debts: list[DebtInput] | None = Field(default=None, max_length=MAX_LISTED)
    scenario_delay_months: Annotated[int, Field(ge=1, le=MAX_HORIZON_MONTHS)] | None = None
    work_rights: WorkRights | None = None
    remote_work: RemoteWork | None = None
    admissions: list[Identifier] = Field(
        default_factory=list,
        max_length=MAX_LISTED,
        description="Offerings where the person holds a place or an accepted offer.",
    )
    variants: list[VariantInputs] = Field(default_factory=list, max_length=MAX_LISTED)
    shared_schemes: list[Identifier] = Field(
        default_factory=list,
        max_length=MAX_LISTED,
        description="Schemes the person confirmed may pay for more than one of their options, "
        "each one of their stated supports' instrument IDs.",
    )
    # Task 12b (ADR 0013's Task 12b amendment).
    offering_figures: list[OfferingFigures] = Field(
        default_factory=list,
        max_length=MAX_LISTED,
        description="The person's own figures for facts an offering lacks: theirs, not "
        "reviewed, so every route resting on one is qualified.",
    )
    excluded_variants: list[Identifier] = Field(
        default_factory=list,
        max_length=MAX_EXCLUDED,
        description="Options the person leaves out of the route search (the rest are "
        "retained): how a comparison over the model's bounds is narrowed, never silently.",
    )

    @model_validator(mode="after")
    def _one_answer_each(self) -> Self:
        _unique(self.admissions, "admission")
        _unique([v.variant_id for v in self.variants], "option")
        _unique(self.shared_schemes, "shared scheme")
        _unique([f.offering_id for f in self.offering_figures], "offering's figures")
        _unique(self.excluded_variants, "left-out option")
        stated = {s.instrument_id for v in self.variants for s in v.supports}
        if set(self.shared_schemes) - stated:
            raise ValueError("a shared scheme is one of the person's stated supports")
        return self


class PlanningInputsIn(StatedInputs):
    """What a client submits: the whole document, every input it leaves out unstated."""

    outcome_decisions: list[OutcomeDecisionInput] = Field(
        default_factory=list, max_length=MAX_LISTED
    )
    own_options: list[OwnOptionInput] = Field(
        default_factory=list,
        max_length=MAX_OWN_OPTIONS,
        description="Options the person added themselves: their own records, never reviewed.",
    )

    @model_validator(mode="after")
    def _one_decision_each(self) -> Self:
        _unique([d.outcome_id for d in self.outcome_decisions], "outcome decision")
        _unique([o.option_id for o in self.own_options], "own option")
        return self


class PlanningInputsDocument(StatedInputs):
    """A stored version's content."""

    schema_version: Literal["1"] = INPUTS_SCHEMA_VERSION
    outcome_decisions: list[OutcomeDecision] = Field(default_factory=list, max_length=MAX_LISTED)
    own_options: list[OwnOption] = Field(default_factory=list, max_length=MAX_OWN_OPTIONS)

    @model_validator(mode="after")
    def _one_decision_each(self) -> Self:
        _unique([d.outcome_id for d in self.outcome_decisions], "outcome decision")
        _unique([o.option_id for o in self.own_options], "own option")
        return self


def _unique(values: Sequence[str], what: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"each {what} is named once")


def stamped(
    new: PlanningInputsIn, *, previous: PlanningInputsDocument | None, by: uuid.UUID, at: datetime
) -> PlanningInputsDocument:
    """The document to store: a decision unchanged since `previous` keeps who made it and when;
    a new or changed one is this actor's, now."""
    before = {d.outcome_id: d for d in previous.outcome_decisions} if previous else {}
    decisions = []
    for decision in new.outcome_decisions:
        kept = before.get(decision.outcome_id)
        if kept is not None and _as_input(kept) == decision:
            decisions.append(kept)
        else:
            decisions.append(
                OutcomeDecision(**decision.model_dump(), recorded_by=by, recorded_at=at)
            )
    return PlanningInputsDocument(
        **new.model_dump(exclude={"outcome_decisions", "own_options"}),
        outcome_decisions=decisions,
        own_options=stamped_options(
            new.own_options, previous.own_options if previous else [], by=by, at=at
        ),
    )


def _as_input(decision: OutcomeDecision) -> OutcomeDecisionInput:
    return OutcomeDecisionInput.model_validate(
        decision.model_dump(exclude={"recorded_by", "recorded_at"})
    )


def as_submitted(document: PlanningInputsDocument) -> PlanningInputsIn:
    """A stored document as its client would send it back: without the decisions' stamps."""
    return PlanningInputsIn(
        **document.model_dump(exclude={"schema_version", "outcome_decisions", "own_options"}),
        outcome_decisions=[_as_input(d) for d in document.outcome_decisions],
        own_options=[option_input(o) for o in document.own_options],
    )


# What a solve needs (API-05).


class NeededInput(StrEnum):
    OBJECTIVE_BASIS = "objective_basis"
    CONTINUATION = "continuation"
    OPENING_CASH = "opening_cash"
    LIVING_COSTS = "living_costs"
    COMMITMENTS = "commitments"
    EXISTING_DEBTS = "existing_debts"
    SCENARIO_DELAY_MONTHS = "scenario_delay_months"
    DIRECT_SPEND_CAP = "direct_spend_cap"  # the profile's
    MONTHLY_PAYMENT_CAP = "monthly_payment_cap"  # the profile's
    RESERVE = "reserve"
    WEEKLY_AVAILABILITY = "weekly_availability"
    BASELINE = "baseline"
    WORK_RIGHTS = "work_rights"


class NeedEffect(StrEnum):
    BLOCKS_A_SOLVE = "blocks_a_solve"  # no route can be checked without it
    LEAVES_EVERY_ROUTE_UNRESOLVED = "leaves_every_route_unresolved"


class Need(StrictModel):
    input: NeededInput
    effect: NeedEffect


@dataclass(frozen=True)
class SpendingCaps:
    """The profile's two hard spending limits: null is not stated, never "no limit"."""

    direct_spend_cap: Money | None
    monthly_payment_cap: Money | None


def needs(stated: StatedInputs, caps: SpendingCaps) -> list[Need]:
    """Every input still to state, in the order a person meets them, with its effect."""
    blocking = [
        (NeededInput.OBJECTIVE_BASIS, stated.objective_basis is None),
        (NeededInput.CONTINUATION, stated.continuation is None),
        (NeededInput.OPENING_CASH, stated.opening_cash is None),
        (NeededInput.LIVING_COSTS, stated.living_costs is None),
        (NeededInput.COMMITMENTS, stated.commitments is None),
        (NeededInput.EXISTING_DEBTS, stated.existing_debts is None),
        (NeededInput.SCENARIO_DELAY_MONTHS, stated.scenario_delay_months is None),
    ]
    # The economic comparison and a deficit cap read the baseline; direct spending does not.
    baseline_read = stated.objective_basis == "economic" or stated.monthly_deficit_cap is not None
    unresolved = [
        (NeededInput.DIRECT_SPEND_CAP, caps.direct_spend_cap is None),
        (NeededInput.MONTHLY_PAYMENT_CAP, caps.monthly_payment_cap is None),
        (NeededInput.RESERVE, stated.reserve is None),
        (NeededInput.WEEKLY_AVAILABILITY, stated.weekly_availability is None),
        (NeededInput.BASELINE, baseline_read and stated.baseline is None),
        (NeededInput.WORK_RIGHTS, stated.work_rights in (None, WorkRights.UNKNOWN)),
    ]
    return [
        *(Need(input=n, effect=NeedEffect.BLOCKS_A_SOLVE) for n, unstated in blocking if unstated),
        *(
            Need(input=n, effect=NeedEffect.LEAVES_EVERY_ROUTE_UNRESOLVED)
            for n, unstated in unresolved
            if unstated
        ),
    ]


# As the monthly model reads them.


@dataclass(frozen=True)
class Prepared:
    """One comparison's inputs and its catalogue with the person's answers in it."""

    inputs: PlanningInputs
    catalogue: Catalogue


def prepare(
    document: PlanningInputsDocument,
    catalogue: Catalogue,
    *,
    caps: SpendingCaps,
    planning_start: date,
    horizon_months: int,
    synthetic: bool,
    version: int,
    expected_entry: frozenset[str] = frozenset(),
) -> Prepared:
    """The monthly model's inputs for one comparison, from stored version `version`. Refused,
    naming them, while an input a solve needs is not stated: never filled with a default.
    `expected_entry`: the concepts whose stated entry requirements are named only by a
    qualification the person expects (`checkpoint.expected_entry`)."""
    blocking = [n for n in needs(document, caps) if n.effect is NeedEffect.BLOCKS_A_SOLVE]
    missing = [n.input.value for n in blocking]
    objective, continuation = document.objective_basis, document.continuation
    opening, living = document.opening_cash, document.living_costs
    commitments, debts = document.commitments, document.existing_debts
    delay = document.scenario_delay_months
    # `missing` names each one; the other tests only repeat, for the type checker, what
    # `needs` found.
    if (
        missing
        or objective is None
        or continuation is None
        or opening is None
        or living is None
        or commitments is None
        or debts is None
        or delay is None
    ):
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "A comparison needs the person's money and time first.",
            stage=ErrorStage.PLANNING,
            details={"reason": "inputs_missing", "missing": missing},
        )
    cited = Citation(basis=CitationBasis.PERSON, locator=f"planning inputs, version {version}")
    months = horizon_months
    person = with_answers(catalogue, document, cited, expected_entry=expected_entry)
    admitted = set(document.admissions)
    baseline = document.baseline
    inputs = PlanningInputs(
        planning_start=planning_start,
        horizon_months=months,
        objective_basis=objective,
        baseline=Baseline(
            label=baseline.kind.value,
            net_income_by_month=[baseline.net_income.minor_units] * months,
            cited=cited,
        )
        if baseline is not None
        else None,
        continuation=Continuation(
            label=CONTINUATION_LABEL,
            hours_per_week=continuation.hours_per_week,
            net_income_by_month=[continuation.net_income.minor_units] * months,
            cited=cited,
        ),
        opening_cash_minor=opening.minor_units,
        living_outgoings_by_month=[living.minor_units] * months,
        reserve_minor=_minor(document.reserve),
        direct_spend_cap_minor=_minor(caps.direct_spend_cap),
        monthly_payment_cap_minor=_minor(caps.monthly_payment_cap),
        monthly_deficit_cap_minor=_minor(document.monthly_deficit_cap),
        weekly_availability_by_month=[document.weekly_availability] * months
        if document.weekly_availability is not None
        else None,
        commitments=[
            Commitment(label=c.kind.value, hours_per_week=c.hours_per_week, cited=cited)
            for c in commitments
        ],
        existing_debts=[
            ExistingDebt(
                debt_id=f"debt:{n}",
                monthly_repayment_minor=d.monthly_repayment.minor_units,
                balance_minor=_minor(d.balance),
                annual_interest_bps=d.annual_interest_bps,
                cited=cited,
            )
            for n, d in enumerate(debts, start=1)
        ],
        initial_gates=sorted(
            {
                o.application_gate
                for o in catalogue.offerings
                if o.offering_id in admitted and o.application_gate is not None
            }
        ),
        scenario_delay_months=delay,
        work_rights=document.work_rights or WorkRights.UNKNOWN,
        shared_schemes=list(document.shared_schemes),
        synthetic=synthetic,
    )
    return Prepared(inputs=inputs, catalogue=person)


def with_answers(
    catalogue: Catalogue,
    document: StatedInputs,
    cited: Citation,
    *,
    expected_entry: frozenset[str] = frozenset(),
) -> Catalogue:
    """The catalogue with the person's answers in each variant they name, their own figures
    in each offering they supplied them for, an accepted offer on each offering they hold a
    place or an offer for, and without the options they left out of the search."""
    answers = {v.variant_id: v for v in document.variants}
    admitted = set(document.admissions)
    left_out = set(document.excluded_variants)
    concepts = {c.concept_id: c for c in catalogue.concepts}
    offered = {o.offering_id: o.concept_id for o in catalogue.offerings}
    variants = []
    for variant in catalogue.variants:
        if variant.variant_id in left_out:
            continue
        found = answers.get(variant.variant_id)
        concept = concepts[offered[variant.offering_id]]
        if concept.concept_id in expected_entry and concept.entry_requirements:
            variant = variant.model_copy(update={"entry_expected": True})
        if found is None:
            variants.append(variant)
            continue
        pattern = found.work_pattern
        variants.append(
            variant.model_copy(
                update={
                    "work_pattern": WorkPattern(**pattern.model_dump(), cited=cited)
                    if pattern is not None
                    else None,
                    "wage": Wage(net_income=found.wage, cited=cited)
                    if found.wage is not None
                    else None,
                    "supports": [s.support(cited) for s in found.supports],
                    "stacking_confirmed": found.stacking_confirmed,
                    "tuition_fee_loan": found.tuition_fee_loan.loan(cited)
                    if found.tuition_fee_loan is not None
                    else None,
                    "entry_requirements_met": found.entry_requirements_met,
                    "condition_statuses": dict(found.condition_statuses),
                }
            )
        )
    figures = {f.offering_id: f for f in document.offering_figures}
    offerings = []
    for offering in catalogue.offerings:
        supplied = figures.get(offering.offering_id)
        if supplied is not None:
            offering = with_figures(offering, supplied, cited)
        if offering.offering_id in admitted and offering.offer_gate is not None:
            gate = offering.offer_gate.model_copy(update={"accepted": True})
            offering = offering.model_copy(update={"offer_gate": gate})
        offerings.append(offering)
    return catalogue.model_copy(update={"variants": variants, "offerings": offerings})


def _minor(amount: Money | None) -> int | None:
    return None if amount is None else amount.minor_units


# Outcome decisions (ADR 0012 decision 11).


def decided_outcomes(
    outcomes: Iterable[PlannedOutcome], decisions: Iterable[OutcomeDecision]
) -> list[PlannedOutcome]:
    """The planned outcomes with the person's decisions: an accepted one becomes their
    modelling assumption; an override is a separate record beside the unchanged provider
    claim. A decision whose outcome is not among `outcomes` changes nothing."""
    by_id = {d.outcome_id: d for d in decisions}
    found: list[PlannedOutcome] = []
    for outcome in outcomes:
        decision = by_id.get(outcome.outcome_id)
        if decision is None:
            found.append(outcome)
        elif decision.decision == "accept":
            found.append(accept(outcome, by=decision.recorded_by, at=decision.recorded_at))
        else:
            found.append(outcome)
            found.append(_override(outcome, decision))
    return found


def _override(outcome: PlannedOutcome, decision: OutcomeDecision) -> PlannedOutcome:
    if decision.evidence_kind is None or decision.reason is None:
        raise ValueError("an override states its evidence kind and why")
    return user_override(
        outcome,
        evidence_kind=decision.evidence_kind,
        level_on_completion=decision.level_on_completion,
        rubric_version=decision.rubric_version,
        reason=decision.reason,
        by=decision.recorded_by,
        at=decision.recorded_at,
    )


def refused_decision(
    outcomes: Iterable[PlannedOutcome], decisions: Iterable[OutcomeDecision]
) -> str | None:
    """Why a decision cannot stand (its outcome is not a planned outcome, or an override the
    outcome contract refuses, such as a level for a topic mention), or None."""
    by_id = {o.outcome_id: o for o in outcomes}
    for decision in decisions:
        outcome = by_id.get(decision.outcome_id)
        if outcome is None:
            return "unknown_outcome"
        if decision.decision == "override":
            try:
                _override(outcome, decision)
            except ValidationError:
                return "override_not_supported"
    return None
