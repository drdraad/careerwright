"""Chosen plan versions and their portable JSON and calendar views."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.db import Tx, actor_transaction
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.planning.calendar import calendar_text
from careerwright.planning.own_options import OWN_PREFIX
from careerwright.planning.plan_records import ChoosePlan, PlanSnapshot, ProgressUpdate
from careerwright.planning.plans import (
    PlanChanges,
    PlanHistoryItem,
    PlanRevisionPreview,
    choose_plan,
    plan_changes,
    plan_history,
    record_progress,
    revision_preview,
    selected_plan,
)

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}/planning/plans",
    responses=ERROR_RESPONSES,
    tags=["planning"],
)


@router.post("", status_code=201, response_model=PlanSnapshot, operation_id="choose_plan")
def post_plan(
    workspace_id: uuid.UUID,
    body: ChoosePlan,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        snapshot = choose_plan(
            tx,
            caller.actor,
            workspace_id,
            body,
            keyring=deps.keyring,
            data=deps.capability,
            now=deps.clock(),
        )
        return CommandResult(201, snapshot.model_dump(mode="json"), workspace_id)

    request = {
        "workspace_id": str(workspace_id),
        **body.model_dump(mode="json", exclude_defaults=True),
    }
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "choose_plan",
        fingerprint("choose_plan", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/current", response_model=PlanSnapshot, operation_id="get_current_plan")
def get_current_plan(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> PlanSnapshot:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return selected_plan(tx, workspace_id, now=deps.clock())


@router.get("/history", response_model=list[PlanHistoryItem], operation_id="list_plan_versions")
def get_plan_history(
    workspace_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> list[PlanHistoryItem]:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return plan_history(tx, workspace_id)


@router.get("/changes", response_model=PlanChanges, operation_id="get_plan_changes")
def get_plan_changes(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> PlanChanges:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return plan_changes(tx, workspace_id, deps.keyring, deps.capability)


@router.get(
    "/revision-preview", response_model=PlanRevisionPreview, operation_id="preview_plan_revision"
)
def get_revision_preview(
    workspace_id: uuid.UUID,
    solve_run_id: uuid.UUID,
    schedule_index: Annotated[int, Query(ge=0)],
    caller: CallerDep,
    deps: Deps,
) -> PlanRevisionPreview:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return revision_preview(
            tx,
            workspace_id,
            solve_run_id,
            schedule_index,
            keyring=deps.keyring,
            data=deps.capability,
        )


@router.post(
    "/progress", status_code=201, response_model=PlanSnapshot, operation_id="record_plan_progress"
)
def post_plan_progress(
    workspace_id: uuid.UUID,
    body: ProgressUpdate,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        snapshot = record_progress(tx, caller.actor, workspace_id, body, now=deps.clock())
        return CommandResult(201, snapshot.model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "record_plan_progress",
        fingerprint("record_plan_progress", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/{version}", response_model=PlanSnapshot, operation_id="get_plan_version")
def get_plan_version(
    workspace_id: uuid.UUID, version: int, caller: CallerDep, deps: Deps
) -> PlanSnapshot:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return selected_plan(tx, workspace_id, version, now=deps.clock())


def export_data(
    snapshot: PlanSnapshot, *, omit_financial_detail: bool, omit_sensitive_detail: bool
) -> dict[str, Any]:
    """A derivative of the stored snapshot: selective omission never changes the saved plan."""
    data = snapshot.model_dump(mode="json")
    route = data["route"]
    replan = route["basis"].get("replan")
    if omit_financial_detail:
        schedule, basis = route["schedule"], route["basis"]
        data["route"] = route = {
            "label": route["label"],
            "basis": {
                name: basis[name]
                for name in (
                    "objective_basis",
                    "planning_start",
                    "horizon_months",
                    "currency",
                    "scenario",
                    "synthetic",
                )
            },
            "schedule": {
                name: schedule[name]
                for name in (
                    "index",
                    "route",
                    "family_id",
                    "point_id",
                    "months_to_readiness",
                    "readiness_month",
                    "verdict",
                    "qualifications",
                    "conditions",
                    "layer",
                )
            },
            "steps": [
                {
                    name: step[name]
                    for name in (
                        "variant_id",
                        "concept_id",
                        "offering_id",
                        "kind",
                        "title",
                        "provider",
                        "start_date",
                        "finish_date",
                        "start_month",
                        "finish_month",
                        "usable_month",
                        "active_months",
                        "application_deadline",
                        "prerequisites",
                        "grants",
                        "records",
                        "as_of",
                        "added_by_person",
                        "synthetic",
                        "qualified_by",
                        "sources",
                    )
                }
                for step in route["steps"]
            ],
            "gates": route["gates"],
            "waits": route["waits"],
            "milestones": route["milestones"],
        }
        if basis.get("replan") is not None:
            route["basis"]["replan"] = {"from_plan_version": basis["replan"]["from_plan_version"]}
    if omit_sensitive_detail:
        data.pop("selected_by")
        own_variants = [step["variant_id"] for step in route["steps"] if step["added_by_person"]]
        own_variants.extend(
            activity["variant_id"]
            for activity in data["progress"]["activity"]
            if activity["variant_id"] is not None and activity["variant_id"].startswith(OWN_PREFIX)
        )
        if replan is not None:
            own_variants.extend(
                variant_id
                for variant_id in [
                    *replan["completed_variants"],
                    *replan["excluded_variants"],
                    *(payment["variant_id"] for payment in replan["remaining_payments"]),
                ]
                if variant_id.startswith(OWN_PREFIX)
            )
        own_ids = {
            variant_id: f"redacted-option-{index}"
            for index, variant_id in enumerate(dict.fromkeys(own_variants), 1)
        }
        for step in route["steps"]:
            step.pop("supplied", None)
            if step["added_by_person"]:
                step.update(
                    title="Your option",
                    provider=None,
                    prerequisites=[],
                    grants=[],
                    records=[],
                    sources=[],
                )
        for event in data["events"]:
            if event["variant_id"] in own_ids:
                event["title"] = "Your option"
        if data["next_action"] is not None and data["next_action"]["variant_id"] in own_ids:
            data["next_action"]["title"] = "Your option"
        for activity in data["progress"]["activity"]:
            if activity["variant_id"] in own_ids:
                activity["step_title"] = "Your option"
    if omit_sensitive_detail or omit_financial_detail:
        for step in route["steps"]:
            for source in step["sources"]:
                source.pop("excerpt")
    if omit_sensitive_detail and own_ids:
        data = _replace_own_ids(data, own_ids)
    return data


def _replace_own_ids(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_own_ids(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_own_ids(item, replacements) for item in value]
    if isinstance(value, str):
        for original, replacement in sorted(replacements.items(), key=lambda item: -len(item[0])):
            value = value.replace(original, replacement)
    return value


@router.get("/{version}/export.json", operation_id="export_plan_json")
def export_plan_json(
    workspace_id: uuid.UUID,
    version: int,
    caller: CallerDep,
    deps: Deps,
    omit_financial_detail: bool = False,
    omit_sensitive_detail: bool = False,
) -> JSONResponse:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        snapshot = selected_plan(tx, workspace_id, version, now=deps.clock())
    return JSONResponse(
        export_data(
            snapshot,
            omit_financial_detail=omit_financial_detail,
            omit_sensitive_detail=omit_sensitive_detail,
        ),
        headers={
            "Content-Disposition": f'attachment; filename="careerwright-plan-v{version}.json"'
        },
    )


@router.get("/{version}/calendar.ics", operation_id="export_plan_calendar")
def export_plan_calendar(
    workspace_id: uuid.UUID, version: int, caller: CallerDep, deps: Deps
) -> Response:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        snapshot = selected_plan(tx, workspace_id, version)
    return Response(
        calendar_text(snapshot),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="careerwright-plan-v{version}.ics"'},
    )
