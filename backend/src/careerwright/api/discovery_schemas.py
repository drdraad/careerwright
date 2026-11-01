"""API contract for career discovery (slates, their written explanation, targets chosen
from ESCO and stored once) and the early requirement sketch. No suggestion carries a
percentage, score or rank meant as fit, and no response carries a sentence the person reads:
codes, numbers and the person's or ESCO's own words, which the web words (ruling R11)."""

import uuid
from datetime import date
from typing import Literal

from pydantic import Field

from careerwright.api.catalogue_schemas import IscoGroupOut
from careerwright.api.schemas import ResponseModel, RunOut
from careerwright.catalogue.esco import concept_id
from careerwright.catalogue.pay import FloorCounts, FloorUnknown
from careerwright.catalogue.records import ConceptKind, SkillRef, TaxonomyRelease
from careerwright.money import Money
from careerwright.profile.discovery import DiscoveryProposal, EvidenceItem, QueryChannel
from careerwright.profile.document import FieldState, PayPeriod
from careerwright.profile.exploration import AiFilterView, SlateView, Suggestion
from careerwright.profile.interview import ProfileField, ProposalOrigin
from careerwright.profile.records import TargetCoverage, TargetKind, TargetLink, TargetRecord
from careerwright.profile.sketch import OccupationRef, Resolution, Sketch, Step, TargetSketch
from careerwright.profile.slate import (
    POOL_LIMIT,
    POOL_TARGET,
    SLATE_SIZE,
    Direction,
    Emphasis,
    Left,
    NotIncluded,
    PoolQuery,
    SlateChannel,
)
from careerwright.profile.slate_explanation import QuoteSource, RecordPart, SlateExplanation
from careerwright.profile.slate_facts import FewerReason, SlateNote, SuggestionReason, TitleIdea


class EvidenceOut(ResponseModel):
    """One of the person's confirmed answers, quoted."""

    field: ProfileField
    text: str

    @classmethod
    def of(cls, item: EvidenceItem) -> "EvidenceOut":
        return cls(field=item.field, text=item.text)


class QueryOut(ResponseModel):
    query_id: str
    text: str
    channel: QueryChannel
    based_on: list[EvidenceOut]


class HypothesisOut(ResponseModel):
    title: str = Field(description="A search hypothesis until ESCO is found to hold it.")
    based_on: list[EvidenceOut]


class DiscoveryProposalOut(ResponseModel):
    """The validated searches. They name no suggestion: the slate is computed from them."""

    origin: ProposalOrigin = Field(
        description="fixture: the deterministic demo proposer (synthetic), never a live model."
    )
    prompt_version: str
    queries: list[QueryOut]
    hypotheses: list[HypothesisOut]

    @classmethod
    def of(cls, proposal: DiscoveryProposal) -> "DiscoveryProposalOut":
        return cls(
            origin=proposal.origin,
            prompt_version=proposal.prompt_version,
            queries=[
                QueryOut(
                    query_id=q.query_id,
                    text=q.text,
                    channel=q.channel,
                    based_on=[EvidenceOut.of(e) for e in q.based_on],
                )
                for q in proposal.queries
            ],
            hypotheses=[
                HypothesisOut(title=h.title, based_on=[EvidenceOut.of(e) for e in h.based_on])
                for h in proposal.hypotheses
            ],
        )


class QuotationOut(ResponseModel):
    source: QuoteSource
    answer_field: ProfileField | None = Field(
        description="Which of your answers, for a quotation of yours."
    )
    record_part: RecordPart | None = Field(
        description="Which part of ESCO's record, for a quotation of ESCO's."
    )
    text: str = Field(description="The source's own words, checked as an exact span of it.")


class ClaimOut(ResponseModel):
    text: str = Field(
        description="The model's own words (or the demo explainer's), at most 240 characters "
        "with no quotation of their own: not checked against any source. Only the quotations "
        "beside it were checked."
    )
    quotations: list[QuotationOut]


class WrittenWhyOut(ResponseModel):
    concept_id: uuid.UUID
    title: str
    claims: list[ClaimOut]


class WrittenExplanationOut(ResponseModel):
    origin: ProposalOrigin = Field(
        description="fixture: the deterministic demo explainer (synthetic), never a live model."
    )
    prompt_version: str
    profile_version: int = Field(description="The discovery's pinned version it quotes.")
    release: str = Field(description="The ESCO release whose records it quotes.")
    suggestions: list[WrittenWhyOut] = Field(
        description="The first view's suggestions (balanced, no exclusions), in its order. A "
        "suggestion another view shows that is not here has no written explanation."
    )

    @classmethod
    def of(cls, written: SlateExplanation) -> "WrittenExplanationOut":
        return cls(
            origin=written.origin,
            prompt_version=written.prompt_version,
            profile_version=written.profile_version,
            release=written.release,
            suggestions=[
                WrittenWhyOut(
                    concept_id=s.concept_id,
                    title=s.title,
                    claims=[
                        ClaimOut(
                            text=c.text,
                            quotations=[QuotationOut(**q.model_dump()) for q in c.quotations],
                        )
                        for c in s.claims
                    ],
                )
                for s in written.suggestions
            ],
        )


class ExplanationRunOut(ResponseModel):
    """A slate explanation's run, as asking for it answers: never what it wrote, since a
    command's answer is kept as its receipt and model output is kept sealed. The discovery
    (`GET .../discoveries/{id}`) carries the written text."""

    explanation_id: uuid.UUID
    discovery_id: uuid.UUID
    run: RunOut
    can_retry: bool = Field(
        description="The run failed before any request reached a model, so the person's Try "
        "again (`retry_failed`) may start the note afresh. False once a request was sent: "
        "the slate has had its one call, and Suggest again makes a new slate."
    )


class SlateExplanationOut(ExplanationRunOut):
    """The written "Why this could suit you" of a discovery's slate: at most one per
    discovery, whatever view is shown. `run` is authoritative for its state; `written`
    exists only once the run is complete, and a failed run's failure class says why there is
    none. It changes no suggestion; the deterministic provenance beside it (each
    suggestion's linked answers, searches and ESCO source) is what exports cite."""

    written: WrittenExplanationOut | None


class DiscoveryOut(ResponseModel):
    """One discovery. `run` is authoritative for its state; `proposal` exists only once the
    run is complete, and a failed run's failure class says why there is none."""

    discovery_id: uuid.UUID
    profile_version: int = Field(description="The profile version it read, pinned.")
    current: bool = Field(
        description="Whether it was made from the current answers: true while every profile "
        "version since the pinned one changed only the targets, each chosen from this "
        "discovery's slate; false once anything else changed."
    )
    run: RunOut
    proposal: DiscoveryProposalOut | None
    explanation: SlateExplanationOut | None = Field(
        description="Its slate's written explanation; null: never asked for."
    )


class DiscoveryPage(ResponseModel):
    items: list[DiscoveryOut] = Field(description="Newest first.")
    next_cursor: str | None


class ReleaseRefOut(ResponseModel):
    """The ESCO release the slate searched; show the attribution and adaptation with it."""

    dataset_id: str
    version: str
    attribution: str
    adaptation: str
    sample: bool

    @classmethod
    def of(cls, release: TaxonomyRelease) -> "ReleaseRefOut":
        return cls(
            dataset_id=release.dataset_id,
            version=release.version,
            attribution=release.attribution,
            adaptation=release.adaptation,
            sample=release.sample,
        )


class SourceRefOut(ResponseModel):
    kind: Literal["esco"] = "esco"
    uri: str = Field(description="The ESCO occupation's URI.")
    release: str


class SharedSkillOut(ResponseModel):
    skill_id: uuid.UUID
    label: str
    skill_type: str | None

    @classmethod
    def of(cls, skill: SkillRef) -> "SharedSkillOut":
        return cls(
            skill_id=skill.skill_id, label=skill.preferred_label, skill_type=skill.skill_type
        )


class SuggestionOut(ResponseModel):
    """A career hypothesis (spec section 4's `CareerSuggestion`): an ESCO occupation, the
    answers that found it and ESCO's facts about it, as facts the web words. Becoming a
    target needs the person's choice (`POST .../targets`)."""

    concept_id: uuid.UUID
    concept_kind: Literal[ConceptKind.ESCO] = ConceptKind.ESCO
    title: str
    esco_code: str
    isco_group: IscoGroupOut
    family: IscoGroupOut = Field(description="The kind of work: its ISCO-08 minor group.")
    sector: IscoGroupOut = Field(description="Its ISCO-08 major group.")
    direction: Direction
    channels: list[SlateChannel]
    linked_evidence: list[EvidenceOut] = Field(description="The answers that found it.")
    matched_queries: list[str] = Field(description="The query IDs that found it.")
    sources: list[SourceRefOut]
    workday: str = Field(description="ESCO's description of the work, shortened.")
    reasons: list[SuggestionReason] = Field(
        description="Why it could suit the person: what found it, from at most three of their "
        "answers."
    )
    essential_skill_count: int = Field(
        description="Essential skills ESCO lists for it, not yet compared with experience."
    )
    essential_skills: list[str] = Field(description="The first few of them, by ESCO's label.")
    regulated: bool | None = Field(
        description="ESCO marks it a regulated profession in at least one European country "
        "(whether England requires registration isn't checked); null: ESCO records no note."
    )
    different_kind_of_work: bool = Field(
        description="Another kind of work than any the person told Careerwright about (false "
        "when that isn't known)."
    )
    shared_skills: list[SharedSkillOut] = Field(
        description="The essential skills Careerwright joined it to a title of the person's "
        "by (those ESCO lists for both), by label; empty unless it was joined by shared skills."
    )

    @classmethod
    def of(cls, suggestion: Suggestion, release: TaxonomyRelease) -> "SuggestionOut":
        candidate, facts, words = suggestion.candidate, suggestion.facts, suggestion.explanation
        evidence = list(
            dict.fromkeys(item for match in candidate.matches for item in match.query.based_on)
        )
        return cls(
            concept_id=facts.concept_id,
            title=facts.preferred_label,
            esco_code=facts.esco_code,
            isco_group=IscoGroupOut(code=facts.unit.code, label=facts.unit.label),
            family=IscoGroupOut(code=facts.family.code, label=facts.family.label),
            sector=IscoGroupOut(code=facts.sector.code, label=facts.sector.label),
            direction=candidate.direction,
            channels=sorted(candidate.channels),
            linked_evidence=[EvidenceOut.of(e) for e in evidence],
            matched_queries=list(dict.fromkeys(m.query.query_id for m in candidate.matches)),
            sources=[SourceRefOut(uri=facts.esco_uri, release=release.dataset_id)],
            workday=words.workday,
            reasons=words.reasons,
            essential_skill_count=facts.essential_skill_count,
            essential_skills=list(facts.essential_skills),
            regulated=facts.regulated,
            different_kind_of_work=words.different_kind_of_work,
            shared_skills=[SharedSkillOut.of(skill) for skill in suggestion.shared_skills],
        )


class NotIncludedOut(ResponseModel):
    """A pooled occupation the slate does not show, and why."""

    concept_id: uuid.UUID
    title: str
    family: IscoGroupOut
    reason: NotIncluded
    duplicate_of: uuid.UUID | None
    duplicate_of_title: str | None

    @classmethod
    def of(cls, left: Left, titles: dict[uuid.UUID, str]) -> "NotIncludedOut":
        occupation = left.candidate.occupation
        return cls(
            concept_id=occupation.concept_id,
            title=occupation.title,
            family=IscoGroupOut(code=occupation.family_code, label=occupation.family_label),
            reason=left.reason,
            duplicate_of=left.duplicate_of,
            duplicate_of_title=titles.get(left.duplicate_of) if left.duplicate_of else None,
        )


class PoolQueryOut(ResponseModel):
    query_id: str
    text: str
    channel: SlateChannel
    based_on: list[EvidenceOut]
    hits: int = Field(
        description="Occupations this query found (bounded per query); for one too general "
        "to find work on its own, those another search found that it adds weight to."
    )
    reach: int = Field(description="Occupations it reached in all, past its own bound too.")
    too_general: bool = Field(
        description="Too general to find work on its own (it reaches too many occupations, or "
        "too many different skills): it only adds weight to work another search found."
    )

    @classmethod
    def of(cls, query: PoolQuery) -> "PoolQueryOut":
        return cls(
            query_id=query.query_id,
            text=query.text,
            channel=query.channel,
            based_on=[EvidenceOut.of(e) for e in query.based_on],
            hits=len(query.hits),
            reach=query.reach,
            too_general=query.too_general,
        )


class ExcludedOut(ResponseModel):
    occupations: int = Field(description="Pooled occupations your excluded titles removed.")
    families: int = Field(description="Pooled occupations your excluded kinds of work removed.")


class FloorReasonOut(ResponseModel):
    reason: FloorUnknown
    count: int


class SalaryFloorOut(ResponseModel):
    """Your confirmed salary floor, applied as a hard filter: a suggestion is left out only
    when official pay for it (ASHE through a reviewed UK SOC mapping, the 90th percentile in
    every region of your cities) is below it. Unknown pay is never treated as below it. The
    web words the counts, which add up: left out, meeting it, and kept by reason."""

    amount: Money
    period: PayPeriod
    basis: Literal["gross"] = "gross"
    left_out: int = Field(description="Suggestions left out because their pay is below it.")
    meets: int
    kept_pay_unknown: int = Field(description="Kept: their pay could not be compared.")
    kept_by_reason: list[FloorReasonOut]

    @classmethod
    def of(cls, counts: FloorCounts) -> "SalaryFloorOut":
        floor = counts.floor
        return cls(
            amount=Money(minor_units=floor.minor_units, currency="GBP"),
            period=PayPeriod(floor.period),
            left_out=counts.left_out,
            meets=counts.meets,
            kept_pay_unknown=counts.kept_unknown,
            kept_by_reason=[FloorReasonOut(reason=r, count=n) for r, n in counts.unknown.items()],
        )


class AiResilienceFilterOut(ResponseModel):
    """The AI Resilience filter's basis and counts (AIR1-05): the minimum applies to the
    lower end of a reviewed range; unscored occupations are included unless you switch
    them off, and are never read as 0 or 10. The web words the counts, when the filter is not
    at its default (a minimum, or unscored ones left out)."""

    basis: Literal["lower_bound"] = "lower_bound"
    minimum: int | None = Field(description="Null: Any.")
    include_unscored: bool
    scored: int
    below_minimum: int
    unscored: int
    unscored_excluded: int
    synthetic: bool = Field(
        description="A scored range here is a synthetic fixture's, never a real assessment."
    )
    pack_version: str
    pack_dated: date

    @classmethod
    def of(cls, view: AiFilterView) -> "AiResilienceFilterOut":
        chosen = view.chosen
        return cls(
            minimum=chosen.minimum,
            include_unscored=chosen.include_unscored,
            scored=view.scored,
            below_minimum=view.below_minimum,
            unscored=view.unscored,
            unscored_excluded=view.unscored_excluded,
            synthetic=view.synthetic,
            pack_version=view.pack_version,
            pack_dated=view.pack_dated,
        )


class SlateOut(ResponseModel):
    """A varied slate of up to six career hypotheses from the discovery's searches, computed
    deterministically each time it is read, with every count that explains it. A title of
    the person's own (their role, a target, or a search naming one) joins other work only by
    shared essential skills, never by its words, and only once it names one occupation."""

    discovery_id: uuid.UUID
    profile_version: int
    release: ReleaseRefOut
    emphasis: Emphasis
    target_size: int = SLATE_SIZE
    family_limit: int = Field(description="At most this many from one kind of work.")
    suggestions: list[SuggestionOut]
    fewer_reasons: list[FewerReason] = Field(
        description="Why there are fewer than six, if there are, as facts the web words."
    )
    notes: list[SlateNote] = Field(
        description="How the slate was made, as facts the web words: a control's effect, a "
        "changed ESCO release, answers not searched, answers that found no work or were too "
        "general to find it alone, what a join keeps, or fewer occupations to choose from than "
        "Careerwright aims for."
    )
    salary_floor: SalaryFloorOut | None = Field(
        description="Your confirmed salary floor's effect, as a hard filter; null with none."
    )
    ai_resilience_filter: AiResilienceFilterOut
    pool_size: int = Field(description="Distinct occupations after folding near-duplicates.")
    pool_target: tuple[int, int] = (POOL_TARGET, POOL_LIMIT)
    beyond_pool_limit: int = Field(
        description="Occupations found but not kept: past a join's best 30 or the pool's bound."
    )
    excluded: ExcludedOut
    queries: list[PoolQueryOut] = Field(description="Every search that ran, with its hits.")
    unsearchable_queries: list[str] = Field(description="Queries with no searchable word.")
    title_ideas: list[TitleIdea] = Field(
        description="Titles Careerwright thought of, each with what it did with it (`reason`): "
        "one ESCO holds as a label joins the slate's pool; one the UK job-title index lists "
        "(exactly) is a suggestion in its own list beside the slate, never in it; one no list "
        "holds is not yet found and never suggested."
    )
    not_included: list[NotIncludedOut] = Field(description="Show why this wasn't included.")
    unmatched_titles: list[str] = Field(
        description="Titles of the person's own that Careerwright couldn't match to an "
        "occupation in ESCO (case, punctuation and plurals folded): nothing is joined to them."
    )
    ambiguous_titles: list[str] = Field(
        description="Titles of the person's own that Careerwright matched to several "
        "occupations in ESCO: nothing is joined to them until the person chooses which one "
        "they mean."
    )
    familiarity_known: bool = Field(
        description="Whether the person's role or a target names an ESCO occupation, so "
        "Careerwright knows the kinds of work close to theirs: only then does a direction say "
        "it is different from their work (`less_familiar`)."
    )

    @classmethod
    def of(cls, view: SlateView, emphasis: Emphasis) -> "SlateOut":
        slate = view.slate
        return cls(
            discovery_id=view.discovery.run.run_id,
            profile_version=view.discovery.run.profile_version or 0,
            release=ReleaseRefOut.of(view.release),
            emphasis=emphasis,
            family_limit=slate.family_limit,
            suggestions=[SuggestionOut.of(s, view.release) for s in view.suggestions],
            fewer_reasons=slate.fewer_reasons,
            notes=slate.notes,
            salary_floor=SalaryFloorOut.of(view.salary_floor) if view.salary_floor else None,
            ai_resilience_filter=AiResilienceFilterOut.of(view.ai_filter),
            pool_size=slate.pool_size,
            beyond_pool_limit=slate.beyond_limit,
            excluded=ExcludedOut(**slate.excluded),
            queries=[PoolQueryOut.of(q) for q in view.queries],
            unsearchable_queries=view.unsearchable_queries,
            title_ideas=view.title_ideas,
            not_included=[NotIncludedOut.of(left, view.titles) for left in slate.not_included],
            unmatched_titles=view.unmatched_titles,
            ambiguous_titles=view.ambiguous_titles,
            familiarity_known=view.familiarity_known,
        )


class OccupationRefOut(ResponseModel):
    concept_id: uuid.UUID
    title: str
    isco_group: IscoGroupOut

    @classmethod
    def of(cls, ref: OccupationRef) -> "OccupationRefOut":
        return cls(
            concept_id=ref.concept_id,
            title=ref.title,
            isco_group=IscoGroupOut(code=ref.isco_group.code, label=ref.isco_group.label),
        )


class TargetSketchOut(ResponseModel):
    title: str
    resolution: Resolution
    occupations: list[OccupationRefOut] = Field(
        description="The ESCO occupation, or the several that share the title (choose one)."
    )
    close_matches: list[OccupationRefOut] = Field(
        description="For a title Careerwright couldn't match to an occupation in ESCO: the "
        "nearest occupations by full text."
    )
    requirements: list[str] = Field(description="ESCO's essential skills, the first few.")
    requirement_count: int | None = Field(description="null: no requirement list.")
    regulated: bool | None
    coverage: TargetCoverage = Field(
        description="From the target's stored record: one of the option pack's targets, or "
        "not (several: the pack targets it could be, none guessed)."
    )

    @classmethod
    def of(cls, target: TargetSketch) -> "TargetSketchOut":
        return cls(
            title=target.title,
            resolution=target.resolution,
            occupations=[OccupationRefOut.of(o) for o in target.occupations],
            close_matches=[OccupationRefOut.of(o) for o in target.close_matches],
            requirements=target.requirements,
            requirement_count=target.requirement_count,
            regulated=target.regulated,
            coverage=target.coverage,
        )


class TargetRecordOut(ResponseModel):
    """A target as it is stored once, when chosen or saved: what it names, the source of that
    link and how far Careerwright can cover it. Every chapter reads this record, so a title
    resolves the same everywhere."""

    key: str = Field(
        description='The title as a concept (case, punctuation, plurals, accents and "&" '
        "folded): the target's identity."
    )
    title: str = Field(description="The person's words, as the profile holds them.")
    kind: TargetKind
    link: TargetLink
    concept_id: uuid.UUID | None = Field(
        description="The ESCO occupation the title names in ESCO itself (the person's choice, "
        "or the one occupation holding the title as a label); null otherwise."
    )
    label_matches: int = Field(
        description="How many ESCO occupations hold the title as a label (several: the person "
        "chooses which they mean, none is guessed)."
    )
    coverage: TargetCoverage
    pack_target_id: str | None = Field(description="The option pack's target, when covered.")

    @classmethod
    def of(cls, record: TargetRecord) -> "TargetRecordOut":
        esco = record.esco_occupation
        return cls(
            key=record.key,
            title=record.title,
            kind=record.kind,
            link=record.link,
            concept_id=concept_id(esco) if esco else None,
            label_matches=len(record.label_matches),
            coverage=record.coverage,
            pack_target_id=record.pack_target_id,
        )


class TargetRecordsOut(ResponseModel):
    profile_version: int
    targets: list[TargetRecordOut] = Field(description="In the profile's order, one per concept.")


class StepOut(ResponseModel):
    step: Step
    state: Literal["unresolved"]


class SketchOut(ResponseModel):
    """The early requirement sketch: never a feasible or optimal route, never priced or
    dated. Every step stays unresolved until a later chapter resolves it. Facts only: the web
    words them."""

    profile_version: int
    inputs: dict[ProfileField, FieldState] = Field(
        description="The minimum inputs: a target and four practical answers."
    )
    not_asked: list[ProfileField]
    targets: list[TargetSketchOut]
    steps: list[StepOut]

    @classmethod
    def of(cls, sketch: Sketch) -> "SketchOut":
        return cls(
            profile_version=sketch.profile_version,
            inputs=sketch.inputs,
            not_asked=sketch.not_asked,
            targets=[TargetSketchOut.of(t) for t in sketch.targets],
            steps=[StepOut(step=step, state="unresolved") for step in sketch.steps],
        )
