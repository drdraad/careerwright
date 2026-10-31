"""Route solves, worker side, without a store (Task 13b; ADR 0016's Task 13b amendment): the
cancel check the search reads. The run end to end, against real PostgreSQL 16 and DBOS, is in
`tests/integration/test_route_solves.py`."""

import threading
import time
from collections.abc import Callable

import pytest

from careerwright.db import StoreUnavailableError
from careerwright.planning.compiler import MonthlyInput, compile_input
from careerwright.planning.search import (
    M0SearchLimits,
    SearchCancelledError,
    SearchCoverage,
    rank_archive,
    search_archive,
)
from careerwright.planning.solve_runs import cancel_watch
from tests.support.planning import directai_instance

SLOW_STORE_S = 1.5  # one read of the cancel request: longer than the search's whole limit
WAIT_S = 5.0


def directai() -> MonthlyInput:
    inputs, catalogue, readiness = directai_instance()
    return compile_input(inputs, catalogue, readiness=readiness)


def eventually(check: Callable[[], bool]) -> bool:
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.01)
    return False


@pytest.mark.req("LIMITS-05", "DUR-05")
def test_a_slow_store_is_never_charged_to_the_search_s_clock() -> None:
    answered = threading.Event()

    def slow_read() -> bool:
        answered.wait(SLOW_STORE_S)  # the store answers, but late
        return False

    try:
        with cancel_watch(slow_read) as cancelled:
            archive = search_archive(
                directai(), limits=M0SearchLimits(wall_seconds=1), cancelled=cancelled
            )
            result = rank_archive(archive, cancelled=cancelled)
    finally:
        answered.set()

    # The search ran its whole tree inside its second: the read never stopped its clock.
    assert (result.coverage, result.stop_reason) == (SearchCoverage.COMPLETE, None)


@pytest.mark.req("LIMITS-06", "DUR-05")
def test_a_cancel_the_watch_reads_stops_the_search_at_its_next_check() -> None:
    with cancel_watch(lambda: True) as cancelled:
        assert eventually(cancelled)
        with pytest.raises(SearchCancelledError):
            search_archive(directai(), cancelled=cancelled)
        assert cancelled()  # true for good once read


@pytest.mark.req("DUR-05")
def test_a_failed_read_is_never_a_cancel_and_the_watch_reads_again() -> None:
    reads: list[int] = []
    second_read, go_on = threading.Event(), threading.Event()

    def read() -> bool:
        reads.append(len(reads) + 1)
        if len(reads) == 1:
            raise StoreUnavailableError
        if len(reads) == 2:
            second_read.set()
            go_on.wait(WAIT_S)
            return False
        return True  # the person cancels

    with cancel_watch(read) as cancelled:
        assert second_read.wait(WAIT_S)  # the failed read is behind it
        assert cancelled() is False
        go_on.set()
        assert eventually(cancelled)
