"""The Routes chapter's facts (Task 14's backend half; ADR 0016 decisions 23 to 27), read from
a complete route solve: its comparison, its archive paged and viewed, and a chosen route.

Facts, never sentences (R11): codes, numbers, months and money, which the web words. Nothing
here re-ranks the archive or computes affordability: ranks are the search's, and a chosen
route's ledgers and stress cases are `check_route` on the solve's own input. A solve that is
not complete has none of these: it is refused naming its state, never an empty success."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query
from pydantic import BaseModel, ConfigDict, Field

from careerwright.api import pagination
from careerwright.api.deps import CallerDep, Deps
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.db import actor_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.planning.commands import current_inputs
from careerwright.planning.comparison import (
    DEFAULT_PAGE,
    MAX_PAGE,
    Comparison,
    RouteDetail,
    SchedulePage,
    ViewFilter,
    comparison,
    outdated,
    route_detail,
    schedule_page,
)
from careerwright.planning.compiler import MonthlyInput
from careerwright.planning.search import SearchResult
from careerwright.planning.solves import SolveView, solve_view

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}/planning/solves/{run_id}",
    responses=ERROR_RESPONSES,
    tags=["planning"],
)

Pins = Annotated[
    list[int] | None,
    Query(description="Archive indexes of pinned routes: kept whatever the view or projection."),
]


class Changed(BaseModel):
    """What changed since the solve read its inputs (STATE-06): its routes are shown as they
    were, beside this, until the person asks for a new solve. Nothing is invalidated here."""

    model_config = ConfigDict(frozen=True)

    planning_inputs: bool = Field(description="The planning inputs have a newer version.")
    profile: bool = Field(description="The profile (its limits among it) has a newer version.")


class ComparisonOut(Comparison):
    changed_since: Changed


class SchedulePageOut(SchedulePage):
    next_cursor: str | None = Field(description="Opaque: the next page, or null at the end.")  # type: ignore[assignment]


def _complete(view: SolveView) -> tuple[SearchResult, MonthlyInput]:
    if view.result is None:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "This route search has no result.",
            stage=ErrorStage.PLANNING,
            details={"reason": "solve_not_complete", "state": view.run.status.value},
        )
    if view.monthly is None:  # stored before its input was kept beside it
        raise outdated()
    return view.result, view.monthly


@router.get("/comparison", response_model=ComparisonOut, operation_id="get_route_comparison")
def get_comparison(
    workspace_id: uuid.UUID, run_id: uuid.UUID, caller: CallerDep, deps: Deps, pin: Pins = None
) -> ComparisonOut:
    """A complete solve's comparison: what leads, its cost definition and bounds, the points
    (a bounded projection with shown and total counts), the families and each point's named
    comparator."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        view = solve_view(tx, deps.keyring, workspace_id, run_id)
        result, monthly = _complete(view)
        now = current_inputs(tx, workspace_id)
    found = comparison(result, monthly, pinned=pin or [])
    return ComparisonOut(
        **dict(found),
        changed_since=Changed(
            planning_inputs=now.version != view.solve.inputs_version,
            profile=view.run.profile_version is not None
            and now.profile_version != view.run.profile_version,
        ),
    )


@router.get("/schedules", response_model=SchedulePageOut, operation_id="list_route_schedules")
def list_schedules(
    workspace_id: uuid.UUID,
    run_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE)] = DEFAULT_PAGE,
    min_months: Annotated[int | None, Query(ge=0)] = None,
    max_months: Annotated[int | None, Query(ge=0)] = None,
    min_cost_minor: int | None = None,
    max_cost_minor: int | None = None,
    layer: Annotated[int | None, Query(ge=1, le=3)] = None,
    family_id: str | None = None,
    rerank: Annotated[
        bool, Query(description="Explicit: layers within the view, beside the recorded ones.")
    ] = False,
    pin: Pins = None,
) -> SchedulePageOut:
    """Every retained schedule, paged in archive order and filtered by a view that never
    changes a recorded layer."""
    start = pagination.decode_int(cursor)
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        result, _ = _complete(solve_view(tx, deps.keyring, workspace_id, run_id))
    view = ViewFilter(
        min_months=min_months,
        max_months=max_months,
        min_cost_minor=min_cost_minor,
        max_cost_minor=max_cost_minor,
        layer=layer,
        family_id=family_id,
    )
    page = schedule_page(result, view, cursor=start, limit=limit, rerank=rerank, pinned=pin or [])
    following = page.next_cursor
    return SchedulePageOut(
        **{
            **dict(page),
            "next_cursor": pagination.encode(following) if following is not None else None,
        }
    )


@router.get("/schedules/{index}", response_model=RouteDetail, operation_id="get_route_schedule")
def get_schedule(
    workspace_id: uuid.UUID,
    run_id: uuid.UUID,
    index: Annotated[int, Path(ge=0)],
    caller: CallerDep,
    deps: Deps,
) -> RouteDetail:
    """A chosen route: its cost parts, monthly table, steps, gates, waits and milestones, and
    its stress cases apart, rechecked on the solve's own input."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        result, monthly = _complete(solve_view(tx, deps.keyring, workspace_id, run_id))
    return route_detail(result, monthly, index)
