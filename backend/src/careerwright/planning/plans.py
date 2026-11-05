"""Choose and read a route as a durable plan without changing its source solve."""

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict

from careerwright.capability.commands import CapabilityData, CapabilityView, capability_view
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence.jobs import title_key
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.workspaces import visible_workspace
from careerwright.money import Money, SignedMoney
from careerwright.planning import store
from careerwright.planning.catalogue import CatalogueLabel
from careerwright.planning.commands import InputsView, current_inputs, target_catalogues
from careerwright.planning.comparison import ComparisonBasis, RouteDetail, outdated, route_detail
from careerwright.planning.plan_records import (
    ChoosePlan,
    PlanActivity,
    PlanEvent,
    PlanProgress,
    PlanSearch,
    PlanSnapshot,
    PlanSource,
    ProgressUpdate,
    events_for,
    review_event,
)
from careerwright.planning.solves import SolveView, solve_view


def selected_plan(
    tx: Tx, workspace_id: uuid.UUID, version: int | None = None, *, now: datetime | None = None
) -> PlanSnapshot:
    visible_workspace(tx, workspace_id)
    found = store.plan(tx, workspace_id, version)
    if found is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No chosen plan at this version.", stage=ErrorStage.PLANNING
        )
    # The saved version is sealed; only its time-dependent read projection changes.
    return (
        found.model_copy(update={"next_action": _next_action(found.events, found.progress, now)})
        if now
        else found
    )


def _next_action(
    events: list[PlanEvent], progress: PlanProgress, now: datetime
) -> PlanEvent | None:
    today = now.astimezone(ZoneInfo("Europe/London")).date()
    if progress.rest_until is not None and progress.rest_until >= today:
        return None
    review = review_event(progress)
    upcoming = [
        event
        for event in [*events, *([review] if review else [])]
        if event.on >= today and event.variant_id not in progress.completed_steps
    ]
    return min(
        upcoming, key=lambda event: (event.on, event.kind != "review", event.key), default=None
    )


def _stable_step_ids(previous: PlanSnapshot, route: RouteDetail) -> set[str]:
    old_steps = {step.variant_id: step for step in previous.route.steps}
    return {step.variant_id for step in route.steps if old_steps.get(step.variant_id) == step}


def _progress_for_revision(previous: PlanSnapshot, route: RouteDetail) -> PlanProgress:
    """Only identical retained steps keep active completion; reports remain in history."""
    stable = _stable_step_ids(previous, route)
    return previous.progress.model_copy(
        update={
            "completed_steps": [
                variant_id
                for variant_id in previous.progress.completed_steps
                if variant_id in stable
            ]
        }
    )


class PlanHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int
    plan_id: uuid.UUID
    target_title: str
    selected_at: datetime
    last_activity_at: datetime | None
    solve_run_id: uuid.UUID
    schedule_index: int
    completed_steps: int


class PlanChanges(BaseModel):
    """Conservative invalidation: a changed source may affect any unfinished route step."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_version: int
    profile: bool
    planning_inputs: bool
    capability: bool
    target_matrix: bool
    option_pack: bool
    possibly_affected_steps: list[str]
    new_solve_needed: bool


class PlanDifference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    added_steps: list[str]
    removed_steps: list[str]
    changed_steps: list[str]
    old_readiness_month: str
    new_readiness_month: str
    old_direct_cost: Money
    new_direct_cost: Money
    old_economic_cost: SignedMoney | None
    new_economic_cost: SignedMoney | None
    same_accounting_basis: bool
    old_basis: ComparisonBasis
    new_basis: ComparisonBasis
    remaining_horizon_recalculated: bool = False


class PlanRevisionPreview(BaseModel):
    """A read-only proposal. Accepting it is a separate expected-version plan write."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    from_version: int
    proposed_solve_run_id: uuid.UUID
    proposed_schedule_index: int
    proposed_route: RouteDetail
    proposed_search: PlanSearch
    difference: PlanDifference
    completed_steps: list[str]


def plan_history(tx: Tx, workspace_id: uuid.UUID) -> list[PlanHistoryItem]:
    visible_workspace(tx, workspace_id)
    return [
        PlanHistoryItem(
            version=plan.version,
            plan_id=plan.plan_id,
            target_title=plan.target_title,
            selected_at=plan.selected_at,
            last_activity_at=plan.progress.activity[-1].recorded_at
            if plan.progress.activity
            else None,
            solve_run_id=plan.source.solve_run_id,
            schedule_index=plan.source.schedule_index,
            completed_steps=len(plan.progress.completed_steps),
        )
        for plan in store.plan_versions(tx, workspace_id)
    ]


def _current_target_versions(
    tx: Tx,
    workspace_id: uuid.UUID,
    keyring: Keyring,
    data: CapabilityData,
    inputs: InputsView,
    view: CapabilityView,
    target_title: str,
) -> tuple[str | None, str | None, CatalogueLabel | None]:
    matrix = next((m for m in view.matrices if m.target_key == title_key(target_title)), None)
    if matrix is None:
        return None, None, None
    [(_, options)] = target_catalogues(
        tx, keyring, workspace_id, [matrix], inputs.document.own_options, data
    )
    return (
        matrix.matrix_version,
        matrix.definition_version,
        options.catalogue.label if options.catalogue is not None else None,
    )


def plan_changes(
    tx: Tx, workspace_id: uuid.UUID, keyring: Keyring, data: CapabilityData
) -> PlanChanges:
    plan = selected_plan(tx, workspace_id)
    inputs = current_inputs(tx, workspace_id)
    view = capability_view(tx, workspace_id, data)
    matrix_version, definition_version, catalogue_label = _current_target_versions(
        tx, workspace_id, keyring, data, inputs, view, plan.target_title
    )
    matrix_changed = (
        matrix_version != plan.source.matrix_version
        or definition_version != plan.source.definition_version
    )
    catalogue_changed = catalogue_label != plan.route.label
    profile_changed = inputs.profile_version != plan.source.profile_version
    inputs_changed = inputs.version != plan.source.inputs_version
    capability_changed = view.version != plan.source.capability_version
    changed = any(
        (profile_changed, inputs_changed, capability_changed, matrix_changed, catalogue_changed)
    )
    return PlanChanges(
        plan_version=plan.version,
        profile=profile_changed,
        planning_inputs=inputs_changed,
        capability=capability_changed,
        target_matrix=matrix_changed,
        option_pack=catalogue_changed,
        possibly_affected_steps=[
            step.variant_id
            for step in plan.route.steps
            if step.variant_id not in plan.progress.completed_steps
        ]
        if changed
        else [],
        new_solve_needed=changed,
    )


def _fresh_route(
    tx: Tx,
    workspace_id: uuid.UUID,
    run_id: uuid.UUID,
    schedule_index: int,
    keyring: Keyring,
    data: CapabilityData,
) -> tuple[SolveView, RouteDetail, InputsView, CapabilityView]:
    """A proposed selection must still match the versions its complete solve read."""
    solve = solve_view(tx, keyring, workspace_id, run_id)
    if solve.result is None:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "This route search has no result.",
            stage=ErrorStage.PLANNING,
            details={"reason": "solve_not_complete", "state": solve.run.status.value},
        )
    if solve.monthly is None:
        raise outdated()
    replan = solve.monthly.inputs.replan
    current_plan = store.plan(tx, workspace_id)
    if replan is not None and (
        current_plan is None or current_plan.version != replan.from_plan_version
    ):
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "The plan changed after this replan was requested. Search again.",
            stage=ErrorStage.PLANNING,
            details={"reason": "replan_source_changed"},
        )
    inputs = current_inputs(tx, workspace_id)
    capability = capability_view(tx, workspace_id, data)
    if (
        inputs.version != solve.solve.inputs_version
        or inputs.profile_version != solve.run.profile_version
        or capability.version != solve.solve.capability_version
    ):
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "The route's inputs or evidence changed. Search again before choosing it.",
            stage=ErrorStage.PLANNING,
            details={"reason": "solve_inputs_changed"},
        )
    matrix_version, definition_version, catalogue_label = _current_target_versions(
        tx, workspace_id, keyring, data, inputs, capability, solve.result.target_title
    )
    if (
        matrix_version != solve.result.matrix_version
        or definition_version != solve.result.definition_version
        or catalogue_label != solve.result.label
    ):
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "The route's target definition or options changed. Search again before choosing it.",
            stage=ErrorStage.PLANNING,
            details={"reason": "solve_source_changed"},
        )
    return (
        solve,
        route_detail(solve.result, solve.monthly, schedule_index),
        inputs,
        capability,
    )


def revision_preview(
    tx: Tx,
    workspace_id: uuid.UUID,
    run_id: uuid.UUID,
    schedule_index: int,
    *,
    keyring: Keyring,
    data: CapabilityData,
) -> PlanRevisionPreview:
    previous = selected_plan(tx, workspace_id)
    solve, proposed, _, _ = _fresh_route(tx, workspace_id, run_id, schedule_index, keyring, data)
    before = previous.route
    old_steps = {step.variant_id: step for step in before.steps}
    new_steps = {step.variant_id: step for step in proposed.steps}
    old_economic = before.schedule.economic_cost
    new_economic = proposed.schedule.economic_cost
    result = solve.result
    if result is None:  # _fresh_route requires a complete solve
        raise outdated()
    return PlanRevisionPreview(
        from_version=previous.version,
        proposed_solve_run_id=run_id,
        proposed_schedule_index=schedule_index,
        proposed_route=proposed,
        proposed_search=PlanSearch(
            coverage=result.coverage,
            stop_reason=result.stop_reason,
            instance=result.instance,
            limits=result.limits,
        ),
        difference=PlanDifference(
            added_steps=sorted(new_steps.keys() - old_steps.keys()),
            removed_steps=sorted(old_steps.keys() - new_steps.keys()),
            changed_steps=sorted(
                key
                for key in old_steps.keys() & new_steps.keys()
                if old_steps[key] != new_steps[key]
            ),
            old_readiness_month=before.schedule.readiness_month,
            new_readiness_month=proposed.schedule.readiness_month,
            old_direct_cost=before.schedule.direct_cost,
            new_direct_cost=proposed.schedule.direct_cost,
            old_economic_cost=old_economic,
            new_economic_cost=new_economic,
            same_accounting_basis=before.basis == proposed.basis,
            old_basis=before.basis,
            new_basis=proposed.basis,
            remaining_horizon_recalculated=proposed.basis.replan is not None,
        ),
        completed_steps=previous.progress.completed_steps,
    )


def record_progress(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    update: ProgressUpdate,
    *,
    now: datetime,
) -> PlanSnapshot:
    """A self-report creates a new plan version; it never writes capability evidence."""
    visible_workspace(tx, workspace_id, lock=True)
    previous = selected_plan(tx, workspace_id)
    if previous.version != update.expected_version:
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "The plan changed. Reload, then try again.",
            stage=ErrorStage.PLANNING,
            details={"current_version": previous.version},
        )
    prior = previous.progress
    step = next(
        (step for step in previous.route.steps if step.variant_id == update.variant_id), None
    )
    if update.kind in ("step_completed", "commitment_accepted"):
        if step is None:
            raise CareerwrightError(
                ErrorCode.NOT_FOUND, "No such step in this plan.", stage=ErrorStage.PLANNING
            )
        existing = (
            prior.completed_steps if update.kind == "step_completed" else previous.commitments
        )
        if update.variant_id in existing:
            raise CareerwrightError(
                ErrorCode.ALREADY_DECIDED,
                "This step was already reported.",
                stage=ErrorStage.PLANNING,
            )
    if update.kind == "step_retracted" and update.variant_id not in prior.completed_steps:
        raise CareerwrightError(
            ErrorCode.ALREADY_DECIDED,
            "There is no active completion to retract for this step.",
            stage=ErrorStage.PLANNING,
        )
    if update.kind == "commitment_retracted" and update.variant_id not in previous.commitments:
        raise CareerwrightError(
            ErrorCode.ALREADY_DECIDED,
            "There is no active commitment to retract for this step.",
            stage=ErrorStage.PLANNING,
        )
    if update.until is not None and update.until < now.astimezone(ZoneInfo("Europe/London")).date():
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Choose today or a later date.",
            stage=ErrorStage.PLANNING,
            details={"reason": "date_in_past"},
        )
    completed = [*prior.completed_steps]
    if update.kind == "step_completed" and update.variant_id is not None:
        completed.append(update.variant_id)
    if update.kind == "step_retracted" and update.variant_id is not None:
        completed.remove(update.variant_id)
    commitments = [*previous.commitments]
    if update.kind == "commitment_accepted" and update.variant_id is not None:
        commitments.append(update.variant_id)
    if update.kind == "commitment_retracted" and update.variant_id is not None:
        commitments.remove(update.variant_id)
    rest_until = (
        update.until
        if update.kind == "rest"
        else (None if update.kind == "resume" else prior.rest_until)
    )
    review_on = update.until if update.kind == "review_rescheduled" else prior.review_on
    step_title = (
        (step.title or step.concept_id)
        if step is not None
        else next(
            (
                activity.step_title
                for activity in reversed(prior.activity)
                if activity.variant_id == update.variant_id and activity.step_title is not None
            ),
            None,
        )
    )
    progress = PlanProgress(
        completed_steps=completed,
        rest_until=rest_until,
        review_on=review_on,
        activity=[
            *prior.activity,
            PlanActivity(
                kind=update.kind,
                variant_id=update.variant_id,
                until=update.until,
                recorded_at=now,
                step_title=step_title,
            ),
        ],
    )
    snapshot = previous.model_copy(
        update={
            "version": previous.version + 1,
            "progress": progress,
            "commitments": commitments,
            "next_action": _next_action(previous.events, progress, now),
        }
    )
    store.insert_plan(tx, snapshot, created_by=actor.actor_id, created_at=now)
    return snapshot


def choose_plan(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    request: ChoosePlan,
    *,
    keyring: Keyring,
    data: CapabilityData,
    now: datetime,
) -> PlanSnapshot:
    """Lock the workspace, check the current versions, then insert one sealed selection."""
    visible_workspace(tx, workspace_id, lock=True)
    previous = store.plan(tx, workspace_id)
    current_version = previous.version if previous else 0
    if request.expected_version != current_version:
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "The chosen plan changed. Reload, then try again.",
            stage=ErrorStage.PLANNING,
            details={"current_version": current_version},
        )
    solve, route, inputs, capability = _fresh_route(
        tx, workspace_id, request.solve_run_id, request.schedule_index, keyring, data
    )
    stable = _stable_step_ids(previous, route) if previous else set()
    if previous is not None:
        unfinished = next(
            (
                variant_id
                for variant_id in previous.commitments
                if variant_id not in previous.progress.completed_steps and variant_id not in stable
            ),
            None,
        )
        if unfinished is not None:
            raise CareerwrightError(
                ErrorCode.VALIDATION_FAILED,
                "Keep the unfinished step or retract its accepted commitment before replacing it.",
                stage=ErrorStage.PLANNING,
                details={"reason": "ongoing_step_not_modelled", "variant_id": unfinished},
            )
    if (
        previous is not None
        and previous.progress.completed_steps
        and route.basis.replan is None
        and not request.full_horizon_accounting_acknowledged
    ):
        raise CareerwrightError(
            ErrorCode.CONFIRMATION_REQUIRED,
            "This route compares a full horizon and does not subtract completed work or "
            "sunk costs.",
            stage=ErrorStage.PLANNING,
            details={"reason": "full_horizon_accounting"},
        )
    events = events_for(route)
    result, record = solve.result, solve.solve
    if result is None:  # _fresh_route requires a complete solve
        raise outdated()
    progress = _progress_for_revision(previous, route) if previous else PlanProgress()
    snapshot = PlanSnapshot(
        plan_id=previous.plan_id if previous else uuid.uuid4(),
        version=current_version + 1,
        workspace_id=workspace_id,
        selected_at=now,
        selected_by=actor.actor_id,
        target_title=result.target_title,
        source=PlanSource(
            solve_run_id=request.solve_run_id,
            solve_id=record.solve_id,
            schedule_index=request.schedule_index,
            profile_version=inputs.profile_version,
            inputs_version=inputs.version,
            capability_version=capability.version,
            input_version=result.input_version,
            matrix_version=result.matrix_version,
            definition_version=result.definition_version,
            algorithm_version=result.algorithm_version,
            pruning_version=result.pruning_version,
        ),
        search=PlanSearch(
            coverage=result.coverage,
            stop_reason=result.stop_reason,
            instance=result.instance,
            limits=result.limits,
        ),
        route=route,
        events=events,
        next_action=_next_action(events, progress, now),
        progress=progress,
        commitments=[variant_id for variant_id in previous.commitments if variant_id in stable]
        if previous
        else [],
    )
    store.insert_plan(tx, snapshot)
    return snapshot
