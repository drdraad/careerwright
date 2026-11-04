"""Option search keeps only grounded, permitted course and funding pages."""

import json

import pytest

from careerwright.evidence.option_research import pages_to_read
from careerwright.evidence.search import (
    OPTION_SEARCH,
    OptionSearchInput,
    SearchOutput,
    SearchPurpose,
    check_search,
    option_prompt_bytes,
    render_option_prompt,
    sealed_search_input,
)


@pytest.mark.req("SEC-05", "OPTN-16")
def test_option_search_sends_only_a_confirmed_target_and_one_city() -> None:
    context = OptionSearchInput(profile_version=3, target="Nurse", city="Leeds")

    assert json.loads(render_option_prompt(context).partition("\n")[2]) == {
        "role": "Nurse",
        "city": "Leeds",
        "country": "England",
    }
    assert sealed_search_input(context.model_dump_json().encode()) == context
    assert option_prompt_bytes(context) <= OPTION_SEARCH.max_prompt_bytes


@pytest.mark.req("ACQ-03", "OPTN-16")
def test_option_search_refuses_guessed_and_unlisted_pages() -> None:
    context = OptionSearchInput(profile_version=3, target="Nurse", city="Leeds")
    page = "https://www.gov.uk/student-finance/new-fulltime-students"
    guessed = "https://www.gov.uk/student-finance/new-parttime-students"
    unlisted = "https://unlisted.example/courses/nursing"
    output = SearchOutput.model_validate(
        {
            "candidates": [
                {"url": page, "title": "Student finance"},
                {"url": guessed, "title": "Guessed"},
                {"url": unlisted, "title": "Nursing"},
            ]
        }
    )

    proposal = check_search(output, context, sources=[page, unlisted], queries=["nursing Leeds"])

    assert proposal.purpose is SearchPurpose.OPTION_RESEARCH
    assert [candidate.url for candidate in proposal.candidates] == [page]
    assert {excluded.reason.value for excluded in proposal.excluded} == {
        "not_returned_by_search",
        "rights_review_required",
    }


def test_only_five_grounded_pages_can_be_read() -> None:
    context = OptionSearchInput(profile_version=3, target="Nurse", city="Leeds")
    urls = [f"https://www.gov.uk/student-finance/nursing-course-{i}" for i in range(8)]
    output = SearchOutput.model_validate(
        {"candidates": [{"url": url, "title": "Nursing course"} for url in urls]}
    )

    proposal = check_search(output, context, sources=urls, queries=["nursing Leeds"])

    assert pages_to_read(proposal) == urls[:5]
