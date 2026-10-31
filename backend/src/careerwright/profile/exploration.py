"""Career discovery use cases (spec section 4, REC-1 and DIV-1; S2.4): start a discovery,
read its slate, and choose an occupation as a target.

The chain is traceable end to end: the person's confirmed answers (a pinned profile
version) become the model's search queries, each citing the answers it rests on; every
query runs against the held ESCO release (a title of the person's own is joined by shared
essential skills; any other query searches the essential skills' labels, every word then
any word, bounded, and names the skill that reached each occupation; the release the
searches were chosen for is recorded, and a slate read against another says so), and
Careerwright adds the person's current role and own target titles;
the hits are pooled, de-duplicated and ranked into a slate by deterministic code
(`careerwright.profile.slate`). A model's title hypothesis is shown only if ESCO holds it as a
label; otherwise it is listed as unsupported, never as a suggestion (DIV1-04). Every
suggestion is an ESCO occupation with its URI as the source, the answers that found it and
its essential skills; its words are composed from those facts, never from model prose, and
carry no percentage (REC1-05).

The slate's controls (emphasis, excluded titles and kinds of work) are view parameters:
they never change the profile and never become a planning limit. A suggestion becomes a
target only when the person chooses it (REC1-07), through the one profile write path, with
an `occupation_choice` source naming the ESCO occupation and the discovery.

A discovery's slate may also have one written "Why this could suit you" (S2.7, ADR 0007
decision 12): a model run over its first view (balanced, no exclusions) whose every
quotation is checked against the pinned answers and ESCO's records
(`careerwright.profile.slate_explanation`). A changed view is never a new slate, so it never makes
a call. The written text is shown beside the words above, never instead of them, and
changes no suggestion.
"""

import re
import uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.ai_resilience import (
    AssessmentPacks,
    CheckedPack,
    FilterOutcome,
    ResilienceFilter,
    assessment,
    filter_outcome,
)
from careerwright.catalogue.pay import (
    FloorCounts,
    FloorVerdict,
    MappingReviewPack,
    ModelledPayUnavailable,
    floor_counts,
    modelled_floor_verdict,
)
from careerwright.catalogue.records import (
    OccupationDetail,
    OccupationFacts,
    SkillRef,
    TaxonomyRelease,
)
from careerwright.catalogue.reference import modelled_pay_of, region_codes
from careerwright.catalogue.taxonomy import held_release, search_essential_skills
from careerwright.config import RuntimeMode
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import run_store
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.records import Attempt, Run, RunKind
from careerwright.identity.runs import RunRequest, open_output, submit_run
from careerwright.identity.spend import SpendLimits, SpendState
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import discovery, explanation_store, slate_explanation, titles
from careerwright.profile import store as profile_store
from careerwright.profile.commands import (
    FieldUpdate,
    NewSource,
    ProfileView,
    commit_profile_version,
    current_profile,
)
from careerwright.profile.discovery import (
    DiscoveryInput,
    DiscoveryProposal,
    EvidenceItem,
    evidence_of,
)
from careerwright.profile.document import (
    FieldState,
    ProfileDocument,
    TextInput,
    TextListInput,
    TextValue,
)
from careerwright.profile.interview import ProfileField
from careerwright.profile.records import ExplanationRequest, SourceKind
from careerwright.profile.role_evidence import cities_of, salary_floor
from careerwright.profile.slate import (
    MIN_SHARED_SKILLS,
    SLATE_SIZE,
    Candidate,
    Direction,
    Hit,
    NotIncluded,
    Occupation,
    Pool,
    PoolQuery,
    Slate,
    SlateChannel,
    SlateControls,
    build_pool,
    choose_slate,
    skill_join_hits,
    unexpected_connection,
)
from careerwright.profile.slate_explanation import (
    RECORD_STEPS,
    SlateExplanation,
    accepted_quotation,
    build_input,
)
from careerwright.profile.store import stale_version
from careerwright.profile.titles import ResolvedTitle
from careerwright.vocabulary import WorkState

QUERY_HITS = 30  # occupations kept per search (the taxonomy search's bound is 50)
ROLE_JOIN = "j1"  # the query ID of the work joined to the person's role by shared skills
# An occupation that matches only some of a query's words counts for at most half as much
# as one that matches them all (product policy, subject to evaluation).
PARTIAL_MATCH_WEIGHT = 0.5
SKILLS_SHOWN = 3
DESCRIPTION_CHARS = 360
CHOSEN_FROM_SUGGESTIONS = "Chosen from Careerwright's suggestions"
CHOSEN_FROM_ESCO = "Chosen from the ESCO occupations"
CHOSEN_AS_ROLE = "Chosen from the ESCO occupations as your current or last role"
_SOURCE_WORDS = {
    ProfileField.CURRENT_ROLE: "Your current role",
    ProfileField.TARGET_TITLES: "A role you named",
    ProfileField.ENJOYED_TASKS: "What you enjoy",
    ProfileField.CONFIDENT_TASKS: "What you believe you can do",
    ProfileField.EVIDENCED_TASKS: "What you have done",
    ProfileField.WORK_STYLE: "How you like to work",
}


class SubmitDiscovery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_profile_version: int = Field(ge=0)


class ChooseTarget(BaseModel):
    """Make an ESCO occupation one of the targets: added, or in place of `replaces` (a
    target title it is the occupation for)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0)
    concept_id: uuid.UUID
    replaces: TextValue | None = None
    discovery_id: uuid.UUID | None = Field(
        default=None, description="The discovery that suggested it, if any."
    )


class SubmitExplanation(BaseModel):
    """Ask for the written explanation of a discovery's slate, made against these answers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_profile_version: int = Field(ge=0)
    retry_failed: bool = Field(
        default=False,
        description="The person's explicit Try again: start the note afresh if its run failed "
        "before any request reached a model (`can_retry`). Never sent automatically.",
    )


@dataclass(frozen=True)
class ExplanationView:
    request: ExplanationRequest
    run: Run
    written: SlateExplanation | None  # only once the run is complete
    # The run failed before any request reached a model, so the slate's one call is unused.
    can_retry: bool = False


_ENDED_WITHOUT_OUTPUT = frozenset({WorkState.FAILED, WorkState.PROVIDER_UNAVAILABLE})


def reached_no_model(run: Run, attempts: list[Attempt]) -> bool:
    """A failed run none of whose attempts took a reservation or recorded a request: it was
    refused inside the activity (budget, key, access, model) before any call. A live
    attempt holds its reservation before it calls, so one left unfinished or with an
    unknown charge counts as a call (a crash may follow one); a fixture attempt takes no
    reservation and makes no provider call, so it counts only by the requests it recorded,
    and one left unfinished counts as no call."""
    return run.status in _ENDED_WITHOUT_OUTPUT and all(
        attempt.spend_state == SpendState.NONE.value and not attempt.requests_sent
        for attempt in attempts
    )


@dataclass(frozen=True)
class DiscoveryView:
    run: Run
    proposal: DiscoveryProposal | None  # only once the run is complete
    explanation: ExplanationView | None = None  # its slate's one written explanation, if asked


@dataclass(frozen=True)
class Explanation:
    workday: str  # ESCO's description, shortened
    why: list[str]
    might_not: list[str]
    entry_gates: list[str]
    evidence_gaps: list[str]
    try_it: list[str]


@dataclass(frozen=True)
class Suggestion:
    candidate: Candidate
    facts: OccupationFacts
    explanation: Explanation


@dataclass(frozen=True)
class SlateView:
    """A slate computed from a discovery's stored searches and its pinned answers."""

    discovery: DiscoveryView
    release: TaxonomyRelease
    slate: Slate
    suggestions: list[Suggestion]
    queries: list[PoolQuery]
    unsupported_hypotheses: list[str]  # model titles ESCO does not hold
    unsearchable_queries: list[str]  # queries with no searchable word (none ran)
    titles: dict[uuid.UUID, str]  # every pooled occupation's title
    # The confirmed salary floor's effect on the pool (None when the person set none), and
    # the AI Resilience filter's (Task 7 slice B, ADR 0010).
    salary_floor: FloorCounts | None
    ai_filter: "AiFilterView"
    # The person's titles ESCO does not hold: nothing is joined to them (Sprint W).
    unmatched_titles: list[str] = field(default_factory=list)
    connection: "ConnectionView | None" = None


STILL_UNCERTAIN = (
    "These are the skills ESCO lists for both roles. They aren't compared with your own "
    "experience yet."
)


@dataclass(frozen=True)
class ConnectionView:
    """The unexpected connection (plan section 4; ADR 0007 decision 13): a fact about two
    roles, never about the person, with the essential skills both list one step away."""

    role_title: str  # the person's role as ESCO titles it
    candidate: Candidate
    destination: OccupationFacts
    shared: list[SkillRef]  # the essential skills ESCO lists for both, by label

    @property
    def sentence(self) -> str:
        first = with_article(self.role_title)
        return (
            f"{first[0].upper()}{first[1:]} and {with_article(self.destination.preferred_label)} "
            f"share {len(self.shared)} essential skills."
        )


@dataclass(frozen=True)
class HardFilterInput:
    """What the slate's hard filters read besides the answers: the reviewed UK SOC mappings
    (modelled pay), the workspace's assessment pack and the AI Resilience filter chosen."""

    reviews: MappingReviewPack
    pack: CheckedPack
    ai_filter: ResilienceFilter = field(default_factory=ResilienceFilter)


@dataclass(frozen=True)
class AiFilterView:
    """What the AI Resilience filter did to the pool: its basis is the lower end of a
    published range, and unscored occupations are counted, never read as 0 or 10."""

    chosen: ResilienceFilter
    pack_version: str
    pack_dated: date
    scored: int
    below_minimum: int
    unscored: int
    unscored_excluded: int
    # A scored occupation's range is a synthetic fixture's, never a real assessment (fix
    # round 1, review B M8).
    synthetic: bool = False


def _hard_filters(
    tx: Tx,
    pool: Pool,
    document: ProfileDocument,
    controls: SlateControls,
    hard: HardFilterInput,
    esco_uris: dict[uuid.UUID, str],
) -> tuple[dict[uuid.UUID, NotIncluded], FloorCounts | None, AiFilterView]:
    """The occupations the salary floor and the AI Resilience filter leave out, decided by
    deterministic code over the evidence, with each filter's counts. Only the distinct
    occupations the person did not exclude themselves are considered."""
    considered = [
        c.occupation.concept_id
        for c in pool
        if c.duplicate_of is None
        and c.occupation.concept_id not in controls.exclude_concepts
        and c.occupation.family_code not in controls.exclude_families
    ]
    left_out: dict[uuid.UUID, NotIncluded] = {}
    floor = salary_floor(document)
    counts = None
    if floor is not None:
        regions = region_codes(cities_of(document))
        modelled = modelled_pay_of(tx, considered, regions, hard.reviews)
        verdicts = {
            c: modelled_floor_verdict(
                floor, modelled.get(c, ModelledPayUnavailable.NO_REVIEWED_MAPPING), regions
            )
            for c in considered
        }
        counts = floor_counts(floor, verdicts.values())
        left_out = {
            c: NotIncluded.BELOW_SALARY_FLOOR
            for c, (verdict, _) in verdicts.items()
            if verdict is FloorVerdict.BELOW
        }
    assessments = {c: assessment(hard.pack, esco_uris[c]) for c in considered if c in esco_uris}
    outcomes = {c: filter_outcome(found, hard.ai_filter) for c, found in assessments.items()}
    for concept, outcome in outcomes.items():
        if concept in left_out:
            continue
        if outcome is FilterOutcome.BELOW_MINIMUM:
            left_out[concept] = NotIncluded.BELOW_AI_RESILIENCE_MINIMUM
        elif outcome is FilterOutcome.UNSCORED_EXCLUDED:
            left_out[concept] = NotIncluded.AI_RESILIENCE_UNSCORED_EXCLUDED
    found = list(outcomes.values())
    unscored = (FilterOutcome.UNSCORED_KEPT, FilterOutcome.UNSCORED_EXCLUDED)
    view = AiFilterView(
        chosen=hard.ai_filter,
        pack_version=hard.pack.pack.pack_version,
        pack_dated=hard.pack.pack.dated,
        scored=sum(o not in unscored for o in found),
        below_minimum=found.count(FilterOutcome.BELOW_MINIMUM),
        unscored=sum(o in unscored for o in found),
        unscored_excluded=found.count(FilterOutcome.UNSCORED_EXCLUDED),
        synthetic=any(a.synthetic and outcomes[c] not in unscored for c, a in assessments.items()),
    )
    return left_out, counts, view


def _proposal(tx: Tx, keyring: Keyring, run: Run) -> DiscoveryProposal | None:
    if run.kind is not RunKind.DISCOVERY or run.status is not WorkState.COMPLETE:
        return None
    plaintext = open_output(tx, keyring, run)
    return None if plaintext is None else DiscoveryProposal.model_validate_json(plaintext)


def _written(tx: Tx, keyring: Keyring, run: Run) -> SlateExplanation | None:
    if run.kind is not RunKind.SLATE_EXPLANATION or run.status is not WorkState.COMPLETE:
        return None
    plaintext = open_output(tx, keyring, run)
    return None if plaintext is None else SlateExplanation.model_validate_json(plaintext)


def _explanation(tx: Tx, keyring: Keyring, discovery_run: Run) -> ExplanationView | None:
    request = explanation_store.for_discovery(tx, discovery_run.workspace_id, discovery_run.run_id)
    if request is None:
        return None
    run = run_store.run(tx, request.explanation_id)
    if run is None:  # the run and its link are written together; never show half of one
        raise CareerwrightError(
            ErrorCode.INTERNAL_ERROR, "The explanation has no run.", stage=ErrorStage.PROFILE
        )
    attempts = run_store.attempts(tx, run.run_id)
    return ExplanationView(
        request, run, _written(tx, keyring, run), reached_no_model(run, attempts)
    )


def _view(tx: Tx, keyring: Keyring, run: Run) -> DiscoveryView:
    return DiscoveryView(run, _proposal(tx, keyring, run), _explanation(tx, keyring, run))


def visible_discovery(
    tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, discovery_id: uuid.UUID
) -> DiscoveryView:
    visible_workspace(tx, workspace_id)
    run = run_store.run(tx, discovery_id)
    if run is None or run.workspace_id != workspace_id or run.kind is not RunKind.DISCOVERY:
        raise CareerwrightError(ErrorCode.NOT_FOUND, "No such discovery.", stage=ErrorStage.PROFILE)
    return _view(tx, keyring, run)


def discoveries(
    tx: Tx,
    keyring: Keyring,
    workspace_id: uuid.UUID,
    *,
    before: tuple[datetime, uuid.UUID] | None,
    limit: int,
) -> list[DiscoveryView]:
    """Newest first."""
    visible_workspace(tx, workspace_id)
    runs = run_store.runs(tx, workspace_id, before=before, limit=limit, kind=RunKind.DISCOVERY)
    return [_view(tx, keyring, run) for run in runs]


def submit_discovery(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: SubmitDiscovery,
    *,
    models: ModelChoice,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
) -> DiscoveryView:
    """A discovery run on the current profile version, which it pins. Refused before any
    run exists when the profile is stale, when no answer describes work yet, or when the
    taxonomy it would search is missing."""
    visible_workspace(tx, workspace_id, lock=True)
    profile = current_profile(tx, workspace_id)
    if command.expected_profile_version != profile.version:
        raise stale_version(profile.version)
    evidence = evidence_of(profile.document)
    if not evidence:
        raise CareerwrightError(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "Tell Careerwright what you do now, what you enjoy or what you can do first.",
            stage=ErrorStage.PROFILE,
            details={"needs": [field.value for field in discovery.EVIDENCE_FIELDS]},
        )
    release = held_release(tx)
    context = DiscoveryInput(
        profile_version=profile.version, evidence=evidence, release=release.dataset_id
    )
    run = submit_run(
        tx,
        actor,
        workspace_id,
        RunRequest(
            RunKind.DISCOVERY,
            discovery.worst_case_nano_usd,
            profile_version=profile.version,
            input=context.model_dump_json().encode(),
        ),
        models=models,
        keyring=keyring,
        runtime_mode=runtime_mode,
        defaults=defaults,
        now=now,
    )
    return DiscoveryView(run, None)


def _search_hits(tx: Tx, text: str) -> tuple[Hit, ...] | None:
    """The occupations a search reaches through their essential skills (ADR 0007 decision
    13): reached with every word, they score their skill's rank over the best such rank;
    with only some words, at most `PARTIAL_MATCH_WEIGHT`. Each hit names the essential skill
    whose words it matched. Never an occupation's titles, hidden labels, ISCO group or
    description: work is never found by a word in a title. None: the query has no
    searchable word, so nothing ran (never an empty result)."""
    try:
        every = search_essential_skills(tx, text, QUERY_HITS, any_word=False)
        some = search_essential_skills(tx, text, QUERY_HITS, any_word=True)
    except CareerwrightError as error:
        if error.details.get("reason") == "no_search_terms":
            return None
        raise
    hits: dict[uuid.UUID, Hit] = {}
    for found, weight in ((every, 1.0), (some, PARTIAL_MATCH_WEIGHT)):
        top = max((reach.text_rank for reach in found.reached), default=0.0)
        for reach in found.reached:
            score = weight * reach.text_rank / top if top > 0 else 0.0
            held = hits.get(reach.concept_id)
            if held is None or score > held.score:
                hits[reach.concept_id] = Hit(
                    reach.concept_id, score, label_match=False, skill=reach.skill_label
                )
    return tuple(hits.values())


def _label_hits(tx: Tx, title: str) -> tuple[Hit, ...]:
    """Occupations that hold this title as a label (`careerwright.concept_key`), all scoring 1."""
    matches = taxonomy_store.concept_key_matches(tx, title)
    return tuple(Hit(m.concept_id, 1.0, label_match=True) for m in matches)


def _named_hits(occupations: tuple[uuid.UUID, ...]) -> tuple[Hit, ...]:
    return tuple(Hit(concept, 1.0, label_match=True) for concept in occupations)


def _joined(
    tx: Tx,
    query_id: str,
    title: ResolvedTitle,
    channel: SlateChannel,
    based_on: tuple[EvidenceItem, ...],
) -> PoolQuery:
    """The work joined to a title's occupations by shared essential skills: never a search
    of the title's words."""
    essential, neighbours = taxonomy_store.skill_neighbours(
        tx, title.occupations, MIN_SHARED_SKILLS
    )
    return PoolQuery(
        query_id, title.text, channel, based_on, skill_join_hits(essential, neighbours)
    )


def _provided(document: ProfileDocument, field: ProfileField) -> list[str]:
    value = getattr(document, field.value)
    if value.state is not FieldState.PROVIDED or value.value is None:
        return []
    return [str(item) for item in (value.value if isinstance(value.value, list) else [value.value])]


def _pinned_document(tx: Tx, run: Run) -> ProfileDocument:
    pinned = profile_store.profile_version(tx, run.workspace_id, run.profile_version or 0)
    if pinned is None:  # a discovery needs answers, so its version was saved
        raise CareerwrightError(
            ErrorCode.INTERNAL_ERROR,
            "The discovery's profile is missing.",
            stage=ErrorStage.PROFILE,
        )
    return pinned.document


def _description(text: str) -> str:
    if len(text) <= DESCRIPTION_CHARS:
        return text
    cut = text[:DESCRIPTION_CHARS].rsplit(" ", 1)[0]
    return f"{cut}…"


# Spelled with a vowel but said with a consonant ("a university lecturer"), or the reverse:
# a silent h ("an hour") and capitals read as letters ("an ICT help desk agent").
_CONSONANT_SOUND = re.compile(r"^(?:uni|use|usu|uti|eu|one\b)", re.IGNORECASE)
_VOWEL_SOUND = re.compile(r"^(?:hour|honest|honou?r|heir|[AEFHILMNORSX][A-Z])")


def with_article(title: str) -> str:
    """The title after "a" or "an", as it is said."""
    said_as_you = _CONSONANT_SOUND.match(title) or re.match(r"U[A-Z]", title)  # "a UX designer"
    vowel = title[:1].casefold() in "aeiou" and not said_as_you
    return f"{'an' if vowel or _VOWEL_SOUND.match(title) else 'a'} {title}"


def explain(candidate: Candidate, facts: OccupationFacts, familiarity_known: bool) -> Explanation:
    """The suggestion's words, from the answers that found it and ESCO's record only."""
    title = facts.preferred_label
    why: list[str] = []
    seen: set[tuple[str, str]] = set()
    for match in candidate.matches:
        for item in match.query.based_on:
            key = (item.field.value, item.text)
            if key in seen or len(why) == 3:
                continue
            seen.add(key)
            if match.shared_skills is not None:
                why.append(
                    f"{_SOURCE_WORDS[item.field]}: “{item.text}”. ESCO lists "
                    f"{match.shared_skills} of the same essential skills for both, so Careerwright "
                    "joined them by those skills."
                )
            elif match.skill is not None:
                why.append(
                    f"{_SOURCE_WORDS[item.field]}: “{item.text}”. Careerwright searched for "
                    f"“{match.query.text}”, and ESCO lists “{match.skill}” as an essential "
                    "skill for this work."
                )
            elif match.query.channel is SlateChannel.HYPOTHESIS:
                why.append(
                    f"{_SOURCE_WORDS[item.field]}: “{item.text}”. Careerwright thought of this "
                    "title "
                    "from it, and ESCO lists it."
                )
            else:  # the person's own title, resolved to this occupation
                why.append(
                    f"{_SOURCE_WORDS[item.field]}: “{item.text}”. ESCO lists it as this occupation."
                )
    might_not: list[str] = []
    if facts.essential_skills:
        might_not.append(
            f"ESCO lists {facts.essential_skill_count} essential skills, not yet compared "
            f"with your experience, including: {', '.join(facts.essential_skills)}."
        )
    if facts.regulated:
        might_not.append(
            "ESCO marks this as a regulated profession in at least one European country. "
            "Whether England requires registration isn't checked yet."
        )
    if familiarity_known and candidate.direction is Direction.LESS_FAMILIAR:
        might_not.append(
            "It's a different kind of work from what you've told Careerwright about, so it may "
            "need new experience."
        )
    gates = (
        ["Registration may be required. Not checked yet."]
        if facts.regulated
        else ["Entry requirements aren't researched yet."]
    )
    try_it = [
        f"Talk to someone who works as {with_article(title)} about a typical week (an "
        "informational interview)."
    ]
    if facts.essential_skills:
        try_it.append(f"Try one of its tasks on a small scale: {facts.essential_skills[0]}.")
    return Explanation(
        workday=_description(facts.description),
        why=why,
        might_not=might_not,
        entry_gates=gates,
        evidence_gaps=[
            "Pay, demand and listings in your work areas aren't researched yet. Finding no "
            "listings later would be a demand signal, not proof this work doesn't exist."
        ],
        try_it=try_it,
    )


def hard_filters(
    tx: Tx,
    workspace_id: uuid.UUID,
    reviews: MappingReviewPack,
    packs: AssessmentPacks,
    ai_filter: ResilienceFilter | None = None,
) -> HardFilterInput:
    """The workspace's hard-filter inputs: the synthetic fixture pack applies only in the
    fixture workspace, the product pack everywhere else."""
    workspace = visible_workspace(tx, workspace_id)
    pack = packs.for_workspace(fixture_workspace=workspace.fixture_key is not None)
    return HardFilterInput(reviews, pack, ai_filter or ResilienceFilter())


def discovery_slate(
    tx: Tx,
    keyring: Keyring,
    workspace_id: uuid.UUID,
    discovery_id: uuid.UUID,
    controls: SlateControls,
    hard: HardFilterInput,
) -> SlateView:
    view = visible_discovery(tx, keyring, workspace_id, discovery_id)
    proposal = view.proposal
    if proposal is None:
        raise CareerwrightError(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "This discovery has no validated queries yet.",
            stage=ErrorStage.PROFILE,
            details={
                "run_status": view.run.status.value,
                "failure_class": view.run.failure_class or "",
            },
        )
    return compute_slate(tx, view, proposal, _pinned_document(tx, view.run), controls, hard)


def release_note(searched: str | None, held: str) -> str | None:
    """What to say when the searches were chosen for another ESCO release than the one the
    slate now uses (the slate is recomputed on each read)."""
    if searched is None or searched == held:
        return None
    return (
        f"These searches were chosen when ESCO {searched} was held; this slate uses {held}, "
        "so some occupations may have changed."
    )


def compute_slate(
    tx: Tx,
    view: DiscoveryView,
    proposal: DiscoveryProposal,
    document: ProfileDocument,
    controls: SlateControls,
    hard: HardFilterInput,
) -> SlateView:
    """The slate for these searches and answers over the held taxonomy, with the person's
    confirmed salary floor and the chosen AI Resilience filter applied as hard filters, each
    counted. Pay is read only through a reviewed UK SOC mapping, so without one the
    taxonomy tables are all it reads, and the offline evaluation runs it unchanged against
    the full release."""
    release = held_release(tx)
    role = titles.current_role(tx, view.run.workspace_id, document)
    named = titles.targets(tx, view.run.workspace_id, document)
    mine = ([role] if role else []) + named
    # A search is one of the person's titles when it is that title as a concept
    # (`careerwright.concept_key`): "Data analysts" is their "data analyst".
    keys = taxonomy_store.concept_keys(
        tx, [t.text for t in mine] + [q.text for q in proposal.queries]
    )
    own = {keys[t.text]: t for t in mine if keys[t.text]}
    queries: list[PoolQuery] = []
    unsearchable: list[str] = []
    role_joins: set[str] = set()
    for query in proposal.queries:
        title = own.get(keys[query.text])
        if title is not None:  # a title of the person's own: joined by skills, never searched
            if title.occupations:
                channel = SlateChannel(query.channel.value)
                queries.append(_joined(tx, query.query_id, title, channel, tuple(query.based_on)))
                if title is role:
                    role_joins.add(query.query_id)
            continue
        hits = _search_hits(tx, query.text)
        if hits is None:
            unsearchable.append(query.text)
            continue
        queries.append(
            PoolQuery(
                query.query_id,
                query.text,
                SlateChannel(query.channel.value),
                tuple(query.based_on),
                hits,
            )
        )
    familiar: set[uuid.UUID] = set()
    if role is not None and role.occupations:
        item = EvidenceItem(field=ProfileField.CURRENT_ROLE, text=role.text)
        queries.append(
            PoolQuery("r1", role.text, SlateChannel.CURRENT, (item,), _named_hits(role.occupations))
        )
        queries.append(_joined(tx, ROLE_JOIN, role, SlateChannel.SHARED_SKILLS, (item,)))
        role_joins.add(ROLE_JOIN)
        familiar.update(role.occupations)
    for index, target in enumerate(named, start=1):
        item = EvidenceItem(field=ProfileField.TARGET_TITLES, text=target.text)
        hits = _named_hits(target.occupations)
        familiar.update(target.occupations)
        queries.append(
            PoolQuery(f"t{index}", target.text, SlateChannel.USER_PROPOSED, (item,), hits)
        )
    unsupported: list[str] = []
    for index, hypothesis in enumerate(proposal.hypotheses, start=1):
        hits = _label_hits(tx, hypothesis.title)
        if not hits:
            unsupported.append(hypothesis.title)
            continue
        queries.append(
            PoolQuery(
                f"h{index}",
                hypothesis.title,
                SlateChannel.HYPOTHESIS,
                tuple(hypothesis.based_on),
                hits,
            )
        )
    found = {hit.concept_id for query in queries for hit in query.hits}
    facts = taxonomy_store.occupation_facts(tx, found, skills_shown=SKILLS_SHOWN)
    occupations = _occupations(facts)
    familiar_families = frozenset(facts[c].family.code for c in familiar if c in facts)
    pool = build_pool(queries, occupations, familiar_families)
    esco_uris = {concept_id: fact.esco_uri for concept_id, fact in facts.items()}
    left_out, floor, ai_filter = _hard_filters(tx, pool, document, controls, hard, esco_uris)
    slate = choose_slate(pool, controls, left_out)
    changed = release_note(proposal.release, release.dataset_id)
    if changed is not None:
        slate = replace(slate, notes=[changed, *slate.notes])
    unmatched = [t.text for t in ([role] if role else []) + named if not t.occupations]
    if unmatched and len(slate.suggestions) < SLATE_SIZE:
        slate = replace(slate, fewer_reasons=[*slate.fewer_reasons, *map(_unmatched, unmatched)])
    return SlateView(
        discovery=view,
        release=release,
        slate=slate,
        suggestions=_suggestions(slate, facts, bool(familiar_families)),
        queries=queries,
        unsupported_hypotheses=unsupported,
        unsearchable_queries=unsearchable,
        titles={concept_id: occupation.title for concept_id, occupation in occupations.items()},
        salary_floor=floor,
        ai_filter=ai_filter,
        unmatched_titles=unmatched,
        connection=_connection(tx, slate, role, named, facts, frozenset(role_joins)),
    )


def _occupations(facts: dict[uuid.UUID, OccupationFacts]) -> dict[uuid.UUID, Occupation]:
    return {
        concept_id: Occupation(
            concept_id=concept_id,
            title=fact.preferred_label,
            family_code=fact.family.code,
            family_label=fact.family.label,
            sector_code=fact.sector.code,
            preferred_key=fact.preferred_key,
            label_keys=fact.label_keys,
        )
        for concept_id, fact in facts.items()
    }


def _suggestions(
    slate: Slate, facts: dict[uuid.UUID, OccupationFacts], familiarity_known: bool
) -> list[Suggestion]:
    return [
        Suggestion(
            candidate,
            facts[candidate.occupation.concept_id],
            explain(candidate, facts[candidate.occupation.concept_id], familiarity_known),
        )
        for candidate in slate.suggestions
    ]


def _unmatched(title: str) -> str:
    return (
        f"“{title}” isn't a title ESCO lists, so Careerwright can't join other work to it by "
        "shared skills. Choose the ESCO occupation closest to it."
    )


def _connection(
    tx: Tx,
    slate: Slate,
    role: ResolvedTitle | None,
    named: list[ResolvedTitle],
    facts: dict[uuid.UUID, OccupationFacts],
    role_joins: frozenset[str],
) -> ConnectionView | None:
    """The slate's unexpected connection to the person's role, with the skills the two
    share (ESCO) one step away. None unless the role names exactly one ESCO occupation: a
    role several occupations hold as a title is no one occupation to state a fact about."""
    if role is None or len(role.occupations) != 1:
        return None
    own = facts[role.occupations[0]]  # the role's own occupation is always pooled
    names = frozenset(c for t in [role, *named] for c in t.occupations)
    found = unexpected_connection(slate, role_joins, frozenset({own.family.code}), names)
    if found is None:
        return None
    destination = found.candidate.occupation.concept_id
    shared = taxonomy_store.shared_essential_skills(tx, role.occupations, destination)
    return ConnectionView(own.preferred_label, found.candidate, facts[destination], shared)


def submit_explanation(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    discovery_id: uuid.UUID,
    command: SubmitExplanation,
    *,
    models: ModelChoice,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
    hard: HardFilterInput,
) -> tuple[ExplanationView, bool]:
    """The slate's one written explanation, and whether this request started it. A slate is
    a discovery's first view (balanced, no exclusions, the salary floor applied and the AI
    Resilience filter at Any): asking again, from any view, returns
    the explanation already asked for, in whatever state, so a slate never has a second call.

    The one exception is the person's explicit Try again (`retry_failed`) on a run that
    failed before any request reached a model (`reached_no_model`): that call was never
    made, so a new run replaces the failed link, in this locked transaction. Try again on a
    run that did send a request is refused (`SLATE_ALREADY_EXPLAINED`): Suggest again makes a
    new slate, with a note of its own.

    Refused before any run exists when the discovery has no validated searches, when the
    answers it pinned are not the current ones (it would quote answers since changed), when
    no pinned answer is one the note can quote (`accepted_quotation`, as the demo explainer
    reads it), or when its slate is empty."""
    visible_workspace(tx, workspace_id, lock=True)
    view = visible_discovery(tx, keyring, workspace_id, discovery_id)
    existing = view.explanation
    if existing is not None:
        if not (command.retry_failed and existing.run.status in _ENDED_WITHOUT_OUTPUT):
            return existing, False
        if not existing.can_retry:
            raise CareerwrightError(
                ErrorCode.SLATE_ALREADY_EXPLAINED,
                "This set of suggestions has had its one written note. Suggest again for a new "
                "set, with a note of its own.",
                stage=ErrorStage.PROFILE,
                details={"explanation_id": str(existing.request.explanation_id)},
            )
    profile = current_profile(tx, workspace_id)
    if command.expected_profile_version != profile.version:
        raise stale_version(profile.version)
    proposal = view.proposal
    if proposal is None:
        raise CareerwrightError(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "This discovery has no validated queries yet.",
            stage=ErrorStage.PROFILE,
            details={
                "run_status": view.run.status.value,
                "failure_class": view.run.failure_class or "",
            },
        )
    pinned = view.run.profile_version or 0
    if pinned != profile.version:
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "Your answers changed after these suggestions were made. Suggest again first.",
            stage=ErrorStage.PROFILE,
            details={"current_version": profile.version, "discovery_version": pinned},
        )
    document = _pinned_document(tx, view.run)
    answers = evidence_of(document)
    if not any(accepted_quotation(item.text, item.text) for item in answers):
        raise CareerwrightError(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "None of your answers has a word the note could quote.",
            stage=ErrorStage.PROFILE,
            details={"reason": "no_quotable_answer"},
        )
    shown = compute_slate(
        tx, view, proposal, document, SlateControls(), replace(hard, ai_filter=ResilienceFilter())
    )
    if not shown.suggestions:
        raise CareerwrightError(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "This slate has no suggestions to explain.",
            stage=ErrorStage.PROFILE,
            details={"reason": "no_suggestions"},
        )
    concepts = [s.candidate.occupation.concept_id for s in shown.suggestions]
    records = taxonomy_store.occupation_facts(tx, concepts, skills_shown=RECORD_STEPS[0][1])
    context = build_input(
        discovery_id=discovery_id,
        profile_version=pinned,
        release=shown.release.dataset_id,
        answers=answers,
        occupations=[records[concept] for concept in concepts],
    )
    run = submit_run(
        tx,
        actor,
        workspace_id,
        RunRequest(
            RunKind.SLATE_EXPLANATION,
            slate_explanation.worst_case_nano_usd,
            profile_version=pinned,
            input=context.model_dump_json().encode(),
        ),
        models=models,
        keyring=keyring,
        runtime_mode=runtime_mode,
        defaults=defaults,
        now=now,
    )
    request = ExplanationRequest(
        explanation_id=run.run_id,
        workspace_id=workspace_id,
        discovery_id=discovery_id,
        created_by=actor.actor_id,
        created_at=now,
    )
    if existing is not None:  # a Try again of a run that reached no model
        explanation_store.replace(tx, existing.request.explanation_id, now)
    explanation_store.insert(tx, request)
    return ExplanationView(request, run, None), True


def choose_target(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: ChooseTarget, now: datetime
) -> tuple[ProfileView, bool]:
    """The person's explicit choice is the confirmation a target needs (PROF-04). Returns
    the profile and whether it changed (the occupation may already be a target)."""
    visible_workspace(tx, workspace_id, lock=True)
    held_release(tx)
    occupation = taxonomy_store.occupation(tx, command.concept_id)
    if occupation is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such ESCO occupation.", stage=ErrorStage.PROFILE
        )
    if command.discovery_id is not None:
        run = run_store.run(tx, command.discovery_id)
        if run is None or run.workspace_id != workspace_id or run.kind is not RunKind.DISCOVERY:
            raise CareerwrightError(
                ErrorCode.NOT_FOUND, "No such discovery.", stage=ErrorStage.PROFILE
            )
    profile = current_profile(tx, workspace_id)
    if command.expected_version != profile.version:
        raise stale_version(profile.version)
    targets = _provided(profile.document, ProfileField.TARGET_TITLES)
    label = occupation.preferred_label
    folded = [target.casefold() for target in targets]
    if command.replaces is not None:
        if command.replaces.casefold() not in folded:
            raise CareerwrightError(
                ErrorCode.VALIDATION_FAILED,
                "That is not one of your target roles.",
                stage=ErrorStage.PROFILE,
                details={"field": "replaces", "reason": "not_a_target"},
            )
        chosen = [
            label if target.casefold() == command.replaces.casefold() else target
            for target in targets
        ]
        chosen = list(dict.fromkeys(chosen))  # the occupation may already be a target too
    elif label.casefold() in folded:
        return profile, False
    else:
        chosen = [*targets, label]
    source = NewSource(
        source_ref_id=uuid.uuid4(),
        kind=SourceKind.OCCUPATION_CHOICE,
        label=CHOSEN_FROM_SUGGESTIONS if command.discovery_id else CHOSEN_FROM_ESCO,
        observed_at=now,
        recorded_by=actor.actor_id,
        run_id=command.discovery_id,
        locator=occupation.esco_uri,
    )
    update = FieldUpdate(TextListInput(state=FieldState.PROVIDED, value=chosen), source)
    view, changed = commit_profile_version(
        tx, actor, workspace_id, command.expected_version, {"target_titles": update}
    )
    return view, bool(changed)


class ChooseRole(BaseModel):
    """The first answer: the ESCO occupation the person does now, or did last."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0)
    concept_id: uuid.UUID = Field(description="An occupation from `GET /v1/taxonomy/titles`.")
    label: str | None = Field(
        default=None,
        description="The title the person picked (the type-ahead's `matched_label`): ESCO's "
        "title for the occupation or one of its other titles. It stays their words; the role "
        "is resolved by the occupation's ESCO URI. Omitted: ESCO's title.",
    )


def choose_role(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: ChooseRole, now: datetime
) -> tuple[ProfileView, bool]:
    """Answer "What do you do now, or what did you do last?" with an ESCO occupation, through
    the one profile write path: the current role becomes the title the person picked (ESCO's
    or another it lists for that occupation), citing an `occupation_choice` source with its
    ESCO URI, which is what the role resolves by. Choosing the occupation and title the role
    already names changes nothing. Returns the profile and whether it changed."""
    visible_workspace(tx, workspace_id, lock=True)
    held_release(tx)
    occupation = taxonomy_store.occupation(tx, command.concept_id)
    if occupation is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such ESCO occupation.", stage=ErrorStage.PROFILE
        )
    label = command.label or occupation.preferred_label
    if label not in (occupation.preferred_label, *occupation.alternative_labels):
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Choose one of the titles ESCO lists for this occupation.",
            stage=ErrorStage.PROFILE,
            details={"field": "label", "reason": "not_its_title"},
        )
    profile = current_profile(tx, workspace_id)
    if command.expected_version != profile.version:
        raise stale_version(profile.version)
    role = titles.current_role(tx, workspace_id, profile.document)
    if role == ResolvedTitle(label, ProfileField.CURRENT_ROLE, (occupation.concept_id,), True):
        return profile, False  # already the role, chosen from ESCO
    source = NewSource(
        source_ref_id=uuid.uuid4(),
        kind=SourceKind.OCCUPATION_CHOICE,
        label=CHOSEN_AS_ROLE,
        observed_at=now,
        recorded_by=actor.actor_id,
        locator=occupation.esco_uri,
    )
    update = FieldUpdate(TextInput(state=FieldState.PROVIDED, value=label), source)
    view, changed = commit_profile_version(
        tx,
        actor,
        workspace_id,
        command.expected_version,
        {"current_role": update},
        recite=frozenset({"current_role"}),
    )
    return view, bool(changed)


class RoleState(StrEnum):
    """What the person's current or last role names in ESCO."""

    NOT_ANSWERED = "not_answered"
    ESCO = "esco"  # one ESCO occupation
    AMBIGUOUS = "ambiguous"  # several hold it as a label: the person chooses, none is guessed
    NOT_IN_ESCO = "not_in_esco"  # no ESCO label: nothing is joined to it


@dataclass(frozen=True)
class FirstSlate:
    """The world's answer to the first question, computed by deterministic code over the
    held ESCO release with no model call: the person's role, the essential skills it usually
    needs, and the first destinations, joined to it by shared essential skills, with the
    unexpected connection among them. Recomputed on each read."""

    profile_version: int
    release: TaxonomyRelease
    role: ResolvedTitle | None
    state: RoleState
    occupation: OccupationDetail | None = None  # the role's occupation, when it names one
    choices: list[OccupationFacts] = field(default_factory=list)  # an ambiguous role's
    slate: Slate | None = None  # None until the role names one occupation
    suggestions: list[Suggestion] = field(default_factory=list)
    connection: ConnectionView | None = None
    salary_floor: FloorCounts | None = None


def first_slate(tx: Tx, workspace_id: uuid.UUID, hard: HardFilterInput) -> FirstSlate:
    """The first scatter of destinations follows from the first answer alone: the role's
    occupation joined to others by shared essential skills (the role itself is the origin,
    never a destination), chosen by the slate's rules and its hard filters (the confirmed
    salary floor), with the unexpected connection singled out."""
    release = held_release(tx)
    profile = current_profile(tx, workspace_id)
    role = titles.current_role(tx, workspace_id, profile.document)
    nothing = FirstSlate(profile.version, release, role, RoleState.NOT_ANSWERED)
    if role is None:
        return nothing
    if len(role.occupations) != 1:
        choices = taxonomy_store.occupation_facts(tx, role.occupations, skills_shown=SKILLS_SHOWN)
        state = RoleState.AMBIGUOUS if role.occupations else RoleState.NOT_IN_ESCO
        return replace(
            nothing, state=state, choices=sorted(choices.values(), key=lambda f: f.preferred_label)
        )
    [concept] = role.occupations
    item = EvidenceItem(field=ProfileField.CURRENT_ROLE, text=role.text)
    join = _joined(tx, ROLE_JOIN, role, SlateChannel.SHARED_SKILLS, (item,))
    found = {hit.concept_id for hit in join.hits} | {concept}
    facts = taxonomy_store.occupation_facts(tx, found, skills_shown=SKILLS_SHOWN)
    familiar = frozenset({facts[concept].family.code})
    pool = build_pool([join], _occupations(facts), familiar)
    esco_uris = {concept_id: fact.esco_uri for concept_id, fact in facts.items()}
    controls = SlateControls()
    left_out, floor, _ = _hard_filters(tx, pool, profile.document, controls, hard, esco_uris)
    slate = choose_slate(pool, controls, left_out)
    if not join.hits:
        slate = replace(
            slate,
            fewer_reasons=[
                f"No other occupation in ESCO shares {MIN_SHARED_SKILLS} or more essential skills "
                f"with {with_article(facts[concept].preferred_label)}."
            ],
        )
    named = titles.targets(tx, workspace_id, profile.document)
    return FirstSlate(
        profile_version=profile.version,
        release=release,
        role=role,
        state=RoleState.ESCO,
        occupation=taxonomy_store.occupation(tx, concept),
        choices=[],
        slate=slate,
        suggestions=_suggestions(slate, facts, familiarity_known=True),
        connection=_connection(tx, slate, role, named, facts, frozenset({ROLE_JOIN})),
        salary_floor=floor,
    )
