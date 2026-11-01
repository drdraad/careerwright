"""The discovery pool and slate (S2.4; DIV-1, REC-1): de-duplicate before counting
diversity, keep a relevance floor, prefer a varied slate with a soft family limit, return
fewer with the reason, and never let a preference or a view filter remove work silently.
Hand-built candidates; no database."""

import uuid

import pytest

from careerwright.catalogue.records import IscoGroupRef, OccupationFacts
from careerwright.profile.discovery import DiscoveryQuery, EvidenceItem, QueryChannel
from careerwright.profile.exploration import (
    _general_note,
    _join_note,
    _missed_notes,
    explain,
)
from careerwright.profile.interview import ProfileField
from careerwright.profile.slate import (
    FAMILY_LIMIT,
    FURTHER_QUERY_BONUS,
    POOL_LIMIT,
    SLATE_SIZE,
    TOO_GENERAL_OCCUPATIONS,
    TOO_GENERAL_SKILLS,
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
    too_general,
)
from careerwright.profile.slate_facts import (
    AnswerFoundNoWork,
    AnswerSearch,
    CastingWider,
    ExclusionsRemoved,
    FewMatched,
    JoinKeptBest,
    KindsOfWorkShown,
    MoreDepth,
    NothingFound,
    OneWordWorkStyle,
    Outcome,
    OwnTitleMatched,
    SearchDid,
    SearchedThroughSkill,
    TitleIdeaMatched,
    TooGeneral,
    TooGeneralBy,
)

ENJOY = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="repairing physical objects")
ROLE = EvidenceItem(field=ProfileField.CURRENT_ROLE, text="Warehouse supervisor")


def concept(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"test:{name}")


def occupation(name: str, family: str, *aliases: str, essential: int = 20) -> Occupation:
    return Occupation(
        concept_id=concept(name),
        title=name,
        family_code=family,
        family_label=f"Family {family}",
        sector_code=family[0],
        preferred_key=name.casefold(),
        label_keys=frozenset({name.casefold(), *(a.casefold() for a in aliases)}),
        essential_skills=essential,
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


def facts_of(o: Occupation) -> OccupationFacts:
    family = IscoGroupRef(o.family_code, o.family_label)
    return OccupationFacts(
        concept_id=o.concept_id,
        preferred_label=o.title,
        esco_uri=f"http://data.europa.eu/esco/occupation/{o.concept_id}",
        esco_code=f"{o.family_code}0.1",
        description="",
        regulated=False,
        unit=family,
        family=family,
        sector=IscoGroupRef(o.sector_code, f"Sector {o.sector_code}"),
        preferred_key=o.preferred_key,
        label_keys=o.label_keys,
        essential_skills=(),
        essential_skill_count=0,
    )


@pytest.mark.req("DIV1-05", "DIV1-08")
def test_a_why_line_never_names_a_near_identical_role_s_skill_as_this_one_s() -> None:
    # Task W2B re-review I-A, ESCO v1.2.1's own case: the sound editor lists "sound designer"
    # as one of its titles, so the two fold into one suggestion. "Attend music recording
    # sessions" is essential to the sound editor and not to the sound designer, so the sound
    # designer's words may not say ESCO lists it for this work.
    mixing = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="mixing recordings")
    attending = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="attending recording sessions")
    sound = {
        o.concept_id: o
        for o in (
            occupation("sound designer", "352"),
            occupation("sound editor", "352", "sound designer"),
        )
    }
    queries = [
        PoolQuery(
            "q1",
            "mixing recordings",
            SlateChannel.TASKS,
            (mixing,),
            (Hit(concept("sound designer"), 1.0, False, skill="mix multi-track recordings"),),
        ),
        PoolQuery(
            "q2",
            "attending recording sessions",
            SlateChannel.TASKS,
            (attending,),
            (Hit(concept("sound editor"), 0.9, False, skill="attend music recording sessions"),),
        ),
    ]

    pool = build_pool(queries, sound, frozenset())

    [lead] = [c for c in pool if c.duplicate_of is None]
    assert lead.occupation.title == "sound designer"
    reasons = explain(lead, facts_of(lead.occupation), familiarity_known=False).reasons
    assert reasons == [
        SearchedThroughSkill(
            field=ProfileField.ENJOYED_TASKS,
            answer="mixing recordings",
            search="mixing recordings",
            skill="mix multi-track recordings",
        )
    ]


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


@pytest.mark.req("DIV1-02", "DIV1-06")
def test_equal_matches_go_to_the_larger_share_of_essential_skills_never_to_the_title() -> None:
    # Task W2B re-review I-B: every occupation a search reaches through the same skill ties
    # on its rank. The tie goes to the one whose essential skills the person's answers reach
    # the larger share of (the skill is a bigger part of that work), the title only last, in
    # the pool and on the slate. A skill reached twice counts once. (ESCO v1.2.1's counts for
    # "stocking shelves", through "stock shelves"; fix round 3 replaced "planning shifts",
    # now too general to find work on its own.)
    stock = uuid.uuid5(uuid.NAMESPACE_URL, "test:stock shelves")
    tied = {
        o.concept_id: o
        for o in (
            occupation("Merchandiser", "524", essential=27),
            occupation("Ticket issuing clerk", "421", essential=42),
            occupation("Shelf filler", "933", essential=8),
        )
    }

    def reached(*names: str) -> tuple[Hit, ...]:
        return tuple(
            Hit(concept(name), 1.0, False, skill="stock shelves", skills=frozenset({stock}))
            for name in names
        )

    shelves = PoolQuery(
        "q1",
        "stocking shelves",
        SlateChannel.TASKS,
        (ENJOY,),
        reached("Merchandiser", "Ticket issuing clerk", "Shelf filler"),
    )
    again = PoolQuery("q2", "stock shelves", SlateChannel.TASKS, (ENJOY,), reached("Shelf filler"))

    pool = build_pool([shelves], tied, frozenset())
    chosen = choose_slate(pool)

    by_share = ["Shelf filler", "Merchandiser", "Ticket issuing clerk"]
    assert [c.occupation.title for c in pool] == by_share  # 1 of 8, 1 of 27, 1 of 42
    assert [c.occupation.title for c in chosen.suggestions] == by_share
    twice = {c.occupation.title: c.share for c in build_pool([shelves, again], tied, frozenset())}
    assert twice["Shelf filler"] == 1 / 8


OUTDOORS = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="working outdoors")
BICYCLES = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="repairing bicycles")
REPORTS = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="writing reports")


def through(skill: str, *names: str) -> tuple[Hit, ...]:
    """Every occupation a search reached through one skill: all tie on its rank."""
    reached = frozenset({uuid.uuid5(uuid.NAMESPACE_URL, f"test:{skill}")})
    return tuple(Hit(concept(name), 1.0, False, skill=skill, skills=reached) for name in names)


@pytest.mark.req("DIV1-06", "DIV1-12")
def test_work_a_specific_answer_found_comes_before_work_a_general_one_found() -> None:
    # Task W2B re-review 2, N-M4: "repairing bicycles" reaches 1 occupation and "working
    # outdoors" 12, and each search's best scores 1, so the share of essential skills put the
    # leaflet distributor (6 essential skills) before the bicycle mechanic (30). How specific
    # the search that reached it was now comes first.
    found = {
        o.concept_id: o
        for o in (
            occupation("Bicycle mechanic", "723", essential=30),
            occupation("Leaflet distributor", "962", essential=6),
            occupation("Fruit picker", "921", essential=7),
        )
    }
    queries = [
        PoolQuery(
            "q1",
            "repairing bicycles",
            SlateChannel.TASKS,
            (BICYCLES,),
            through("perform repairs on bicycles", "Bicycle mechanic"),
        ),
        PoolQuery(
            "q2",
            "working outdoors",
            SlateChannel.TASKS,
            (OUTDOORS,),
            through("work in outdoor conditions", "Leaflet distributor", "Fruit picker"),
            total=12,
        ),
    ]

    pool = build_pool(queries, found, frozenset())

    assert next(iter(pool)).occupation.title == "Bicycle mechanic"
    assert {c.occupation.title: c.reach for c in pool} == {
        "Bicycle mechanic": 1,
        "Leaflet distributor": 12,
        "Fruit picker": 12,
    }
    assert choose_slate(pool).suggestions[0].occupation.title == "Bicycle mechanic"


@pytest.mark.req("DIV1-06", "DIV1-08")
def test_a_search_too_general_to_find_work_alone_only_adds_weight_to_work_another_found() -> None:
    # Task W2B re-review 2, N-I2 (provisional thresholds): "writing reports" reaches 217
    # occupations through 17 skills, so on its own it scattered the slate across ambulance
    # drivers, chiropractors and city councillors.
    assert too_general(TOO_GENERAL_OCCUPATIONS + 1, 1, exact=True)  # "writing reports": 217
    assert too_general(17, TOO_GENERAL_SKILLS + 1, exact=False)  # "training staff": 10 skills
    assert not too_general(12, 8, exact=True)  # "selling products": "sell products" is exact
    assert not too_general(TOO_GENERAL_OCCUPATIONS, TOO_GENERAL_SKILLS, exact=False)
    found = {
        o.concept_id: o
        for o in (
            occupation("Bicycle mechanic", "723"),
            occupation("Chiropractor", "226"),
            occupation("City councillor", "111"),
        )
    }
    bicycles = PoolQuery(
        "q1",
        "repairing bicycles",
        SlateChannel.TASKS,
        (BICYCLES,),
        through("perform repairs on bicycles", "Bicycle mechanic"),
    )
    reports = PoolQuery(
        "q2",
        "writing reports",
        SlateChannel.TASKS,
        (REPORTS,),
        (
            *through("write work-related reports", "Bicycle mechanic", "City councillor"),
            *through("write reports on neurological tests", "Chiropractor"),
        ),
        total=217,
        too_general=True,
    )

    alone = build_pool([reports], found, frozenset())
    both = build_pool([bicycles, reports], found, frozenset())

    assert list(alone) == []
    assert alone.beyond_limit == 0  # not kept because too general, never past the bound
    [mechanic] = both
    assert mechanic.occupation.title == "Bicycle mechanic"
    assert [m.query.query_id for m in mechanic.matches] == ["q1", "q2"]
    assert mechanic.relevance == 1.0 + FURTHER_QUERY_BONUS
    assert mechanic.reach == 1  # the search that found it, not the general one
    assert choose_slate(alone).fewer_reasons == [NothingFound()]
    # It adds only that little: its own score never becomes the best, so it never lifts a
    # weak match over the relevance floor.
    weakly = PoolQuery(
        "q3",
        "adjusting spines",
        SlateChannel.TASKS,
        (BICYCLES,),
        (Hit(concept("Chiropractor"), 0.3, False, skill="adjust spines"),),
    )
    lifted = {c.occupation.title: c for c in build_pool([weakly, reports], found, frozenset())}
    assert lifted["Chiropractor"].relevance == 0.3 + FURTHER_QUERY_BONUS
    assert lifted["Chiropractor"].best_score == 0.3
    [left] = choose_slate(build_pool([weakly, reports], found, frozenset())).not_included
    assert left.reason is NotIncluded.BELOW_RELEVANCE_FLOOR


def searched(
    query_id: str, text: str, *based_on: EvidenceItem, reach: int = 0, general: bool = False
) -> PoolQuery:
    """A search as the notes read it: its words, the answers it cites and how many
    occupations it reached."""
    channel = SlateChannel.TASKS
    return PoolQuery(query_id, text, channel, based_on, (), total=reach, too_general=general)


# What each of an answer's searches did (`SearchDid`): the web words them, saying what the
# search did, never what ESCO holds (Task W2B re-review 4; Task 6d slice A).
READ = SearchDid.READ_MAIN_NAMES
COMMON = SearchDid.ONLY_COMMON_WORDS
JOINED = SearchDid.NO_SHARED_OCCUPATION


def found_none(answer: str, *searches: tuple[str, SearchDid], own: bool) -> AnswerFoundNoWork:
    return AnswerFoundNoWork(
        answer=answer,
        own_words=own,
        searches=[AnswerSearch(text=text, did=did) for text, did in searches],
        min_shared=3,
    )


@pytest.mark.req("DIV1-06", "DIV1-10")
def test_the_notes_say_what_a_model_s_searches_checked_and_which_answers_found_no_work() -> None:
    # Task W2B re-review 3: M2, a model may write several searches from one answer, or one
    # from a task and a one-word work style, and no product test read those notes; I1, "isn't
    # how ESCO names any skill" was untrue where ESCO names the skill but lists it as
    # essential for no occupation ("take pictures"); M1, a model's search too general asked
    # the person to say more about an answer that was already specific. Re-review 4: I1,
    # "isn't part of any skill ESCO lists as essential" was untrue where the words are another
    # name of an essential skill ("operating farm machinery"), since a search reads main names
    # only; M1, a model's search too general asked for a narrower search from an answer
    # another search had already found work from.
    fixing = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="fixing things")
    tidying = EvidenceItem(field=ProfileField.CONFIDENT_TASKS, text="tidying stockrooms")
    practical = EvidenceItem(field=ProfileField.WORK_STYLE, text="practical")
    pictures = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="taking pictures")
    bridges = EvidenceItem(
        field=ProfileField.EVIDENCED_TASKS, text="writing inspection reports for bridges"
    )
    staff = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="training staff")
    model = [
        searched("q1", "repair machinery", fixing),
        searched("q2", "fix equipment", fixing),
        searched("q3", "organise stock", tidying, practical),
        searched("q4", "taking pictures", pictures),  # the answer's own words
    ]

    assert _missed_notes(model, [], ["structured"], frozenset()) == [
        OneWordWorkStyle(answers=["structured", "practical"]),
        found_none("fixing things", ("repair machinery", READ), ("fix equipment", READ), own=False),
        found_none("tidying stockrooms", ("organise stock", READ), own=False),
        found_none("taking pictures", ("taking pictures", READ), own=True),
    ]
    # Named only when none of the searches citing it found anything.
    one_found = [model[0], searched("q2", "fix equipment", fixing, reach=3)]
    assert _missed_notes(one_found, [], [], frozenset()) == []
    # A one-word style a search found work with is named nowhere, like the task beside it.
    stock = searched("q3", "organise stock", tidying, practical, reach=4)
    assert _missed_notes([stock], [], [], frozenset()) == []

    reports = searched("q5", "write reports", bridges, reach=217, general=True)
    bridge_reports = "writing inspection reports for bridges"
    by_reach = {"search": "write reports", "answers": [bridge_reports], "own_words": False}
    assert _general_note(reports, 17, [reports]) == TooGeneral(
        **by_reach,
        by=TooGeneralBy.OCCUPATIONS,
        occupations=217,
        skills=17,
        narrower_for=[bridge_reports],
    )
    # Another search from the same answer found work, so no narrower search is called for.
    inspection = searched("q7", "write inspection reports", bridges, reach=6)
    assert _general_note(reports, 17, [reports, inspection]) == TooGeneral(
        **by_reach, by=TooGeneralBy.OCCUPATIONS, occupations=217, skills=17, narrower_for=[]
    )
    general = searched("q6", "training staff", staff, reach=17, general=True)
    # The answer's own words: the person is asked to say more, never for a narrower search.
    assert _general_note(general, 10, [general]) == TooGeneral(
        search="training staff",
        answers=["training staff"],
        own_words=True,
        by=TooGeneralBy.SKILLS,
        occupations=17,
        skills=10,
        narrower_for=[],
    )


@pytest.mark.req("DIV1-06")
def test_an_answer_whose_searches_read_no_skill_name_is_named_for_what_they_did() -> None:
    # Task W2B re-review 4, I1: a note says what each search did. A search of only common
    # words reads nothing, and a model's search naming the person's own title is answered by
    # the title's skill join, so neither may be said to have read a skill's name.
    everything = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="all of it")
    fixing = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="fixing things")

    def common(query_id: str, text: str, item: EvidenceItem) -> DiscoveryQuery:
        return DiscoveryQuery(
            query_id=query_id, text=text, channel=QueryChannel.TASKS, based_on=[item]
        )

    assert _missed_notes([], [common("q1", "all of it", everything)], [], frozenset()) == [
        found_none("all of it", ("all of it", COMMON), own=True)
    ]
    role = searched("q3", "warehouse manager", fixing)  # the person's role: joined, never read
    assert _missed_notes(
        [searched("q2", "repair machinery", fixing), role],
        [common("q4", "the other", fixing)],
        [],
        frozenset({"q3"}),
    ) == [
        found_none(
            "fixing things",
            ("repair machinery", READ),
            ("the other", COMMON),
            ("warehouse manager", JOINED),
            own=False,
        )
    ]


@pytest.mark.req("REC1-05", "DIV1-06")
def test_a_title_of_the_person_s_own_says_careerwright_matched_it() -> None:
    # Task W2B re-review 4, I1's rule: "ESCO lists it as this occupation" claimed ESCO holds
    # the person's words, though a title is matched with case, punctuation and plurals folded
    # ("Warehouse managers"); the line says what Careerwright did.
    role = EvidenceItem(field=ProfileField.CURRENT_ROLE, text="Warehouse managers")
    query = PoolQuery(
        "r1",
        role.text,
        SlateChannel.CURRENT,
        (role,),
        (Hit(concept("Warehouse manager"), 1.0, label_match=True),),
    )
    [candidate] = build_pool([query], OCCUPATIONS, frozenset())

    reasons = explain(candidate, facts_of(candidate.occupation), familiarity_known=True).reasons

    assert reasons == [
        OwnTitleMatched(field=ProfileField.CURRENT_ROLE, answer="Warehouse managers")
    ]
    assert reasons[0].outcome is Outcome.MATCHED


@pytest.mark.req("REC1-05", "DIV1-06")
def test_a_title_idea_names_the_idea_and_says_careerwright_matched_it() -> None:
    # Task W2B re-review 5, I1: "Careerwright thought of this title from it, and ESCO lists
    # it" was untrue where the idea matched another of the occupation's titles: a model's
    # "dog groomer" shows as the card "Animal groomer". The line names the idea and says what
    # the match did.
    groomer = occupation("Animal groomer", "516", "dog groomer")
    dogs = EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="looking after dogs")
    idea = PoolQuery(
        "h1",
        "dog groomer",
        SlateChannel.HYPOTHESIS,
        (dogs,),
        (Hit(groomer.concept_id, 1.0, label_match=True),),
    )
    [candidate] = build_pool([idea], {groomer.concept_id: groomer}, frozenset())

    reasons = explain(candidate, facts_of(groomer), familiarity_known=False).reasons

    assert reasons == [
        TitleIdeaMatched(
            field=ProfileField.ENJOYED_TASKS, answer="looking after dogs", title="dog groomer"
        )
    ]


@pytest.mark.req("DIV1-02")
def test_the_pool_counts_what_a_join_reached_past_its_cut_and_its_own_bound() -> None:
    # Task W2B re-review 2, N-M2: "data analyst" joins 47 occupations by three or more shared
    # skills and keeps its best 30, so the slate said it chose from 31 and that nothing more
    # was found. What a join reached past its cut is now counted, once, unless another
    # search found it.
    found = {
        o.concept_id: o
        for o in (
            occupation("Data scientist", "251"),
            occupation("Chief data officer", "133"),
            occupation("Statistician", "212"),
        )
    }
    cut = frozenset({concept("Statistician"), concept("Data entry clerk"), concept("Archivist")})
    joined = PoolQuery(
        "j1",
        "data analyst",
        SlateChannel.SHARED_SKILLS,
        (ROLE,),
        hits(("Data scientist", 1.0), ("Chief data officer", 0.5)),
        total=5,
        unkept=cut,
    )
    statistics = PoolQuery(
        "q1",
        "applying statistics",
        SlateChannel.TASKS,
        (ENJOY,),
        through("apply statistical analysis techniques", "Statistician"),
    )

    assert build_pool([joined], found, frozenset()).beyond_limit == 3
    assert build_pool([joined, statistics], found, frozenset()).beyond_limit == 2
    # Task W2B re-review 3, I2: the join keeps the largest share of essential skills in
    # common, not the most shared skills (P03's join keeps a live chat operator sharing 5 and
    # leaves out a ticket issuing clerk sharing 7). Re-review 4, I1's rule: it says what
    # Careerwright found, never what ESCO holds.
    assert _join_note(joined) == JoinKeptBest(title="data analyst", found=5, kept=2, min_shared=3)
    # A search that can find work reaches at most this many, under the pool's bound, so it
    # keeps everything it reaches and the count needs no "at least".
    assert TOO_GENERAL_OCCUPATIONS < POOL_LIMIT


@pytest.mark.req("DIV1-06")
def test_a_thin_pool_returns_fewer_with_the_reason_never_filler() -> None:
    thin = [
        pool_query("q1", SlateChannel.TASKS, ("Bicycle mechanic", 1.0), ("Tree surgeon", 0.1)),
    ]

    chosen = slate(thin)

    assert [s.occupation.title for s in chosen.suggestions] == ["Bicycle mechanic"]
    assert chosen.fewer_reasons == [FewMatched(count=1)]  # said why, as a fact
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
    assert deeper.notes == [MoreDepth(family_limit=4)]  # the relaxation is stated, never silent
    assert default.fewer_reasons == [
        FewMatched(count=3),
        KindsOfWorkShown(count=1, family_limit=FAMILY_LIMIT),
    ]
    broad = slate(narrow, SlateControls(emphasis=Emphasis.BROAD))
    assert broad.notes == [CastingWider()]
    without = slate(
        narrow, SlateControls(exclude_concepts=frozenset({concept("Bicycle mechanic")}))
    )
    assert without.fewer_reasons == [FewMatched(count=2), ExclusionsRemoved(count=1)]


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
