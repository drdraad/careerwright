"""The salary floor's facts on the slate say exactly what it did (slice 7B fix round 1, review
A M7): every count, so they add up to the occupations the floor considered. The web words them
(Task 6d slice A; `apps/web/src/lib/vocabulary.test.ts` checks the sentence)."""

import pytest

from careerwright.api.discovery_schemas import FloorReasonOut, SalaryFloorOut
from careerwright.catalogue.pay import FloorCounts, FloorUnknown, SalaryFloorRule
from careerwright.money import Money
from careerwright.profile.document import PayPeriod


@pytest.mark.req("DIV1-07")
def test_the_slate_s_floor_facts_give_every_count() -> None:
    counts = FloorCounts(
        SalaryFloorRule(2_600_000, "year"),
        left_out=1,
        meets=2,
        unknown={FloorUnknown.NO_REVIEWED_MAPPING: 3, FloorUnknown.NOT_PUBLISHED: 4},
    )

    shown = SalaryFloorOut.of(counts)

    assert (shown.amount, shown.period, shown.basis) == (
        Money(minor_units=2_600_000, currency="GBP"),
        PayPeriod.YEAR,
        "gross",
    )
    assert (shown.left_out, shown.meets) == (1, 2)
    assert shown.kept_by_reason == [
        FloorReasonOut(reason=FloorUnknown.NO_REVIEWED_MAPPING, count=3),
        FloorReasonOut(reason=FloorUnknown.NOT_PUBLISHED, count=4),
    ]
    assert shown.left_out + shown.meets + shown.kept_pay_unknown == 10
