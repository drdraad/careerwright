"""Run commands: submit a run (202 + run ID) through the transactional outbox, and read it.

Submission records the run, its pinned model, the workspace's data mode and synthetic label,
the profile version it read (if any), its sealed input (if any) and the outbox entry in one
transaction. It refuses early what the worker would refuse anyway (demo runtime, no key,
the Contributor model on non-synthetic data, a call that cannot fit the spend limits), but
the worker re-checks everything before the call, because keys, access and budgets can
change while a run is queued.

A demo workspace never reaches a provider: its interview turns, discoveries and slate
explanations use the fixture models (no key, no spend, no network), and every other kind is
refused.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from nessa.config import RuntimeMode
from nessa.db import Tx
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity import connection_check, credential_store, run_store, store
from nessa.identity.access import Actor
from nessa.identity.keyring import Keyring, RecordContext
from nessa.identity.model_choice import ModelChoice, assert_model_permitted, fixture_model
from nessa.identity.model_registry import ModelEntry
from nessa.identity.records import (
    KEYLESS_KINDS,
    EventKind,
    PartialCompleteness,
    PartialReply,
    Run,
    RunKind,
)
from nessa.identity.spend import SpendLimits, budget_exceeded, period_start, refused_scope
from nessa.identity.workspaces import visible_workspace
from nessa.vocabulary import DataMode, WorkState

OUTPUT_KIND = "run_output"
INPUT_KIND = "run_input"
PARTIAL_KIND = "run_partial"


class SubmitRun(BaseModel):
    """`POST /runs` starts the runs that need no input; interview turns have their own
    endpoint, which records the person's message with the run."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal[RunKind.CONNECTION_CHECK]


@dataclass(frozen=True)
class RunRequest:
    kind: RunKind
    worst_case_nano_usd: Callable[[str], int]  # one attempt, for a model ID
    profile_version: int | None = None  # the profile version the run reads, pinned
    input: bytes | None = None  # sealed into the run; opened only by the worker's activity


def connection_check_request() -> RunRequest:
    return RunRequest(RunKind.CONNECTION_CHECK, connection_check.worst_case_nano_usd)


def workflow_id(run_id: uuid.UUID) -> str:
    return f"nessa-run-{run_id}"


def output_context(workspace_id: uuid.UUID, output_id: uuid.UUID) -> RecordContext:
    return RecordContext(OUTPUT_KIND, str(workspace_id), str(output_id))


def input_context(workspace_id: uuid.UUID, run_id: uuid.UUID) -> RecordContext:
    return RecordContext(INPUT_KIND, str(workspace_id), str(run_id))


def partial_context(workspace_id: uuid.UUID, run_id: uuid.UUID) -> RecordContext:
    return RecordContext(PARTIAL_KIND, str(workspace_id), str(run_id))


def record_partial(
    tx: Tx, keyring: Keyring, run: Run, text: str, completeness: PartialCompleteness
) -> None:
    """Worker: the streamed reply so far, sealed, and a status event that carries the run ID
    and the partial's sequence only."""
    sealed = keyring.seal(text.encode(), partial_context(run.workspace_id, run.run_id))
    seq = run_store.upsert_partial(tx, run, sealed, completeness)
    store.append_event(
        tx, run.workspace_id, EventKind.RUN_PARTIAL_UPDATED, str(run.run_id), detail={"seq": seq}
    )


def end_partial(tx: Tx, keyring: Keyring, run: Run, latest: str | None) -> None:
    """Worker: the attempt or run failed, so this streamed reply has stopped. `latest` is
    the reply so far, if the attempt streamed any (it may be newer than the last write).
    Whether it is final is the run's state (`partial_reply`)."""
    if latest is not None:
        record_partial(tx, keyring, run, latest, PartialCompleteness.STOPPED)
        return
    seq = run_store.mark_partial_stopped(tx, run.run_id)
    if seq is not None:
        store.append_event(
            tx,
            run.workspace_id,
            EventKind.RUN_PARTIAL_UPDATED,
            str(run.run_id),
            detail={"seq": seq},
        )


_FAILED = frozenset({WorkState.FAILED, WorkState.PROVIDER_UNAVAILABLE, WorkState.CANCELLED})


_SUPERSEDED = PartialReply(None, PartialCompleteness.SUPERSEDED, None, None)


def partial_reply(tx: Tx, keyring: Keyring, run: Run) -> PartialReply:
    """The run's streamed reply for its owner: never validated and never a result. Once a
    validated output is stored only it counts, so no partial text is returned.

    The run, the partial and the output are read by separate statements. The worker deletes
    the partial in the transaction that stores the output, and publishes the run complete
    later, so a partial found missing is checked against the output last: a stored output
    answers `superseded`, never `none`."""
    if run.status is WorkState.COMPLETE:
        return _SUPERSEDED
    found = run_store.partial(tx, run.run_id)
    if found is None:
        if run_store.accepted_output(tx, run.run_id) is not None:
            return _SUPERSEDED
        return PartialReply(None, PartialCompleteness.NONE, None, None)
    seq, stored, sealed, updated_at = found
    # Final once the run has failed, whatever the worker last recorded (even after a crash);
    # otherwise streaming, or stopped while the run goes on.
    completeness = PartialCompleteness.INCOMPLETE if run.status in _FAILED else stored
    text = keyring.open(sealed, partial_context(run.workspace_id, run.run_id)).decode()
    return PartialReply(seq, completeness, text, updated_at)


def _provider_model(
    tx: Tx,
    workspace_id: uuid.UUID,
    synthetic: bool,
    request: RunRequest,
    *,
    models: ModelChoice,
    defaults: SpendLimits,
    now: datetime,
) -> ModelEntry:
    model = models.for_workspace(synthetic=synthetic)
    assert_model_permitted(model, synthetic=synthetic)
    if not any(c.revoked_at is None for c in credential_store.credentials(tx, workspace_id)):
        raise NessaError(
            ErrorCode.CREDENTIAL_REQUIRED,
            "Store a Meta API key for this workspace first.",
            stage=ErrorStage.CREDENTIAL,
        )
    stored = credential_store.spend_limits(tx, workspace_id)
    limits = stored[0] if stored else defaults
    committed, _ = run_store.period_spend(tx, workspace_id, period_start(now))
    scope = refused_scope(
        limits,
        period_committed=committed,
        run_committed=0,
        worst_case=request.worst_case_nano_usd(model.model_id),
    )
    if scope is not None:
        raise budget_exceeded(scope)
    return model


def submit_run(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    request: RunRequest,
    *,
    models: ModelChoice,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
) -> Run:
    workspace = visible_workspace(tx, workspace_id, lock=True)
    stand_in = fixture_model(request.kind) if workspace.data_mode is DataMode.DEMO else None
    if stand_in is None:
        if runtime_mode is RuntimeMode.DEMO:
            raise NessaError(
                ErrorCode.MODEL_UNAVAILABLE,
                "Nessa is running in offline demo mode, so no model calls are made.",
                stage=ErrorStage.EXECUTION,
            )
        if workspace.data_mode is DataMode.DEMO:
            raise NessaError(
                ErrorCode.MODE_NOT_SUPPORTED,
                "Demo workspaces run on fixtures only and never call a model.",
                stage=ErrorStage.EXECUTION,
            )
    model = (
        stand_in
        if stand_in is not None
        else _provider_model(
            tx,
            workspace_id,
            workspace.synthetic,
            request,
            models=models,
            defaults=defaults,
            now=now,
        )
    )
    run = Run(
        run_id=uuid.uuid4(),
        workspace_id=workspace_id,
        kind=request.kind,
        data_mode=workspace.data_mode,
        synthetic=workspace.synthetic,
        requested_by=actor.actor_id,
        model_id=model.model_id,
        model_mode=model.mode.value,
        status=WorkState.QUEUED,
        failure_class=None,
        output_id=None,
        created_at=now,
        started_at=None,
        finished_at=None,
        profile_version=request.profile_version,
    )
    sealed = (
        None
        if request.input is None
        else keyring.seal(request.input, input_context(workspace_id, run.run_id))
    )
    run_store.insert_run(tx, run, workflow_id(run.run_id), sealed)
    store.append_event(
        tx,
        workspace_id,
        EventKind.RUN_STATE_CHANGED,
        str(run.run_id),
        state=WorkState.QUEUED,
        detail={"kind": run.kind.value},
    )
    stored_run = run_store.run(tx, run.run_id)
    if stored_run is None:  # the insert is in this transaction; never report a phantom run
        raise NessaError(
            ErrorCode.INTERNAL_ERROR, "The run was not recorded.", stage=ErrorStage.EXECUTION
        )
    return stored_run


def submit_keyless_run(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    kind: RunKind,
    *,
    runtime_mode: RuntimeMode,
    workflow_name: str,
    now: datetime,
) -> Run:
    """A run that calls no model (`KEYLESS_KINDS`): no key, model or spend, but the same
    run record, outbox, events and cancellation as every other run. It needs a route out of
    the machine, so the demo runtime and demo workspaces refuse it."""
    if kind not in KEYLESS_KINDS:
        raise ValueError(f"{kind} calls a model")
    workspace = visible_workspace(tx, workspace_id, lock=True)
    if runtime_mode is RuntimeMode.DEMO or workspace.data_mode is DataMode.DEMO:
        raise NessaError(
            ErrorCode.MODE_NOT_SUPPORTED,
            "Demo workspaces and the offline demo never fetch sources.",
            stage=ErrorStage.EXECUTION,
        )
    run = Run(
        run_id=uuid.uuid4(),
        workspace_id=workspace_id,
        kind=kind,
        data_mode=workspace.data_mode,
        synthetic=workspace.synthetic,
        requested_by=actor.actor_id,
        model_id=None,
        model_mode=None,
        status=WorkState.QUEUED,
        failure_class=None,
        output_id=None,
        created_at=now,
        started_at=None,
        finished_at=None,
    )
    run_store.insert_run(tx, run, workflow_id(run.run_id), None, workflow_name=workflow_name)
    store.append_event(
        tx,
        workspace_id,
        EventKind.RUN_STATE_CHANGED,
        str(run.run_id),
        state=WorkState.QUEUED,
        detail={"kind": run.kind.value},
    )
    stored_run = run_store.run(tx, run.run_id)
    if stored_run is None:
        raise NessaError(
            ErrorCode.INTERNAL_ERROR, "The run was not recorded.", stage=ErrorStage.EXECUTION
        )
    return stored_run


_TERMINAL = frozenset(
    {WorkState.COMPLETE, WorkState.FAILED, WorkState.PROVIDER_UNAVAILABLE, WorkState.CANCELLED}
)


def cancel_run(tx: Tx, actor: Actor, workspace_id: uuid.UUID, run_id: uuid.UUID) -> Run:
    """Ask for a queued or running run to stop (DUR-05). The worker cancels its workflow, so
    nothing more is called or fetched for it, and publishes it `cancelled`, distinct from a
    failure; what it already finished is kept. A run that has finished cannot be cancelled.
    The run ID is the precondition (like revoking a key); asking twice changes nothing."""
    visible_workspace(tx, workspace_id, lock=True)
    # Not locked: the API may not lock runs. If the worker finishes the run meanwhile, the
    # request changes nothing (publication records a terminal state once).
    run = run_store.run(tx, run_id)
    if run is None or run.workspace_id != workspace_id:
        raise NessaError(ErrorCode.NOT_FOUND, "No such run.", stage=ErrorStage.EXECUTION)
    if run.status in _TERMINAL:
        raise NessaError(
            ErrorCode.RUN_FINISHED,
            "This run has already finished, so there is nothing to cancel.",
            stage=ErrorStage.EXECUTION,
            details={"status": run.status.value},
        )
    if run_store.request_cancellation(tx, run, actor.actor_id):
        store.append_event(tx, workspace_id, EventKind.RUN_CANCEL_REQUESTED, str(run_id))
    cancelled = run_store.run(tx, run_id)
    if cancelled is None:
        raise NessaError(
            ErrorCode.INTERNAL_ERROR, "The run was not recorded.", stage=ErrorStage.EXECUTION
        )
    return cancelled


def visible_run(tx: Tx, workspace_id: uuid.UUID, run_id: uuid.UUID) -> Run:
    visible_workspace(tx, workspace_id)
    found = run_store.run(tx, run_id)
    if found is None or found.workspace_id != workspace_id:
        raise NessaError(ErrorCode.NOT_FOUND, "No such run.", stage=ErrorStage.EXECUTION)
    return found


def open_output(tx: Tx, keyring: Keyring, run: Run) -> bytes | None:
    """The run's accepted output (its validated JSON), or None if it has none."""
    sealed = run_store.sealed_output(tx, run.run_id)
    if sealed is None:
        return None
    output_id, value = sealed
    return keyring.open(value, output_context(run.workspace_id, output_id))


def connection_check_output(
    tx: Tx, keyring: Keyring, run: Run
) -> connection_check.ConnectionCheckResult | None:
    """A complete connection check's output only: a run settled but not yet published, or
    cancelled, shows none (its result is not used)."""
    if run.kind is not RunKind.CONNECTION_CHECK or run.status is not WorkState.COMPLETE:
        return None
    plaintext = open_output(tx, keyring, run)
    if plaintext is None:
        return None
    return connection_check.ConnectionCheckResult.model_validate_json(plaintext)
