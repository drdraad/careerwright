"""The discovery pool and slate (S2.4; DIV-1, REC-1): de-duplicate before counting
diversity, keep a relevance floor, prefer a varied slate with a soft family limit, return
fewer with the reason, and never let a preference or a view filter remove work silently.
Hand-built candidates; no database."""

import uuid

import pytest

from nessa.profile.discovery import EvidenceItem
from nessa.profile.interview import ProfileField
from nessa.profile.slate import (
    FAMILY_LIMIT,
    SLATE_SIZE,
    Direction,
    Emphasis,
    Hit,
    NotIncluded,
    Occupation,
    PoolQuery,
    Slate,
    SlateChannel,
    SlateControls,
    build_pool,
    choose_slate,
)

ENJOY = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="repairing physical objects")
ROLE = EvidenceItem(field=ProfileField.CURRENT_ROLE, text="Warehouse supervisor")


def concept(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"test:{name}")


def occupation(name: str, family: str, *aliases: str) -> Occupation:
    return Occupation(
        concept_id=concept(name),
        title=name,
        family_code=family,
        family_label=f"Family {family}",
        sector_code=family[0],
        label_keys=frozenset({name.casefold(), *(a.casefold() for a in aliases)}),
    )


def hits(*scored: tuple[str, float]) -> tuple[Hit, ...]:
    return tuple(Hit(concept(name), score, label_match=False) for name, score in scored)


def pool_query(
    query_id: str, channel: SlateChannel, *scored: tuple[str, float], evidence: EvidenceItem = ENJOY
) -> PoolQuery:
    return PoolQuery(query_id, f"query {query_id}", channel, (evidence,), hits(*scored))


# Seven families across three sectors: 7231 and 7233 are both sector 7, as are 7126.
OCCUPATIONS = {
    o.concept_id: o
    for o in (
        occupation("Bicycle mechanic", "723"),
        occupation("Agricultural machinery technician", "723"),
        occupation("Motor vehicle mechanic", "723"),
        occupation("Groundsperson", "921", "grounds maintenance worker"),
        occupation("Grounds maintenance worker", "921"),
        occupation("Tree surgeon", "621"),
        occupation("Furniture restorer", "752"),
        occupation("Warehouse manager", "432"),
        occupation("Stock controller", "432"),
        occupation("Facilities technician", "311"),
        occupation("Wind turbine technician", "311"),
    )
}
FAMILIAR = frozenset({"432"})  # the families of the current role


def p02_like_pool() -> list[PoolQuery]:
    return [
        pool_query(
            "q1",
            SlateChannel.TASKS,
            ("Bicycle mechanic", 1.0),
            ("Agricultural machinery technician", 0.9),
            ("Motor vehicle mechanic", 0.8),
            ("Furniture restorer", 0.7),
        ),
        pool_query(
            "q2",
            SlateChannel.ENVIRONMENT,
            ("Groundsperson", 1.0),
            ("Grounds maintenance worker", 0.95),
            ("Tree surgeon", 0.9),
            ("Wind turbine technician", 0.6),
        ),
        pool_query(
            "q3",
            SlateChannel.TRANSFERABLE,
            ("Facilities technician", 1.0),
            ("Stock controller", 0.5),
            evidence=ROLE,
        ),
        pool_query(
            "current",
            SlateChannel.CURRENT,
            ("Warehouse manager", 1.0),
            ("Stock controller", 0.8),
            evidence=ROLE,
        ),
    ]


def slate(queries: list[PoolQuery] | None = None, controls: SlateControls | None = None) -> Slate:
    pool = build_pool(queries or p02_like_pool(), OCCUPATIONS, FAMILIAR)
    return choose_slate(pool, controls)


@pytest.mark.req("DIV1-06", "DIV1-11")
def test_a_varied_slate_of_six_from_several_families_and_all_three_directions() -> None:
    chosen = slate()

    titles = [s.occupation.title for s in chosen.suggestions]
    assert len(titles) == SLATE_SIZE
    families = [s.occupation.family_code for s in chosen.suggestions]
    assert max(families.count(f) for f in families) <= FAMILY_LIMIT
    assert len(set(families)) >= 3  # P02: at least three families when the pool supports it
    directions = {s.direction for s in chosen.suggestions}
    assert directions == set(Direction)
    assert chosen.fewer_reasons == []


@pytest.mark.req("DIV1-05")
def test_near_identical_roles_count_once_and_say_which_they_duplicate() -> None:
    chosen = slate()

    shown = {s.occupation.title for s in chosen.suggestions}
    assert not {"Groundsperson", "Grounds maintenance worker"} <= shown
    [duplicate] = [n for n in chosen.not_included if n.reason is NotIncluded.DUPLICATE]
    assert duplicate.candidate.occupation.title == "Grounds maintenance worker"
    assert duplicate.duplicate_of == concept("Groundsperson")


@pytest.mark.req("DIV1-06")
def test_a_thin_pool_returns_fewer_with_the_reason_never_filler() -> None:
    thin = [
        pool_query("q1", SlateChannel.TASKS, ("Bicycle mechanic", 1.0), ("Tree surgeon", 0.1)),
    ]

    chosen = slate(thin)

    assert [s.occupation.title for s in chosen.suggestions] == ["Bicycle mechanic"]
    assert chosen.fewer_reasons  # said why, in words
    [below] = [n for n in chosen.not_included if n.reason is NotIncluded.BELOW_RELEVANCE_FLOOR]
    assert below.candidate.occupation.title == "Tree surgeon"


@pytest.mark.req("DIV1-11")
def test_the_family_limit_is_soft_and_relaxed_visibly_when_depth_is_asked_for() -> None:
    narrow = [
        pool_query(
            "q1",
            SlateChannel.TASKS,
            ("Bicycle mechanic", 1.0),
            ("Agricultural machinery technician", 0.95),
            ("Motor vehicle mechanic", 0.9),
        )
    ]

    default = slate(narrow)
    deeper = slate(narrow, SlateControls(emphasis=Emphasis.DEEPER))

    assert len(default.suggestions) == FAMILY_LIMIT
    assert any(n.reason is NotIncluded.FAMILY_LIMIT for n in default.not_included)
    assert len(deeper.suggestions) == 3
    assert deeper.notes  # the relaxation is stated, never silent


@pytest.mark.req("REC1-08", "DIV1-07")
def test_excluding_a_title_keeps_its_family_and_every_filter_is_counted() -> None:
    chosen = slate(
        controls=SlateControls(exclude_concepts=frozenset({concept("Bicycle mechanic")}))
    )

    shown = {s.occupation.title for s in chosen.suggestions}
    assert "Bicycle mechanic" not in shown
    assert {"Agricultural machinery technician", "Motor vehicle mechanic"} & shown
    assert chosen.excluded == {"occupations": 1, "families": 0}

    by_family = slate(controls=SlateControls(exclude_families=frozenset({"723"})))
    assert not any(s.occupation.family_code == "723" for s in by_family.suggestions)
    assert by_family.excluded == {"occupations": 0, "families": 3}


@pytest.mark.req("REC1-08", "DIV1-12")
def test_less_familiar_and_more_practical_shift_the_slate_relative_to_the_person() -> None:
    unfamiliar = slate(controls=SlateControls(emphasis=Emphasis.UNFAMILIAR))
    practical = slate(controls=SlateControls(emphasis=Emphasis.PRACTICAL))

    def count(chosen: Slate, direction: Direction) -> int:
        return sum(s.direction is direction for s in chosen.suggestions)

    assert count(unfamiliar, Direction.LESS_FAMILIAR) > count(practical, Direction.LESS_FAMILIAR)
    assert count(practical, Direction.CLOSE) >= 2
    # Familiarity is the person's: the same occupation is close for someone whose current
    # role is in its family, and less familiar for someone else.
    other = choose_slate(build_pool(p02_like_pool(), OCCUPATIONS, frozenset({"723"})))
    mechanic = next(s for s in other.suggestions if s.occupation.title == "Bicycle mechanic")
    assert mechanic.direction is Direction.CLOSE


@pytest.mark.req("REC1-03")
def test_a_work_style_preference_only_adds_candidates_never_removes_one() -> None:
    without = [q for q in p02_like_pool() if q.channel is not SlateChannel.ENVIRONMENT]

    pool_without = {c.occupation.concept_id for c in build_pool(without, OCCUPATIONS, FAMILIAR)}
    pool_with = {
        c.occupation.concept_id for c in build_pool(p02_like_pool(), OCCUPATIONS, FAMILIAR)
    }

    assert pool_without < pool_with


@pytest.mark.req("REC1-05", "DIV1-12")
def test_relevance_rests_on_the_answers_not_on_popularity_and_has_no_percentage() -> None:
    chosen = slate()

    first = chosen.suggestions[0]
    assert first.matches  # the queries (and so the answers) that found it
    assert all(m.query.based_on for m in first.matches)
    fields = set(type(first).__dataclass_fields__) | set(
        type(first.occupation).__dataclass_fields__
    )
    assert not {f for f in fields if "percent" in f or "match_score" in f or "popular" in f}
