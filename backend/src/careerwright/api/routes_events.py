"""Workspace status events: a JSON page and a resumable server-sent-event stream (DUR-03).

Each SSE message has `id: <seq>`; a client that reconnects with `Last-Event-ID` receives
everything after it, because sequence numbers increase in commit order. The stream re-reads
through row-level security on every poll, so a revoked invitation ends it at once; it
re-verifies the ID token with the Auth emulator every `REVERIFY_S`, so a revoked or disabled
account ends it within that bound; and it ends when the token expires (the client reconnects
with a fresh token). The terminal state of a run is always available from the runs API;
events only tell the client when to look.
"""

import time
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

import anyio
from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from careerwright.api.deps import Caller, CallerDep, Deps
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.api.schemas import EventOut, EventPage
from careerwright.db import Engine, actor_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import store
from careerwright.identity.records import WorkspaceEvent
from careerwright.identity.workspaces import visible_workspace

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["events"]
)
PAGE = 200
POLL_INTERVAL_S = 0.5
HEARTBEAT_S = 15.0
REVERIFY_S = 60.0
RETRY_MS = 2000


def _events(
    engine: Engine, caller: Caller, workspace_id: uuid.UUID, after: int
) -> list[WorkspaceEvent]:
    with actor_transaction(engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        return store.events_after(tx, workspace_id, after, PAGE)


def _resume_point(last_event_id: str | None, after: int | None) -> int:
    if last_event_id is None:
        return after or 0
    try:
        value = int(last_event_id)
    except ValueError:
        value = -1
    if value < 0:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Last-Event-ID must be an event sequence number from this stream.",
            stage=ErrorStage.REQUEST,
            details={"field": "Last-Event-ID"},
        )
    return value


@router.get("/events", response_model=EventPage)
def list_events(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    after: Annotated[int, Query(ge=0)] = 0,
) -> EventPage:
    events = _events(deps.engine, caller, workspace_id, after)
    return EventPage(
        items=[EventOut.of(e) for e in events], last_seq=events[-1].seq if events else after
    )


@router.get(
    "/events/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Server-sent events; each `data` is an EventOut, `id` its seq.",
            "content": {"text/event-stream": {"schema": {"$ref": "#/components/schemas/EventOut"}}},
        }
    },
)
async def stream_events(
    workspace_id: uuid.UUID,
    request: Request,
    caller: CallerDep,
    deps: Deps,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    after: Annotated[int | None, Query(ge=0)] = None,
) -> StreamingResponse:
    start = _resume_point(last_event_id, after)
    # Fail before streaming: another actor's workspace is a plain 404 envelope.
    await run_in_threadpool(_events, deps.engine, caller, workspace_id, start)

    async def generate() -> AsyncIterator[str]:
        cursor = start
        last_sent = time.monotonic()
        next_verify = last_sent + REVERIFY_S
        yield f"retry: {RETRY_MS}\n\n"
        while not await request.is_disconnected():
            if time.time() >= caller.identity.expires_at:
                yield "event: reauthenticate\ndata: {}\n\n"
                return
            try:
                if time.monotonic() >= next_verify:
                    await run_in_threadpool(deps.verifier.verify, caller.token.get_secret_value())
                    next_verify = time.monotonic() + REVERIFY_S
                events = await run_in_threadpool(_events, deps.engine, caller, workspace_id, cursor)
            except CareerwrightError as error:
                yield f'event: stream_ended\ndata: {{"code": "{error.code.value}"}}\n\n'
                return
            for event in events:
                yield f"id: {event.seq}\ndata: {EventOut.of(event).model_dump_json()}\n\n"
                cursor = event.seq
                last_sent = time.monotonic()
            if time.monotonic() - last_sent >= HEARTBEAT_S:
                yield ": keep-alive\n\n"
                last_sent = time.monotonic()
            await anyio.sleep(POLL_INTERVAL_S)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
