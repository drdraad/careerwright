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
from datetime import date
from pathlib import Path
from typing import Any

import psycopg
import pytest

from careerwright.planning.months import Month
from careerwright.seed import INVITED_ACTORS
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra
from tests.support.workers import Worker, start_worker, wait_for

pytestmark = pytest.mark.integration

ADA_ID, BEN_ID = (str(actor.actor_id) for actor in INVITED_ACTORS)
DATA = "Data quality analyst"
TERMINAL = {"complete", "failed", "provider_unavailable", "cancelled"}
SOLVE_STEPS = {"careerwright.bounded_route_solve", "careerwright.publish_outcome"}
CHECK_DELAY_S = 2.0  # each candidate, in the slow worker: the pack target checks about five


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
