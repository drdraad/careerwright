"""The planning options' public contract (Task 11 fix round 1; ADR 0013 decision 11; spec
section 18, "payments/fees use `Money`"): every amount reaches the generated client as
`Money`, never a bare minor-unit integer, and no planning schema renames an existing one."""

from typing import Any

import pytest

from careerwright.api.app import openapi_document
from careerwright.api.routes_planning import result_code
from careerwright.errors import ErrorCode
from careerwright.planning.compiler import compile_input
from careerwright.planning.search import (
    M0SearchLimits,
    Outcome,
    SearchCoverage,
    SearchResult,
    search_routes,
)
from tests.support.planning import (
    ROW,
    START,
    catalogue_of,
    month_end,
    option,
    person,
    readiness_of,
)

RESPONSE = "OptionsOut"


def schemas() -> dict[str, Any]:
    found: dict[str, Any] = openapi_document()["components"]["schemas"]
    return found


def reachable(name: str, every: dict[str, Any]) -> set[str]:
    """The schemas a response can contain, by name."""
    seen: set[str] = set()
    pending = [name]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        stack: list[Any] = [every[current]]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                ref = node.get("$ref")
                if isinstance(ref, str):
                    pending.append(ref.rsplit("/", 1)[-1])
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return seen


@pytest.mark.req("ARC1-10", "OPTN-01", "PLN-11")
# The options, the person's planning inputs as they are read and written (Task 12a), and a
# route solve with its result (Task 13b).
@pytest.mark.parametrize("schema", [RESPONSE, "PlanningInputsOut", "WriteInputs", "SolveOut"])
def test_every_amount_the_options_serve_is_money(schema: str) -> None:
    every = schemas()
    served = reachable(schema, every)
    bare = sorted(
        f"{name}.{field}"
        for name in served
        for field in every[name].get("properties", {})
        if field.endswith("_minor")
    )

    assert bare == []
    assert "Money" in served


@pytest.mark.req("ARC1-10")
def test_no_schema_is_named_by_its_module_path() -> None:
    # A planning enum once collided with the profile's `Basis` and FastAPI renamed both.
    every = schemas()

    assert [name for name in every if "__" in name] == []
    assert every["Basis"]["enum"] == ["stated", "inferred"]


def _solved(direct_cap: int = 1000, **limits: int) -> SearchResult:
    """A £5 and a £20 course, each reaching the target, under a direct-spend cap."""
    options = [
        option(name, start=START, finish=month_end(START, 1), hours=0, payments=((0, fee),))
        for name, fee in (("cheap", 500), ("dear", 2000))
    ]
    readiness = readiness_of({"offering:cheap": (ROW,), "offering:dear": (ROW,)})
    monthly = compile_input(
        person(horizon=3, opening=1_000_000, direct_cap=direct_cap),
        catalogue_of(*options),
        readiness=readiness,
    )
    return search_routes(monthly, limits=M0SearchLimits(**limits))


@pytest.mark.req("API-02", "OPT1-07", "OPT1-15", "STATE-03")
def test_a_solve_s_code_names_a_stopped_search_or_a_proven_no_route_and_nothing_else() -> None:
    found = _solved()
    stopped = _solved(max_states=1)
    nothing = _solved(direct_cap=100)  # both above the cap: complete, and nothing unknown

    # Spec section 18's codes, as facts: never an error envelope, never on a result of routes.
    assert (found.coverage, found.outcome) == (SearchCoverage.COMPLETE, Outcome.ROUTES_FOUND)
    assert result_code(found) is None
    assert stopped.coverage is SearchCoverage.BUDGET_TRUNCATED
    assert result_code(stopped) == "SOLVE_LIMIT_REACHED"
    assert nothing.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    assert result_code(nothing) == "NO_ROUTE_IN_BOUNDED_MODEL"
    assert set(schemas()["SolveOut"]["properties"]["code"]["anyOf"][0]["enum"]) == {
        ErrorCode.SOLVE_LIMIT_REACHED.value,
        ErrorCode.NO_ROUTE_IN_BOUNDED_MODEL.value,
    }
