"""Workspace commands: create and rename, with expected-version writes and status events."""

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from nessa.db import Tx
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity import store
from nessa.identity.access import Actor, workspace_not_found
from nessa.identity.records import EventKind, Workspace
from nessa.vocabulary import DataMode

WorkspaceName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]


class CreateWorkspace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: WorkspaceName
    data_mode: DataMode
    synthetic: bool


def create_workspace(tx: Tx, actor: Actor, command: CreateWorkspace) -> Workspace:
    if command.data_mode is DataMode.LIVE_VACANCY:
        raise NessaError(
            ErrorCode.MODE_NOT_SUPPORTED,
            "Live-vacancy mode needs separately qualified Adzuna credentials, which are not "
            "configured. Use live-assisted mode.",
            stage=ErrorStage.WORKSPACE,
        )
    if command.data_mode is DataMode.DEMO and not command.synthetic:
        raise NessaError(
            ErrorCode.VALIDATION_FAILED,
            "A demo workspace always holds synthetic data.",
            stage=ErrorStage.WORKSPACE,
            details={"field": "synthetic", "reason": "demo_is_synthetic"},
        )
    workspace = store.insert_workspace(
        tx,
        workspace_id=uuid.uuid4(),
        owner_actor_id=actor.actor_id,
        name=command.name,
        data_mode=command.data_mode,
        synthetic=command.synthetic,
    )
    store.append_event(
        tx, workspace.workspace_id, EventKind.WORKSPACE_CREATED, str(workspace.workspace_id)
    )
    return workspace


def stale_workspace(current: int) -> NessaError:
    return NessaError(
        ErrorCode.STALE_INPUT_VERSION,
        "The workspace changed since you loaded it. Reload, then try again.",
        stage=ErrorStage.WORKSPACE,
        details={"current_version": current},
    )


def rename_workspace(
    tx: Tx, workspace_id: uuid.UUID, expected_version: int, name: str
) -> Workspace:
    current = store.get_workspace(tx, workspace_id, lock=True)
    if current is None:
        raise workspace_not_found()
    if current.version != expected_version:
        raise stale_workspace(current.version)
    renamed = store.rename_workspace(tx, workspace_id, expected_version, name)
    if renamed is None:  # cannot happen under the row lock; never report a silent success
        raise stale_workspace(current.version)
    store.append_event(
        tx,
        workspace_id,
        EventKind.WORKSPACE_UPDATED,
        str(workspace_id),
        detail={"version": renamed.version},
    )
    return renamed


def visible_workspace(tx: Tx, workspace_id: uuid.UUID, *, lock: bool = False) -> Workspace:
    workspace = store.get_workspace(tx, workspace_id, lock=lock)
    if workspace is None:
        raise workspace_not_found()
    return workspace
