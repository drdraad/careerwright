"""Runs: submit (202 + run ID + Location) and read the authoritative state (DUR-03)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from nessa.api.deps import CallerDep, Deps, IdempotencyKey
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_timestamped, encode
from nessa.api.schemas import RunOut, RunPage
from nessa.db import Tx, actor_transaction
from nessa.identity import run_store
from nessa.identity.keyring import Keyring
from nessa.identity.receipts import CommandResult, fingerprint, run_idempotent
from nessa.identity.records import Run
from nessa.identity.runs import SubmitRun, open_output, submit_run, visible_run
from nessa.identity.workspaces import visible_workspace

router = APIRouter(prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["runs"])
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]


def run_out(tx: Tx, keyring: Keyring, run: Run) -> RunOut:
    """A run with its attempts and, if accepted, its opened output (also used by export)."""
    return RunOut.of(run, run_store.attempts(tx, run.run_id), open_output(tx, keyring, run))


@router.post("/runs", status_code=202, response_model=RunOut, operation_id="submit_run")
def submit(
    workspace_id: uuid.UUID, body: SubmitRun, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        run = submit_run(
            tx,
            caller.actor,
            workspace_id,
            body,
            models=deps.models,
            runtime_mode=deps.settings.runtime_mode,
            defaults=deps.spend_defaults,
            now=deps.clock(),
        )
        return CommandResult(
            202, run_out(tx, deps.keyring, run).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "submit_run",
        fingerprint("submit_run", request),
        execute,
    )
    location = f"/v1/workspaces/{workspace_id}/runs/{response['run_id']}"
    return JSONResponse(response, status_code=status, headers={"Location": location})


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(workspace_id: uuid.UUID, run_id: uuid.UUID, caller: CallerDep, deps: Deps) -> RunOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return run_out(tx, deps.keyring, visible_run(tx, workspace_id, run_id))


@router.get("/runs", response_model=RunPage)
def list_runs(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    cursor: str | None = None,
    limit: Limit = DEFAULT_LIMIT,
) -> RunPage:
    before = decode_timestamped(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        rows = run_store.runs(tx, workspace_id, before=before, limit=limit + 1)
        page, more = rows[:limit], len(rows) > limit
        items = [run_out(tx, deps.keyring, run) for run in page]
    return RunPage(
        items=items,
        next_cursor=encode([page[-1].created_at.isoformat(), str(page[-1].run_id)])
        if more
        else None,
    )
