"""Route solve use cases, API side (Task 13b; ADR 0016's Task 13b amendment): ask for a solve,
and read one.

Asking takes the snapshot the search will read, once, in the caller's transaction: the person's
stored planning inputs at the version they saw (a newer one is refused as stale), the profile's
two spending caps, the target's options with the person's answers in them, and its readiness
basis (the matrix, evidence and statements at the capability version, with the person's
outcome decisions), compiled into one `MonthlyInput`. Anything a solve cannot start without is
refused here with its code, never run and never an empty result: a stale version, a target
that is not theirs, a target with no options, a planning start already past, an input a solve
needs (named), or a catalogue beyond the M0 bounds. The snapshot is sealed into the run, so a
later edit makes a new version and never reaches a solve under way. The same solve asked for
again while one is queued or running joins it, unless the person has asked to cancel that one:
then it is a new run.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from careerwright.capability.commands import CapabilityData, capability_view
from careerwright.capability.evidence import Month as MonthText
from careerwright.config import RuntimeMode
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence.jobs import title_key
from careerwright.identity import run_store
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.records import Run, RunKind
from careerwright.identity.runs import open_output, submit_keyless_run, visible_run
from careerwright.identity.workspaces import visible_workspace
from careerwright.planning import store
from careerwright.planning.checkpoint import expected_entry
from careerwright.planning.commands import current_inputs, person_entry, target_catalogues
from careerwright.planning.compiler import MonthlyInput, ReadinessBasis, compile_input
from careerwright.planning.inputs import decided_outcomes, prepare
from careerwright.planning.months import MAX_HORIZON_MONTHS, Month
from careerwright.planning.search import (
    ALGORITHM_VERSION,
    PRUNING_VERSION,
    RANK_SECONDS,
    M0SearchLimits,
    SearchResult,
    check_scope,
)
from careerwright.planning.solve_records import (
    SolveAttempt,
    SolveRecord,
    SolveSnapshot,
    read_output,
    solve_identity,
)
from careerwright.profile.commands import current_profile
from careerwright.profile.document import TextValue
from careerwright.vocabulary import WorkState


class SolveRequest(BaseModel):
    """Search one target's routes over a comparison's start and horizon."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_inputs_version: int = Field(
        ge=0, description="The planning inputs version the person saw."
    )
    target: TextValue = Field(description="One of the profile's target titles.")
    planning_start: MonthText = Field(
        description="The comparison's first month, as YYYY-MM: this month or later."
    )
    horizon_months: int = Field(ge=1, le=MAX_HORIZON_MONTHS)


@dataclass(frozen=True)
class SolveView:
    run: Run
    solve: SolveRecord
    attempts: list[SolveAttempt]
    result: SearchResult | None  # only once the run is complete
    # The monthly input the result was computed from (Task 14); None: no result, or one
    # stored before the input was kept beside it.
    monthly: MonthlyInput | None = None


def _refused(reason: str, **details: str) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        "A route search can't start from what is stated yet.",
        stage=ErrorStage.PLANNING,
        details={"reason": reason, **details},
    )


def request_solve(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    request: SolveRequest,
    *,
    data: CapabilityData,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    now: datetime,
) -> tuple[SolveView, bool]:
    """The solve, and whether this call started it (False: it joined the same solve)."""
    # Locked first, as every planning write is: the snapshot reads one state of the inputs,
    # and two asks for the same solve are one.
    visible_workspace(tx, workspace_id, lock=True)
    inputs = current_inputs(tx, workspace_id)
    if request.expected_inputs_version != inputs.version:
        raise store.stale_version(inputs.version)
    view = capability_view(tx, workspace_id, data)
    key = title_key(request.target)
    matrix = next((m for m in view.matrices if m.target_key == key), None)
    if matrix is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "That is not one of your target roles.", stage=ErrorStage.PLANNING
        )
    # The pack's options and the person's own beside them (Task 12b).
    [(_, options)] = target_catalogues(
        tx, keyring, workspace_id, [matrix], inputs.document.own_options, data
    )
    if options.catalogue is None:
        raise _refused("no_options", note=options.note or "no_pack_target")
    start = Month.parse(request.planning_start)
    if start < Month.of(now.date()):
        raise _refused("planning_start_past")
    profile = current_profile(tx, workspace_id).document
    qualifications, keys = person_entry(tx, profile, [options.catalogue])
    prepared = prepare(
        inputs.document,
        options.catalogue,
        caps=inputs.caps,
        planning_start=start.first_day(),
        horizon_months=request.horizon_months,
        synthetic=inputs.synthetic,
        version=inputs.version,
        expected_entry=expected_entry(options.catalogue, qualifications, keys),
    )
    basis = ReadinessBasis(
        matrix=matrix,
        evidence=view.evidence,
        statements=view.statements,
        outcomes=decided_outcomes(data.outcomes, inputs.document.outcome_decisions),
        evidence_version=view.version,
    )
    monthly = compile_input(prepared.inputs, prepared.catalogue, readiness=basis)
    limits = M0SearchLimits()
    check_scope(monthly, limits)
    solve_id = solve_identity(monthly, limits, RANK_SECONDS)
    joined = store.unsettled_solve(tx, workspace_id, solve_id)
    if joined is not None:
        return solve_view(tx, keyring, workspace_id, joined), False
    snapshot = SolveSnapshot(
        solve_id=solve_id, monthly=monthly, limits=limits, rank_seconds=RANK_SECONDS
    )
    run = submit_keyless_run(
        tx,
        actor,
        workspace_id,
        RunKind.ROUTE_SOLVE,
        runtime_mode=runtime_mode,
        workflow_name=run_store.ROUTE_SOLVE_WORKFLOW,
        now=now,
        profile_version=inputs.profile_version,
        sealed_input=(keyring, snapshot.sealed_text()),
    )
    store.insert_solve(
        tx,
        SolveRecord(
            run_id=run.run_id,
            workspace_id=workspace_id,
            solve_id=solve_id,
            target_title=matrix.target_title,
            inputs_version=inputs.version,
            capability_version=view.version,
            input_version=monthly.input_version,
            planning_start=start.first_day(),
            horizon_months=request.horizon_months,
            objective_basis=monthly.inputs.objective_basis,
            limits=limits,
            rank_seconds=RANK_SECONDS,
            algorithm_version=ALGORITHM_VERSION,
            pruning_version=PRUNING_VERSION,
            created_by=actor.actor_id,
            created_at=now,
        ),
    )
    return solve_view(tx, keyring, workspace_id, run.run_id), True


def solve_view(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, run_id: uuid.UUID) -> SolveView:
    """A solve with its run and attempts, and its result once the run is complete: a run
    cancelled or failed shows none, whatever an attempt stored."""
    run = visible_run(tx, workspace_id, run_id)
    found = store.solve(tx, run_id) if run.kind is RunKind.ROUTE_SOLVE else None
    if found is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such route search.", stage=ErrorStage.PLANNING
        )
    result, monthly = None, None
    if run.status is WorkState.COMPLETE:
        output = open_output(tx, keyring, run)
        if output is None:  # a complete run always has its output (a database CHECK)
            raise CareerwrightError(
                ErrorCode.INTERNAL_ERROR,
                "A complete route search has no result.",
                stage=ErrorStage.PLANNING,
            )
        result, monthly = read_output(output)
    return SolveView(run, found, store.solve_attempts(tx, run_id), result, monthly)
