"""The DBOS workflow for acquisition runs (adapter; ADR 0002, ADR 0009): identifiers in,
labels out.

One step per target, then one to publish. The journal holds the run ID, target positions,
`{"status", "attempt_id"}` outcomes and label-only errors; never a URL, a page or a
credential. DBOS owns the bounded retries of a target (spec section 6: "DBOS owns bounded
fetch retries"): a transient source failure, the acquisition worker unreachable or the
database busy is retried by the step, at most three tries; every try is its own attempt
row naming the one it repeats. Completed steps are not repeated after a crash, so a resumed
run carries on from its next target with its earlier results kept. Cancellation (the
worker loop's `DBOS.cancel_workflow`) stops it before its next step.
"""

import contextlib
import uuid

from dbos import DBOS
from dbos import error as dbos_error

from nessa.db import StoreUnavailableError
from nessa.evidence import acquisition
from nessa.evidence.acquisition import AcquisitionRuntime, TransientAcquisitionError
from nessa.identity import run_store
from nessa.identity.failures import LabelledError

WORKFLOW_NAME = run_store.ACQUISITION_WORKFLOW
TARGET_MAX_ATTEMPTS = 3
TARGET_INTERVAL_S = 2.0
TARGET_BACKOFF_RATE = 2.0
PUBLISH_MAX_ATTEMPTS = 12

_runtime: AcquisitionRuntime | None = None


def configure(runtime: AcquisitionRuntime) -> None:
    global _runtime
    _runtime = runtime


def _rt() -> AcquisitionRuntime:
    if _runtime is None:
        raise RuntimeError("acquisition runtime is not configured")
    return _runtime


def _is_transient(error: BaseException) -> bool:
    return isinstance(error, TransientAcquisitionError)


@DBOS.step(
    name="nessa.acquisition_targets", retries_allowed=True, max_attempts=PUBLISH_MAX_ATTEMPTS
)
def target_positions(run_id: str) -> list[int]:
    return acquisition.target_positions(_rt(), uuid.UUID(run_id))


@DBOS.step(
    name="nessa.acquire_target",
    retries_allowed=True,
    max_attempts=TARGET_MAX_ATTEMPTS,
    interval_seconds=TARGET_INTERVAL_S,
    backoff_rate=TARGET_BACKOFF_RATE,
    should_retry=_is_transient,
)
def acquire_target(run_id: str, position: int) -> dict[str, str]:
    try:
        return acquisition.acquire_target(_rt(), uuid.UUID(run_id), position)
    except TransientAcquisitionError as error:
        label: str = error.label
        transient = True
    except StoreUnavailableError:
        label, transient = "transient_store", True
    except Exception as error:
        label, transient = f"unknown_failure:{type(error).__name__}", False
    # Raised outside any handler: the exception carries a label and nothing else.
    if transient:
        raise TransientAcquisitionError(label)
    raise LabelledError(label)


@DBOS.step(
    name="nessa.publish_acquisition",
    retries_allowed=True,
    max_attempts=PUBLISH_MAX_ATTEMPTS,
    interval_seconds=1.0,
    backoff_rate=2.0,
)
def publish_acquisition(run_id: str) -> None:
    try:
        acquisition.publish_acquisition(_rt(), uuid.UUID(run_id))
    except Exception as error:
        label: str | None = type(error).__name__
    else:
        label = None
    if label is not None:
        raise LabelledError(label)


@DBOS.workflow(name=WORKFLOW_NAME)
def acquisition_workflow(run_id: str) -> None:
    for position in target_positions(run_id):
        # A target whose tries are spent: its last attempt records why; the run goes on.
        with contextlib.suppress(dbos_error.DBOSMaxStepRetriesExceeded, LabelledError):
            acquire_target(run_id, position)
    publish_acquisition(run_id)
