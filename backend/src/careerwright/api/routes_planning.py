"""Planning endpoints (S5.1-S5.4; ADR 0013): each target's options from the option pack as the
planning model reads them, labelled with the pack's date and every record's review state; and
the person's own planning inputs (Task 12a, ADR 0013 decision 11 as amended), read with what a
solve still needs and written with an expected version and an Idempotency-Key.

Facts, never sentences (R11): codes, numbers and money; the web words them. Every input is the
person's direct entry: no model fills one."""

import uuid
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from careerwright.api.capability_schemas import PackLabel
from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.capability.commands import capability_view
from careerwright.db import Tx, actor_transaction
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.money import Money
from careerwright.planning.commands import InputsView, WriteInputs, current_inputs, write_inputs
from careerwright.planning.inputs import Need, PlanningInputsDocument
from careerwright.planning.pack import TargetOptions, target_options
from careerwright.vocabulary import DataMode

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
    field cited beside its span or unknown with its reason."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = capability_view(tx, workspace_id, deps.capability)
    return OptionsOut(
        profile_version=view.profile_version,
        synthetic=view.synthetic,
        data_mode=view.data_mode,
        pack=PackLabel.of(deps.capability),
        targets=[target_options(m, deps.capability.pack) for m in view.matrices],
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
            tx, caller.actor, workspace_id, body, data=deps.capability, now=deps.clock()
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
