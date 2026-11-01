"""Read and set a workspace's spend limits, with an expected version (MODEL-08), and what a
run may spend before it starts (spec section 16: "display estimated incremental cost before
deep research")."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import credential_store, run_store, store
from careerwright.identity.activity import run_worst_case_nano_usd
from careerwright.identity.model_choice import ModelChoice, fixture_model
from careerwright.identity.model_registry import ModelEntry
from careerwright.identity.records import EventKind, RunKind
from careerwright.identity.spend import BudgetScope, SpendLimits, period_start, refused_scope
from careerwright.identity.workspaces import stale_workspace, visible_workspace
from careerwright.vocabulary import DataMode


class SetSpendLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=0, description="0 while the defaults have never been saved.")
    run_limit_nano_usd: int = Field(ge=0)
    period_limit_nano_usd: int = Field(ge=0)


@dataclass(frozen=True)
class SpendSummary:
    limits: SpendLimits
    version: int  # 0: the configured defaults, never saved for this workspace
    period_start: date
    period_committed_nano_usd: int
    unknown_cost_attempts: int


def spend_summary(
    tx: Tx, workspace_id: uuid.UUID, now: datetime, defaults: SpendLimits
) -> SpendSummary:
    visible_workspace(tx, workspace_id)
    stored = credential_store.spend_limits(tx, workspace_id)
    period = period_start(now)
    committed, unknown = run_store.period_spend(tx, workspace_id, period)
    limits, version = stored if stored else (defaults, 0)
    return SpendSummary(limits, version, period, committed, unknown)


@dataclass(frozen=True)
class RunEstimate:
    """What one run of a kind may spend on the person's key, before it starts: two maxima,
    never an expected cost. Without a worker crash, every attempt the DBOS step may make at
    the reservation the activity takes for each, and never past the run limit; with a crash
    (DBOS gives the step fresh attempts), still never past the run limit, which the activity
    never reserves beyond. `refused_scope`: the limit that would refuse it if it started now,
    by the submission's own rule."""

    kind: RunKind
    model: ModelEntry
    per_run_nano_usd: int
    hard_maximum_nano_usd: int
    refused_scope: BudgetScope | None


def run_estimate(
    tx: Tx,
    workspace_id: uuid.UUID,
    kind: RunKind,
    attempt_worst_case: Callable[[str], int],
    *,
    models: ModelChoice,
    now: datetime,
    defaults: SpendLimits,
) -> RunEstimate:
    """For the model the workspace's runs of this kind pin: a demo workspace's fixture
    stand-in costs nothing, and a kind it never runs is refused as at submission."""
    workspace = visible_workspace(tx, workspace_id)
    if workspace.data_mode is DataMode.DEMO:
        stand_in = fixture_model(kind)
        if stand_in is None:
            raise CareerwrightError(
                ErrorCode.MODE_NOT_SUPPORTED,
                "Demo workspaces run on fixtures only and never call a model.",
                stage=ErrorStage.EXECUTION,
            )
        return RunEstimate(kind, stand_in, 0, 0, None)
    model = models.for_workspace(synthetic=workspace.synthetic)
    summary = spend_summary(tx, workspace_id, now, defaults)
    run_limit = summary.limits.run_limit_nano_usd
    return RunEstimate(
        kind,
        model,
        per_run_nano_usd=min(
            run_worst_case_nano_usd(attempt_worst_case, model.model_id), run_limit
        ),
        hard_maximum_nano_usd=run_limit,
        refused_scope=refused_scope(
            summary.limits,
            period_committed=summary.period_committed_nano_usd,
            run_committed=0,
            worst_case=attempt_worst_case(model.model_id),
        ),
    )


def set_spend_limits(
    tx: Tx, workspace_id: uuid.UUID, command: SetSpendLimits, now: datetime, defaults: SpendLimits
) -> SpendSummary:
    visible_workspace(tx, workspace_id, lock=True)
    stored = credential_store.spend_limits(tx, workspace_id)
    current_version = stored[1] if stored else 0
    if command.expected_version != current_version:
        raise stale_workspace(current_version)
    limits = SpendLimits(command.run_limit_nano_usd, command.period_limit_nano_usd)
    if stored is None:
        credential_store.ensure_spend_limits(tx, workspace_id, limits)
    elif not credential_store.update_spend_limits(tx, workspace_id, current_version, limits):
        raise stale_workspace(current_version)
    store.append_event(tx, workspace_id, EventKind.SPEND_LIMITS_UPDATED, str(workspace_id))
    return spend_summary(tx, workspace_id, now, defaults)
