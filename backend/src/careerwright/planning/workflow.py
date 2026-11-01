"""The DBOS workflow for route solves (adapter; ADR 0002, ADR 0016's Task 13b amendment):
the run ID in, `{"status", "output_id"}` or `{"status", "failure_class"}` out.

One bounded step runs the solve (`solve_runs.execute`), then the shared publication step
(`careerwright.identity.workflow.publish_outcome`), which keeps retrying through a database
outage. The journal holds the run ID, the outcome and label-only errors: never the snapshot or
the result. The step is the one retry owner, and only for a store outage: it runs the activity
again, which solves again from the start under a new attempt ID (the solve is pure and costs
nothing). A worker crash is recovered the same way, by DBOS. A cancel reaches the search at
its next check, inside the step; the worker loop's `DBOS.cancel_workflow` stops anything after.
"""

import uuid

from dbos import DBOS
from dbos import error as dbos_error

from careerwright.identity import run_store
from careerwright.identity.activity import Outcome, failed
from careerwright.identity.failures import FailureClass
from careerwright.identity.workflow import publish_outcome
from careerwright.planning import solve_runs
from careerwright.planning.solve_runs import SolveRuntime

WORKFLOW_NAME = run_store.ROUTE_SOLVE_WORKFLOW
SOLVE_STEP_ATTEMPTS = 3
SOLVE_INTERVAL_S = 1.0
SOLVE_BACKOFF_RATE = 2.0

_runtime: SolveRuntime | None = None


class TransientSolveError(Exception):
    """The store went away while the solve ran. Carries a label only."""

    def __init__(self, label: str) -> None:
        super().__init__(f"transient route solve failure ({label})")
        self.label = label


def configure(runtime: SolveRuntime) -> None:
    global _runtime
    _runtime = runtime


def _rt() -> SolveRuntime:
    if _runtime is None:
        raise RuntimeError("route solve runtime is not configured")
    return _runtime


def _is_transient(error: BaseException) -> bool:
    return isinstance(error, TransientSolveError)


@DBOS.step(
    name="careerwright.bounded_route_solve",
    retries_allowed=True,
    max_attempts=SOLVE_STEP_ATTEMPTS,
    interval_seconds=SOLVE_INTERVAL_S,
    backoff_rate=SOLVE_BACKOFF_RATE,
    should_retry=_is_transient,
)
def bounded_route_solve(run_id: str) -> Outcome:
    end = solve_runs.execute(_rt(), uuid.UUID(run_id))
    if end.outcome is not None:
        return end.outcome
    # Raised outside any handler: the exception carries a label and nothing else.
    raise TransientSolveError(end.label)


@DBOS.workflow(name=WORKFLOW_NAME)
def route_solve_workflow(run_id: str) -> Outcome:
    try:
        outcome = bounded_route_solve(run_id)
    except dbos_error.DBOSMaxStepRetriesExceeded:
        outcome = failed(FailureClass.APP_STORE_UNAVAILABLE)
    publish_outcome(run_id, outcome)
    return outcome
