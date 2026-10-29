"""TIME-1's monthly grid (spec section 12, "Monthly decision contract"; S5.4): named calendar
months, every touched month reserved, a completion usable only from the next month boundary,
the strictly-before application rule, and actual dates never moved."""

from datetime import date, timedelta
from itertools import pairwise

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nessa.planning.months import (
    ApplicationTiming,
    Month,
    application_timing,
    grid,
    touched,
    usable_from,
)

DAYS = st.dates(min_value=date(2026, 1, 1), max_value=date(2030, 12, 31))


@pytest.mark.req("TIME1-01")
def test_a_month_is_a_named_calendar_month() -> None:
    assert str(Month.of(date(2027, 2, 28))) == "2027-02"
    assert Month.parse("2027-12").plus(1) == Month(2028, 1)
    assert Month(2027, 1).last_day() == date(2027, 1, 31)
    assert Month(2027, 2).last_day() == date(2027, 2, 28)  # 2027 is not a leap year
    assert Month(2028, 3).months_after(Month(2027, 1)) == 14
    with pytest.raises(ValueError, match="month"):
        Month(2027, 13)


@pytest.mark.req("TIME-01", "TIME1-02")
def test_a_mid_month_start_and_finish_reserve_every_touched_month() -> None:
    assert touched(date(2027, 1, 20), date(2027, 3, 3)) == [
        Month(2027, 1),
        Month(2027, 2),
        Month(2027, 3),
    ]
    assert touched(date(2027, 1, 31), date(2027, 2, 1)) == [Month(2027, 1), Month(2027, 2)]
    with pytest.raises(ValueError, match="finish"):
        touched(date(2027, 3, 1), date(2027, 2, 28))


@pytest.mark.req("TIME-02", "TIME1-02", "TRACE01-08")
def test_a_completion_is_usable_only_from_the_next_month_boundary() -> None:
    # TRACE-01 route B finishes on 30 April 2027: its outcome is usable from 1 May.
    assert usable_from(date(2027, 4, 30)) == Month(2027, 5)
    # A course finishing on the first of a month still waits for the following boundary.
    assert usable_from(date(2027, 4, 1)) == Month(2027, 5)


@pytest.mark.req("TIME-03", "TIME1-03")
def test_an_application_completes_strictly_before_its_deadline_month() -> None:
    deadline = date(2027, 3, 15)

    assert application_timing(Month(2027, 2), deadline) is ApplicationTiming.IN_TIME
    # The same month as the deadline is not resolved by this monthly model: never ineligible.
    assert application_timing(Month(2027, 3), deadline) is ApplicationTiming.SAME_MONTH
    assert application_timing(Month(2027, 4), deadline) is ApplicationTiming.TOO_LATE


@pytest.mark.req("TIME1-01")
def test_the_grid_names_each_month_of_the_horizon() -> None:
    months = grid(Month(2027, 1), 6)

    assert [str(m) for m in months] == [
        "2027-01",
        "2027-02",
        "2027-03",
        "2027-04",
        "2027-05",
        "2027-06",
    ]
    with pytest.raises(ValueError, match="24"):
        grid(Month(2027, 1), 25)


@pytest.mark.req("TIME-04", "TIME1-02")
@given(start=DAYS, length=st.integers(min_value=0, max_value=900))
def test_touched_months_run_from_the_start_month_to_the_finish_month(
    start: date, length: int
) -> None:
    finish = start + timedelta(days=length)
    months = touched(start, finish)

    assert months[0] == Month.of(start)  # never snapped earlier
    assert months[-1] == Month.of(finish)  # never rounded down
    assert len(months) == Month.of(finish).months_after(Month.of(start)) + 1
    assert all(b == a.plus(1) for a, b in pairwise(months))
    assert months[0].first_day() <= start <= finish <= months[-1].last_day()


@pytest.mark.req("TIME-02", "TIME1-02")
@given(finish=DAYS)
def test_what_a_completion_grants_is_never_usable_in_a_month_it_touches(finish: date) -> None:
    usable = usable_from(finish)

    assert usable == Month.of(finish).plus(1)
    assert usable.first_day() > finish


@pytest.mark.req("TIME-03", "TIME1-03")
@given(completes=DAYS, deadline=DAYS)
def test_the_application_rule_compares_whole_months(completes: date, deadline: date) -> None:
    timing = application_timing(Month.of(completes), deadline)
    month, due = Month.of(completes), Month.of(deadline)

    assert (timing is ApplicationTiming.IN_TIME) == (month < due)
    assert (timing is ApplicationTiming.SAME_MONTH) == (month == due)
    assert (timing is ApplicationTiming.TOO_LATE) == (month > due)


@given(first=st.integers(min_value=2026, max_value=2030), n=st.integers(min_value=0, max_value=60))
def test_months_add_and_subtract_exactly(first: int, n: int) -> None:
    start = Month(first, 1)

    assert start.plus(n).months_after(start) == n
