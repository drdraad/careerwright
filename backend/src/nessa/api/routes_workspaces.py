"""Identity and workspace endpoints. Writes are idempotent, versioned commands."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from nessa.api.deps import CallerDep, Deps, IdempotencyKey
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_timestamped, encode
from nessa.api.schemas import ActorOut, RenameWorkspaceIn, WorkspaceOut, WorkspacePage
from nessa.db import Tx, actor_transaction
from nessa.identity import store
from nessa.identity.receipts import CommandResult, fingerprint, run_idempotent
from nessa.identity.workspaces import (
    CreateWorkspace,
    create_workspace,
    rename_workspace,
    visible_workspace,
)

router = APIRouter(prefix="/v1", responses=ERROR_RESPONSES)
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]


@router.get("/me", response_model=ActorOut, tags=["identity"], operation_id="get_me")
def me(caller: CallerDep) -> ActorOut:
    return ActorOut.of(caller.actor)


@router.get("/workspaces", response_model=WorkspacePage, tags=["workspaces"])
def list_workspaces(
    caller: CallerDep, deps: Deps, cursor: str | None = None, limit: Limit = DEFAULT_LIMIT
) -> WorkspacePage:
    after = decode_timestamped(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        rows = store.list_workspaces(tx, after=after, limit=limit + 1)
    page, more = rows[:limit], len(rows) > limit
    return WorkspacePage(
        items=[WorkspaceOut.of(w) for w in page],
        next_cursor=encode([page[-1].created_at.isoformat(), str(page[-1].workspace_id)])
        if more
        else None,
    )


@router.post(
    "/workspaces",
    status_code=201,
    response_model=WorkspaceOut,
    tags=["workspaces"],
    operation_id="create_workspace",
)
def create(
    body: CreateWorkspace, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        workspace = create_workspace(tx, caller.actor, body)
        return CommandResult(
            201, WorkspaceOut.of(workspace).model_dump(mode="json"), workspace.workspace_id
        )

    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "create_workspace",
        fingerprint("create_workspace", body.model_dump(mode="json")),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceOut,
    tags=["workspaces"],
    operation_id="get_workspace",
)
def get(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> WorkspaceOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return WorkspaceOut.of(visible_workspace(tx, workspace_id))


@router.patch(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceOut,
    tags=["workspaces"],
    operation_id="rename_workspace",
)
def rename(
    workspace_id: uuid.UUID,
    body: RenameWorkspaceIn,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        workspace = rename_workspace(tx, workspace_id, body.expected_version, body.name)
        return CommandResult(200, WorkspaceOut.of(workspace).model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "rename_workspace",
        fingerprint("rename_workspace", request),
        execute,
    )
    return JSONResponse(response, status_code=status)
