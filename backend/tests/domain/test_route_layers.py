"""The three Pareto layers by iterative nondominated peeling (spec section 12, "The three Pareto
layers"; S6.5): F1 is the archive's nondominated set, F2 the nondominated set of what is left,
F3 the same again. Equal objective pairs never dominate each other, and being bettered by many
routes is never a reason to drop one. Expected layers are the specification's own tables."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from careerwright.planning.layers import dominates, peel
from tests.support.planning import directai_fixture


@pytest.mark.req("PARETO-01", "OPT1-08")
def test_three_dominators_leave_the_fourth_point_in_the_second_layer() -> None:
    # Spec section 12: (1,3), (2,2), (3,1) are mutually nondominated and all dominate (4,4).
    points = [(1, 3), (2, 2), (3, 1), (4, 4)]

    assert all(dominates(p, (4, 4)) for p in points[:3])
    assert peel(points) == [1, 1, 1, 2]


@pytest.mark.req("PARETO-02", "OPT1-08")
def test_equal_objective_pairs_never_dominate_each_other() -> None:
    points = [(4, 600), (4, 600), (5, 600), (4, 700)]

    assert not dominates((4, 600), (4, 600))
    # Both copies stay on the first layer; each is bettered by neither.
    assert peel(points) == [1, 1, 2, 2]


@pytest.mark.req("PARETO-02")
def test_a_point_is_dominated_only_when_no_worse_on_both_and_better_on_one() -> None:
    assert dominates((2, 5), (3, 5))  # the same cost, sooner
    assert dominates((3, 4), (3, 5))  # the same time, cheaper
    assert not dominates((2, 6), (3, 5))  # a trade-off
    assert not dominates((3, 5), (2, 5))


@pytest.mark.req("DIRECTAI-01", "OPT1-08")
def test_the_a_to_i_table_peels_into_its_three_stated_layers() -> None:
    routes = directai_fixture()["routes"]
    points = [(r["time_months"], r["direct_spend_minor"]) for r in routes]

    assert peel(points) == [r["expected_layer"] for r in routes]


def test_points_beyond_the_third_layer_have_no_layer_and_an_empty_archive_peels_to_nothing() -> (
    None
):
    chain = [(n, n) for n in range(1, 6)]  # each bettered by every earlier one

    assert peel(chain) == [1, 2, 3, None, None]
    assert peel([]) == []


def _longest_chain(points: list[tuple[int, int]]) -> list[int]:
    """A point's layer as one more than the deepest layer of any point dominating it, written
    apart from `peel`: the same definition, reached another way."""
    depth = [0] * len(points)
    for i in sorted(range(len(points)), key=lambda n: points[n]):
        better = [depth[j] for j in range(len(points)) if j != i and _better(points[j], points[i])]
        depth[i] = 1 + max(better, default=0)
    return depth


def _better(p: tuple[int, int], q: tuple[int, int]) -> bool:
    return p[0] <= q[0] and p[1] <= q[1] and p != q


@pytest.mark.req("OPT1-08", "PARETO-01", "PARETO-02")
@settings(max_examples=200, deadline=None)
@given(
    points=st.lists(
        st.tuples(st.integers(0, 8), st.integers(-5, 8)),  # economic cost may be negative
        max_size=25,
    )
)
def test_peeling_agrees_with_the_longest_dominance_chain(points: list[tuple[int, int]]) -> None:
    expected = [d if d <= 3 else None for d in _longest_chain(points)]

    assert peel(points) == expected
