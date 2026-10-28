"""The minimal response policy (S2.6, PROF-09, REC1-02). One recall-first screen over the
normalised words of a message: a listed risk word, or a listed construction whose words
fall within its small window, triggers the support flow (the support panel, and the
smaller-step instruction for that turn), and the message is sent as usual. No intent is
judged, so a stem inside career phrasing triggers it too (an accepted false positive,
listed for H-12), and a message with none gets nothing. Model output may not infer a
health condition, a diagnosis, a personality type or a match percentage the person never
used."""

import pytest

from nessa.profile.safety import (
    SUPPORT_RESOURCES,
    has_risk_stem,
    inferred_sensitive_terms,
    recorded_health_terms,
)

FLOW, NO_FLOW = True, False
MODIFIER_APOSTROPHE = "\N{MODIFIER LETTER APOSTROPHE}"
CURLY_APOSTROPHE = "\N{RIGHT SINGLE QUOTATION MARK}"
NON_BREAKING_HYPHEN = "\N{NON-BREAKING HYPHEN}"
EN_DASH = "\N{EN DASH}"

# One hand-written table (controller ruling, fix round 5): every shape the reviewers
# reported in re-reviews 2, 3 and 4 must trigger the flow; the reviewers' career examples
# with no stem must not. Each row names where it comes from. Fragments are minimal.
CORPUS: list[tuple[str, str, bool]] = [
    # The corpus from before re-review 2 (re-review 1's misses and the first tier).
    ("rr1", "I want to kill myself over this.", FLOW),
    ("rr1", "I keep hurting myself.", FLOW),
    ("rr1", "I don't want to live like this.", FLOW),
    ("rr1", "I feel suicidal and I need support.", FLOW),
    ("rr1", "Some days I just want to die.", FLOW),
    ("rr1", "I've been thinking about ending my life.", FLOW),
    ("rr1", "I don't want to be alive any more.", FLOW),
    ("rr1", "Everyone would be better off if I took my own life", FLOW),
    ("rr1", "I can't go on.", FLOW),
    ("rr1", "I want to take my life in a new direction.", FLOW),
    ("rr1", "I took my life savings out to retrain.", FLOW),
    ("rr1", "I don't want to live in London.", FLOW),
    ("rr1", "I hurt myself lifting boxes at the warehouse.", FLOW),
    ("rr1", "There is no reason to go on with the accounting course.", FLOW),
    ("rr1", "I'm killing myself with overtime at the depot.", FLOW),
    ("rr1", "I could kill myself for missing that deadline.", FLOW),
    # Re-review 2: the career phrasings tier 1 caught, and the inflections no tier caught.
    ("rr2 I-1", "I have been thinking about suicide prevention work.", FLOW),
    ("rr2 I-1", "I am thinking of suicide prevention as a career.", FLOW),
    ("rr2 I-1", "I think the high street is going to die.", FLOW),
    ("rr2 I-1", "Print is going to die, so I want to retrain.", FLOW),
    ("rr2 I-1", "I am going to die of boredom in this job.", FLOW),
    ("rr2 I-1", "I am ready to die on this hill about remote work.", FLOW),
    ("rr2 I-1", "I answer calls from people feeling suicidal on the helpline.", FLOW),
    ("rr2 I-1", "I support young people feeling suicidal as a youth worker.", FLOW),
    ("rr2 I-1", "I have self-harm awareness training from my NHS role.", FLOW),
    ("rr2 I-1", "I kept cutting myself on the packaging tape at the depot.", FLOW),
    ("rr2 I-1", "I have been hurting myself lifting boxes at the warehouse.", FLOW),
    ("rr2 I-2", "I was cutting myself on the packaging tape at the depot.", FLOW),
    ("rr2 I-2", "I cut myself on the packaging tape at the depot.", FLOW),
    ("rr2 I-2", "I cannot go on with this course.", FLOW),
    ("rr2 I-2", "I can not go on like this at work.", FLOW),
    ("rr2 I-2", "Retraining has taken my life savings.", FLOW),
    ("rr2 I-2", "Wanting to die on every hill slows meetings down.", FLOW),
    ("rr2 M-2", "I do not want to be here any more.", FLOW),
    ("rr2 M-2", "I do not want to live this way.", FLOW),
    ("rr2 M-2", "I don't want to be here in five years.", FLOW),
    # Re-review 3: C-1 (shapes read from the patterns), N-I1, N-I2, M-a and M-c.
    ("rr3 C-1", "thinking about dying", FLOW),
    ("rr3 C-1", "thought about dying", FLOW),
    ("rr3 C-1", "think of dying", FLOW),
    ("rr3 C-1", "thoughts of dying", FLOW),
    ("rr3 C-1", "decided to die", FLOW),
    ("rr3 C-1", "the urge to die", FLOW),
    ("rr3 C-1", "urges to die", FLOW),
    ("rr3 C-1", "want to just die", FLOW),
    ("rr3 N-I1", "I would be better off if I took my life savings and retrained.", FLOW),
    ("rr3 N-I1", "I am thinking about ending my life sciences career.", FLOW),
    ("rr3 N-I1", "I want to end my life coaching business and teach.", FLOW),
    ("rr3 N-I1", "My old team is better off without me, so I want a new role.", FLOW),
    ("rr3 N-I1", "I am going to hurt myself lifting these boxes at the depot.", FLOW),
    ("rr3 N-I2", "He did not want to live in London.", FLOW),
    ("rr3 N-I2", "She does not want to live in Leeds.", FLOW),
    ("rr3 N-I2", "I could not go on with the accounting course.", FLOW),
    ("rr3 N-I2", "tries to die", FLOW),
    ("rr3 N-I2", "tried to die", FLOW),
    ("rr3 M-a", "thinking about suicide", FLOW),
    ("rr3 M-a", "I am feeling suicidal", FLOW),
    ("rr3 M-a", "want to simply die", FLOW),
    ("rr3 M-a", "The tape is sharp and I keep cutting myself.", FLOW),
    ("rr3 M-a", "I see no reason to go on with the course.", FLOW),
    ("rr3 M-c", "overdose", FLOW),
    ("rr3 M-c", "overdosed", FLOW),
    ("rr3 M-c", "harming myself", FLOW),
    ("rr3 M-c", "harmed myself", FLOW),
    ("rr3 M-c", "cuts myself", FLOW),
    ("rr3 M-c", "ends my life", FLOW),
    ("rr3 M-c", "ended my life", FLOW),
    ("rr3 M-c", "end it all", FLOW),
    ("rr3 M-c", "takes my life", FLOW),
    ("rr3 M-c", "taking my own life", FLOW),
    ("rr3 M-c", "wish I was dead", FLOW),
    ("rr3 M-c", "better off dead", FLOW),
    ("rr3 M-c", "better off without me", FLOW),
    ("rr3 M-c", "doesn't want to live", FLOW),
    ("rr3 M-c", "didn't want to live", FLOW),
    ("rr3 M-c", "couldn't go on", FLOW),
    ("rr3 M-c", "plan to die", FLOW),
    ("rr3 M-c", "tempted to die", FLOW),
    ("rr3 M-c", "trying to die", FLOW),
    ("rr3 M-c", "intend to die", FLOW),
    ("rr3 M-c", "wanna die", FLOW),
    ("rr3 M-c", "gonna die", FLOW),
    ("rr3 M-c", "no reason to live", FLOW),
    # Re-review 4: I-1's probes and the forms read from the code, and M-3's Unicode.
    ("rr4 I-1", "He hadn't wanted to live in London.", FLOW),
    ("rr4 I-1", "She hasn't wanted to live in Leeds.", FLOW),
    ("rr4 I-1", "I haven't wanted to live in London for years.", FLOW),
    ("rr4 I-1", "I wasn't wanting to live in London.", FLOW),
    ("rr4 I-1", "He isn't wanting to live in Leeds.", FLOW),
    ("rr4 I-1", "They aren't wanting to live in London.", FLOW),
    ("rr4 I-1", "They weren't wanting to live in Leeds.", FLOW),
    ("rr4 I-1", "I ain't wanting to live in London.", FLOW),
    ("rr4 I-1", "I don't wanna live in London.", FLOW),
    ("rr4 I-1", "I don't even really want to live in London.", FLOW),
    ("rr4 I-1", "I never ever want to live in London.", FLOW),
    ("rr4 I-1", "I can no longer go on with the accounting course.", FLOW),
    ("rr4 I-1", "I could no longer go on with the accounting course.", FLOW),
    ("rr4 I-1", "I can't really go on with this course.", FLOW),
    ("rr4 I-1", "I can't just go on with this course.", FLOW),
    ("rr4 I-1", "There isn't any reason to go on with the course.", FLOW),
    ("rr4 I-1", "There are no reasons to go on with the course.", FLOW),
    ("rr4 I-1", "There is no real reason to go on with the course.", FLOW),
    ("rr4 I-1", "wish I'd die", FLOW),
    ("rr4 I-1", "wish I'd died", FLOW),
    ("rr4 I-1", "wish I had died", FLOW),
    ("rr4 I-1", "wish I had been dead", FLOW),
    ("rr4 I-1", "wish I was truly dead", FLOW),
    ("rr4 I-1", "wish my manager was dead", FLOW),
    ("rr4 I-1", "He took own life savings out.", FLOW),
    ("rr4 I-1", "ended Alex's life", FLOW),
    ("rr4 M-3", f"I don{MODIFIER_APOSTROPHE}t want to live in London.", FLOW),
    ("rr4 M-3", f"I don{CURLY_APOSTROPHE}t want to live in London.", FLOW),
    ("rr4 M-3", f"self{NON_BREAKING_HYPHEN}harm support services", FLOW),
    ("rr4 M-3", f"self{EN_DASH}harm support services", FLOW),
    # The reviewers' career examples with no stem, and guards for the windows: nothing.
    ("rr3 N-I1", "I am planning to end my lifeguard job this summer.", NO_FLOW),
    ("rr3 N-I1", "I want to end my lifelong career in retail.", NO_FLOW),
    ("rr3 N-I1", "The team would be better off without meetings on Fridays.", NO_FLOW),
    ("rr3 C-1", "I'm dying to try woodwork.", NO_FLOW),
    ("career", "I studied life sciences at college.", NO_FLOW),
    ("career", "I spent my life savings on the course.", NO_FLOW),
    ("career", "There were job cuts at work this year.", NO_FLOW),
    ("career", "I cut costs in my team.", NO_FLOW),
    ("career", "We would be better off without the old rota.", NO_FLOW),
    ("career", "Redundancy hurt my self-esteem.", NO_FLOW),
    ("career", "I want to live in Leeds.", NO_FLOW),
    ("career", "I don't want to work here.", NO_FLOW),
    ("career", "I didn't go on to university.", NO_FLOW),
    ("career", "I can't go online at work.", NO_FLOW),
    ("career", "The noise will die down soon.", NO_FLOW),
    ("career", "This commute is killing me.", NO_FLOW),
    ("career", "I'd kill for a four-day week.", NO_FLOW),
    ("career", "The deadline pressure made me want to quit.", NO_FLOW),
    ("career", "I feel a bit overwhelmed by all the options.", NO_FLOW),
    ("career", "I have dyslexia, so long written tests are hard.", NO_FLOW),
]


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize(
    ("source", "message", "flow"), CORPUS, ids=[f"{row[0]}: {row[1]}" for row in CORPUS]
)
def test_every_reported_shape_triggers_the_support_flow_and_career_text_without_one_does_not(
    source: str, message: str, flow: bool
) -> None:
    assert has_risk_stem(message) is flow, source
    # Whatever surrounds it, and in capitals.
    assert has_risk_stem(f"At work, {message}, and so on.") is flow, source
    assert has_risk_stem(message.upper()) is flow, source


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
