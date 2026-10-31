"""Each target is stored once, and every chapter reads that record (Task 6d slice A; PROF-10;
the audit's code appendix, finding F5), against real PostgreSQL 16 and the ESCO sample: a
punctuated plural, an accented title and an "&" title resolve the same in the slate, the
sketch, the strength, Skills and the world, and the record says how far Careerwright can
cover the target."""

import uuid
from typing import Any

import pytest

from careerwright.catalogue.esco import concept_id
from careerwright.db import system_transaction
from careerwright.profile import store, titles
from careerwright.profile.targets import stored_targets
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra, migrator_engine

pytestmark = pytest.mark.integration

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
            resolved = titles.targets(tx, stored_targets(tx, uuid.UUID(workspace), latest.document))
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
    assert [(t["resolution"], t["coverage"]) for t in sketch] == [
        ("not_found", "pack_target"),
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
    assert [(t["title"], t["resolution"], t["coverage"]) for t in sketch] == [
        (title, "not_found", "pack_target") for title in covered
    ]
    matrices = get(api, ada, f"/v1/workspaces/{workspace}/capability/matrices")["matrices"]
    assert {
        m["target_title"]: (m["sources"]["pack_target"]["target_id"],
                            m["sources"]["pack_target"]["basis"])
        for m in matrices
    } == {title: (target, "title") for title, target in covered.items()}  # fmt: skip
