"""The coverage-size measurement (`tools.route_search_sizes`; OPT1-16): its instances are
labelled synthetic and as large as declared; with no binding limit nothing is pruned, so the
search checks the whole selection space (the worst case); with P01's limits it prunes; and a
measurement reports complete coverage only when the search did."""

import pytest

from careerwright.planning.search import search_routes
from tools.route_search_sizes import instance, measure, sweep, table


@pytest.mark.req("OPT1-16")
def test_an_instance_is_synthetic_and_as_large_as_declared() -> None:
    monthly = instance(6, 2, 12, "p01")

    assert monthly.inputs.synthetic
    assert monthly.label.synthetic
    assert all(v.synthetic for v in monthly.variants)
    assert len({v.concept_id for v in monthly.variants}) == 6
    assert len(monthly.variants) == 12
    assert monthly.months[0] == "2027-01"
    assert len(monthly.months) == 12


@pytest.mark.req("OPT1-16", "OPT1-02")
def test_with_no_binding_limit_the_whole_selection_space_is_checked() -> None:
    result = search_routes(instance(5, 2, 6, "unbounded"))

    assert result.coverage.value == "complete"
    assert result.pruned == {}
    assert result.expanded_states == result.instance.selection_space == 243  # 3^5
    assert result.schedules


@pytest.mark.req("OPT1-16", "OPT1-02")
def test_with_p01_s_limits_the_same_courses_are_pruned_and_still_complete() -> None:
    tight = measure(5, 2, 6, "p01")
    loose = measure(5, 2, 6, "unbounded")

    assert tight.complete
    assert loose.complete
    assert tight.selection_space == loose.selection_space
    assert tight.expanded_states < loose.expanded_states
    assert 0 < tight.archived < loose.archived


@pytest.mark.req("OPT1-16")
def test_a_sweep_measures_each_size_in_order_and_tabulates_its_coverage() -> None:
    runs = sweep(families=("p01",), concepts=(2, 4), starts=(1,), horizons=(6,))

    assert [(r.concepts, r.complete) for r in runs] == [(2, True), (4, True)]
    assert "| p01 | 4 | 1 | 6 |" in table(runs)
    assert "complete" in table(runs)
