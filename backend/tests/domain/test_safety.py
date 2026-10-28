"""The minimal response policy (S2.6, PROF-09, REC1-02). The screen has two tiers: a message
that states acute distress in the first person gets a fixed, reviewed support response
before any model call and is not sent; any other mention of a risk word is sent as usual
with a calm support note beside it, so no risk word is ever silently dropped and ordinary
career talk is never blocked. Model output may not infer a health condition, a diagnosis,
a personality type or a match percentage the person never used."""

import pytest

from nessa.profile.safety import (
    POLICY_VERSION,
    SUPPORT_RESOURCES,
    SupportTier,
    inferred_sensitive_terms,
    recorded_health_terms,
    screen_message,
)

# Clear first-person intent or a first-person statement of distress or self-injury.
ACUTE = [
    "Honestly I want to kill myself, nothing is working.",
    "I've been thinking about ending my life.",
    "I feel suicidal most days since I lost my job.",
    "I have been self-harming again.",
    "Some days I just want to die.",
    "I don't want to be alive any more.",
    "Everyone would be better off if I took my own life",
    "Some days I wanna die.",
    "I want to hurt myself.",
    "I don't want to live anymore.",
    "There's no reason to go on.",
    "I want to end it all.",
    # Shapes the fix-round 1 matcher missed (re-review 1): intent with a reason after it,
    # self-injury disclosed without an intent word, a qualifier after "live", and a
    # first-person statement followed by a career-sounding word.
    "I want to kill myself over this.",
    "I keep hurting myself.",
    "I don't want to live like this.",
    "I feel suicidal and I need support.",
    "I self-harm when work gets too much.",
    "I can't go on.",
]

# A risk word without clear first-person intent: sent as usual, with the support note.
MENTION = [
    # The earlier career false positives (review A-I-1): never blocked.
    "I want to take my life in a new direction.",
    "I took my life savings out to retrain.",
    "I don't want to live in London.",
    "I hurt myself lifting boxes at the warehouse, so I need lighter work.",
    "There is no reason to go on with the accounting course.",
    "I'm killing myself with overtime at the depot.",
    "I volunteer on a suicide prevention helpline and want paid work like it.",
    "I'd like to work in self-harm support services.",
    # Missed shapes without clear intent: noted, never dropped.
    "I could kill myself for missing that deadline.",
    "I hurt myself again last night.",
    "I can't go on like this at work.",
]

ORDINARY = [
    "This commute is killing me.",
    "I'm dying to try woodwork.",
    "I'd kill for a four-day week.",
    "The deadline pressure made me want to quit.",
    "I feel a bit overwhelmed by all the options.",
    "I have dyslexia, so long written tests are hard.",
]


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize("message", ACUTE)
def test_first_person_acute_distress_gets_the_support_response_and_is_not_sent(
    message: str,
) -> None:
    concern = screen_message(message)

    assert concern is not None
    assert concern.tier is SupportTier.ACUTE
    assert concern.policy == "acute_distress"
    assert concern.policy_version == POLICY_VERSION


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize("message", MENTION)
def test_any_other_risk_word_is_sent_as_usual_with_a_support_note(message: str) -> None:
    concern = screen_message(message)

    assert concern is not None  # never silently dropped
    assert concern.tier is SupportTier.MENTION  # never blocked
    assert concern.policy == "risk_mention"


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize("message", ORDINARY)
def test_ordinary_figures_of_speech_and_disclosures_get_nothing(message: str) -> None:
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


@pytest.mark.req("REC1-02")
def test_a_search_may_name_who_the_work_serves_in_a_kindred_word_but_a_reply_may_not() -> None:
    # Task 6 review A-M13: in a search, who the work serves is not a guess about the
    # person. Re-review N-M4: in a reply about the person it would be, so only searches
    # get the kindred words.
    person = ["I loved helping new mothers at the children's centre."]

    def searched(text: str, said: list[str] = person) -> list[str]:
        return inferred_sensitive_terms([text], said, kindred=True)

    assert searched("maternity support work for women") == []
    assert searched("mother and baby support") == []
    assert searched("jobs for women", ["I like fixing bikes."]) == ["women"]
    assert searched("work for pregnant women") == ["pregnant"]
    assert inferred_sensitive_terms(["As a woman you might enjoy this."], person) == ["woman"]
    assert inferred_sensitive_terms(["Work with mothers suits you."], person) == []  # their word


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
