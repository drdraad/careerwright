"""The minimal response policy for explicit acute distress and inappropriate inference (spec
section 4, "Uncertainty and emotional comfort"; S2.6; PROF-09, REC1-02).

It is kept apart from career suitability: nothing here scores, labels or remembers the
person, and nothing it sees reaches the profile, a proposal or a suggestion.

- **One recall-first screen** (controller rulings, Task 6 fix rounds 4 and 5; three phrases
  added after session 1: "carry on", "end it", "not exist"). The message
  is first normalised to words (`words_of`: compatibility forms, the listed apostrophe,
  hyphen and dash characters, case, hyphenated compounds split, contractions and a few
  informal forms spelt out). It triggers the support
  flow if a word is a listed risk word (`_risk_word`), or if a listed construction's core
  word has its markers (a negation, a reflexive, a possessive, an intent) within the small
  window each rule names (`_RULES`), so tense, contraction, adverbs and the words between
  do not defeat it within that window. The person sees a calm support panel with the UK
  services below, and the interviewer gets `SUPPORT_TURN_INSTRUCTION` for that turn only
  (any next question it still writes is dropped, `interview.check_turn`); the message is
  sent as usual, and a refused send shows the panel with its refusal. The
  screen does not try to judge intent, so a stem inside career phrasing ("took my life
  savings") triggers it too, an accepted false positive; words outside the lists or the
  windows get nothing ("this commute is killing me"). Whether a message triggers it is
  recomputed from the message every time it is needed and never stored. Clinical
  screening is out of scope; this is not one.
- **Inference.** Model output may not suggest a health condition, a diagnosis or a
  personality type the person never mentioned, and never gives a percentage the person did
  not use (no "92% match"). A condition the person names may be acknowledged, to ask which
  adjustment would help, but is never recorded in a career field.

**Accepted for L0 as built by the product owner at session 1 (2026-10-28; human gate H-12):**
the wording, the word lists, the windows and the resources. The three phrasings they asked
for there were added on 2026-10-28 after the session, as constructions (a controller
ruling), and are not yet reviewed as built (`REVIEW_STATUS`). The resources were checked on
the services' own pages on `CHECKED_ON`; nothing here is invented, and anything not on those
pages is left out.
"""

import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass

POLICY_VERSION = "support-policy-7"
CHECKED_ON = "2026-10-28"
REVIEW_STATUS = (
    "accepted for L0 at session 1 (human gate H-12); the three phrasings added on 2026-10-28 "
    "are not yet reviewed as built"
)

# Normalisation: the listed apostrophe variants to `'`, the hyphens U+2010 and U+2011 to `-`,
# the dashes U+2012 to U+2015 and U+2212 to a space; invisible characters (soft hyphen,
# zero-width spaces and joiners) removed. Other characters are not mapped.
_CHARACTERS = str.maketrans(
    {
        **dict.fromkeys(map(chr, (0x2018, 0x2019, 0x201B, 0x02BB, 0x02BC, 0x0060, 0x00B4)), "'"),
        **dict.fromkeys(map(chr, (0x2010, 0x2011)), "-"),
        **dict.fromkeys(map(chr, (0x2012, 0x2013, 0x2014, 0x2015, 0x2212)), " "),
        **dict.fromkeys(map(chr, (0x00AD, 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF)), ""),
    }
)
_WORD = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*")
# Contractions and informal forms written without an apostrophe, spelt out.
_SPELT_OUT: dict[str, tuple[str, ...]] = {
    "cannot": ("can", "not"),
    "cant": ("can", "not"),
    "dont": ("do", "not"),
    "doesnt": ("does", "not"),
    "didnt": ("did", "not"),
    "couldnt": ("could", "not"),
    "wont": ("will", "not"),
    "wouldnt": ("would", "not"),
    "shouldnt": ("should", "not"),
    "isnt": ("is", "not"),
    "arent": ("are", "not"),
    "wasnt": ("was", "not"),
    "werent": ("were", "not"),
    "hasnt": ("has", "not"),
    "havent": ("have", "not"),
    "hadnt": ("had", "not"),
    "aint": ("is", "not"),
    "wanna": ("want", "to"),
    "gonna": ("going", "to"),
    "gotta": ("got", "to"),
    "tryna": ("trying", "to"),
    "im": ("i", "am"),
    "ive": ("i", "have"),
}
_NOT_STEMS = {"ca": "can", "wo": "will", "sha": "shall", "ai": "is"}  # can't, won't, ...
_CLITICS = (("'m", "am"), ("'re", "are"), ("'ve", "have"), ("'ll", "will"), ("'d", "would"))


def _spelt_out(word: str) -> tuple[str, ...]:
    if word in _SPELT_OUT:
        return _SPELT_OUT[word]
    if word.endswith("n't"):
        stem = word[:-3]
        return (_NOT_STEMS.get(stem, stem), "not")
    for clitic, full in _CLITICS:
        if word.endswith(clitic) and len(word) > len(clitic):
            return (*_spelt_out(word[: -len(clitic)]), full)
    return (word,)


def _compound_parts(word: str) -> list[str]:
    parts: list[str] = []
    for part in word.split("-"):
        if parts and parts[-1].endswith("self-"):
            parts[-1] += part
        elif part == "self":
            parts.append("self-")
        else:
            parts.append(part)
    return [part.removesuffix("-") for part in parts]


def words_of(message: str) -> list[str]:
    """The message's words as the screen reads them: compatibility forms (NFKC), the listed
    apostrophe, hyphen and dash characters, lower case, and contractions spelt out ("don't" is "do
    not", "I'd" is "I would", "wanna" is "want to"). A hyphenated compound is split into its
    parts, so each is a word ("anti-suicide" is "anti suicide", "die-so" is "die so"), except
    that "self" stays joined to the part after it ("self-harm", "self-esteem")."""
    text = unicodedata.normalize("NFKC", message).translate(_CHARACTERS).casefold()
    return [
        part
        for word in _WORD.findall(text)
        for piece in _compound_parts(word)
        for part in _spelt_out(piece)
    ]


# The listed words. Each construction rule below anchors on a core word and looks for its
# markers within a small window of words; the windows are part of the policy (H-12).
_INJURE = {"kill", "kills", "killed", "killing", "hurt", "hurts", "hurting", "harm", "harms"}
_INJURE |= {"harmed", "harming", "cut", "cuts", "cutting"}
_REFLEXIVES = {"myself", "yourself", "himself", "herself", "ourselves", "yourselves"}
_REFLEXIVES |= {"themselves", "themself", "oneself"}
_SELF_OWNERS = {"my", "your", "him", "her", "our", "them", "one"}  # "my self", spelt apart
_END = {"end", "ends", "ended", "ending"}
_END_OR_TAKE = _END | {"take", "takes", "took", "taking", "taken"}
_POSSESSIVES = {"my", "your", "his", "her", "our", "their", "own"}  # and any "...'s"
_INTENTS = {"want", "wants", "wanted", "wanting", "going", "ready", "tempted", "urge", "urges"}
_INTENTS |= {"plan", "plans", "planned", "planning", "try", "tries", "tried", "trying"}
_INTENTS |= {"intend", "intends", "intended", "intending", "decide", "decides", "decided"}
_INTENTS |= {"deciding", "wish", "wishes", "wished", "wishing"}
_DEATH = {"die", "dies", "died", "dead"}
_THINKING = {"think", "thinks", "thinking", "thought", "thoughts"}
_WANT = {"want", "wants", "wanted", "wanting"}
_WANT_OR_WISH = _WANT | {"wish", "wishes", "wished", "wishing"}
_GO_OR_CARRY = {"go", "goes", "going", "went", "gone", "carry", "carries", "carried", "carrying"}
_EXIST = {"exist", "exists", "existed"}  # not "existing", mostly an adjective in career text
_PRONOUNS = {"me", "you", "him", "her", "us", "them"}

Words = list[str]


def _after(words: Words, i: int, window: int) -> range:
    return range(i + 1, min(i + 1 + window, len(words)))


def _before(words: Words, i: int, window: int) -> range:
    return range(max(0, i - window), i)


def _negation(words: Words, k: int) -> bool:
    return words[k] in {"not", "never"} or (words[k] == "longer" and k > 0 and words[k - 1] == "no")


def _reflexive(words: Words, k: int) -> bool:
    return words[k] in _REFLEXIVES or (
        words[k] == "self" and k > 0 and words[k - 1] in _SELF_OWNERS
    )


def _go_or_carry_on(words: Words, k: int) -> bool:
    return words[k] in _GO_OR_CARRY and words[k + 1 : k + 2] == ["on"]


def _risk_word(words: Words, i: int) -> bool:
    """A word starting suicid-, overdos-, self-harm or selfharm, or "self" followed by a word
    starting harm."""
    word = words[i]
    if word.startswith(("suicid", "overdos", "self-harm", "selfharm")):
        return True
    return word == "self" and i + 1 < len(words) and words[i + 1].startswith("harm")


def _self_injury(words: Words, i: int) -> bool:
    """kill / hurt / harm / cut, then a reflexive within 3 words ("cut myself")."""
    return words[i] in _INJURE and any(_reflexive(words, k) for k in _after(words, i, 3))


def _end_it_all(words: Words, i: int) -> bool:
    return words[i] in _END and words[i + 1 : i + 3] == ["it", "all"]


def _to_end_it(words: Words, i: int) -> bool:
    """An intent or a wish, then end (-s, -ed, -ing) and "it" within 4 words ("want to end
    it"). "end it all" needs no intent (`_end_it_all`)."""
    return words[i] in _INTENTS and any(
        words[k] in _END and words[k + 1 : k + 2] == ["it"] for k in _after(words, i, 4)
    )


def _a_life(words: Words, i: int) -> bool:
    """end / take, then "life" or "lives" within 3 words, with a possessive between ("took
    my own life", "ended Alex's life")."""
    if words[i] not in _END_OR_TAKE:
        return False
    for k in _after(words, i, 3):
        if words[k] in {"life", "lives"}:
            between = words[i + 1 : k]
            return any(w in _POSSESSIVES or w.endswith("'s") for w in between)
    return False


def _to_die(words: Words, i: int) -> bool:
    """An intent or a wish, then die, died or dead within 4 words ("want to just die", "wish
    I'd died", "wish I was dead")."""
    return words[i] in _INTENTS and any(words[k] in _DEATH for k in _after(words, i, 4))


def _dying(words: Words, i: int) -> bool:
    """think / thought(s), then "dying" within 4 words ("thoughts of dying")."""
    return words[i] in _THINKING and any(words[k] == "dying" for k in _after(words, i, 4))


def _not_living(words: Words, i: int) -> bool:
    """A negation within 3 words before "want", and "live", "alive" or "be here" within 3
    after ("hadn't wanted to live", "don't even really want to be alive")."""
    return (
        words[i] in _WANT
        and any(_negation(words, k) for k in _before(words, i, 3))
        and any(
            words[k] in {"live", "alive"} or (words[k] == "here" and words[k - 1] == "be")
            for k in _after(words, i, 3)
        )
    )


def _not_exist(words: Words, i: int) -> bool:
    """exist, exists or existed, with want or wish (any form) and a negation within 4 words
    before it ("want to not exist", "wish I didn't exist", "don't want to exist"). Only want
    and wish: with the other intents, "isn't going to exist" about a job would trigger it
    (fix round 1)."""
    before = _before(words, i, 4)
    return (
        words[i] in _EXIST
        and any(words[k] in _WANT_OR_WISH for k in before)
        and any(_negation(words, k) for k in before)
    )


def _no_reason(words: Words, i: int) -> bool:
    """The word reason(s), with no, not or never within 3 words before it, and live, living,
    alive, "go on" or "carry on" within 4 after ("isn't any reason to go on", "no real reason
    to live")."""
    return (
        words[i] in {"reason", "reasons"}
        and any(words[k] in {"no", "not", "never"} for k in _before(words, i, 3))
        and any(
            words[k] in {"live", "living", "alive"} or _go_or_carry_on(words, k)
            for k in _after(words, i, 4)
        )
    )


def _cannot_go_on(words: Words, i: int) -> bool:
    """The words go on or carry on, with a negation within 3 words before them and can or
    could within 4 ("can no longer go on", "can't really go on", "can't carry on")."""
    return (
        _go_or_carry_on(words, i)
        and any(_negation(words, k) for k in _before(words, i, 3))
        and any(words[k] in {"can", "could"} for k in _before(words, i, 4))
    )


def _better_off(words: Words, i: int) -> bool:
    """The words better off, then dead, or without me / you / him / her / us / them, within 4
    words."""
    return (
        words[i] == "off"
        and i > 0
        and words[i - 1] == "better"
        and any(
            words[k] == "dead"
            or (words[k] == "without" and k + 1 < len(words) and words[k + 1] in _PRONOUNS)
            for k in _after(words, i, 4)
        )
    )


_RULES: tuple[Callable[[Words, int], bool], ...] = (
    _risk_word,
    _self_injury,
    _end_it_all,
    _to_end_it,
    _a_life,
    _to_die,
    _dying,
    _not_living,
    _not_exist,
    _no_reason,
    _cannot_go_on,
    _better_off,
)

SUPPORT_NOTE = (
    "If anything you mentioned is about how you are feeling, support is available any time, "
    "from people trained to help. Your message was sent to Nessa as usual."
)
# The same panel beside a send that was refused (stale, too long, over budget, no key...).
SUPPORT_NOTE_NOT_SENT = (
    "If anything you mentioned is about how you are feeling, support is available any time, "
    "from people trained to help. Your message was not sent; the reason is shown below."
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
    """Whether the message holds a listed risk word or construction, so triggers the
    support flow."""
    words = words_of(message)
    return any(rule(words, i) for i in range(len(words)) for rule in _RULES)


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
