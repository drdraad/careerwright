"""Hard caps on live Meta calls (ruling R5): call count, production-model calls and cost."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetPolicy:
    max_calls: int
    max_production_calls: int
    max_cost_nano_usd: int


@dataclass(frozen=True)
class SpentSoFar:
    calls: int
    production_calls: int
    committed_nano_usd: int


@dataclass(frozen=True)
class CallPlan:
    is_production_model: bool
    worst_case_nano_usd: int


class BudgetExceededError(RuntimeError):
    """The planned call would break a cap, so it must not be sent."""


def authorise_call(policy: BudgetPolicy, spent: SpentSoFar, plan: CallPlan) -> None:
    # Free calls (invalid-key checks, model listing) still count: the cap bounds traffic
    # to Meta, not only spend.
    if spent.calls >= policy.max_calls:
        raise BudgetExceededError(f"call cap reached ({spent.calls}/{policy.max_calls})")
    if plan.is_production_model and spent.production_calls >= policy.max_production_calls:
        raise BudgetExceededError(
            f"production-model call cap reached "
            f"({spent.production_calls}/{policy.max_production_calls})"
        )
    if spent.committed_nano_usd + plan.worst_case_nano_usd > policy.max_cost_nano_usd:
        raise BudgetExceededError(
            f"cost cap would be exceeded: committed {spent.committed_nano_usd} + worst case "
            f"{plan.worst_case_nano_usd} > {policy.max_cost_nano_usd} nano-USD"
        )
