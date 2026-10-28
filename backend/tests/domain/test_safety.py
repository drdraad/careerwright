"""The minimal response policy (S2.6, PROF-09, REC1-02). One recall-first screen: a message
holding any listed risk stem, in any inflection, person, tense or negation, triggers the
support flow (the support panel, and the smaller-step instruction for that turn), and the
message is sent as usual. No intent is judged, so a stem inside career phrasing triggers it
too (an accepted false positive, listed for H-12), and a message with no stem gets nothing.
Model output may not infer a health condition, a diagnosis, a personality type or a match
percentage the person never used."""

from collections.abc import Iterable
from itertools import product

import pytest

from nessa.profile.safety import (
    SUPPORT_RESOURCES,
    has_risk_stem,
    inferred_sensitive_terms,
    recorded_health_terms,
)

FLOW, NO_FLOW = True, False
Row = tuple[str, str, bool]
CURLY = "\N{RIGHT SINGLE QUOTATION MARK}"  # the apostrophe phone keyboards type

SELVES = (
    "myself",
    "yourself",
    "himself",
    "herself",
    "ourselves",
    "yourselves",
    "themselves",
    "themself",
    "oneself",
    "my self",
)
WHOSE = ("my", "your", "his", "her", "our", "their", "one's")
PRONOUNS = ("I", "you", "he", "she", "we", "they")
INTENTS = (
    "want to",
    "wants to",
    "wanted to",
    "wanting to",
    "wanna",
    "going to",
    "gonna",
    "ready to",
    "plan to",
    "plans to",
    "planned to",
    "planning to",
    "tempted to",
    "try to",
    "tries to",
    "tried to",
    "trying to",
    "intend to",
    "intends to",
    "intended to",
    "intending to",
    "decide to",
    "decides to",
    "decided to",
    "deciding to",
    "urge to",
    "urges to",
)
THINKING = ("think", "thinks", "thinking", "thought", "thoughts")
NOT_WANTING = (
    "don't want",
    "dont want",
    f"don{CURLY}t want",
    "do not want",
    "don't really want",
    "don't even want",
    "doesn't want",
    "does not want",
    "didn't want",
    "did not want",
    "won't want",
    "wouldn't want",
    "would not want",
    "never want",
    "never wanted",
    "no longer want",
    "no longer wants",
    "not wanting",
)
CANNOT = ("can't", "cant", f"can{CURLY}t", "cannot", "can not", "couldn't", "couldnt", "could not")


def forms(stem: str, phrases: Iterable[str]) -> list[Row]:
    """Each listed form of a stem, bare: every one triggers the flow."""
    return [(f"{stem}: {phrase}", phrase, FLOW) for phrase in phrases]


# One table (controller ruling, fix round 4). First every stem in every form the policy
# lists, then sentences, then messages with no stem.
CORPUS: list[Row] = [
    *forms("suicid-", ["suicide", "suicides", "suicidal", "suicidality", "Suicide"]),
    *forms(
        "self-harm",
        [
            "self-harm",
            "self harm",
            "selfharm",
            "self-harms",
            "self-harmed",
            "self-harming",
            "SELF-HARM",
        ],
    ),
    *forms("overdos-", ["overdose", "overdoses", "overdosed", "overdosing"]),
    *forms(
        "kill/hurt/harm/cut + self",
        [
            f"{verb} {self}"
            for verb, self in product(
                (
                    "kill",
                    "kills",
                    "killed",
                    "killing",
                    "hurt",
                    "hurts",
                    "hurting",
                    "harm",
                    "harms",
                    "harmed",
                    "harming",
                    "cut",
                    "cuts",
                    "cutting",
                ),
                SELVES,
            )
        ],
    ),
    *forms("end it all", ["end it all", "ends it all", "ended it all", "ending it all"]),
    *forms(
        "end/take + a life",
        [
            f"{verb} {whose} {life}"
            for verb, whose, life in product(
                ("end", "ends", "ended", "ending", "take", "takes", "took", "taking", "taken"),
                WHOSE,
                ("life", "own life", "lives", "own lives"),
            )
        ],
    ),
    *forms(
        "intent + die",
        [f"{intent} {adverb}die" for intent, adverb in product(INTENTS, ("", "just ", "really "))],
    ),
    *forms(
        "thinking about/of + dying",
        [
            f"{verb} {about} {adverb}dying"
            for verb, about, adverb in product(THINKING, ("about", "of"), ("", "just "))
        ],
    ),
    *forms(
        "wish + dead",
        [
            *(
                f"{wish} {who} {was} dead"
                for wish, who, was in product(
                    ("wish", "wishes", "wished", "wishing"), PRONOUNS, ("was", "were")
                )
            ),
            "wish that I was dead",
            "wish I could die",
            "wish I could just die",
            "wished she would die",
        ],
    ),
    *forms(
        "better off dead/without",
        [
            "better off dead",
            *(f"better off without {who}" for who in ("me", "you", "him", "her", "us", "them")),
        ],
    ),
    *forms(
        "not want to live/be alive/be here",
        [f"{neg} to {what}" for neg, what in product(NOT_WANTING, ("live", "be alive", "be here"))],
    ),
    *forms("no reason to", ["no reason to live", "no reason to go on"]),
    *forms("cannot go on", [f"{cannot} go on" for cannot in CANNOT]),
    # Sentences: the earlier corpus (fix rounds 1-3), every row of which held a stem.
    ("intent + kill myself", "Honestly I want to kill myself, nothing is working.", FLOW),
    ("intent (perfect) + end my life", "I've been thinking about ending my life.", FLOW),
    ("intent + die, clause end", "Some days I just want to die.", FLOW),
    ("informal intent + die", "Some days I wanna die.", FLOW),
    ("capitals", "Some days I Want To Die.", FLOW),
    ("I feel suicidal", "I feel suicidal most days since I lost my job.", FLOW),
    ("I have been self-harming", "I have been self-harming again.", FLOW),
    ("I keep hurting myself", "I keep hurting myself.", FLOW),
    ("I don't want to be alive", "I don't want to be alive any more.", FLOW),
    ("I do not want to be here any more", "I do not want to be here any more.", FLOW),
    (
        "better off if I took my own life",
        "Everyone would be better off if I took my own life",
        FLOW,
    ),
    ("I can't go on", "I can't go on.", FLOW),
    ("professional: suicide prevention", "I volunteer on a suicide prevention helpline.", FLOW),
    ("professional: self-harm services", "I'd like to work in self-harm support services.", FLOW),
    ("third party: feeling suicidal", "I answer calls from people feeling suicidal.", FLOW),
    ("third party: going to die", "Print is going to die, so I want to retrain.", FLOW),
    ("figurative: die of boredom", "I am going to die of boredom in this job.", FLOW),
    (
        "figurative: killing myself with work",
        "I'm killing myself with overtime at the depot.",
        FLOW,
    ),
    ("object: take my life in a direction", "I want to take my life in a new direction.", FLOW),
    ("object: took my life savings", "I took my life savings out to retrain.", FLOW),
    ("object: taken my life savings", "Retraining has taken my life savings.", FLOW),
    ("object: live in a place", "I don't want to live in London.", FLOW),
    ("injury: hurt myself lifting", "I hurt myself lifting boxes at the warehouse.", FLOW),
    ("injury: kept cutting myself", "I kept cutting myself on the packaging tape.", FLOW),
    ("course: no reason to go on with", "There is no reason to go on with the course.", FLOW),
    ("course: cannot go on with", "I cannot go on with this course.", FLOW),
    ("job: don't want to be here", "I don't want to be here in five years.", FLOW),
    # The re-review 3 career probes that hold a stem: accepted false positives (H-12).
    (
        "career: took my life savings",
        "I would be better off if I took my life savings and retrained.",
        FLOW,
    ),
    (
        "career: ending my life sciences career",
        "I am thinking about ending my life sciences career.",
        FLOW,
    ),
    (
        "career: end my life coaching business",
        "I want to end my life coaching business and teach.",
        FLOW,
    ),
    (
        "career: team better off without me",
        "My old team is better off without me, so I want a new role.",
        FLOW,
    ),
    (
        "career: hurt myself lifting",
        "I am going to hurt myself lifting these boxes at the depot.",
        FLOW,
    ),
    ("career: keep cutting myself", "The tape is sharp and I keep cutting myself.", FLOW),
    ("career: did not want to live in", "He did not want to live in London.", FLOW),
    ("career: does not want to live in", "She does not want to live in Leeds.", FLOW),
    ("career: could not go on with", "I could not go on with the accounting course.", FLOW),
    # No stem: nothing, however close the words.
    ("lifeguard", "I am planning to end my lifeguard job this summer.", NO_FLOW),
    ("lifelong", "I want to end my lifelong career in retail.", NO_FLOW),
    ("lifestyle", "I want to end my lifestyle blog.", NO_FLOW),
    ("working life", "I want to end my working life in teaching.", NO_FLOW),
    ("life sciences, no verb", "I studied life sciences at college.", NO_FLOW),
    ("life savings, no verb", "I spent my life savings on the course.", NO_FLOW),
    ("workplace cuts", "There were job cuts at work this year.", NO_FLOW),
    ("cut costs", "I cut costs in my team.", NO_FLOW),
    ("without meetings", "The team would be better off without meetings on Fridays.", NO_FLOW),
    ("better off without a thing", "We would be better off without the old rota.", NO_FLOW),
    ("self-esteem", "Redundancy hurt my self-esteem.", NO_FLOW),
    ("want to live in", "I want to live in Leeds.", NO_FLOW),
    ("go online", "I can't go online at work.", NO_FLOW),
    ("die down", "The noise will die down soon.", NO_FLOW),
    ("dying to", "I'm dying to try woodwork.", NO_FLOW),
    ("killing me", "This commute is killing me.", NO_FLOW),
    ("kill for", "I'd kill for a four-day week.", NO_FLOW),
    ("want to quit", "The deadline pressure made me want to quit.", NO_FLOW),
    ("overwhelmed", "I feel a bit overwhelmed by all the options.", NO_FLOW),
    ("a named condition", "I have dyslexia, so long written tests are hard.", NO_FLOW),
]


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize(("shape", "message", "flow"), CORPUS, ids=[row[0] for row in CORPUS])
def test_any_listed_stem_triggers_the_support_flow_and_nothing_else_does(
    shape: str, message: str, flow: bool
) -> None:
    assert has_risk_stem(message) is flow, shape
    # Whatever surrounds it: a stem inside other words still counts, and none appears.
    assert has_risk_stem(f"At work, {message}, and so on.") is flow, shape


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
