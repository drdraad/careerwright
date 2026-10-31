"""The discovery evaluation cases against the full pinned ESCO release (DIV1-08, TEST1-10).

The subject is the deterministic pipeline: the fixture proposer's queries (each answer text
as a query), English full-text search over all 3,039 occupations, de-duplication and the
slate. It certifies the pipeline and its rules, not a model's queries (those are the live
run's, `tools.live_eval`). Failures are reported by type."""

import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa

from careerwright.capability.strength import SCRIPTED_STRENGTHS
from careerwright.catalogue.esco import ESCO_RELEASE
from careerwright.cli import import_taxonomy, migrate_app
from careerwright.db import system_transaction
from careerwright.profile.slate import POOL_LIMIT, POOL_TARGET
from tests.support.infra import Infra, migrator_engine
from tools.datasets import DATASETS_DIR
from tools.evaluation import (
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
    # P02's four searches fill the working pool within its soft 60-120 (DIV1-02). Each
    # search reaches work only through essential skills now (fix round 1 of Task W2B), so
    # four searches of at most 30 each no longer pass the bound; the bound's cut is
    # `test_slate.py`'s.
    assert POOL_TARGET <= p02["pool_size"] <= POOL_LIMIT
    assert p02["release"]["sample"] is False  # the real catalogue, not the test subset


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
