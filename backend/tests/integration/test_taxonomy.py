"""The ESCO taxonomy in PostgreSQL 16: import manifest, full-text retrieval, alias lookup,
ISCO grouping and provisional concepts (TAX1-01, TAX1-04, DIV1-01, DIV1-03).

The session database holds the committed sample. One test imports the full pinned release
(fetched by `make setup`) into its own database: acceptance needs `make setup` first.
"""

import dataclasses
import uuid
from pathlib import Path
from typing import Any

import pytest
from psycopg import errors

from careerwright.catalogue.esco import ESCO_RELEASE, concept_id, parse_release
from careerwright.catalogue.releases import read_verified
from careerwright.catalogue.taxonomy import (
    TaxonomyMismatchError,
    import_release,
    occupation_detail,
    search_occupations,
)
from careerwright.cli import import_taxonomy, migrate_app
from careerwright.db import create_engine, system_transaction
from careerwright.errors import CareerwrightError, ErrorCode
from tests.support.client import ApiClient
from tests.support.esco import SAMPLE_PATH, SAMPLE_RELEASE
from tests.support.infra import Infra, migrator_engine
from tools.datasets import DATASETS_DIR

pytestmark = pytest.mark.integration


def search(api: ApiClient, token: str, q: str, **params: object) -> dict[str, Any]:
    response = api.get("/v1/taxonomy/occupations", token, q=q, **params)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


@pytest.mark.req("TAX1-04")
def test_the_manifest_records_release_hash_licence_attribution_and_versions(
    api: ApiClient, ada: str
) -> None:
    response = api.get("/v1/taxonomy", ada)

    assert response.status_code == 200, response.text
    release = response.json()
    assert release["dataset_id"] == SAMPLE_RELEASE.dataset_id
    assert release["sample"] is True  # the test copy says so, everywhere it is shown
    assert release["sha256"] == SAMPLE_RELEASE.sha256
    assert release["version"] == "v1.2.1"
    assert release["transformation_version"] == "careerwright-esco-import-1"
    assert "ISCO-08" in release["native_code_version"]
    assert "2011/833/EU" in release["licence"]
    assert release["attribution"] == (
        "This service uses the ESCO classification of the European Commission."
    )
    # The import is itself a reduced, transformed version: marked as adapted (reuse
    # condition 2), naming what it leaves out and the transformation.
    assert release["adaptation"].startswith("Adapted from ESCO")
    assert "careerwright-esco-import-1" in release["adaptation"]
    assert "skill hierarchy" in release["adaptation"]
    assert (release["occupation_count"], release["isco_group_count"]) == (30, 70)


@pytest.mark.req("DIV1-01")
def test_an_alias_finds_its_occupation_before_the_ranked_full_text_matches(
    api: ApiClient, ada: str
) -> None:
    found = search(api, ada, "IT support technician")

    [match] = found["label_matches"]
    assert (match["preferred_label"], match["label"], match["label_kind"]) == (
        "ICT help desk agent",
        "IT support technician",
        "alternative",
    )
    assert match["concept_id"] not in {h["concept_id"] for h in found["full_text"]}
    # Each result says it is an ESCO concept, never a provisional one.
    assert {m["concept_kind"] for m in [match, *found["full_text"]]} == {"esco"}


def test_a_label_match_with_no_searchable_words_reports_full_text_as_not_run(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    holder = search(api, ada, "bicycle mechanic")["label_matches"][0]["concept_id"]
    # A hidden label of stop words only: it matches as a label, but full-text search has
    # no word to look for. (The sample has none, so the test adds one and removes it.)
    infra.query(
        "INSERT INTO careerwright.occupation_labels (concept_id, label, normalised, kind) "
        "VALUES (%s, 'Of The', 'of the', 'hidden')",
        (holder,),
    )
    try:
        found = search(api, ada, "of the")
    finally:
        infra.query("DELETE FROM careerwright.occupation_labels WHERE label = 'Of The'")

    assert [m["concept_id"] for m in found["label_matches"]] == [holder]
    assert (found["full_text"], found["full_text_total"]) == ([], None)  # not run, not zero


@pytest.mark.req("DIV1-01")
def test_full_text_search_ranks_by_task_words_and_counts_every_match(
    api: ApiClient, ada: str
) -> None:
    found = search(api, ada, "repair bicycles", limit=1)

    assert found["label_matches"] == []
    [best] = found["full_text"]
    assert best["preferred_label"] == "bicycle mechanic"
    assert found["full_text_total"] >= 1
    assert found["limit"] == 1
    helpdesk = search(api, ada, "help desk")
    labels = [h["preferred_label"] for h in helpdesk["full_text"]]
    assert {"ICT help desk agent", "ICT help desk manager"} <= set(labels)
    assert helpdesk["full_text_total"] == len(labels)  # a page never hides a remainder
    assert helpdesk["match"] == "all"
    broad = search(api, ada, "fixing bicycles outdoors gardens", match="any")
    assert broad["match"] == "any"
    assert {"bicycle mechanic", "landscape gardener"} <= {
        h["preferred_label"] for h in broad["full_text"]
    }
    assert search(api, ada, "fixing bicycles outdoors gardens")["full_text"] == []


def test_a_label_two_occupations_share_returns_both_never_one_silently(
    api: ApiClient, ada: str
) -> None:
    found = search(api, ada, "Bus Operator")

    labels = sorted(m["preferred_label"] for m in found["label_matches"])
    assert labels == ["bus driver", "trolley bus driver"]


def test_a_hidden_label_matches_without_its_text_being_shown(api: ApiClient, ada: str) -> None:
    found = search(api, ada, "g.p.")

    [match] = found["label_matches"]
    assert (match["preferred_label"], match["label"], match["label_kind"]) == (
        "general practitioner",
        None,
        "hidden",
    )


def test_a_query_with_no_searchable_words_is_refused_not_answered_empty(
    api: ApiClient, ada: str
) -> None:
    response = api.get("/v1/taxonomy/occupations", ada, q="the and of")

    assert response.status_code == 422
    assert response.json()["error"]["details"] == {"field": "q", "reason": "no_search_terms"}


@pytest.mark.req("TAX1-01")
def test_an_occupation_shows_its_isco_chain_skills_and_attribution(
    api: ApiClient, ada: str
) -> None:
    agent = search(api, ada, "ICT help desk agent")["label_matches"][0]

    detail = api.get(f"/v1/taxonomy/occupations/{agent['concept_id']}", ada).json()

    assert [g["code"] for g in detail["isco_groups"]] == ["3", "35", "351", "3512"]
    assert detail["esco_uri"].startswith("http://data.europa.eu/esco/occupation/")
    assert detail["concept_id"] == str(concept_id(detail["esco_uri"]))
    assert {s["relation"] for s in detail["skills"]} <= {"essential", "optional"}
    assert any(s["relation"] == "essential" for s in detail["skills"])
    assert "IT support technician" in detail["alternative_labels"]
    assert detail["attribution"].startswith("This service uses the ESCO classification")
    assert detail["adaptation"].startswith("Adapted from ESCO")  # shown with the data
    assert detail["concept_kind"] == "esco"
    manager = search(api, ada, "ICT help desk manager")["label_matches"][0]
    assert manager["isco_code"] == agent["isco_code"]  # same ISCO group, distinct concepts
    assert manager["concept_id"] != agent["concept_id"]
    missing = api.get(f"/v1/taxonomy/occupations/{uuid.uuid4()}", ada)
    assert missing.status_code == 404


def test_the_taxonomy_needs_an_invited_caller(api: ApiClient) -> None:
    assert api.get("/v1/taxonomy", None).status_code == 401
    assert api.get("/v1/places", None).status_code == 401


@pytest.mark.req("BND1-04")
def test_the_english_city_list_is_served_with_its_source(api: ApiClient, ada: str) -> None:
    places = api.get("/v1/places", ada).json()

    assert len(places["items"]) == 55
    assert places["source_url"].startswith("https://www.gov.uk/")
    assert places["licence"] == "Open Government Licence v3.0"
    leeds = next(p for p in places["items"] if p["label"] == "Leeds")
    assert (leeds["place_id"], leeds["region"], leeds["timezone"]) == (
        "gb-eng-leeds",
        "Yorkshire and The Humber",
        "Europe/London",
    )
    # A city is geography only: nothing about residence, nationality or work rights.
    assert {key for p in places["items"] for key in p} == {
        "place_id",
        "label",
        "aliases",
        "region",
        "region_code",
        "country_code",
        "subdivision_code",
        "timezone",
    }


def test_the_api_role_reads_but_cannot_change_the_taxonomy(infra: Infra) -> None:
    with pytest.raises(errors.InsufficientPrivilege):
        infra.as_role("pg_api", "DELETE FROM careerwright.occupation_labels")
    with pytest.raises(errors.InsufficientPrivilege):
        infra.as_role("pg_api", "UPDATE careerwright.taxonomy_releases SET sample = false")
    assert infra.as_role(
        "pg_api", "SELECT count(*) AS n FROM careerwright.occupation_concepts"
    ) == [{"n": 30}]


def test_importing_again_changes_nothing_and_another_release_is_refused(infra: Infra) -> None:
    catalogue = parse_release(read_verified(SAMPLE_PATH, SAMPLE_RELEASE), SAMPLE_RELEASE)
    other = dataclasses.replace(
        catalogue, pin=dataclasses.replace(SAMPLE_RELEASE, dataset_id="esco-v9.9.9-en-csv")
    )
    engine = migrator_engine(infra)
    try:
        assert import_taxonomy(engine, SAMPLE_PATH, SAMPLE_RELEASE) == "already imported"
        # The check after the lock, for an import that raced past the first one.
        with engine.begin() as tx:
            assert import_release(tx, catalogue) == "already imported"
        with engine.begin() as tx, pytest.raises(TaxonomyMismatchError):
            import_release(tx, other)
    finally:
        engine.dispose()
    assert infra.query("SELECT count(*) AS n FROM careerwright.taxonomy_releases") == [{"n": 1}]


TAXONOMY_TABLES = (
    "taxonomy_releases",
    "isco_groups",
    "occupation_concepts",
    "occupation_labels",
    "occupation_broader",
    "skills",
    "skill_labels",
    "occupation_skills",
    "skill_relations",
)


def migrated_database(infra: Infra, prefix: str) -> str:
    database = f"careerwright_{prefix}_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    try:
        migrate_app(owner)
    finally:
        owner.dispose()
    return database


@pytest.mark.req("TAX1-04")
def test_a_release_imported_by_another_transformation_is_refused_not_kept(infra: Infra) -> None:
    database = migrated_database(infra, "transform")
    owner = migrator_engine(infra, database)
    try:
        assert import_taxonomy(owner, SAMPLE_PATH, SAMPLE_RELEASE) == "imported"
        with owner.begin() as tx:  # as if an earlier transformation had built it
            tx.exec_driver_sql(
                "UPDATE careerwright.taxonomy_releases SET transformation_version = "
                "'careerwright-esco-import-0'"
            )

        # The same release bytes are not enough: its stored labels and vectors are stale.
        with pytest.raises(TaxonomyMismatchError, match="transformation"):
            import_taxonomy(owner, SAMPLE_PATH, SAMPLE_RELEASE)
    finally:
        owner.dispose()


@pytest.mark.req("TAX1-04")
def test_an_import_that_fails_part_way_leaves_no_taxonomy_rows(infra: Infra) -> None:
    database = migrated_database(infra, "atomic")
    catalogue = parse_release(read_verified(SAMPLE_PATH, SAMPLE_RELEASE), SAMPLE_RELEASE)
    # Past the parser's checks: a relation naming a skill the catalogue does not hold.
    broken = dataclasses.replace(
        catalogue,
        occupation_skills=(
            *catalogue.occupation_skills,
            dataclasses.replace(catalogue.occupation_skills[0], skill_id=uuid.uuid4()),
        ),
    )
    owner = migrator_engine(infra, database)
    try:
        with pytest.raises(errors.ForeignKeyViolation), owner.begin() as tx:
            import_release(tx, broken)
    finally:
        owner.dispose()

    for table in TAXONOMY_TABLES:
        assert infra.query(
            f"SELECT count(*) AS n FROM careerwright.{table}",  # noqa: S608 - fixed names
            database=database,
        ) == [{"n": 0}], table


def test_a_database_without_the_taxonomy_refuses_searches(infra: Infra) -> None:
    database = f"careerwright_empty_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    try:
        migrate_app(owner)
    finally:
        owner.dispose()
    engine = create_engine(infra.api_settings(database).app_database, application_name="t")
    try:
        with system_transaction(engine) as tx, pytest.raises(CareerwrightError) as raised:
            search_occupations(tx, "data analyst", 5)
    finally:
        engine.dispose()

    assert raised.value.code is ErrorCode.TAXONOMY_UNAVAILABLE


@pytest.mark.req("TAX1-04", "DIV1-01", "TAX1-01")
def test_the_full_pinned_release_imports_and_is_searchable(infra: Infra) -> None:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    database = f"careerwright_esco_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    try:
        migrate_app(owner)
        assert import_taxonomy(owner, release) == "imported"
        assert import_taxonomy(owner, release) == "already imported"
    finally:
        owner.dispose()

    counts = infra.query(
        "SELECT (SELECT count(*) FROM careerwright.occupation_concepts) AS occupations, "
        "(SELECT count(*) FROM careerwright.occupation_labels) AS labels, "
        "(SELECT count(*) FROM careerwright.skills) AS skills, "
        "(SELECT count(*) FROM careerwright.skill_labels) AS skill_labels, "
        "(SELECT count(*) FROM careerwright.occupation_skills) AS occupation_skills, "
        "(SELECT count(*) FROM careerwright.skill_relations) AS skill_relations, "
        "(SELECT count(*) FROM careerwright.isco_groups) AS isco, "
        "(SELECT count(*) FROM careerwright.occupation_broader) AS broader, "
        "(SELECT count(*) FROM careerwright.occupation_concepts WHERE search_vector IS NULL) AS "
        "unindexed",
        database=database,
    )
    # 3,043 occupation rows and 13,960 skill rows, of which 4 and 21 repeat a concept with
    # only `modifiedDate` changed (counted by hand from the CSVs, 2026-10-28).
    assert counts == [
        {
            "occupations": 3_039,
            "labels": 33_498,
            "skills": 13_939,
            "skill_labels": 100_886,
            "occupation_skills": 126_051,
            "skill_relations": 5_818,
            "isco": 619,
            "broader": 3_039,
            "unindexed": 0,
        }
    ]
    [manifest] = infra.query(
        "SELECT dataset_id, sha256, sample, repeated_rows_collapsed FROM "
        "careerwright.taxonomy_releases",
        database=database,
    )
    assert manifest == {
        "dataset_id": ESCO_RELEASE.dataset_id,
        "sha256": ESCO_RELEASE.sha256,
        "sample": False,
        "repeated_rows_collapsed": 25,
    }
    engine = create_engine(infra.api_settings(database).app_database, application_name="t")
    try:
        with system_transaction(engine) as tx:
            shared = search_occupations(tx, "clinical research assistant", 10)
            every_word = search_occupations(tx, "repairing physical objects outdoors", 20)
            tasks = search_occupations(tx, "repairing physical objects outdoors", 20, any_word=True)
            nurse = search_occupations(tx, "nurse responsible for general care", 5)
            detail = occupation_detail(tx, nurse.label_matches[0].concept_id)
    finally:
        engine.dispose()
    assert sorted(m.preferred_label for m in shared.label_matches) == [
        "clinical trial assistant",
        "medical laboratory assistant",
    ]
    # Every word: a complete, honest zero. Any word: a ranked page that says it is a page.
    assert (every_word.full_text, every_word.full_text_total) == ([], 0)
    assert tasks.full_text_total is not None
    assert tasks.full_text_total > len(tasks.full_text) == 20
    assert [g.code for g in detail.isco_groups] == ["2", "22", "222", "2221"]
    assert any(s.relation == "essential" for s in detail.skills)
