"""A route solve's records (Task 13b; ADR 0016's Task 13b amendment): the snapshot it reads,
its identity, its stages and attempts. Pure: no SQL, no network, no model.

The snapshot is everything the search reads, compiled once when the solve is asked for and
sealed into the run: the person's planning inputs as the monthly model reads them, the target's
options with their answers in them, and its readiness basis (`MonthlyInput`), with every
limit. A later edit to any of them is a new version and can never change a solve under way.
The solve's identity comes from the snapshot's version and the limits, so the same solve
asked for twice is one solve.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.planning.compiler import MonthlyInput
from careerwright.planning.search import ALGORITHM_VERSION, PRUNING_VERSION, M0SearchLimits

SOLVE_DIGITS = 16


class SolveStage(StrEnum):
    """Where a running attempt is: the search stage, then the rank stage (S6.8)."""

    SEARCHING = "searching"
    RANKING = "ranking"


class AttemptOutcome(StrEnum):
    SUCCEEDED = "succeeded"  # its result is stored
    # It never finished: the worker stopped (a crash), its store went away, or its result
    # could not be stored before the run ended. Never a truncated result: the solve starts
    # again under a new attempt ID (spec section 22), or the run has ended without one.
    INTERRUPTED = "interrupted"
    # The person cancelled: the search stopped at its next check, or the run's end was
    # published while its worker was gone.
    CANCELLED = "cancelled"
    RANK_LIMIT_REACHED = "rank_limit_reached"  # the rank stage's own limit: no result
    FAILED = "failed"  # anything else, named by class only in the logs


class SolveSnapshot(BaseModel):
    """A route solve's sealed input: what its search reads, fixed when it was asked for."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    solve_id: str
    monthly: MonthlyInput
    limits: M0SearchLimits
    rank_seconds: int = Field(ge=1)

    def sealed_text(self) -> bytes:
        """What is sealed into the run. Derived fields (a matrix row's `required`) are left out:
        reading derives them again, and the closed models refuse them as input."""
        return self.model_dump_json(exclude_computed_fields=True).encode()


def solve_identity(monthly: MonthlyInput, limits: M0SearchLimits, rank_seconds: int) -> str:
    """The same snapshot under the same limits and the same search is the same solve."""
    payload = {
        "input_version": monthly.input_version,
        "limits": limits.model_dump(mode="json"),
        "rank_seconds": rank_seconds,
        "algorithm_version": ALGORITHM_VERSION,
        "pruning_version": PRUNING_VERSION,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"solve:{digest[:SOLVE_DIGITS]}"


@dataclass(frozen=True)
class SolveRecord:
    """A solve as it was asked for (`route_solves`)."""

    run_id: uuid.UUID
    workspace_id: uuid.UUID
    solve_id: str
    target_title: str
    inputs_version: int  # the person's planning inputs
    capability_version: int  # the evidence the readiness basis read
    input_version: str  # the monthly input's own version
    planning_start: date
    horizon_months: int
    objective_basis: Literal["economic", "direct_spending"]
    limits: M0SearchLimits
    rank_seconds: int
    algorithm_version: str
    pruning_version: str
    created_by: uuid.UUID
    created_at: datetime


@dataclass(frozen=True)
class SolveAttempt:
    attempt_id: int
    stage: SolveStage
    outcome: AttemptOutcome | None  # None while it runs
    started_at: datetime
    finished_at: datetime | None
