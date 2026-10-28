"""Interview turns: send a message (202 + turn, run in the background), read turns, and
decide on a turn's proposals (the profile changes only here, through the same command as
a direct edit)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from nessa.api.deps import CallerDep, Deps, IdempotencyKey
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.interview_schemas import DecisionOut, DecisionResult, TurnOut, TurnPage
from nessa.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_timestamped, encode
from nessa.api.routes_runs import run_out
from nessa.api.schemas import ProfileOut
from nessa.db import Tx, actor_transaction
from nessa.identity.keyring import Keyring
from nessa.identity.receipts import CommandResult, fingerprint, run_idempotent
from nessa.identity.workspaces import visible_workspace
from nessa.profile import interview_store
from nessa.profile.conversation import (
    DecideTurn,
    SubmitTurn,
    TurnView,
    decide_turn,
    submit_turn,
    turn_view,
    visible_turn,
)

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}/interview", responses=ERROR_RESPONSES, tags=["interview"]
)
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]


def turn_out(tx: Tx, keyring: Keyring, view: TurnView) -> TurnOut:
    return TurnOut.of(view, run_out(tx, keyring, view.run))


@router.post("/turns", status_code=202, response_model=TurnOut, operation_id="submit_turn")
def submit(
    workspace_id: uuid.UUID, body: SubmitTurn, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        view = submit_turn(
            tx,
            caller.actor,
            workspace_id,
            body,
            models=deps.models,
            keyring=deps.keyring,
            runtime_mode=deps.settings.runtime_mode,
            defaults=deps.spend_defaults,
            now=deps.clock(),
        )
        return CommandResult(
            202, turn_out(tx, deps.keyring, view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "submit_turn",
        fingerprint("submit_turn", request),
        execute,
    )
    location = f"/v1/workspaces/{workspace_id}/interview/turns/{response['turn_id']}"
    return JSONResponse(response, status_code=status, headers={"Location": location})


@router.get("/turns/{turn_id}", response_model=TurnOut, operation_id="get_turn")
def get_turn(workspace_id: uuid.UUID, turn_id: uuid.UUID, caller: CallerDep, deps: Deps) -> TurnOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return turn_out(tx, deps.keyring, visible_turn(tx, deps.keyring, workspace_id, turn_id))


@router.get("/turns", response_model=TurnPage, operation_id="list_turns")
def list_turns(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    cursor: str | None = None,
    limit: Limit = DEFAULT_LIMIT,
) -> TurnPage:
    before = decode_timestamped(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        rows = interview_store.turns(tx, workspace_id, before=before, limit=limit + 1)
        page, more = rows[:limit], len(rows) > limit
        items = [turn_out(tx, deps.keyring, turn_view(tx, deps.keyring, t)) for t in page]
    return TurnPage(
        items=items,
        next_cursor=encode([page[-1].created_at.isoformat(), str(page[-1].turn_id)])
        if more
        else None,
    )


@router.post(
    "/turns/{turn_id}/decision",
    response_model=DecisionResult,
    status_code=201,
    responses={200: {"model": DecisionResult, "description": "Decided; no field changed."}},
    operation_id="decide_turn",
)
def decide(
    workspace_id: uuid.UUID,
    turn_id: uuid.UUID,
    body: DecideTurn,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        decision, profile = decide_turn(
            tx, caller.actor, workspace_id, turn_id, body, keyring=deps.keyring, now=deps.clock()
        )
        result = DecisionResult(
            turn_id=turn_id, decision=DecisionOut.of(decision), profile=ProfileOut.of(profile)
        )
        status = 201 if decision.profile_version is not None else 200
        return CommandResult(status, result.model_dump(mode="json"), workspace_id)

    request = {
        "workspace_id": str(workspace_id),
        "turn_id": str(turn_id),
        **body.model_dump(mode="json"),
    }
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "decide_turn",
        fingerprint("decide_turn", request),
        execute,
    )
    return JSONResponse(response, status_code=status)
