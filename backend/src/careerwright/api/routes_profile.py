"""Profile endpoints: read the current version and its history; write with an expected version."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from careerwright.api.catalogue_schemas import ProvisionalConceptOut, ProvisionalConceptPage
from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.api.pagination import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    decode_int,
    decode_timestamped,
    encode,
)
from careerwright.api.schemas import (
    ProfileOut,
    ProfileVersionPage,
    ProfileWriteIn,
    SourceOut,
    SourcePage,
)
from careerwright.catalogue import taxonomy_store
from careerwright.db import Tx, actor_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import store
from careerwright.profile.commands import (
    RevertProfile,
    current_profile,
    revert_profile,
    write_profile,
)
from careerwright.profile.concepts import RegisterProvisionalConcept, register_provisional_concept

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


@router.post(
    "/profile/revert",
    response_model=ProfileOut,
    status_code=201,
    responses={200: {"model": ProfileOut, "description": "No field changed; no new version."}},
    operation_id="revert_profile",
)
def revert(
    workspace_id: uuid.UUID,
    body: RevertProfile,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """Undo: an earlier version's answers, each with the source it had, as a new version."""

    def execute(tx: Tx) -> CommandResult:
        view, created = revert_profile(tx, caller.actor, workspace_id, body)
        return CommandResult(
            201 if created else 200, ProfileOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "revert_profile",
        fingerprint("revert_profile", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get(
    "/profile/versions",
    response_model=ProfileVersionPage,
    operation_id="list_profile_versions",
)
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
        items=[ProfileOut.of_version(v) for v in page],
        next_cursor=encode(page[-1].version) if more else None,
    )


@router.get(
    "/profile/versions/{version}",
    response_model=ProfileOut,
    operation_id="get_profile_version",
)
def get_version(
    workspace_id: uuid.UUID, version: Annotated[int, Path(ge=1)], caller: CallerDep, deps: Deps
) -> ProfileOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        found = store.profile_version(tx, workspace_id, version)
    if found is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such profile version.", stage=ErrorStage.PROFILE
        )
    return ProfileOut.of_version(found)


@router.post(
    "/occupations/provisional",
    response_model=ProvisionalConceptOut,
    status_code=201,
    responses={200: {"model": ProvisionalConceptOut, "description": "Already registered."}},
    operation_id="register_provisional_concept",
)
def register_provisional(
    workspace_id: uuid.UUID,
    body: RegisterProvisionalConcept,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        concept, created = register_provisional_concept(
            tx, caller.actor, workspace_id, body, deps.clock()
        )
        return CommandResult(
            201 if created else 200,
            ProvisionalConceptOut.of(concept).model_dump(mode="json"),
            workspace_id,
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "register_provisional_concept",
        fingerprint("register_provisional_concept", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get(
    "/occupations/provisional",
    response_model=ProvisionalConceptPage,
    operation_id="list_provisional_concepts",
)
def list_provisional(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    cursor: str | None = None,
    limit: Limit = DEFAULT_LIMIT,
) -> ProvisionalConceptPage:
    after = decode_timestamped(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        rows = taxonomy_store.provisional_concepts(tx, workspace_id, after=after, limit=limit + 1)
    page, more = rows[:limit], len(rows) > limit
    return ProvisionalConceptPage(
        items=[ProvisionalConceptOut.of(c) for c in page],
        next_cursor=encode([page[-1].created_at.isoformat(), str(page[-1].concept_id)])
        if more
        else None,
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
