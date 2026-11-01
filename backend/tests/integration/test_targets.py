"""Each target is stored once, and every chapter reads that record (Task 6d slice A; PROF-10;
the audit's code appendix, finding F5), against real PostgreSQL 16 and the ESCO sample: a
punctuated plural, an accented title and an "&" title resolve the same in the slate, the
sketch, the strength, Skills and the world, and the record says how far Careerwright can
cover the target."""

import uuid
from pathlib import Path
from typing import Any

import pytest

from careerwright.capability.commands import committed_data, pack_targets
from careerwright.catalogue.esco import concept_id
from careerwright.cli import import_reference_data, import_taxonomy, migrate_app, reset_demo, seed
from careerwright.db import system_transaction
from careerwright.profile import store, titles
from careerwright.profile.targets import stored_targets
from careerwright.seed import FIXTURE_WORKSPACE_ID
from tests.support.client import ApiClient, profile_with
from tests.support.esco import SAMPLE_PATH, SAMPLE_RELEASE
from tests.support.infra import Infra, migrator_engine
from tests.support.reference_data import sample_files

pytestmark = pytest.mark.integration

PACK = pack_targets(committed_data())
MECHANIC = "http://data.europa.eu/esco/occupation/336cf331-8082-4a0c-bf5f-e7c54706211c"
COOK = "http://data.europa.eu/esco/occupation/90f75f67-495d-49fa-ab57-2f320e251d7e"
LOGISTICS = "http://data.europa.eu/esco/occupation/823db06f-25e1-4658-b063-d6ef956b41f5"
NURSE = "http://data.europa.eu/esco/occupation/8d3e8aaa-791b-4c75-a465-f3f827028f50"
# Real ESCO titles: "bicycle mechanic", typed as a punctuated plural; "sauté cook" (the cook's
# other title), typed without its accent; "distribution & logistics manager" (the logistics
# and distribution manager's), typed with "and". ESCO also lists that one with "and"; the
# test takes that twin away for its run, as ESCO lists "food & beverage supervisor" alone.
TYPED = {
    "Bicycle-mechanics.": MECHANIC,
    "Saute cooks": COOK,
    "Distribution and logistics managers": LOGISTICS,
}
TWIN = "distribution and logistics manager"


def put_targets(api: ApiClient, token: str, workspace: str, *targets: str) -> None:
    response = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        token,
        {"expected_version": 0, "profile": profile_with(target_titles=list(targets))},
    )
    assert response.status_code == 201, response.text


def get(api: ApiClient, token: str, path: str) -> Any:
    response = api.get(path, token)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.req("PROF-10")
def test_a_punctuated_an_accented_and_an_ampersand_title_resolve_the_same_everywhere(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace = str(api.create_workspace(ada, "Targets once (synthetic)")["workspace_id"])
    [twin] = infra.query(
        "SELECT concept_id, label, normalised, kind FROM careerwright.occupation_labels "
        "WHERE normalised = %s",
        (TWIN,),
    )
    infra.query("DELETE FROM careerwright.occupation_labels WHERE normalised = %s", (TWIN,))
    try:
        put_targets(api, ada, workspace, *TYPED)
    finally:
        infra.query(
            "INSERT INTO careerwright.occupation_labels (concept_id, label, normalised, kind) "
            "VALUES (%s, %s, %s, %s)",
            (twin["concept_id"], twin["label"], twin["normalised"], twin["kind"]),
        )
    expected = {title: str(concept_id(uri)) for title, uri in TYPED.items()}

    # The world reads the stored records.
    records = get(api, ada, f"/v1/workspaces/{workspace}/targets")
    assert records["profile_version"] == 1
    assert {t["title"]: (t["link"], t["concept_id"]) for t in records["targets"]} == {
        title: ("exact_label", concept) for title, concept in expected.items()
    }
    assert {t["kind"] for t in records["targets"]} == {"own_words"}
    assert {t["coverage"] for t in records["targets"]} == {"not_covered"}
    # The sketch.
    sketch = get(api, ada, f"/v1/workspaces/{workspace}/sketch")
    assert {
        t["title"]: (t["resolution"], [o["concept_id"] for o in t["occupations"]])
        for t in sketch["targets"]
    } == {title: ("esco", [concept]) for title, concept in expected.items()}
    # Skills (before: a typed title's seed was an exact normalised label, so none of these had
    # one).
    matrices = get(api, ada, f"/v1/workspaces/{workspace}/capability/matrices")["matrices"]
    assert {
        m["target_title"]: (
            m["sources"]["occupation"]["basis"],
            m["sources"]["occupation"]["concept_id"],
        )
        for m in matrices
    } == {title: ("esco_label", concept) for title, concept in expected.items()}
    # The slate and the strength read the targets through `titles.targets`.
    engine = migrator_engine(infra)
    try:
        with system_transaction(engine) as tx:
            latest = store.current_profile(tx, uuid.UUID(workspace))
            assert latest is not None
            records = stored_targets(tx, uuid.UUID(workspace), latest.document, PACK)
            resolved = titles.targets(tx, records)
    finally:
        engine.dispose()
    assert {t.text: [str(o) for o in t.occupations] for t in resolved} == {
        title: [concept] for title, concept in expected.items()
    }
    # Choosing the bicycle mechanic finds it already a target: one title, as a concept.
    again = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/targets",
        ada,
        {"expected_version": 1, "concept_id": expected["Bicycle-mechanics."]},
    )
    assert again.status_code == 200, again.text
    assert again.json()["version"] == 1


@pytest.mark.req("PROF-10", "MAP1-05")
def test_a_chosen_occupation_is_stored_with_the_choice_and_the_pack_target_it_covers(
    api: ApiClient, ada: str, ben: str
) -> None:
    workspace = str(api.create_workspace(ada, "Chosen target (synthetic)")["workspace_id"])
    chosen = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/targets",
        ada,
        {"expected_version": 0, "concept_id": str(concept_id(NURSE))},
    )
    assert chosen.status_code == 201, chosen.text
    typed = str(api.create_workspace(ada, "Pack title (synthetic)")["workspace_id"])
    put_targets(api, ada, typed, "Registered nurse", "Tidal lagoon whisperer")

    [nurse] = get(api, ada, f"/v1/workspaces/{workspace}/targets")["targets"]
    pack, unknown = get(api, ada, f"/v1/workspaces/{typed}/targets")["targets"]

    assert nurse == {
        "key": "nurse responsible for general care",
        "title": "nurse responsible for general care",
        "kind": "esco",
        "link": "occupation_choice",
        "concept_id": str(concept_id(NURSE)),
        "label_matches": 1,
        "coverage": "pack_target",
        "pack_target_id": "registered-nurse-manchester",
        # Task 6e fix round 1 (review M2): chosen from ESCO, so a list holds the title.
        "on_a_list": True,
    }
    # The pack's title: Skills seeds it through the crosswalk, but ESCO itself names no
    # occupation for it, so the slate and the sketch join nothing to it.
    assert (pack["link"], pack["concept_id"], pack["coverage"], pack["pack_target_id"]) == (
        "pack_crosswalk",
        None,
        "pack_target",
        "registered-nurse-manchester",
    )
    assert (unknown["link"], unknown["label_matches"], unknown["coverage"]) == (
        "none",
        0,
        "not_covered",
    )
    sketch = get(api, ada, f"/v1/workspaces/{typed}/sketch")["targets"]
    # Task 6d slice B: the UK job-title index lists "Registered nurse" (as the synthetic sample
    # does, like the real index), so the sketch says Careerwright found it there.
    assert [(t["resolution"], t["coverage"]) for t in sketch] == [
        ("uk_title", "pack_target"),
        ("not_found", "not_covered"),
    ]
    # Another person's targets are not found, never an empty list.
    other = api.get(f"/v1/workspaces/{workspace}/targets", ben)
    assert other.status_code == 404


@pytest.mark.req("PROF-10", "MAP1-05")
def test_each_pack_title_esco_doesn_t_name_is_covered_even_with_a_qualifier_in_brackets(
    api: ApiClient, ada: str
) -> None:
    # Task 6d slice A fix round 1: three of the pack's four titles are no ESCO label, so this is
    # the main path for the roles Careerwright covers (review I-1; the web words it, never "Not
    # researched"); and "Registered nurse (adult)" reaches the nursing pack target by its title,
    # as it did before targets were stored once (review Minor 2).
    workspace = str(api.create_workspace(ada, "Pack titles (synthetic)")["workspace_id"])
    put_targets(api, ada, workspace, "Registered nurse (adult)", "Data quality analyst",
                "Bookkeeping assistant")  # fmt: skip
    covered = {
        "Registered nurse (adult)": "registered-nurse-manchester",
        "Data quality analyst": "data-quality-analyst-manchester",
        "Bookkeeping assistant": "bookkeeping-assistant-leeds",
    }

    records = get(api, ada, f"/v1/workspaces/{workspace}/targets")["targets"]
    assert {t["title"]: (t["link"], t["coverage"], t["pack_target_id"]) for t in records} == {
        title: ("pack_crosswalk", "pack_target", target) for title, target in covered.items()
    }
    sketch = get(api, ada, f"/v1/workspaces/{workspace}/sketch")["targets"]
    # Task 6d slice B: the UK job-title index lists "Data quality analyst" (as the synthetic
    # sample does, like the real index); the other two are in neither list.
    listed = {"Data quality analyst"}
    assert [(t["title"], t["resolution"], t["coverage"]) for t in sketch] == [
        (title, "uk_title" if title in listed else "not_found", "pack_target") for title in covered
    ]
    matrices = get(api, ada, f"/v1/workspaces/{workspace}/capability/matrices")["matrices"]
    assert {
        m["target_title"]: (m["sources"]["pack_target"]["target_id"],
                            m["sources"]["pack_target"]["basis"])
        for m in matrices
    } == {title: (target, "title") for title, target in covered.items()}  # fmt: skip


def unrecorded(infra: Infra, workspace: uuid.UUID, database: str = "careerwright_app") -> list[str]:
    """Each target title of each of the workspace's profile versions that has no stored
    record, read from the tables themselves: a read through the API decides a title with
    none, so it can't show one is missing."""
    rows = infra.query(
        "SELECT t.title FROM careerwright.profile_versions v, jsonb_array_elements_text("
        "CASE WHEN jsonb_typeof(v.document -> 'target_titles' -> 'value') = 'array' "
        "THEN v.document -> 'target_titles' -> 'value' ELSE '[]'::jsonb END) AS t(title) "
        "WHERE v.workspace_id = %s AND NOT EXISTS (SELECT 1 FROM careerwright.target_records r "
        "WHERE r.workspace_id = v.workspace_id "
        "AND r.title_key = careerwright.concept_key(t.title)) ORDER BY v.version, t.title",
        (workspace,),
        database=database,
    )
    return [row["title"] for row in rows]


def forget(infra: Infra, workspace: uuid.UUID, *titles: str) -> None:
    """Take these titles' stored records away, as a path that skipped them would leave it."""
    for title in titles:
        infra.query(
            "DELETE FROM careerwright.target_records WHERE workspace_id = %s "
            "AND title_key = careerwright.concept_key(%s)",
            (workspace, title),
        )


@pytest.mark.req("PROF-10")
def test_a_target_with_no_record_is_decided_on_read_and_a_read_stores_nothing(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # Task 6d slice A fix round 2 (the re-review's Important 1): a title with no record reads
    # as its record would be stored, so no chapter says Careerwright couldn't match a title it
    # never tried, and nothing errors.
    workspace = str(api.create_workspace(ada, "Decided on read (synthetic)")["workspace_id"])
    put_targets(api, ada, workspace, "Bicycle-mechanics.", "Registered nurse (adult)")
    reads = [
        f"/v1/workspaces/{workspace}/{path}"
        for path in ("targets", "sketch", "capability/matrices", "capability/readiness")
    ]
    stored = [get(api, ada, path) for path in reads]

    forget(infra, uuid.UUID(workspace), "Bicycle-mechanics.", "Registered nurse (adult)")
    decided = [get(api, ada, path) for path in reads]

    assert decided == stored
    assert unrecorded(infra, uuid.UUID(workspace)) == [
        "Bicycle-mechanics.",
        "Registered nurse (adult)",
    ]


@pytest.mark.req("PROF-10")
def test_every_write_path_stores_a_record_for_each_target_it_saves(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # Task 6d slice A fix round 2: a read decides a title with no record, so only the tables
    # show whether a write stored its targets' records. Every profile write goes through
    # `commit_profile_version`: a direct edit, the choice of an occupation and a revert here
    # (a decision on a turn saves through it too); the architecture test keeps every other
    # writer out, and the seed's and the demo reset's records are checked below.
    workspace = uuid.UUID(api.create_workspace(ada, "Every write (synthetic)")["workspace_id"])
    base = f"/v1/workspaces/{workspace}"
    put_targets(api, ada, str(workspace), "Bicycle-mechanics.", "Registered nurse (adult)")
    edited = unrecorded(infra, workspace)
    chosen = api.write(
        "POST",
        f"{base}/targets",
        ada,
        {
            "expected_version": 1,
            "concept_id": str(concept_id(COOK)),
            "replaces": "Bicycle-mechanics.",
        },
    )
    assert chosen.status_code == 201, chosen.text
    after_choice = unrecorded(infra, workspace)
    # A version 1 title's record taken away: reverting to version 1 stores it again.
    forget(infra, workspace, "Bicycle-mechanics.")
    reverted = api.write(
        "POST", f"{base}/profile/revert", ada, {"expected_version": 2, "to_version": 1}
    )
    assert reverted.status_code == 201, reverted.text

    assert (edited, after_choice, unrecorded(infra, workspace)) == ([], [], [])
    assert [t["title"] for t in get(api, ada, f"{base}/targets")["targets"]] == [
        "Bicycle-mechanics.",
        "Registered nurse (adult)",
    ]


@pytest.mark.req("PROF-10")
def test_the_seed_and_the_demo_reset_store_the_fixture_s_target_records(
    infra: Infra, tmp_path: Path
) -> None:
    database = f"careerwright_seeded_targets_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    settings = infra.ops_settings(database)
    try:
        migrate_app(engine)
        assert import_taxonomy(engine, SAMPLE_PATH, SAMPLE_RELEASE) == "imported"
        import_reference_data(engine, sample_files(tmp_path))  # the UK job-title index
        seed(engine, settings)
        seeded = unrecorded(infra, FIXTURE_WORKSPACE_ID, database)
        reset_demo(engine, settings)
        reset = unrecorded(infra, FIXTURE_WORKSPACE_ID, database)
    finally:
        engine.dispose()
    records = infra.query(
        "SELECT title, link FROM careerwright.target_records WHERE workspace_id = %s",
        (FIXTURE_WORKSPACE_ID,),
        database=database,
    )

    assert (seeded, reset) == ([], [])
    assert records == [{"title": "Data quality analyst", "link": "pack_crosswalk"}]
