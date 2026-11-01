"""The DBOS worker loop: recovers pending workflows, drains the outbox, reports health.

The worker never receives a Meta key from its environment: the activity opens the
workspace's sealed key just in time. Shutdown is bounded: after SIGTERM the loop stops,
DBOS is destroyed without waiting for workflows, and the process then ends at once, so a
workflow still on a DBOS executor thread (a model call in flight, or its bookkeeping) is
left as a crash would leave it, and DBOS recovers it on the next start. A normal interpreter
exit would join those non-daemon threads with no bound: that was the recurring shutdown hang
(Task 1, W2B; Task 3b's regression test). A watchdog, armed by the signal, ends the process
if any of this takes longer than `SHUTDOWN_DEADLINE_S`. The process entry point, which
composes the run tasks of every module, is `careerwright.worker`.
"""

import logging
import os
import signal
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from types import FrameType
from typing import NoReturn

from dbos import DBOS, DBOSConfig, DBOSPortableJSONSerializer, SetWorkflowID

from careerwright.db import Engine, system_transaction
from careerwright.identity import activity, run_store, workflow
from careerwright.identity.activity import ActivityRuntime

APP_NAME = "careerwright"
# Pinned: DBOS recovers only workflows of the same version. Changing the workflow's step
# sequence needs a new version and a drain of in-flight runs (ADR 0002 decision 9).
APPLICATION_VERSION = "careerwright-l0-1"
DISPATCH_INTERVAL_S = 0.2
RECONCILE_INTERVAL_S = 60.0
SHUTDOWN_DEADLINE_S = 10.0
HEARTBEAT_FILE = Path(
    os.environ.get("CAREERWRIGHT_WORKER_HEARTBEAT", "/tmp/careerwright-worker-heartbeat")  # noqa: S108
)
HEARTBEAT_STALE_S = 15.0
EXIT_SHUTDOWN_TIMEOUT = 75
_log = logging.getLogger("careerwright.worker")


def dbos_config(system_database_url: str) -> DBOSConfig:
    return {
        "name": APP_NAME,
        "system_database_url": system_database_url,
        "application_version": APPLICATION_VERSION,
        # JSON journal: only plain values can be journalled, inspectable without unpickling.
        "serializer": DBOSPortableJSONSerializer(),
        # The runtime role cannot run DDL; setup migrated the schema (ADR 0002 decision 2).
        "run_migrations": False,
    }


# A workflow by its outbox name: the model run's here; other modules' are composed in
# `careerwright.worker` (identity imports no other module).
Workflows = Mapping[str, Callable[[str], object]]
MODEL_WORKFLOWS: Workflows = {run_store.MODEL_RUN_WORKFLOW: workflow.model_run_workflow}


def dispatch_outbox(engine: Engine, workflows: Workflows = MODEL_WORKFLOWS) -> int:
    with system_transaction(engine) as tx:
        entries = run_store.pending_outbox(tx)
    for outbox_id, workflow_id, run_id, name in entries:
        # The workflow ID is the idempotency key: replaying an entry that was started but not
        # marked dispatched returns the existing workflow instead of starting another.
        with SetWorkflowID(workflow_id):
            DBOS.start_workflow(workflows[name], str(run_id))
        with system_transaction(engine) as tx:
            run_store.mark_dispatched(tx, outbox_id)
    return len(entries)


def act_on_cancellations(engine: Engine, runtime: ActivityRuntime) -> int:
    """DUR-05: cancel each requested run's DBOS workflow, so no further step (model call or
    fetch) starts, then publish the run `cancelled`. A step already under way finishes and
    its attempt is settled as usual (a sent request may have been billed); its result is
    kept but the run stays cancelled. A run cancelled before dispatch is never started.
    Each is handled on its own: one that fails (logged by class, tried again next pass)
    never holds up the others or dispatch."""
    with system_transaction(engine) as tx:
        pending = run_store.pending_cancellations(tx)
    acted = 0
    for run_id, workflow_id, dispatched in pending:
        try:
            if dispatched:
                DBOS.cancel_workflow(workflow_id)
            activity.publish(runtime, run_id, activity.cancelled())
            with system_transaction(engine) as tx:
                run_store.mark_cancellation_signalled(tx, run_id)
        except Exception as error:
            _log.warning("cancellation failed", extra={"error_class": type(error).__name__})
            continue
        acted += 1
    return acted


def reconcile_errored_runs(runtime: ActivityRuntime) -> int:
    """A workflow that ended in DBOS ERROR (its outcome could not be published for longer
    than the publish retries allow) still leaves a typed terminal run, never a queued one,
    and a run whose output was accepted ends complete with it (`activity.reconcile`). Runs
    already terminal cost one lookup each: errored workflows are rare and never re-run."""
    errored = DBOS.list_workflows(
        status="ERROR",
        name=[
            run_store.MODEL_RUN_WORKFLOW,
            run_store.ACQUISITION_WORKFLOW,
            run_store.ROUTE_SOLVE_WORKFLOW,
        ],
        load_input=False,
        load_output=False,
    )
    return sum(
        activity.reconcile(runtime, uuid.UUID(status.workflow_id.removeprefix("careerwright-run-")))
        for status in errored
    )


def _heartbeat() -> None:
    HEARTBEAT_FILE.touch()


def check() -> int:
    try:
        age = time.time() - HEARTBEAT_FILE.stat().st_mtime
    except OSError:
        return 1
    return 0 if age < HEARTBEAT_STALE_S else 1


def loop_pass(
    engine: Engine,
    runtime: ActivityRuntime,
    *,
    next_reconcile: float,
    workflows: Workflows = MODEL_WORKFLOWS,
) -> float:
    """One pass of the worker loop; returns when reconciliation is next due. A failure is
    logged by class and the outbox retried next pass; reconciliation waits its interval even
    after a failed pass, so it never spins. Cancellations are acted on before dispatch."""
    try:
        act_on_cancellations(engine, runtime)
        dispatch_outbox(engine, workflows)
        if time.monotonic() >= next_reconcile:
            next_reconcile = time.monotonic() + RECONCILE_INTERVAL_S
            reconcile_errored_runs(runtime)
        _heartbeat()
    except Exception as error:
        _log.warning("worker pass failed", extra={"error_class": type(error).__name__})
    return next_reconcile


def run(
    engine: Engine,
    runtime: ActivityRuntime,
    system_database_url: str,
    workflows: Workflows = MODEL_WORKFLOWS,
) -> NoReturn:
    """Launch DBOS, loop until SIGTERM/SIGINT, then end the process within the deadline."""
    workflow.configure(runtime)
    DBOS(config=dbos_config(system_database_url))
    DBOS.launch()
    stop = threading.Event()
    watchdog = threading.Timer(SHUTDOWN_DEADLINE_S, os._exit, args=(EXIT_SHUTDOWN_TIMEOUT,))
    watchdog.daemon = True

    def request_stop(signum: int, frame: FrameType | None) -> None:
        if not stop.is_set():
            stop.set()
            watchdog.start()  # from the signal: a pass that never returns is bounded too

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    _log.info("worker ready", extra={"application_version": APPLICATION_VERSION})
    next_reconcile = 0.0
    while not stop.is_set():
        next_reconcile = loop_pass(
            engine, runtime, next_reconcile=next_reconcile, workflows=workflows
        )
        stop.wait(DISPATCH_INTERVAL_S)
    _log.info("worker stopping")
    DBOS.destroy()
    _log.info("worker stopped")
    # Never the interpreter's exit, which waits for every DBOS executor thread (module doc).
    logging.shutdown()
    os._exit(0)
