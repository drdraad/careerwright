"""Planning endpoints (S5.1, S5.2; ADR 0013): each target's options from the option pack as
the planning model reads them, labelled with the pack's date and every record's review state.

Read-only. What has no store yet is every input the person supplies (ADR 0013 decision 11):
the baseline, the continuation scenario, opening cash, living costs, the reserve, the three
hard limits and the deficit cap, weekly availability, commitments, existing debts, the
objective basis, the delay months, and, per variant, the work pattern, wage, funding statuses
and entry confirmation. The option checkpoint (Task 12) confirms them and owns their
persistence; until then a variant's support is "none confirmed yet" and its entry
confirmation null."""

import uuid

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from nessa.api.capability_schemas import PackLabel
from nessa.api.deps import CallerDep, Deps
from nessa.api.envelope import ERROR_RESPONSES
from nessa.capability.commands import capability_view
from nessa.db import actor_transaction
from nessa.planning.pack import TargetOptions, target_options
from nessa.vocabulary import DataMode

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
