"""The calm support panel lists the same UK services wherever it shows: beside a sent or
refused message, the first question's title field, and every entry a person types and saves
or has refused (What we know, the review step, a title's details, a workspace's name). Every
place builds it through `SupportNoteOut`; the integration tests check each route returns it."""

import pytest

from careerwright.api.interview_schemas import SupportNoteOut
from careerwright.profile import safety

EVERY_PLACE = {
    "a sent message": SupportNoteOut.current(sent=True),
    "a refused message": SupportNoteOut.current(sent=False),
    "the first question's title": SupportNoteOut.beside_a_title(),
    "a saved entry": SupportNoteOut.beside_an_entry(saved=True),
    "a refused entry": SupportNoteOut.beside_an_entry(saved=False),
}


@pytest.mark.req("PROF-15")
@pytest.mark.parametrize("place", EVERY_PLACE)
def test_the_panel_lists_childline_with_an_https_link_wherever_it_shows(place: str) -> None:
    note = EVERY_PLACE[place]

    assert note.policy_version == "support-policy-12"
    assert "not yet reviewed as built" in note.review_status
    assert [r.name for r in note.resources] == [
        "Emergency services",
        "NHS 111",
        "Samaritans",
        "Shout",
        "Childline",
    ]
    childline = note.resources[-1]
    assert childline.contact == (
        "Call 0800 1111 or use the 1-2-1 chat online (free, 24 hours a day, 7 days a week)"
    )
    assert childline.when == "For children and young people"
    assert childline.source_url.startswith("https://")
    assert childline.checked_on == safety.CHILDLINE_CHECKED_ON == "2026-11-01"
