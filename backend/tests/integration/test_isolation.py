"""Another actor's workspace is invisible through the API and in the database itself (SEC-01,
SEC-02): the runtime role is not the table owner, so row-level security applies to it."""

import uuid

import psycopg
import pytest

from careerwright.seed import FIXTURE_WORKSPACE_ID, INVITED_ACTORS
from tests.integration.durable import make_scenario
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
        "SELECT version, name FROM careerwright.workspaces WHERE workspace_id = %s",
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
            "SELECT version, name FROM careerwright.workspaces WHERE workspace_id = %s",
            (FIXTURE_WORKSPACE_ID,),
        )
        == before
    )


@pytest.mark.req("SEC-01", "DUR-03")
def test_runs_keys_and_spend_of_another_actor_are_invisible(
    api: ApiClient, ada: str, ben: str
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    base = f"/v1/workspaces/{workspace_id}"
    api.write(
        "POST",
        f"{base}/credentials",
        ada,
        {"api_key": "k" * 40, "consent_to_encrypted_storage": True},
    )
    submitted = api.write("POST", f"{base}/runs", ada, {"kind": "connection_check"})
    run_id = submitted.json()["run_id"]

    assert submitted.status_code == 202
    assert submitted.headers["location"] == f"{base}/runs/{run_id}"
    assert submitted.json()["status"] == "queued"
    for path in (f"{base}/runs/{run_id}", f"{base}/runs", f"{base}/credentials", f"{base}/spend"):
        assert api.get(path, ben).status_code == 404, path
    assert api.write("POST", f"{base}/runs", ben, {"kind": "connection_check"}).status_code == 404


@pytest.mark.req("SEC-02", "ARC1-08")
@pytest.mark.parametrize("table", WORKSPACE_TABLES)
def test_the_api_role_sees_no_rows_of_another_actors_workspace(infra: Infra, table: str) -> None:
    statement = f"SELECT count(*) AS n FROM careerwright.{table} WHERE workspace_id = %s"  # noqa: S608

    as_owner = infra.as_role("pg_api", statement, (FIXTURE_WORKSPACE_ID,), actor=ADA)
    as_other = infra.as_role("pg_api", statement, (FIXTURE_WORKSPACE_ID,), actor=BEN)
    with_no_actor = infra.as_role("pg_api", statement, (FIXTURE_WORKSPACE_ID,))

    assert int(str(as_owner[0]["n"])) >= 1
    assert as_other[0]["n"] == with_no_actor[0]["n"] == 0


EXECUTION_TABLES = (
    "credentials",
    "spend_limits",
    "runs",
    "run_outputs",
    "model_attempts",
    "outbox",
)


@pytest.fixture(scope="module")
def completed_run_workspace(
    infra: Infra, api: ApiClient, ada: str, tmp_path_factory: pytest.TempPathFactory
) -> str:
    """Ada's workspace holding a key, spend limits, and a completed run with its output,
    attempts and outbox entry: a row in every execution table."""
    scenario = make_scenario(infra, api, ada, tmp_path_factory.mktemp("isolation-run"))
    run_id = scenario.submit()
    worker = scenario.worker("worker")
    try:
        assert scenario.wait_terminal(run_id)["status"] == "complete"
    finally:
        worker.stop()
    return scenario.workspace_id


@pytest.mark.req("SEC-02", "ARC1-08")
@pytest.mark.parametrize("table", EXECUTION_TABLES)
def test_the_api_role_sees_no_execution_rows_of_another_actors_workspace(
    infra: Infra, completed_run_workspace: str, table: str
) -> None:
    # count(workspace_id): the API role holds column-level SELECT on credentials.
    statement = f"SELECT count(workspace_id) AS n FROM careerwright.{table} WHERE workspace_id = %s"  # noqa: S608

    as_owner = infra.as_role("pg_api", statement, (completed_run_workspace,), actor=ADA)
    as_other = infra.as_role("pg_api", statement, (completed_run_workspace,), actor=BEN)
    with_no_actor = infra.as_role("pg_api", statement, (completed_run_workspace,))

    assert int(as_owner[0]["n"]) >= 1
    assert as_other[0]["n"] == with_no_actor[0]["n"] == 0


@pytest.mark.req("SEC-02")
def test_the_database_refuses_rows_written_into_another_actors_workspace(infra: Infra) -> None:
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        infra.as_role(
            "pg_api",
            "INSERT INTO careerwright.workspace_events (workspace_id, seq, kind, subject_id) "
            "VALUES (%s, 999, 'workspace.updated', 'forged')",
            (FIXTURE_WORKSPACE_ID,),
            actor=BEN,
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        infra.as_role(
            "pg_api",
            "INSERT INTO careerwright.workspaces (workspace_id, owner_actor_id, name, data_mode, "
            "synthetic) VALUES (%s, %s, 'Planted on Ada', 'demo', true)",
            (uuid.uuid4(), ADA),
            actor=BEN,
        )


@pytest.mark.req("SEC-02", "ARC1-08")
def test_runtime_roles_are_not_owners_and_cannot_bypass_row_security(infra: Infra) -> None:
    roles = infra.query(
        "SELECT rolname, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles "
        "WHERE rolname IN ('careerwright_api', 'careerwright_worker', 'careerwright_dbos_runtime')"
    )
    owners = infra.query(
        "SELECT DISTINCT tableowner FROM pg_tables WHERE schemaname = 'careerwright'"
    )

    assert len(roles) == 3
    assert all(
        not any((r["rolsuper"], r["rolbypassrls"], r["rolcreaterole"], r["rolcreatedb"]))
        for r in roles
    )
    assert owners == [{"tableowner": "careerwright_migrator"}]
    dbos_owners = infra.query(
        "SELECT DISTINCT tableowner FROM pg_tables WHERE schemaname = 'dbos'",
        database="careerwright_dbos",
    )
    assert dbos_owners == [{"tableowner": "careerwright_dbos_owner"}]
    rls = infra.query(
        "SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'careerwright' AND c.relkind = 'r' AND NOT c.relrowsecurity"
    )
    assert rls == []  # every application table has row-level security enabled


@pytest.mark.req("SEC-02")
def test_profile_history_is_append_only_for_the_api_role(infra: Infra) -> None:
    for statement in (
        "UPDATE careerwright.profile_versions SET document = '{}'::jsonb",
        "DELETE FROM careerwright.profile_versions",
        "DELETE FROM careerwright.workspace_events",
        "UPDATE careerwright.source_references SET label = 'x'",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            infra.as_role("pg_api", statement, actor=ADA)
