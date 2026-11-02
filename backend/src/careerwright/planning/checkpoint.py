"""The Options chapter's review checkpoint, as facts (Task 12b; spec section 10, "Option review
checkpoint"; S5.3; plan v1.5 and v1.6). Pure: no SQL, no network, no model. Facts and codes,
never sentences (R11): the web words every code.

For each target, what the person reviews before a route search:

- **Each option** with its review state and date, whether the person added it, and the facts
  the route search still lacks for it (`figures.MissingFact`), the ones they supplied as their
  own figures, the intake months its page states, its entry requirements with the person's
  qualifications that name each (Task 6f: an expected one is never met), its fee's eligibility
  conditions with their status, each age rule beside it, its planned outcomes with the
  person's decision on each provisional mapping (accept or override, Task 12a's command), and
  whether it is left out of the search.
- **Each scheme** (funding instrument) with its review state and its age rules beside it. The
  person's age is never asked or inferred (spec section 3; Task 6f), so no age rule is ever
  applied: each is shown, `applied: false`.
- **Whether any option is reviewed**: a target with none says so (and offers "add an option
  yourself"; the words are the web's).
- **The scope** against the M0 bounds (24 concepts, two starts each): over either, a code asking
  the person to retain options, with the counts, never a silent cut to the first ones.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue

from careerwright.capability.outcomes import (
    EvidenceKind,
    OutcomeReview,
    OutcomeType,
    PlannedOutcome,
)
from careerwright.capability.skills import (
    EntryFact,
    EntryStanding,
    PersonQualification,
    names,
)
from careerwright.planning.catalogue import (
    ActionConcept,
    Catalogue,
    CatalogueLabel,
    EligibilityStatus,
    Fact,
    InstrumentKind,
    RecordState,
    SuppliedFact,
)
from careerwright.planning.figures import MissingFact, variant_missing
from careerwright.planning.search import M0SearchLimits
from careerwright.profile.document import QualificationStatus

AGE_FIELDS = ("rule_age", "eligibility_age")  # a scheme's or an offering's age rules, by prefix
RETAIN_VARIANTS = "retain_variants"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AgeRule(StrictModel):
    """A stated age rule, beside its scheme or offering: never applied, because Careerwright
    does not know the person's age."""

    field: str
    value: JsonValue
    applied: Literal[False] = False


class EntryRequirement(StrictModel):
    """One stated entry requirement, with the person's qualifications that name it."""

    field: str
    value: JsonValue
    qualifications: list[EntryFact]


class ConditionFact(StrictModel):
    """An eligibility condition of the option's stated fee, with the person's status for it
    (null: not answered; only `confirmed` meets it)."""

    field: str
    value: JsonValue
    status: EligibilityStatus | None


class OutcomeFacts(StrictModel):
    """A planned outcome of the option (OUT-1), with the person's decision on a provisional
    mapping: accept it as their assumption or override it, through the planning inputs'
    command (ADR 0012 decision 11). Null: no decision yet."""

    outcome_id: str
    skill_id: str
    outcome_type: OutcomeType
    level_on_completion: int | None
    evidence_kind: EvidenceKind
    review_state: OutcomeReview
    decision: Literal["accept", "override"] | None


class OptionFacts(StrictModel):
    variant_id: str
    offering_id: str
    concept_id: str
    plan_id: str | None
    review_states: list[RecordState]  # its concept's, then its offering's
    as_of: date | None  # the date of its evidence, or the day the person added it
    added_by_person: bool
    missing: list[MissingFact]
    supplied: list[SuppliedFact]
    stated_intakes: list[date]
    entry_requirements: list[EntryRequirement]
    entry_requirements_met: bool | None  # the person's answer: null not yet answered
    entry_expected: bool  # met only if they get the grades they expect: never met
    eligibility_conditions: list[ConditionFact]
    age_rules: list[AgeRule]
    outcomes: list[OutcomeFacts]
    left_out: bool  # the person left it out of the route search


class SchemeFacts(StrictModel):
    instrument_id: str
    kind: InstrumentKind
    review_state: RecordState
    as_of: date | None
    age_rules: list[AgeRule]


class ConceptStarts(StrictModel):
    concept_id: str
    starts: int


class Scope(StrictModel):
    """The retained options against the M0 bounds. Over either bound, `code` asks the person
    to retain options (leave others out); nothing is cut silently."""

    concepts: int
    max_concepts: int
    most_starts: int
    max_starts: int
    over_starts: list[ConceptStarts]  # each concept with more starts than the bound
    code: Literal["retain_variants"] | None


class TargetCheckpoint(StrictModel):
    target_title: str
    pack_target_id: str | None
    note: Literal["no_pack_target", "ambiguous_crosswalk"] | None
    label: CatalogueLabel | None  # the pack's version and date, or the person's own options'
    reviewed_options: int  # options whose concept and offering are both reviewed
    options: list[OptionFacts]
    schemes: list[SchemeFacts]
    scope: Scope


def _age_rules(facts: Sequence[Fact]) -> list[AgeRule]:
    return [
        AgeRule(field=f.field, value=f.value)
        for f in facts
        if f.field.startswith(AGE_FIELDS) and f.value is not None
    ]


def entry_requirements(
    concept: ActionConcept,
    qualifications: Sequence[PersonQualification],
    keys: Mapping[str, str],
) -> list[EntryRequirement]:
    """Each stated entry requirement with the person's qualifications whose words, as a
    concept, appear whole in it (the Skills chapter's rule, `capability.skills.names`). `keys`
    holds every requirement's words and qualification name as a concept."""
    found = []
    for fact in concept.entry_requirements:
        words = fact.value if isinstance(fact.value, str) else None
        named = [
            q for q in qualifications if words is not None and names(keys[q.name], [keys[words]])
        ]
        found.append(
            EntryRequirement(
                field=fact.field,
                value=fact.value,
                qualifications=[
                    EntryFact(
                        qualification=q.name,
                        status=q.status,
                        standing=EntryStanding.EXPECTED_NOT_MET
                        if q.status is QualificationStatus.EXPECTED
                        else EntryStanding.ACHIEVED_STATED,
                    )
                    for q in named
                ],
            )
        )
    return found


def entry_texts(catalogue: Catalogue) -> list[str]:
    """Every entry requirement's words, to be keyed as concepts beside the qualifications."""
    return [
        f.value
        for c in catalogue.concepts
        for f in c.entry_requirements
        if isinstance(f.value, str)
    ]


def expected_entry(
    catalogue: Catalogue,
    qualifications: Sequence[PersonQualification],
    keys: Mapping[str, str],
) -> frozenset[str]:
    """The concepts with an entry requirement that only qualifications the person expects
    name: met only if they get their grades, so never met (plan v1.6)."""
    found = set()
    for concept in catalogue.concepts:
        for requirement in entry_requirements(concept, qualifications, keys):
            standings = {q.standing for q in requirement.qualifications}
            if standings == {EntryStanding.EXPECTED_NOT_MET}:
                found.add(concept.concept_id)
    return frozenset(found)


def scope(catalogue: Catalogue | None, limits: M0SearchLimits) -> Scope:
    """The retained options (the catalogue after the person's exclusions) against the M0
    bounds."""
    starts: Counter[str] = Counter()
    if catalogue is not None:
        offered = {o.offering_id: o.concept_id for o in catalogue.offerings}
        starts = Counter(offered[v.offering_id] for v in catalogue.variants)
    over = [
        ConceptStarts(concept_id=c, starts=n)
        for c, n in sorted(starts.items())
        if n > limits.max_starts_per_action
    ]
    beyond = len(starts) > limits.max_actions or bool(over)
    return Scope(
        concepts=len(starts),
        max_concepts=limits.max_actions,
        most_starts=max(starts.values(), default=0),
        max_starts=limits.max_starts_per_action,
        over_starts=over,
        code=RETAIN_VARIANTS if beyond else None,
    )


def target_checkpoint(
    *,
    target_title: str,
    pack_target_id: str | None,
    note: Literal["no_pack_target", "ambiguous_crosswalk"] | None,
    answered: Catalogue | None,
    retained: Catalogue | None,
    left_out: frozenset[str],
    qualifications: Sequence[PersonQualification],
    keys: Mapping[str, str],
    limits: M0SearchLimits,
    outcomes: Sequence[PlannedOutcome] = (),
    decisions: Mapping[str, Literal["accept", "override"]] | None = None,
) -> TargetCheckpoint:
    """One target's checkpoint. `answered`: its catalogue with the person's answers, figures
    and expected entry in it (`inputs.with_answers`), every option kept; `retained`: the same
    without the options left out."""
    options: list[OptionFacts] = []
    schemes: list[SchemeFacts] = []
    reviewed = 0
    if answered is not None:
        concepts = {c.concept_id: c for c in answered.concepts}
        offerings = {o.offering_id: o for o in answered.offerings}
        for variant in answered.variants:
            offering = offerings[variant.offering_id]
            concept = concepts[offering.concept_id]
            states = [concept.review_state, offering.review_state]
            reviewed += states == [RecordState.REVIEWED, RecordState.REVIEWED]
            options.append(
                OptionFacts(
                    variant_id=variant.variant_id,
                    offering_id=offering.offering_id,
                    concept_id=concept.concept_id,
                    plan_id=variant.plan_id,
                    review_states=states,
                    as_of=offering.as_of or concept.as_of,
                    added_by_person=concept.added_by_person,
                    missing=variant_missing(concept, offering, variant),
                    supplied=list(offering.supplied),
                    stated_intakes=list(offering.stated_intakes),
                    entry_requirements=entry_requirements(concept, qualifications, keys),
                    entry_requirements_met=variant.entry_requirements_met,
                    entry_expected=variant.entry_expected
                    and variant.entry_requirements_met is not False,
                    eligibility_conditions=[
                        ConditionFact(
                            field=c.field,
                            value=c.value,
                            status=variant.condition_statuses.get(c.field),
                        )
                        for c in offering.eligibility_conditions
                    ],
                    age_rules=_age_rules(offering.eligibility_conditions),
                    outcomes=[
                        OutcomeFacts(
                            outcome_id=o.outcome_id,
                            skill_id=o.skill_id,
                            outcome_type=o.outcome_type,
                            level_on_completion=o.level_on_completion,
                            evidence_kind=o.evidence_kind,
                            review_state=o.review_state,
                            decision=(decisions or {}).get(o.outcome_id),
                        )
                        for o in outcomes
                        if o.offering_id == (offering.outcomes_from or offering.offering_id)
                    ],
                    left_out=variant.variant_id in left_out,
                )
            )
        schemes = [
            SchemeFacts(
                instrument_id=i.instrument_id,
                kind=i.kind,
                review_state=i.review_state,
                as_of=i.as_of,
                age_rules=_age_rules(i.rules),
            )
            for i in answered.instruments
        ]
    return TargetCheckpoint(
        target_title=target_title,
        pack_target_id=pack_target_id,
        note=note,
        label=answered.label if answered is not None else None,
        reviewed_options=reviewed,
        options=options,
        schemes=schemes,
        scope=scope(retained, limits),
    )
