"""The planning options' public contract (Task 11 fix round 1; ADR 0013 decision 11; spec
section 18, "payments/fees use `Money`"): every amount reaches the generated client as
`Money`, never a bare minor-unit integer, and no planning schema renames an existing one."""

from typing import Any

import pytest

from careerwright.api.app import openapi_document

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
# The options, and the person's planning inputs as they are read and written (Task 12a).
@pytest.mark.parametrize("schema", [RESPONSE, "PlanningInputsOut", "WriteInputs"])
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
