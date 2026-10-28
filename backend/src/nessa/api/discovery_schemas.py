"""API contract for career discovery (slates, targets chosen from ESCO) and the early
requirement sketch. No suggestion carries a percentage, score or rank meant as fit."""

import uuid
from typing import Literal

from pydantic import Field

from nessa.api.catalogue_schemas import IscoGroupOut
from nessa.api.schemas import ResponseModel, RunOut
from nessa.catalogue.records import ConceptKind, TaxonomyRelease
from nessa.profile.discovery import DiscoveryProposal, EvidenceItem, QueryChannel
from nessa.profile.document import FieldState
from nessa.profile.exploration import SlateView, Suggestion
from nessa.profile.interview import ProfileField, ProposalOrigin
from nessa.profile.sketch import OccupationRef, Resolution, Sketch, Step, TargetSketch
from nessa.profile.slate import (
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


class DiscoveryOut(ResponseModel):
    """One discovery. `run` is authoritative for its state; `proposal` exists only once the
    run is complete, and a failed run's failure class says why there is none."""

    discovery_id: uuid.UUID
    profile_version: int = Field(description="The profile version it read, pinned.")
    run: RunOut
    proposal: DiscoveryProposalOut | None


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


class SuggestionOut(ResponseModel):
    """A career hypothesis (spec section 4's `CareerSuggestion`): an ESCO occupation, the
    answers that found it and ESCO's facts about it, in words. Becoming a target needs the
    person's choice (`POST .../targets`)."""

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
    why_it_could_suit: list[str]
    what_might_not_suit: list[str]
    entry_gates: list[str]
    evidence_gaps: list[str]
    try_it: list[str] = Field(description="Low-cost ways to test the idea before committing.")

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
            why_it_could_suit=words.why,
            what_might_not_suit=words.might_not,
            entry_gates=words.entry_gates,
            evidence_gaps=words.evidence_gaps,
            try_it=words.try_it,
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
    hits: int = Field(description="Occupations this query found (bounded per query).")

    @classmethod
    def of(cls, query: PoolQuery) -> "PoolQueryOut":
        return cls(
            query_id=query.query_id,
            text=query.text,
            channel=query.channel,
            based_on=[EvidenceOut.of(e) for e in query.based_on],
            hits=len(query.hits),
        )


class ExcludedOut(ResponseModel):
    occupations: int = Field(description="Pooled occupations your excluded titles removed.")
    families: int = Field(description="Pooled occupations your excluded kinds of work removed.")


class SlateOut(ResponseModel):
    """A varied slate of up to six career hypotheses from the discovery's searches, computed
    deterministically each time it is read, with every count that explains it."""

    discovery_id: uuid.UUID
    profile_version: int
    release: ReleaseRefOut
    emphasis: Emphasis
    target_size: int = SLATE_SIZE
    family_limit: int = Field(description="At most this many from one kind of work.")
    suggestions: list[SuggestionOut]
    fewer_reasons: list[str] = Field(description="Why there are fewer than six, if there are.")
    notes: list[str] = Field(description="How a control changed the slate, in words.")
    limits_not_applied: list[str] = Field(
        description="Limits you set that the slate records but cannot apply yet."
    )
    pool_size: int = Field(description="Distinct occupations after folding near-duplicates.")
    pool_target: tuple[int, int] = (POOL_TARGET, POOL_LIMIT)
    beyond_pool_limit: int = Field(description="Occupations found past the pool's bound.")
    excluded: ExcludedOut
    queries: list[PoolQueryOut] = Field(description="Every search that ran, with its hits.")
    unsearchable_queries: list[str] = Field(description="Queries with no searchable word.")
    unsupported_hypotheses: list[str] = Field(
        description="Titles Nessa thought of that ESCO does not list: never suggested."
    )
    not_included: list[NotIncludedOut] = Field(description="Show why this wasn't included.")

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
            limits_not_applied=view.limits_not_applied,
            pool_size=slate.pool_size,
            beyond_pool_limit=slate.beyond_limit,
            excluded=ExcludedOut(**slate.excluded),
            queries=[PoolQueryOut.of(q) for q in view.queries],
            unsearchable_queries=view.unsearchable_queries,
            unsupported_hypotheses=view.unsupported_hypotheses,
            not_included=[NotIncludedOut.of(left, view.titles) for left in slate.not_included],
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
        description="For a title ESCO does not hold: the nearest occupations by full text."
    )
    requirements: list[str] = Field(description="ESCO's essential skills, the first few.")
    requirement_count: int | None = Field(description="null: no requirement list.")
    regulated: bool | None
    research_status: str

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
            research_status=target.research_status,
        )


class StepOut(ResponseModel):
    name: str
    chapter: str
    detail: str
    state: Literal["unresolved"]

    @classmethod
    def of(cls, step: Step) -> "StepOut":
        return cls(name=step.name, chapter=step.chapter, detail=step.detail, state="unresolved")


class SketchOut(ResponseModel):
    """The early requirement sketch: never a feasible or optimal route, never priced or
    dated. Every step stays unresolved until a later chapter resolves it."""

    label: str
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
            label=sketch.label,
            profile_version=sketch.profile_version,
            inputs=sketch.inputs,
            not_asked=sketch.not_asked,
            targets=[TargetSketchOut.of(t) for t in sketch.targets],
            steps=[StepOut.of(s) for s in sketch.steps],
        )
