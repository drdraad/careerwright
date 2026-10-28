"""Spend limits and reservation rules for a user's Meta key (spec section 16, MODEL-08).

Before every provider call the worker reserves the call's worst-case cost against two caps:
per run and per calendar month (UTC). An attempt then settles: a reported usage reconciles
it to its estimated cost; an interrupted or failed call with no reported usage stays
`unknown` and keeps its full reservation committed. Unknown is never zero.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum

from nessa.errors import ErrorCode, ErrorStage, NessaError


class SpendState(StrEnum):
    NONE = "none"  # no provider call was made
    HELD = "held"  # reserved; the call may be in flight
    RECONCILED = "reconciled"  # cost estimated from reported usage
    UNKNOWN = "unknown"  # a call may have been billed; its reservation stays committed


class BudgetScope(StrEnum):
    RUN = "run"
    PERIOD = "period"


@dataclass(frozen=True)
class SpendLimits:
    run_limit_nano_usd: int
    period_limit_nano_usd: int

    def __post_init__(self) -> None:
        if min(self.run_limit_nano_usd, self.period_limit_nano_usd) < 0:
            raise ValueError("spend limits cannot be negative")


def period_start(now: datetime) -> date:
    utc = now.astimezone(UTC)
    return date(utc.year, utc.month, 1)


def committed_cost(state: SpendState, *, reserved_nano_usd: int, cost_nano_usd: int | None) -> int:
    match state:
        case SpendState.RECONCILED:
            if cost_nano_usd is None:
                raise ValueError("a reconciled attempt has a known cost")
            return cost_nano_usd
        case SpendState.HELD | SpendState.UNKNOWN:
            return reserved_nano_usd
        case SpendState.NONE:
            return 0


def refused_scope(
    limits: SpendLimits, *, period_committed: int, run_committed: int, worst_case: int
) -> BudgetScope | None:
    """Which cap a reservation of `worst_case` would break, or None if it fits both."""
    if run_committed + worst_case > limits.run_limit_nano_usd:
        return BudgetScope.RUN
    if period_committed + worst_case > limits.period_limit_nano_usd:
        return BudgetScope.PERIOD
    return None


def budget_exceeded(scope: BudgetScope) -> NessaError:
    return NessaError(
        ErrorCode.BUDGET_EXCEEDED,
        f"This call would exceed the {scope.value} spend limit for your key. Raise the limit "
        "or wait for the next period.",
        stage=ErrorStage.SPEND,
        details={"scope": scope.value},
    )
