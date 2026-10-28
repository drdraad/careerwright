"""Run commands: submit a run (202 + run ID) through the transactional outbox, and read it.

Submission records the run, its pinned model, the workspace's data mode and synthetic label,
and the outbox entry in one transaction. It refuses early what the worker would refuse
anyway (demo runtime or workspace, no key, the Contributor model on non-synthetic data, a
call that cannot fit the spend limits), but the worker re-checks everything before the
call, because keys, access and budgets can change while a run is queued.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from nessa.config import RuntimeMode
from nessa.db import Tx
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity import connection_check, credential_store, run_store, store
from nessa.identity.access import Actor
from nessa.identity.keyring import Keyring, RecordContext
from nessa.identity.model_choice import ModelChoice, assert_model_permitted
from nessa.identity.records import EventKind, Run, RunKind
from nessa.identity.spend import SpendLimits, budget_exceeded, period_start, refused_scope
from nessa.identity.workspaces import visible_workspace
from nessa.vocabulary import DataMode, WorkState

OUTPUT_KIND = "run_output"


class SubmitRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: RunKind


def workflow_id(run_id: uuid.UUID) -> str:
    return f"nessa-run-{run_id}"


def output_context(workspace_id: uuid.UUID, output_id: uuid.UUID) -> RecordContext:
    return RecordContext(OUTPUT_KIND, str(workspace_id), str(output_id))


def submit_run(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: SubmitRun,
    *,
    models: ModelChoice,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
) -> Run:
    workspace = visible_workspace(tx, workspace_id, lock=True)
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
    model = models.for_workspace(synthetic=workspace.synthetic)
    assert_model_permitted(model, synthetic=workspace.synthetic)
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
        worst_case=connection_check.worst_case_nano_usd(model.model_id),
    )
    if scope is not None:
        raise budget_exceeded(scope)
    run = Run(
        run_id=uuid.uuid4(),
        workspace_id=workspace_id,
        kind=command.kind,
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
    )
    run_store.insert_run(tx, run, workflow_id(run.run_id))
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


def visible_run(tx: Tx, workspace_id: uuid.UUID, run_id: uuid.UUID) -> Run:
    visible_workspace(tx, workspace_id)
    found = run_store.run(tx, run_id)
    if found is None or found.workspace_id != workspace_id:
        raise NessaError(ErrorCode.NOT_FOUND, "No such run.", stage=ErrorStage.EXECUTION)
    return found


def open_output(
    tx: Tx, keyring: Keyring, run: Run
) -> connection_check.ConnectionCheckResult | None:
    sealed = run_store.sealed_output(tx, run.run_id)
    if sealed is None:
        return None
    output_id, value = sealed
    plaintext = keyring.open(value, output_context(run.workspace_id, output_id))
    return connection_check.ConnectionCheckResult.model_validate_json(plaintext)
