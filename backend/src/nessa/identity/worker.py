"""The DBOS worker process: recovers pending workflows, drains the outbox, reports health.

Configuration comes from the environment and files only. The worker never receives a Meta
key from its environment: the activity opens the workspace's sealed key just in time.
Shutdown is bounded: after SIGTERM the loop stops, DBOS is destroyed without waiting for
workflows, and a watchdog exits the process if that ever hangs (Sprint 0 saw one unexplained
hang in 19 runs). DBOS recovers whatever was in flight on the next start.

Run: `python -m nessa.identity.worker`; health check: `python -m nessa.identity.worker --check`.
"""

import logging
import os
import signal
import sys
import threading
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType

from dbos import DBOS, DBOSConfig, DBOSPortableJSONSerializer, SetWorkflowID
from pydantic import SecretStr
from pydantic_ai.models import Model

from nessa.config import WorkerSettings
from nessa.db import Engine, create_engine, system_transaction, url_with_password
from nessa.identity import activity, connection_check, run_store, workflow
from nessa.identity.activity import ActivityRuntime
from nessa.identity.keyring import load_keyring
from nessa.identity.meta import meta_model
from nessa.identity.model_choice import ModelChoice
from nessa.logs import configure_logging

APP_NAME = "nessa"
# Pinned: DBOS recovers only workflows of the same version. Changing the workflow's step
# sequence needs a new version and a drain of in-flight runs (ADR 0002 decision 9).
APPLICATION_VERSION = "nessa-l0-1"
DISPATCH_INTERVAL_S = 0.2
RECONCILE_INTERVAL_S = 60.0
SHUTDOWN_DEADLINE_S = 10.0
HEARTBEAT_FILE = Path(os.environ.get("NESSA_WORKER_HEARTBEAT", "/tmp/nessa-worker-heartbeat"))  # noqa: S108
HEARTBEAT_STALE_S = 15.0
EXIT_SHUTDOWN_TIMEOUT = 75
_log = logging.getLogger("nessa.worker")


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


def dispatch_outbox(engine: Engine) -> int:
    with system_transaction(engine) as tx:
        entries = run_store.pending_outbox(tx)
    for outbox_id, workflow_id, run_id in entries:
        # The workflow ID is the idempotency key: replaying an entry that was started but not
        # marked dispatched returns the existing workflow instead of starting another.
        with SetWorkflowID(workflow_id):
            DBOS.start_workflow(workflow.model_run_workflow, str(run_id))
        with system_transaction(engine) as tx:
            run_store.mark_dispatched(tx, outbox_id)
    return len(entries)


def reconcile_errored_runs(runtime: ActivityRuntime) -> int:
    """A workflow that ended in DBOS ERROR (its outcome could not be published for longer
    than the publish retries allow) still leaves a typed terminal run, never a queued one,
    and a run whose output was accepted ends complete with it (`activity.reconcile`). Runs
    already terminal cost one lookup each: errored workflows are rare and never re-run."""
    errored = DBOS.list_workflows(
        status="ERROR", name=workflow.WORKFLOW_NAME, load_input=False, load_output=False
    )
    return sum(
        activity.reconcile(runtime, uuid.UUID(status.workflow_id.removeprefix("nessa-run-")))
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


def loop_pass(engine: Engine, runtime: ActivityRuntime, *, next_reconcile: float) -> float:
    """One pass of the worker loop; returns when reconciliation is next due. A failure is
    logged by class and the outbox retried next pass; reconciliation waits its interval even
    after a failed pass, so it never spins."""
    try:
        dispatch_outbox(engine)
        if time.monotonic() >= next_reconcile:
            next_reconcile = time.monotonic() + RECONCILE_INTERVAL_S
            reconcile_errored_runs(runtime)
        _heartbeat()
    except Exception as error:
        _log.warning("worker pass failed", extra={"error_class": type(error).__name__})
    return next_reconcile


def run(engine: Engine, runtime: ActivityRuntime, system_database_url: str) -> None:
    """Launch DBOS, loop until SIGTERM/SIGINT, then shut down within the deadline."""
    workflow.configure(runtime)
    DBOS(config=dbos_config(system_database_url))
    DBOS.launch()
    stop = threading.Event()

    def request_stop(signum: int, frame: FrameType | None) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    _log.info("worker ready", extra={"application_version": APPLICATION_VERSION})
    next_reconcile = 0.0
    while not stop.is_set():
        next_reconcile = loop_pass(engine, runtime, next_reconcile=next_reconcile)
        stop.wait(DISPATCH_INTERVAL_S)
    _log.info("worker stopping")
    watchdog = threading.Timer(SHUTDOWN_DEADLINE_S, os._exit, args=(EXIT_SHUTDOWN_TIMEOUT,))
    watchdog.daemon = True
    watchdog.start()
    DBOS.destroy()
    watchdog.cancel()
    _log.info("worker stopped")


def meta_model_builder() -> Callable[[str, SecretStr], Model]:
    def build(model_id: str, api_key: SecretStr) -> Model:
        return meta_model(
            model_id,
            api_key,
            max_output_tokens=connection_check.LIMITS.max_output_tokens,
            effort="minimal",
        )

    return build


def _utc_now() -> datetime:
    return datetime.now(UTC)


def main() -> None:
    if sys.argv[1:] == ["--check"]:
        sys.exit(check())
    configure_logging("worker")
    settings = WorkerSettings()
    # Fail closed on an unusable model configuration before any work is accepted.
    ModelChoice.configure(
        settings.meta_test_model, settings.meta_production_model, settings.synthetic_model_role
    )
    engine = create_engine(settings.app_database, application_name="nessa-worker")
    runtime = ActivityRuntime(
        engine=engine,
        keyring=load_keyring(settings.master_key_dir),
        build_model=meta_model_builder(),
        clock=_utc_now,
    )
    run(engine, runtime, url_with_password(settings.dbos_database))


if __name__ == "__main__":
    main()
