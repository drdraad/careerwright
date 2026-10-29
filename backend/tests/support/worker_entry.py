"""The real worker loop with a fake model and optional crash points, as a separate process.

Configured by environment only, like the product worker. Crash points are a real SIGKILL at
a named moment, so DBOS recovery is exercised rather than simulated:
- `after_settle`: the attempt's result (an accepted output, or a terminal failure) and its
  usage are committed, the DBOS step is not;
- `after_dispatch_before_mark`: the workflow started, its outbox entry not yet marked;
- `after_first_partial`: the first piece of a streamed reply is committed, mid-call.
- `after_acquired_target`: an acquisition target's result is committed, its step is not.

The acquisition worker it calls is `NESSA_ACQUISITION_URL` (a test-started one).
"""

import os
import signal
import uuid
from datetime import UTC, datetime
from pathlib import Path

from nessa.config import WorkerSettings
from nessa.db import create_engine, url_with_password
from nessa.evidence import acquisition
from nessa.evidence import workflow as acquisition_workflow
from nessa.evidence.acquisition import AcquisitionRuntime
from nessa.evidence.service_client import HttpAcquisitionClient
from nessa.identity import activity, run_store, worker
from nessa.identity.activity import ActivityRuntime
from nessa.identity.keyring import load_keyring
from nessa.identity.records import Run
from nessa.logs import configure_logging
from nessa.worker import TASKS, WORKFLOWS, model_builder
from tests.support.fake_models import FakeFailure, fake_model_builder


def _kill() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


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
    elif point:
        raise ValueError(f"unknown crash point {point!r}")


def main() -> None:
    configure_logging("test-worker")
    settings = WorkerSettings()
    failure = os.environ.get("NESSA_TEST_FAKE_FAILURE")
    runtime = ActivityRuntime(
        engine=create_engine(settings.app_database, application_name="test-worker"),
        keyring=load_keyring(settings.master_key_dir),
        # The product builder (the real fixture interviewer for demo workspaces), with the
        # fake in place of Meta.
        build_model=model_builder(
            fake_model_builder(
                delay_s=float(os.environ.get("NESSA_TEST_FAKE_DELAY_S", "0")),
                failure=FakeFailure(failure) if failure else None,
                output_sentinel=os.environ.get("NESSA_TEST_OUTPUT_SENTINEL", ""),
                call_log=Path(log) if (log := os.environ.get("NESSA_TEST_CALL_LOG")) else None,
            )
        ),
        clock=lambda: datetime.now(UTC),
        tasks=TASKS,
        store_retry_budget_s=float(
            os.environ.get("NESSA_TEST_STORE_RETRY_BUDGET_S", activity.STORE_RETRY_BUDGET_S)
        ),
    )
    install_crash_point(os.environ.get("NESSA_TEST_CRASH_AT", ""))
    acquisition_workflow.configure(
        AcquisitionRuntime(runtime, HttpAcquisitionClient(settings.acquisition_url))
    )
    worker.run(runtime.engine, runtime, url_with_password(settings.dbos_database), WORKFLOWS)


if __name__ == "__main__":
    main()
