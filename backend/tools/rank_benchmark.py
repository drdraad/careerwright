"""Benchmark 50,000-point ranking (plan Sprint 6b, S6.8; OPT1-11; spec section 12): the efficient
layering (`layers.rank`) beside Sprint 6a's iterative peeling (`layers.peel`) at the archive
cap, and the whole rank stage (`search.rank_archive`: the layers, then families and equal
points) on a real archive the search filled to its cap.

- **Points.** Five shapes of 50,000 points (months, cost), each ranked by both layerings,
  which must agree: `random` (uniform over 24 months and £10,000 either side of zero),
  `front` (every point on F1: each sooner and dearer than the next), `chain` (each bettered
  by every earlier one, so all but three are beyond F3), `equal` (one point 50,000 times) and
  `ties` (24 months by 500 costs, every coordinate shared).
- **The rank stage at the cap.** The search fills its 50,000-schedule archive on the synthetic
  `unbounded` instance of `tools.route_search_sizes` (20 concepts, one start, 24 months; no
  limit binds, so nothing is pruned). Its clock is held still, so the archive cap stops it
  rather than the 30 seconds. The rank stage then runs on its own clock and limit
  (`RANK_SECONDS`). The instance is labelled synthetic and never product data.

Times are wall clock, on the machine named: each layering's the best of three runs, the rank
stage at the cap's one run (its archive takes about half a minute to fill). Run from
`backend/`: `uv run --locked python -m tools.rank_benchmark` (`--points-only` skips the
archive).
"""

import argparse
import platform
import random
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from careerwright.planning.layers import Point, peel, rank
from careerwright.planning.search import (
    RANK_SECONDS,
    M0SearchLimits,
    rank_archive,
    search_archive,
)
from tools.route_search_sizes import instance

Shape = Literal["random", "front", "chain", "equal", "ties"]
SHAPES: tuple[Shape, ...] = ("random", "front", "chain", "equal", "ties")
POINTS = 50_000  # the archive cap (spec section 12, M0SearchLimits.max_feasible_archive)
REPEATS = 3
SEED = 2026_10_31
MONTHS = 24
COST_SPREAD = 1_000_000  # £10,000 either side of zero, in minor units
TIE_COSTS = 500
CAP_INSTANCE = (20, 1, 24)  # concepts, starts, months: fills the archive cap (Task 13a)


class LayeringRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    shape: Shape
    points: int
    rank_s: float
    peel_s: float
    agree: bool
    layered: tuple[int, int, int]  # how many points in F1, F2 and F3


class StageRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    archived: int
    search_s: float
    rank_ms: int  # the stage's own measurement
    rank_seconds: int  # its limit


def points(shape: Shape, size: int = POINTS) -> list[Point]:
    if shape == "random":
        draw = random.Random(SEED)  # noqa: S311 - reproducible benchmark points, not a secret
        return [
            (draw.randint(1, MONTHS), draw.randint(-COST_SPREAD, COST_SPREAD)) for _ in range(size)
        ]
    if shape == "front":
        return [(n, size - n) for n in range(size)]
    if shape == "chain":
        return [(n, n) for n in range(size)]
    if shape == "equal":
        return [(7, 7)] * size
    return [(n % MONTHS + 1, (n * 7919) % TIE_COSTS) for n in range(size)]


def _best(work: Callable[[], object]) -> float:
    times = []
    for _ in range(REPEATS):
        began = time.perf_counter()
        work()
        times.append(time.perf_counter() - began)
    return min(times)


def layering(shape: Shape, size: int = POINTS) -> LayeringRun:
    found = points(shape, size)
    ranked, peeled = rank(found), peel(found)
    return LayeringRun(
        shape=shape,
        points=size,
        rank_s=_best(lambda: rank(found)),
        peel_s=_best(lambda: peel(found)),
        agree=ranked == peeled,
        layered=(ranked.count(1), ranked.count(2), ranked.count(3)),
    )


def stage_at_the_cap() -> StageRun:
    """The search fills its archive cap on a frozen clock; then the rank stage, timed."""
    monthly = instance(*CAP_INSTANCE, "unbounded")
    began = time.perf_counter()
    archive = search_archive(monthly, limits=M0SearchLimits(), clock=lambda: 0.0)
    search_s = time.perf_counter() - began
    result = rank_archive(archive)
    return StageRun(
        archived=len(archive),
        search_s=search_s,
        rank_ms=result.rank_ms,
        rank_seconds=result.rank_seconds,
    )


def table(runs: Sequence[LayeringRun], stage: StageRun | None) -> str:
    lines = [
        f"Measured {datetime.now(UTC):%Y-%m-%d} on {platform.machine()} "
        f"({platform.system()}), Python {platform.python_version()}; layerings best of "
        f"{REPEATS}; the rank stage at the cap, one run.",
        "",
        "| Shape | Points | Efficient layering (s) | Iterative peeling (s) | Equal | F1, F2, F3 |",
        "|---|---:|---:|---:|---|---|",
        *(
            f"| {r.shape} | {r.points:,} | {r.rank_s:.3f} | {r.peel_s:.3f} | "
            f"{'yes' if r.agree else 'NO'} | {r.layered[0]:,}, {r.layered[1]:,}, "
            f"{r.layered[2]:,} |"
            for r in runs
        ),
    ]
    if stage is not None:
        lines += [
            "",
            "| Archived schedules | Search to the cap (s) | Rank stage (ms) | Its limit (s) |",
            "|---:|---:|---:|---:|",
            f"| {stage.archived:,} | {stage.search_s:.1f} | {stage.rank_ms:,} | "
            f"{stage.rank_seconds} |",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--points-only", action="store_true", help="skip the archive at the cap")
    args = parser.parse_args()
    runs = [layering(shape) for shape in SHAPES]
    stage = None if args.points_only else stage_at_the_cap()
    print(table(runs, stage))
    if not all(r.agree for r in runs):
        raise SystemExit("the efficient layering and peeling disagree")
    if stage is not None and stage.rank_ms >= RANK_SECONDS * 1000:
        raise SystemExit("the rank stage at the archive cap reached its own limit")


if __name__ == "__main__":
    main()
