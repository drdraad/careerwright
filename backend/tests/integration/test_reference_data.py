"""The pinned reference datasets on PostgreSQL 16, and an occupation's pay and AI evidence
through the API (ADR 0010; TAX1-02..07, AIR1-02, AIR1-03, AIR1-05, AIR1-07, AIR1-10,
AIR1-11, JOB-05). The session database holds the synthetic samples
(`tests/support/reference_data.py`); the pinned files are imported in their own database."""

import dataclasses
import uuid
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from nessa.api.app import create_app
from nessa.api.deps import ApiDependencies
from nessa.catalogue.esco import ESCO_RELEASE, concept_id
from nessa.catalogue.pay import MappingReview, MappingReviewPack
from nessa.catalogue.reference import DATASETS, ReferenceMismatchError
from nessa.catalogue.releases import ReleaseIntegrityError
from nessa.cli import import_reference_data, import_taxonomy, migrate_app
from nessa.seed import FIXTURE_WORKSPACE_ID
from tests.support import reference_data as samples
from tests.support.client import ApiClient, profile_with
from tests.support.esco import SAMPLE_PATH, SAMPLE_RELEASE
from tests.support.infra import API_BASE, Infra, migrator_engine
from tools.datasets import DATASETS_DIR

pytestmark = pytest.mark.integration

DATA_ANALYST = concept_id(samples.DATA_ANALYST)
BOOKKEEPER = concept_id(samples.BOOKKEEPER)
COOK = concept_id("http://data.europa.eu/esco/occupation/90f75f67-495d-49fa-ab57-2f320e251d7e")
DATA_QUALITY_SPECIALIST = concept_id(samples.DATA_QUALITY_SPECIALIST)


def evidence(api: ApiClient, token: str, workspace: str, concept: uuid.UUID) -> Any:
    response = api.get(f"/v1/workspaces/{workspace}/occupations/{concept}/evidence", token)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def manchester(api: ApiClient, ada: str) -> str:
    workspace = str(api.create_workspace(ada, "Reference evidence")["workspace_id"])
    put = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        ada,
        {"expected_version": 0, "profile": profile_with(cities=["Manchester"])},
    )
    assert put.status_code == 201, put.text
    return workspace


@pytest.mark.req("TAX1-04")
def test_each_dataset_s_manifest_records_its_release_licence_hash_and_versions(
    infra: Infra,
) -> None:
    rows = infra.query(
        "SELECT dataset, dataset_id, sha256, size_bytes, licence, attribution, sample, "
        "native_code_version, transformation_version, record_count, counts "
        "FROM nessa.reference_releases ORDER BY dataset"
    )

    assert [r["dataset"] for r in rows] == sorted(d.name for d in DATASETS)
    for row in rows:
        assert row["sample"] is True  # the synthetic samples, labelled
        assert row["dataset_id"].endswith("-synthetic-sample")
        assert row["licence"]
        assert row["attribution"]
        assert row["native_code_version"].endswith("synthetic test sample")
        assert row["transformation_version"].startswith("nessa-")
        assert len(row["sha256"]) == 64
    by_name = {r["dataset"]: r for r in rows}
    assert by_name["ashe"]["licence"] == "Open Government Licence v3.0"  # session 1, line A2
    assert "Office for National Statistics" in by_name["ashe"]["attribution"]
    assert "© ILO" in by_name["ilo_exposure"]["attribution"]
    # The crosswalk's version bridge, counted against what is held (TAX1-07).
    assert by_name["crosswalk"]["counts"] == {
        "esco_rows_not_in_held_release": 0,
        "onet_codes_without_tasks": 2,
        "isco_rows": 1,
    }


@pytest.mark.req("TAX1-04")
def test_an_import_is_kept_once_and_another_release_of_a_dataset_is_refused(
    infra: Infra, tmp_path: Path
) -> None:
    database = f"nessa_reference_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    try:
        migrate_app(owner)
        import_taxonomy(owner, SAMPLE_PATH, SAMPLE_RELEASE)
        files = samples.sample_files(tmp_path)
        altered = tmp_path / "altered"
        altered.write_bytes(files[0][1].read_bytes() + b"x")
        with pytest.raises(ReleaseIntegrityError):  # not the pinned bytes: nothing imported
            import_reference_data(owner, [(files[0][0], altered)])
        assert infra.query("SELECT * FROM nessa.reference_releases", database=database) == []
        assert set(import_reference_data(owner, files).values()) == {"imported"}
        assert set(import_reference_data(owner, files).values()) == {"already imported"}
        other = [
            (dataclasses.replace(d, pin=dataclasses.replace(d.pin, dataset_id="other")), p)
            for d, p in files
        ]
        with pytest.raises(ReferenceMismatchError, match="reviewed migration"):
            import_reference_data(owner, other[:1])
    finally:
        owner.dispose()


@pytest.mark.req("TAX1-02", "TAX1-03", "TAX1-05", "TAX1-06", "JOB-05")
def test_an_occupation_s_pay_keeps_every_uk_soc_candidate_regional_and_unmodelled(
    api: ApiClient, ada: str, manchester: str
) -> None:
    found = evidence(api, ada, manchester, DATA_ANALYST)

    assert found["regions"] == [{"code": samples.NORTH_WEST, "name": "North West"}]
    mapping = found["uk_soc"]
    assert mapping["isco_code"] == "2511"
    assert (mapping["resolution"], mapping["proposed_soc_code"]) == ("title_resolved", "3544")
    assert (mapping["review_state"], mapping["reviewed_soc_code"]) == ("unreviewed", None)
    assert [c["soc_code"] for c in mapping["candidates"]] == ["3544", "2135"]  # both kept
    [analysts, systems] = mapping["candidates"]
    assert {(b["region_code"], b["period"]) for b in analysts["benchmarks"]} == {
        (samples.NORTH_WEST, period) for period in ("year", "week", "hour")
    }  # the person's region only: London's figure is not shown
    for benchmark in analysts["benchmarks"]:
        assert benchmark["geography"] == "region"  # never a city's figure
        assert benchmark["population"] == "full_time"
    annual = next(b for b in analysts["benchmarks"] if b["period"] == "year")
    statistics = {s["statistic"]: s for s in annual["statistics"]}
    assert statistics["median"]["amount"] == {"minor_units": 3_806_310, "currency": "GBP"}
    assert statistics["p10"] == {
        "statistic": "p10",
        "amount": None,
        "withheld": "x",
        "cv": None,
        "reliability": "unreliable",
    }
    # Fix round 1, A-M4: each statistic carries its own CV and band, P90 among them.
    assert (statistics["median"]["cv"], statistics["median"]["reliability"]) == (
        "9.6",
        "reasonably_precise",
    )
    assert (statistics["p90"]["cv"], statistics["p90"]["reliability"]) == (
        samples.P90_CV,
        "acceptable",
    )
    [withheld] = [b for b in systems["benchmarks"] if b["period"] == "year"]
    assert {s["statistic"]: s["reliability"] for s in withheld["statistics"]}["median"] == (
        "unreliable"
    )
    # No reviewed mapping: no modelled pay, so no ASHE figure is the occupation's own.
    assert found["modelled_pay"] is None
    assert found["modelled_pay_unavailable"] == "no_reviewed_mapping"
    assert found["trend"] == {"state": "unavailable", "reason": "single_snapshot"}
    cook = evidence(api, ada, manchester, COOK)
    assert (cook["uk_soc"]["resolution"], cook["uk_soc"]["candidates"]) == ("no_candidate", [])


@pytest.mark.req("AIR1-03", "AIR1-11", "TAX1-07", "AIR1-10")
def test_exposure_and_observed_use_are_shown_and_resilience_stays_unscored(
    api: ApiClient, ada: str, manchester: str
) -> None:
    found = evidence(api, ada, manchester, DATA_ANALYST)

    ai = found["ai_evidence"]
    assert ai["state"] == "exposure_only"
    assert (ai["ilo"]["isco_code"], ai["ilo"]["mean_score"], ai["ilo"]["gradient"]) == (
        "2511",
        "0.4900",
        "Exposed: Gradient 2",
    )
    assert "never a prediction of job loss" in ai["ilo"]["measure"]
    by_code = {m["onet_code"]: m for m in ai["observed_use"]}
    assert by_code["15-2051.01"]["match_type"] == "closeMatch"
    assert (by_code["15-2051.01"]["tasks_listed"], by_code["15-2051.01"]["tasks_observed"]) == (
        2,
        1,
    )
    assert by_code["15-2051.01"]["top_tasks"] == [
        {"task": "Synthetic task: build dashboards.", "share_pct": "0.25"}
    ]
    # A match whose O*NET code the release holds no task for: missing, never zero.
    assert by_code["15-2041.00"] == {
        "onet_code": "15-2041.00",
        "onet_title": "Statisticians",
        "match_type": "broadMatch",
        "in_release": False,
        "tasks_listed": None,
        "tasks_observed": None,
        "top_tasks": [],
    }
    assert "not replacement" in ai["observed_use_measure"]
    resilience = found["ai_resilience"]
    assert (resilience["state"], resilience["unscored_reason"]) == ("unscored", "no_record")
    assert (resilience["lower"], resilience["upper"], resilience["bands"]) == (None, None, [])
    assert resilience["label"] == "AI Resilience Score"
    assert resilience["experimental"] is True
    assert resilience["horizon_years"] == 5
    assert "not a probability" in resilience["meaning"]
    assert resilience["pack_version"] == "l0-2026-10-29"
    assert {r["dataset"] for r in found["releases"]} == {d.name for d in DATASETS}


@pytest.mark.req("AIR1-02", "AIR1-07")
def test_the_synthetic_fixture_record_publishes_only_in_the_fixture_workspace(
    api: ApiClient, ada: str, manchester: str
) -> None:
    fixture = evidence(api, ada, str(FIXTURE_WORKSPACE_ID), DATA_QUALITY_SPECIALIST)
    elsewhere = evidence(api, ada, manchester, DATA_QUALITY_SPECIALIST)

    shown = fixture["ai_resilience"]
    assert (shown["state"], shown["lower"], shown["upper"]) == ("published_range", 5, 8)
    assert shown["bands"] == ["5-6", "7-8"]
    assert shown["synthetic"] is True
    assert "Synthetic fixture" in shown["synthetic_label"]
    assert shown["pack_version"].startswith("fixture-")
    assert elsewhere["ai_resilience"]["state"] == "unscored"  # never a real assessment
    assert elsewhere["ai_resilience"]["synthetic"] is False


@pytest.fixture
def reviewed_api(api_deps: ApiDependencies) -> Iterator[ApiClient]:
    """The API with one synthetic reviewed mapping, as an accountable reviewer would record
    it: bookkeeper to SOC 2020 4122 (H-10; no real review exists)."""
    review = MappingReview(
        esco_uri=samples.BOOKKEEPER,
        soc_code="4122",
        reviewer="Synthetic reviewer (tests only)",
        reviewed_on=date(2026, 10, 29),
        reasons="Synthetic review for a test.",
    )
    reviews = MappingReviewPack(pack_version="test", dated=date(2026, 10, 29), reviews=[review])
    with TestClient(
        create_app(dataclasses.replace(api_deps, mapping_reviews=reviews)),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57011),
    ) as client:
        yield ApiClient(client)


@pytest.mark.req("JOB-05", "TAX1-03", "TAX1-06")
def test_a_reviewed_mapping_gives_modelled_pay_for_the_person_s_region_only(
    reviewed_api: ApiClient, api: ApiClient, ada: str, manchester: str
) -> None:
    found = evidence(reviewed_api, ada, manchester, BOOKKEEPER)
    unreviewed = evidence(api, ada, manchester, BOOKKEEPER)

    assert found["uk_soc"]["review_state"] == "reviewed"
    assert found["uk_soc"]["reviewer"] == "Synthetic reviewer (tests only)"
    modelled = found["modelled_pay"]
    assert (modelled["basis"], modelled["soc_code"]) == ("modelled", "4122")
    assert {(b["region_code"], b["geography"]) for b in modelled["benchmarks"]} == {
        (samples.NORTH_WEST, "region")
    }
    assert unreviewed["modelled_pay"] is None


def test_another_person_s_workspace_is_not_found(api: ApiClient, ben: str, manchester: str) -> None:
    response = api.get(f"/v1/workspaces/{manchester}/occupations/{DATA_ANALYST}/evidence", ben)

    assert response.status_code == 404


@pytest.mark.req("TAX1-04", "TAX1-02", "AIR1-11", "TAX1-07")
def test_the_pinned_files_import_with_their_documented_counts(infra: Infra) -> None:
    files = [(d, Path(DATASETS_DIR) / d.pin.file_name) for d in DATASETS]
    missing = [str(path) for _, path in files if not path.is_file()]
    assert not missing, f"run `make setup` first: {missing}"
    esco = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    database = f"nessa_pinned_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    try:
        migrate_app(owner)
        import_taxonomy(owner, esco)
        assert set(import_reference_data(owner, files).values()) == {"imported"}
    finally:
        owner.dispose()

    rows = infra.query(
        "SELECT dataset, record_count, counts, sample FROM nessa.reference_releases "
        "ORDER BY dataset",
        database=database,
    )
    # Counted from the files by hand (2026-10-29).
    assert {r["dataset"]: (r["record_count"], r["counts"], r["sample"]) for r in rows} == {
        "ashe": (13_596, {"median_withheld": 8_505}, False),
        "crosswalk": (
            4_253,
            {"esco_rows_not_in_held_release": 3, "onet_codes_without_tasks": 235, "isco_rows": 43},
            False,
        ),
        "ilo_exposure": (427, {"tasks": 3_265}, False),
        "onet_tasks": (19_530, {"occupations": 974}, False),
        "soc_index": (32_435, {"unit_groups": 412, "uncoded": 235}, False),
        "task_usage": (3_364, {}, False),
    }
    [regions] = infra.query(
        "SELECT count(DISTINCT region_code) AS n FROM nessa.ashe_estimates", database=database
    )
    assert regions["n"] == 11  # England's nine regions, Wales and Scotland: never a city
