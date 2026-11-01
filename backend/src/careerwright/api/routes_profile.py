"""Profile endpoints: read the current version and its history; write with an expected version."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import JSONResponse

from careerwright.api.catalogue_schemas import ProvisionalConceptOut, ProvisionalConceptPage
from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES, correlation_id, error_body, error_status
from careerwright.api.interview_schemas import (
    ProfileRefusedOut,
    ProfileSavedOut,
    SupportNoteOut,
    TitleDetailsListOut,
    TitleDetailsOut,
    TitleDetailsRefusedOut,
    TitleDetailsSavedOut,
)
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
from careerwright.profile import store, title_details
from careerwright.profile.commands import (
    RevertProfile,
    current_profile,
    entered_words,
    revert_profile,
    write_profile,
)
from careerwright.profile.concepts import RegisterProvisionalConcept, register_provisional_concept
from careerwright.profile.document import FIELD_NAMES
from careerwright.profile.safety import has_risk_stem
from careerwright.profile.title_details import SetTitleDetails

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
    response_model=ProfileSavedOut,
    status_code=201,
    responses={
        200: {"model": ProfileSavedOut, "description": "No field changed; no new version."},
        "4XX": {"model": ProfileRefusedOut, "description": "Typed error envelope"},
        "5XX": {"model": ProfileRefusedOut, "description": "Typed error envelope"},
    },
)
def put_profile(
    workspace_id: uuid.UUID,
    body: ProfileWriteIn,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
    http: Request,
) -> JSONResponse:
    """A direct edit in What we know. Its new entries go through the support screen
    (`careerwright.profile.safety`), as a message does: an edit that triggers it is saved as
    usual, with the calm support panel beside the answer, or beside its refusal."""
    # Screened before anything can refuse it, so a refusal shows the panel too; derived from
    # the request every time and never stored, not even in the receipt.
    answers = {name: getattr(body.profile, name) for name in FIELD_NAMES}
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        entered = entered_words(tx, workspace_id, body.expected_version, answers)
    support = any(has_risk_stem(words) for words in entered)

    def execute(tx: Tx) -> CommandResult:
        view, created = write_profile(
            tx,
            caller.actor,
            workspace_id,
            body.expected_version,
            body.profile,
            deps.clock(),
            deps.pack_targets,
        )
        return CommandResult(
            201 if created else 200, ProfileOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    try:
        status, response = run_idempotent(
            deps.engine,
            caller.actor.actor_id,
            key,
            "write_profile",
            fingerprint("write_profile", request),
            execute,
        )
    except CareerwrightError as error:
        if not support:
            raise
        refused = ProfileRefusedOut(
            error=error_body(error, correlation_id(http)),
            support_note=SupportNoteOut.beside_an_entry(saved=False),
        )
        return JSONResponse(refused.model_dump(mode="json"), status_code=error_status(error))
    saved = ProfileSavedOut.saved(ProfileOut.model_validate(response), support=support)
    return JSONResponse(saved.model_dump(mode="json"), status_code=status)


@router.get("/profile/titles", response_model=TitleDetailsListOut, operation_id="get_title_details")
def get_title_details(
    workspace_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> TitleDetailsListOut:
    """The person's own details beside their role and each target: seniority and industry,
    each optional (null: not given), and the skills ESCO lists for the work they marked not
    part of their job. Matching ignores them."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        version, views = title_details.current_title_details(tx, workspace_id)
    return TitleDetailsListOut(
        profile_version=version, titles=[TitleDetailsOut.of(v) for v in views]
    )


@router.put(
    "/profile/titles",
    response_model=TitleDetailsSavedOut,
    status_code=201,
    responses={
        200: {"model": TitleDetailsSavedOut, "description": "Nothing changed; no new version."},
        "4XX": {"model": TitleDetailsRefusedOut, "description": "Typed error envelope"},
        "5XX": {"model": TitleDetailsRefusedOut, "description": "Typed error envelope"},
    },
    operation_id="put_title_details",
)
def put_title_details(
    workspace_id: uuid.UUID,
    body: SetTitleDetails,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
    http: Request,
) -> JSONResponse:
    """Save the details beside one of the person's titles. The words it enters go through the
    support screen, as What we know's direct entries do: saved as usual, with the calm panel
    beside the answer or its refusal, derived from the request and never stored."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        entered = title_details.entered_words(tx, workspace_id, body)
    support = any(has_risk_stem(words) for words in entered)

    def execute(tx: Tx) -> CommandResult:
        view, created = title_details.set_title_details(
            tx, caller.actor, workspace_id, body, deps.pack_targets
        )
        return CommandResult(
            201 if created else 200, TitleDetailsOut.of(view).model_dump(mode="json"), workspace_id
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    try:
        status, response = run_idempotent(
            deps.engine,
            caller.actor.actor_id,
            key,
            "set_title_details",
            fingerprint("set_title_details", request),
            execute,
        )
    except CareerwrightError as error:
        if not support:
            raise
        refused = TitleDetailsRefusedOut(
            error=error_body(error, correlation_id(http)),
            support_note=SupportNoteOut.beside_an_entry(saved=False),
        )
        return JSONResponse(refused.model_dump(mode="json"), status_code=error_status(error))
    saved = TitleDetailsSavedOut.saved(TitleDetailsOut.model_validate(response), support=support)
    return JSONResponse(saved.model_dump(mode="json"), status_code=status)


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
        view, created = revert_profile(tx, caller.actor, workspace_id, body, deps.pack_targets)
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
