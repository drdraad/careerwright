"""Workspaces and profiles: expected-version writes, idempotent commands, source references."""

import threading
import uuid
from typing import Any

import psycopg
import pytest

from nessa.seed import FIXTURE_SOURCE_ID, FIXTURE_WORKSPACE_ID, INVITED_ACTORS
from tests.support.client import ApiClient, profile_with, unasked_profile
from tests.support.infra import Infra, create_emulator_user, sign_in

pytestmark = pytest.mark.integration


def put_profile(
    api: ApiClient, token: str, workspace_id: str, expected: int, profile: dict[str, Any], **kw: Any
) -> Any:
    return api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        token,
        {"expected_version": expected, "profile": profile},
        **kw,
    )


@pytest.mark.req("BND1-10", "BND1-12")
def test_workspace_records_its_data_mode_and_permanent_synthetic_label(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace = api.create_workspace(ada, "Live but synthetic", synthetic=True)

    assert (workspace["data_mode"], workspace["synthetic"], workspace["version"]) == (
        "live_assisted",
        True,
        1,
    )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        infra.as_role(
            "pg_api",
            "UPDATE nessa.workspaces SET synthetic = false WHERE workspace_id = %s",
            (workspace["workspace_id"],),
            actor=str(INVITED_ACTORS[0].actor_id),
        )


def test_demo_workspaces_are_always_synthetic_and_live_vacancy_is_refused(
    api: ApiClient, ada: str
) -> None:
    demo = api.write(
        "POST", "/v1/workspaces", ada, {"name": "d", "data_mode": "demo", "synthetic": False}
    )
    vacancy = api.write(
        "POST", "/v1/workspaces", ada, {"name": "v", "data_mode": "live_vacancy", "synthetic": True}
    )

    assert demo.json()["error"]["code"] == "VALIDATION_FAILED"
    assert (vacancy.status_code, vacancy.json()["error"]["code"]) == (422, "MODE_NOT_SUPPORTED")


@pytest.mark.req("API-01")
def test_writes_need_an_idempotency_key(api: ApiClient, ada: str) -> None:
    response = api.http.post(
        "/v1/workspaces",
        json={"name": "x", "data_mode": "live_assisted", "synthetic": True},
        headers={"Authorization": f"Bearer {ada}", "Origin": "http://127.0.0.1:57300"},
    )

    assert (response.status_code, response.json()["error"]["code"]) == (
        400,
        "IDEMPOTENCY_KEY_REQUIRED",
    )


@pytest.mark.req("API-01")
def test_a_retried_command_returns_the_first_result_and_acts_once(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    key = uuid.uuid4()
    body = {"name": f"Retried {key}", "data_mode": "live_assisted", "synthetic": True}

    first = api.write("POST", "/v1/workspaces", ada, body, key=key)
    second = api.write("POST", "/v1/workspaces", ada, body, key=key)
    different = api.write("POST", "/v1/workspaces", ada, {**body, "name": "other"}, key=key)

    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json() == second.json()
    assert (
        infra.query("SELECT count(*) AS n FROM nessa.workspaces WHERE name = %s", (body["name"],))[
            0
        ]["n"]
        == 1
    )
    assert (different.status_code, different.json()["error"]["code"]) == (
        422,
        "IDEMPOTENCY_KEY_REUSED",
    )


def test_concurrent_duplicates_of_one_command_create_one_workspace(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    key = uuid.uuid4()
    body = {"name": f"Raced {key}", "data_mode": "live_assisted", "synthetic": True}
    results: list[Any] = []

    def send() -> None:
        results.append(api.write("POST", "/v1/workspaces", ada, body, key=key))

    threads = [threading.Thread(target=send) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert {r.status_code for r in results} == {201}
    assert len({r.json()["workspace_id"] for r in results}) == 1
    assert (
        infra.query("SELECT count(*) AS n FROM nessa.workspaces WHERE name = %s", (body["name"],))[
            0
        ]["n"]
        == 1
    )


@pytest.mark.req("VERSIONS-01")
def test_rename_with_a_stale_version_is_rejected(api: ApiClient, ada: str) -> None:
    workspace = api.create_workspace(ada)
    path = f"/v1/workspaces/{workspace['workspace_id']}"

    renamed = api.write("PATCH", path, ada, {"expected_version": 1, "name": "Renamed"})
    stale = api.write("PATCH", path, ada, {"expected_version": 1, "name": "Lost update"})

    assert (renamed.status_code, renamed.json()["version"]) == (200, 2)
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert stale.json()["error"]["details"] == {"current_version": 2}
    assert api.get(path, ada).json()["name"] == "Renamed"


@pytest.mark.req("VERSIONS-01", "PROF-05")
def test_profile_writes_create_versions_and_reject_stale_expected_versions(
    api: ApiClient, ada: str
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    path = f"/v1/workspaces/{workspace_id}/profile"
    assert api.get(path, ada).json()["version"] == 0  # nothing saved yet, never a fake v1

    first = put_profile(api, ada, workspace_id, 0, profile_with(cities=["Leeds"]))
    stale = put_profile(api, ada, workspace_id, 0, profile_with(cities=["York"]))
    second = put_profile(api, ada, workspace_id, 1, profile_with(cities=["York"]))

    assert (first.status_code, first.json()["version"]) == (201, 1)
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert stale.json()["error"]["details"] == {"current_version": 1}
    assert (second.status_code, second.json()["version"]) == (201, 2)
    current = api.get(path, ada).json()
    assert current["document"]["cities"]["value"] == ["York"]
    old = api.get(f"{path}/versions/1", ada).json()
    assert old["document"]["cities"]["value"] == ["Leeds"]  # old versions are immutable


def test_an_unchanged_profile_write_creates_no_version(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    put_profile(api, ada, workspace_id, 0, profile_with(cities=["Leeds"]))

    again = put_profile(api, ada, workspace_id, 1, profile_with(cities=["Leeds"]))

    assert (again.status_code, again.json()["version"]) == (200, 1)


@pytest.mark.req("VERSIONS-01", "DUR-04")
def test_concurrent_writes_from_one_version_commit_exactly_one(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    results: list[Any] = []

    def write(city: str) -> None:
        results.append(put_profile(api, ada, workspace_id, 0, profile_with(cities=[city])))

    threads = [threading.Thread(target=write, args=(c,)) for c in ("Leeds", "York", "Hull", "Bath")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    statuses = sorted(r.status_code for r in results)
    assert statuses == [201, 409, 409, 409]
    versions = api.get(f"/v1/workspaces/{workspace_id}/profile/versions", ada).json()["items"]
    assert [v["version"] for v in versions] == [1]


@pytest.mark.req("BND1-03")
def test_a_fourth_city_is_rejected_and_nothing_is_saved(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]

    response = put_profile(
        api, ada, workspace_id, 0, profile_with(cities=["Leeds", "York", "Hull", "Bath"])
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "LIMIT_EXCEEDED"
    assert response.json()["error"]["details"] == {"field": "cities", "limit": 3}
    assert api.get(f"/v1/workspaces/{workspace_id}/profile", ada).json()["version"] == 0


@pytest.mark.req("API-04")
def test_unknown_money_is_null_not_zero_and_states_round_trip(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    profile = unasked_profile()
    profile["direct_spend_cap"] = {"state": "unknown"}
    profile["monthly_payment_cap"] = {"state": "prefer_not_to_say"}
    profile["current_role"] = {"state": "skipped"}

    put_profile(api, ada, workspace_id, 0, profile)

    document = api.get(f"/v1/workspaces/{workspace_id}/profile", ada).json()["document"]
    assert document["direct_spend_cap"]["state"] == "unknown"
    assert document["direct_spend_cap"]["value"] is None
    assert document["monthly_payment_cap"]["state"] == "prefer_not_to_say"
    assert document["current_role"]["state"] == "skipped"
    assert document["preferred_name"] == {"state": "unasked", "value": None, "source_ref_id": None}


def test_answers_cite_server_assigned_direct_entry_sources(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    put_profile(api, ada, workspace_id, 0, profile_with(cities=["Leeds"]))
    put_profile(api, ada, workspace_id, 1, profile_with(cities=["Leeds"], current_role="Analyst"))

    document = api.get(f"/v1/workspaces/{workspace_id}/profile", ada).json()["document"]
    sources = api.get(f"/v1/workspaces/{workspace_id}/sources", ada).json()["items"]

    assert len(sources) == 2
    assert {s["kind"] for s in sources} == {"direct_entry"}
    by_order = [s["source_ref_id"] for s in sources]
    assert document["cities"]["source_ref_id"] == by_order[0]  # unchanged answer keeps its source
    assert document["current_role"]["source_ref_id"] == by_order[1]


def test_clients_cannot_submit_their_own_source_references(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    profile = profile_with(cities=["Leeds"])
    profile["cities"]["source_ref_id"] = str(uuid.uuid4())

    response = put_profile(api, ada, workspace_id, 0, profile)

    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_FAILED")


@pytest.mark.req("BND1-12")
def test_the_fixture_workspace_cites_the_pinned_fixture_file(api: ApiClient, ada: str) -> None:
    profile = api.get(f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}/profile", ada).json()
    [source] = api.get(f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}/sources", ada).json()["items"]
    workspace = api.get(f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}", ada).json()

    assert (workspace["data_mode"], workspace["synthetic"], workspace["fixture"]) == (
        "demo",
        True,
        True,
    )
    assert profile["document"]["direct_spend_cap"]["value"] == {
        "minor_units": 150000,
        "currency": "GBP",
    }
    assert profile["document"]["direct_spend_cap"]["source_ref_id"] == str(FIXTURE_SOURCE_ID)
    assert (source["kind"], source["locator"]) == ("fixture", "fixtures/m0/personas/P01.json")
    assert (
        source["content_sha256"]
        == "03e72eefa7f975fc50c075a17f2136a0f39385efce25ccdb2834b5f9a5ec518e"
    )
    # Fields the fixture does not hold are unasked, never filled in.
    assert profile["document"]["weekly_study_hours"]["state"] == "unasked"


@pytest.mark.req("API-01")
def test_workspace_list_paginates_with_an_opaque_cursor(api: ApiClient, infra: Infra) -> None:
    uid = f"pager-{uuid.uuid4().hex[:8]}"
    email = f"{uid}@nessa.test"
    create_emulator_user(uid, email, "password-123456")
    infra.query(
        "INSERT INTO nessa.actors (actor_id, email, display_name, access) "
        "VALUES (%s, %s, 'P', 'active')",
        (uuid.uuid4(), email),
    )
    token = sign_in(email, "password-123456")
    created = [api.create_workspace(token, f"W{i}")["workspace_id"] for i in range(5)]

    first = api.get("/v1/workspaces", token, limit=2).json()
    second = api.get("/v1/workspaces", token, limit=2, cursor=first["next_cursor"]).json()
    third = api.get("/v1/workspaces", token, limit=2, cursor=second["next_cursor"]).json()
    bad = api.get("/v1/workspaces", token, cursor="not-a-cursor")

    seen = [w["workspace_id"] for page in (first, second, third) for w in page["items"]]
    assert seen == created
    assert third["next_cursor"] is None
    assert bad.json()["error"]["code"] == "VALIDATION_FAILED"
