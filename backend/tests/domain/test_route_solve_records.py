"""A route solve's records (Task 13b; ADR 0016's Task 13b amendment): the sealed snapshot and the
stored result read back exactly as they were written, so the worker searches the very input the
person asked about and the API serves the very result the worker found; and the solve's
identity is the snapshot's version under the same limits and the same search."""

from careerwright.planning.compiler import MonthlyInput, compile_input
from careerwright.planning.search import RANK_SECONDS, M0SearchLimits, SearchResult, search_routes
from careerwright.planning.solve_records import SolveSnapshot, solve_identity
from tests.support.planning import (
    directai_instance,
    trace_catalogue,
    trace_inputs,
    trace_readiness,
)


def trace() -> MonthlyInput:
    return compile_input(trace_inputs(), trace_catalogue(), readiness=trace_readiness())


def directai() -> MonthlyInput:
    inputs, catalogue, readiness = directai_instance()
    return compile_input(inputs, catalogue, readiness=readiness)


def test_a_sealed_snapshot_reads_back_as_the_same_input_and_searches_the_same() -> None:
    monthly = trace()
    limits = M0SearchLimits()
    snapshot = SolveSnapshot(
        solve_id=solve_identity(monthly, limits, RANK_SECONDS),
        monthly=monthly,
        limits=limits,
        rank_seconds=RANK_SECONDS,
    )

    opened = SolveSnapshot.model_validate_json(snapshot.sealed_text())

    assert opened == snapshot
    assert opened.monthly.input_version == monthly.input_version
    times = {"elapsed_ms", "rank_ms"}
    assert search_routes(opened.monthly).model_dump(exclude=times) == search_routes(
        monthly
    ).model_dump(exclude=times)


def test_a_stored_result_reads_back_exactly() -> None:
    result = search_routes(trace())

    assert result.schedules  # qualifications, conditions and families included
    assert SearchResult.model_validate_json(result.model_dump_json()) == result


def test_one_snapshot_under_the_same_limits_is_one_solve() -> None:
    monthly, other = trace(), directai()
    limits = M0SearchLimits()

    same = solve_identity(monthly, limits, RANK_SECONDS)

    assert same == solve_identity(trace(), M0SearchLimits(), RANK_SECONDS)
    assert same.startswith("solve:")
    assert len(same) == len("solve:") + 16
    assert same != solve_identity(other, limits, RANK_SECONDS)
    assert same != solve_identity(monthly, M0SearchLimits(max_states=10), RANK_SECONDS)
    assert same != solve_identity(monthly, limits, RANK_SECONDS + 1)
