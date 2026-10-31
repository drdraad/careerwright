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
    # Task W2B re-review I-B: "planning shifts" reaches 58 occupations through one essential
    # skill ("plan shifts of employees"), so all 58 tie. A search kept its first 30 by title
    # (bricklaying supervisor to laundry and dry cleaning manager), so the warehouse worker,
    # which "stacking goods" reaches too, never met it, and the slate began alphabetically.
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"confident_tasks": ["planning shifts", "stacking goods"]})

    hits = {q["text"]: q["hits"] for q in slate["queries"]}
    first = slate["suggestions"][0]
    assert hits["planning shifts"] == 58  # every occupation it reaches, within the pool bound
    assert first["title"] == "warehouse worker"
    assert {e["text"] for e in first["linked_evidence"]} == {"planning shifts", "stacking goods"}


@pytest.mark.req("DIV1-02")
def test_the_working_pool_keeps_its_bound_and_counts_the_work_beyond_it(
    full_release: sa.Engine,
) -> None:
    # "Maintaining equipment" alone reaches 242 occupations through 74 essential skills; a
    # search keeps the pool's bound of them, and two searches together reach more than the
    # pool holds, so it is cut across families and the rest counted (DIV1-02).
    with system_transaction(full_release) as tx:
        slate = observed_for(tx, {"confident_tasks": ["maintaining equipment", "planning shifts"]})

    hits = {q["text"]: q["hits"] for q in slate["queries"]}
    assert hits["maintaining equipment"] == POOL_LIMIT
    assert slate["pool_size"] == POOL_LIMIT
    assert slate["beyond_pool_limit"] > 0


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
