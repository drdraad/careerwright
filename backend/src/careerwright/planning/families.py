"""Route families and equal points (spec section 12, ROU-1 and "The three Pareto layers";
S6.5). Pure. Grouping is for presentation only: it never removes, merges or re-ranks a
schedule, so the archive and the scope of what was proved stay as the search left them.

A family's identity is its canonical action graph, never an unordered set of actions:

- **each action:** its concept (the syllabus and provider, or a bridge job's role class); the
  way it is taken, where one intake is offered several ways (full or part time, carried by
  `outcomes_from`: a different family); the work pattern it runs with (a study break or
  reduced hours change the job-role sequence); and its financing and conditional gates (each
  support's instrument and award state, a tuition fee loan paid to the provider and its
  application state, and an offer still to be accepted);
- **precedence:** which action finishes in a month before another starts. Two actions neither
  of which comes first run in parallel, so the same actions in sequence and in parallel are
  two families.

A later intake of the same sequence, or another payment plan for the same action, is a
schedule of the same family. A family's best rank is the lowest layer among its schedules,
labelled as the family's (ROU1-03); a layer may hold no new family. Schedules with equal
coordinates share a point, and every one of them stays behind it.
"""

import hashlib
import json
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from careerwright.money import SignedMoney
from careerwright.planning.catalogue import WorkPatternKind
from careerwright.planning.compiler import CompiledVariant

FAMILY_DIGITS = 16


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FamilyAction(StrictModel):
    concept_id: str
    way: str | None  # the offering, when it is one way of taking an intake
    work_pattern: WorkPatternKind | None
    # "instrument:award" for each support it rests on, and "tuition_fee_loan:application"
    financing: list[str]
    conditional_offer: bool


class FamilyKey(StrictModel):
    family_id: str
    actions: list[FamilyAction]  # in their key's order
    precedence: list[tuple[int, int]]  # (earlier, later): indexes into `actions`


class Family(StrictModel):
    family_id: str
    actions: list[FamilyAction]
    precedence: list[tuple[int, int]]
    routes: list[list[str]]  # its schedules, in the archive's order
    best_layer: int | None  # the lowest layer among its schedules; None: all beyond F3


class EqualPoint(StrictModel):
    months_to_readiness: int
    objective_cost: SignedMoney
    layer: int | None
    routes: list[list[str]]  # every schedule at these coordinates


def family_key(route: Sequence[CompiledVariant]) -> FamilyKey:
    """A placed route's family: its actions and the precedence between them."""
    keyed = sorted(((_action(v), v) for v in route), key=lambda pair: pair[0].model_dump_json())
    actions = [action for action, _ in keyed]
    precedence = [
        (i, j)
        for i, (_, first) in enumerate(keyed)
        for j, (_, second) in enumerate(keyed)
        if _before(first, second)
    ]
    payload = json.dumps(
        {"actions": [a.model_dump(mode="json") for a in actions], "precedence": precedence},
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:FAMILY_DIGITS]
    return FamilyKey(family_id=f"family:{digest}", actions=actions, precedence=precedence)


def families(
    schedules: Sequence[tuple[list[str], FamilyKey, int | None]],
) -> list[Family]:
    """Group (route, family, layer) by family: best layer first, then as first found."""
    grouped: dict[str, tuple[FamilyKey, list[list[str]], list[int]]] = {}
    for route, key, layer in schedules:
        _, routes, layers = grouped.setdefault(key.family_id, (key, [], []))
        routes.append(route)
        if layer is not None:
            layers.append(layer)
    found = [
        Family(
            family_id=key.family_id,
            actions=key.actions,
            precedence=key.precedence,
            routes=routes,
            best_layer=min(layers, default=None),
        )
        for key, routes, layers in grouped.values()
    ]
    return sorted(found, key=lambda f: (f.best_layer is None, f.best_layer or 0))


def equal_points(
    schedules: Sequence[tuple[list[str], int, SignedMoney, int | None]],
) -> list[EqualPoint]:
    """Group (route, months, cost, layer) by coordinates, in order of time then cost."""
    grouped: dict[tuple[int, int], tuple[SignedMoney, int | None, list[list[str]]]] = {}
    for route, months, cost, layer in schedules:
        grouped.setdefault((months, cost.minor_units), (cost, layer, []))[2].append(route)
    return [
        EqualPoint(months_to_readiness=months, objective_cost=cost, layer=layer, routes=routes)
        for (months, _), (cost, layer, routes) in sorted(grouped.items())
    ]


def _action(variant: CompiledVariant) -> FamilyAction:
    pattern = variant.work_pattern
    return FamilyAction(
        concept_id=variant.concept_id,
        way=variant.offering_id if variant.outcome_offering_id != variant.offering_id else None,
        work_pattern=pattern.kind if pattern is not None else None,
        financing=sorted(
            [
                *(f"{s.instrument_id}:{s.award.value}" for s in variant.supports),
                *(
                    [f"tuition_fee_loan:{variant.tuition_fee_loan.application.value}"]
                    if variant.tuition_fee_loan is not None
                    else []
                ),
            ]
        ),
        conditional_offer=variant.conditional_offer,
    )


def _before(first: CompiledVariant, second: CompiledVariant) -> bool:
    """`first` finishes in a month before `second` starts."""
    if first.finish_index is None or second.start_index is None:
        return False
    return first.finish_index < second.start_index
