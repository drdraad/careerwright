"""Destinations joined by shared essential skills, never by shared words in a title (plan
section 4, Sprint W SW.5; ADR 0007 decision 13): the skill join's hits, the direction they
take. Hand-built occupations; no database."""

import uuid

import pytest

from careerwright.catalogue.records import SkillNeighbour
from careerwright.profile.discovery import EvidenceItem
from careerwright.profile.interview import ProfileField
from careerwright.profile.slate import (
    JOIN_HITS,
    MIN_SHARED_SKILLS,
    Direction,
    Occupation,
    PoolQuery,
    SlateChannel,
    build_pool,
    skill_join,
    skill_join_hits,
)

ROLE = EvidenceItem(field=ProfileField.CURRENT_ROLE, text="data analyst")


def concept(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"test:{name}")


def occupation(name: str, family: str) -> Occupation:
    return Occupation(
        concept_id=concept(name),
        title=name,
        family_code=family,
        family_label=f"Family {family}",
        sector_code=family[0],
        preferred_key=name.casefold(),
        label_keys=frozenset({name.casefold()}),
        essential_skills=20,
    )


# ESCO v1.2.1's counts for the data analyst (36 essential skills): the occupation, how many
# essential skills it shares with the data analyst, and how many it has.
NEIGHBOURS = {
    "data scientist": ("251", 22, 63),
    "data quality specialist": ("251", 12, 20),
    "chief data officer": ("133", 7, 16),
    "ICT information and knowledge manager": ("133", 8, 26),
    "statistician": ("212", 7, 50),
    "data entry clerk": ("413", 5, 10),
    "call centre analyst": ("334", 1, 20),  # one shared skill: below the join's minimum
}
OCCUPATIONS = {
    o.concept_id: o
    for o in (
        occupation("data analyst", "251"),
        *(occupation(name, family) for name, (family, _, _) in NEIGHBOURS.items()),
    )
}


def neighbours() -> list[SkillNeighbour]:
    return [
        SkillNeighbour(concept(name), shared, essential)
        for name, (_, shared, essential) in NEIGHBOURS.items()
    ]


def join(*, query_id: str = "skills") -> PoolQuery:
    return PoolQuery(
        query_id,
        "data analyst",
        SlateChannel.SHARED_SKILLS,
        (ROLE,),
        skill_join_hits(36, neighbours()),
    )


def test_a_join_needs_its_minimum_of_shared_skills_and_ranks_by_their_share_of_both() -> None:
    hits = {h.concept_id: h for h in skill_join_hits(36, neighbours())}

    assert concept("call centre analyst") not in hits  # 1 shared: never a join
    assert all(h.shared_skills is not None and h.shared_skills >= 3 for h in hits.values())
    assert MIN_SHARED_SKILLS == 3
    # Jaccard (shared over the two roles' essential skills together), over the best one:
    # the data scientist (22 / 77) leads, and the statistician's 50 skills dilute its 7.
    best = hits[concept("data scientist")]
    assert (best.score, best.label_match) == (1.0, False)
    order = sorted(hits, key=lambda c: -hits[c].score)
    assert order[:2] == [concept("data scientist"), concept("data quality specialist")]
    assert hits[concept("statistician")].score < hits[concept("chief data officer")].score
    assert all(0 < h.score <= 1 for h in hits.values())


def test_a_join_is_bounded_and_its_order_is_deterministic() -> None:
    many = [SkillNeighbour(concept(f"o{n}"), 3 + n % 5, 20) for n in range(50)]

    first = skill_join_hits(30, many, limit=10)
    again = skill_join_hits(30, list(reversed(many)), limit=10)

    assert len(first) == 10
    assert first == again
    assert skill_join_hits(30, []) == ()


@pytest.mark.req("DIV1-02", "DIV1-06")
def test_a_join_never_cuts_inside_a_tie() -> None:
    # Task W2B re-review 2, N-M1: the warehouse manager's places 23 to 47 tie exactly (equal
    # share, equal shared count), and the best 30 kept 8 of them by concept ID. The cut now
    # runs to the end of the tied group.
    better = [SkillNeighbour(concept(f"better {n}"), 8, 20) for n in range(2)]
    tied = [SkillNeighbour(concept(f"tied {n}"), 5, 20) for n in range(4)]
    worse = SkillNeighbour(concept("worse"), 4, 20)

    hits = skill_join_hits(30, [worse, *tied, *better], limit=3)

    assert {h.concept_id for h in hits} == {n.concept_id for n in [*better, *tied]}
    assert len(skill_join_hits(30, [worse, *tied, *better], limit=2)) == 2  # a cut between ties


@pytest.mark.req("DIV1-02")
def test_a_join_says_how_many_it_reached_and_which_it_did_not_keep() -> None:
    # Task W2B re-review 2, N-M2: what a join reaches past its best 30 is counted, not lost.
    reached = [SkillNeighbour(concept(f"o{n}"), MIN_SHARED_SKILLS + n, 40) for n in range(35)]
    below = SkillNeighbour(concept("one shared skill"), 1, 20)

    query = skill_join(
        "j1", "data analyst", SlateChannel.SHARED_SKILLS, (ROLE,), 36, [*reached, below]
    )

    assert (len(query.hits), query.reach) == (JOIN_HITS, 35)
    assert query.unkept == {concept(f"o{n}") for n in range(5)}  # the five sharing fewest


@pytest.mark.req("DIV1-10", "DIV1-12")
def test_a_joined_role_is_close_in_the_person_s_own_kind_of_work_and_transferable_elsewhere() -> (
    None
):
    pool = build_pool([join()], OCCUPATIONS, frozenset({"251"}))

    directions = {c.occupation.title: c.direction for c in pool}
    assert directions["data quality specialist"] is Direction.CLOSE
    assert directions["chief data officer"] is Direction.TRANSFERABLE
    assert directions["data entry clerk"] is Direction.TRANSFERABLE
    shared = {c.occupation.title: c.matches[0].shared_skills for c in pool}
    assert shared["chief data officer"] == 7
