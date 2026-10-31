"""The discovery evaluation cases against the full pinned ESCO release (DIV1-08, TEST1-10).

The subject is the deterministic pipeline: the fixture proposer's queries (each answer text
as a query), English full-text search over all 3,039 occupations, de-duplication and the
slate. It certifies the pipeline and its rules, not a model's queries (those are the live
run's, `tools.live_eval`). Failures are reported by type."""

import json
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from careerwright.capability.commands import committed_data, pack_targets
from careerwright.capability.strength import SCRIPTED_STRENGTHS
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.esco import ESCO_RELEASE
from careerwright.catalogue.reference import DATASETS
from careerwright.catalogue.taxonomy import MAX_REACH, search_essential_skills
from careerwright.cli import import_reference_data, import_taxonomy, migrate_app
from careerwright.db import Tx, system_transaction
from careerwright.profile.records import TargetLink
from careerwright.profile.slate import POOL_LIMIT, POOL_TARGET
from careerwright.profile.targets import resolve_target
from tests.support.infra import Infra, migrator_engine
from tools.datasets import DATASETS_DIR
from tools.evaluation import (
    Case,
    CaseKind,
    Failure,
    evaluate,
    failures_by_type,
    load_cases,
    observe_discovery_offline,
    observe_explanation_offline,
)

pytestmark = pytest.mark.integration
UK_INDEX = next(dataset for dataset in DATASETS if dataset.name == "soc_index")


@pytest.fixture(scope="module")
def full_release(infra: Infra) -> Iterator[sa.Engine]:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    database = f"careerwright_eval_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    migrate_app(owner)
    assert import_taxonomy(owner, release) == "imported"
    # The pinned UK job-title index: a title the index lists is a suggestion beside the slate
    # (ADR 0015 decision 2), and every title's record says whether it lists it.
    index = Path(DATASETS_DIR) / UK_INDEX.pin.file_name
    assert import_reference_data(owner, [(UK_INDEX, index)]) == {"soc_index": "imported"}
    yield owner
    owner.dispose()


@pytest.mark.req("DIV1-08", "TEST1-10", "REC1-09", "REC1-03", "DIV1-06")
def test_every_discovery_case_passes_on_the_full_release(full_release: sa.Engine) -> None:
    cases = [case for case in load_cases() if case.kind is CaseKind.DISCOVERY]
    with system_transaction(full_release) as tx:
        observed = {case.id: observe_discovery_offline(tx, case) for case in cases}

    results: dict[str, list[Failure]] = {
        case.id: evaluate(case, observed[case.id], observed) for case in cases
    }

    print(f"discovery cases: {len(cases)}, failures by type: {failures_by_type(results)}")
    for case_id in ("DSC-01", "DSC-03"):
        shown = [
            (s["title"], s["family"]["code"], s["direction"])
            for s in observed[case_id]["suggestions"]
        ]
        print(f"{case_id}: pool {observed[case_id]['pool_size']}, slate {shown}")
    assert {case_id: failures for case_id, failures in results.items() if failures} == {}
    p02 = observed["DSC-01"]
    # P02's pool stays within the bound. Its soft 60-120 holds only where evidence permits
    # (DIV1-02): since Task W2B fix round 2 a search reaches work only through a skill whose
    # label holds all its words, and work style isn't searched, so only "working outdoors"
    # reaches work (12 occupations). Below the target, the slate says why (DSC-01's
    # `small_pool_has_reason`). The bound itself is exercised on the full release by
    # `test_the_working_pool_keeps_its_bound_and_counts_the_work_beyond_it`.
    assert p02["pool_size"] <= POOL_LIMIT
    if p02["pool_size"] < POOL_TARGET:
        assert {
            "reason": "small_pool",
            "outcome": "found_work",
            "pool_size": p02["pool_size"],
            "pool_target": POOL_TARGET,
        } in p02["notes"]
    assert p02["release"]["sample"] is False  # the real catalogue, not the test subset


def slate_shape(observed: dict[str, Any]) -> dict[str, Any]:
    """Everything a slate chose and why, without its words."""
    return {
        "suggestions": [
            [s["concept_id"], s["title"], s["direction"], s["matched_queries"]]
            for s in observed["suggestions"]
        ],
        "pool_size": observed["pool_size"],
        "beyond_pool_limit": observed["beyond_pool_limit"],
        "not_included": [[n["concept_id"], n["reason"]] for n in observed["not_included"]],
        "unmatched_titles": observed["unmatched_titles"],
        "ambiguous_titles": observed["ambiguous_titles"],
        "connection": observed["connection"]["concept_id"] if observed["connection"] else None,
        "queries": [
            [q["query_id"], q["text"], q["hits"], q["reach"], q["too_general"]]
            for q in observed["queries"]
        ],
    }


# Every discovery case's slate as the code before Task 6d slice A computed it on the full
# release (its suggestions in order, pool, what was left out and why, the person's titles that
# joined nothing, the connection and every search), recorded from commit 86d7ead.
SLATES_BEFORE = Path(__file__).with_name("slates_before_task_6d.json")


@pytest.mark.req("DIV1-06", "DIV1-08", "PROF-10")
def test_every_evaluation_case_s_slate_is_the_one_before_targets_were_stored_once(
    full_release: sa.Engine,
) -> None:
    # Task 6d slice A: the notes became facts and each target is read from its stored
    # record; the slate's ranking, rules and thresholds don't change (R11). Slice B adds a
    # case (DSC-20, title ideas beside the slate); every case recorded before is compared.
    before = json.loads(SLATES_BEFORE.read_text(encoding="utf-8"))
    cases = [case for case in load_cases() if case.kind is CaseKind.DISCOVERY]
    assert set(before) <= {case.id for case in cases}
    with system_transaction(full_release) as tx:
        now = {
            case.id: slate_shape(observe_discovery_offline(tx, case))
            for case in cases
            if case.id in before
        }

    assert now == before


@pytest.mark.req("PROF-10")
@pytest.mark.parametrize(
    ("typed", "label", "preferred"),
    [
        # "&" in ESCO's title, "and" typed: no other label says it with "and".
        ("food and beverage supervisors", "food & beverage supervisor", "restaurant manager"),
        # An accent in ESCO's title, the plain spelling typed.
        ("facade cleaner", "façade cleaner", "building exterior cleaner"),
        ("Dance repetiteurs.", "dance répétiteur", "dance répétiteur"),
    ],
)
def test_a_real_esco_title_with_an_ampersand_or_an_accent_resolves_from_its_plain_spelling(
    full_release: sa.Engine, typed: str, label: str, preferred: str
) -> None:
    pack = pack_targets(committed_data())
    with system_transaction(full_release) as tx:
        record = resolve_target(tx, uuid.uuid4(), typed, pack)
        holders = taxonomy_store.label_match_uris(tx, label)
        found = tx.execute(
            sa.text(
                "SELECT preferred_label FROM careerwright.occupation_concepts WHERE esco_uri = :uri"
            ),
            {"uri": record.occupation_uri},
        ).scalar_one()

    assert len(holders) == 1  # ESCO's own title, of one occupation
    assert (record.link, record.label_matches) == (TargetLink.EXACT_LABEL, tuple(holders))
    assert found == preferred


def found_none_reading(answer: str) -> dict[str, Any]:
    """An answer searched in its own words that read the main names of essential skills and
    found none holding all its words: the web says that, never what ESCO holds."""
    return {
        "reason": "answer_found_no_work",
        "outcome": "found_none",
        "answer": answer,
        "own_words": True,
        "searches": [{"text": answer, "did": "read_main_names"}],
        "min_shared": 3,
    }


def observed_for(tx: Tx, profile: dict[str, Any]) -> dict[str, Any]:
    """The offline slate for a profile that is not one of the reviewed cases."""
    case = Case(
        id="ad hoc",
        kind=CaseKind.DISCOVERY,
        title="ad hoc",
        requirements=[],
        synthetic=True,
        profile=profile,
        expect=[],
    )
    return observe_discovery_offline(tx, case)


@pytest.mark.req("DIV1-02", "DIV1-06")
def test_a_search_keeps_all_the_work_one_skill_reaches_so_no_tie_is_cut_by_title(
    full_release: sa.Engine,
) -> None:
    # Task W2B re-review I-B: "planning shifts" reached 58 occupations through one essential
    # skill, so all 58 tied; a search kept its first 30 by title, so the warehouse worker,
    # which "stacking goods" reaches too, never met it. Since fix round 3 "planning shifts" is
    # too general to find work on its own (more than 50 occupations), so the same case is
    # "stocking shelves": 44 occupations through "stock shelves". The ticket issuing clerk,
    # 42nd by title, is the one "upselling products" reaches too.
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"confident_tasks": ["stocking shelves", "upselling products"]})

    hits = {q["text"]: q["hits"] for q in slate["queries"]}
    first = slate["suggestions"][0]
    assert hits["stocking shelves"] == 44  # every occupation it reaches, within the pool bound
    assert first["title"] == "ticket issuing clerk"
    assert {e["text"] for e in first["linked_evidence"]} == {
        "stocking shelves",
        "upselling products",
    }


@pytest.mark.req("DIV1-02", "DIV1-06")
def test_a_search_never_cuts_inside_a_tie(full_release: sa.Engine) -> None:
    # Task W2B re-review 2, N-M1: "stocking shelves" reaches 44 occupations, all through
    # "stock shelves", so they tie on rank and order by the share of their essential skills:
    # 1 of 8, 1 of 22, then two with 1 of 27 each. A cut after 3 keeps both of those.
    with system_transaction(full_release) as tx:
        cut = search_essential_skills(tx, "stocking shelves", 3)
        whole = search_essential_skills(tx, "stocking shelves", MAX_REACH)

    assert cut.total == whole.total == 44
    assert [r.concept_id for r in cut.reached] == [r.concept_id for r in whole.reached[:4]]
    assert (cut.skills, cut.exact) == (1, True)  # one skill, named exactly by its words


@pytest.mark.req("DIV1-06", "DIV1-08")
def test_a_hyphen_in_a_search_is_read_as_a_space(full_release: sa.Engine) -> None:
    # Task W2C (W2B re-review 5's hyphen check): PostgreSQL's English parser keeps
    # "first-aid" whole beside its parts, so its query also needs the lexeme "first-aid",
    # which no skill named with "first aid" holds, and "first-aid" found no work. A hyphen
    # in the search is now read as a space before the search; nothing else changes.
    with system_transaction(full_release) as tx:
        parsed = tx.execute(
            sa.text("SELECT plainto_tsquery('english', 'first-aid')::text")
        ).scalar_one()
        hyphen = search_essential_skills(tx, "first-aid", MAX_REACH)
        space = search_essential_skills(tx, "first aid", MAX_REACH)

    assert parsed == "'first-aid' & 'first' & 'aid'"  # the case, as the database parses it
    assert "provide first aid" in {r.skill_label for r in hyphen.reached}
    assert (hyphen.total, hyphen.skills, hyphen.exact) == (space.total, space.skills, space.exact)
    assert [r.concept_id for r in hyphen.reached] == [r.concept_id for r in space.reached]


@pytest.mark.req("DIV1-02")
def test_the_working_pool_keeps_its_bound_and_counts_the_work_beyond_it(
    full_release: sa.Engine,
) -> None:
    # Four specific searches together reach 178 occupations (each 44 to 48, through one
    # skill), more than the pool holds, so it is cut across families and the rest counted
    # (DIV1-02). Fix round 3: the two general searches this test used ("maintaining
    # equipment", 242; "planning shifts", 58) no longer find work on their own.
    tasks = [
        "stocking shelves",
        "processing payments",
        "interpreting 2D plans",
        "analysing test data",
    ]
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"confident_tasks": tasks})

    queries = slate["queries"]
    assert [(q["hits"], q["too_general"]) for q in queries] == [
        (44, False),
        (48, False),
        (45, False),
        (44, False),
    ]
    assert all(q["hits"] == q["reach"] for q in queries)  # a search that can find work keeps all
    assert slate["pool_size"] == POOL_LIMIT
    assert slate["beyond_pool_limit"] == 178 - POOL_LIMIT


@pytest.mark.req("DIV1-06", "DIV1-08")
@pytest.mark.parametrize(
    ("answer", "by", "count"),
    [
        ("solving problems", "occupations", 77),
        ("writing reports", "occupations", 217),
        ("working in a team", "occupations", 242),
        ("training staff", "skills", 10),
        ("analysing data", "occupations", 92),
    ],
)
def test_an_answer_too_general_to_find_work_alone_finds_none_and_says_why(
    full_release: sa.Engine, answer: str, by: str, count: int
) -> None:
    # Task W2B re-review 2, N-I2: each scattered its slate across unrelated work ("writing
    # reports": an ambulance driver, a chiropractor, a city councillor, a lieutenant).
    # Re-review 3, I1: the note says what was counted, essential skills only. Re-review 4,
    # I1: it says what the search did, the main names it read, never what ESCO holds.
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"enjoyed_tasks": [answer]})

    assert slate["suggestions"] == []
    [query] = slate["queries"]
    assert query["too_general"]
    [note] = [note for note in slate["notes"] if note["reason"] == "too_general"]
    assert (note["search"], note["answers"], note["own_words"], note["by"]) == (
        answer,
        [answer],
        True,
        by,
    )
    assert note[by] == count
    assert note["narrower_for"] == []  # the answer's own words: say more about it instead


@pytest.mark.req("DIV1-06", "DIV1-08")
def test_an_answer_naming_a_skill_no_occupation_lists_as_essential_is_named_for_what_was_checked(
    full_release: sa.Engine,
) -> None:
    # Task W2B re-review 3, I1: ESCO names "take pictures" but lists it as essential for no
    # occupation (optional for two), so "taking pictures" finds no work, and the slate said
    # "isn't how ESCO names any skill", which is untrue.
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"enjoyed_tasks": ["taking pictures"]})

    assert slate["suggestions"] == []
    assert [(q["text"], q["reach"]) for q in slate["queries"]] == [("taking pictures", 0)]
    assert found_none_reading("taking pictures") in slate["notes"]


@pytest.mark.req("DIV1-06", "DIV1-08")
def test_an_answer_that_is_another_name_of_an_essential_skill_is_named_for_what_was_read(
    full_release: sa.Engine,
) -> None:
    # Task W2B re-review 4, I1: "operating farm machinery" is ESCO's other name for "operate
    # agricultural machinery", essential for 8 occupations. A search reads main names only,
    # so it finds no work, and the slate said it "isn't part of any skill ESCO lists as
    # essential", which is untrue. It now says what the search read, and that holds.
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"enjoyed_tasks": ["operating farm machinery"]})
        other_name = tx.execute(
            sa.text(
                "SELECT count(DISTINCT r.concept_id) FROM careerwright.skill_labels l "
                "JOIN careerwright.occupation_skills r ON r.skill_id = l.skill_id "
                "AND r.relation = 'essential' "
                "WHERE l.kind = 'alternative' AND l.normalised = 'operating farm machinery'"
            )
        ).scalar_one()
        # Independent of the search: a word starting as each of its words does, which holds
        # at least every word the English stems would match.
        main_names = tx.execute(
            sa.text(
                "SELECT count(*) FROM careerwright.skills s WHERE s.preferred_label ~* '\\moper' "
                "AND s.preferred_label ~* '\\mfarm' AND s.preferred_label ~* '\\mmachin' "
                "AND EXISTS (SELECT 1 FROM careerwright.occupation_skills r "
                "WHERE r.skill_id = s.skill_id AND r.relation = 'essential')"
            )
        ).scalar_one()

    assert other_name == 8  # the case: ESCO's other name for an essential skill
    assert main_names == 0  # the note's words hold
    assert slate["suggestions"] == []
    assert [(q["text"], q["reach"]) for q in slate["queries"]] == [("operating farm machinery", 0)]
    assert found_none_reading("operating farm machinery") in slate["notes"]


@pytest.mark.req("DIV1-06", "DIV1-08")
def test_a_general_answer_adds_weight_to_all_the_work_another_answer_found(
    full_release: sa.Engine,
) -> None:
    # Task W2B fix round 3 (found while checking DSC-19): "writing reports" reaches 217
    # occupations and kept its best 127, which leave out the nursery school head teacher
    # ("write work-related reports"), so the one occupation both answers reach lost the
    # general answer's weight. It now adds to every occupation another search found.
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"enjoyed_tasks": ["caring for children", "writing reports"]})

    first = slate["suggestions"][0]
    assert first["title"] == "nursery school head teacher"
    assert {e["text"] for e in first["linked_evidence"]} == {
        "caring for children",
        "writing reports",
    }
    reports = next(q for q in slate["queries"] if q["text"] == "writing reports")
    assert (reports["hits"], reports["reach"], reports["too_general"]) == (1, 217, True)


@pytest.mark.req("REC1-03", "DIV1-10", "DIV1-12")
def test_where_someone_likes_to_work_is_searched_and_a_specific_answer_s_work_comes_first(
    full_release: sa.Engine,
) -> None:
    # Task W2B re-review 2: N-I3, "working outdoors" as how someone likes to work reaches
    # work through "work in outdoor conditions", while the one-word "structured" is not
    # searched; N-M4, the bicycle mechanic, the only work "repairing bicycles" reaches, comes
    # before the 12 outdoor occupations. Re-review 3, M3: both answers are how someone likes
    # to work, so both search in one channel and score alike; by the share of essential
    # skills alone the leaflet distributor (1 of 6) would come before the bicycle mechanic
    # (1 of 13).
    profile = {"work_style": ["repairing bicycles", "working outdoors", "structured"]}
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, profile)

    assert {q["text"]: q["hits"] for q in slate["queries"]} == {
        "repairing bicycles": 1,
        "working outdoors": 12,
    }
    assert slate["suggestions"][0]["title"] == "bicycle mechanic"
    assert any(reason.get("skill") == "work in outdoor conditions"
               for s in slate["suggestions"][1:] for reason in s["reasons"])  # fmt: skip
    [style] = [note for note in slate["notes"] if note["reason"] == "one_word_work_style"]
    assert style["answers"] == ["structured"]


@pytest.mark.req("BND1-11")
def test_the_demo_s_scripted_strengths_are_essential_esco_skills_named_as_esco_names_them(
    full_release: sa.Engine,
) -> None:
    # The scripted demo strength finds its skill in the prompt by ESCO's label for its URI;
    # each is essential to at least one occupation.
    with system_transaction(full_release) as tx:
        rows = tx.execute(
            sa.text(
                "SELECT DISTINCT s.esco_uri, s.preferred_label FROM careerwright.skills s "
                "JOIN careerwright.occupation_skills r "
                "ON r.skill_id = s.skill_id AND r.relation = 'essential' "
                "WHERE s.esco_uri = ANY(CAST(:uris AS text[]))"
            ),
            {"uris": [s.skill_uri for s in SCRIPTED_STRENGTHS]},
        ).mappings()
        found = {row["esco_uri"]: row["preferred_label"] for row in rows}

    assert found == {s.skill_uri: s.skill_label for s in SCRIPTED_STRENGTHS}


@pytest.mark.req("REC1-11", "TEST1-10")
def test_every_explanation_case_passes_on_the_full_release(full_release: sa.Engine) -> None:
    # The fixture explainer over real ESCO records: the prompt fits its bound, every
    # quotation is a span of the record or the answers, and the API shape holds.
    cases = [case for case in load_cases() if case.kind is CaseKind.EXPLANATION]
    with system_transaction(full_release) as tx:
        observed = {case.id: observe_explanation_offline(tx, case) for case in cases}

    results = {case.id: evaluate(case, observed[case.id], observed) for case in cases}

    print(f"explanation cases: {len(cases)}, failures by type: {failures_by_type(results)}")
    assert cases
    assert {case_id: failures for case_id, failures in results.items() if failures} == {}
