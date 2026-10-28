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

from nessa.catalogue.esco import ESCO_RELEASE
from nessa.cli import import_taxonomy, migrate_app
from nessa.db import system_transaction
from tests.support.infra import Infra, migrator_engine
from tools.datasets import DATASETS_DIR
from tools.evaluation import (
    CaseKind,
    Failure,
    evaluate,
    failures_by_type,
    load_cases,
    observe_discovery_offline,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def full_release(infra: Infra) -> Iterator[sa.Engine]:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    database = f"nessa_eval_{uuid.uuid4().hex[:8]}"
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
    assert 60 <= p02["pool_size"] <= 120 or p02["beyond_pool_limit"] == 0
    assert p02["release"]["sample"] is False  # the real catalogue, not the test subset
