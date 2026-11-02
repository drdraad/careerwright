"""The planning catalogue: stable action concepts apart from their dated offerings, funding
instruments apart from a person's status for them, and variants, an offering with the
person's confirmed assumptions (spec sections 10, 12 and 18; S5.1, S5.2). Pure: no SQL, no
network, no model.

- **Concepts and offerings.** A concept is the stable thing (a syllabus and its provider, a
  role class); an offering is one dated intake of it, with its fees, timetable, prerequisites
  and what its completion grants. Unknown is never zero: a field with no value says why.
- **One composite apprenticeship.** An apprenticeship is one action whose offering carries
  the training hours, the wage and the credential together, so its time, money and learning
  are counted once (OPTN-02).
- **Funding** (S5.2). An instrument is a scheme's rules, never a conclusion about a person.
  A person's eligibility for it has four statuses, kept apart from whether an award was
  actually approved. Only approved, confirmed, non-repayable support enters unconditional
  figures; a loan is information to verify and never a receipt or a discount (FUNDING-04).
- **One loan changes, for L0** (spec section 22, the product owner's decision of 2026-11-01):
  a tuition fee loan paid straight to the provider pays that fee, so the fee is not the
  person's own spending or cash; it is a loan to repay later, never support, a grant, income
  or a receipt. Every other loan, a maintenance loan included, stays information (FUNDING-06).
- **Variants.** M0 selects at most two reviewed starts per concept: each is an offering with
  the payment plan, the work pattern and the support the person confirmed for it.
- **Review state** is kept on every record: a proposed record is explorable but never in an
  unqualified "affordable and feasible" result (OPTN-09, ruling R9).
"""

from datetime import date, time
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from careerwright.money import Money

Hours = Annotated[int, Field(ge=0, le=168)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CitationBasis(StrEnum):
    """Where a cited value comes from (named apart from the profile's `Basis`)."""

    SOURCE = "source"  # read from a page: a pack claim with its span
    PERSON = "person"  # the person's own confirmed answer or assumption
    FIXTURE = "fixture"  # a synthetic fixture value, always labelled


class Citation(StrictModel):
    """Where a value came from. A source value names its claim, span and exact excerpt."""

    basis: CitationBasis
    claim_id: str | None = None
    source_id: str | None = None
    source_hash: str | None = None
    locator: str | None = None  # offsets "start-end", a JSON pointer, or a fixture's path
    excerpt: str | None = None
    retrieved_on: date | None = None


class Fact(StrictModel):
    """One consequential field as a reviewer reads it: its value and citation, or why it is
    unknown (never zero, never a default)."""

    field: str
    value: JsonValue = None
    unknown: str | None = None
    cited: Citation | None = None
    note: str | None = None  # how the model reads it, where that is not the page's own words

    @model_validator(mode="after")
    def _known_or_why(self) -> Self:
        if (self.unknown is None) == (self.value is None):
            raise ValueError("a fact has a value or says why it is unknown, not both")
        return self


class RecordState(StrEnum):
    PROPOSED = "proposed"  # curated or researched, not reviewed (R9)
    REVIEWED = "reviewed"  # accepted in a person's recorded review (Task 7c)
    ACCEPTED_ASSUMPTION = "accepted_assumption"  # accepted as a modelling assumption only


class ActionKind(StrEnum):
    LEARNING = "learning"
    APPRENTICESHIP = "apprenticeship"  # wages, training and credential in one action
    WORK = "work"  # an intermediate job: a role class behind an offer gate (OPTN-04)
    APPLICATION = "application"  # an application or admission step: time is never free


class ActionConcept(StrictModel):
    concept_id: str
    kind: ActionKind
    title: str | None
    provider: str | None
    review_state: RecordState
    as_of: date | None = None  # the retrieval date of its evidence: never "current"
    exclusive_group: str | None = None  # at most one selected concept per group
    synthetic: bool
    # An option the person added themselves (S5.7, Task 12b): their own record, `proposed`,
    # never reviewed, so a route through it is always qualified.
    added_by_person: bool = False
    cited: Citation | None = None
    facts: list[Fact] = Field(default_factory=list)  # credential, level, assessment, claims
    # Stated entry requirements: until the person confirms they meet them, a route through
    # the concept is unresolved (spec section 10, "Option review checkpoint").
    entry_requirements: list[Fact] = Field(default_factory=list)


class Payment(StrictModel):
    """A contractual payment: a fee, an instalment or an extra cost (FIN1-02). Its date, or
    its month counted from the offering's start month (0 is the first). An outflow is taken
    as due on the first day of its month: conservative prefunding (TIME-1)."""

    kind: Literal["fee", "instalment", "extra"]
    amount: Money
    due: date | None = None
    month_offset: Annotated[int, Field(ge=0)] | None = None
    cited: Citation

    @model_validator(mode="after")
    def _dated(self) -> Self:
        if (self.due is None) == (self.month_offset is None):
            raise ValueError("a payment has a due date or a month offset, not both")
        return self


class Recurring(StrictModel):
    """Payments stated as "from £X a month" with or without their number: a total is known
    only with the count and an exact amount."""

    amount: Money
    at_least: bool
    count: Annotated[int, Field(ge=1)] | None
    cited: Citation

    @property
    def total_minor(self) -> int | None:
        if self.count is None or self.at_least:
            return None
        return self.amount.minor_units * self.count


class PaymentPlan(StrictModel):
    """One way of paying for an offering. With `unknown` set, its cost is not stated."""

    plan_id: str
    label: str | None = None
    payments: list[Payment] = Field(default_factory=list)
    recurring: Recurring | None = None
    unknown: str | None = None
    # Task 12b: its unstated part is the person's own figure (`planning.figures`), so a route
    # on this plan, and only on this plan, rests on it.
    supplied_cost: bool = False


class Session(StrictModel):
    """A fixed timetable session, for clashes (TIME1-04): a weekday (0 is Monday) and times."""

    weekday: Annotated[int, Field(ge=0, le=6)]
    starts: time
    ends: time

    def overlaps(self, other: "Session") -> bool:
        return (
            self.weekday == other.weekday and self.starts < other.ends and other.starts < self.ends
        )


class SuppliedFact(StrEnum):
    """A fact the route search needs that the person supplied as their own figure for an
    offering (Task 12b): labelled theirs and not reviewed, so a route resting on it is
    qualified."""

    START_DATE = "start_date"
    FINISH_DATE = "finish_date"
    COST = "cost"
    WEEKLY_HOURS = "weekly_hours"


class Duration(StrictModel):
    """One exact length a page states (never a typical, open or ranged one): with a start, it
    gives the finish (`pack.finish_from`)."""

    unit: Literal["weeks", "months", "years"]
    count: Annotated[int, Field(ge=1)]
    cited: Citation | None = None


class OfferGate(StrictModel):
    """A job or an apprenticeship starts only when an offer is accepted: its wages and its
    experience start at that gate, never before (FIN1-04, PLN-05)."""

    accepted: bool  # already accepted in the initial state, so not a condition
    role_class: str | None = None  # a future job: a role class and a search, never a vacancy


class Offering(StrictModel):
    """One dated intake of a concept (spec section 18, Offering)."""

    offering_id: str
    concept_id: str
    review_state: RecordState
    as_of: date | None = None
    start: date | None
    finish: date | None
    unknown: dict[str, str] = Field(default_factory=dict)  # critical field -> why unknown
    weekly_hours: Hours | None  # the maximum weekly load; None: no timetable is stated
    sessions: list[Session] = Field(default_factory=list)
    payment_plans: list[PaymentPlan] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)  # gates needed before the start
    grants: list[str] = Field(default_factory=list)  # gates its completion grants
    application_deadline: date | None = None
    # The prerequisite an application grants: its application must complete in a month
    # strictly before the deadline month, unless the gate is verified in the initial state.
    application_gate: str | None = None
    offer_gate: OfferGate | None = None
    # The dated offering whose planned outcomes (OUT-1) this one carries, when one intake is
    # taken several ways (full time, part time); None: its own.
    outcomes_from: str | None = None
    # The eligibility conditions its page states for its funding (an age, an area, the right to
    # work): its stated fee is an eligible learner's, so until the person confirms each one the
    # fee is not theirs (review 13a, C07: "£0.00" for an eligible learner).
    eligibility_conditions: list[Fact] = Field(default_factory=list)
    synthetic: bool
    cited: Citation | None = None
    facts: list[Fact] = Field(default_factory=list)  # every consequential field, cited
    # Task 12b. Its one exact stated length, if any: a start the person supplies then gives
    # its finish. The intake months its page states, which the person may choose as its start.
    duration: Duration | None = None
    stated_intakes: list[date] = Field(default_factory=list)
    # The facts of its own the person supplied as their figures (`planning.inputs`): dates and
    # hours. A supplied cost belongs to the plan it fills (`PaymentPlan.supplied_cost`).
    supplied: list[SuppliedFact] = Field(default_factory=list)

    def supplied_for(self, plan: PaymentPlan | None) -> list[SuppliedFact]:
        """What a route on this offering paid by `plan` rests on of the person's figures."""
        cost = [SuppliedFact.COST] if plan is not None and plan.supplied_cost else []
        return [*self.supplied, *cost]

    def plan(self, plan_id: str | None) -> PaymentPlan | None:
        return next((p for p in self.payment_plans if p.plan_id == plan_id), None)


class InstrumentKind(StrEnum):
    FEE_WAIVER = "fee_waiver"
    GRANT = "grant"
    BURSARY = "bursary"
    EMPLOYER_SUPPORT = "employer_support"
    LOAN = "loan"  # information to verify: never optimised, never a receipt (spec section 10)
    PROGRAMME = "programme"  # a programme's own rules (Skills Bootcamps): no money by itself


NON_REPAYABLE = frozenset(
    {
        InstrumentKind.FEE_WAIVER,
        InstrumentKind.GRANT,
        InstrumentKind.BURSARY,
        InstrumentKind.EMPLOYER_SUPPORT,
    }
)


class FundingInstrument(StrictModel):
    """A scheme's rules (spec section 18, FundingInstrument): never a person's eligibility."""

    instrument_id: str
    programme: str | None
    kind: InstrumentKind
    jurisdiction: str
    review_state: RecordState
    as_of: date | None = None
    rules: list[Fact] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    # Schemes a record states this one may not be combined with, by instrument ID: a route
    # counting both is not feasible in this model. Pack 0.1.0 and 0.2.0 record none (their
    # exclusions are words naming no scheme), so different schemes are then an L0 limit.
    exclusive_with: list[str] = Field(default_factory=list)


class EligibilityStatus(StrEnum):
    """A person's eligibility for one instrument on one offering (spec section 10): a status
    the person or provider confirms, never computed by an eligibility engine in M0."""

    CONFIRMED = "confirmed"
    POTENTIALLY_ELIGIBLE = "potentially_eligible"
    INELIGIBLE = "ineligible"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class AwardState(StrEnum):
    """Whether an award was actually made, apart from eligibility: an eligible person may
    still not win a competitive award."""

    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    APPROVED = "approved"
    REFUSED = "refused"


class Support(StrictModel):
    """One use of a non-repayable instrument on one variant. Paid to the provider, it reduces
    the fees the person pays and is never also a receipt; paid to the person, it is a receipt
    in its month and reduces direct cost once (FIN1-10)."""

    instrument_id: str
    kind: InstrumentKind
    covers_fees_in_full: bool = False  # a waiver of the whole fee, whatever its amount
    amount: Money | None = None
    paid_to: Literal["provider", "person"]
    paid_month_offset: Annotated[int, Field(ge=0)] | None = None  # for a payment to the person
    proven_before_outflows: bool = False  # stated to arrive before that month's outflows
    eligibility: EligibilityStatus
    award: AwardState
    # An explicitly conditional award scenario ("if funding is approved"): counted in the
    # base and delay scenarios, never in no-award and never as unconditional (spec section 10).
    assumed: bool = False
    review_state: RecordState
    cited: Citation

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.kind not in NON_REPAYABLE:
            raise ValueError("only non-repayable support is planned: a loan is information")
        if (
            self.award is AwardState.APPROVED
            and self.eligibility is not EligibilityStatus.CONFIRMED
        ):
            raise ValueError("an approved award needs confirmed eligibility")
        if self.covers_fees_in_full == (self.amount is not None):
            raise ValueError("support covers the fees in full or states its amount")
        if (self.paid_to == "person") != (self.paid_month_offset is not None):
            raise ValueError("support paid to the person states its month")
        return self

    @property
    def amount_minor(self) -> int:
        """The stated amount in minor units, for arithmetic; 0 for a waiver in full."""
        return self.amount.minor_units if self.amount is not None else 0

    @property
    def confirmed(self) -> bool:
        """Counts in every scenario, and so in unconditional figures."""
        return self.award is AwardState.APPROVED

    @property
    def conditional(self) -> bool:
        """Counts only while the award is assumed: the base and delay scenarios."""
        return (
            not self.confirmed
            and self.assumed
            and self.award is not AwardState.REFUSED
            and self.eligibility
            in (EligibilityStatus.CONFIRMED, EligibilityStatus.POTENTIALLY_ELIGIBLE)
        )


class FeeLoanKind(StrEnum):
    """The two loans paid straight to the provider that are a loan to repay in L0: a tuition
    fee loan (spec section 22, 2026-11-01) and, by the product owner's provisional yes of the
    same day, an Advanced Learner Loan. One rule for both; the kind only says which."""

    TUITION_FEE_LOAN = "tuition_fee_loan"
    ADVANCED_LEARNER_LOAN = "advanced_learner_loan"


class TuitionFeeLoan(StrictModel):
    """A fee loan paid straight to the provider (a tuition fee loan, or an Advanced Learner
    Loan: `kind`), as the person states it for one
    variant (spec section 22, 2026-11-01; FUNDING-06). It pays the variant's fees (never its
    extra costs), after any support paid to the provider, up to its amount: what it pays is not
    the person's payment, cash or direct spending, and the route carries it as a loan to repay
    later. It is never support, a grant, income or a receipt, and Careerwright never chooses
    it: the person states it. Its repayment is not modelled in L0: unknown, never 0.

    Its statuses are the funding statuses (ADR 0013 decision 5): only a loan the person
    confirms approved counts in every scenario; one not yet approved, for which they are or may
    be eligible, makes the route conditional on it, beside the route where they pay the fee
    (the no-award scenario). An unknown amount leaves the route unresolved, never £0."""

    kind: FeeLoanKind = Field(
        default=FeeLoanKind.TUITION_FEE_LOAN,
        description="Which loan: a tuition fee loan unless the person says otherwise.",
    )
    amount: Money | None = Field(description="Null: not known, never £0.")
    eligibility: EligibilityStatus
    application: AwardState
    review_state: RecordState
    cited: Citation

    @model_validator(mode="after")
    def _approved_only_if_eligible(self) -> Self:
        if (
            self.application is AwardState.APPROVED
            and self.eligibility is not EligibilityStatus.CONFIRMED
        ):
            raise ValueError("an approved loan needs confirmed eligibility")
        return self

    @property
    def confirmed(self) -> bool:
        """Counts in every scenario, and so in unconditional figures."""
        return self.application is AwardState.APPROVED

    @property
    def conditional(self) -> bool:
        """Not yet approved, not refused, and the person is or may be eligible: the route rests
        on its approval (the base and delay scenarios only)."""
        return (
            not self.confirmed
            and self.application is not AwardState.REFUSED
            and self.eligibility
            in (EligibilityStatus.CONFIRMED, EligibilityStatus.POTENTIALLY_ELIGIBLE)
        )


class WorkPatternKind(StrEnum):
    RETAIN_WORK = "retain_work"  # "remain in the current job while studying" (OPTN-07)
    REDUCED_HOURS = "reduced_hours"
    TEMPORARY_STUDY_BREAK = "temporary_study_break"
    LEAVE_CURRENT_JOB = "leave_current_job"  # an explicit decision, never a side effect


class WorkPattern(StrictModel):
    """How the person's current job runs while a variant is active, as they confirmed it: its
    weekly hours and the take-home pay they confirmed (no tax or benefit is inferred)."""

    kind: WorkPatternKind
    hours_per_week: Hours
    net_income: Money  # a month, while the variant is active
    cited: Citation


class Wage(StrictModel):
    """A job's or an apprenticeship's take-home pay a month, as the person confirmed it: it
    starts at the offer gate and never funds a payment before it arrives."""

    net_income: Money
    cited: Citation


class Variant(StrictModel):
    """One reviewed start of a concept: an offering with the payment plan, work pattern, wage
    and support the person confirmed for it."""

    variant_id: str
    offering_id: str
    plan_id: str | None = None
    work_pattern: WorkPattern | None = Field(
        default=None,
        description="Null: none confirmed yet, so the continuation scenario's work applies.",
    )
    wage: Wage | None = Field(default=None, description="Null: no take-home wage confirmed yet.")
    supports: list[Support] = Field(
        default_factory=list,
        description="The support the person has confirmed for this variant: empty means none "
        "confirmed yet, never that none is available.",
    )
    stacking_confirmed: bool = Field(
        default=False,
        description="The person confirmed that this variant's supports may be combined: "
        "neither excludes the other and together they stay within each one's eligible costs. "
        "Until then, more than one support leaves the route unresolved.",
    )
    tuition_fee_loan: TuitionFeeLoan | None = Field(
        default=None,
        description="A tuition fee loan paid straight to the provider, as the person stated "
        "it: a loan to repay later, never support. Null: none stated.",
    )
    condition_statuses: dict[str, EligibilityStatus] = Field(
        default_factory=dict,
        description="The person's status for each of the offering's eligibility conditions, "
        "by the condition's field: only `confirmed` meets one.",
    )
    entry_requirements_met: bool | None = Field(
        default=None,
        description="Whether the person meets the stated entry requirements: null is not yet "
        "confirmed; false is their own 'no', still never ineligible.",
    )
    entry_expected: bool = Field(
        default=False,
        description="A stated entry requirement is named only by a qualification the person "
        "expects (Task 6f): met only if they get their grades, so unresolved, never met.",
    )


class CatalogueLabel(StrictModel):
    """What the catalogue is: a pack version and its date, or a fixture (R9)."""

    name: str
    dated: date
    synthetic: bool


class Catalogue(StrictModel):
    label: CatalogueLabel
    concepts: list[ActionConcept]
    offerings: list[Offering]
    instruments: list[FundingInstrument] = Field(default_factory=list)
    variants: list[Variant]

    @model_validator(mode="after")
    def _references(self) -> Self:
        concepts = {c.concept_id for c in self.concepts}
        offerings = {o.offering_id: o for o in self.offerings}
        problems = [o.offering_id for o in self.offerings if o.concept_id not in concepts]
        for variant in self.variants:
            offering = offerings.get(variant.offering_id)
            if offering is None or (
                variant.plan_id is not None and offering.plan(variant.plan_id) is None
            ):
                problems.append(variant.variant_id)
        ids = [v.variant_id for v in self.variants]
        if problems or len(ids) != len(set(ids)):
            raise ValueError(f"catalogue references do not resolve: {sorted(problems)}")
        return self
