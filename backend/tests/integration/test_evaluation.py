"""The discovery evaluation cases against the full pinned ESCO release (DIV1-08, TEST1-10).

The subject is the deterministic pipeline: the fixture proposer's queries (each answer text
as a query), English full-text search over all 3,039 occupations, de-duplication and the
slate. It certifies the pipeline and its rules, not a model's queries (those are the live
run's, `tools.live_eval`). Failures are reported by type."""

import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from careerwright.capability.strength import SCRIPTED_STRENGTHS
from careerwright.catalogue.esco import ESCO_RELEASE
from careerwright.catalogue.taxonomy import MAX_REACH, search_essential_skills
from careerwright.cli import import_taxonomy, migrate_app
from careerwright.db import Tx, system_transaction
from careerwright.profile.slate import POOL_LIMIT, POOL_TARGET
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


@pytest.fixture(scope="module")
def full_release(infra: Infra) -> Iterator[sa.Engine]:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    database = f"careerwright_eval_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    migrate_app(owner)
    assert import_taxonomy(owner, release) == "imported"
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
        assert any(f"from {p02['pool_size']} occupations" in note for note in p02["notes"])
    assert p02["release"]["sample"] is False  # the real catalogue, not the test subset


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
    ("answer", "reach"),
    [
        ("solving problems", "77 occupations"),
        ("writing reports", "217 occupations"),
        ("working in a team", "242 occupations"),
        ("training staff", "10 different ESCO skills"),
        ("analysing data", "92 occupations"),
    ],
)
def test_an_answer_too_general_to_find_work_alone_finds_none_and_says_why(
    full_release: sa.Engine, answer: str, reach: str
) -> None:
    # Task W2B re-review 2, N-I2: each scattered its slate across unrelated work ("writing
    # reports": an ambulance driver, a chiropractor, a city councillor, a lieutenant).
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"enjoyed_tasks": [answer]})

    assert slate["suggestions"] == []
    [query] = slate["queries"]
    assert query["too_general"]
    assert any(f"“{answer.capitalize()}” is part of {reach}" in note for note in slate["notes"])


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
    # before the 12 outdoor occupations.
    profile = {
        "enjoyed_tasks": ["repairing bicycles"],
        "work_style": ["working outdoors", "structured"],
    }
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, profile)

    assert {q["text"]: q["hits"] for q in slate["queries"]} == {
        "repairing bicycles": 1,
        "working outdoors": 12,
    }
    assert slate["suggestions"][0]["title"] == "bicycle mechanic"
    assert any("ESCO lists “work in outdoor conditions”" in line
               for s in slate["suggestions"][1:] for line in s["why_it_could_suit"])  # fmt: skip
    [style] = [note for note in slate["notes"] if "How you like to work" in note]
    assert "“structured”" in style
    assert "“working outdoors”)" not in style


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
