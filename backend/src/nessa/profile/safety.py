"""The minimal response policy for explicit acute distress and inappropriate inference (spec
section 4, "Uncertainty and emotional comfort"; S2.6; PROF-09, REC1-02).

It is kept apart from career suitability: nothing here scores, labels or remembers the
person, and nothing it sees reaches the profile, a proposal or a suggestion.

- **One recall-first screen** (controller ruling, Task 6 fix round 4). A message holding
  any listed risk stem (`_RISK`), in any inflection, person or tense, with contracted or
  uncontracted negation, triggers the support flow: the person sees a calm support panel
  with the UK services below, and the interviewer gets `SUPPORT_TURN_INSTRUCTION` for that
  turn only. The message is sent as usual: nothing is held back or blocked. The screen does
  not try to judge intent, so a stem inside career phrasing ("took my life savings")
  triggers it too, an accepted false positive; a message with no stem gets nothing ("this
  commute is killing me"). Whether a message triggers it is recomputed from the message
  every time it is needed and never stored. Clinical screening is out of scope; this is
  not one.
- **Inference.** Model output may not suggest a health condition, a diagnosis or a
  personality type the person never mentioned, and never gives a percentage the person did
  not use (no "92% match"). A condition the person names may be acknowledged, to ask which
  adjustment would help, but is never recorded in a career field.

**Provisional, needs reviewed sign-off (ruling R6; human gate H-12):** the wording, the stem
list and the resources. The resources were checked on the services' own pages on
`CHECKED_ON`; nothing here is invented, and anything not on those pages is left out.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass

POLICY_VERSION = "support-policy-4"
CHECKED_ON = "2026-10-28"
REVIEW_STATUS = "provisional: needs reviewed sign-off (human gate H-12)"

_A = r"[^\w\s]?"  # an apostrophe, straight or curly, or none ("don't", "dont")
_ADVERB = r"(?:\s+(?:just|really|simply|actually|honestly|even|truly|still))?"
_SELF = r"(?:my|your|him|her|our|them|one)\s?sel(?:f|ves)(?![\w-])"  # not "self-esteem"
_LIFE = rf"(?:my|your|his|her|our|their|one{_A}s)\s+(?:own\s+)?li(?:fe|ves)\b"
_INTENT = (
    r"(?:(?:want(?:s|ed|ing)?|going|ready|plan(?:s|ned|ning)?|tempted|tr(?:y|ies|ied|ying)|"
    r"intend(?:s|ed|ing)?|decid(?:e|es|ed|ing)|urges?)\s+to|wanna|gonna)"
)
_NOT = rf"(?:\b(?:do|does|did|wo|would|could|should)n{_A}t|\bnot|\bnever|\bno\s+longer)"
_CANNOT = rf"(?:\bca(?:n{_A}t|nnot|n\s+not)|\bcould(?:n{_A}t|\s+not))"
_WHO = r"(?:I|you|he|she|we|they)"

# The listed risk stems. Each branch is one stem in all of its forms, whatever surrounds it;
# `\b` keeps a stem from matching inside a longer word ("lifeguard", "meetings").
_RISK = re.compile(
    "|".join(
        (
            r"\bsuicid\w*",
            r"\bself[- ]?harm\w*",
            r"\boverdos\w*",
            rf"\b(?:kill(?:s|ed|ing)?|hurt(?:s|ing)?|harm(?:s|ed|ing)?|cut(?:s|ting)?)\s+{_SELF}",
            rf"\bend(?:s|ed|ing)?\s+(?:it\s+all\b|{_LIFE})",
            rf"\bt(?:ake|akes|aking|aken|ook)\s+{_LIFE}",
            rf"\b{_INTENT}{_ADVERB}\s+die\b",
            rf"\b(?:think(?:s|ing)?|thoughts?)\s+(?:about|of){_ADVERB}\s+dying\b",
            rf"\bwish(?:es|ed|ing)?\s+(?:that\s+)?{_WHO}\s+"
            rf"(?:(?:was|were)\s+dead|(?:could|would){_ADVERB}\s+die)\b",
            r"\bbetter\s+off\s+(?:dead|without\s+(?:me|you|him|her|us|them))\b",
            rf"{_NOT}{_ADVERB}\s+want(?:s|ed|ing)?\s+to\s+(?:live|be\s+alive|be\s+here)\b",
            r"\bno\s+reason\s+to\s+(?:live|go\s+on)\b",
            rf"{_CANNOT}\s+go\s+on\b",
        )
    ),
    re.IGNORECASE,
)

SUPPORT_NOTE = (
    "If anything you mentioned is about how you are feeling, support is available any time, "
    "from people trained to help. Your message was sent to Nessa as usual."
)
# Added to the interviewer's instructions for a turn whose message triggers the screen, and
# for that turn only. It names neither the screen nor anything matched.
SUPPORT_TURN_INSTRUCTION = (
    "For this message only: acknowledge what the person said, briefly and kindly; offer one "
    "smaller next step, such as pausing here or coming back later; and ask no career question "
    "(next_question is null). Give no phone numbers and name no services."
)


@dataclass(frozen=True)
class SupportResource:
    name: str
    contact: str
    when: str
    source_url: str
    checked_on: str


SUPPORT_RESOURCES: tuple[SupportResource, ...] = (
    SupportResource(
        "Emergency services",
        "Call 999 or go to A&E",
        "If your life is at risk now, or you can't keep yourself safe",
        "https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/",
        CHECKED_ON,
    ),
    SupportResource(
        "NHS 111",
        "Call 111 and choose the mental health option, or use 111 online",
        "For urgent mental health help and advice",
        "https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/",
        CHECKED_ON,
    ),
    SupportResource(
        "Samaritans",
        "Call 116 123 (free, any time, day or night)",
        "To talk to someone who will listen",
        "https://www.samaritans.org/how-we-can-help/contact-samaritan/",
        CHECKED_ON,
    ),
    SupportResource(
        "Shout",
        "Text SHOUT to 85258 (free, 24/7)",
        "If you would rather text than talk",
        "https://giveusashout.org/get-help/",
        CHECKED_ON,
    ),
)


def has_risk_stem(message: str) -> bool:
    """Whether the message holds a listed risk stem, so triggers the support flow."""
    return _RISK.search(message) is not None


# Health conditions and diagnoses a career conversation must never infer or record.
_HEALTH = (
    "adhd",
    "anorexia",
    "anxiety disorder",
    "asperger",
    "autism",
    "autistic",
    "bipolar",
    "borderline",
    "bulimia",
    "depression",
    "depressed",
    "dyscalculia",
    "dyslexia",
    "dyslexic",
    "dyspraxia",
    "eating disorder",
    "mental illness",
    "neurodivergent",
    "neurodiverse",
    "obsessive compulsive",
    "ocd",
    "panic disorder",
    "personality disorder",
    "psychosis",
    "ptsd",
    "schizophrenia",
)
# Categorical type labels (no MBTI-style assignment, spec section 4).
_TYPES = (
    "enneagram",
    "extravert",
    "extraverted",
    "extrovert",
    "extroverted",
    "introvert",
    "introverted",
    "personality type",
)
# Protected characteristics, which never decide suitability (spec section 3). Only clear
# words: "young people" or "older adults" can name legitimate work, so they are not here.
_DEMOGRAPHIC = (
    "ethnic",
    "ethnicity",
    "father",
    "female",
    "gender",
    "girl",
    "girls",
    "male",
    "mother",
    "mum",
    "nationality",
    "pregnancy",
    "pregnant",
    "religion",
    "religious",
    "woman",
    "women",
)
# Kindred words: a person who wrote one may be answered with another, since naming who the
# work serves ("new mothers", so "maternity work for women") is not a guess about the person.
_KINDRED = (
    frozenset({"female", "girl", "girls", "mother", "mum", "woman", "women"}),
    frozenset({"father", "male"}),
    frozenset({"ethnic", "ethnicity"}),
    frozenset({"pregnancy", "pregnant"}),
    frozenset({"religion", "religious"}),
)
_MBTI = re.compile(r"\b[IE][NS][TF][JP]\b")  # type codes are written in capitals
_PERCENT = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?(?:%|per ?cent\b)", re.IGNORECASE)


def _words(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])", re.IGNORECASE)


def _said_any(terms: Iterable[str], person: str) -> bool:
    """Whether the person used one of the terms, singular or plural ("mothers", "mums")."""
    return any(
        re.search(rf"(?<![\w-]){re.escape(term)}s?(?![\w-])", person, re.IGNORECASE)
        for term in terms
    )


_HEALTH_PATTERNS = tuple((term, _words(term)) for term in _HEALTH)
_TYPE_PATTERNS = tuple((term, _words(term)) for term in (*_TYPES, *_DEMOGRAPHIC))


def _found(text: str) -> list[str]:
    terms = [t for t, pattern in (*_HEALTH_PATTERNS, *_TYPE_PATTERNS) if pattern.search(text)]
    terms += _MBTI.findall(text)
    terms += [m.group(0).casefold() for m in _PERCENT.finditer(text)]
    return terms


def _said(term: str, person: str, kindred: bool) -> bool:
    if _MBTI.fullmatch(term):
        return re.search(rf"\b{term}\b", person, re.IGNORECASE) is not None
    if _PERCENT.fullmatch(term):
        number = re.match(r"\d{1,3}(?:\.\d+)?", term)
        return (
            number is not None
            and re.search(
                rf"\b{re.escape(number.group(0))}\s?(?:%|per ?cent\b)", person, re.IGNORECASE
            )
            is not None
        )
    group = next((group for group in _KINDRED if term in group), None) if kindred else None
    return _said_any(group or frozenset({term}), person)


def inferred_sensitive_terms(
    model_texts: Iterable[str], person_texts: Iterable[str], *, kindred: bool = False
) -> list[str]:
    """Health conditions, diagnoses, type labels, protected characteristics and percentages
    in the model's text that the person's own words never used, in order of appearance.
    `kindred` (searches only): a kindred word counts as the person's own, since a search
    naming who the work serves is not a guess about the person; a reply about the person
    gets no such allowance."""
    person = "\n".join(person_texts)
    found: list[str] = []
    for text in model_texts:
        for term in _found(text):
            if term not in found and not _said(term, person, kindred):
                found.append(term)
    return found


def recorded_health_terms(values: Iterable[str]) -> list[str]:
    """Health conditions in values proposed for career fields (never recorded there)."""
    joined = "\n".join(values)
    return [term for term, pattern in _HEALTH_PATTERNS if pattern.search(joined)]
