"""Interview turns: send a message (202 + turn, run in the background), read turns and the
reply as it streams, and decide on a turn's proposals (the profile changes only here,
through the same command as a direct edit)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES, correlation_id, error_body, error_status
from careerwright.api.interview_schemas import (
    DecisionOut,
    DecisionResult,
    PartialReplyOut,
    PreferencesOut,
    SupportNoteOut,
    TurnOut,
    TurnPage,
    TurnRefusedOut,
    TurnSubmittedOut,
)
from careerwright.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_timestamped, encode
from careerwright.api.routes_runs import run_out
from careerwright.api.schemas import ProfileOut
from careerwright.db import Tx, actor_transaction
from careerwright.errors import CareerwrightError
from careerwright.identity.keyring import Keyring
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.identity.runs import partial_reply
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import interview_store
from careerwright.profile.conversation import (
    DecideTurn,
    SubmitTurn,
    TurnView,
    decide_turn,
    submit_turn,
    turn_view,
    visible_turn,
)
from careerwright.profile.preferences import SetPreferences, current_preferences, set_preferences
from careerwright.profile.safety import has_risk_stem

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}/interview", responses=ERROR_RESPONSES, tags=["interview"]
)
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]


def turn_out(tx: Tx, keyring: Keyring, view: TurnView) -> TurnOut:
    return TurnOut.of(view, run_out(tx, keyring, view.run))


@router.post(
    "/turns",
    status_code=202,
    response_model=TurnSubmittedOut,
    responses={
        "4XX": {"model": TurnRefusedOut, "description": "Typed error envelope"},
        "5XX": {"model": TurnRefusedOut, "description": "Typed error envelope"},
    },
    operation_id="submit_turn",
)
def submit(
    workspace_id: uuid.UUID,
    body: SubmitTurn,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
    http: Request,
) -> JSONResponse:
    # Screened before anything can refuse the send, so a refusal shows the panel too.
    support = has_risk_stem(body.message)

    def execute(tx: Tx) -> CommandResult:
        sent = submit_turn(
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
        # The receipt records the turn only; the support panel is added below, every time.
        return CommandResult(
            202, turn_out(tx, deps.keyring, sent).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    try:
        status, response = run_idempotent(
            deps.engine,
            caller.actor.actor_id,
            key,
            "submit_turn",
            fingerprint("submit_turn", request),
            execute,
        )
    except CareerwrightError as error:
        if not support:
            raise
        refused = TurnRefusedOut(
            error=error_body(error, correlation_id(http)),
            support_note=SupportNoteOut.current(sent=False),
        )
        return JSONResponse(refused.model_dump(mode="json"), status_code=error_status(error))
    # A replay has the same request (by fingerprint), so the same panel is derived again.
    submitted = TurnSubmittedOut.sent(TurnOut.model_validate(response), support=support)
    location = f"/v1/workspaces/{workspace_id}/interview/turns/{response['turn_id']}"
    return JSONResponse(
        submitted.model_dump(mode="json"), status_code=status, headers={"Location": location}
    )


@router.get("/preferences", response_model=PreferencesOut, operation_id="get_preferences")
def get_preferences(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> PreferencesOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return PreferencesOut.of(current_preferences(tx, workspace_id))


@router.put("/preferences", response_model=PreferencesOut, operation_id="put_preferences")
def put_preferences(
    workspace_id: uuid.UUID,
    body: SetPreferences,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        saved = set_preferences(tx, caller.actor, workspace_id, body)
        return CommandResult(200, PreferencesOut.of(saved).model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "set_interview_preferences",
        fingerprint("set_interview_preferences", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/turns/{turn_id}", response_model=TurnOut, operation_id="get_turn")
def get_turn(workspace_id: uuid.UUID, turn_id: uuid.UUID, caller: CallerDep, deps: Deps) -> TurnOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return turn_out(tx, deps.keyring, visible_turn(tx, deps.keyring, workspace_id, turn_id))


@router.get("/turns/{turn_id}/reply", response_model=PartialReplyOut, operation_id="get_turn_reply")
def get_turn_reply(
    workspace_id: uuid.UUID, turn_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> PartialReplyOut:
    """The reply as it streams; poll it when a `run.partial_updated` event names the turn."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = visible_turn(tx, deps.keyring, workspace_id, turn_id)
        return PartialReplyOut.of(turn_id, partial_reply(tx, deps.keyring, view.run))


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
