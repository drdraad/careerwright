"""The 50,000-point ranking benchmark (`tools.rank_benchmark`; OPT1-11): each shape is what it
says, both layerings rank it and must agree, and the table says so. The full run, with the
rank stage on an archive filled to its cap, is recorded in the Task 13b report and ADR 0016."""

import pytest

from careerwright.planning.layers import peel, rank
from tools.rank_benchmark import POINTS, SHAPES, StageRun, layering, points, table


@pytest.mark.req("OPT1-11")
def test_each_shape_is_the_archive_cap_s_size_and_what_it_says() -> None:
    assert POINTS == 50_000
    assert len(set(points("random"))) > POINTS * 0.99
    assert rank(points("front", 100)) == [1] * 100
    assert rank(points("chain", 100)) == [1, 2, 3] + [None] * 97
    assert set(points("equal", 100)) == {(7, 7)}
    assert len({t for t, _ in points("ties")}) == 24


@pytest.mark.req("OPT1-11")
@pytest.mark.parametrize("shape", SHAPES)
def test_both_layerings_rank_each_shape_and_agree(shape: str) -> None:
    run = layering(shape, 2_000)  # type: ignore[arg-type]
    found = points(shape, 2_000)  # type: ignore[arg-type]

    assert run.agree
    assert run.layered == tuple(rank(found).count(n) for n in (1, 2, 3))
    assert rank(found) == peel(found)


@pytest.mark.req("OPT1-11")
def test_the_table_names_each_shape_and_the_rank_stage_beside_its_limit() -> None:
    runs = [layering("front", 1_000)]
    stage = StageRun(archived=50_000, search_s=30.0, rank_ms=900, rank_seconds=5)

    printed = table(runs, stage)
    assert "| front | 1,000 |" in printed
    assert "| yes | 1,000, 0, 0 |" in printed
    assert "| 50,000 | 30.0 | 900 | 5 |" in printed
    # Only the layerings are the best of three: the rank stage at the cap is one run.
    assert "layerings best of 3; the rank stage at the cap, one run." in printed
