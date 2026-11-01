"""Capability endpoints (S4.1-S4.6): read the provisional matrices, the combined question
graph and readiness, and the Skills chapter's facts (Task 10); record skill evidence,
requirement statements, matrix edits and the person's chosen advert spans; stop or resume the
questions. Every write takes an expected version and an Idempotency-Key."""

import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from careerwright.api.capability_schemas import (
    CapabilityChangeOut,
    MatricesOut,
    PackLabel,
    QuestionsOut,
    ReadinessOut,
    ReferenceLabel,
    SkillsOut,
)
from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.capability.commands import (
    EditRow,
    RecordEvidence,
    RecordStatement,
    SetQuestions,
    capability_view,
    edit_row,
    questions,
    readiness,
    record_evidence,
    record_statement,
    set_questions,
)
from careerwright.capability.skills_commands import (
    SelectAdvertSpans,
    select_advert_spans,
    skills_view,
)
from careerwright.db import Tx, actor_transaction
from careerwright.identity.receipts import CommandResult, Execute, fingerprint, run_idempotent

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}/capability",
    responses=ERROR_RESPONSES,
    tags=["capability"],
)


@router.get("/matrices", response_model=MatricesOut, operation_id="list_capability_matrices")
def get_matrices(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> MatricesOut:
    """Each target's provisional matrix, labelled with the pack's date and review states."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = capability_view(tx, workspace_id, deps.capability)
    return MatricesOut(
        version=view.version,
        questions_stopped=view.questions_stopped,
        profile_version=view.profile_version,
        synthetic=view.synthetic,
        data_mode=view.data_mode,
        pack=PackLabel.of(deps.capability),
        reference=ReferenceLabel.of(deps.capability),
        matrices=view.matrices,
    )


@router.get("/questions", response_model=QuestionsOut, operation_id="get_capability_questions")
def get_questions(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> QuestionsOut:
    """One question graph across the targets: gates first, then decision-impact order."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = capability_view(tx, workspace_id, deps.capability)
    return QuestionsOut(
        version=view.version,
        profile_version=view.profile_version,
        synthetic=view.synthetic,
        data_mode=view.data_mode,
        pack=PackLabel.of(deps.capability),
        reference=ReferenceLabel.of(deps.capability),
        graph=questions(view),
    )


@router.get("/readiness", response_model=ReadinessOut, operation_id="get_capability_readiness")
def get_readiness(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> ReadinessOut:
    """Readiness, gaps and abstract actions for each target, with the versions they rest on."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = capability_view(tx, workspace_id, deps.capability)
    return ReadinessOut(
        version=view.version,
        profile_version=view.profile_version,
        synthetic=view.synthetic,
        data_mode=view.data_mode,
        pack=PackLabel.of(deps.capability),
        reference=ReferenceLabel.of(deps.capability),
        assessments=readiness(view, deps.capability),
    )


@router.get("/skills", response_model=SkillsOut, operation_id="get_skills")
def get_skills(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> SkillsOut:
    """The Skills chapter's facts for each target: what ESCO lists for its occupation (with the
    person's "not part of my job" marks), their own examples and the parts they chose, what
    the target asks with their qualifications beside it, and readiness only where a reviewed
    rubric exists; the evidence questions shared across targets; and the usual skills of the
    person's role, absent without a role."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = skills_view(tx, workspace_id, deps.capability, deps.keyring)
    return SkillsOut.of(view, deps.capability)


def _write(
    deps: Deps,
    caller: CallerDep,
    key: uuid.UUID,
    workspace_id: uuid.UUID,
    command: str,
    body: dict[str, object],
    execute: Execute,
) -> JSONResponse:
    request = {"workspace_id": str(workspace_id), **body}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        command,
        fingerprint(command, request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.post(
    "/evidence",
    status_code=201,
    response_model=CapabilityChangeOut,
    operation_id="record_skill_evidence",
)
def post_evidence(
    workspace_id: uuid.UUID,
    body: RecordEvidence,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """An answer about a skill, against one rubric's anchors: shared across targets."""

    def execute(tx: Tx) -> CommandResult:
        change = record_evidence(
            tx, caller.actor, workspace_id, body, data=deps.capability, now=deps.clock()
        )
        return CommandResult(
            201, CapabilityChangeOut.of(change).model_dump(mode="json"), workspace_id
        )

    return _write(
        deps,
        caller,
        key,
        workspace_id,
        "record_skill_evidence",
        body.model_dump(mode="json"),
        execute,
    )


@router.post(
    "/statements",
    status_code=201,
    response_model=CapabilityChangeOut,
    operation_id="record_requirement_statement",
)
def post_statement(
    workspace_id: uuid.UUID,
    body: RecordStatement,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """Whether the person holds a credential, experience or eligibility requirement."""

    def execute(tx: Tx) -> CommandResult:
        change = record_statement(
            tx, caller.actor, workspace_id, body, data=deps.capability, now=deps.clock()
        )
        return CommandResult(
            201, CapabilityChangeOut.of(change).model_dump(mode="json"), workspace_id
        )

    return _write(
        deps,
        caller,
        key,
        workspace_id,
        "record_requirement_statement",
        body.model_dump(mode="json"),
        execute,
    )


@router.post(
    "/edits",
    status_code=201,
    response_model=CapabilityChangeOut,
    responses={200: {"model": CapabilityChangeOut, "description": "Nothing changed."}},
    operation_id="edit_matrix_row",
)
def post_edit(
    workspace_id: uuid.UUID, body: EditRow, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    """Set a row's importance or challenge its source. A protected gate is never demoted
    (`PROTECTED_GATE`); relaxing an employer's requirement needs the warning acknowledged."""

    def execute(tx: Tx) -> CommandResult:
        change = edit_row(
            tx, caller.actor, workspace_id, body, data=deps.capability, now=deps.clock()
        )
        status = 201 if change.recorded_id is not None else 200
        return CommandResult(
            status, CapabilityChangeOut.of(change).model_dump(mode="json"), workspace_id
        )

    return _write(
        deps, caller, key, workspace_id, "edit_matrix_row", body.model_dump(mode="json"), execute
    )


@router.post(
    "/advert-spans",
    status_code=201,
    response_model=CapabilityChangeOut,
    operation_id="select_advert_spans",
)
def post_advert_spans(
    workspace_id: uuid.UUID,
    body: SelectAdvertSpans,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """The parts of one of the person's own example adverts that say what a target asks for
    (offsets into its text; an empty list clears them). No model run."""

    def execute(tx: Tx) -> CommandResult:
        change = select_advert_spans(
            tx, caller.actor, workspace_id, body, keyring=deps.keyring, now=deps.clock()
        )
        return CommandResult(
            201, CapabilityChangeOut.of(change).model_dump(mode="json"), workspace_id
        )

    return _write(
        deps,
        caller,
        key,
        workspace_id,
        "select_advert_spans",
        body.model_dump(mode="json"),
        execute,
    )


@router.put(
    "/questions/state",
    response_model=CapabilityChangeOut,
    operation_id="set_capability_questions",
)
def put_questions_state(
    workspace_id: uuid.UUID, body: SetQuestions, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    """Stop or pause the questions (every open question is kept), or resume them."""

    def execute(tx: Tx) -> CommandResult:
        change = set_questions(tx, caller.actor, workspace_id, body)
        return CommandResult(
            200, CapabilityChangeOut.of(change).model_dump(mode="json"), workspace_id
        )

    return _write(
        deps,
        caller,
        key,
        workspace_id,
        "set_capability_questions",
        body.model_dump(mode="json"),
        execute,
    )
