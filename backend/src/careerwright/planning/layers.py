"""The three Pareto layers (spec section 12, "The three Pareto layers"; S6.5, S6.8). Pure.

For feasible schedules to one target under one set of assumptions, `p` dominates `q` when it is
no later and no dearer and the two points differ:

    p < q  iff  T(p) <= T(q), C(p) <= C(q) and (T(p), C(p)) != (T(q), C(q)).

F1 is the nondominated set of the whole encountered archive, dominated schedules included; F2
is the nondominated set of what F1 leaves, and F3 of what F1 and F2 leave. The layers come
from peeling, never from counting dominators: (1,3), (2,2) and (3,1) all dominate (4,4), and
(4,4) is still in F2. Equal points never dominate each other, so copies share a layer. A
point beyond the third layer has no layer. Costs may be negative (economic cost is measured
against a baseline).

Two implementations of that one definition:

- `rank`, the efficient two-objective layering the route search's rank stage uses (S6.8): one
  sort and one pass, O(n log n) for n points. In order of time, then cost, everything that
  dominates a point comes before it. Each layer keeps its tail, the last point it took: the
  layer's cheapest, and no sooner than any of it. A point is dominated by some point of a layer
  exactly when that layer's tail dominates it, and a point dominated by layer k is dominated by
  layer k - 1 too (dominance is transitive), so its layer is the first whose tail does not
  dominate it. That is one more than the deepest layer of anything dominating it, which is
  what peeling gives.
- `peel`, Sprint 6a's iterative peeling, the reference `rank` is qualified against on the same
  archives (S6.8): each peel finds the nondominated set with one sort (in order of time, a
  point is nondominated when it is cheaper than everything sooner and no point at its own time
  is cheaper). Kept for that qualification and for the benchmark (`tools.rank_benchmark`).
"""

from collections.abc import Sequence
from itertools import groupby

LAYERS = 3  # F1, F2 and F3 (spec section 12)

Point = tuple[int, int]  # (months to readiness, cost in minor units)


def dominates(p: Point, q: Point) -> bool:
    return p[0] <= q[0] and p[1] <= q[1] and p != q


def rank(points: Sequence[Point]) -> list[int | None]:
    """Each point's layer, 1 to 3, in one sort and one pass; None beyond F3. Equal to `peel`
    on every input."""
    layer: list[int | None] = [None] * len(points)
    tails: list[Point] = []  # each layer's tail: its cheapest point, taken last
    for index in sorted(range(len(points)), key=points.__getitem__):
        point = points[index]
        found = 0
        while found < len(tails) and dominates(tails[found], point):
            found += 1
        if found == LAYERS:
            continue  # dominated by F3 itself: beyond the third layer
        if found == len(tails):
            tails.append(point)
        else:
            tails[found] = point
        layer[index] = found + 1
    return layer


def peel(points: Sequence[Point]) -> list[int | None]:
    """Each point's layer, 1 to 3, by iterative nondominated peeling; None beyond F3."""
    layer: list[int | None] = [None] * len(points)
    remaining = list(range(len(points)))
    for number in range(1, LAYERS + 1):
        if not remaining:
            break
        front = set(_nondominated(points, remaining))
        for index in front:
            layer[index] = number
        remaining = [i for i in remaining if i not in front]
    return layer


def _nondominated(points: Sequence[Point], indexes: list[int]) -> list[int]:
    found: list[int] = []
    cheapest_sooner: int | None = None
    ordered = sorted(indexes, key=lambda i: points[i])
    for _, same_time in groupby(ordered, key=lambda i: points[i][0]):
        group = list(same_time)
        cheapest = points[group[0]][1]  # sorted by cost within one time
        if cheapest_sooner is None or cheapest < cheapest_sooner:
            found += [i for i in group if points[i][1] == cheapest]
            cheapest_sooner = cheapest
    return found
