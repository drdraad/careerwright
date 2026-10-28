"""Profile endpoints: read the current version and its history; write with an expected version."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from nessa.api.deps import CallerDep, Deps, IdempotencyKey
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_int, decode_timestamped, encode
from nessa.api.schemas import ProfileOut, ProfileVersionPage, ProfileWriteIn, SourceOut, SourcePage
from nessa.db import Tx, actor_transaction
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity.receipts import CommandResult, fingerprint, run_idempotent
from nessa.identity.workspaces import visible_workspace
from nessa.profile import store
from nessa.profile.commands import ProfileView, current_profile, write_profile

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["profile"]
)
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]


@router.get("/profile", response_model=ProfileOut)
def get_profile(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> ProfileOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return ProfileOut.of(current_profile(tx, workspace_id))


@router.put(
    "/profile",
    response_model=ProfileOut,
    status_code=201,
    responses={200: {"model": ProfileOut, "description": "No field changed; no new version."}},
)
def put_profile(
    workspace_id: uuid.UUID,
    body: ProfileWriteIn,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        view, created = write_profile(
            tx, caller.actor, workspace_id, body.expected_version, body.profile, deps.clock()
        )
        return CommandResult(
            201 if created else 200, ProfileOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "write_profile",
        fingerprint("write_profile", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/profile/versions", response_model=ProfileVersionPage)
def list_versions(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    cursor: str | None = None,
    limit: Limit = DEFAULT_LIMIT,
) -> ProfileVersionPage:
    before = decode_int(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        rows = store.list_profile_versions(tx, workspace_id, before=before, limit=limit + 1)
    page, more = rows[:limit], len(rows) > limit
    return ProfileVersionPage(
        items=[
            ProfileOut.of(
                ProfileView(v.workspace_id, v.version, v.document, v.created_by, v.created_at)
            )
            for v in page
        ],
        next_cursor=encode(page[-1].version) if more else None,
    )


@router.get("/profile/versions/{version}", response_model=ProfileOut)
def get_version(
    workspace_id: uuid.UUID, version: Annotated[int, Path(ge=1)], caller: CallerDep, deps: Deps
) -> ProfileOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        found = store.profile_version(tx, workspace_id, version)
    if found is None:
        raise NessaError(ErrorCode.NOT_FOUND, "No such profile version.", stage=ErrorStage.PROFILE)
    return ProfileOut.of(
        ProfileView(
            found.workspace_id, found.version, found.document, found.created_by, found.created_at
        )
    )


@router.get("/sources", response_model=SourcePage)
def list_sources(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    cursor: str | None = None,
    limit: Limit = DEFAULT_LIMIT,
) -> SourcePage:
    after = decode_timestamped(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        rows = store.list_sources(tx, workspace_id, after=after, limit=limit + 1)
    page, more = rows[:limit], len(rows) > limit
    return SourcePage(
        items=[SourceOut.of(s) for s in page],
        next_cursor=encode([page[-1].created_at.isoformat(), str(page[-1].source_ref_id)])
        if more
        else None,
    )
