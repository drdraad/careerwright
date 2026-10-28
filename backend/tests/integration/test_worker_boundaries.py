"""What a worker may do is decided by the database, run by run (SEC-02, GC7), and spend is
reserved server-side before every call (MODEL-08). Also: a database outage ends in a typed
terminal state (DUR-08) and the Contributor model never sees non-synthetic data (MODEL-02)."""

import threading
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from nessa.identity import connection_check
from tests.integration.durable import Scenario, make_scenario
from tests.support.client import ApiClient
from tests.support.infra import Infra, create_emulator_user, sign_in
from tests.support.workers import wait_for

pytestmark = pytest.mark.integration


@pytest.fixture
def scenario(infra: Infra, api: ApiClient, ada: str, tmp_path: Path) -> Iterator[Scenario]:
    started = make_scenario(infra, api, ada, tmp_path)
    yield started
    for worker in started.workers:
        worker.kill_if_running()


def fresh_actor(api: ApiClient, infra: Infra) -> tuple[str, str]:
    uid = f"actor-{uuid.uuid4().hex[:8]}"
    email = f"{uid}@nessa.test"
    create_emulator_user(uid, email, "password-123456")
    infra.query(
        "INSERT INTO nessa.actors (actor_id, email, display_name, access) "
        "VALUES (%s, %s, 'Fresh', 'active')",
        (uuid.uuid4(), email),
    )
    return email, sign_in(email, "password-123456")


@pytest.mark.req("SEC-02", "ARC1-08", "SEC-01")
def test_the_worker_role_sees_only_the_run_it_executes(
    scenario: Scenario, api: ApiClient, ben: str, infra: Infra
) -> None:
    run_id = scenario.submit()
    other = make_scenario(infra, api, ben, scenario.log_dir)
    other_run = other.submit()
    count = "SELECT count(*) AS n FROM nessa.{} WHERE workspace_id = %s"

    def visible(table: str, workspace: str, run: str | None) -> int:
        rows = infra.as_role("pg_worker", count.format(table), (workspace,), run=run)
        return int(str(rows[0]["n"]))

    for table in ("credentials", "runs", "workspaces"):
        assert visible(table, scenario.workspace_id, run_id) == 1, table
        assert visible(table, other.workspace_id, run_id) == 0, table  # another workspace
        assert visible(table, scenario.workspace_id, None) == 0, table  # no run context
    assert visible("credentials", other.workspace_id, other_run) == 1
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        infra.as_role("pg_worker", "SELECT * FROM nessa.profile_versions", run=run_id)


@pytest.mark.req("SEC-01", "SEC-02")
def test_revoking_access_while_a_run_is_queued_hides_the_key_from_the_worker(
    api: ApiClient, infra: Infra, tmp_path: Path
) -> None:
    email, token = fresh_actor(api, infra)
    scenario = make_scenario(infra, api, token, tmp_path)
    run_id = scenario.submit()
    infra.query("UPDATE nessa.actors SET access = 'revoked' WHERE email = %s", (email,))

    rows = infra.as_role(
        "pg_worker",
        "SELECT count(*) AS n FROM nessa.credentials WHERE workspace_id = %s",
        (scenario.workspace_id,),
        run=run_id,
    )
    worker = scenario.worker("worker")
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert rows[0]["n"] == 0
    assert (run["status"], run["failure_class"]) == ("failed", "access_revoked")
    assert [a["spend_state"] for a in scenario.attempts(run_id)] == ["none"]
    assert scenario.leaks() == []


@pytest.mark.req("MODEL-02")
def test_the_contributor_model_is_refused_for_non_synthetic_data_at_every_layer(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    real = api.create_workspace(ada, "Real person (not synthetic)", synthetic=False)
    api.write(
        "POST",
        f"/v1/workspaces/{real['workspace_id']}/credentials",
        ada,
        {"api_key": "x" * 40, "consent_to_encrypted_storage": True},
    )

    submitted = api.write(
        "POST", f"/v1/workspaces/{real['workspace_id']}/runs", ada, {"kind": "connection_check"}
    )

    # The API never offers the test model to non-synthetic data: it pins the Standard model.
    assert submitted.status_code == 202
    assert (submitted.json()["model_id"], submitted.json()["model_mode"]) == (
        "muse-spark-1.3",
        "standard",
    )
    # And the database refuses a Contributor run on non-synthetic data outright.
    with pytest.raises(
        psycopg.errors.CheckViolation, match="contributor_models_only_for_synthetic_data"
    ):
        infra.query(
            "INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, "
            "requested_by, model_id, model_mode, status) SELECT %s, workspace_id, data_mode, "
            "synthetic, 'connection_check', owner_actor_id, 'muse-spark-1.3-contributor', "
            "'contributor', 'queued' FROM nessa.workspaces WHERE workspace_id = %s",
            (uuid.uuid4(), real["workspace_id"]),
        )


def test_synthetic_runs_use_the_test_model(scenario: Scenario) -> None:
    run = scenario.api_run(scenario.submit())

    assert (run["model_id"], run["model_mode"], run["synthetic"]) == (
        "muse-spark-1.3-contributor",
        "contributor",
        True,
    )


@pytest.mark.req("MODEL-08")
def test_a_run_that_cannot_fit_the_spend_limit_is_refused_at_submission(scenario: Scenario) -> None:
    path = f"/v1/workspaces/{scenario.workspace_id}"
    spend = scenario.api.get(f"{path}/spend", scenario.token).json()
    scenario.api.write(
        "PUT",
        f"{path}/spend/limits",
        scenario.token,
        {"expected_version": spend["version"], "run_limit_nano_usd": 1, "period_limit_nano_usd": 1},
    )

    refused = scenario.api.write(
        "POST", f"{path}/runs", scenario.token, {"kind": "connection_check"}
    )

    assert (refused.status_code, refused.json()["error"]["code"]) == (402, "BUDGET_EXCEEDED")
    assert refused.json()["error"]["details"] == {"scope": "run"}


@pytest.mark.req("MODEL-08")
def test_concurrent_calls_cannot_reserve_past_the_period_limit(scenario: Scenario) -> None:
    worst = connection_check.worst_case_nano_usd("muse-spark-1.3-contributor")
    path = f"/v1/workspaces/{scenario.workspace_id}"
    spend = scenario.api.get(f"{path}/spend", scenario.token).json()
    limits = scenario.api.write(
        "PUT",
        f"{path}/spend/limits",
        scenario.token,
        {
            "expected_version": spend["version"],
            "run_limit_nano_usd": worst,
            "period_limit_nano_usd": worst + worst // 2,  # room for one call, not two
        },
    )
    assert limits.status_code == 200, limits.text
    runs = [scenario.submit() for _ in range(3)]

    worker = scenario.worker("worker", fake_delay_s="2")
    finished = [scenario.wait_terminal(run_id) for run_id in runs]
    worker.stop()

    outcomes = sorted((r["status"], r["failure_class"]) for r in finished)
    assert outcomes == [
        ("complete", None),
        ("failed", "budget_exceeded"),
        ("failed", "budget_exceeded"),
    ]
    summary = scenario.api.get(f"{path}/spend", scenario.token).json()
    assert summary["period_committed_nano_usd"] <= summary["period_limit_nano_usd"]
    assert summary["unknown_cost_attempts"] == 0


def cut_worker_database_for(infra: Infra, seconds: float) -> threading.Thread:
    """The worker's database role loses its connections for `seconds` (DBOS's own database
    stays up), as in a restart of the application database."""
    infra.query("ALTER ROLE nessa_worker NOLOGIN")
    infra.query(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'nessa_worker'"
    )

    def restore() -> None:
        time.sleep(seconds)
        infra.query("ALTER ROLE nessa_worker LOGIN")

    restorer = threading.Thread(target=restore)
    restorer.start()
    return restorer


@pytest.mark.req("DUR-08")
def test_a_short_app_database_outage_mid_call_keeps_the_paid_result(
    scenario: Scenario, infra: Infra
) -> None:
    """B-M5: the call succeeds while the database is away; the activity keeps its result and
    retries storing it within its store budget, so the run completes on that one call."""
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_delay_s="3")
    wait_for(lambda: len(scenario.attempts(run_id)) == 1, timeout_s=30, what="attempt")

    restorer = cut_worker_database_for(infra, 12)
    try:
        run = scenario.wait_terminal(run_id, timeout_s=120)
    finally:
        restorer.join()
        infra.query("ALTER ROLE nessa_worker LOGIN")
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("complete", None)
    [attempt] = scenario.attempts(run_id)
    assert (attempt["outcome"], attempt["spend_state"]) == ("succeeded", "reconciled")
    assert scenario.leaks() == []


@pytest.mark.req("DUR-08")
def test_an_outage_longer_than_the_store_budget_ends_in_a_typed_terminal_state(
    scenario: Scenario, infra: Infra
) -> None:
    """Past the store budget the run fails `app_store_unavailable` once the database is back
    (publication keeps retrying), never left queued or running, and never re-calls."""
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_delay_s="3", store_retry_budget_s="2")
    wait_for(lambda: len(scenario.attempts(run_id)) == 1, timeout_s=30, what="attempt")

    restorer = cut_worker_database_for(infra, 12)
    try:
        run = scenario.wait_terminal(run_id, timeout_s=120)
    finally:
        restorer.join()
        infra.query("ALTER ROLE nessa_worker LOGIN")
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "app_store_unavailable")
    [attempt] = scenario.attempts(run_id)
    # The call happened but its result could not be stored: an unknown charge, settled.
    assert (attempt["outcome"], attempt["spend_state"]) == ("interrupted", "unknown")
    assert attempt["finished_at"] is not None
    assert scenario.leaks() == []
