"""TIME-1's monthly grid (spec section 12, "Monthly decision contract"). Pure.

A month is a named calendar month in the work area's timezone. England's dates are calendar
dates, so a month is its year and number, never a block of 30 days. The model reserves every
month a dated activity touches, and what a completion grants is usable only from the
following month boundary. Actual dates stay beside the months: an intake is never moved
earlier and a course is never shortened by rounding its duration down.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

MONTHS_PER_YEAR = 12
MAX_HORIZON_MONTHS = 24  # M0SearchLimits.max_months (spec section 18)


@dataclass(frozen=True, order=True)
class Month:
    year: int
    number: int

    def __post_init__(self) -> None:
        if not 1 <= self.number <= MONTHS_PER_YEAR:
            raise ValueError(f"no month {self.number}")

    @classmethod
    def of(cls, day: date) -> "Month":
        return cls(day.year, day.month)

    @classmethod
    def parse(cls, text: str) -> "Month":
        year, number = text.split("-")
        return cls(int(year), int(number))

    def plus(self, months: int) -> "Month":
        total = self.year * MONTHS_PER_YEAR + self.number - 1 + months
        return Month(total // MONTHS_PER_YEAR, total % MONTHS_PER_YEAR + 1)

    def months_after(self, earlier: "Month") -> int:
        return (self.year - earlier.year) * MONTHS_PER_YEAR + self.number - earlier.number

    def first_day(self) -> date:
        return date(self.year, self.number, 1)

    def last_day(self) -> date:
        return date(self.year, self.number, monthrange(self.year, self.number)[1])

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.number:02d}"


def grid(start: Month, horizon: int) -> list[Month]:
    """The months of a planning horizon, the first being the planning start's month."""
    if not 1 <= horizon <= MAX_HORIZON_MONTHS:
        raise ValueError(f"a horizon is 1 to {MAX_HORIZON_MONTHS} months")
    return [start.plus(n) for n in range(horizon)]


def touched(start: date, finish: date) -> list[Month]:
    """Every month a dated activity touches, from its start's month to its finish's."""
    if finish < start:
        raise ValueError("an activity cannot finish before it starts")
    first, last = Month.of(start), Month.of(finish)
    return [first.plus(n) for n in range(last.months_after(first) + 1)]


def usable_from(completion: date) -> Month:
    """What a completion grants becomes available at the following month boundary, never in a
    month the activity touches: conservative, and stated as the model's choice."""
    return Month.of(completion).plus(1)


class ApplicationTiming(StrEnum):
    IN_TIME = "in_time"  # completes in a month strictly before the deadline month
    # The deadline's own month: "not resolved by this monthly model", never "ineligible".
    SAME_MONTH = "same_month"
    TOO_LATE = "too_late"  # after the deadline month: the source deadline cannot be ignored


def application_timing(completes_in: Month, deadline: date) -> ApplicationTiming:
    due = Month.of(deadline)
    if completes_in < due:
        return ApplicationTiming.IN_TIME
    if completes_in == due:
        return ApplicationTiming.SAME_MONTH
    return ApplicationTiming.TOO_LATE
