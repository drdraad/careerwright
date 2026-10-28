"""The real worker loop with a fake model and optional crash points, as a separate process.

Configured by environment only, like the product worker. Crash points are a real SIGKILL at
a named moment, so DBOS recovery is exercised rather than simulated:
- `after_output_accepted`: the output and usage are committed, the DBOS step is not;
- `after_dispatch_before_mark`: the workflow started, its outbox entry not yet marked.
"""

import os
import signal
from datetime import UTC, datetime

from nessa.config import WorkerSettings
from nessa.db import create_engine, url_with_password
from nessa.identity import activity, run_store, worker
from nessa.identity.activity import ActivityRuntime
from nessa.identity.keyring import load_keyring
from nessa.logs import configure_logging
from tests.support.fake_models import FakeFailure, fake_model_builder


def _kill() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


def install_crash_point(point: str) -> None:
    if point == "after_output_accepted":
        settle = activity._settle

        def settle_then_die(*args: object) -> activity.ActivityEnd:
            settle(*args)  # type: ignore[arg-type]
            _kill()
            raise AssertionError("unreachable")

        activity._settle = settle_then_die  # type: ignore[assignment]
    elif point == "after_dispatch_before_mark":
        run_store.mark_dispatched = lambda tx, outbox_id: _kill()
    elif point:
        raise ValueError(f"unknown crash point {point!r}")


def main() -> None:
    configure_logging("test-worker")
    settings = WorkerSettings()
    failure = os.environ.get("NESSA_TEST_FAKE_FAILURE")
    runtime = ActivityRuntime(
        engine=create_engine(settings.app_database, application_name="test-worker"),
        keyring=load_keyring(settings.master_key_dir),
        build_model=fake_model_builder(
            delay_s=float(os.environ.get("NESSA_TEST_FAKE_DELAY_S", "0")),
            failure=FakeFailure(failure) if failure else None,
            output_sentinel=os.environ.get("NESSA_TEST_OUTPUT_SENTINEL", ""),
        ),
        clock=lambda: datetime.now(UTC),
    )
    install_crash_point(os.environ.get("NESSA_TEST_CRASH_AT", ""))
    worker.run(runtime.engine, runtime, url_with_password(settings.dbos_database))


if __name__ == "__main__":
    main()
