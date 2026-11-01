"""The product owner's live session (Task 3b; ADR 0003, amendment of 2026-10-31), offline:
with Muse Wonder configured as the production model the API and the worker start and a
synthetic workspace still runs the test model; the session's caps go on each live workspace
not marked synthetic and the product's own checks hold them; the estimate before a run
states its maxima; and the ledger copy reads counts, cost and state only. The worker's model
is the fake: nothing contacts Meta."""

import dataclasses
import secrets
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
import pytest
from fastapi.testclient import TestClient

from careerwright.api.app import create_app
from careerwright.api.deps import ApiDependencies
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.model_registry import WONDER_MODEL_ID, Usage, estimate_cost_nano_usd
from careerwright.profile import interview
from careerwright.seed import FIXTURE_WORKSPACE_ID
from tests.integration.durable import fresh_actor
from tests.support.client import ApiClient, profile_with
from tests.support.infra import API_BASE, HOST, TEST_PORTS, WEB_ORIGIN, Infra
from tests.support.workers import start_worker, wait_for
from tools.live_smoke import Api
from tools.session import (
    COPIED_COLUMNS,
    SESSION_RUN_LIMIT_NANO_USD,
    SESSION_SPEND_PER_WORKSPACE_NANO_USD,
    copy_session_calls,
    set_session_caps,
)
from tools.usage_ledger import Ledger

pytestmark = pytest.mark.integration
TEST_MODEL = "muse-spark-1.3-contributor"
TERMINAL = {"complete", "failed", "provider_unavailable", "cancelled"}


@dataclass(frozen=True)
class Session:
    """What a Wonder-configured stack did for one fresh person, with the text it must
    never copy."""

    api: ApiClient
    token: str
    personal: str
    synthetic: str
    turn_run: str
    check_run: str
    message: str
    output_sentinel: str
    profile_sentinel: str
    api_key: str


@pytest.fixture(scope="module")
def wonder_api(api_deps: ApiDependencies) -> Iterator[ApiClient]:
    """The API as `make session` configures it: Wonder the production model, the synthetic
    role the test model, and the session's caps as the default limits (Spark's defaults
    would refuse every Wonder interview turn: $0.176 at worst against $0.15)."""
    models = ModelChoice.configure(api_deps.settings.meta_test_model, WONDER_MODEL_ID, "test")
    settings = api_deps.settings.model_copy(
        update={
            "default_run_spend_limit_nano_usd": SESSION_RUN_LIMIT_NANO_USD,
            "default_period_spend_limit_nano_usd": SESSION_SPEND_PER_WORKSPACE_NANO_USD,
        }
    )
    with TestClient(
        create_app(dataclasses.replace(api_deps, models=models, settings=settings)),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57001),
    ) as client:
        yield ApiClient(client)


def _workspace(api: ApiClient, token: str, *, synthetic: bool, key: str) -> str:
    workspace_id = str(
        api.create_workspace(token, "Live session", synthetic=synthetic)["workspace_id"]
    )
    stored = api.write(
        "POST",
        f"/v1/workspaces/{workspace_id}/credentials",
        token,
        {"api_key": key, "consent_to_encrypted_storage": True},
    )
    assert stored.status_code == 201, stored.text
    return workspace_id


@pytest.fixture(scope="module")
def session(
    infra: Infra, wonder_api: ApiClient, tmp_path_factory: pytest.TempPathFactory
) -> Session:
    _, token = fresh_actor(wonder_api, infra)
    key = secrets.token_urlsafe(32)
    personal = _workspace(wonder_api, token, synthetic=False, key=key)
    synthetic = _workspace(wonder_api, token, synthetic=True, key=key)
    profile_sentinel = f"PRIVATE-PROFILE-{secrets.token_hex(6)}"
    wonder_api.write(
        "PUT",
        f"/v1/workspaces/{personal}/profile",
        token,
        {"expected_version": 0, "profile": profile_with(current_role=profile_sentinel)},
    )
    message = f"I train new starters at a warehouse. PRIVATE-MESSAGE-{secrets.token_hex(6)}"
    turn = wonder_api.write(
        "POST",
        f"/v1/workspaces/{personal}/interview/turns",
        token,
        {"expected_profile_version": 1, "message": message},
    )
    assert turn.status_code == 202, turn.text
    check = wonder_api.write(
        "POST", f"/v1/workspaces/{synthetic}/runs", token, {"kind": "connection_check"}
    )
    assert check.status_code == 202, check.text
    output_sentinel = f"OUTPUT-SENTINEL-{uuid.uuid4().hex[:12]}"
    log = Path(tmp_path_factory.mktemp("session")) / "worker.log"
    worker = start_worker(
        infra, log, production_model=WONDER_MODEL_ID, output_sentinel=output_sentinel
    )
    runs = (turn.json()["run"]["run_id"], check.json()["run_id"])
    try:
        wait_for(
            lambda: all(
                infra.query("SELECT status FROM careerwright.runs WHERE run_id = %s", (r,))[0][
                    "status"
                ]
                in TERMINAL
                for r in runs
            ),
            timeout_s=60,
            what="both runs",
        )
        assert worker.stop() == 0
    finally:
        worker.kill_if_running()
    return Session(
        wonder_api,
        token,
        personal,
        synthetic,
        runs[0],
        runs[1],
        message,
        output_sentinel,
        profile_sentinel,
        key,
    )


def _attempt(infra: Infra, run_id: str) -> dict[str, Any]:
    [attempt] = infra.query(
        "SELECT * FROM careerwright.model_attempts WHERE run_id = %s", (run_id,)
    )
    return attempt


@pytest.mark.req("MODEL-11", "MODEL-03")
def test_with_wonder_configured_the_worker_runs_it_and_a_synthetic_workspace_keeps_the_test_model(
    infra: Infra, session: Session
) -> None:
    turn, check = _attempt(infra, session.turn_run), _attempt(infra, session.check_run)

    assert (turn["model_id"], check["model_id"]) == (WONDER_MODEL_ID, TEST_MODEL)
    for run_id in (session.turn_run, session.check_run):
        [run] = infra.query("SELECT * FROM careerwright.runs WHERE run_id = %s", (run_id,))
        assert run["status"] == "complete"
    usage = Usage(turn["input_tokens"], turn["cached_input_tokens"], turn["output_tokens"])
    assert turn["spend_state"] == "reconciled"
    assert turn["cost_nano_usd"] == estimate_cost_nano_usd(
        WONDER_MODEL_ID, usage
    )  # Wonder's prices
    # The database still refuses a personal-data run on the Contributor test model.
    with pytest.raises(psycopg.errors.CheckViolation):
        infra.query(
            "UPDATE careerwright.runs SET model_id = %s, model_mode = 'contributor' "
            "WHERE run_id = %s",
            (TEST_MODEL, session.turn_run),
        )


@dataclass(frozen=True)
class Target:
    http: TestClient
    web_origin: str = WEB_ORIGIN


def _spend(session: Session, workspace_id: str) -> dict[str, Any]:
    body: dict[str, Any] = session.api.get(
        f"/v1/workspaces/{workspace_id}/spend", session.token
    ).json()
    return body


def _estimate(session: Session, workspace_id: str, kind: str) -> Any:
    return session.api.get(
        f"/v1/workspaces/{workspace_id}/spend/estimate", session.token, kind=kind
    )


@pytest.mark.req("MODEL-11", "MODEL-08")
def test_the_session_caps_go_on_each_live_workspace_not_marked_synthetic_and_hold(
    session: Session,
) -> None:
    before = _spend(session, session.personal)
    untouched = _spend(session, session.synthetic)

    [capped] = set_session_caps(Api(Target(session.api.http), session.token))

    assert capped.workspace_id == session.personal
    after = _spend(session, session.personal)
    assert (after["run_limit_nano_usd"], after["period_limit_nano_usd"]) == (
        SESSION_RUN_LIMIT_NANO_USD,
        before["period_committed_nano_usd"] + SESSION_SPEND_PER_WORKSPACE_NANO_USD,
    )
    assert after["version"] == before["version"] + 1
    assert _spend(session, session.synthetic) == untouched
    # The estimate before a turn, on Wonder: three attempts at $0.176, under the run cap.
    estimate = _estimate(session, session.personal, "interview_turn").json()
    assert estimate == {
        "kind": "interview_turn",
        "model_id": WONDER_MODEL_ID,
        "model_mode": "standard",
        "per_run_nano_usd": 3 * interview.worst_case_nano_usd(WONDER_MODEL_ID),
        "hard_maximum_nano_usd": SESSION_RUN_LIMIT_NANO_USD,
        "refused_scope": None,
    }
    assert _estimate(session, session.synthetic, "interview_turn").json()["model_id"] == TEST_MODEL
    # A second session adds its own $5 to what the workspace's month has committed by then.
    [again] = set_session_caps(Api(Target(session.api.http), session.token))
    assert (
        again.period_limit_nano_usd
        == after["period_committed_nano_usd"] + SESSION_SPEND_PER_WORKSPACE_NANO_USD
    )
    # Past the workspace's spend, the product's own checks refuse the next turn before it runs.
    spent = _spend(session, session.personal)
    nearly = spent["period_committed_nano_usd"] + interview.worst_case_nano_usd(WONDER_MODEL_ID) - 1
    limited = session.api.write(
        "PUT",
        f"/v1/workspaces/{session.personal}/spend/limits",
        session.token,
        {
            "expected_version": spent["version"],
            "run_limit_nano_usd": SESSION_RUN_LIMIT_NANO_USD,
            "period_limit_nano_usd": nearly,
        },
    )
    assert limited.status_code == 200, limited.text
    assert (
        _estimate(session, session.personal, "interview_turn").json()["refused_scope"] == "period"
    )
    refused = session.api.write(
        "POST",
        f"/v1/workspaces/{session.personal}/interview/turns",
        session.token,
        {"expected_profile_version": 1, "message": "Synthetic: one more question."},
    )
    assert refused.json()["error"]["code"] == "BUDGET_EXCEEDED"


@pytest.mark.req("MODEL-08")
def test_the_estimate_is_free_on_a_demo_fixture_and_refused_for_a_kind_no_one_starts(
    api: ApiClient, ada: str
) -> None:
    base = f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}/spend/estimate"

    demo = api.get(base, ada, kind="interview_turn").json()
    never = api.get(base, ada, kind="source_search")
    none = api.get(base, ada, kind="acquisition")

    assert (demo["model_mode"], demo["per_run_nano_usd"], demo["hard_maximum_nano_usd"]) == (
        "fixture",
        0,
        0,
    )
    assert (never.status_code, never.json()["error"]["code"]) == (422, "MODE_NOT_SUPPORTED")
    assert none.status_code == 422
    assert none.json()["error"]["details"]["reason"] == "no_estimate_for_kind"


@pytest.fixture
def ledger_reader(infra: Infra) -> Iterator[str]:
    """A database role that can read exactly the columns the copy names, across workspaces:
    any other column it touched would fail the copy."""
    role = f"ledger_reader_{secrets.token_hex(4)}"
    password = secrets.token_hex(16)
    by_table: dict[str, list[str]] = {"a": [], "r": []}
    for column in COPIED_COLUMNS:
        table, name = column.split(".")
        by_table[table].append(name)
    by_table["r"].append("run_id")  # the join
    infra.query(f"CREATE ROLE {role} LOGIN PASSWORD '{password}' BYPASSRLS")
    infra.query(f"GRANT CONNECT ON DATABASE careerwright_app TO {role}")
    infra.query(f"GRANT USAGE ON SCHEMA careerwright TO {role}")
    infra.query(
        f"GRANT SELECT ({', '.join(by_table['a'])}) ON careerwright.model_attempts TO {role}"
    )
    infra.query(f"GRANT SELECT ({', '.join(by_table['r'])}) ON careerwright.runs TO {role}")
    try:
        yield f"postgresql://{role}:{password}@{HOST}:{TEST_PORTS.postgres}/careerwright_app"
    finally:
        infra.query(f"DROP OWNED BY {role}")
        infra.query(f"DROP ROLE {role}")


@pytest.mark.req("MODEL-11")
def test_the_ledger_copy_reads_counts_cost_and_state_only_and_writes_no_text(
    infra: Infra, session: Session, ledger_reader: str, tmp_path: Path
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    with (
        psycopg.connect(ledger_reader) as conn,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        conn.execute("SELECT provider_response_id FROM careerwright.model_attempts")

    first = copy_session_calls(ledger_reader, ledger)
    again = copy_session_calls(ledger_reader, ledger)

    turn = _attempt(infra, session.turn_run)
    [row] = [r for r in first.copied if session.turn_run in r.notes]
    assert row.budget_scope == f"live-app-{turn['started_at']:%Y-%m-%d}"
    assert "interview turn" in row.purpose
    assert (row.model_id, row.is_production_model) == (WONDER_MODEL_ID, True)
    assert (row.input_tokens, row.output_tokens, row.estimated_cost_nano_usd) == (
        turn["input_tokens"],
        turn["output_tokens"],
        turn["cost_nano_usd"],
    )
    assert row.provider_response_id is None  # not read
    # Copied once: a second copy finds every settled attempt already in the ledger.
    assert (again.copied, again.already) == ([], first.already + len(first.copied))
    written = (tmp_path / "live-usage.jsonl").read_text() + (tmp_path / "live-usage.md").read_text()
    for text in (
        session.message,
        session.output_sentinel,
        session.profile_sentinel,
        session.api_key[:12],
    ):
        assert text not in written
