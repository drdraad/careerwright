"""The minimal response policy for explicit acute distress and inappropriate inference (spec
section 4, "Uncertainty and emotional comfort"; S2.6; PROF-09, REC1-02).

It is kept apart from career suitability: nothing here scores, labels or remembers the
person, and nothing it sees reaches the profile or a suggestion.

- **A two-tier screen** (controller rulings, Task 6 fix rounds 2 and 3):
  - *Acute* (tier 1, narrow): a first-person, present statement of intent or distress ("I
    want to die", "I feel suicidal", "I've been self-harming", "I don't want to live any
    more") is answered at once with a fixed support response and the UK services below,
    before any model call: it is not sent to the interviewer, not stored and never used
    for suggestions. A person shown it by mistake can choose to send the message anyway.
    A risk word in a professional, third-party, figurative or object frame ("people
    feeling suicidal", "print is going to die", "suicide prevention work") never reaches
    it.
  - *Mention* (tier 2, broad): any other message containing a risk stem, in any
    inflection ("I took my life savings", "killing myself with overtime", "cutting myself
    on the tape") is sent as usual, and the person sees a calm support note with the same
    services beside it. Nothing containing a risk stem is silently dropped, and ordinary
    career talk is never blocked. The note is derived from the request each time and never
    stored.
  Only words count, so figures of speech without a risk stem ("this commute is killing me")
  get nothing. Tier 1 rests on positive evidence only (who and what), never on a list of
  words that excuse a match. Clinical screening is out of scope; this is not one.
- **Inference.** Model output may not suggest a health condition, a diagnosis or a
  personality type the person never mentioned, and never gives a percentage the person did
  not use (no "92% match"). A condition the person names may be acknowledged, to ask which
  adjustment would help, but is never recorded in a career field.

**Provisional, needs reviewed sign-off (ruling R6; human gate H-12):** the wording, the
phrase lists and the resources. The resources were checked on the services' own pages on
`CHECKED_ON`; nothing here is invented, and anything not on those pages is left out.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

POLICY_VERSION = "support-policy-3"
CHECKED_ON = "2026-10-28"
REVIEW_STATUS = "provisional: needs reviewed sign-off (human gate H-12)"

_A = r"[^\w\s]?"  # an apostrophe, straight or curly, or none ("don't", "dont")
_END = r"(?=\s*(?:[.!?,;:]|$))"  # the end of a clause
_MORE = r"(?:\s+(?:any\s?more|again))?"
_NOT = rf"(?:don{_A}t|do\s+not)"
_CANNOT = rf"(?:can{_A}t|cannot|can\s+not)"

# Tier 1: first person, present intent or distress; positive evidence only. Every branch
# starts from "I" (or "me"), so a professional, third-party, figurative or object frame
# never reaches it ("people feeling suicidal", "print is going to die", "die of boredom",
# "suicide prevention work", "I have self-harm awareness training").
_I = (
    rf"\bI(?:{_A}m|\s+am|{_A}ve\s+been|\s+have\s+been)?"
    r"(?:\s+(?:just|really|honestly|still|so|keep|often|sometimes))*"
)
_INTENT = (
    r"(?:want\s+to|wanna|(?:am\s+)?going\s+to|gonna|plan(?:ning)?\s+to|intend(?:ing)?\s+to|"
    r"(?:thinking|think)\s+(?:about|of))"
)
# The acts. "die" only at the end of a clause ("die of boredom", "die on this hill" are not).
_ACT = (
    rf"(?:die{_END}|kill(?:ing)?\s+myself|end(?:ing)?\s+(?:it\s+all|my\s+(?:own\s+)?life)|"
    r"tak(?:e|ing)\s+my\s+own\s+life|hurt(?:ing)?\s+myself|harm(?:ing)?\s+myself)"
)
_ACUTE = re.compile(
    r"(?:"
    rf"{_I}\s+{_INTENT}\s+{_ACT}|"
    rf"\bI(?:{_A}m|\s+am|\s+feel|{_A}m\s+feeling|{_A}ve\s+(?:been(?:\s+feeling)?|felt)|"
    rf"\s+have\s+(?:been(?:\s+feeling)?|felt)|\s+keep\s+feeling)"
    r"\s+(?:so\s+|really\s+|very\s+)?suicidal|"
    rf"\bI\s+(?:self[- ]?harm|harm\s+myself)\b|"
    rf"\bI(?:{_A}m|\s+am|{_A}ve\s+been|\s+have\s+been|\s+keep|{_A}ve\s+started|"
    rf"\s+have\s+started)\s+(?:self[- ]?harming|harming\s+myself)|"
    rf"\bI(?:{_A}m|\s+am|{_A}ve\s+been|\s+have\s+been|\s+keep)\s+(?:hurting|cutting)\s+myself"
    rf"{_MORE}{_END}|"
    r"\bwish(?:ed)?\s+I\s+(?:was|were)\s+dead|"
    rf"\bI(?:{_A}d|\s+would|\s+might)\s+be\s+better\s+off\s+dead|"
    r"\bbetter\s+off\s+(?:without\s+me|if\s+I\s+(?:took|take|ended|end)\s+my\s+(?:own\s+)?life)|"
    rf"\bI\s+{_NOT}\s+want\s+to\s+(?:be\s+alive|be\s+here\s+any\s?more{_END}|"
    rf"live(?:\s+like\s+this|\s+this\s+way)?(?:\s+any\s?more)?{_END})|"
    rf"\bI\s+(?:have|{_A}ve\s+got|see)\s+no\s+reason\s+to\s+(?:live|go\s+on)(?:\s+any\s?more)?{_END}|"
    rf"\bI\s+{_CANNOT}\s+go\s+on(?:\s+any\s?more)?{_END}"
    r")",
    re.IGNORECASE,
)
# Tier 2: every risk stem, in every inflection, whatever surrounds it. Nothing containing
# one reaches no tier.
_RISK = re.compile(
    r"\b(?:"
    r"suicid\w*|self[- ]?harm\w*|overdos\w*|"
    r"(?:kill(?:s|ing|ed)?|hurt(?:s|ing)?|harm(?:s|ing|ed)?|cut(?:s|ting)?)\s+myself|"
    r"end(?:s|ing|ed)?\s+(?:it\s+all|my\s+(?:own\s+)?life)|"
    r"t(?:ake|akes|aking|aken|ook)\s+my\s+(?:own\s+)?life|"
    r"(?:(?:want(?:s|ing|ed)?|going|ready|plan(?:s|ning|ned)?|tempted|try(?:ing)?|"
    r"intend(?:s|ing|ed)?)\s+to|wanna|gonna)\s+die|"
    r"wish(?:es|ed)?\s+I\s+(?:was|were)\s+dead|better\s+off\s+(?:dead|without\s+me)|"
    rf"(?:{_NOT}|doesn{_A}t|didn{_A}t)\s+want\s+to\s+(?:be\s+alive|live|be\s+here)|"
    rf"no\s+reason\s+to\s+(?:live|go\s+on)|(?:{_CANNOT}|couldn{_A}t)\s+go\s+on"
    r")\b",
    re.IGNORECASE,
)

SUPPORT_MESSAGE = (
    "I'm sorry things feel this hard. You don't have to face this on your own, and you "
    "deserve support right now from people trained to help. Your message hasn't been sent to "
    "Nessa's interviewer and nothing has been saved. If you are in danger now or can't keep "
    "yourself safe, call 999 or go to A&E. The career questions can wait until you want to "
    "come back to them."
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


SUPPORT_NOTE = (
    "If anything you mentioned is about how you are feeling, support is available any time, "
    "from people trained to help. Your message was sent to Nessa as usual."
)


class SupportTier(StrEnum):
    ACUTE = "acute_distress"  # the support response; the message is not sent
    MENTION = "risk_mention"  # sent as usual, with a support note beside it


@dataclass(frozen=True)
class SupportConcern:
    """What the screen found in a message, and so what the person sees."""

    tier: SupportTier
    policy_version: str

    @property
    def policy(self) -> str:
        return self.tier.value


def screen_message(message: str) -> SupportConcern | None:
    """Tier 1 for first-person acute distress, tier 2 for any other risk word, else None."""
    if _ACUTE.search(message):
        return SupportConcern(SupportTier.ACUTE, POLICY_VERSION)
    if _RISK.search(message):
        return SupportConcern(SupportTier.MENTION, POLICY_VERSION)
    return None


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
