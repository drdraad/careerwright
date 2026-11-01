"""Identity and workspace endpoints. Writes are idempotent, versioned commands. A workspace's
name is typed by the person, so it goes through the support screen."""

import uuid
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES, correlation_id, error_body, error_status
from careerwright.api.interview_schemas import (
    SupportNoteOut,
    WorkspaceRefusedOut,
    WorkspaceSavedOut,
)
from careerwright.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_timestamped, encode
from careerwright.api.schemas import ActorOut, RenameWorkspaceIn, WorkspaceOut, WorkspacePage
from careerwright.db import Tx, actor_transaction
from careerwright.errors import CareerwrightError
from careerwright.identity import store
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.identity.workspaces import (
    CreateWorkspace,
    create_workspace,
    rename_workspace,
    visible_workspace,
)
from careerwright.profile.safety import has_risk_stem

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


def _screened(
    support: bool, http: Request, command: Callable[[], tuple[int, dict[str, Any]]]
) -> JSONResponse:
    """Runs a create or rename whose name went through the support screen (the product
    owner's "every place a person types"; `careerwright.profile.safety`): saved as usual, with
    the calm panel beside the answer or its refusal. The panel is derived from the request,
    never stored: the receipt stays the plain `WorkspaceOut`."""
    try:
        status, response = command()
    except CareerwrightError as error:
        if not support:
            raise
        refused = WorkspaceRefusedOut(
            error=error_body(error, correlation_id(http)),
            support_note=SupportNoteOut.beside_an_entry(saved=False),
        )
        return JSONResponse(refused.model_dump(mode="json"), status_code=error_status(error))
    saved = WorkspaceSavedOut.saved(WorkspaceOut.model_validate(response), support=support)
    return JSONResponse(saved.model_dump(mode="json"), status_code=status)


_SCREENED_RESPONSES: dict[int | str, dict[str, Any]] = {
    "4XX": {"model": WorkspaceRefusedOut, "description": "Typed error envelope"},
    "5XX": {"model": WorkspaceRefusedOut, "description": "Typed error envelope"},
}


@router.post(
    "/workspaces",
    status_code=201,
    response_model=WorkspaceSavedOut,
    responses=_SCREENED_RESPONSES,
    tags=["workspaces"],
    operation_id="create_workspace",
)
def create(
    body: CreateWorkspace, caller: CallerDep, deps: Deps, key: IdempotencyKey, http: Request
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        workspace = create_workspace(
            tx, caller.actor, body, adzuna_configured=deps.settings.adzuna_configured
        )
        return CommandResult(
            201, WorkspaceOut.of(workspace).model_dump(mode="json"), workspace.workspace_id
        )

    return _screened(
        has_risk_stem(body.name),
        http,
        lambda: run_idempotent(
            deps.engine,
            caller.actor.actor_id,
            key,
            "create_workspace",
            fingerprint("create_workspace", body.model_dump(mode="json")),
            execute,
        ),
    )


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
    response_model=WorkspaceSavedOut,
    responses=_SCREENED_RESPONSES,
    tags=["workspaces"],
    operation_id="rename_workspace",
)
def rename(
    workspace_id: uuid.UUID,
    body: RenameWorkspaceIn,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
    http: Request,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        workspace = rename_workspace(tx, workspace_id, body.expected_version, body.name)
        return CommandResult(200, WorkspaceOut.of(workspace).model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    return _screened(
        has_risk_stem(body.name),
        http,
        lambda: run_idempotent(
            deps.engine,
            caller.actor.actor_id,
            key,
            "rename_workspace",
            fingerprint("rename_workspace", request),
            execute,
        ),
    )
