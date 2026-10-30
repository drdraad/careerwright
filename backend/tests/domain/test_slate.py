"""The discovery pool and slate (S2.4; DIV-1, REC-1): de-duplicate before counting
diversity, keep a relevance floor, prefer a varied slate with a soft family limit, return
fewer with the reason, and never let a preference or a view filter remove work silently.
Hand-built candidates; no database."""

import uuid

import pytest

from careerwright.profile.discovery import EvidenceItem
from careerwright.profile.interview import ProfileField
from careerwright.profile.slate import (
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
        preferred_key=name.casefold(),
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


@pytest.mark.req("DIV1-05")
def test_folding_never_chains_unrelated_work_through_shared_labels() -> None:
    # ESCO v1.2.1's own labels (Task 6 review A-I-2): quarry engineer and quarry manager name
    # each other; mine manager is also called "quarry manager" and "facility manager"; the
    # building caretaker is also a "facility manager"; and "building caretaker" is a name of
    # the building cleaner. Transitively that made quarry engineer and building cleaner one.
    chained = {
        o.concept_id: o
        for o in (
            occupation("Quarry engineer", "214", "quarry manager", "mining engineer"),
            occupation("Quarry manager", "132", "quarry engineer", "quarrying engineer"),
            occupation("Mine manager", "132", "quarry manager", "facility manager"),
            occupation("Building caretaker", "515", "facility manager", "caretaker"),
            occupation("Building cleaner", "911", "building caretaker", "janitor"),
        )
    }
    query = pool_query(
        "q1",
        SlateChannel.TASKS,
        ("Quarry engineer", 0.9),
        ("Building cleaner", 0.85),
        ("Mine manager", 0.8),
        ("Building caretaker", 0.7),
        ("Quarry manager", 0.6),
    )

    pool = build_pool([query], chained, frozenset())

    folded = {c.occupation.title: c.duplicate_of for c in pool}
    # Nothing folds across kinds of work (ISCO minor groups 214, 132, 515, 911; re-review
    # N-M3), so the chain is gone. Within 132, "quarry manager" is a name of the mine manager.
    assert folded == {
        "Quarry engineer": None,
        "Building cleaner": None,
        "Mine manager": None,
        "Building caretaker": None,
        "Quarry manager": concept("Mine manager"),
    }

    # Within one kind of work a chain is still never followed: the groundskeeper is a name of
    # the gardener, the park keeper a name of the groundskeeper, not of the gardener.
    in_one_family = {
        o.concept_id: o
        for o in (
            occupation("Gardener", "921", "groundskeeper"),
            occupation("Groundskeeper", "921", "park keeper"),
            occupation("Park keeper", "921"),
        )
    }
    query = pool_query(
        "q2", SlateChannel.TASKS, ("Gardener", 0.9), ("Park keeper", 0.8), ("Groundskeeper", 0.7)
    )
    folded = {
        c.occupation.title: c.duplicate_of for c in build_pool([query], in_one_family, frozenset())
    }
    assert folded == {
        "Gardener": None,
        "Park keeper": None,
        "Groundskeeper": concept("Gardener"),
    }


@pytest.mark.req("DIV1-05")
def test_an_alias_from_another_kind_of_work_is_not_a_duplicate() -> None:
    # Re-review N-M3: ESCO lists "biochemist" as a label of chemist, but they are
    # different ISCO minor groups (211, 213): related work, not the same role.
    related = {
        o.concept_id: o
        for o in (
            occupation("Chemist", "211", "biochemist"),
            occupation("Biochemist", "213"),
            occupation("Groundsperson", "921", "grounds maintenance worker"),
            occupation("Grounds maintenance worker", "921"),
        )
    }
    query = pool_query(
        "q1",
        SlateChannel.TASKS,
        ("Chemist", 0.9),
        ("Biochemist", 0.8),
        ("Groundsperson", 0.7),
        ("Grounds maintenance worker", 0.6),
    )

    folded = {c.occupation.title: c.duplicate_of for c in build_pool([query], related, frozenset())}

    assert folded["Biochemist"] is None
    assert folded["Grounds maintenance worker"] == concept("Groundsperson")


@pytest.mark.req("DIV1-02", "DIV1-10")
def test_the_bounded_pool_samples_across_families_before_relevance_cuts_it() -> None:
    # Spec section 4 DIV-1: sample across occupational families before reranking. One family
    # with many strong matches must not crowd every other family out of the working pool.
    crowded = {
        o.concept_id: o
        for o in (
            *(occupation(f"Mechanic {n}", "723") for n in range(6)),
            occupation("Tree surgeon", "621"),
            occupation("Furniture restorer", "752"),
        )
    }
    query = pool_query(
        "q1",
        SlateChannel.TASKS,
        *((f"Mechanic {n}", 1.0 - n / 100) for n in range(6)),
        ("Tree surgeon", 0.5),
        ("Furniture restorer", 0.4),
    )

    pool = build_pool([query], crowded, frozenset(), limit=4)

    kept = {c.occupation.family_code for c in pool}
    assert kept == {"723", "621", "752"}
    assert pool.beyond_limit == 4


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


@pytest.mark.req("DIV1-07", "AIR1-05")
def test_a_hard_filter_leaves_out_only_what_it_names_and_says_why_for_each() -> None:
    # The salary floor and the AI Resilience filter decide what is below them (deterministic
    # code over the evidence); the slate only leaves those out, each with its own reason,
    # and fills from the rest: nothing else is removed (Task 7 slice B).
    pool = build_pool(p02_like_pool(), OCCUPATIONS, FAMILIAR)
    unfiltered = choose_slate(pool)
    left_out = {
        concept("Bicycle mechanic"): NotIncluded.BELOW_SALARY_FLOOR,
        concept("Tree surgeon"): NotIncluded.BELOW_AI_RESILIENCE_MINIMUM,
    }

    chosen = choose_slate(pool, left_out=left_out)

    shown = {s.occupation.title for s in chosen.suggestions}
    assert not {"Bicycle mechanic", "Tree surgeon"} & shown
    assert len(chosen.suggestions) == len(unfiltered.suggestions)  # filled from the rest
    reasons = {left.candidate.occupation.title: left.reason for left in chosen.not_included}
    assert reasons["Bicycle mechanic"] is NotIncluded.BELOW_SALARY_FLOOR
    assert reasons["Tree surgeon"] is NotIncluded.BELOW_AI_RESILIENCE_MINIMUM
    assert chosen.excluded == {"occupations": 0, "families": 0}  # the person's exclusions


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
