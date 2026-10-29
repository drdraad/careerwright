"""Research: start an acquisition (202 + run, in the background) and read it with its
targets and attempts; record pasted text; list and read jobs with their copies, claims and
freshness; mark favourites (Task 7A; spec sections 6, 7 and 11)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from nessa.api.deps import CallerDep, Deps, IdempotencyKey
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_timestamped, encode
from nessa.api.research_schemas import (
    AcquisitionOut,
    AcquisitionSummaryOut,
    AdvertsOut,
    JobDetailOut,
    JobOut,
    JobPage,
    ModelSpendOut,
    SearchOut,
    SkippedOut,
    SourceClaimOut,
    SubmittedAcquisitionOut,
    TargetOut,
)
from nessa.api.routes_runs import run_out
from nessa.db import Tx, actor_transaction
from nessa.evidence import acquisition as research
from nessa.evidence.acquisition import PasteText, SubmitAcquisition
from nessa.evidence.search import SubmitSearch, search_view, submit_search
from nessa.identity.keyring import Keyring
from nessa.identity.receipts import CommandResult, fingerprint, run_idempotent

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["research"]
)
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]


def acquisition_out(
    tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, run_id: uuid.UUID
) -> AcquisitionOut:
    view = research.acquisition(tx, workspace_id, run_id)
    summary = research.summary_of(tx, keyring, view.run)
    return AcquisitionOut(
        run=run_out(tx, keyring, view.run),
        targets=[TargetOut.of(t) for t in view.targets],
        job_ids=view.job_ids,
        summary=AcquisitionSummaryOut.of(summary) if summary else None,
        partial=view.partial,
    )


@router.post(
    "/research/acquisitions",
    status_code=202,
    response_model=SubmittedAcquisitionOut,
    operation_id="submit_acquisition",
)
def submit(
    workspace_id: uuid.UUID,
    body: SubmitAcquisition,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """202 with the run that fetches the sources; 200 with no run when every URL is being
    fetched already or is waiting out a back-off (each listed in `skipped`)."""

    def execute(tx: Tx) -> CommandResult:
        submitted = research.submit_acquisition(
            tx,
            caller.actor,
            workspace_id,
            body,
            runtime_mode=deps.settings.runtime_mode,
            now=deps.clock(),
        )
        out = SubmittedAcquisitionOut(
            acquisition=acquisition_out(tx, deps.keyring, workspace_id, submitted.run.run_id)
            if submitted.run
            else None,
            skipped=[SkippedOut.of(s) for s in submitted.skipped],
        )
        return CommandResult(
            202 if submitted.run else 200, out.model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "submit_acquisition",
        fingerprint("submit_acquisition", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get(
    "/research/acquisitions/{run_id}", response_model=AcquisitionOut, operation_id="get_acquisition"
)
def get_acquisition(
    workspace_id: uuid.UUID, run_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> AcquisitionOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return acquisition_out(tx, deps.keyring, workspace_id, run_id)


def search_out(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, run_id: uuid.UUID) -> SearchOut:
    view = search_view(tx, keyring, workspace_id, run_id)
    return SearchOut(search_id=run_id, run=run_out(tx, keyring, view.run), proposal=view.proposal)


@router.post(
    "/research/searches", status_code=202, response_model=SearchOut, operation_id="submit_search"
)
def submit_source_search(
    workspace_id: uuid.UUID, body: SubmitSearch, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    """Meta search for candidate pages for one confirmed target in one of your cities (202 +
    run). The run pins the profile version it read."""

    def execute(tx: Tx) -> CommandResult:
        run = submit_search(
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
        out = search_out(tx, deps.keyring, workspace_id, run.run_id)
        return CommandResult(202, out.model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "submit_search",
        fingerprint("submit_search", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/research/searches/{run_id}", response_model=SearchOut, operation_id="get_search")
def get_search(
    workspace_id: uuid.UUID, run_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> SearchOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return search_out(tx, deps.keyring, workspace_id, run_id)


@router.post(
    "/research/pasted", status_code=201, response_model=JobDetailOut, operation_id="paste_text"
)
def paste(
    workspace_id: uuid.UUID, body: PasteText, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    """Record a posting the person pasted: its own input route, never fetched, kept as their
    example of a target (at most three per target)."""

    def execute(tx: Tx) -> CommandResult:
        now = deps.clock()
        job_id = research.paste_text(
            tx, caller.actor, workspace_id, body, keyring=deps.keyring, now=now
        )
        view, claims = research.job_detail(tx, workspace_id, job_id, now=now)
        out = JobDetailOut(job=JobOut.of(view), claims=[SourceClaimOut.of(c) for c in claims])
        return CommandResult(201, out.model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "paste_text",
        fingerprint("paste_text", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/jobs", response_model=JobPage, operation_id="list_jobs")
def list_jobs(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    favourites: bool = False,
    cursor: str | None = None,
    limit: Limit = DEFAULT_LIMIT,
) -> JobPage:
    before = decode_timestamped(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        listing = research.list_jobs(
            tx,
            workspace_id,
            favourites_only=favourites,
            before=before,
            limit=limit,
            now=deps.clock(),
            models=deps.models,
        )
    last = listing.jobs[-1].job if listing.jobs else None
    return JobPage(
        items=[JobOut.of(v) for v in listing.jobs],
        next_cursor=encode([last.first_seen_at.isoformat(), str(last.job_id)])
        if listing.more and last
        else None,
        total_jobs=listing.total_jobs,
        exemplars=listing.exemplars,
        city_counts=listing.city_counts,
        coverage=listing.coverage,
        adverts=AdvertsOut.of(listing.adverts) if listing.adverts else None,
        empty_reason=listing.empty_reason,
        acquisition_model_spend=ModelSpendOut.of(listing.model_spend)
        if listing.model_spend
        else None,
    )


@router.get("/jobs/{job_id}", response_model=JobDetailOut, operation_id="get_job")
def get_job(
    workspace_id: uuid.UUID, job_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> JobDetailOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view, claims = research.job_detail(tx, workspace_id, job_id, now=deps.clock())
    return JobDetailOut(job=JobOut.of(view), claims=[SourceClaimOut.of(c) for c in claims])


def _favourite(
    workspace_id: uuid.UUID,
    job_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    key: uuid.UUID,
    *,
    favourite: bool,
) -> JSONResponse:
    command = "favourite_job" if favourite else "unfavourite_job"

    def execute(tx: Tx) -> CommandResult:
        research.set_favourite(tx, caller.actor, workspace_id, job_id, favourite=favourite)
        view, _ = research.job_detail(tx, workspace_id, job_id, now=deps.clock())
        return CommandResult(200, JobOut.of(view).model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), "job_id": str(job_id)}
    status, response = run_idempotent(
        deps.engine, caller.actor.actor_id, key, command, fingerprint(command, request), execute
    )
    return JSONResponse(response, status_code=status)


@router.put("/jobs/{job_id}/favourite", response_model=JobOut, operation_id="favourite_job")
def favourite_job(
    workspace_id: uuid.UUID, job_id: uuid.UUID, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    return _favourite(workspace_id, job_id, caller, deps, key, favourite=True)


@router.delete("/jobs/{job_id}/favourite", response_model=JobOut, operation_id="unfavourite_job")
def unfavourite_job(
    workspace_id: uuid.UUID, job_id: uuid.UUID, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    return _favourite(workspace_id, job_id, caller, deps, key, favourite=False)
