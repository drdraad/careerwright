"""Planning endpoints (S5.1-S5.4; ADR 0013): each target's options from the option pack as the
planning model reads them, labelled with the pack's date and every record's review state; the
person's own planning inputs (Task 12a, ADR 0013 decision 11 as amended), read with what a
solve still needs and written with an expected version and an Idempotency-Key; and route
solves (Task 13b, ADR 0016's amendment): one target's route search as a run, asked for with the
inputs version the person saw and an Idempotency-Key, read with its stage and, once complete,
its result. `POST .../runs/{run_id}/cancel` cancels one.

Facts, never sentences (R11): codes, numbers and money; the web words them. Every input is the
person's direct entry: no model fills one."""

import uuid
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from careerwright.api.capability_schemas import PackLabel
from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.api.routes_runs import run_out
from careerwright.api.schemas import RunOut
from careerwright.capability.commands import capability_view
from careerwright.db import Tx, actor_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity.keyring import Keyring
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.identity.workspaces import visible_workspace
from careerwright.money import Money
from careerwright.planning.checkpoint import TargetCheckpoint
from careerwright.planning.commands import (
    InputsView,
    WriteInputs,
    checkpoint_view,
    current_inputs,
    target_catalogues,
    write_inputs,
)
from careerwright.planning.comparison import ResultCode, result_code
from careerwright.planning.inputs import (
    BaselineInput,
    ContinuationInput,
    Need,
    PlanningInputsDocument,
)
from careerwright.planning.option_texts import PasteOptionText, option_text, paste_option_text
from careerwright.planning.pack import TargetOptions
from careerwright.planning.search import M0SearchLimits, SearchResult
from careerwright.planning.solve_records import SolveStage
from careerwright.planning.solves import SolveRequest, SolveView, request_solve, solve_view
from careerwright.profile.document import WorkStatus
from careerwright.vocabulary import DataMode, WorkState

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}/planning",
    responses=ERROR_RESPONSES,
    tags=["planning"],
)


class OptionsOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    profile_version: int
    synthetic: bool
    data_mode: DataMode
    pack: PackLabel
    targets: list[TargetOptions]


class PlanningInputsOut(BaseModel):
    """The person's stored planning inputs, with the profile's two spending caps beside them
    (read-only here: they are the profile's answers) and what a solve still needs."""

    model_config = ConfigDict(frozen=True)

    version: int  # 0: nothing stated yet
    inputs: PlanningInputsDocument
    created_by: uuid.UUID | None
    created_at: datetime | None
    profile_version: int
    direct_spend_cap: Money | None  # null: not stated, never "no limit"
    monthly_payment_cap: Money | None
    needs: list[Need]
    synthetic: bool
    data_mode: DataMode

    @classmethod
    def of(cls, view: InputsView) -> "PlanningInputsOut":
        return cls(
            version=view.version,
            inputs=view.document,
            created_by=view.created_by,
            created_at=view.created_at,
            profile_version=view.profile_version,
            direct_spend_cap=view.caps.direct_spend_cap,
            monthly_payment_cap=view.caps.monthly_payment_cap,
            needs=view.needs,
            synthetic=view.synthetic,
            data_mode=view.data_mode,
        )


@router.get("/options", response_model=OptionsOut, operation_id="list_planning_options")
def get_options(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> OptionsOut:
    """Each target's options: concepts, dated offerings, payment plans and funding, every
    field cited beside its span or unknown with its reason; the options the person added
    themselves beside the pack's, each `proposed` and marked as theirs."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = capability_view(tx, workspace_id, deps.capability)
        own = current_inputs(tx, workspace_id).document.own_options
        found = target_catalogues(
            tx, deps.keyring, workspace_id, view.matrices, own, deps.capability
        )
    return OptionsOut(
        profile_version=view.profile_version,
        synthetic=view.synthetic,
        data_mode=view.data_mode,
        pack=PackLabel.of(deps.capability),
        targets=[options for _, options in found],
    )


@router.get("/inputs", response_model=PlanningInputsOut, operation_id="get_planning_inputs")
def get_inputs(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> PlanningInputsOut:
    """The person's planning inputs and what a solve still needs."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return PlanningInputsOut.of(current_inputs(tx, workspace_id))


@router.put(
    "/inputs",
    response_model=PlanningInputsOut,
    status_code=201,
    responses={200: {"model": PlanningInputsOut, "description": "Nothing changed."}},
    operation_id="write_planning_inputs",
)
def put_inputs(
    workspace_id: uuid.UUID,
    body: WriteInputs,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """Replace the person's planning inputs as a new version; a stale version is refused."""

    def execute(tx: Tx) -> CommandResult:
        view, created = write_inputs(
            tx,
            caller.actor,
            workspace_id,
            body,
            data=deps.capability,
            keyring=deps.keyring,
            now=deps.clock(),
        )
        return CommandResult(
            201 if created else 200,
            PlanningInputsOut.of(view).model_dump(mode="json"),
            workspace_id,
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "write_planning_inputs",
        fingerprint("write_planning_inputs", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


# The review checkpoint and options the person adds (Task 12b).

# What the monthly payment cap holds, as the checker applies it: every payment for the change
# and every existing debt repayment in the month (spec section 12, P_m + R_m <= M_m; session 2,
# D15 yes). A fact the web words beside the cap's question.
PaymentCapBasis = Literal["payments_and_debt_repayments"]


class CheckpointOut(BaseModel):
    """The Options chapter's review checkpoint: for each target, its options with the facts the
    route search still lacks, what the person supplied, entry requirements beside their
    qualifications, eligibility conditions, age rules (never applied) and the scope against
    the model's bounds; and the planning inputs a solve still needs."""

    model_config = ConfigDict(frozen=True)

    inputs_version: int
    profile_version: int
    synthetic: bool
    data_mode: DataMode
    pack: PackLabel
    needs: list[Need]
    direct_spend_cap: Money | None  # the profile's: null, not stated, never "no limit"
    monthly_payment_cap: Money | None
    payment_cap_basis: PaymentCapBasis = "payments_and_debt_repayments"
    work_status: WorkStatus | None = Field(description="The profile's answer; null: not given.")
    baseline: BaselineInput | None
    continuation: ContinuationInput | None
    not_working: bool | None = Field(
        description="The continuation is the person's own 0 hours and £0 a month (a stated "
        "figure, never an unknown read as zero); null while it is not stated."
    )
    targets: list[TargetCheckpoint]


@router.get("/checkpoint", response_model=CheckpointOut, operation_id="get_option_checkpoint")
def get_checkpoint(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> CheckpointOut:
    """The review checkpoint, read with the planning inputs' version for the next write."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = checkpoint_view(tx, deps.keyring, workspace_id, deps.capability)
    inputs, document = view.inputs, view.inputs.document
    continuation = document.continuation
    return CheckpointOut(
        inputs_version=inputs.version,
        profile_version=inputs.profile_version,
        synthetic=inputs.synthetic,
        data_mode=inputs.data_mode,
        pack=PackLabel.of(deps.capability),
        needs=inputs.needs,
        direct_spend_cap=inputs.caps.direct_spend_cap,
        monthly_payment_cap=inputs.caps.monthly_payment_cap,
        work_status=view.work_status,
        baseline=document.baseline,
        continuation=continuation,
        not_working=continuation.hours_per_week == 0 and continuation.net_income.minor_units == 0
        if continuation is not None
        else None,
        targets=view.targets,
    )


class OptionTextRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    text_id: uuid.UUID
    sha256: str


class OptionTextOut(OptionTextRef):
    """A pasted text as it was kept (third parties' contact details removed): spans of an
    option are chosen in these words, in UTF-16 code units."""

    text: str
    source_url: str | None


@router.post(
    "/option-texts",
    status_code=201,
    response_model=OptionTextRef,
    operation_id="paste_option_text",
)
def post_option_text(
    workspace_id: uuid.UUID,
    body: PasteOptionText,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """Keep a course or funding page's text the person pasted for an option they add: its
    own input, never fetched. Read it back with `GET .../option-texts/{text_id}`."""

    def execute(tx: Tx) -> CommandResult:
        text_id = paste_option_text(tx, caller.actor, workspace_id, body, keyring=deps.keyring)
        kept = option_text(tx, deps.keyring, workspace_id, text_id)
        if kept is None:  # just written in this transaction
            raise CareerwrightError(
                ErrorCode.INTERNAL_ERROR, "The text was not kept.", stage=ErrorStage.PLANNING
            )
        out = OptionTextRef(text_id=text_id, sha256=kept.sha256)
        return CommandResult(201, out.model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "paste_option_text",
        fingerprint("paste_option_text", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/option-texts/{text_id}", response_model=OptionTextOut, operation_id="get_option_text")
def get_option_text(
    workspace_id: uuid.UUID, text_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> OptionTextOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        kept = option_text(tx, deps.keyring, workspace_id, text_id)
    if kept is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such pasted text.", stage=ErrorStage.PLANNING
        )
    return OptionTextOut(
        text_id=kept.text_id, sha256=kept.sha256, text=kept.text, source_url=kept.source_url
    )


# Route solves (Task 13b).


class SolveOut(BaseModel):
    """A route solve: its run, what it was asked for and read, where it is, and once its run
    is complete its result. A queued, running, failed or cancelled solve has no result."""

    model_config = ConfigDict(frozen=True)

    run: RunOut
    solve_id: str = Field(description="The same snapshot under the same limits: one solve.")
    target_title: str
    inputs_version: int = Field(description="The planning inputs version the snapshot read.")
    capability_version: int = Field(description="The evidence version the snapshot read.")
    input_version: str = Field(description="The monthly input's own version.")
    planning_start: date
    horizon_months: int
    objective_basis: Literal["economic", "direct_spending"]
    limits: M0SearchLimits
    rank_seconds: int = Field(description="The rank stage's own limit.")
    algorithm_version: str
    pruning_version: str
    stage: SolveStage | None = Field(
        description="Where a running solve is: its search, then its rank stage. Null before "
        "it starts and once it has ended."
    )
    attempts: int = Field(
        description="Its executions: more than one, it started again after a crash."
    )
    code: ResultCode | None
    result: SearchResult | None


def solve_out(tx: Tx, keyring: Keyring, view: SolveView) -> SolveOut:
    solve, latest = view.solve, view.attempts[-1] if view.attempts else None
    running = view.run.status is WorkState.RUNNING and latest is not None and not latest.outcome
    return SolveOut(
        run=run_out(tx, keyring, view.run),
        solve_id=solve.solve_id,
        target_title=solve.target_title,
        inputs_version=solve.inputs_version,
        capability_version=solve.capability_version,
        input_version=solve.input_version,
        planning_start=solve.planning_start,
        horizon_months=solve.horizon_months,
        objective_basis=solve.objective_basis,
        limits=solve.limits,
        rank_seconds=solve.rank_seconds,
        algorithm_version=solve.algorithm_version,
        pruning_version=solve.pruning_version,
        stage=latest.stage if running and latest is not None else None,
        attempts=len(view.attempts),
        code=result_code(view.result) if view.result is not None else None,
        result=view.result,
    )


@router.post(
    "/solves",
    status_code=202,
    response_model=SolveOut,
    responses={200: {"model": SolveOut, "description": "The same solve is under way: joined."}},
    operation_id="request_route_solve",
)
def post_solve(
    workspace_id: uuid.UUID,
    body: SolveRequest,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    """Search one target's routes as a run, from a snapshot of the planning inputs at the
    version the person saw: 202 with the new solve, or 200 with the same one under way."""

    def execute(tx: Tx) -> CommandResult:
        view, started = request_solve(
            tx,
            caller.actor,
            workspace_id,
            body,
            data=deps.capability,
            keyring=deps.keyring,
            runtime_mode=deps.settings.runtime_mode,
            now=deps.clock(),
        )
        return CommandResult(
            202 if started else 200,
            solve_out(tx, deps.keyring, view).model_dump(mode="json"),
            workspace_id,
        )

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "request_route_solve",
        fingerprint("request_route_solve", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/solves/{run_id}", response_model=SolveOut, operation_id="get_route_solve")
def get_solve(
    workspace_id: uuid.UUID, run_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> SolveOut:
    """A route solve, its stage while it runs, and its result once complete."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return solve_out(tx, deps.keyring, solve_view(tx, deps.keyring, workspace_id, run_id))
