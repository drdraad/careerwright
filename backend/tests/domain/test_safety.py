"""The minimal response policy (S2.6, PROF-09, REC1-02): explicit acute distress gets a fixed,
reviewed support response before any model call, and model output may not infer a health
condition, a diagnosis, a personality type or a match percentage the person never used."""

import pytest

from nessa.profile.safety import (
    POLICY_VERSION,
    SUPPORT_RESOURCES,
    inferred_sensitive_terms,
    recorded_health_terms,
    screen_message,
)


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize(
    "message",
    [
        "Honestly I want to kill myself, nothing is working.",
        "I've been thinking about ending my life.",
        "I feel suicidal most days since I lost my job.",
        "I have been self-harming again.",
        "Some days I just want to die.",
        "I don't want to be alive any more.",
        "Everyone would be better off if I took my own life",
    ],
)
def test_explicit_acute_distress_gets_the_support_response(message: str) -> None:
    concern = screen_message(message)

    assert concern is not None
    assert concern.policy == "acute_distress"
    assert concern.policy_version == POLICY_VERSION


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize(
    "message",
    [
        "This commute is killing me.",
        "I'm dying to try woodwork.",
        "I'd kill for a four-day week.",
        "The deadline pressure made me want to quit.",
        "I feel a bit overwhelmed by all the options.",
        "I have dyslexia, so long written tests are hard.",
    ],
)
def test_ordinary_figures_of_speech_and_disclosures_are_not_treated_as_distress(
    message: str,
) -> None:
    assert screen_message(message) is None


@pytest.mark.req("PROF-09")
def test_the_support_resources_are_the_checked_uk_services_with_their_sources() -> None:
    contacts = {resource.name: resource.contact for resource in SUPPORT_RESOURCES}

    assert contacts == {
        "Emergency services": "Call 999 or go to A&E",
        "NHS 111": "Call 111 and choose the mental health option, or use 111 online",
        "Samaritans": "Call 116 123 (free, any time, day or night)",
        "Shout": "Text SHOUT to 85258 (free, 24/7)",
    }
    assert all(resource.source_url.startswith("https://") for resource in SUPPORT_RESOURCES)
    assert {resource.checked_on for resource in SUPPORT_RESOURCES} == {"2026-10-28"}


@pytest.mark.req("REC1-02")
def test_a_diagnosis_or_type_the_person_never_mentioned_is_an_inference() -> None:
    person = ["I lose track of time when I'm fixing things and hate paperwork."]

    found = inferred_sensitive_terms(
        [
            "It sounds like you might have ADHD.",
            "As an INTP you would enjoy this.",
            "You seem like an introvert.",
        ],
        person,
    )

    assert found == ["adhd", "INTP", "introvert"]


@pytest.mark.req("REC1-02")
def test_a_condition_the_person_named_may_be_acknowledged() -> None:
    person = ["I have dyslexia, so long written tests are hard. I'm an introvert."]

    assert (
        inferred_sensitive_terms(
            ["Thanks for telling me about your dyslexia. What adjustment would help?"], person
        )
        == []
    )


@pytest.mark.req("REC1-05")
def test_a_percentage_the_person_never_used_is_an_inference() -> None:
    person = ["I could take a 10% pay cut for a year."]

    assert inferred_sensitive_terms(["A 10% pay cut is noted."], person) == []
    assert inferred_sensitive_terms(["You are a 92% match for this."], person) == ["92%"]
    assert inferred_sensitive_terms(["You are a 92 per cent match."], person) == ["92 per cent"]


@pytest.mark.req("REC1-02", "PROF-09")
def test_a_health_condition_is_never_recorded_as_a_career_fact() -> None:
    assert recorded_health_terms(["managing my dyslexia at work", "fixing bikes"]) == ["dyslexia"]
    assert recorded_health_terms(["quiet focus", "a small team"]) == []
