"""Durable worker process: launches DBOS (which recovers pending workflows) and drains the outbox.

Configuration arrives through the environment only (database URLs carry passwords and the
master key is a file path), never through command arguments. The worker never receives the
Meta key: the activity reads it from the sealed credential store just in time.
"""

import os
import signal
import threading
from pathlib import Path
from types import FrameType

from dbos import DBOS, DBOSConfig, DBOSPortableJSONSerializer, SetWorkflowID

from spikes.durable import workflow
from spikes.durable.models import (
    FAKE_MODEL_ID,
    FakeFailure,
    ModelBuilder,
    fake_model_builder,
    meta_model_builder,
)
from spikes.durable.sealing import Keyring
from spikes.durable.store import AppStore

APP_NAME = "nessa-spike"
# Pinned so a restarted worker recovers workflows recorded by the killed one.
APPLICATION_VERSION = "nessa-spike-1"
DISPATCH_INTERVAL_S = 0.1


def dbos_config(system_database_url: str) -> DBOSConfig:
    return {
        "name": APP_NAME,
        "system_database_url": system_database_url,
        "application_version": APPLICATION_VERSION,
        # JSON journal: only plain values can be journalled, and it is inspectable without
        # unpickling database content.
        "serializer": DBOSPortableJSONSerializer(),
    }


def keyring_from_file(path: Path) -> Keyring:
    return Keyring({1: path.read_bytes()}, current_version=1)


def dispatch_outbox(store: AppStore, crash_point: str | None) -> None:
    for entry in store.pending_outbox():
        # The workflow ID is the idempotency key: replaying an entry that was started but
        # not marked dispatched returns the existing workflow instead of starting another.
        with SetWorkflowID(entry.workflow_id):
            DBOS.start_workflow(workflow.profile_run_workflow, entry.run_id)
        if crash_point == "after_dispatch_before_mark":
            os.kill(os.getpid(), signal.SIGKILL)
        store.mark_dispatched(entry.outbox_id)


def _model_builder(model_id: str) -> ModelBuilder:
    if model_id != FAKE_MODEL_ID:
        return meta_model_builder(model_id)
    failure = os.environ.get("NESSA_SPIKE_FAKE_FAILURE")
    return fake_model_builder(
        delay_s=float(os.environ.get("NESSA_SPIKE_FAKE_DELAY_S", "0")),
        failure=FakeFailure(failure) if failure else None,
    )


def main() -> None:
    crash_point = os.environ.get("NESSA_SPIKE_CRASH_AT") or None
    model_id = os.environ.get("NESSA_SPIKE_ACTIVITY_MODEL", FAKE_MODEL_ID)
    store = AppStore(
        os.environ["NESSA_SPIKE_APP_URL"],
        keyring_from_file(Path(os.environ["NESSA_SPIKE_MASTER_KEY_FILE"])),
    )
    workflow.configure(
        workflow.ActivityRuntime(
            store=store,
            model_id=model_id,
            build_model=_model_builder(model_id),
            crash_point=crash_point,
        )
    )
    DBOS(config=dbos_config(os.environ["NESSA_SPIKE_DBOS_URL"]))
    DBOS.launch()

    stop = threading.Event()

    def request_stop(signum: int, frame: FrameType | None) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    print("worker ready", flush=True)
    while not stop.is_set():
        dispatch_outbox(store, crash_point)
        stop.wait(DISPATCH_INTERVAL_S)
    DBOS.destroy()


if __name__ == "__main__":
    main()
