"""Planning endpoints (S5.1, S5.2; ADR 0013): each target's options from the option pack as
the planning model reads them, labelled with the pack's date and every record's review state.
Read-only: the person's planning assumptions are confirmed at the option checkpoint
(Task 12), which owns their persistence."""

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
