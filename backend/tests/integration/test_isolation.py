"""Another actor's workspace is invisible through the API and in the database itself (SEC-01,
SEC-02): the runtime role is not the table owner, so row-level security applies to it."""

import uuid

import psycopg
import pytest

from nessa.seed import FIXTURE_WORKSPACE_ID, INVITED_ACTORS
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra

pytestmark = pytest.mark.integration

ADA, BEN = (str(actor.actor_id) for actor in INVITED_ACTORS)
WORKSPACE_TABLES = (
    "workspaces",
    "profile_versions",
    "profile_version_sources",
    "source_references",
    "workspace_events",
)


@pytest.mark.req("SEC-01")
def test_every_endpoint_hides_another_actors_workspace(api: ApiClient, ben: str) -> None:
    base = f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}"
    for path in (
        base,
        f"{base}/profile",
        f"{base}/profile/versions",
        f"{base}/profile/versions/1",
        f"{base}/sources",
        f"{base}/events",
        f"{base}/events/stream",
        f"{base}/export",
    ):
        response = api.get(path, ben)
        assert (response.status_code, response.json()["error"]["code"]) == (404, "NOT_FOUND"), path
    assert str(FIXTURE_WORKSPACE_ID) not in api.get("/v1/workspaces", ben).text


@pytest.mark.req("SEC-01")
def test_writes_to_another_actors_workspace_fail_and_change_nothing(
    api: ApiClient, ben: str, infra: Infra
) -> None:
    before = infra.query(
        "SELECT version, name FROM nessa.workspaces WHERE workspace_id = %s",
        (FIXTURE_WORKSPACE_ID,),
    )
    base = f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}"

    rename = api.write("PATCH", base, ben, {"expected_version": 1, "name": "Taken over"})
    profile = api.write(
        "PUT",
        f"{base}/profile",
        ben,
        {"expected_version": 1, "profile": profile_with(cities=["X"])},
    )

    assert rename.status_code == profile.status_code == 404
    assert (
        infra.query(
            "SELECT version, name FROM nessa.workspaces WHERE workspace_id = %s",
            (FIXTURE_WORKSPACE_ID,),
        )
        == before
    )


@pytest.mark.req("SEC-02", "ARC1-08")
@pytest.mark.parametrize("table", WORKSPACE_TABLES)
def test_the_api_role_sees_no_rows_of_another_actors_workspace(infra: Infra, table: str) -> None:
    statement = f"SELECT count(*) AS n FROM nessa.{table} WHERE workspace_id = %s"  # noqa: S608

    as_owner = infra.as_role("pg_api", statement, (FIXTURE_WORKSPACE_ID,), actor=ADA)
    as_other = infra.as_role("pg_api", statement, (FIXTURE_WORKSPACE_ID,), actor=BEN)
    with_no_actor = infra.as_role("pg_api", statement, (FIXTURE_WORKSPACE_ID,))

    assert int(str(as_owner[0]["n"])) >= 1
    assert as_other[0]["n"] == with_no_actor[0]["n"] == 0


@pytest.mark.req("SEC-02")
def test_the_database_refuses_rows_written_into_another_actors_workspace(infra: Infra) -> None:
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        infra.as_role(
            "pg_api",
            "INSERT INTO nessa.workspace_events (workspace_id, seq, kind, subject_id) "
            "VALUES (%s, 999, 'workspace.updated', 'forged')",
            (FIXTURE_WORKSPACE_ID,),
            actor=BEN,
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        infra.as_role(
            "pg_api",
            "INSERT INTO nessa.workspaces (workspace_id, owner_actor_id, name, data_mode, "
            "synthetic) VALUES (%s, %s, 'Planted on Ada', 'demo', true)",
            (uuid.uuid4(), ADA),
            actor=BEN,
        )


@pytest.mark.req("SEC-02", "ARC1-08")
def test_runtime_roles_are_not_owners_and_cannot_bypass_row_security(infra: Infra) -> None:
    roles = infra.query(
        "SELECT rolname, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles "
        "WHERE rolname IN ('nessa_api', 'nessa_worker', 'nessa_dbos_runtime')"
    )
    owners = infra.query("SELECT DISTINCT tableowner FROM pg_tables WHERE schemaname = 'nessa'")

    assert len(roles) == 3
    assert all(
        not any((r["rolsuper"], r["rolbypassrls"], r["rolcreaterole"], r["rolcreatedb"]))
        for r in roles
    )
    assert owners == [{"tableowner": "nessa_migrator"}]
    rls = infra.query(
        "SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'nessa' AND c.relkind = 'r' AND NOT c.relrowsecurity"
    )
    assert rls == []  # every application table has row-level security enabled


@pytest.mark.req("SEC-02")
def test_profile_history_is_append_only_for_the_api_role(infra: Infra) -> None:
    for statement in (
        "UPDATE nessa.profile_versions SET document = '{}'::jsonb",
        "DELETE FROM nessa.profile_versions",
        "DELETE FROM nessa.workspace_events",
        "UPDATE nessa.source_references SET label = 'x'",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            infra.as_role("pg_api", statement, actor=ADA)
