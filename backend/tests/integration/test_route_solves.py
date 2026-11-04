"""The route search as a run, end to end against real PostgreSQL 16 and DBOS (Task 13b; ADR
0016's Task 13b amendment): the API takes the snapshot and records the solve, a real worker
process runs it, and the result is stored sealed with its facts. Workers are real processes;
"kill" is SIGKILL. The person and their figures are synthetic; the options are the committed
option pack's.

With the pack's options as they stand, every offering lacks a fact the search needs, so a
complete run is `unresolved`, never a route and never "no route" (Task 13a's measurement).
"""

import json
import signal
import time
import uuid
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import psycopg
import pytest

from careerwright.api.deps import ApiDependencies
from careerwright.planning.months import Month
from careerwright.seed import INVITED_ACTORS
from tests.integration.durable import fresh_actor
from tests.integration.test_worker_boundaries import cut_worker_database_for
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra
from tests.support.workers import Worker, start_worker, wait_for

pytestmark = pytest.mark.integration

ADA_ID, BEN_ID = (str(actor.actor_id) for actor in INVITED_ACTORS)
DATA = "Data quality analyst"
TERMINAL = {"complete", "failed", "provider_unavailable", "cancelled"}
SOLVE_STEPS = {"careerwright.bounded_route_solve", "careerwright.publish_outcome"}
CHECK_DELAY_S = 2.0  # each candidate, in the slow worker: the pack target checks about five
SHORT_CHECK_S = 0.5  # each candidate, where a search need only last a few seconds
STALLED_CHECK_S = 10.0  # the first candidate outlasts everything the test does meanwhile
OUTAGE_S = 15.0  # longer than the solve step's three tries (1 s, then 2 s, apart)
MAX_ATTEMPTS = 3  # executions of one solve (ADR 0016 decision 15)


def no_reason_anywhere(served: Any) -> bool:
    """No finding's `reason` is served: the web words a finding from its facts (R11)."""
    if isinstance(served, dict):
        return "reason" not in served and all(no_reason_anywhere(v) for v in served.values())
    if isinstance(served, list):
        return all(no_reason_anywhere(v) for v in served)
    return True


def gbp(minor: int) -> dict[str, Any]:
    return {"minor_units": minor, "currency": "GBP"}


def stated(**changes: Any) -> dict[str, Any]:
    """P01-like figures (synthetic): every input a solve needs, and no answer about options."""
    return {
        "objective_basis": "economic",
        "baseline": {"kind": "current_role", "net_income": gbp(200000)},
        "continuation": {"hours_per_week": 30, "net_income": gbp(200000)},
        "opening_cash": gbp(600000),
        "living_costs": gbp(100000),
        "reserve": gbp(50000),
        "weekly_availability": 40,
        "commitments": [],
        "existing_debts": [],
        "scenario_delay_months": 2,
        "work_rights": "held",
        **changes,
    }


def next_month() -> str:
    return str(Month.of(date.today()).plus(1))


class Person:
    def __init__(self, api: ApiClient, infra: Infra, token: str) -> None:
        self.api, self.infra, self.token = api, infra, token
        self.workspace_id = str(api.create_workspace(token, "Route solves")["workspace_id"])
        profile = profile_with(
            cities=["Manchester"],
            target_titles=[DATA],
            direct_spend_cap=gbp(150000),
            monthly_payment_cap=gbp(150000),
        )
        written = api.write(
            "PUT",
            f"/v1/workspaces/{self.workspace_id}/profile",
            token,
            {"expected_version": 0, "profile": profile},
        )
        assert written.status_code == 201, written.text
        self.inputs_version = 0

    @property
    def base(self) -> str:
        return f"/v1/workspaces/{self.workspace_id}"

    def state(self, inputs: dict[str, Any]) -> None:
        response = self.api.write(
            "PUT",
            f"{self.base}/planning/inputs",
            self.token,
            {"expected_version": self.inputs_version, "inputs": inputs},
        )
        assert response.status_code == 201, response.text
        self.inputs_version = response.json()["version"]

    def ready_for_the_target(self) -> None:
        """Synthetic evidence at the required level for each of the target's required rows:
        ready now for its modelled requirements, so the empty route reaches readiness."""
        found = self.api.get(f"{self.base}/capability/matrices", self.token).json()
        matrix = next(m for m in found["matrices"] if m["target_title"] == DATA)
        required = [r for r in matrix["rows"] if r["required"]]
        assert required
        for version, row in enumerate(required):
            recorded = self.api.write(
                "POST",
                f"{self.base}/capability/evidence",
                self.token,
                {
                    "expected_version": version,
                    "subject": row["subject"],
                    "rubric_version": row["rubric"]["version_id"],
                    "answer": "done_independently",
                    "self_assessed_level": row["required_level"],
                    "example": "Synthetic: checked a data import and fixed what it broke",
                    "last_done": "2026-08",
                    "context": "paid_work",
                    "independence": "independent",
                },
            )
            assert recorded.status_code == 201, recorded.text

    def ask(self, *, key: uuid.UUID | None = None, **changes: Any) -> Any:
        body = {
            "expected_inputs_version": self.inputs_version,
            "target": DATA,
            "planning_start": next_month(),
            "horizon_months": 24,
            **changes,
        }
        return self.api.write("POST", f"{self.base}/planning/solves", self.token, body, key=key)

    def solve(self, run_id: str, token: str | None = None) -> Any:
        return self.api.get(f"{self.base}/planning/solves/{run_id}", token or self.token)

    def cancel(self, run_id: str) -> Any:
        return self.api.write("POST", f"{self.base}/runs/{run_id}/cancel", self.token)

    def run(self, run_id: str) -> dict[str, Any]:
        return self.infra.query("SELECT * FROM careerwright.runs WHERE run_id = %s", (run_id,))[0]

    def attempts(self, run_id: str) -> list[dict[str, Any]]:
        return self.infra.query(
            "SELECT * FROM careerwright.route_solve_attempts WHERE run_id = %s ORDER BY attempt_id",
            (run_id,),
        )

    def stored(self, run_id: str) -> list[dict[str, Any]]:
        return self.infra.query(
            "SELECT * FROM careerwright.route_solve_results WHERE run_id = %s", (run_id,)
        )

    def wait_terminal(self, run_id: str, timeout_s: float = 60.0) -> dict[str, Any]:
        wait_for(lambda: self.run(run_id)["status"] in TERMINAL, timeout_s=timeout_s, what="run")
        return self.run(run_id)

    def journal(self, run_id: str) -> dict[str, list[dict[str, Any]]]:
        workflow = f"careerwright-run-{run_id}"
        query = self.infra.query
        return {
            "inputs": query(
                "SELECT inputs FROM dbos.workflow_input WHERE workflow_uuid = %s",
                (workflow,),
                database="careerwright_dbos",
            ),
            "output": query(
                "SELECT output FROM dbos.workflow_output WHERE workflow_uuid = %s",
                (workflow,),
                database="careerwright_dbos",
            ),
            "steps": query(
                "SELECT function_name, output, error FROM dbos.operation_outputs "
                "WHERE workflow_uuid = %s ORDER BY function_id",
                (workflow,),
                database="careerwright_dbos",
            ),
        }


@pytest.fixture
def person(api: ApiClient, infra: Infra, ada: str) -> Person:
    found = Person(api, infra, ada)
    found.state(stated())
    return found


@pytest.fixture
def workers(infra: Infra, tmp_path: Path) -> Any:
    started: list[Worker] = []

    def start(name: str, **settings: str) -> Worker:
        worker = start_worker(infra, tmp_path / f"{name}.log", **settings)
        started.append(worker)
        return worker

    yield start
    for worker in started:
        worker.kill_if_running()


@pytest.mark.req("OPT1-05", "OPT1-06", "OPT1-07", "OPT1-11", "DUR-05", "API-02")
def test_a_solve_runs_durably_and_stores_its_ranked_result_with_its_facts(
    person: Person, workers: Any
) -> None:
    asked = person.ask()
    assert asked.status_code == 202, asked.text
    queued = asked.json()
    run_id = queued["run"]["run_id"]
    worker = workers("worker")
    run = person.wait_terminal(run_id)
    worker.stop()
    body = person.solve(run_id).json()
    [attempt] = person.attempts(run_id)
    [stored] = person.stored(run_id)
    journal = person.journal(run_id)
    result = body["result"]

    # Asked for: a keyless run pinned to the profile version it read, with its snapshot sealed.
    assert queued["run"]["kind"] == "route_solve"
    assert (queued["run"]["model_id"], queued["run"]["status"]) == (None, "queued")
    assert queued["run"]["profile_version"] == 1
    assert (queued["stage"], queued["result"], queued["code"]) == (None, None, None)
    assert queued["inputs_version"] == 1
    assert queued["limits"] == {
        "max_actions": 24,
        "max_starts_per_action": 2,
        "max_selected_actions": 6,
        "max_months": 24,
        "wall_seconds": 30,
        "max_states": 1000000,
        "max_feasible_archive": 50000,
    }
    assert person.infra.query(
        "SELECT count(*) AS n FROM careerwright.run_inputs WHERE run_id = %s", (run_id,)
    ) == [{"n": 1}]
    # Run: complete, once, by one attempt that searched then ranked.
    assert (run["status"], run["failure_class"]) == ("complete", None)
    assert (attempt["outcome"], attempt["stage"]) == ("succeeded", "ranking")
    assert body["attempts"] == 1
    assert body["stage"] is None  # it has ended
    # Result: complete and honest. The pack's offerings each lack a fact the search needs.
    assert result["input_version"] == queued["input_version"]
    assert result["target_title"] == DATA
    assert (result["coverage"], result["stop_reason"]) == ("complete", None)
    assert result["outcome"] == "unresolved"  # never "no route" while something is unknown
    assert body["code"] is None
    assert result["set_aside"]
    assert result["rank_seconds"] == 5
    assert result["rank_ms"] >= 0
    # Its facts beside the sealed output repeat the result.
    assert stored["attempt_id"] == attempt["attempt_id"]
    assert stored["output_id"] == run["output_id"]
    assert (stored["coverage"], stored["outcome"], stored["layers_exact"]) == (
        "complete",
        "unresolved",
        True,
    )
    assert stored["expanded_states"] == result["expanded_states"]
    assert stored["archived"] == len(result["schedules"]) == 0
    # The journal holds the run ID and the outcome only: never the snapshot or the result.
    assert json.loads(journal["inputs"][0]["inputs"]) == {
        "positionalArgs": [run_id],
        "namedArgs": {},
    }
    assert set(json.loads(journal["output"][0]["output"])) == {"status", "output_id"}
    assert {s["function_name"] for s in journal["steps"]} == SOLVE_STEPS
    dbos_text = json.dumps(journal, default=str)
    assert DATA not in dbos_text
    assert "minor_units" not in dbos_text


@pytest.mark.req("OPT1-12", "VERSIONS-01")
def test_a_later_edit_never_reaches_a_solve_under_way(person: Person, workers: Any) -> None:
    first = person.ask().json()
    run_id = first["run"]["run_id"]
    person.state(stated(opening_cash=gbp(900000)))  # while the solve is queued
    second = person.ask().json()
    worker = workers("worker")
    person.wait_terminal(run_id)
    person.wait_terminal(second["run"]["run_id"])
    worker.stop()

    solved = person.solve(run_id).json()
    # The first solve read version 1, as it was when asked for; the edit is a new snapshot.
    assert (first["inputs_version"], second["inputs_version"]) == (1, 2)
    assert second["input_version"] != first["input_version"]
    assert solved["result"]["input_version"] == first["input_version"]
    assert second["solve_id"] != first["solve_id"]


@pytest.mark.req("API-01", "VERSIONS-01", "OPT1-03")
def test_asking_twice_is_one_solve_and_what_a_solve_cannot_start_from_is_refused(
    person: Person,
) -> None:
    key = uuid.uuid4()
    first = person.ask(key=key)
    replayed = person.ask(key=key)
    joined = person.ask()  # another request for the same solve while it is queued
    stale = person.ask(expected_inputs_version=0)
    elsewhere = person.ask(target="Lighthouse keeper")
    past = person.ask(planning_start="2020-01")
    beyond = person.ask(horizon_months=25)

    run_id = first.json()["run"]["run_id"]
    assert first.status_code == 202, first.text
    assert (replayed.status_code, replayed.json()) == (202, first.json())
    assert joined.status_code == 200
    assert joined.json()["run"]["run_id"] == run_id
    assert joined.json()["solve_id"] == first.json()["solve_id"]
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert stale.json()["error"]["details"] == {"current_version": 1}
    assert elsewhere.status_code == 404
    assert past.status_code == 422
    assert past.json()["error"]["details"]["reason"] == "planning_start_past"
    assert beyond.status_code == 422
    solves = person.infra.query(
        "SELECT run_id FROM careerwright.route_solves WHERE workspace_id = %s",
        (person.workspace_id,),
    )
    assert [str(s["run_id"]) for s in solves] == [run_id]  # nothing refused was recorded
    # No worker ran here: cancelled while queued, the solve is never started by a later one.
    assert person.cancel(run_id).status_code == 202


@pytest.mark.req("API-05", "LIMITS-04")
def test_a_solve_missing_what_it_needs_is_refused_naming_it_never_run(
    api: ApiClient, infra: Infra, ada: str
) -> None:
    person = Person(api, infra, ada)
    person.state(stated(opening_cash=None, living_costs=None))

    refused = person.ask()

    assert refused.status_code == 422
    assert refused.json()["error"]["details"] == {
        "reason": "inputs_missing",
        "missing": ["opening_cash", "living_costs"],
    }
    assert infra.query(
        "SELECT count(*) AS n FROM careerwright.runs WHERE workspace_id = %s",
        (person.workspace_id,),
    ) == [{"n": 0}]


@pytest.mark.req("DUR-05", "LIMITS-06", "LIMITS-04")
def test_a_cancel_reaches_the_search_at_its_next_check_and_stores_nothing(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("slow", solve_check_delay_s=str(CHECK_DELAY_S))
    wait_for(lambda: bool(person.attempts(run_id)), timeout_s=30, what="the search to start")
    running = person.solve(run_id).json()

    began = time.monotonic()
    assert person.cancel(run_id).status_code == 202
    run = person.wait_terminal(run_id, timeout_s=20)
    wait_for(
        lambda: person.attempts(run_id)[0]["finished_at"] is not None,
        timeout_s=10,
        what="the attempt to end",
    )
    stopped_s = time.monotonic() - began
    worker.stop()
    [attempt] = person.attempts(run_id)

    assert (running["stage"], running["run"]["status"]) == ("searching", "running")
    assert (run["status"], run["failure_class"], run["output_id"]) == ("cancelled", None, None)
    assert attempt["outcome"] == "cancelled"
    # At its next check: well before the rest of the search would have run.
    assert stopped_s < 2 * CHECK_DELAY_S + 2
    assert person.stored(run_id) == []
    assert person.solve(run_id).json()["result"] is None


@pytest.mark.req("STATE-03", "LIMITS-02", "LIMITS-05", "OPT1-15", "API-02")
def test_a_search_its_limit_stops_is_stored_truncated_never_no_route(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("clock", solve_clock_jump="search")
    run = person.wait_terminal(run_id)
    worker.stop()
    body = person.solve(run_id).json()
    result = body["result"]
    [stored] = person.stored(run_id)

    assert run["status"] == "complete"  # a limit is a result, never a failure
    assert (result["coverage"], result["stop_reason"]) == ("budget_truncated", "wall_time_limit")
    assert result["outcome"] == "none_found_before_limit"  # never "no route"
    assert body["code"] == "SOLVE_LIMIT_REACHED"
    assert result["expanded_states"] == 1
    assert result["narrowings"]
    assert result["instance"]["concepts"] >= 1
    assert not result["layers_exact"]
    assert (stored["coverage"], stored["stop_reason"], stored["outcome"]) == (
        "budget_truncated",
        "wall_time_limit",
        "none_found_before_limit",
    )


@pytest.mark.req("OPT1-11", "LIMITS-04")
def test_a_rank_stage_past_its_own_limit_fails_the_run_and_claims_no_ranks(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("clock", solve_clock_jump="ranking")
    run = person.wait_terminal(run_id)
    worker.stop()
    [attempt] = person.attempts(run_id)

    assert (run["status"], run["failure_class"], run["output_id"]) == (
        "failed",
        "rank_limit_reached",
        None,
    )
    assert (attempt["stage"], attempt["outcome"]) == ("ranking", "rank_limit_reached")
    assert person.stored(run_id) == []
    assert person.solve(run_id).json()["result"] is None


@pytest.mark.req("OPT1-03", "OPT1-05", "DUR-02")
def test_a_crashed_solve_starts_again_under_a_new_attempt_never_a_truncated_result(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    first = workers("first", crash_at="mid_solve")
    assert first.wait_exit(60) == -signal.SIGKILL
    assert [a["outcome"] for a in person.attempts(run_id)] == [None]  # mid-search when it died

    second = workers("second")
    run = person.wait_terminal(run_id)
    second.stop()
    attempts = person.attempts(run_id)
    [stored] = person.stored(run_id)

    assert [a["outcome"] for a in attempts] == ["interrupted", "succeeded"]
    assert run["status"] == "complete"
    assert stored["attempt_id"] == attempts[1]["attempt_id"]  # the new attempt's result only
    assert stored["coverage"] == "complete"
    assert person.solve(run_id).json()["attempts"] == 2


@pytest.mark.req("OPT1-03", "DUR-02")
def test_a_result_stored_before_a_crash_is_published_and_never_solved_again(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    first = workers("first", crash_at="after_solve_stored")
    assert first.wait_exit(60) == -signal.SIGKILL
    [stored] = person.stored(run_id)
    assert person.run(run_id)["status"] == "running"  # stored, never published

    second = workers("second")
    run = person.wait_terminal(run_id)
    second.stop()
    [attempt] = person.attempts(run_id)

    assert (run["status"], run["output_id"]) == ("complete", stored["output_id"])
    assert attempt["outcome"] == "succeeded"  # one attempt: the stored result is the result
    assert person.stored(run_id) == [stored]
    assert person.solve(run_id).json()["attempts"] == 1


@pytest.mark.req("OPT1-03", "DUR-02")
def test_a_solve_whose_worker_keeps_crashing_fails_after_three_attempts(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    for n in range(MAX_ATTEMPTS):
        crashed = workers(f"crash-{n}", crash_at="mid_solve")
        assert crashed.wait_exit(60) == -signal.SIGKILL

    last = workers("last")
    run = person.wait_terminal(run_id)
    last.stop()

    assert (run["status"], run["failure_class"], run["output_id"]) == (
        "failed",
        "unknown_failure",
        None,
    )
    assert [a["outcome"] for a in person.attempts(run_id)] == ["interrupted"] * MAX_ATTEMPTS
    assert person.stored(run_id) == []


@pytest.mark.req("SEC-01", "OPT1-05")
def test_access_revoked_while_a_solve_runs_fails_it_and_stores_nothing(
    api: ApiClient, infra: Infra, workers: Any
) -> None:
    email, token = fresh_actor(api, infra)
    someone = Person(api, infra, token)
    someone.state(stated())
    run_id = someone.ask().json()["run"]["run_id"]
    worker = workers("slow", solve_check_delay_s=str(SHORT_CHECK_S))
    wait_for(lambda: bool(someone.attempts(run_id)), timeout_s=30, what="the search to start")

    infra.query("UPDATE careerwright.actors SET access = 'revoked' WHERE email = %s", (email,))
    run = someone.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"], run["output_id"]) == (
        "failed",
        "access_revoked",
        None,
    )
    assert [a["outcome"] for a in someone.attempts(run_id)] == ["failed"]
    assert someone.stored(run_id) == []


@pytest.mark.req("OPT1-06", "OPT1-07", "API-02")
def test_a_solve_that_finds_routes_stores_and_serves_them_with_their_schedules(
    person: Person, workers: Any
) -> None:
    person.ready_for_the_target()
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("worker")
    run = person.wait_terminal(run_id)
    worker.stop()
    body = person.solve(run_id).json()
    result = body["result"]
    [stored] = person.stored(run_id)

    assert run["status"] == "complete"
    assert (result["coverage"], result["outcome"], result["layers_exact"]) == (
        "complete",
        "routes_found",
        True,
    )
    assert body["code"] is None  # complete with routes: "Best trade-offs found" is the web's
    # Ready now for the modelled requirements: the empty route reaches readiness at once, in
    # F1. The pack's offerings each still lack a fact the search needs, so are set aside.
    [schedule] = result["schedules"]
    assert (schedule["route"], schedule["months_to_readiness"], schedule["layer"]) == ([], 0, 1)
    assert schedule["family_id"] in {f["family_id"] for f in result["families"]}
    assert result["set_aside"]
    # Its facts beside the sealed output repeat it.
    assert (stored["outcome"], stored["archived"], stored["layers_exact"]) == (
        "routes_found",
        1,
        True,
    )
    assert no_reason_anywhere(result)


@pytest.mark.req("PLAN-05", "EXP-01", "DUR-06", "SEC-10")
def test_a_chosen_route_is_immutable_idempotent_private_and_deleted_with_its_workspace(
    person: Person, workers: Any, infra: Infra, ben: str, api_deps: ApiDependencies
) -> None:
    person.ready_for_the_target()
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("worker")
    person.wait_terminal(run_id)
    worker.stop()
    path = f"{person.base}/planning/plans"
    assert person.api.get(f"{path}/current", person.token).status_code == 404
    body = {
        "expected_version": 0,
        "solve_run_id": run_id,
        "schedule_index": 0,
        "assumptions_confirmed": True,
    }
    original = api_deps.capability
    updated_pack = original.pack.model_copy(
        update={"dated": original.pack.dated + timedelta(days=1)}
    )
    object.__setattr__(api_deps, "capability", replace(original, pack=updated_pack))
    try:
        source_stale = person.api.write("POST", path, person.token, body)
    finally:
        object.__setattr__(api_deps, "capability", original)
    assert source_stale.json()["error"]["details"]["reason"] == "solve_source_changed"
    key = uuid.uuid4()
    first = person.api.write("POST", path, person.token, body, key=key)
    repeated = person.api.write("POST", path, person.token, body, key=key)
    assert first.status_code == repeated.status_code == 201
    saved = first.json()
    assert repeated.json() == saved
    assert saved["version"] == 1
    assert saved["source"]["solve_run_id"] == run_id
    assert (
        saved["route"]["schedule"]
        == person.api.get(
            f"{person.base}/planning/solves/{run_id}/schedules/0", person.token
        ).json()["schedule"]
    )
    assert person.api.get(f"{path}/current", person.token).json() == saved
    assert person.api.get(f"{path}/1", person.token).json() == saved
    assert person.api.get(f"{path}/changes", person.token).json()["new_solve_needed"] is False
    assert person.api.get(f"{path}/1", ben).status_code == 404
    assert person.api.write("POST", path, person.token, body).json()["error"]["code"] == (
        "STALE_INPUT_VERSION"
    )
    exported = person.api.get(f"{path}/1/export.json", person.token).json()
    assert exported == saved
    omitted = person.api.get(
        f"{path}/1/export.json",
        person.token,
        omit_financial_detail=True,
        omit_sensitive_detail=True,
    ).json()
    assert omitted["plan_id"] == saved["plan_id"]
    assert "costs" not in omitted["route"]
    assert person.api.get(f"{path}/1/calendar.ics", person.token).status_code == 200
    progress_body = {"expected_version": 1, "kind": "rest", "until": f"{next_month()}-01"}
    progress_key = uuid.uuid4()
    rest = person.api.write(
        "POST", f"{path}/progress", person.token, progress_body, key=progress_key
    )
    assert rest.status_code == 201, rest.text
    assert rest.json()["version"] == 2
    assert rest.json()["progress"]["rest_until"] == progress_body["until"]
    assert (
        person.api.write(
            "POST", f"{path}/progress", person.token, progress_body, key=progress_key
        ).json()
        == rest.json()
    )
    assert [item["version"] for item in person.api.get(f"{path}/history", person.token).json()] == [
        1,
        2,
    ]
    assert person.api.get(f"{path}/1", person.token).json() == saved
    person.state(stated(opening_cash=gbp(900000)))
    stale = person.api.write("POST", path, person.token, {**body, "expected_version": 2})
    assert stale.json()["error"]["details"]["reason"] == "solve_inputs_changed"
    assert person.api.get(f"{path}/changes", person.token).json()["planning_inputs"] is True
    assert person.api.get(f"{path}/1", person.token).json() == saved
    infra.query(
        "DELETE FROM careerwright.workspaces WHERE workspace_id = %s", (person.workspace_id,)
    )
    assert infra.query(
        "SELECT count(*) AS n FROM careerwright.plan_versions WHERE workspace_id = %s",
        (person.workspace_id,),
    ) == [{"n": 0}]
    assert person.api.get(f"{path}/1", person.token).status_code == 404


C01_FULL_TIME = "offering:C01#full_time"
C01_CONDITIONS = (
    "eligibility_area",
    "eligibility_age",
    "eligibility_earnings",
    "eligibility_no_other_funded_training",
)


@pytest.mark.req("PLAN-05", "STATE-06")
def test_a_mistaken_commitment_can_be_retracted_before_a_remaining_replan(
    person: Person, workers: Any
) -> None:
    person.ready_for_the_target()
    person.state(
        stated(
            offering_figures=[
                {
                    "offering_id": C01_FULL_TIME,
                    "start": {"on": f"{next_month()}-01", "basis": "own_figure"},
                    "weekly_hours": 9,
                    "cost": gbp(0),
                }
            ],
            variants=[
                {
                    "variant_id": C01_FULL_TIME,
                    "condition_statuses": dict.fromkeys(C01_CONDITIONS, "confirmed"),
                }
            ],
        )
    )
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("worker")
    person.wait_terminal(run_id)
    worker.stop()
    schedules = person.solve(run_id).json()["result"]["schedules"]
    index = next(i for i, row in enumerate(schedules) if row["route"] == [C01_FULL_TIME])
    plans = f"{person.base}/planning/plans"
    chosen = person.api.write(
        "POST",
        plans,
        person.token,
        {
            "expected_version": 0,
            "solve_run_id": run_id,
            "schedule_index": index,
            "assumptions_confirmed": True,
        },
    )
    assert chosen.status_code == 201, chosen.text
    accepted = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 1, "kind": "commitment_accepted", "variant_id": C01_FULL_TIME},
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["commitments"] == [C01_FULL_TIME]
    corrected = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 2, "kind": "commitment_retracted", "variant_id": C01_FULL_TIME},
    )
    assert corrected.status_code == 201, corrected.text
    assert corrected.json()["commitments"] == []
    assert corrected.json()["progress"]["completed_steps"] == []
    assert [item["kind"] for item in corrected.json()["progress"]["activity"]] == [
        "commitment_accepted",
        "commitment_retracted",
    ]
    assert person.api.get(f"{plans}/2", person.token).json() == accepted.json()
    repeated = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 3, "kind": "commitment_retracted", "variant_id": C01_FULL_TIME},
    )
    assert repeated.json()["error"]["code"] == "ALREADY_DECIDED"
    remaining_start = Month.parse(next_month()).plus(1)
    replan = person.api.write(
        "POST",
        f"{person.base}/planning/solves/replan",
        person.token,
        {
            "expected_inputs_version": person.inputs_version,
            "expected_plan_version": 3,
            "target": DATA,
            "planning_start": str(remaining_start),
            "horizon_months": 23,
            "opening_cash": gbp(500000),
            "sunk_paid": gbp(0),
            "remaining_payments": [],
            "all_remaining_payments_confirmed": True,
            "no_ongoing_steps_confirmed": True,
        },
    )
    assert replan.status_code == 202, replan.text


@pytest.mark.req("PLAN-05", "FIN1-02", "STATE-06")
def test_replan_uses_confirmed_remaining_actuals_without_recharging_completed_work(
    person: Person, workers: Any
) -> None:
    person.ready_for_the_target()
    person.state(
        stated(
            offering_figures=[
                {
                    "offering_id": C01_FULL_TIME,
                    "start": {"on": f"{next_month()}-01", "basis": "own_figure"},
                    "weekly_hours": 9,
                    "cost": gbp(0),
                }
            ],
            variants=[
                {
                    "variant_id": C01_FULL_TIME,
                    "condition_statuses": dict.fromkeys(C01_CONDITIONS, "confirmed"),
                }
            ],
        )
    )
    first_run = person.ask().json()["run"]["run_id"]
    first_worker = workers("first")
    person.wait_terminal(first_run)
    first_worker.stop()
    result = person.solve(first_run).json()["result"]
    assert result is not None, (person.run(first_run)["status"], person.attempts(first_run))
    index = next(i for i, row in enumerate(result["schedules"]) if row["route"] == [C01_FULL_TIME])
    plans = f"{person.base}/planning/plans"
    chosen = person.api.write(
        "POST",
        plans,
        person.token,
        {
            "expected_version": 0,
            "solve_run_id": first_run,
            "schedule_index": index,
            "assumptions_confirmed": True,
        },
    )
    assert chosen.status_code == 201, chosen.text
    committed = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 1, "kind": "commitment_accepted", "variant_id": C01_FULL_TIME},
    )
    assert committed.status_code == 201, committed.text
    remaining_start = Month.parse(next_month()).plus(1)
    body = {
        "expected_inputs_version": person.inputs_version,
        "expected_plan_version": 2,
        "target": DATA,
        "planning_start": str(remaining_start),
        "horizon_months": 23,
        "opening_cash": gbp(500000),
        "sunk_paid": gbp(20000),
        "remaining_payments": [
            {
                "variant_id": C01_FULL_TIME,
                "due": str(remaining_start.first_day()),
                "amount": gbp(30000),
            }
        ],
        "all_remaining_payments_confirmed": True,
        "no_ongoing_steps_confirmed": True,
    }
    path = f"{person.base}/planning/solves/replan"
    missing_confirmation = person.api.write(
        "POST",
        path,
        person.token,
        {k: v for k, v in body.items() if k != "no_ongoing_steps_confirmed"},
    )
    assert missing_confirmation.status_code == 422
    prepaid = person.api.write("POST", path, person.token, {**body, "remaining_payments": []})
    assert prepaid.json()["error"]["details"]["reason"] == "ongoing_step_not_modelled"
    assert prepaid.json()["error"]["details"]["variant_id"] == C01_FULL_TIME
    unfinished = person.api.write("POST", path, person.token, body)
    assert unfinished.json()["error"]["details"]["reason"] == "ongoing_step_not_modelled"
    assert unfinished.json()["error"]["details"]["variant_id"] == C01_FULL_TIME
    completed = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 2, "kind": "step_completed", "variant_id": C01_FULL_TIME},
    )
    assert completed.status_code == 201, completed.text
    body = {**body, "expected_plan_version": 3}
    stale = person.api.write("POST", path, person.token, {**body, "expected_plan_version": 2})
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    key = uuid.uuid4()
    asked = person.api.write("POST", path, person.token, body, key=key)
    assert asked.status_code == 202, asked.text
    assert person.api.write("POST", path, person.token, body, key=key).json() == asked.json()
    run_id = asked.json()["run"]["run_id"]
    worker = workers("remaining")
    person.wait_terminal(run_id)
    worker.stop()
    solved = person.solve(run_id).json()
    assert solved["remaining_horizon_recalculated"] is True
    assert all(C01_FULL_TIME not in row["route"] for row in solved["result"]["schedules"])
    empty = next(i for i, row in enumerate(solved["result"]["schedules"]) if not row["route"])
    preview = person.api.get(
        f"{plans}/revision-preview", person.token, solve_run_id=run_id, schedule_index=empty
    )
    assert preview.status_code == 200, preview.text
    difference = preview.json()["difference"]
    assert difference["remaining_horizon_recalculated"] is True
    assert difference["same_accounting_basis"] is False
    assert difference["old_basis"]["planning_start"] == next_month()
    assert difference["new_basis"]["planning_start"] == str(remaining_start)
    assert difference["new_basis"]["replan"]["sunk_paid"] == gbp(20000)
    assert difference["new_direct_cost"] == gbp(30000)
    revised = person.api.write(
        "POST",
        plans,
        person.token,
        {
            "expected_version": 3,
            "solve_run_id": run_id,
            "schedule_index": empty,
            "assumptions_confirmed": True,
        },
    )
    assert revised.status_code == 201, revised.text
    assert revised.json()["version"] == 4
    assert revised.json()["route"]["basis"]["replan"]["sunk_paid"] == gbp(20000)
    assert revised.json()["progress"]["completed_steps"] == []
    assert person.api.get(f"{plans}/3", person.token).json() == completed.json()
    reused = person.api.write(
        "POST",
        plans,
        person.token,
        {
            "expected_version": 4,
            "solve_run_id": run_id,
            "schedule_index": empty,
            "assumptions_confirmed": True,
        },
    )
    assert reused.json()["error"]["details"]["reason"] == "replan_source_changed"
    omitted = person.api.get(
        f"{plans}/4/export.json", person.token, omit_financial_detail=True
    ).json()
    assert "20000" not in str(omitted)
    assert "30000" not in str(omitted)
    assert omitted["route"]["basis"]["replan"] == {"from_plan_version": 3}


@pytest.mark.req("OPTN-13", "OPTN-09", "OPT1-07", "API-06")
def test_p01_with_the_missing_facts_supplied_gets_routes_each_qualified_and_without_them_names_them(
    person: Person, workers: Any
) -> None:
    """Task 12b's P01 acceptance at the API: without the facts the search lacks, the result
    names them on each option set aside, never "no route"; with them supplied at the
    checkpoint, computed routes, the one resting on the person's figures qualified."""
    person.ready_for_the_target()
    without = person.ask().json()["run"]["run_id"]
    worker = workers("worker")
    person.wait_terminal(without)
    person.state(
        stated(
            offering_figures=[
                {
                    "offering_id": C01_FULL_TIME,
                    "start": {"on": f"{next_month()}-01", "basis": "own_figure"},
                    "weekly_hours": 9,
                    "cost": gbp(0),
                }
            ],
            variants=[
                {
                    "variant_id": C01_FULL_TIME,
                    "condition_statuses": dict.fromkeys(C01_CONDITIONS, "confirmed"),
                }
            ],
        )
    )
    supplied = person.ask().json()["run"]["run_id"]
    person.wait_terminal(supplied)
    worker.stop()
    before = person.solve(without).json()["result"]
    after = person.solve(supplied).json()["result"]

    assert before["outcome"] != "no_route_in_bounded_model"
    aside = {s["variant_id"]: s for s in before["set_aside"]}
    assert {"dates_unknown", "cost_unknown", "workload_unknown"} <= set(
        aside[C01_FULL_TIME]["unresolved"]
    )
    assert after["outcome"] == "routes_found"
    routes = {tuple(s["route"]): s for s in after["schedules"]}
    assert (C01_FULL_TIME,) in routes
    assert "supplied_figures" in routes[(C01_FULL_TIME,)]["qualifications"]
    assert "supplied_figures" not in routes[()]["qualifications"]
    assert C01_FULL_TIME not in {s["variant_id"] for s in after["set_aside"]}
    assert no_reason_anywhere(after)


@pytest.mark.req("VIS2-09", "VIS2-08", "OPTN-13", "FRESH-06", "STATE-06", "API-06", "DUR-03")
def test_the_routes_chapter_reads_a_solve_s_comparison_pages_and_a_chosen_route(
    person: Person, workers: Any
) -> None:
    """Task 14's facts at the API, on P01 with C01's missing facts supplied: the comparison
    leads with the best trade-offs, every schedule is reachable in the pages, and a chosen
    route's steps name the pack's date and each record's review state, rechecked on the
    solve's own input. A later edit is named beside the routes, never applied to them."""
    person.ready_for_the_target()
    person.state(
        stated(
            offering_figures=[
                {
                    "offering_id": C01_FULL_TIME,
                    "start": {"on": f"{next_month()}-01", "basis": "own_figure"},
                    "weekly_hours": 9,
                    "cost": gbp(0),
                }
            ],
            variants=[
                {
                    "variant_id": C01_FULL_TIME,
                    "condition_statuses": dict.fromkeys(C01_CONDITIONS, "confirmed"),
                }
            ],
        )
    )
    asked = person.ask().json()
    run_id = asked["run"]["run_id"]
    base = f"{person.base}/planning/solves/{run_id}"
    early = person.api.get(f"{base}/comparison", person.token)  # queued: no result yet
    worker = workers("worker")
    person.wait_terminal(run_id)
    worker.stop()

    compared = person.api.get(f"{base}/comparison", person.token)
    # Query parameters as `params`: httpx replaces a query string in the path with them.
    pages = person.api.get(f"{base}/schedules", person.token, limit=1).json()
    rest = person.api.get(
        f"{base}/schedules", person.token, limit=200, cursor=pages["next_cursor"]
    ).json()
    assert pages["next_cursor"] is not None  # more than one schedule: the empty route and C01
    index = next(i["index"] for i in [*pages["items"], *rest["items"]] if i["route"])
    detail = person.api.get(f"{base}/schedules/{index}", person.token)
    plans = f"{person.base}/planning/plans"
    chosen = person.api.write(
        "POST",
        plans,
        person.token,
        {
            "expected_version": 0,
            "solve_run_id": run_id,
            "schedule_index": index,
            "assumptions_confirmed": True,
        },
    )
    assert chosen.status_code == 201, chosen.text
    committed = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 1, "kind": "commitment_accepted", "variant_id": C01_FULL_TIME},
    )
    assert committed.status_code == 201, committed.text
    assert committed.json()["commitments"] == [C01_FULL_TIME]
    reported = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 2, "kind": "step_completed", "variant_id": C01_FULL_TIME},
    )
    assert reported.status_code == 201, reported.text
    assert reported.json()["progress"]["completed_steps"] == [C01_FULL_TIME]
    step_title = chosen.json()["route"]["steps"][0]["title"]
    assert reported.json()["progress"]["activity"][-1]["step_title"] == step_title
    assert reported.json()["route"] == chosen.json()["route"]
    assert reported.json()["source"] == chosen.json()["source"]
    assert "BEGIN:VEVENT" not in person.api.get(f"{plans}/3/calendar.ics", person.token).text
    retracted = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 3, "kind": "step_retracted", "variant_id": C01_FULL_TIME},
    )
    assert retracted.status_code == 201, retracted.text
    assert retracted.json()["progress"]["completed_steps"] == []
    assert retracted.json()["progress"]["activity"][-1]["step_title"] == step_title
    assert "BEGIN:VEVENT" in person.api.get(f"{plans}/4/calendar.ics", person.token).text
    duplicate_retraction = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 4, "kind": "step_retracted", "variant_id": C01_FULL_TIME},
    )
    assert duplicate_retraction.json()["error"]["code"] == "ALREADY_DECIDED"
    reported_again = person.api.write(
        "POST",
        f"{plans}/progress",
        person.token,
        {"expected_version": 4, "kind": "step_completed", "variant_id": C01_FULL_TIME},
    )
    assert reported_again.status_code == 201, reported_again.text
    assert reported_again.json()["progress"]["completed_steps"] == [C01_FULL_TIME]
    preview = person.api.get(
        f"{plans}/revision-preview", person.token, solve_run_id=run_id, schedule_index=0
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["from_version"] == 5
    assert preview.json()["difference"]["removed_steps"] == [C01_FULL_TIME]
    assert preview.json()["difference"]["remaining_horizon_recalculated"] is False
    assert person.api.get(f"{plans}/current", person.token).json()["version"] == 5
    revision_body = {
        "expected_version": 5,
        "solve_run_id": run_id,
        "schedule_index": 0,
        "assumptions_confirmed": True,
    }
    refused = person.api.write("POST", plans, person.token, revision_body)
    assert refused.json()["error"]["details"]["reason"] == "full_horizon_accounting"
    accepted = person.api.write(
        "POST",
        plans,
        person.token,
        {**revision_body, "full_horizon_accounting_acknowledged": True},
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["version"] == 6
    assert accepted.json()["progress"]["completed_steps"] == []
    assert any(
        item["kind"] == "step_completed" and item["variant_id"] == C01_FULL_TIME
        for item in accepted.json()["progress"]["activity"]
    )
    assert accepted.json()["commitments"] == []
    assert all(
        item["step_title"] == step_title
        for item in accepted.json()["progress"]["activity"]
        if item["variant_id"] == C01_FULL_TIME
    )
    assert any(
        item["kind"] == "commitment_accepted" and item["variant_id"] == C01_FULL_TIME
        for item in accepted.json()["progress"]["activity"]
    )
    assert person.api.get(f"{plans}/1", person.token).json() == chosen.json()
    assert person.api.get(f"{plans}/2", person.token).json()["commitments"] == [C01_FULL_TIME]
    matrices = person.api.get(f"{person.base}/capability/matrices", person.token).json()
    row = next(r for m in matrices["matrices"] for r in m["rows"] if r["required"])
    corrected = person.api.write(
        "POST",
        f"{person.base}/capability/evidence",
        person.token,
        {
            "expected_version": matrices["version"],
            "subject": row["subject"],
            "rubric_version": row["rubric"]["version_id"],
            "answer": "unsure",
        },
    )
    assert corrected.status_code == 201, corrected.text
    skill_later = person.api.get(f"{base}/comparison", person.token).json()
    person.state(stated(opening_cash=gbp(900000)))  # a later edit
    later = person.api.get(f"{base}/comparison", person.token).json()
    missing = person.api.get(f"{base}/schedules/999", person.token)

    assert early.status_code == 422
    assert early.json()["error"]["details"]["reason"] == "solve_not_complete"
    assert compared.status_code == 200, compared.text
    body = compared.json()
    assert (body["lead"], body["code"], body["coverage"]) == (
        "best_trade_offs_found",
        None,
        "complete",
    )
    assert body["basis"]["objective_basis"] == "economic"
    assert body["basis"]["baseline"]["kind"] == "current_role"
    assert body["basis"]["horizon_months"] == 24
    assert body["label"]["dated"]  # the pack's date (R9)
    assert body["points_shown"] == body["points_total"]
    assert body["changed_since"] == {
        "planning_inputs": False,
        "profile": False,
        "capability": False,
        "target_matrix": False,
        "option_pack": False,
    }
    assert skill_later["changed_since"] == {
        "planning_inputs": False,
        "profile": False,
        "capability": True,
        "target_matrix": True,
        "option_pack": False,
    }
    assert later["changed_since"]["planning_inputs"] is True
    # Every retained schedule, once, across the pages.
    seen = [i["index"] for i in [*pages["items"], *rest["items"]]]
    assert seen == list(range(body["schedules_total"]))
    assert rest["next_cursor"] is None
    assert detail.status_code == 200, detail.text
    chosen = detail.json()
    [step] = chosen["steps"]
    assert step["variant_id"] == C01_FULL_TIME
    assert "supplied_figures" in step["qualified_by"]
    assert {r["record"] for r in step["records"]} >= {"concept", "offering"}
    assert all(r["review_state"] for r in step["records"])
    assert step["title"]
    assert next(m["month"] for m in chosen["months"]) == next_month()
    assert len(chosen["scenarios"]) == 3
    assert missing.status_code == 404
    assert no_reason_anywhere(body)
    assert no_reason_anywhere(chosen)


@pytest.mark.req("OPT1-04", "LIMITS-02")
def test_two_solves_asked_together_run_one_at_a_time_each_on_its_own_clock(
    person: Person, workers: Any
) -> None:
    runs = [
        person.ask().json()["run"]["run_id"],
        person.ask(horizon_months=23).json()["run"]["run_id"],  # another solve, not a join
    ]
    worker = workers("slow", solve_check_delay_s=str(SHORT_CHECK_S))
    wait_for(lambda: any(person.attempts(r) for r in runs), timeout_s=30, what="a search")
    # While one searches, the other waits its turn: still queued, with no attempt.
    waiting = [person.run(r)["status"] for r in runs if not person.attempts(r)]
    finished = [person.wait_terminal(r)["status"] for r in runs]
    worker.stop()
    attempts = sorted(
        ((person.attempts(r), person.stored(r)) for r in runs),
        key=lambda found: found[0][0]["started_at"],
    )
    [([earlier], _), ([later], [later_result])] = attempts

    assert finished == ["complete", "complete"]
    assert waiting == ["queued"]
    assert later["started_at"] >= earlier["finished_at"]  # one at a time
    # Its clock started when it ran: its search took no longer than its own attempt.
    ran_ms = (later["finished_at"] - later["started_at"]).total_seconds() * 1000
    assert later_result["search_ms"] <= ran_ms


@pytest.mark.req("DUR-05", "OPT1-05")
def test_a_solve_cancelled_while_it_waits_its_turn_never_runs(person: Person, workers: Any) -> None:
    runs = [
        person.ask().json()["run"]["run_id"],
        person.ask(horizon_months=23).json()["run"]["run_id"],
    ]
    worker = workers("slow", solve_check_delay_s=str(SHORT_CHECK_S))
    wait_for(lambda: any(person.attempts(r) for r in runs), timeout_s=30, what="a search")
    [running] = [r for r in runs if person.attempts(r)]
    [waiting] = [r for r in runs if r != running]

    assert person.cancel(waiting).status_code == 202
    cancelled = person.wait_terminal(waiting, timeout_s=10)
    other_then = person.run(running)["status"]
    finished = person.wait_terminal(running)
    worker.stop()

    assert cancelled["status"] == "cancelled"
    assert person.attempts(waiting) == []  # it never ran, and never will
    assert other_then == "running"  # it ended while the other still searched
    assert finished["status"] == "complete"


@pytest.mark.req("DUR-05", "OPT1-03")
def test_a_solve_asked_for_again_after_its_cancel_is_a_new_run(person: Person) -> None:
    first = person.ask().json()["run"]["run_id"]
    # No worker runs here: the run stays queued with its cancel recorded, never joined.
    assert person.cancel(first).status_code == 202

    again = person.ask()

    assert again.status_code == 202, again.text
    assert again.json()["run"]["run_id"] != first
    assert person.run(first)["status"] == "queued"
    # Cancelled too, so no later test's worker starts it (solves run one at a time).
    assert person.cancel(again.json()["run"]["run_id"]).status_code == 202


# Every way a run ends settles its attempts: none reads as still running once the run has
# ended (review 13b, run half Minor 2).


@pytest.mark.req("DUR-05")
def test_a_cancel_published_as_the_worker_dies_leaves_no_attempt_unfinished(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("stalled", solve_check_delay_s=str(STALLED_CHECK_S))
    wait_for(lambda: bool(person.attempts(run_id)), timeout_s=30, what="the search to start")

    assert person.cancel(run_id).status_code == 202
    run = person.wait_terminal(run_id, timeout_s=STALLED_CHECK_S / 2)  # the worker loop's
    worker.kill()  # before the search's next check could end its attempt

    assert run["status"] == "cancelled"
    [attempt] = person.attempts(run_id)
    assert attempt["outcome"] == "cancelled"
    assert attempt["finished_at"] is not None


@pytest.mark.req("DUR-05", "DUR-02")
def test_a_solve_cancelled_after_a_crash_leaves_no_attempt_unfinished(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    first = workers("first", crash_at="mid_solve")
    assert first.wait_exit(60) == -signal.SIGKILL
    assert person.cancel(run_id).status_code == 202

    second = workers("second")
    run = person.wait_terminal(run_id)
    second.stop()

    assert run["status"] == "cancelled"
    assert [a["outcome"] for a in person.attempts(run_id)] == ["cancelled"]


@pytest.mark.req("DUR-08", "OPT1-05")
def test_a_solve_whose_store_stays_away_fails_and_leaves_no_attempt_unfinished(
    person: Person, infra: Infra, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("slow", solve_check_delay_s=str(SHORT_CHECK_S))
    wait_for(lambda: bool(person.attempts(run_id)), timeout_s=30, what="the search to start")

    restorer = cut_worker_database_for(infra, OUTAGE_S)
    try:
        run = person.wait_terminal(run_id, timeout_s=120)
    finally:
        restorer.join()
        infra.query("ALTER ROLE careerwright_worker LOGIN")
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "app_store_unavailable")
    [attempt] = person.attempts(run_id)
    assert (attempt["outcome"], attempt["finished_at"] is not None) == ("interrupted", True)
    assert person.stored(run_id) == []


@pytest.mark.req("OPT1-05")
def test_a_solve_whose_result_cannot_be_stored_fails_and_leaves_no_attempt_unfinished(
    person: Person, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("worker", crash_at="solve_store_fails")
    run = person.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"], run["output_id"]) == (
        "failed",
        "unknown_failure",
        None,
    )
    assert [a["outcome"] for a in person.attempts(run_id)] == ["interrupted"]
    assert person.stored(run_id) == []


@pytest.mark.req("SEC-02", "ARC1-08")
def test_another_person_sees_no_solve_of_mine(
    person: Person, infra: Infra, ben: str, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("worker")
    person.wait_terminal(run_id)
    worker.stop()

    assert person.solve(run_id, ben).status_code == 404
    for table in ("route_solves", "route_solve_attempts", "route_solve_results"):
        statement = f"SELECT count(*) AS n FROM careerwright.{table} WHERE run_id = %s"  # noqa: S608
        as_owner = infra.as_role("pg_api", statement, (run_id,), actor=ADA_ID)
        as_other = infra.as_role("pg_api", statement, (run_id,), actor=BEN_ID)
        assert (as_owner, as_other) == ([{"n": 1}], [{"n": 0}]), table


BROKEN_RESULTS = (
    # A stopped search is never "no route" and never unresolved.
    "coverage = 'budget_truncated', stop_reason = 'wall_time_limit', layers_exact = false, "
    "outcome = 'no_route_in_bounded_model'",
    "coverage = 'budget_truncated', stop_reason = 'state_limit', layers_exact = false, "
    "unexplored_branches = 3",
    "stop_reason = 'archive_limit'",  # complete, yet names a limit
    "layers_exact = false",  # complete, yet not exact
    "outcome = 'none_found_before_limit'",  # complete, yet "before the limit"
    "outcome = 'routes_found'",  # nothing archived
    "unexplored_branches = 1",  # complete, yet something left unexplored
    "archived = 50001, outcome = 'routes_found'",  # past the archive cap
    "expanded_states = 1000001",  # past the state cap
)


@pytest.mark.req("STATE-03", "LIMITS-05", "OPT1-07", "OPT1-05")
def test_the_database_repeats_the_search_s_rules(
    person: Person, infra: Infra, workers: Any
) -> None:
    run_id = person.ask().json()["run"]["run_id"]
    worker = workers("worker")
    person.wait_terminal(run_id)
    worker.stop()
    [stored] = person.stored(run_id)
    assert (stored["coverage"], stored["outcome"]) == ("complete", "unresolved")

    for broken in BROKEN_RESULTS:
        with pytest.raises(psycopg.errors.CheckViolation):
            infra.query(
                f"UPDATE careerwright.route_solve_results SET {broken} WHERE run_id = %s",  # noqa: S608
                (run_id,),
            )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        infra.as_role(  # the API only reads a result
            "pg_api",
            "UPDATE careerwright.route_solve_results SET archived = 0 WHERE run_id = %s",
            (run_id,),
            actor=ADA_ID,
        )
