"""The real worker loop with a fake model and optional crash points, as a separate process.

Configured by environment only, like the product worker. Crash points are a real SIGKILL at
a named moment, so DBOS recovery is exercised rather than simulated:
- `after_settle`: the attempt's result (an accepted output, or a terminal failure) and its
  usage are committed, the DBOS step is not;
- `after_dispatch_before_mark`: the workflow started, its outbox entry not yet marked;
- `after_first_partial`: the first piece of a streamed reply is committed, mid-call.
- `after_acquired_target`: an acquisition target's result is committed, its step is not.
- `mid_solve`: a route solve's attempt is committed and its search has begun.
- `after_solve_stored`: a route solve's result, its facts and its attempt's end are
  committed, the DBOS step is not.
Two fault points are not crashes: `recording_fails` makes every target's recording
transaction fail for good, so it rolls back and leaves the attempt `pending`; and
`solve_store_fails` makes storing a route solve's result fail for good, so its transaction,
the attempt's end included, rolls back.

Route solves (Task 13b) take two more settings: `solve_check_delay_s` makes each candidate
check that long (so a test can cancel a search under way), and `solve_clock_jump` moves the
search's clock past a limit at one moment: `search` after its first candidate (the 30-second
limit stops it), `ranking` after the rank stage's layers (its own limit stops it).

The acquisition worker it calls is `CAREERWRIGHT_ACQUISITION_URL` (a test-started one).
"""

import os
import signal
import time
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from careerwright.config import WorkerSettings
from careerwright.db import create_engine, url_with_password
from careerwright.evidence import acquisition
from careerwright.evidence import workflow as acquisition_workflow
from careerwright.evidence.acquisition import AcquisitionRuntime
from careerwright.evidence.service_client import HttpAcquisitionClient
from careerwright.identity import activity, run_store, worker
from careerwright.identity.activity import ActivityRuntime
from careerwright.identity.keyring import load_keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.records import Run
from careerwright.logs import configure_logging
from careerwright.planning import search as route_search
from careerwright.planning import solve_runs
from careerwright.planning import store as planning_store
from careerwright.planning import workflow as solve_workflow
from careerwright.planning.checker import RouteCheck, Scenario, check_route
from careerwright.planning.compiler import MonthlyInput
from careerwright.planning.layers import Point, rank
from careerwright.planning.solve_runs import SolveRuntime
from careerwright.worker import SETTLE_ATTEMPTS, TASKS, WORKFLOWS, model_builder
from tests.support.fake_models import FakeFailure, fake_model_builder

PAST_THE_SEARCH_LIMIT_S = 31.0


def _kill() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


class JumpingClock:
    """The route search's clock: the real one, moved on by `offset` once a fault says so."""

    def __init__(self) -> None:
        self.offset = 0.0

    def __call__(self) -> float:
        return time.monotonic() + self.offset


def install_solve_faults(clock: JumpingClock) -> None:
    delay = float(os.environ.get("CAREERWRIGHT_TEST_SOLVE_CHECK_DELAY_S", "0"))
    jump = os.environ.get("CAREERWRIGHT_TEST_SOLVE_CLOCK_JUMP", "")

    def slow_or_jumping_check(
        monthly: MonthlyInput, route: Sequence[str], scenario: Scenario = Scenario.BASE
    ) -> RouteCheck:
        time.sleep(delay)
        found = check_route(monthly, route, scenario)
        if jump == "search":
            clock.offset = PAST_THE_SEARCH_LIMIT_S
        return found

    def jumping_layers(points: Sequence[Point]) -> list[int | None]:
        found = rank(points)
        clock.offset += route_search.RANK_SECONDS
        return found

    route_search.check_route = slow_or_jumping_check  # type: ignore[attr-defined]
    if jump == "ranking":
        route_search.rank = jumping_layers  # type: ignore[attr-defined]
    elif jump not in ("", "search"):
        raise ValueError(f"unknown clock jump {jump!r}")


def install_crash_point(point: str) -> None:
    if point == "after_settle":
        settle = activity._settle

        def settle_then_die(*args: object) -> activity.ActivityEnd:
            settle(*args)  # type: ignore[arg-type]
            _kill()
            raise AssertionError("unreachable")

        activity._settle = settle_then_die  # type: ignore[assignment]
    elif point == "after_dispatch_before_mark":
        run_store.mark_dispatched = lambda tx, outbox_id: _kill()
    elif point == "after_first_partial":
        write = activity._write_partial

        def write_then_die(rt: ActivityRuntime, run: Run, text: str) -> None:
            write(rt, run, text)
            _kill()

        activity._write_partial = write_then_die
    elif point == "after_acquired_target":
        acquire = acquisition.acquire_target

        def acquire_then_die(
            rt: AcquisitionRuntime, run_id: uuid.UUID, position: int
        ) -> dict[str, str]:
            acquire(rt, run_id, position)
            _kill()
            raise AssertionError("unreachable")

        acquisition.acquire_target = acquire_then_die
    elif point == "recording_fails":
        # Not a crash: the recording transaction fails for good, so it rolls back and the
        # target's attempt is left `pending` (fix round 3, review B M1).
        def fail(*args: object) -> None:
            raise RuntimeError("synthetic recording failure")

        acquisition.start_extraction = fail  # type: ignore[attr-defined,assignment]
    elif point == "mid_solve":

        def die(*args: object, **kwargs: object) -> route_search.Archive:
            _kill()
            raise AssertionError("unreachable")

        solve_runs.search_archive = die  # type: ignore[attr-defined]
    elif point == "after_solve_stored":
        store_result = solve_runs._store

        def store_then_die(
            rt: SolveRuntime,
            ready: solve_runs._Ready,
            result: route_search.SearchResult,
            monthly: MonthlyInput,
        ) -> solve_runs.SolveEnd:
            store_result(rt, ready, result, monthly)
            _kill()
            raise AssertionError("unreachable")

        solve_runs._store = store_then_die
    elif point == "solve_store_fails":
        # Not a crash: the result's facts are refused for good, so the transaction that stores
        # them and ends the attempt rolls back.
        def refuse(*args: object) -> None:
            raise RuntimeError("synthetic store failure")

        planning_store.insert_solve_result = refuse  # type: ignore[assignment]
    elif point:
        raise ValueError(f"unknown crash point {point!r}")


def main() -> None:
    configure_logging("test-worker")
    settings = WorkerSettings()
    failure = os.environ.get("CAREERWRIGHT_TEST_FAKE_FAILURE")
    runtime = ActivityRuntime(
        engine=create_engine(settings.app_database, application_name="test-worker"),
        keyring=load_keyring(settings.master_key_dir),
        # The product builder (the real fixture interviewer for demo workspaces), with the
        # fake in place of Meta.
        build_model=model_builder(
            fake_model_builder(
                delay_s=float(os.environ.get("CAREERWRIGHT_TEST_FAKE_DELAY_S", "0")),
                failure=FakeFailure(failure) if failure else None,
                output_sentinel=os.environ.get("CAREERWRIGHT_TEST_OUTPUT_SENTINEL", ""),
                call_log=Path(log)
                if (log := os.environ.get("CAREERWRIGHT_TEST_CALL_LOG"))
                else None,
            )
        ),
        clock=lambda: datetime.now(UTC),
        tasks=TASKS,
        store_retry_budget_s=float(
            os.environ.get("CAREERWRIGHT_TEST_STORE_RETRY_BUDGET_S", activity.STORE_RETRY_BUDGET_S)
        ),
        settle_attempts=SETTLE_ATTEMPTS,
    )
    install_crash_point(os.environ.get("CAREERWRIGHT_TEST_CRASH_AT", ""))
    models = ModelChoice.configure(
        settings.meta_test_model, settings.meta_production_model, settings.synthetic_model_role
    )
    acquisition_workflow.configure(
        AcquisitionRuntime(runtime, HttpAcquisitionClient(settings.acquisition_url), models)
    )
    clock = JumpingClock()
    install_solve_faults(clock)
    solve_workflow.configure(SolveRuntime(runtime, clock=clock))
    worker.run(runtime.engine, runtime, url_with_password(settings.dbos_database), WORKFLOWS)


if __name__ == "__main__":
    main()
