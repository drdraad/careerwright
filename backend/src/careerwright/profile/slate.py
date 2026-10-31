"""The discovery pool and the slate of suggestions (spec section 4, DIV-1; S2.4). Pure.

**Pool.** Every query's taxonomy hits are pooled by concept: an alias is the same concept,
and an occupation whose preferred label is a label of another (as a concept key) is
near-identical to it, so they count once (DIV1-05); the most relevant represents them and
the others say which they duplicate. Folding is never transitive. The working pool is
bounded (`POOL_LIMIT`, the upper end of the soft 60-120 target) and filled round-robin
across ISCO families before relevance cuts it; what it and a join's own cut leave out is
counted. A candidate's relevance rests only on how well the person's own answers retrieved
it: its best normalised rank in any query, plus a little for each further query that found
it. Equal relevance goes to work a more specific search found (it reached fewer
occupations), then to the larger share of its essential skills the answers reach (its own,
never a folded role's), and the title is only the last tie-break: no cut is decided by the
alphabet. No pay, popularity, prestige or AI-resilience figure enters (DIV1-07), and no
percentage is ever produced (REC1-05).

**Titles are joined by skills, never by their words** (plan section 4, Sprint W; ADR 0007
decision 13). The person's role or a title they named is resolved to its ESCO occupation, and
other occupations join it only by the essential skills the two share (`skill_join_hits`):
at least `MIN_SHARED_SKILLS`, ranked by their share of both roles' essential skills. Every
other search reaches an occupation only through one of its essential skills whose label
holds every word of the search, which its hit names (`Hit.skill`); a search too general to
find work on its own (`too_general`) only adds weight to work another search found.

**Direction** is relative to the person (DIV1-12): close to what they do now (its ISCO
family is one of their current role's or targets', or their role or a target found it),
building on skills they could carry over (a transferable or cross-industry query, or a skill
join, found it), or something different (anything else).

**The unexpected connection** (`unexpected_connection`) singles out one suggestion joined to
the person's role by shared essential skills, outside their own kind of work and never a
title they named: the one sharing the most. It is a fact about two roles, never about the
person.

**Slate.** A constrained greedy reranker, with no claim of optimality: each step takes the
eligible candidate with the highest relevance plus bonuses for a family, an ISCO major group
and a direction not yet shown (aiming at two of each direction), less a penalty per
candidate already shown from its family; at most `FAMILY_LIMIT` per family, relaxed visibly
when the person asks for depth. A relevance floor applies: a slot is never filled with a
weak match, so a thin pool returns fewer suggestions with the reason (DIV1-06). The person's
own exclusions come first and are counted (DIV1-07); excluding one title never excludes
its family (REC1-08). The weights are product policy subject to evaluation, not estimates of
fit (spec section 4).
"""

import uuid
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum

from careerwright.catalogue.records import SkillNeighbour
from careerwright.profile.discovery import EvidenceItem, QueryChannel
from careerwright.profile.slate_facts import (
    CastingWider,
    ExclusionsRemoved,
    FewerReason,
    FewMatched,
    KindsOfWorkShown,
    MoreDepth,
    NothingFound,
    SlateNote,
)

SLATE_SIZE = 6
FAMILY_LIMIT = 2
DEEPER_FAMILY_LIMIT = 4
POOL_LIMIT = 120
POOL_TARGET = 60  # the soft lower end of the working pool (spec section 4)
RELEVANCE_FLOOR = 0.35  # best normalised rank in any query
BROAD_RELEVANCE_FLOOR = 0.2
FURTHER_QUERY_BONUS = 0.2
MAX_RELEVANCE = 2.0
# Smaller than relevance differences between a strong and a weak match, so variety never
# outweighs a much better fit (no filler to meet a diversity quota, plan section 9).
NEW_FAMILY_BONUS = 0.3
NEW_SECTOR_BONUS = 0.15
DIRECTION_BONUS = 0.4
SAME_FAMILY_PENALTY = 0.3
# A skill join (product policy, provisional R6): two occupations join only when ESCO lists at
# least this many of the same essential skills for both (ESCO v1.2.1 lists 3 to 99 per
# occupation, 22 on average), and a join keeps its best `JOIN_HITS` like a search.
MIN_SHARED_SKILLS = 3
JOIN_HITS = 30
# A search too general to find work on its own (product policy, provisional for the product
# owner at session W2; Task W2B fix round 3): it reaches more than this many occupations
# ("writing reports" reaches 217)...
TOO_GENERAL_OCCUPATIONS = 50
# ...or more than this many different essential skills, none named by exactly its words
# ("training staff": 10, from "train staff in quality procedures" to "train staff to reduce
# food waste"). It may still add weight to work another search found.
TOO_GENERAL_SKILLS = 5


class SlateChannel(StrEnum):
    """How a candidate was found: the model's channels plus Careerwright's own."""

    CURRENT = "current"  # the person's current role, searched by Careerwright
    USER_PROPOSED = "user_proposed"  # a title the person gave as a target
    TASKS = QueryChannel.TASKS.value
    ENVIRONMENT = QueryChannel.ENVIRONMENT.value
    TRANSFERABLE = QueryChannel.TRANSFERABLE.value
    CROSS_INDUSTRY = QueryChannel.CROSS_INDUSTRY.value
    LESS_FAMILIAR = QueryChannel.LESS_FAMILIAR.value
    HYPOTHESIS = "hypothesis"  # a model title that ESCO holds
    # Joined to the person's role by shared essential skills, by Careerwright.
    SHARED_SKILLS = "shared_skills"


# How much a hit counts by the channel that found it. Where someone likes to work is weaker
# evidence than what they do, enjoy or name (spec section 4: one source of hypotheses among
# several); it is never a filter (REC1-03), and a search resting only on one-word answers
# about how they like to work is not run at all (ADR 0007 decision 13).
CHANNEL_WEIGHT: Mapping[SlateChannel, float] = {
    SlateChannel.CURRENT: 1.0,
    SlateChannel.USER_PROPOSED: 1.0,
    SlateChannel.SHARED_SKILLS: 1.0,
    SlateChannel.TASKS: 1.0,
    SlateChannel.TRANSFERABLE: 1.0,
    SlateChannel.CROSS_INDUSTRY: 0.9,
    SlateChannel.LESS_FAMILIAR: 0.9,
    SlateChannel.HYPOTHESIS: 0.9,
    SlateChannel.ENVIRONMENT: 0.6,
}


class Direction(StrEnum):
    CLOSE = "close_to_current"
    TRANSFERABLE = "transferable"
    LESS_FAMILIAR = "less_familiar"


class Emphasis(StrEnum):
    """The slate controls (REC1-08)."""

    BALANCED = "balanced"
    PRACTICAL = "practical"  # more close to what they do now
    UNFAMILIAR = "unfamiliar"  # more that is different
    BROAD = "broad"  # a lower relevance bar and one per family
    DEEPER = "deeper"  # more from the same kind of work


class NotIncluded(StrEnum):
    """Why a pooled occupation is not on the slate ("show why this wasn't included")."""

    DUPLICATE = "duplicate"
    EXCLUDED_OCCUPATION = "excluded_occupation"
    EXCLUDED_FAMILY = "excluded_family"
    # Hard filters (Task 7 slice B): the person's confirmed salary floor, and the AI
    # Resilience filter they chose; deterministic code decides what is below each.
    BELOW_SALARY_FLOOR = "below_salary_floor"
    BELOW_AI_RESILIENCE_MINIMUM = "below_ai_resilience_minimum"
    AI_RESILIENCE_UNSCORED_EXCLUDED = "ai_resilience_unscored_excluded"
    BELOW_RELEVANCE_FLOOR = "below_relevance_floor"
    FAMILY_LIMIT = "family_limit"
    LESS_RELEVANT = "less_relevant"


@dataclass(frozen=True)
class Hit:
    concept_id: uuid.UUID
    score: float  # rank normalised within its query, 0-1; an exact label match is 1
    label_match: bool
    # A skill join's hit: how many essential skills it shares with the title joined.
    shared_skills: int | None = None
    # A search's hit: the essential skill (its ESCO label) whose words the search matched.
    skill: str | None = None
    # The occupation's essential skills this hit reached: those a search matched, or those a
    # join shares (none for a title's own occupation).
    skills: frozenset[uuid.UUID] = frozenset()


def skill_join_hits(
    essential: int, neighbours: list[SkillNeighbour], *, limit: int = JOIN_HITS
) -> tuple[Hit, ...]:
    """A title's occupation (with `essential` essential skills) joined to others by the
    essential skills they share: each with at least `MIN_SHARED_SKILLS`, scored by the share
    of both roles' essential skills they have in common (Jaccard) over the best such share,
    as a search's ranks are over its best. The best `limit`, in a deterministic order, and
    every occupation tied with the last of them: a cut never falls inside an exact tie."""
    joined = [n for n in neighbours if n.shared >= MIN_SHARED_SKILLS]
    share = {n.concept_id: n.shared / (essential + n.essential - n.shared) for n in joined}

    def tie(n: SkillNeighbour) -> tuple[float, int]:
        return (-share[n.concept_id], -n.shared)

    kept = sorted(joined, key=lambda n: (*tie(n), str(n.concept_id)))
    end = min(limit, len(kept))
    while 0 < end < len(kept) and tie(kept[end]) == tie(kept[end - 1]):
        end += 1
    kept = kept[:end]
    top = max((share[n.concept_id] for n in kept), default=0.0)
    return tuple(
        Hit(
            n.concept_id,
            share[n.concept_id] / top,
            label_match=False,
            shared_skills=n.shared,
            skills=n.skills,
        )
        for n in kept
    )


def too_general(reach: int, skills: int, *, exact: bool) -> bool:
    """A search too general to find work on its own: it reaches more than
    `TOO_GENERAL_OCCUPATIONS` occupations, or more than `TOO_GENERAL_SKILLS` different
    essential skills none of which is named by exactly its words."""
    return reach > TOO_GENERAL_OCCUPATIONS or (skills > TOO_GENERAL_SKILLS and not exact)


@dataclass(frozen=True)
class PoolQuery:
    query_id: str
    text: str
    channel: SlateChannel
    based_on: tuple[EvidenceItem, ...]
    hits: tuple[Hit, ...]
    # How many occupations it reached in all, past its own cut too; None: its hits are all.
    # A search that can find work never reaches past its cut (`TOO_GENERAL_OCCUPATIONS` is
    # below the pool's bound), so only a join's cut leaves occupations out (`unkept`).
    total: int | None = None
    unkept: frozenset[uuid.UUID] = frozenset()  # what a join reached past its best 30
    # Too general to find work on its own (`too_general`): it only adds weight to work
    # another search found.
    too_general: bool = False

    @property
    def reach(self) -> int:
        return len(self.hits) if self.total is None else self.total


def skill_join(
    query_id: str,
    title: str,
    channel: SlateChannel,
    based_on: tuple[EvidenceItem, ...],
    essential: int,
    neighbours: list[SkillNeighbour],
) -> PoolQuery:
    """The work joined to a title's occupation by shared essential skills (`skill_join_hits`),
    with every occupation the join reached, kept or not."""
    hits = skill_join_hits(essential, neighbours)
    joined = frozenset(n.concept_id for n in neighbours if n.shared >= MIN_SHARED_SKILLS)
    unkept = joined - {hit.concept_id for hit in hits}
    return PoolQuery(query_id, title, channel, based_on, hits, total=len(joined), unkept=unkept)


@dataclass(frozen=True)
class Occupation:
    """What the slate needs to know about an occupation from the taxonomy."""

    concept_id: uuid.UUID
    title: str
    family_code: str  # ISCO-08 minor group
    family_label: str
    sector_code: str  # ISCO-08 major group
    preferred_key: str  # its preferred label as a concept key
    label_keys: frozenset[str]  # its non-hidden labels as concept keys
    essential_skills: int  # how many essential skills ESCO lists for it


@dataclass(frozen=True)
class Match:
    query: PoolQuery
    # The occupation the hit reached: the candidate's own, or a near-identical role folded
    # into it (DIV1-05), whose skills are that role's, never the candidate's.
    concept_id: uuid.UUID
    score: float
    label_match: bool
    shared_skills: int | None = None
    skill: str | None = None
    skills: frozenset[uuid.UUID] = frozenset()


@dataclass(frozen=True)
class Candidate:
    occupation: Occupation
    matches: tuple[Match, ...]
    relevance: float
    direction: Direction
    channels: frozenset[SlateChannel]
    # How many occupations the most specific search that found it reached: equal relevance
    # goes to work a specific answer found before work a general one found (Task W2B re-review
    # 2, N-M4), then to the larger share of its essential skills the person's answers reach
    # (its own matches only), never to the title (re-review I-B).
    reach: int
    share: float
    duplicate_of: uuid.UUID | None = None

    @property
    def best_score(self) -> float:
        return _found_by(self.matches)

    @property
    def own_matches(self) -> tuple[Match, ...]:
        """The matches that reached this occupation itself, not a role folded into it."""
        return tuple(m for m in self.matches if m.concept_id == self.occupation.concept_id)


@dataclass(frozen=True)
class Pool:
    candidates: tuple[Candidate, ...]
    # Occupations a search or join that can find work reached and the pool doesn't keep: past
    # a join's best 30 or past `POOL_LIMIT`.
    beyond_limit: int

    def __iter__(self) -> Iterator[Candidate]:
        return iter(self.candidates)


@dataclass(frozen=True)
class SlateControls:
    emphasis: Emphasis = Emphasis.BALANCED
    exclude_concepts: frozenset[uuid.UUID] = frozenset()
    exclude_families: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Left:
    candidate: Candidate
    reason: NotIncluded
    duplicate_of: uuid.UUID | None = None


@dataclass(frozen=True)
class Slate:
    suggestions: tuple[Candidate, ...]
    not_included: tuple[Left, ...]
    pool_size: int  # distinct occupations after de-duplication
    beyond_limit: int
    excluded: dict[str, int]
    family_limit: int
    fewer_reasons: list[FewerReason] = field(default_factory=list)
    notes: list[SlateNote] = field(default_factory=list)


_CLOSE_CHANNELS = frozenset({SlateChannel.CURRENT, SlateChannel.USER_PROPOSED})
_TRANSFER_CHANNELS = frozenset(
    {SlateChannel.TRANSFERABLE, SlateChannel.CROSS_INDUSTRY, SlateChannel.SHARED_SKILLS}
)


def _direction(
    occupation: Occupation, channels: frozenset[SlateChannel], familiar: frozenset[str]
) -> Direction:
    if occupation.family_code in familiar or channels & _CLOSE_CHANNELS:
        return Direction.CLOSE
    if channels & _TRANSFER_CHANNELS:
        return Direction.TRANSFERABLE
    return Direction.LESS_FAMILIAR


def _found_by(matches: Iterable[Match]) -> float:
    """The best score of a search or join that found it: one too general to find work on its
    own never counts here."""
    return max(m.score for m in matches if not m.query.too_general)


def _relevance(matches: list[Match]) -> float:
    """The best score that found it, plus a little for each further query that reached it,
    a search too general to find work alone included."""
    further = len({match.query.query_id for match in matches}) - 1
    return min(MAX_RELEVANCE, _found_by(matches) + FURTHER_QUERY_BONUS * further)


def _reach(occupation: Occupation, matches: list[Match]) -> int:
    return min(
        m.query.reach
        for m in matches
        if m.concept_id == occupation.concept_id and not m.query.too_general
    )


def _share(occupation: Occupation, matches: list[Match]) -> float:
    reached = frozenset().union(
        *(m.skills for m in matches if m.concept_id == occupation.concept_id)
    )
    return len(reached) / occupation.essential_skills if occupation.essential_skills else 0.0


def _candidate(occupation: Occupation, matches: list[Match], familiar: frozenset[str]) -> Candidate:
    channels = frozenset(m.query.channel for m in matches)
    return Candidate(
        occupation,
        tuple(matches),
        _relevance(matches),
        _direction(occupation, channels, familiar),
        channels,
        _reach(occupation, matches),
        _share(occupation, matches),
    )


def _order(candidate: Candidate) -> tuple[float, int, float, str, str]:
    """Relevance first; equals go to work a more specific search found (it reached fewer
    occupations), then to the larger share of essential skills reached, and the title is
    only the last tie-break (never cut ties alphabetically)."""
    return (
        -candidate.relevance,
        candidate.reach,
        -candidate.share,
        candidate.occupation.title,
        str(candidate.occupation.concept_id),
    )


def _aliases(a: Occupation, b: Occupation) -> bool:
    """One is a name of the other within the same kind of work (ISCO minor group): its
    preferred label is one of the other's labels, or they have the same labels. Merely
    sharing some third label is not enough (ESCO gives many distinct occupations a common
    label: "geologist", "facility manager"), and an alias across kinds of work names related
    work, not the same role (ESCO lists "biochemist" as a chemist)."""
    return a.family_code == b.family_code and (
        a.preferred_key in b.label_keys
        or b.preferred_key in a.label_keys
        or a.label_keys == b.label_keys
    )


def _near_identical_groups(candidates: list[Candidate]) -> list[list[Candidate]]:
    """Each candidate joins the most relevant group lead it is an alias of, or leads its own
    group. Never transitive: a candidate is compared with leads only, so a chain of shared
    labels cannot fold unrelated work together (DIV1-05)."""
    groups: list[list[Candidate]] = []
    for candidate in sorted(candidates, key=_order):
        group = next((g for g in groups if _aliases(g[0].occupation, candidate.occupation)), None)
        if group is None:
            groups.append([candidate])
        else:
            group.append(candidate)
    return groups


def _across_families(leads: list[Candidate], limit: int) -> set[uuid.UUID]:
    """The working pool: round-robin across ISCO families in relevance order, so the bound
    samples every retrieved family before relevance cuts any (spec section 4, DIV-1). Under
    the bound it keeps everything. (Oversampling catalogue areas the search under-retrieves
    is not done.)"""
    by_family: dict[str, list[Candidate]] = {}
    for lead in leads:  # already in relevance order
        by_family.setdefault(lead.occupation.family_code, []).append(lead)
    kept: list[Candidate] = []
    depth = 0
    while len(kept) < min(limit, len(leads)):
        kept += [members[depth] for members in by_family.values() if depth < len(members)][
            : limit - len(kept)
        ]
        depth += 1
    return {c.occupation.concept_id for c in kept}


def build_pool(
    queries: list[PoolQuery],
    occupations: Mapping[uuid.UUID, Occupation],
    familiar_families: frozenset[str],
    *,
    limit: int = POOL_LIMIT,
) -> Pool:
    """Every hit pooled by concept and near-identical roles folded together, bounded. A
    search too general to find work on its own only adds to occupations another search or
    join found. What those reached and the pool doesn't keep is counted: past a join's cut,
    or past the pool's bound."""
    finding = [q for q in queries if not q.too_general]
    found: dict[uuid.UUID, list[Match]] = {}
    for query in [*finding, *(q for q in queries if q.too_general)]:
        weight = CHANNEL_WEIGHT[query.channel]
        for hit in query.hits:
            if hit.concept_id in occupations and (not query.too_general or hit.concept_id in found):
                found.setdefault(hit.concept_id, []).append(
                    Match(
                        query,
                        hit.concept_id,
                        hit.score * weight,
                        hit.label_match,
                        hit.shared_skills,
                        hit.skill,
                        hit.skills,
                    )
                )
    candidates = [
        _candidate(occupations[concept_id], matches, familiar_families)
        for concept_id, matches in found.items()
    ]
    pooled: list[Candidate] = []
    for group in _near_identical_groups(candidates):
        lead, rest = group[0], group[1:]
        if rest:  # the representative carries every query that found any of them
            merged = [m for c in group for m in c.matches]
            lead = _candidate(lead.occupation, merged, familiar_families)
        pooled.append(lead)
        pooled += [replace(c, duplicate_of=lead.occupation.concept_id) for c in rest]
    leads = sorted((c for c in pooled if c.duplicate_of is None), key=_order)
    kept = _across_families(leads, limit)
    pool = tuple(
        c for c in sorted(pooled, key=_order) if (c.duplicate_of or c.occupation.concept_id) in kept
    )
    reached = {h.concept_id for q in finding for h in q.hits if h.concept_id in occupations}
    reached |= {concept for q in finding for concept in q.unkept}
    return Pool(pool, len(reached - {c.occupation.concept_id for c in pool}))


@dataclass(frozen=True)
class _Policy:
    floor: float
    family_limit: int
    quotas: Mapping[Direction, int]
    note: SlateNote | None = None


_BALANCED = {Direction.CLOSE: 2, Direction.TRANSFERABLE: 2, Direction.LESS_FAMILIAR: 2}
_POLICIES: Mapping[Emphasis, _Policy] = {
    Emphasis.BALANCED: _Policy(RELEVANCE_FLOOR, FAMILY_LIMIT, _BALANCED),
    Emphasis.PRACTICAL: _Policy(
        RELEVANCE_FLOOR,
        FAMILY_LIMIT,
        {Direction.CLOSE: 3, Direction.TRANSFERABLE: 2, Direction.LESS_FAMILIAR: 1},
    ),
    Emphasis.UNFAMILIAR: _Policy(
        RELEVANCE_FLOOR,
        FAMILY_LIMIT,
        {Direction.CLOSE: 1, Direction.TRANSFERABLE: 1, Direction.LESS_FAMILIAR: 4},
    ),
    Emphasis.BROAD: _Policy(BROAD_RELEVANCE_FLOOR, 1, _BALANCED, CastingWider()),
    Emphasis.DEEPER: _Policy(
        RELEVANCE_FLOOR,
        DEEPER_FAMILY_LIMIT,
        _BALANCED,
        MoreDepth(family_limit=DEEPER_FAMILY_LIMIT),
    ),
}


def choose_slate(
    pool: Pool,
    controls: SlateControls | None = None,
    left_out: Mapping[uuid.UUID, NotIncluded] | None = None,
) -> Slate:
    """`left_out`: occupations a hard filter leaves out (the salary floor, the AI Resilience
    filter), each with its reason; the caller decided, from evidence, that each is below."""
    controls = controls or SlateControls()
    hard = left_out or {}
    policy = _POLICIES[controls.emphasis]
    left: list[Left] = []
    eligible: list[Candidate] = []
    excluded = {"occupations": 0, "families": 0}
    for candidate in pool:
        occupation = candidate.occupation
        if candidate.duplicate_of is not None:
            left.append(Left(candidate, NotIncluded.DUPLICATE, candidate.duplicate_of))
        elif occupation.concept_id in controls.exclude_concepts:
            excluded["occupations"] += 1
            left.append(Left(candidate, NotIncluded.EXCLUDED_OCCUPATION))
        elif occupation.family_code in controls.exclude_families:
            excluded["families"] += 1
            left.append(Left(candidate, NotIncluded.EXCLUDED_FAMILY))
        elif occupation.concept_id in hard:
            left.append(Left(candidate, hard[occupation.concept_id]))
        elif candidate.best_score < policy.floor:
            left.append(Left(candidate, NotIncluded.BELOW_RELEVANCE_FLOOR))
        else:
            eligible.append(candidate)

    chosen: list[Candidate] = []
    families: Counter[str] = Counter()
    sectors: set[str] = set()
    directions: Counter[Direction] = Counter()
    remaining = sorted(eligible, key=_order)

    def gain(candidate: Candidate) -> float:
        occupation = candidate.occupation
        return (
            candidate.relevance
            + NEW_FAMILY_BONUS * (families[occupation.family_code] == 0)
            + NEW_SECTOR_BONUS * (occupation.sector_code not in sectors)
            + DIRECTION_BONUS
            * (directions[candidate.direction] < policy.quotas[candidate.direction])
            - SAME_FAMILY_PENALTY * families[occupation.family_code]
        )

    while len(chosen) < SLATE_SIZE:
        options = [c for c in remaining if families[c.occupation.family_code] < policy.family_limit]
        if not options:
            break
        best = max(options, key=gain)  # the first of equals, in `_order`
        chosen.append(best)
        remaining.remove(best)
        families[best.occupation.family_code] += 1
        sectors.add(best.occupation.sector_code)
        directions[best.direction] += 1

    blocked = 0
    for candidate in remaining:
        at_limit = families[candidate.occupation.family_code] >= policy.family_limit
        blocked += at_limit
        reason = NotIncluded.FAMILY_LIMIT if at_limit else NotIncluded.LESS_RELEVANT
        left.append(Left(candidate, reason))

    fewer: list[FewerReason] = []
    if len(chosen) < SLATE_SIZE:
        if not pool.candidates:
            fewer.append(NothingFound())
        elif len(eligible) < SLATE_SIZE:
            fewer.append(FewMatched(count=len(eligible)))
        if blocked:
            fewer.append(KindsOfWorkShown(count=blocked, family_limit=policy.family_limit))
        removed = sum(excluded.values())
        if removed:
            fewer.append(ExclusionsRemoved(count=removed))
    return Slate(
        suggestions=tuple(chosen),
        not_included=tuple(sorted(left, key=lambda item: _order(item.candidate))),
        pool_size=sum(c.duplicate_of is None for c in pool),
        beyond_limit=pool.beyond_limit,
        excluded=excluded,
        family_limit=policy.family_limit,
        fewer_reasons=fewer,
        notes=[policy.note] if policy.note else [],
    )


@dataclass(frozen=True)
class Connection:
    """The unexpected connection: a suggestion joined to the person's role by the essential
    skills the two share, in another kind of work, never a title the person named."""

    candidate: Candidate
    shared_skills: int


def unexpected_connection(
    slate: Slate,
    role_joins: frozenset[str],
    own_families: frozenset[str],
    named: frozenset[uuid.UUID],
) -> Connection | None:
    """Of the slate's suggestions that a join from the person's role found itself (`role_joins`:
    those queries' IDs; never through a role folded into it), outside the role's own kinds of
    work (`own_families`) and not a title the person named: the one sharing the most essential
    skills with the role, then
    the larger share of both roles' skills, then the first in the slate. None when no
    suggestion qualifies: a revelation with no source is never shown."""
    best: tuple[tuple[int, float, int], Connection] | None = None
    for position, candidate in enumerate(slate.suggestions):
        occupation = candidate.occupation
        if occupation.family_code in own_families or occupation.concept_id in named:
            continue
        joined = [
            m for m in candidate.own_matches if m.query.query_id in role_joins and m.shared_skills
        ]
        if not joined:
            continue
        top = max(joined, key=lambda m: (m.shared_skills or 0, m.score))
        rank = (top.shared_skills or 0, top.score, -position)
        if best is None or rank > best[0]:
            best = (rank, Connection(candidate, top.shared_skills or 0))
    return None if best is None else best[1]
