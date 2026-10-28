"""The DBOS workflow for model runs (ADR 0002): identifiers in, references and labels out.

The journal holds the run ID, the outcome (`{"status", "output_id"}` or
`{"status", "failure_class"}`) and label-only errors. The bounded activity step is the
only retry owner. When its retries run out, the run ends failed with the class of what was
unavailable (the provider, or the application database), never as an empty success. The
outcome is published by a step that keeps retrying through a database outage, so a run
reaches a typed terminal state once the database is back.
"""

import uuid

from dbos import DBOS
from dbos import error as dbos_error

from nessa.identity import activity
from nessa.identity.activity import ActivityRuntime, Outcome
from nessa.identity.failures import (
    AppStoreUnavailableError,
    LabelledError,
    TransientProviderError,
    classify_exhausted,
    classify_failure,
)

WORKFLOW_NAME = "nessa.model_run"
ACTIVITY_MAX_ATTEMPTS = 3
PUBLISH_MAX_ATTEMPTS = 12  # backoff 1 s doubling: about 34 minutes of outage
STORE_LABEL = "transient_store"

_runtime: ActivityRuntime | None = None


def configure(runtime: ActivityRuntime) -> None:
    global _runtime
    _runtime = runtime


def _rt() -> ActivityRuntime:
    if _runtime is None:
        raise RuntimeError("workflow runtime is not configured")
    return _runtime


def _is_transient(error: BaseException) -> bool:
    return isinstance(error, TransientProviderError | AppStoreUnavailableError)


@DBOS.step(
    name="nessa.bounded_model_activity",
    retries_allowed=True,
    max_attempts=ACTIVITY_MAX_ATTEMPTS,
    interval_seconds=1.0,
    backoff_rate=2.0,
    should_retry=_is_transient,
)
def bounded_model_activity(run_id: str) -> Outcome:
    end = activity.execute(_rt(), uuid.UUID(run_id))
    if end.outcome is not None:
        return end.outcome
    # Raised outside any handler: the exception carries a label and nothing else.
    if end.label == STORE_LABEL:
        raise AppStoreUnavailableError()
    raise TransientProviderError(end.label)


@DBOS.step(
    name="nessa.publish_outcome",
    retries_allowed=True,
    max_attempts=PUBLISH_MAX_ATTEMPTS,
    interval_seconds=1.0,
    backoff_rate=2.0,
)
def publish_outcome(run_id: str, outcome: Outcome) -> None:
    try:
        activity.publish(_rt(), uuid.UUID(run_id), outcome)
    except Exception as error:
        label: str | None = classify_failure(error).label
    else:
        label = None
    if label is not None:
        raise LabelledError(label)


@DBOS.workflow(name=WORKFLOW_NAME)
def model_run_workflow(run_id: str) -> Outcome:
    try:
        outcome = bounded_model_activity(run_id)
    except dbos_error.DBOSMaxStepRetriesExceeded as exhausted:
        outcome = activity.failed(classify_exhausted(exhausted.errors))
    publish_outcome(run_id, outcome)
    return outcome
