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

ACUTE, MENTION, NONE = 1, 2, 0

# One table: each row is an input shape, an example and the tier it must reach. Tier 1 is
# first-person present intent or distress only; tier 2 is any other message containing a
# risk stem, in any inflection; nothing with a risk stem reaches no tier (controller
# ruling, fix round 3). Examples are minimal; most are workplace phrasing.
CORPUS: list[tuple[str, str, int]] = [
    # Tier 1: first person, present intent or distress.
    ("intent + kill myself", "Honestly I want to kill myself, nothing is working.", ACUTE),
    ("intent + kill myself + reason", "I want to kill myself over this.", ACUTE),
    ("intent (perfect) + end my life", "I've been thinking about ending my life.", ACUTE),
    ("intent + die, clause end", "Some days I just want to die.", ACUTE),
    ("informal intent + die", "Some days I wanna die.", ACUTE),
    ("intent + hurt myself", "I want to hurt myself.", ACUTE),
    ("intent + end it all", "I want to end it all.", ACUTE),
    ("I feel suicidal", "I feel suicidal most days since I lost my job.", ACUTE),
    ("I feel suicidal + need", "I feel suicidal and I need support.", ACUTE),
    ("I've felt suicidal", "I've felt suicidal since I lost my job.", ACUTE),
    ("I keep thinking about + end my life", "I keep thinking about ending my life.", ACUTE),
    ("I have been self-harming", "I have been self-harming again.", ACUTE),
    ("I self-harm (present)", "I self-harm when work gets too much.", ACUTE),
    ("I keep hurting myself, clause end", "I keep hurting myself.", ACUTE),
    ("I don't want to be alive", "I don't want to be alive any more.", ACUTE),
    ("I don't want to live, clause end", "I don't want to live anymore.", ACUTE),
    ("I don't want to live like this", "I don't want to live like this.", ACUTE),
    ("I do not want to live like this", "I do not want to live like this.", ACUTE),
    ("I do not want to be here any more", "I do not want to be here any more.", ACUTE),
    (
        "better off if I took my own life",
        "Everyone would be better off if I took my own life",
        ACUTE,
    ),
    ("I can't go on, clause end", "I can't go on.", ACUTE),
    # Tier 2: a risk stem in a professional, third-party, figurative or object frame.
    ("professional: suicide prevention", "I volunteer on a suicide prevention helpline.", MENTION),
    (
        "professional: intent + suicide (noun)",
        "I have been thinking about suicide prevention work.",
        MENTION,
    ),
    (
        "professional: intent of + suicide",
        "I am thinking of suicide prevention as a career.",
        MENTION,
    ),
    (
        "professional: self-harm services",
        "I'd like to work in self-harm support services.",
        MENTION,
    ),
    (
        "professional: I have + self-harm (noun)",
        "I have self-harm awareness training from my NHS role.",
        MENTION,
    ),
    (
        "third party: people feeling suicidal",
        "I answer calls from people feeling suicidal.",
        MENTION,
    ),
    (
        "third party: young people feeling suicidal",
        "I support young people feeling suicidal as a youth worker.",
        MENTION,
    ),
    ("third party: something going to die", "I think the high street is going to die.", MENTION),
    ("third party: print going to die", "Print is going to die, so I want to retrain.", MENTION),
    ("no subject: no reason to go on", "There's no reason to go on.", MENTION),
    ("figurative: die of boredom", "I am going to die of boredom in this job.", MENTION),
    ("figurative: die on this hill", "I am ready to die on this hill about remote work.", MENTION),
    (
        "figurative: killing myself with work",
        "I'm killing myself with overtime at the depot.",
        MENTION,
    ),
    ("figurative: could kill myself", "I could kill myself for missing that deadline.", MENTION),
    ("object: take my life in a direction", "I want to take my life in a new direction.", MENTION),
    ("object: life savings", "I took my life savings out to retrain.", MENTION),
    ("object: taken my life savings", "Retraining has taken my life savings.", MENTION),
    ("object: live in a place", "I don't want to live in London.", MENTION),
    ("injury: hurt myself lifting", "I hurt myself lifting boxes at the warehouse.", MENTION),
    (
        "injury: have been hurting myself lifting",
        "I have been hurting myself lifting boxes at the warehouse.",
        MENTION,
    ),
    (
        "injury: kept cutting myself on tape",
        "I kept cutting myself on the packaging tape at the depot.",
        MENTION,
    ),
    (
        "injury: was cutting myself on tape",
        "I was cutting myself on the packaging tape at the depot.",
        MENTION,
    ),
    ("injury: hurt myself (past)", "I hurt myself again last night.", MENTION),
    (
        "course: no reason to go on with",
        "There is no reason to go on with the accounting course.",
        MENTION,
    ),
    ("can't go on + qualifier", "I can't go on like this at work.", MENTION),
    ("cannot go on + object", "I cannot go on with this course.", MENTION),
    ("can not go on + qualifier", "I can not go on like this at work.", MENTION),
    ("wanting to die (figurative)", "Wanting to die on every hill slows meetings down.", MENTION),
    ("don't want to be here (job)", "I don't want to be here in five years.", MENTION),
    # No risk stem: nothing.
    ("killing me (not myself)", "This commute is killing me.", NONE),
    ("dying to", "I'm dying to try woodwork.", NONE),
    ("kill for", "I'd kill for a four-day week.", NONE),
    ("want to quit", "The deadline pressure made me want to quit.", NONE),
    ("overwhelmed", "I feel a bit overwhelmed by all the options.", NONE),
    ("a named condition", "I have dyslexia, so long written tests are hard.", NONE),
]


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize(("shape", "message", "tier"), CORPUS, ids=[row[0] for row in CORPUS])
def test_the_screen_puts_each_shape_in_its_tier(shape: str, message: str, tier: int) -> None:
    concern = screen_message(message)

    found = NONE if concern is None else ACUTE if concern.tier is SupportTier.ACUTE else MENTION
    assert found == tier, shape
    if concern is not None:
        assert concern.policy == ("acute_distress" if tier == ACUTE else "risk_mention")
        assert concern.policy_version == POLICY_VERSION


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
