"""Career discovery: start a discovery (202 + run, in the background), read it and its
slate, ask for its slate's one written explanation (202 + run), choose an ESCO occupation as
a target, and read the early requirement sketch."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from nessa.api.deps import CallerDep, Deps, IdempotencyKey
from nessa.api.discovery_schemas import (
    DiscoveryOut,
    DiscoveryPage,
    DiscoveryProposalOut,
    ExplanationRunOut,
    SketchOut,
    SlateExplanationOut,
    SlateOut,
    WrittenExplanationOut,
)
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.pagination import DEFAULT_LIMIT, MAX_LIMIT, decode_timestamped, encode
from nessa.api.routes_runs import run_out
from nessa.api.schemas import ProfileOut
from nessa.db import Tx, actor_transaction
from nessa.identity.keyring import Keyring
from nessa.identity.receipts import CommandResult, fingerprint, run_idempotent
from nessa.profile.exploration import (
    ChooseTarget,
    DiscoveryView,
    ExplanationView,
    SubmitDiscovery,
    SubmitExplanation,
    choose_target,
    discoveries,
    discovery_slate,
    submit_discovery,
    submit_explanation,
    visible_discovery,
)
from nessa.profile.sketch import requirement_sketch
from nessa.profile.slate import POOL_LIMIT, Emphasis, SlateControls

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["discovery"]
)
Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]
FamilyCode = Annotated[str, Query(pattern=r"^[0-9]{3}$")]


def explanation_out(tx: Tx, keyring: Keyring, view: ExplanationView) -> SlateExplanationOut:
    return SlateExplanationOut(
        explanation_id=view.request.explanation_id,
        discovery_id=view.request.discovery_id,
        run=run_out(tx, keyring, view.run),
        written=WrittenExplanationOut.of(view.written) if view.written else None,
    )


def discovery_out(tx: Tx, keyring: Keyring, view: DiscoveryView) -> DiscoveryOut:
    return DiscoveryOut(
        discovery_id=view.run.run_id,
        profile_version=view.run.profile_version or 0,
        run=run_out(tx, keyring, view.run),
        proposal=DiscoveryProposalOut.of(view.proposal) if view.proposal else None,
        explanation=explanation_out(tx, keyring, view.explanation) if view.explanation else None,
    )


@router.post(
    "/discoveries", status_code=202, response_model=DiscoveryOut, operation_id="submit_discovery"
)
def submit(
    workspace_id: uuid.UUID,
    body: SubmitDiscovery,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        view = submit_discovery(
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
            202, discovery_out(tx, deps.keyring, view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "submit_discovery",
        fingerprint("submit_discovery", request),
        execute,
    )
    location = f"/v1/workspaces/{workspace_id}/discoveries/{response['discovery_id']}"
    return JSONResponse(response, status_code=status, headers={"Location": location})


@router.get("/discoveries", response_model=DiscoveryPage, operation_id="list_discoveries")
def list_all(
    workspace_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    cursor: str | None = None,
    limit: Limit = DEFAULT_LIMIT,
) -> DiscoveryPage:
    before = decode_timestamped(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        views = discoveries(tx, deps.keyring, workspace_id, before=before, limit=limit + 1)
        page, more = views[:limit], len(views) > limit
        items = [discovery_out(tx, deps.keyring, view) for view in page]
    last = page[-1].run if page else None
    return DiscoveryPage(
        items=items,
        next_cursor=encode([last.created_at.isoformat(), str(last.run_id)])
        if more and last
        else None,
    )


@router.get(
    "/discoveries/{discovery_id}", response_model=DiscoveryOut, operation_id="get_discovery"
)
def get_one(
    workspace_id: uuid.UUID, discovery_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> DiscoveryOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = visible_discovery(tx, deps.keyring, workspace_id, discovery_id)
        return discovery_out(tx, deps.keyring, view)


@router.get("/discoveries/{discovery_id}/slate", response_model=SlateOut, operation_id="get_slate")
def get_slate(
    workspace_id: uuid.UUID,
    discovery_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    emphasis: Emphasis = Emphasis.BALANCED,
    exclude_concept: Annotated[list[uuid.UUID], Query(max_length=POOL_LIMIT)] = [],  # noqa: B006
    exclude_family: Annotated[list[FamilyCode], Query(max_length=POOL_LIMIT)] = [],  # noqa: B006
) -> SlateOut:
    """Recomputed on each read from the stored searches and the held taxonomy (a note says
    so if the searches were chosen for another release). The controls are view parameters
    only: they change nothing stored and are never limits."""
    controls = SlateControls(
        emphasis=emphasis,
        exclude_concepts=frozenset(exclude_concept),
        exclude_families=frozenset(exclude_family),
    )
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = discovery_slate(tx, deps.keyring, workspace_id, discovery_id, controls)
        return SlateOut.of(view, emphasis)


@router.post(
    "/discoveries/{discovery_id}/explanation",
    status_code=202,
    response_model=ExplanationRunOut,
    responses={
        200: {
            "model": ExplanationRunOut,
            "description": "Already asked for: the slate's one explanation's run, in its state.",
        }
    },
    operation_id="submit_explanation",
)
def explain(
    workspace_id: uuid.UUID,
    discovery_id: uuid.UUID,
    body: SubmitExplanation,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """The written "Why this could suit you" for the slate's first view, as one bounded
    run. A slate has at most one: asking again, from any view, answers 200 with its run. The
    answer never holds the written text (it is kept as the command's receipt); the
    discovery carries it."""

    def execute(tx: Tx) -> CommandResult:
        view, started = submit_explanation(
            tx,
            caller.actor,
            workspace_id,
            discovery_id,
            body,
            models=deps.models,
            keyring=deps.keyring,
            runtime_mode=deps.settings.runtime_mode,
            defaults=deps.spend_defaults,
            now=deps.clock(),
        )
        answer = ExplanationRunOut(
            explanation_id=view.request.explanation_id,
            discovery_id=view.request.discovery_id,
            run=run_out(tx, deps.keyring, view.run),
        )
        return CommandResult(202 if started else 200, answer.model_dump(mode="json"), workspace_id)

    request = {
        "workspace_id": str(workspace_id),
        "discovery_id": str(discovery_id),
        **body.model_dump(mode="json"),
    }
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "submit_explanation",
        fingerprint("submit_explanation", request),
        execute,
    )
    location = f"/v1/workspaces/{workspace_id}/discoveries/{discovery_id}"
    return JSONResponse(response, status_code=status, headers={"Location": location})


@router.post(
    "/targets",
    response_model=ProfileOut,
    status_code=201,
    responses={200: {"model": ProfileOut, "description": "Already a target; nothing changed."}},
    operation_id="choose_target",
)
def choose(
    workspace_id: uuid.UUID,
    body: ChooseTarget,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        view, changed = choose_target(tx, caller.actor, workspace_id, body, deps.clock())
        return CommandResult(
            201 if changed else 200, ProfileOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "choose_target",
        fingerprint("choose_target", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/sketch", response_model=SketchOut, operation_id="get_sketch")
def get_sketch(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> SketchOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return SketchOut.of(requirement_sketch(tx, workspace_id))
