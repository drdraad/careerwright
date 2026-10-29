"""The salary floor's words on the slate say exactly what it did (slice 7B fix round 1, review
A M7): every count, so the sentence adds up to the occupations the floor considered."""

import pytest

from nessa.api.discovery_schemas import SalaryFloorOut
from nessa.catalogue.pay import FloorCounts, FloorUnknown, SalaryFloorRule


@pytest.mark.req("DIV1-07")
def test_the_slate_s_floor_sentence_gives_every_count() -> None:
    counts = FloorCounts(
        SalaryFloorRule(2_600_000, "year"),
        left_out=1,
        meets=2,
        unknown={FloorUnknown.NO_REVIEWED_MAPPING: 3, FloorUnknown.NOT_PUBLISHED: 4},
    )

    shown = SalaryFloorOut.of(counts)

    assert shown.summary.startswith("Your minimum salary of £26,000 a year (gross) is applied")
    for words in (
        "1 left out because their official pay is below it",
        "2 meet it",
        "3 kept because no reviewed UK occupation code links them to pay data",
        "4 kept because the official figure is not published for your regions",
        "Unknown pay is never treated as below it",
    ):
        assert words in shown.summary
    assert shown.left_out + shown.meets + shown.kept_pay_unknown == 10
