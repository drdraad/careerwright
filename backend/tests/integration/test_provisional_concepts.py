"""Provisional occupation concepts: verified titles outside ESCO stay private internal
concepts, never fabricated ESCO records (DIV1-03; spec section 4, DIV-1)."""

import pytest
from psycopg import errors

from tests.support.client import ApiClient
from tests.support.infra import Infra

pytestmark = pytest.mark.integration


def register(api: ApiClient, token: str, workspace_id: str, title: str) -> tuple[int, dict]:  # type: ignore[type-arg]
    response = api.write(
        "POST", f"/v1/workspaces/{workspace_id}/occupations/provisional", token, {"title": title}
    )
    return response.status_code, response.json()


@pytest.mark.req("DIV1-03")
def test_a_title_esco_lacks_becomes_a_provisional_concept_citing_the_confirmation(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace = api.create_workspace(ada, "Provisional concepts")["workspace_id"]

    status, concept = register(api, ada, workspace, "Drone survey pilot")

    assert status == 201
    assert concept["title"] == "Drone survey pilot"
    assert set(concept) == {"concept_id", "title", "source_ref_id", "created_by", "created_at"}
    [row] = infra.query(
        "SELECT * FROM nessa.provisional_concepts WHERE concept_id = %s", (concept["concept_id"],)
    )
    assert "esco_uri" not in row  # structurally not an ESCO record
    assert "isco_code" not in row
    assert infra.query(
        "SELECT count(*) AS n FROM nessa.occupation_concepts WHERE concept_id = %s",
        (concept["concept_id"],),
    ) == [{"n": 0}]
    [source] = infra.query(
        "SELECT kind, recorded_by FROM nessa.source_references WHERE source_ref_id = %s",
        (concept["source_ref_id"],),
    )
    assert source["kind"] == "direct_entry"
    again_status, again = register(api, ada, workspace, "  drone   SURVEY pilot ")
    assert (again_status, again["concept_id"]) == (200, concept["concept_id"])
    listed = api.get(f"/v1/workspaces/{workspace}/occupations/provisional", ada).json()
    assert [c["concept_id"] for c in listed["items"]] == [concept["concept_id"]]


@pytest.mark.req("DIV1-03")
def test_an_esco_title_or_alias_is_refused_with_the_occupations_that_hold_it(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Provisional ESCO title")["workspace_id"]
    holders = api.get("/v1/taxonomy/occupations", ada, q="bus operator").json()["label_matches"]

    status, refused = register(api, ada, workspace, "Bus operator")

    assert status == 422
    assert refused["error"]["details"]["reason"] == "in_taxonomy"
    assert refused["error"]["details"]["concept_ids"] == sorted(h["concept_id"] for h in holders)
    assert api.get(f"/v1/workspaces/{workspace}/occupations/provisional", ada).json()["items"] == []


def test_another_account_cannot_see_or_add_to_a_workspace_s_concepts(
    api: ApiClient, ada: str, ben: str
) -> None:
    workspace = api.create_workspace(ada, "Private concepts")["workspace_id"]
    register(api, ada, workspace, "Heritage roof thatcher apprentice")

    assert api.get(f"/v1/workspaces/{workspace}/occupations/provisional", ben).status_code == 404
    assert register(api, ben, workspace, "Anything")[0] == 404


def test_the_database_refuses_a_provisional_concept_with_an_esco_title(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace = api.create_workspace(ada, "Trigger check")["workspace_id"]
    _, concept = register(api, ada, workspace, "Wind turbine rope access tech")
    [row] = infra.query(
        "SELECT * FROM nessa.provisional_concepts WHERE concept_id = %s", (concept["concept_id"],)
    )

    with pytest.raises(errors.CheckViolation):
        infra.query(
            "INSERT INTO nessa.provisional_concepts (concept_id, workspace_id, title, "
            "normalised_title, source_ref_id, created_by) VALUES (gen_random_uuid(), %s, "
            "'plumber', 'plumber', %s, %s)",
            (workspace, row["source_ref_id"], row["created_by"]),
        )
