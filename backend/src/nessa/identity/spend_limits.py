"""Read and set a workspace's spend limits, with an expected version (MODEL-08)."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from nessa.db import Tx
from nessa.identity import credential_store, run_store, store
from nessa.identity.records import EventKind
from nessa.identity.spend import SpendLimits, period_start
from nessa.identity.workspaces import stale_workspace, visible_workspace


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
