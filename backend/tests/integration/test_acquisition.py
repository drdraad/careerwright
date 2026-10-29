"""Acquisition runs end to end against real PostgreSQL 16 and DBOS (Task 7A; ADR 0009): the
API submits, a real worker process runs the acquisition workflow, and the restricted
acquisition worker fetches from a controlled source server. Every page is synthetic."""

import dataclasses
import json
import secrets
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from nessa.api.app import create_app
from nessa.api.deps import ApiDependencies
from tests.domain.test_pages import POSTING, page
from tests.integration.durable import make_scenario
from tests.support.acquisition_service import LOOPBACK, acquisition_service
from tests.support.client import ApiClient, profile_with
from tests.support.infra import API_BASE, Infra
from tests.support.source_server import Scripted, SourceServer, html, source_server
from tests.support.workers import Worker, start_worker, wait_for
from tools.leak_scan import Needle, scan

pytestmark = pytest.mark.integration

TERMINAL = {"complete", "failed", "provider_unavailable", "cancelled"}
NAMES = {
    "www.gov.uk": [LOOPBACK],
    "careers.northwind.example": [LOOPBACK],
    "jobs.board.example": [LOOPBACK],
    "slow.board.example": [LOOPBACK],
}


def _slow_page() -> bytes:
    return page({**POSTING, "title": "Slow Analyst"}).encode()


@pytest.fixture(scope="module")
def sources() -> Iterator[SourceServer]:
    routes = {
        "/jobs/7781": Scripted(body=page(POSTING).encode()),
        "/ad/1": Scripted(body=page(POSTING).encode()),
        "/plain": Scripted(body=html("<h1>Gardener</h1><p>Apply by email.</p>")),
        "/gone": Scripted(404, body=b"gone"),
        "/closed": Scripted(410, body=b"closed"),
        "/down": Scripted(503, body=b"down"),
        "/slow/1": Scripted(body=_slow_page(), delay_s=2.0),
        "/slow/2": Scripted(body=_slow_page(), delay_s=2.0),
        "/slow/3": Scripted(body=_slow_page(), delay_s=2.0),
    }
    with source_server(routes) as server:
        yield server


@pytest.fixture(scope="module")
def service_url(sources: SourceServer) -> Iterator[str]:
    with acquisition_service(sources, names=NAMES) as url:
        yield url


@pytest.fixture
def worker(infra: Infra, service_url: str, tmp_path: Path) -> Iterator[Worker]:
    """One worker per test, so a test that starts its own never races another for a run."""
    started = start_worker(infra, tmp_path / "worker.log", acquisition_url=service_url)
    yield started
    if started.process.poll() is None:
        started.stop()


def url(sources: SourceServer, host: str, path: str) -> str:
    return f"http://{host}:{sources.port}{path}"


@pytest.fixture
def workspace(api: ApiClient, ada: str) -> str:
    return str(api.create_workspace(ada, "Acquisition")["workspace_id"])


def submit(api: ApiClient, token: str, workspace: str, body: dict[str, Any]) -> Any:
    response = api.write("POST", f"/v1/workspaces/{workspace}/research/acquisitions", token, body)
    assert response.status_code in (200, 202), response.text
    return response


def run_of(infra: Infra, run_id: str) -> dict[str, Any]:
    return infra.query("SELECT * FROM nessa.runs WHERE run_id = %s", (run_id,))[0]


def wait_terminal(infra: Infra, run_id: str, timeout_s: float = 60.0) -> dict[str, Any]:
    wait_for(lambda: run_of(infra, run_id)["status"] in TERMINAL, timeout_s=timeout_s, what="run")
    return run_of(infra, run_id)


def acquisition(api: ApiClient, token: str, workspace: str, run_id: str) -> Any:
    response = api.get(f"/v1/workspaces/{workspace}/research/acquisitions/{run_id}", token)
    assert response.status_code == 200, response.text
    return response.json()


def jobs(api: ApiClient, token: str, workspace: str, **params: Any) -> Any:
    response = api.get(f"/v1/workspaces/{workspace}/jobs", token, **params)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.req("ACQ-03", "ACQ-06", "API-06", "JOB-02", "FRESH-01", "DUR-03")
def test_an_acquisition_records_every_attempt_and_a_job_with_its_claims(
    infra: Infra, api: ApiClient, ada: str, workspace: str, sources: SourceServer, worker: Worker
) -> None:
    urls = [
        # A keep-privately host by its manifest entry: the controlled server stands in for
        # www.gov.uk through the scripted DNS.
        url(sources, "www.gov.uk", "/jobs/7781"),
        url(sources, "jobs.board.example", "/ad/1"),
        url(sources, "careers.northwind.example", "/plain"),
        url(sources, "careers.northwind.example", "/gone"),
        "http://10.0.0.1/admin",
        "https://www.linkedin.com/jobs/view/1",
    ]
    submitted = submit(api, ada, workspace, {"urls": urls}).json()
    run_id = submitted["acquisition"]["run"]["run_id"]
    assert submitted["acquisition"]["run"]["model_id"] is None  # no model is involved

    run = wait_terminal(infra, run_id)
    shown = acquisition(api, ada, workspace, run_id)

    assert (run["status"], run["failure_class"]) == ("complete", None)
    outcome = [(t["status"], t["attempts"][-1]["reason"]) for t in shown["targets"]]
    assert outcome == [
        ("succeeded", None),
        ("succeeded", None),
        ("succeeded", None),  # retrieved, with no structured posting on it
        ("failed", "http_404"),
        ("blocked", "address_not_allowed"),
        ("blocked", "source_denied"),
    ]
    assert shown["summary"] == {"succeeded": 3, "blocked": 2, "failed": 1}
    refused = shown["targets"][4]
    assert (refused["url"], refused["refusal"], refused["refused_host"]) == (
        None,
        "address_not_allowed",
        "10.0.0.1",
    )
    assert refused["attempts"][-1]["requested_url"] is None
    listed, board, plain = (t["attempts"][-1] for t in shown["targets"][:3])
    assert (listed["rights_class"], listed["retention"]) == ("govuk", "body")
    # The board page's JSON-LD names its hiring organisation; that never raises retention.
    assert (board["rights_class"], board["retention"]) == ("other", "excerpts")
    assert board["rights_status"] == "pending human rights review"
    kept = infra.query(
        "SELECT attempt_id::text AS id FROM nessa.source_documents WHERE workspace_id = %s",
        (workspace,),
    )
    assert [k["id"] for k in kept] == [listed["attempt_id"]]  # only the permitted body
    assert plain["status"] == "succeeded"
    # The two copies of one advert are one job, with both copies kept.
    listing = jobs(api, ada, workspace)
    assert listing["total_jobs"] == 1
    [job] = listing["items"]
    assert len(job["copies"]) == 2
    assert job["salary"]["basis"] == "advertised"
    assert job["salary_confirmed"] is True
    assert job["freshness"]["state"] == "current"
    assert listing["city_counts"] == {"Leeds": 1, "Manchester": 1}  # counted once in total
    assert listing["coverage"] == {"succeeded": 3, "failed": 1, "blocked": 2}
    assert listing["empty_reason"] is None
    detail = api.get(f"/v1/workspaces/{workspace}/jobs/{job['job_id']}", ada).json()
    salary = next(c for c in detail["claims"] if c["field"] == "salary")
    assert salary["span"]["start"] is not None
    assert "32000" in salary["span"]["excerpt"]
    # Robots.txt came first; nothing refused was requested at all.
    assert "/robots.txt" in sources.paths()
    assert "/admin" not in sources.paths()
    journal = infra.query(
        "SELECT function_name, output FROM dbos.operation_outputs WHERE workflow_uuid = %s",
        (f"nessa-run-{run_id}",),
        database="nessa_dbos",
    )
    assert "northwind" not in json.dumps(journal, default=str)  # identifiers only


@pytest.mark.req("STATE-02", "ACQ-06")
def test_every_source_failing_is_a_failed_run_never_no_vacancies(
    infra: Infra, api: ApiClient, ada: str, workspace: str, sources: SourceServer, worker: Worker
) -> None:
    urls = [url(sources, "careers.northwind.example", p) for p in ("/gone", "/down")]
    run_id = submit(api, ada, workspace, {"urls": urls}).json()["acquisition"]["run"]["run_id"]

    run = wait_terminal(infra, run_id)
    shown = acquisition(api, ada, workspace, run_id)
    listing = jobs(api, ada, workspace)

    assert (run["status"], run["failure_class"]) == ("failed", "retrieval_failed")
    assert listing["total_jobs"] == 0
    assert listing["empty_reason"] == "no_source_retrieved"  # not "no vacancies"
    down = shown["targets"][1]["attempts"]
    assert [a["reason"] for a in down] == ["http_503"] * 3  # the DBOS step's three tries
    assert [a["transient"] for a in down] == [True] * 3
    assert down[1]["retry_of"] == down[0]["attempt_id"]
    assert down[2]["retry_of"] == down[1]["attempt_id"]


@pytest.mark.req("ACQ-06", "ACQ-01")
def test_a_run_whose_every_source_is_refused_is_source_blocked_and_records_no_unsafe_url(
    infra: Infra, api: ApiClient, ada: str, workspace: str, worker: Worker
) -> None:
    unsafe = ["javascript:alert(1)", "file:///etc/passwd", "data:text/html,x"]
    body = {
        "urls": [
            "http://169.254.169.254/latest/meta-data/",
            "https://uk.indeed.com/jobs",
            *unsafe,
        ]
    }
    run_id = submit(api, ada, workspace, body).json()["acquisition"]["run"]["run_id"]

    run = wait_terminal(infra, run_id)
    shown = acquisition(api, ada, workspace, run_id)

    assert (run["status"], run["failure_class"]) == ("failed", "source_blocked")
    assert [(t["url"], t["refusal"]) for t in shown["targets"]] == [
        (None, "address_not_allowed"),
        ("https://uk.indeed.com/jobs", None),
        (None, "scheme_not_allowed"),
        (None, "scheme_not_allowed"),
        (None, "scheme_not_allowed"),
    ]
    assert [t["attempts"][-1]["reason"] for t in shown["targets"]] == [
        "address_not_allowed",
        "source_denied",
        "scheme_not_allowed",
        "scheme_not_allowed",
        "scheme_not_allowed",
    ]
    stored = json.dumps(
        infra.query(
            "SELECT t.url, t.refused_host, a.requested_url, a.final_url, a.redirects "
            "FROM nessa.acquisition_targets t JOIN nessa.source_attempts a USING (run_id, "
            "position) WHERE t.run_id = %s",
            (run_id,),
        )
    )
    assert not any(f"{u.split(':')[0]}:" in stored for u in unsafe)  # in no field at all


@pytest.mark.req("DUR-05", "JOB-08")
def test_a_cancelled_acquisition_fetches_nothing_more_and_keeps_what_it_found(
    infra: Infra, api: ApiClient, ada: str, workspace: str, sources: SourceServer, worker: Worker
) -> None:
    urls = [url(sources, "slow.board.example", f"/slow/{n}") for n in (1, 2, 3)]
    before = len(sources.seen)
    run_id = submit(api, ada, workspace, {"urls": urls}).json()["acquisition"]["run"]["run_id"]
    wait_for(
        lambda: bool(
            infra.query(
                "SELECT 1 FROM nessa.source_attempts WHERE run_id = %s AND position = 0", (run_id,)
            )
        ),
        timeout_s=30,
        what="the first attempt",
    )

    cancelled = api.write("POST", f"/v1/workspaces/{workspace}/runs/{run_id}/cancel", ada)
    run = wait_terminal(infra, run_id)
    time.sleep(3.0)  # long enough for the step already under way to finish
    shown = acquisition(api, ada, workspace, run_id)
    again = api.write("POST", f"/v1/workspaces/{workspace}/runs/{run_id}/cancel", ada)

    assert cancelled.status_code == 202, cancelled.text
    assert cancelled.json()["cancel_requested_at"] is not None
    assert (run["status"], run["failure_class"]) == ("cancelled", None)
    statuses = [t["status"] for t in shown["targets"]]
    assert statuses[0] in ("succeeded", "failed")  # the step under way finished
    assert statuses[2] == "cancelled"
    assert "/slow/3" not in [s.path for s in sources.seen[before:]]  # never fetched
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "RUN_FINISHED"
    kinds = [
        e["kind"]
        for e in api.get(f"/v1/workspaces/{workspace}/events", ada).json()["items"]
        if e["subject_id"] == run_id
    ]
    assert "run.cancel_requested" in kinds


@pytest.mark.req("JOB-08", "DUR-02")
def test_a_worker_killed_after_a_target_resumes_at_the_next_one(
    infra: Infra,
    api: ApiClient,
    ada: str,
    workspace: str,
    sources: SourceServer,
    service_url: str,
    tmp_path: Path,
) -> None:
    urls = [
        url(sources, "careers.northwind.example", "/jobs/7781"),
        url(sources, "careers.northwind.example", "/plain"),
    ]
    run_id = submit(api, ada, workspace, {"urls": urls}).json()["acquisition"]["run"]["run_id"]
    crashing = start_worker(
        infra, tmp_path / "crash.log", acquisition_url=service_url, crash_at="after_acquired_target"
    )
    assert crashing.wait_exit(60) != 0  # killed after the first target's results committed

    resumed = start_worker(infra, tmp_path / "resumed.log", acquisition_url=service_url)
    try:
        run = wait_terminal(infra, run_id)
    finally:
        resumed.stop()
    attempts = infra.query(
        "SELECT position, status FROM nessa.source_attempts WHERE run_id = %s ORDER BY started_at",
        (run_id,),
    )

    assert run["status"] == "complete"
    assert [a["position"] for a in attempts].count(0) == 1  # the first target is not repeated
    assert [a["status"] for a in attempts] == ["succeeded", "succeeded"]


@pytest.mark.req("FRESH-03", "JOB-02")
def test_a_failed_refresh_moves_the_last_attempt_and_never_the_last_success(
    infra: Infra,
    api: ApiClient,
    ada: str,
    workspace: str,
    sources: SourceServer,
    service_url: str,
    tmp_path: Path,
) -> None:
    worker = start_worker(infra, tmp_path / "refresh.log", acquisition_url=service_url)
    try:
        page_url = url(sources, "careers.northwind.example", "/refresh/1")
        sources.routes["/refresh/1"] = Scripted(body=page(POSTING).encode())
        first = submit(api, ada, workspace, {"urls": [page_url]}).json()["acquisition"]["run"]
        wait_terminal(infra, first["run_id"])
        [verified] = infra.query(
            "SELECT job_id, last_success_at, last_attempt_at FROM nessa.jobs "
            "WHERE workspace_id = %s",
            (workspace,),
        )

        sources.routes["/refresh/1"] = Scripted(410, body=b"closed")
        second = submit(api, ada, workspace, {"urls": [page_url]}).json()["acquisition"]["run"]
        wait_terminal(infra, second["run_id"])
    finally:
        worker.stop()
    [after] = infra.query(
        "SELECT job_id, last_success_at, last_attempt_at, closed_at FROM nessa.jobs "
        "WHERE workspace_id = %s",
        (workspace,),
    )
    [job] = jobs(api, ada, workspace)["items"]

    assert after["job_id"] == verified["job_id"]
    assert after["last_success_at"] == verified["last_success_at"]
    assert after["last_attempt_at"] > verified["last_attempt_at"]
    assert after["closed_at"] is not None  # the source said the advert is gone
    assert job["freshness"]["state"] == "closed"


@pytest.mark.req("FRESH-04")
def test_a_url_in_flight_is_joined_and_one_that_failed_backs_off(
    infra: Infra, api: ApiClient, ada: str, workspace: str, sources: SourceServer, worker: Worker
) -> None:
    slow = url(sources, "slow.board.example", "/slow/1")
    first = submit(api, ada, workspace, {"urls": [slow]}).json()["acquisition"]["run"]
    joined = submit(api, ada, workspace, {"urls": [slow]})
    wait_terminal(infra, first["run_id"])

    gone = url(sources, "careers.northwind.example", "/gone")
    failed = submit(api, ada, workspace, {"urls": [gone]}).json()["acquisition"]["run"]
    wait_terminal(infra, failed["run_id"])
    backing_off = submit(api, ada, workspace, {"urls": [gone]})

    assert joined.status_code == 200
    assert joined.json()["acquisition"] is None  # nothing new was started
    assert joined.json()["skipped"] == [
        {"url": slow, "reason": "in_flight", "run_id": first["run_id"], "retry_at": None}
    ]
    [skipped] = backing_off.json()["skipped"]
    assert (skipped["reason"], skipped["run_id"]) == ("backing_off", None)
    assert skipped["retry_at"] is not None


@pytest.mark.req("ACQ-10", "JOB-06")
def test_pasted_text_is_its_own_route_and_an_example_never_a_live_vacancy(
    infra: Infra, api: ApiClient, ada: str, workspace: str
) -> None:
    body = {
        "target": "Data quality analyst",
        "title": "Data Quality Analyst",
        "text": "Data Quality Analyst at Northwind. You will profile datasets.",
        "employer": "Northwind",
        "city": "Manchester",
    }
    pasted = api.write("POST", f"/v1/workspaces/{workspace}/research/pasted", ada, body)
    for _ in range(2):
        api.write("POST", f"/v1/workspaces/{workspace}/research/pasted", ada, body)
    fourth = api.write("POST", f"/v1/workspaces/{workspace}/research/pasted", ada, body)

    assert pasted.status_code == 201, pasted.text
    job = pasted.json()["job"]
    assert job["exemplar"] is True
    assert job["freshness"]["state"] == "never_verified"  # never shown as currently available
    assert [c["route"] for c in job["copies"]] == ["pasted_text"]
    claims = pasted.json()["claims"]
    assert {c["validation"] for c in claims} == {"user_supplied"}
    title = next(c for c in claims if c["field"] == "title")
    assert title["span"]["excerpt"] == "Data Quality Analyst"
    attempts = infra.query(
        "SELECT run_id, route, created_by IS NOT NULL AS by_person FROM nessa.source_attempts "
        "WHERE workspace_id = %s",
        (workspace,),
    )
    assert {(a["run_id"], a["route"], a["by_person"]) for a in attempts} == {
        (None, "pasted_text", True)
    }
    assert fourth.status_code == 422
    assert fourth.json()["error"]["details"]["reason"] == "exemplars_per_target"


@pytest.mark.req("ACQ-10", "ACQ-01")
def test_a_pasted_text_s_source_is_kept_only_as_a_checked_url(
    api: ApiClient, ada: str, workspace: str
) -> None:
    base = {"target": "Gardener", "title": "Gardener", "text": "Gardener wanted in Leeds."}
    path = f"/v1/workspaces/{workspace}/research/pasted"
    refused = [
        api.write("POST", path, ada, {**base, "source_url": unsafe})
        for unsafe in ("javascript:alert(1)", "http://localhost/job", "http://10.0.0.1/")
    ]
    kept = api.write("POST", path, ada, {**base, "source_url": "HTTPS://Jobs.Example.org/a#x"})

    for response in refused:
        assert response.status_code == 422, response.text
        assert response.json()["error"]["details"]["field"] == "source_url"
    assert [r.json()["error"]["details"]["reason"] for r in refused] == [
        "scheme_not_allowed",
        "host_not_allowed",
        "address_not_allowed",
    ]
    assert kept.status_code == 201, kept.text
    [copy] = kept.json()["job"]["copies"]
    assert copy["source_url"] == "https://jobs.example.org/a"  # the checked form


@pytest.mark.req("JOB-07")
def test_a_job_is_marked_and_unmarked_as_a_favourite(
    api: ApiClient, ada: str, workspace: str
) -> None:
    body = {"target": "Gardener", "title": "Gardener", "text": "Gardener wanted in Leeds."}
    job_id = api.write("POST", f"/v1/workspaces/{workspace}/research/pasted", ada, body).json()[
        "job"
    ]["job_id"]

    marked = api.write("PUT", f"/v1/workspaces/{workspace}/jobs/{job_id}/favourite", ada)
    only = jobs(api, ada, workspace, favourites=True)
    cleared = api.write("DELETE", f"/v1/workspaces/{workspace}/jobs/{job_id}/favourite", ada)

    assert marked.json()["favourite"] is True
    assert [j["job_id"] for j in only["items"]] == [job_id]
    assert cleared.json()["favourite"] is False
    assert jobs(api, ada, workspace, favourites=True)["items"] == []


@pytest.mark.req("FRESH-01", "SEC-01")
def test_another_person_sees_none_of_the_research(
    api: ApiClient, ada: str, ben: str, workspace: str
) -> None:
    body = {"target": "Gardener", "title": "Gardener", "text": "Gardener wanted in Leeds."}
    job_id = api.write("POST", f"/v1/workspaces/{workspace}/research/pasted", ada, body).json()[
        "job"
    ]["job_id"]

    assert api.get(f"/v1/workspaces/{workspace}/jobs", ben).status_code == 404
    assert api.get(f"/v1/workspaces/{workspace}/jobs/{job_id}", ben).status_code == 404
    assert (
        api.write("PUT", f"/v1/workspaces/{workspace}/jobs/{job_id}/favourite", ben).status_code
        == 404
    )


@pytest.mark.req("ACQ-06")
def test_a_url_carrying_a_credential_is_refused_before_anything_is_recorded(
    api: ApiClient, ada: str, workspace: str
) -> None:
    for unsafe in ("https://user:secret@example.org/job", "https://example.org/x?app_key=abc"):
        response = api.write(
            "POST", f"/v1/workspaces/{workspace}/research/acquisitions", ada, {"urls": [unsafe]}
        )
        assert response.status_code == 422, response.text
        assert response.json()["error"]["details"]["reason"] == "credentials_in_url"


@pytest.mark.req("BND1-11")
def test_a_demo_workspace_never_acquires(api: ApiClient, ada: str) -> None:
    demo = api.write(
        "POST", "/v1/workspaces", ada, {"name": "Demo", "data_mode": "demo", "synthetic": True}
    ).json()["workspace_id"]

    response = api.write(
        "POST",
        f"/v1/workspaces/{demo}/research/acquisitions",
        ada,
        {"urls": ["https://example.org/job"]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MODE_NOT_SUPPORTED"


ADZUNA_FIXTURE = Path(__file__).resolve().parents[3] / "fixtures/acquisition/adzuna-search-gb.json"


@pytest.fixture
def adzuna_api(api_deps: ApiDependencies) -> Iterator[ApiClient]:
    """The API as the stack runs it once setup placed Adzuna credentials (R4)."""
    deps = dataclasses.replace(
        api_deps, settings=api_deps.settings.model_copy(update={"adzuna_configured": True})
    )
    with TestClient(
        create_app(deps),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57002),
    ) as client:
        yield ApiClient(client)


@pytest.mark.req("JOB-05", "SEC-05", "MODEL-06")
def test_an_adzuna_search_keeps_its_pay_basis_and_snippets_and_never_its_credentials(
    infra: Infra, adzuna_api: ApiClient, ada: str, tmp_path: Path
) -> None:
    app_id, app_key = f"id{secrets.token_hex(8)}", f"key{secrets.token_hex(16)}"
    routes = {
        "/v1/api/jobs/gb/search/1": Scripted(
            headers=(("Content-Type", "application/json"),), body=ADZUNA_FIXTURE.read_bytes()
        )
    }
    with (
        source_server(routes) as adzuna_server,
        acquisition_service(
            adzuna_server,
            names={"api.adzuna.test.example": [LOOPBACK]},
            credentials=(SecretStr(app_id), SecretStr(app_key)),
            adzuna_host="api.adzuna.test.example",
        ) as service,
    ):
        worker = start_worker(infra, tmp_path / "adzuna.log", acquisition_url=service)
        created = adzuna_api.write(
            "POST",
            "/v1/workspaces",
            ada,
            {"name": "Live vacancy", "data_mode": "live_vacancy", "synthetic": True},
        )
        assert created.status_code == 201, created.text
        workspace = created.json()["workspace_id"]
        body = {"adzuna": {"what": "data quality analyst", "where": "Manchester"}}
        submitted = adzuna_api.write(
            "POST", f"/v1/workspaces/{workspace}/research/acquisitions", ada, body
        )
        run_id = submitted.json()["acquisition"]["run"]["run_id"]
        try:
            run = wait_terminal(infra, run_id)
        finally:
            worker.stop()
        shown = acquisition(adzuna_api, ada, workspace, run_id)
        listing = jobs(adzuna_api, ada, workspace)
        sent = [s.path for s in adzuna_server.seen]

    assert run["status"] == "complete"
    assert run["data_mode"] == "live_vacancy"
    [attempt] = shown["targets"][0]["attempts"]
    assert (attempt["route"], attempt["rights_class"], attempt["retention"]) == (
        "adzuna",
        "job-board",
        "excerpts",
    )
    assert attempt["http_requests"] == 1
    assert attempt["cost_nano_usd"] == 0  # free tier
    assert "app_key" not in (attempt["requested_url"] or "")
    assert any(app_key in path for path in sent)  # the one request did carry the key
    assert listing["total_jobs"] == 6
    bases = {j["salary"]["basis"] if j["salary"] else None for j in listing["items"]}
    assert bases == {"advertised", "predicted", "unknown", None}
    assert {j["description_kind"] for j in listing["items"]} == {"snippet"}
    assert not infra.query(
        "SELECT 1 FROM nessa.source_documents WHERE workspace_id = %s", (workspace,)
    )  # reference only: the body is never kept
    cells = [*infra.database_cells("nessa_app"), *infra.database_cells("nessa_dbos")]
    logs = [("worker", (tmp_path / "adzuna.log").read_text(encoding="utf-8"))]
    responses = [("api", json.dumps(shown)), ("api", json.dumps(listing))]
    needles = [Needle("Adzuna app id", app_id), Needle("Adzuna key", app_key, fragment_length=12)]
    assert scan([*cells, *logs, *responses], needles) == []


@pytest.mark.req("BND1-11")
def test_live_vacancy_workspaces_are_refused_without_adzuna_credentials(
    api: ApiClient, ada: str
) -> None:
    response = api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Live vacancy", "data_mode": "live_vacancy", "synthetic": True},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MODE_NOT_SUPPORTED"


@pytest.mark.req("SEC-05", "API-05", "ACQ-06", "MODEL-08")
def test_a_source_search_proposes_candidates_for_a_confirmed_target_and_city(
    infra: Infra, api: ApiClient, ada: str, tmp_path: Path
) -> None:
    scenario = make_scenario(infra, api, ada, tmp_path)
    saved = api.write(
        "PUT",
        f"/v1/workspaces/{scenario.workspace_id}/profile",
        ada,
        {
            "expected_version": 1,
            "profile": profile_with(
                current_role=scenario.profile_sentinel,
                target_titles=["Data quality analyst"],
                cities=["Manchester"],
            ),
        },
    )
    assert saved.status_code == 201, saved.text  # a new profile version
    base = f"/v1/workspaces/{scenario.workspace_id}/research/searches"
    elsewhere = api.write(
        "POST",
        base,
        ada,
        {"expected_profile_version": 2, "target": "Data quality analyst", "city": "Leeds"},
    )
    stale = api.write(
        "POST",
        base,
        ada,
        {"expected_profile_version": 1, "target": "Data quality analyst", "city": "Manchester"},
    )
    submitted = api.write(
        "POST",
        base,
        ada,
        {"expected_profile_version": 2, "target": "data quality analyst", "city": "Manchester"},
    )
    search_id = submitted.json()["search_id"]
    worker = scenario.worker("search")
    try:
        run = scenario.wait_terminal(search_id)
    finally:
        worker.stop()
    shown = api.get(f"{base}/{search_id}", ada).json()

    assert elsewhere.status_code == 409
    assert elsewhere.json()["error"]["code"] == "CONFIRMATION_REQUIRED"
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert submitted.status_code == 202, submitted.text
    assert (run["status"], run["profile_version"]) == ("complete", 2)
    proposal = shown["proposal"]
    assert (proposal["target"], proposal["city"]) == ("Data quality analyst", "Manchester")
    assert [(c["url"], c["grounded"]) for c in proposal["candidates"]] == [
        ("https://careers.northwind.example/jobs/1", True),
        ("https://jobs.board.example/ad/9", False),
    ]
    assert proposal["excluded"] == [
        {"url": "https://www.linkedin.com/jobs/view/1", "reason": "source_not_permitted"}
    ]
    [attempt] = scenario.attempts(search_id)
    assert attempt["reserved_nano_usd"] == 8_000_000  # its one request at its bounds
    # The model saw a role and a city only: the profile's private text reached no journal or
    # log, and the model's output is sealed.
    assert scenario.leaks() == []


def test_a_cancelled_unknown_run_is_not_found(api: ApiClient, ada: str, workspace: str) -> None:
    response = api.write("POST", f"/v1/workspaces/{workspace}/runs/{uuid.uuid4()}/cancel", ada)

    assert response.status_code == 404
