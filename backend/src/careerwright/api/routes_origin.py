"""The world's first moments (plan section 4; Sprint W SW.5; S2.8): answer the first question
with an ESCO occupation, a UK job title or the person's own words, and "Which of these is
closest?"; read the origin (the role, the skills it usually needs, the first destinations and
the unexpected connection); and ask for, read and decide a turn's overlooked strength. Every
write takes an expected version and an Idempotency-Key."""

import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES, correlation_id, error_body, error_status
from careerwright.api.interview_schemas import SupportNoteOut
from careerwright.api.origin_schemas import (
    OriginOut,
    ProposedStrengthOut,
    StrengthDecidedOut,
    StrengthDecisionOut,
    StrengthOut,
    StrengthRunOut,
    TitleRefusedOut,
)
from careerwright.api.routes_runs import run_out
from careerwright.api.schemas import ProfileOut
from careerwright.capability import store as capability_store
from careerwright.capability import usual
from careerwright.capability.strengths import (
    DecideStrength,
    StrengthView,
    SubmitStrength,
    decide_strength,
    submit_strength,
    turn_strength,
)
from careerwright.db import Tx, actor_transaction
from careerwright.errors import CareerwrightError
from careerwright.identity.keyring import Keyring
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.profile.exploration import (
    ChooseClosest,
    ChooseRole,
    NameRole,
    choose_closest,
    choose_role,
    first_slate,
    hard_filters,
    name_role,
)
from careerwright.profile.safety import has_risk_stem
from careerwright.vocabulary import WorkState

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["origin"]
)


@router.get("/origin", response_model=OriginOut, operation_id="get_origin")
def get_origin(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> OriginOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        hard = hard_filters(tx, workspace_id, deps.mapping_reviews, deps.assessment_packs)
        first = first_slate(tx, workspace_id, hard, deps.pack_targets)
        evidence = capability_store.evidence(tx, workspace_id)
        found = usual.usual_skills(first.occupation, evidence) if first.occupation else []
        version = capability_store.state(tx, workspace_id).version
        return OriginOut.of(first, found, version)


@router.post(
    "/origin/role",
    response_model=ProfileOut,
    status_code=201,
    responses={200: {"model": ProfileOut, "description": "Already the role; nothing changed."}},
    operation_id="choose_role",
)
def post_role(
    workspace_id: uuid.UUID,
    body: ChooseRole,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """The first answer: the ESCO occupation the person does now or did last, saved as
    their current role through the one profile write path."""

    def execute(tx: Tx) -> CommandResult:
        view, changed = choose_role(
            tx, caller.actor, workspace_id, body, deps.clock(), deps.pack_targets
        )
        return CommandResult(
            201 if changed else 200, ProfileOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "choose_role",
        fingerprint("choose_role", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.post(
    "/origin/role/title",
    response_model=ProfileOut,
    status_code=201,
    responses={
        200: {"model": ProfileOut, "description": "Already the role; nothing changed."},
        "4XX": {"model": TitleRefusedOut, "description": "Typed error envelope"},
        "5XX": {"model": TitleRefusedOut, "description": "Typed error envelope"},
    },
    operation_id="name_role",
)
def post_role_title(
    workspace_id: uuid.UUID,
    body: NameRole,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
    http: Request,
) -> JSONResponse:
    """The first answer in the person's own words: a UK job title picked from the type-ahead,
    or anything typed ("Use my own words"), saved exactly as given as their current role
    through the one profile write path; no model is called. Nothing is refused for its words,
    except a title the support screen answers (`careerwright.profile.safety`), as it answers a
    message: never kept as the role, with the calm support panel beside the refusal."""
    # Screened before anything can refuse it, so every refusal shows the panel too; the
    # panel is derived from the request each time and never stored.
    support = has_risk_stem(body.title)

    def execute(tx: Tx) -> CommandResult:
        view, changed = name_role(
            tx, caller.actor, workspace_id, body, deps.clock(), deps.pack_targets
        )
        return CommandResult(
            201 if changed else 200, ProfileOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    try:
        status, response = run_idempotent(
            deps.engine,
            caller.actor.actor_id,
            key,
            "name_role",
            fingerprint("name_role", request),
            execute,
        )
    except CareerwrightError as error:
        if not support:
            raise
        refused = TitleRefusedOut(
            error=error_body(error, correlation_id(http)),
            support_note=SupportNoteOut.beside_a_title(),
        )
        return JSONResponse(refused.model_dump(mode="json"), status_code=error_status(error))
    return JSONResponse(response, status_code=status)


@router.post(
    "/origin/role/closest",
    response_model=ProfileOut,
    status_code=201,
    responses={200: {"model": ProfileOut, "description": "Already the answer; nothing changed."}},
    operation_id="choose_closest",
)
def post_role_closest(
    workspace_id: uuid.UUID,
    body: ChooseClosest,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """The answer to "Which of these is closest?" (the origin's `role.closest`): one of the
    ESCO occupations offered, which becomes the role's occupation with the person's words
    kept, or null, "None of these is my job", which leaves the role with no ESCO occupation
    and asks for no other."""

    def execute(tx: Tx) -> CommandResult:
        view, changed = choose_closest(
            tx, caller.actor, workspace_id, body, deps.clock(), deps.pack_targets
        )
        return CommandResult(
            201 if changed else 200, ProfileOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "choose_closest",
        fingerprint("choose_closest", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


def _run_out(tx: Tx, keyring: Keyring, view: StrengthView) -> StrengthRunOut:
    return StrengthRunOut(
        strength_id=view.request.strength_id,
        turn_id=view.request.turn_id,
        run=run_out(tx, keyring, view.run),
    )


def _strength_out(tx: Tx, keyring: Keyring, view: StrengthView) -> StrengthOut:
    proposal = view.proposal
    found = proposal.strength if proposal else None
    return StrengthOut(
        **_run_out(tx, keyring, view).model_dump(),
        found=None if view.run.status is not WorkState.COMPLETE else found is not None,
        proposal=ProposedStrengthOut.of(found, proposal.origin) if found and proposal else None,
        decision=StrengthDecisionOut.of(view.decision) if view.decision else None,
    )


@router.post(
    "/interview/turns/{turn_id}/strength",
    status_code=202,
    response_model=StrengthRunOut,
    responses={
        200: {
            "model": StrengthRunOut,
            "description": "Already asked for: the turn's one strength run, in its state.",
        }
    },
    operation_id="submit_strength",
)
def post_strength(
    workspace_id: uuid.UUID,
    turn_id: uuid.UUID,
    body: SubmitStrength,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """Look for one overlooked strength in the answers this turn's decision saved, as one
    bounded run: at most one per turn (asking again answers 200 with its run), never on a
    turn the support screen answered, live only with the person's key within their spend
    limit, and the demo's scripted example in a demo workspace. The answer never holds the
    proposal (it is kept as the command's receipt); read it with GET."""

    def execute(tx: Tx) -> CommandResult:
        view, started = submit_strength(
            tx,
            caller.actor,
            workspace_id,
            turn_id,
            body,
            models=deps.models,
            keyring=deps.keyring,
            runtime_mode=deps.settings.runtime_mode,
            defaults=deps.spend_defaults,
            now=deps.clock(),
            hard=hard_filters(tx, workspace_id, deps.mapping_reviews, deps.assessment_packs),
            pack=deps.pack_targets,
        )
        answer = _run_out(tx, deps.keyring, view)
        return CommandResult(202 if started else 200, answer.model_dump(mode="json"), workspace_id)

    request = {
        "workspace_id": str(workspace_id),
        "turn_id": str(turn_id),
        **body.model_dump(mode="json"),
    }
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "submit_strength",
        fingerprint("submit_strength", request),
        execute,
    )
    location = f"/v1/workspaces/{workspace_id}/interview/turns/{turn_id}/strength"
    return JSONResponse(response, status_code=status, headers={"Location": location})


@router.get(
    "/interview/turns/{turn_id}/strength", response_model=StrengthOut, operation_id="get_strength"
)
def get_strength(
    workspace_id: uuid.UUID, turn_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> StrengthOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return _strength_out(
            tx, deps.keyring, turn_strength(tx, deps.keyring, workspace_id, turn_id)
        )


@router.post(
    "/interview/turns/{turn_id}/strength/decision",
    status_code=201,
    response_model=StrengthDecidedOut,
    operation_id="decide_strength",
)
def post_strength_decision(
    workspace_id: uuid.UUID,
    turn_id: uuid.UUID,
    body: DecideStrength,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """Confirm the proposed strength (recorded as the person's own claim, self-reported, with
    the verified quotation as its example) or decline it (nothing about the skill is
    recorded). Once per strength."""

    def execute(tx: Tx) -> CommandResult:
        decided, version = decide_strength(
            tx,
            caller.actor,
            workspace_id,
            turn_id,
            body,
            keyring=deps.keyring,
            now=deps.clock(),
        )
        answer = StrengthDecidedOut(
            decision=StrengthDecisionOut.of(decided), capability_version=version
        )
        return CommandResult(201, answer.model_dump(mode="json"), workspace_id)

    request = {
        "workspace_id": str(workspace_id),
        "turn_id": str(turn_id),
        **body.model_dump(mode="json"),
    }
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "decide_strength",
        fingerprint("decide_strength", request),
        execute,
    )
    return JSONResponse(response, status_code=status)
