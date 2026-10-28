"""The discovery pool and the slate of suggestions (spec section 4, DIV-1; S2.4). Pure.

**Pool.** Every query's taxonomy hits are pooled by concept: an alias is the same concept,
and an occupation whose preferred label is a label of another (as a concept key) is
near-identical to it, so they count once (DIV1-05); the most relevant represents them and
the others say which they duplicate. Folding is never transitive. The working pool is
bounded (`POOL_LIMIT`, the upper end of the soft 60-120 target) and filled round-robin
across ISCO families before relevance cuts it. A candidate's relevance rests only on how
well the person's own answers retrieved it: its best normalised rank in any query, plus a
little for each further query that found it. No pay, popularity, prestige or AI-resilience
figure enters (DIV1-07), and no percentage is ever produced (REC1-05).

**Direction** is relative to the person (DIV1-12): close to what they do now (its ISCO
family is one of their current role's or targets', or their role or a target found it),
building on skills they could carry over (a transferable or cross-industry query found it),
or something different (anything else).

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
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum

from nessa.profile.discovery import EvidenceItem, QueryChannel

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


class SlateChannel(StrEnum):
    """How a candidate was found: the model's channels plus Nessa's own."""

    CURRENT = "current"  # the person's current role, searched by Nessa
    USER_PROPOSED = "user_proposed"  # a title the person gave as a target
    TASKS = QueryChannel.TASKS.value
    ENVIRONMENT = QueryChannel.ENVIRONMENT.value
    TRANSFERABLE = QueryChannel.TRANSFERABLE.value
    CROSS_INDUSTRY = QueryChannel.CROSS_INDUSTRY.value
    LESS_FAMILIAR = QueryChannel.LESS_FAMILIAR.value
    HYPOTHESIS = "hypothesis"  # a model title that ESCO holds


# How much a hit counts by the channel that found it. How someone likes to work informs the
# search but is weaker evidence than what they do, enjoy or name (spec section 4: one source
# of hypotheses among several); it is never a filter (REC1-03).
CHANNEL_WEIGHT: Mapping[SlateChannel, float] = {
    SlateChannel.CURRENT: 1.0,
    SlateChannel.USER_PROPOSED: 1.0,
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
    BELOW_RELEVANCE_FLOOR = "below_relevance_floor"
    FAMILY_LIMIT = "family_limit"
    LESS_RELEVANT = "less_relevant"


@dataclass(frozen=True)
class Hit:
    concept_id: uuid.UUID
    score: float  # rank normalised within its query, 0-1; an exact label match is 1
    label_match: bool


@dataclass(frozen=True)
class PoolQuery:
    query_id: str
    text: str
    channel: SlateChannel
    based_on: tuple[EvidenceItem, ...]
    hits: tuple[Hit, ...]


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


@dataclass(frozen=True)
class Match:
    query: PoolQuery
    score: float
    label_match: bool


@dataclass(frozen=True)
class Candidate:
    occupation: Occupation
    matches: tuple[Match, ...]
    relevance: float
    direction: Direction
    channels: frozenset[SlateChannel]
    duplicate_of: uuid.UUID | None = None

    @property
    def best_score(self) -> float:
        return max(m.score for m in self.matches)


@dataclass(frozen=True)
class Pool:
    candidates: tuple[Candidate, ...]
    beyond_limit: int  # distinct occupations retrieved past `POOL_LIMIT`, not kept

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
    fewer_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


_CLOSE_CHANNELS = frozenset({SlateChannel.CURRENT, SlateChannel.USER_PROPOSED})
_TRANSFER_CHANNELS = frozenset({SlateChannel.TRANSFERABLE, SlateChannel.CROSS_INDUSTRY})


def _direction(
    occupation: Occupation, channels: frozenset[SlateChannel], familiar: frozenset[str]
) -> Direction:
    if occupation.family_code in familiar or channels & _CLOSE_CHANNELS:
        return Direction.CLOSE
    if channels & _TRANSFER_CHANNELS:
        return Direction.TRANSFERABLE
    return Direction.LESS_FAMILIAR


def _relevance(matches: list[Match]) -> float:
    best: dict[str, float] = {}
    for match in matches:
        best[match.query.query_id] = max(best.get(match.query.query_id, 0.0), match.score)
    scores = sorted(best.values(), reverse=True)
    return min(MAX_RELEVANCE, scores[0] + FURTHER_QUERY_BONUS * (len(scores) - 1))


def _candidate(occupation: Occupation, matches: list[Match], familiar: frozenset[str]) -> Candidate:
    channels = frozenset(m.query.channel for m in matches)
    return Candidate(
        occupation,
        tuple(matches),
        _relevance(matches),
        _direction(occupation, channels, familiar),
        channels,
    )


def _order(candidate: Candidate) -> tuple[float, str, str]:
    return (-candidate.relevance, candidate.occupation.title, str(candidate.occupation.concept_id))


def _aliases(a: Occupation, b: Occupation) -> bool:
    """One is a name of the other: its preferred label is one of the other's labels, or they
    have the same labels. Merely sharing some third label is not enough: ESCO gives many
    distinct occupations a common label ("geologist", "facility manager")."""
    return (
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
    """Every hit pooled by concept and near-identical roles folded together, bounded."""
    found: dict[uuid.UUID, list[Match]] = {}
    for query in queries:
        weight = CHANNEL_WEIGHT[query.channel]
        for hit in query.hits:
            if hit.concept_id in occupations:
                found.setdefault(hit.concept_id, []).append(
                    Match(query, hit.score * weight, hit.label_match)
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
    return Pool(
        tuple(
            c
            for c in sorted(pooled, key=_order)
            if (c.duplicate_of or c.occupation.concept_id) in kept
        ),
        max(0, len(leads) - limit),
    )


@dataclass(frozen=True)
class _Policy:
    floor: float
    family_limit: int
    quotas: Mapping[Direction, int]
    note: str | None = None


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
    Emphasis.BROAD: _Policy(
        BROAD_RELEVANCE_FLOOR,
        1,
        _BALANCED,
        "Casting wider: a lower bar for relevance and one suggestion per kind of work.",
    ),
    Emphasis.DEEPER: _Policy(
        RELEVANCE_FLOOR,
        DEEPER_FAMILY_LIMIT,
        _BALANCED,
        f"Showing up to {DEEPER_FAMILY_LIMIT} from one kind of work, because you asked for "
        "more depth.",
    ),
}


def _plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def choose_slate(pool: Pool, controls: SlateControls | None = None) -> Slate:
    controls = controls or SlateControls()
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

    fewer: list[str] = []
    if len(chosen) < SLATE_SIZE:
        if not pool.candidates:
            fewer.append("None of your answers matched an occupation in ESCO yet.")
        elif len(eligible) < SLATE_SIZE:
            fewer.append(
                f"Only {_plural(len(eligible), 'occupation', 'occupations')} matched your "
                "answers closely enough to suggest. Nessa doesn't fill the rest with weaker "
                "matches."
            )
        if blocked:
            fewer.append(
                f"{_plural(blocked, 'more is', 'more are')} in kinds of work already shown "
                f"{policy.family_limit} times; ask for more depth to see them."
            )
        removed = sum(excluded.values())
        if removed:
            fewer.append(
                f"Your exclusions removed {_plural(removed, 'occupation', 'occupations')}."
            )
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
