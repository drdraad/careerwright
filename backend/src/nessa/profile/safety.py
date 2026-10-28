"""The minimal response policy for explicit acute distress and inappropriate inference (spec
section 4, "Uncertainty and emotional comfort"; S2.6; PROF-09, REC1-02).

It is kept apart from career suitability: nothing here scores, labels or remembers the
person, and nothing it sees reaches the profile or a suggestion.

- **Explicit acute distress.** A message that says so in so many words (wanting to die,
  suicide, self-harm) is answered at once with a fixed support response and the UK services
  below, before any model call: it is not sent to the interviewer, not stored as a turn and
  never used for suggestions. Only explicit wording counts, so ordinary figures of speech
  ("this commute is killing me") do not; a person shown the response by mistake can choose
  to send the message anyway. Clinical screening is out of scope; this is not one.
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

POLICY_VERSION = "support-policy-1"
CHECKED_ON = "2026-10-28"
REVIEW_STATUS = "provisional: needs reviewed sign-off (human gate H-12)"

# Explicit statements only. Matched case-insensitively on whole words.
_ACUTE_DISTRESS = re.compile(
    r"\b(?:"
    r"kill(?:ing)? myself|end(?:ing)? (?:it all|my (?:own )?life)|"
    r"t(?:ake|aking|ook) my (?:own )?life|suicid(?:e|al)|self[- ]?harm(?:ing|ed)?|"
    r"(?:harm|hurt)(?:ing)? myself|want(?:ed)? to die|wish(?:ed)? (?:i|I) (?:was|were) dead|"
    r"better off dead|(?:do not|don't|dont) want to (?:be alive|live|be here any ?more)|"
    r"no reason to (?:live|go on)"
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


@dataclass(frozen=True)
class SupportConcern:
    """Why the support response was shown instead of sending the message on."""

    policy: str
    policy_version: str


def screen_message(message: str) -> SupportConcern | None:
    """The support response's policy if the message explicitly expresses acute distress."""
    if _ACUTE_DISTRESS.search(message):
        return SupportConcern("acute_distress", POLICY_VERSION)
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
_MBTI = re.compile(r"\b[IE][NS][TF][JP]\b")  # type codes are written in capitals
_PERCENT = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?(?:%|per ?cent\b)", re.IGNORECASE)


def _words(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])", re.IGNORECASE)


_HEALTH_PATTERNS = tuple((term, _words(term)) for term in _HEALTH)
_TYPE_PATTERNS = tuple((term, _words(term)) for term in (*_TYPES, *_DEMOGRAPHIC))


def _found(text: str) -> list[str]:
    terms = [t for t, pattern in (*_HEALTH_PATTERNS, *_TYPE_PATTERNS) if pattern.search(text)]
    terms += _MBTI.findall(text)
    terms += [m.group(0).casefold() for m in _PERCENT.finditer(text)]
    return terms


def _said(term: str, person: str) -> bool:
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
    return _words(term).search(person) is not None


def inferred_sensitive_terms(model_texts: Iterable[str], person_texts: Iterable[str]) -> list[str]:
    """Health conditions, diagnoses, type labels, protected characteristics and percentages
    in the model's text that the person's own words never used, in order of appearance."""
    person = "\n".join(person_texts)
    found: list[str] = []
    for text in model_texts:
        for term in _found(text):
            if term not in found and not _said(term, person):
                found.append(term)
    return found


def recorded_health_terms(values: Iterable[str]) -> list[str]:
    """Health conditions in values proposed for career fields (never recorded there)."""
    joined = "\n".join(values)
    return [term for term, pattern in _HEALTH_PATTERNS if pattern.search(joined)]
