"""The written "Why this could suit you" (spec section 4, REC-1; D3, ADR 0008 decision 4;
S2.7; ADR 0007 decision 12).

One bounded model call per slate. The run sends the model the confirmed answers the discovery
pinned (the answers that describe work: never a name, place, money or hours, SEC-05) and
ESCO's record of each suggestion on the slate (its title, description and first essential
skills), and gets back a bounded `ExplanationOutput`: for each suggestion, one or two short
claims, each resting on quotations.

`check_explanation` validates it deterministically. Every quotation must be an exact span of
its source, at word boundaries (case, spacing and apostrophes aside): one of the person's
answers, or ESCO's record of the occupation it explains, never another's. Every claim quotes
at least one answer and the record at least once, so it links what the person said to a fact
ESCO holds. A claim may not carry a quotation of its own, a readiness, affordability or
hiring claim, or a health condition, personality type, protected characteristic or
percentage the person never used and the record does not name (`nessa.profile.safety`).
What it returns is the stored `SlateExplanation`, holding each quotation in its source's own
characters, never in the model's.

The written text is an addition only: it never changes a suggestion, its grounding, its place
in the slate or the profile, and the deterministic provenance (`exploration.explain`) is what
exports cite.

**Provisional (R6, H-12):** the readiness, affordability and hiring word lists, and the claim
and quotation bounds, are product policy to be reviewed.
"""

import json
import re
import unicodedata
import uuid
from collections.abc import Iterable, Sequence
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from nessa.catalogue.records import OccupationFacts
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity.model_registry import worst_case_cost_nano_usd
from nessa.profile.discovery import EvidenceItem
from nessa.profile.interview import ProfileField, ProposalOrigin
from nessa.profile.safety import inferred_sensitive_terms

PROMPT_VERSION = "slate-explanation-1"
INPUT_FORMAT: Literal["nessa.slate-explanation-input"] = "nessa.slate-explanation-input"
MAX_CLAIMS = 2
MAX_QUOTES = 3
CLAIM_CHARS = (20, 240)
QUOTE_CHARS = (2, 160)  # and at least one letter
# How much of each ESCO record the prompt carries, longest first: the first step whose
# prompt fits `MAX_PROMPT_BYTES` is used (descriptions are cut at a word; the title is
# always whole). The answers are never cut: each one is a quotable source.
RECORD_STEPS = ((600, 6), (400, 4), (250, 3), (150, 2), (100, 1))
# Bounds for the spend reservation (bytes bound tokens for byte-level BPE tokenizers). With
# two requests on the production model they keep three step attempts within the default
# run limit (`tests/domain/test_spend.py`).
MAX_PROMPT_BYTES = 8_500  # instructions plus the rendered context, at every list bound
SCHEMA_ALLOWANCE_TOKENS = 1_500
MAX_OUTPUT_TOKENS = 2_000
REPAIR_ALLOWANCE_TOKENS = 1_000
# The repair message is capped below its allowance, leaving room for the fence the agent
# puts around it (about 120 bytes; `repair_message`).
REPAIR_MESSAGE_BYTES = 800
ECHO_CHARS = 60  # at most this much of a model's text is repeated back in a problem
MAX_REQUESTS = 2  # the first request and at most one repair
CONTEXT_MARKER = "Explanation context (JSON):\n"
# A content word: a whole word of four letters or more that is not a common function word.
# A quotation must hold one; so must an answer for the note to have anything to quote.
_CONTENT_WORD = re.compile(r"\b[^\W\d_]{4,}\b")
# The entries of four letters or more of a standard English stopword list (NLTK's),
# contraction stems included ("couldn't" gives "couldn"), a few more modal and function
# words, and "work" (too common in ESCO's records to link anything).
COMMON_WORDS = frozenset(
    {"about", "above", "after", "again", "against", "also", "aren", "because", "been"}
    | {"before", "being", "below", "between", "both", "could", "couldn", "didn", "does"}
    | {"doesn", "doing", "down", "during", "each", "every", "from", "further", "hadn"}
    | {"hasn", "have", "haven", "having", "here", "hers", "herself", "himself", "into"}
    | {"itself", "just", "like", "might", "mightn", "more", "most", "much", "must"}
    | {"mustn", "myself", "needn", "once", "only", "other", "ought", "ours", "ourselves"}
    | {"over", "same", "shall", "shan", "should", "shouldn", "some", "such", "than"}
    | {"that", "their", "theirs", "them", "themselves", "then", "there", "these", "they"}
    | {"this", "those", "through", "under", "until", "upon", "using", "very", "wasn"}
    | {"were", "weren", "what", "when", "where", "which", "while", "whom", "whose", "will"}
    | {"with", "within", "without", "would", "wouldn", "your", "yours", "yourself"}
    | {"yourselves", "work", "works", "working"}
)


def content_words(text: str) -> set[str]:
    """The text's content words, folded as quotations are matched (compatibility forms,
    case): "with" written in fullwidth letters is still the function word "with"."""
    return set(_CONTENT_WORD.findall(_folded(text)[0])) - COMMON_WORDS


def quotable(text: str) -> bool:
    """Whether a text holds a content word, so a quotation of it can say something."""
    return bool(content_words(text))


class QuoteSource(StrEnum):
    ANSWER = "answer"  # one of the person's confirmed answers the discovery pinned
    ESCO = "esco"  # ESCO's record of the occupation the claim is about


class RecordPart(StrEnum):
    TITLE = "title"
    DESCRIPTION = "description"
    ESSENTIAL_SKILL = "essential_skill"


class ModelQuote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: QuoteSource
    text: str


class ModelClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    quotes: list[ModelQuote]


class ModelExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occupation: str  # the occupation's ref in the prompt ("o1")
    claims: list[ModelClaim]


class ExplanationOutput(BaseModel):
    """The model's whole output (sent to Meta as a strict JSON schema)."""

    model_config = ConfigDict(extra="forbid")

    explanations: list[ModelExplanation]


class OccupationRecord(BaseModel):
    """ESCO's record of one suggestion, as far as the prompt carries it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    concept_id: uuid.UUID
    esco_uri: str
    title: str
    description: str
    essential_skills: list[str]


class ExplanationInput(BaseModel):
    """Everything an explanation run sends the model: sealed into the run at submission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    format: Literal["nessa.slate-explanation-input"] = INPUT_FORMAT
    prompt_version: str = PROMPT_VERSION
    discovery_id: uuid.UUID
    profile_version: int  # the discovery's pinned version (never sent to the model)
    release: str  # the ESCO release the records come from (never sent to the model)
    answers: list[EvidenceItem]
    occupations: list[OccupationRecord]  # the slate's suggestions, in slate order


class Quotation(BaseModel):
    """A verified quotation, in its source's own characters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: QuoteSource
    answer_field: ProfileField | None  # which answer, for a quotation of the person's
    record_part: RecordPart | None  # which part of ESCO's record, for one of ESCO's
    text: str


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str  # model prose: one sentence, never a quotation of its own
    quotations: list[Quotation]


class WrittenWhy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: uuid.UUID
    title: str
    claims: list[Claim]


class SlateExplanation(BaseModel):
    """An explanation run's validated output (sealed)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    origin: ProposalOrigin
    prompt_version: str
    discovery_id: uuid.UUID
    profile_version: int
    release: str
    suggestions: list[WrittenWhy]  # one per suggestion explained, in slate order


# Readiness, affordability and hiring are computed by deterministic code or researched later
# (plan section 3); a written explanation never claims them. Whole words and phrases, any
# case; a word the occupation's own ESCO record uses describes the work, so it may be used
# ("payroll clerks check that staff are paid"). The person's answers never unlock one: "ready
# for a change" is no ground for saying they are ready for this work.
_READINESS = (
    "ready",
    "readiness",
    "qualified",
    "qualify",
    "qualifies",
    "eligible",
    "eligibility",
    "meet the requirements",
    "meets the requirements",
)
_AFFORDABILITY = (
    "afford",
    "affordable",
    "cheap",
    "cheaper",
    "expensive",
    "cost",
    "costs",
    "costly",
    "fee",
    "fees",
    "price",
    "salary",
    "salaries",
    "wage",
    "wages",
    "pay",
    "pays",
    "paid",
    "earn",
    "earns",
    "earning",
    "earnings",
    "income",
    "money",
    "budget",
    "funding",
    "funded",
    "loan",
    "grant",
    "grants",
    "lucrative",
    "paying",
)
_HIRING = (
    "hire",
    "hires",
    "hired",
    "hiring",
    "employable",
    "recruit",
    "recruited",
    "recruiting",
    "vacancy",
    "vacancies",
    "job offer",
    "openings",
    "demand for",
    "shortage",
    "shortages",
    "guarantee",
    "guaranteed",
    "get the job",
    "candidate",
    "candidates",
    "crying out for",
    "job market",
)
# Phrasings with a few words free: "in (high) demand", "already have the experience",
# "plenty of jobs".
# A hyphen separates words here as a space does ("an in-demand trade", "high-demand").
_CLAIM_PATTERNS = (
    ("in ... demand", r"in(?:[\s-]+\w+){0,2}[\s-]+demand"),
    ("high demand", r"(?:high|great|growing|strong|huge|big|constant)[\s-]+demand"),
    (
        "already have the ...",
        r"already\s+have\s+(?:the|all\s+the|enough)\s+"
        r"(?:skills?|experience|qualifications?|training)",
    ),
    ("plenty of jobs", r"plenty\s+of\s+(?:jobs|vacancies|openings|roles|work)"),
    ("sought after", r"sought[\s-]+after"),
    ("employers want", r"employers?\s+(?:want|wants|need|needs|are\s+looking|look|seek)"),
    ("short of staff", r"short(?:[\s-]+of)?[\s-]+staff(?:ed)?"),
)
_CURRENCY = ("£", "$", "€")
_CLAIM_TERMS = tuple(
    (term, re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE))
    for term in (*_READINESS, *_AFFORDABILITY, *_HIRING)
) + tuple(
    (label, re.compile(rf"(?<!\w){pattern}(?!\w)", re.IGNORECASE))
    for label, pattern in _CLAIM_PATTERNS
)
# Quotation marks by code point: double (straight, curly, low, reversed, guillemets) and the
# curly single ones.
_DOUBLE = '"' + "".join(map(chr, (0x201C, 0x201D, 0x201E, 0x201F, 0x00AB, 0x00BB)))
_OPEN_SINGLE, _CLOSE_SINGLE = chr(0x2018), chr(0x2019)
# A quotation written into the claim itself: a double quotation mark of any kind, or a
# single-quoted phrase (an apostrophe inside or after a word is not one).
_QUOTE_MARKS = re.compile(
    f"[{_DOUBLE}]"
    f"|(?<!\\w)['{_OPEN_SINGLE}][^'{_OPEN_SINGLE}{_CLOSE_SINGLE}]+?['{_CLOSE_SINGLE}](?!\\w)"
)
# Spans are matched with one kind of apostrophe and one kind of hyphen or dash.
_APOSTROPHES = str.maketrans(
    {
        **dict.fromkeys(map(chr, (0x2018, 0x2019, 0x201B, 0x02BB, 0x02BC, 0x0060, 0x00B4)), "'"),
        **dict.fromkeys(map(chr, (0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212)), "-"),
    }
)
# Taken off a quotation's ends: spaces and double quotation marks, and closing punctuation
# at its end. Single quotes come off only as a matching pair (straight, or curly left and
# right): a lone apostrophe may be the source's own ("'s work", "workers'").
_EDGE_TRIM = f" \t\n{_DOUBLE}"
_CLOSING = f" .,;:!?{chr(0x2026)}"
_SINGLE_PAIRS = (("'", "'"), (_OPEN_SINGLE, _CLOSE_SINGLE))


def _unwrapped(text: str) -> str:
    text = text.strip(_EDGE_TRIM).rstrip(_CLOSING)
    for opening, closing in _SINGLE_PAIRS:
        if len(text) > 2 and text.startswith(opening) and text.endswith(closing):
            return text[1:-1].strip(_EDGE_TRIM).rstrip(_CLOSING)
    return text


def unsupported_claim_terms(text: str, allowed: Iterable[str]) -> list[str]:
    """Readiness, affordability and hiring words and currency signs in a claim that the
    allowed texts (the occupation's own record) do not use, in the order of the lists."""
    allowed_text = "\n".join(allowed)
    found = [
        term
        for term, pattern in _CLAIM_TERMS
        if pattern.search(text) and not pattern.search(allowed_text)
    ]
    return found + [sign for sign in _CURRENCY if sign in text and sign not in allowed_text]


def _folded(text: str) -> tuple[str, list[int]]:
    """The text in lower case, with compatibility forms, one kind of apostrophe and hyphen,
    and single spaces; and, for each character of it, the index of the original character."""
    chars: list[str] = []
    index: list[int] = []
    space = True  # drop leading whitespace
    for i, original in enumerate(text):
        if original.isspace():
            if not space:
                chars.append(" ")
                index.append(i)
            space = True
            continue
        for char in unicodedata.normalize("NFKC", original).translate(_APOSTROPHES).lower():
            chars.append(char)
            index.append(i)
        space = False
    if chars and chars[-1] == " ":
        chars.pop()
        index.pop()
    return "".join(chars), index


def _in_word(folded: str, i: int) -> bool:
    """Whether the folded text's character `i` belongs to a word: a letter or digit, or an
    apostrophe after a letter ("mechanic's" is one word, so "s tools" is not a phrase of
    "mechanic's tools")."""
    char = folded[i]
    return char.isalnum() or (char == "'" and i > 0 and folded[i - 1].isalpha())


def find_span(quote: str, source: str) -> str | None:
    """The source's own characters for the first place the quotation appears in it whole
    (case, spacing and apostrophe forms aside), starting and ending at a word boundary; None
    if it appears nowhere so."""
    wanted, _ = _folded(quote)
    folded, index = _folded(source)
    if not wanted:
        return None
    start = folded.find(wanted)
    while start != -1:
        end = start + len(wanted)
        before = start == 0 or not _in_word(folded, start - 1)
        after = end == len(folded) or not _in_word(folded, end)
        if before and after:
            return source[index[start] : index[end - 1] + 1]
        start = folded.find(wanted, start + 1)
    return None


def _record_parts(record: OccupationRecord) -> list[tuple[RecordPart, str]]:
    return [
        (RecordPart.TITLE, record.title),
        (RecordPart.DESCRIPTION, record.description),
        *((RecordPart.ESSENTIAL_SKILL, skill) for skill in record.essential_skills),
    ]


def _verified(
    quote: ModelQuote, answers: Sequence[EvidenceItem], record: OccupationRecord
) -> Quotation | None:
    text = _unwrapped(quote.text)
    if not QUOTE_CHARS[0] <= len(text) <= QUOTE_CHARS[1] or not any(c.isalpha() for c in text):
        return None
    if quote.source is QuoteSource.ANSWER:
        for item in answers:
            span = find_span(text, item.text)
            if span is not None:
                return Quotation(
                    source=QuoteSource.ANSWER, answer_field=item.field, record_part=None, text=span
                )
        return None
    for part, source in _record_parts(record):
        span = find_span(text, source)
        if span is not None:
            return Quotation(
                source=QuoteSource.ESCO, answer_field=None, record_part=part, text=span
            )
    return None


def _checked_claim(
    claim: ModelClaim,
    where: str,
    answers: Sequence[EvidenceItem],
    record: OccupationRecord,
    problems: list[str],
) -> Claim:
    text = " ".join(claim.text.split())
    record_texts = [source for _, source in _record_parts(record)]
    if not CLAIM_CHARS[0] <= len(text) <= CLAIM_CHARS[1]:
        problems.append(f"{where}: a claim of {CLAIM_CHARS[0]}-{CLAIM_CHARS[1]} characters")
    if _QUOTE_MARKS.search(text):
        problems.append(
            f"{where}: no quotation marks in the claim; put each quotation in quotes instead"
        )
    unsupported = unsupported_claim_terms(text, record_texts)
    if unsupported:
        problems.append(
            f"{where}: no readiness, affordability or hiring claim, which Nessa checks "
            f"separately ({', '.join(unsupported)})"
        )
    if not 1 <= len(claim.quotes) <= MAX_QUOTES:
        problems.append(f"{where}: quotes must hold 1-{MAX_QUOTES} quotations")
    quotations: list[Quotation] = []
    for model_quote in claim.quotes[:MAX_QUOTES]:  # past the bound: counted, not checked
        found = _verified(model_quote, answers, record)
        if found is not None and not quotable(found.text):  # the source's own words, folded
            problems.append(
                f"{where}: “{_echo(model_quote.text)}” has no content word; quote words that "
                "say something"
            )
        elif found is None:
            whose = (
                "your answers"
                if model_quote.source is QuoteSource.ANSWER
                else f"ESCO's record for {record.title}"
            )
            problems.append(
                f"{where}: “{_echo(model_quote.text)}” is not an exact quotation of whole words "
                f"from {whose}"
            )
        else:
            quotations.append(found)
    if len(set(quotations)) != len(quotations):
        problems.append(f"{where}: quote each passage once")
    sources = {quotation.source for quotation in quotations}
    if QuoteSource.ANSWER not in sources:
        problems.append(f"{where}: quote at least one of the person's answers (source answer)")
    if QuoteSource.ESCO not in sources:
        problems.append(f"{where}: quote this occupation's ESCO record at least once (source esco)")
    return Claim(text=text, quotations=quotations)


def _echo(text: str) -> str:
    """A model's text as a problem repeats it: shortened, so the repair stays bounded."""
    text = " ".join(text.split())
    return text if len(text) <= ECHO_CHARS else f"{text[:ECHO_CHARS]}…"


REPAIR_HEADER = (
    "The JSON object does not pass validation. Answer again with the whole object, fixing "
    "these problems:"
)


def repair_message(problems: list[str]) -> str:
    """The repair request: the problems in order, as many as fit `REPAIR_MESSAGE_BYTES`,
    then how many more there are, so it never outgrows its reservation."""
    message = REPAIR_HEADER
    for index, problem in enumerate(problems):
        line = f"\n- {problem}"
        left = len(problems) - index - 1
        tail = f"\n- and {left} more problems." if left else ""
        if len((message + line + tail).encode()) > REPAIR_MESSAGE_BYTES:
            return f"{message}\n- and {len(problems) - index} more problems."
        message += line
    return message


def check_explanation(
    output: ExplanationOutput, context: ExplanationInput, origin: ProposalOrigin
) -> tuple[SlateExplanation | None, list[str]]:
    """The validated explanation, or the problems that prevent it (never both)."""
    problems: list[str] = []
    records = {record.ref: record for record in context.occupations}
    given = [explanation.occupation for explanation in output.explanations]
    if sorted(given) != sorted(records):
        problems.append(
            f"explanations: exactly one for each occupation ref, {', '.join(records)}, and no other"
        )
    written: dict[str, WrittenWhy] = {}
    for explanation in output.explanations:
        record = records.get(explanation.occupation)
        if record is None or explanation.occupation in written:
            continue
        if not 1 <= len(explanation.claims) <= MAX_CLAIMS:
            problems.append(f"{explanation.occupation}: claims must hold 1-{MAX_CLAIMS} claims")
        claims = [  # past the bound: counted above, not checked
            _checked_claim(
                claim, f"{explanation.occupation} claim {n}", context.answers, record, problems
            )
            for n, claim in enumerate(explanation.claims[:MAX_CLAIMS], start=1)
        ]
        if len({claim.text.casefold() for claim in claims}) != len(claims):
            problems.append(f"{explanation.occupation}: make each claim once")
        inferred = inferred_sensitive_terms(
            [claim.text for claim in claims],
            [item.text for item in context.answers] + [s for _, s in _record_parts(record)],
        )
        if inferred:
            problems.append(
                f"{explanation.occupation}: do not name a health condition, personality type, "
                f"personal characteristic or percentage the person did not mention "
                f"({', '.join(inferred)})"
            )
        written[explanation.occupation] = WrittenWhy(
            concept_id=record.concept_id, title=record.title, claims=claims
        )
    if problems:
        return None, problems
    return (
        SlateExplanation(
            origin=origin,
            prompt_version=context.prompt_version,
            discovery_id=context.discovery_id,
            profile_version=context.profile_version,
            release=context.release,
            suggestions=[written[ref] for ref in records],
        ),
        [],
    )


INSTRUCTIONS = f"""\
You write the "Why this could suit you" note beside each occupation Nessa, a career-planning
service in England, suggested to a person. Use only the person's confirmed answers
("answers") and ESCO's record of each occupation (its title, description and essential
skills).

For each occupation, by its ref, write 1-{MAX_CLAIMS} claims. A claim is one plain sentence of
at most {CLAIM_CHARS[1]} characters that links something the person said to something in that
occupation's record. Under each claim, quote at least one of the person's answers (source
"answer") and that occupation's record at least once (source "esco"), each a few words
copied exactly from its source. Never put quotation marks in the claim itself.

Say only what the quotations support. Never say the person is ready, qualified or likely to
be hired, and never mention pay, cost, money, funding, demand or vacancies: Nessa checks
those separately. Never mention health, personality types, age, sex, ethnicity, religion or
nationality, and give no score or percentage. Answer only with the JSON object.
"""


class PromptOccupation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    title: str
    description: str
    essential_skills: list[str]


class PromptExplanationContext(BaseModel):
    """What the model reads: answer texts by field and the records, nothing else."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answers: dict[ProfileField, list[str]]
    occupations: list[PromptOccupation]


def render_prompt(context: ExplanationInput) -> str:
    """The user prompt. The fixture explainer reads the same text."""
    answers: dict[ProfileField, list[str]] = {}
    for item in context.answers:
        answers.setdefault(item.field, []).append(item.text)
    prompt = PromptExplanationContext(
        answers=answers,
        occupations=[
            PromptOccupation(
                ref=record.ref,
                title=record.title,
                description=record.description,
                essential_skills=record.essential_skills,
            )
            for record in context.occupations
        ],
    )
    payload = json.loads(prompt.model_dump_json())
    return CONTEXT_MARKER + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def prompt_bytes(context: ExplanationInput) -> int:
    return len(INSTRUCTIONS.encode()) + len(render_prompt(context).encode())


def _cut(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip()


def build_input(
    *,
    discovery_id: uuid.UUID,
    profile_version: int,
    release: str,
    answers: list[EvidenceItem],
    occupations: Sequence[OccupationFacts],
) -> ExplanationInput:
    """The run's input: every pinned answer whole, and as much of each record as fits. The
    bound is in bytes, so answers in characters of several bytes can leave no step that
    fits: that is refused (`LIMIT_EXCEEDED`) before any run or reservation exists."""
    for description_chars, skills in RECORD_STEPS:
        context = ExplanationInput(
            discovery_id=discovery_id,
            profile_version=profile_version,
            release=release,
            answers=answers,
            occupations=[
                OccupationRecord(
                    ref=f"o{n}",
                    concept_id=facts.concept_id,
                    esco_uri=facts.esco_uri,
                    title=facts.preferred_label,
                    description=_cut(facts.description, description_chars),
                    essential_skills=list(facts.essential_skills[:skills]),
                )
                for n, facts in enumerate(occupations, start=1)
            ],
        )
        if prompt_bytes(context) <= MAX_PROMPT_BYTES:
            return context
    raise NessaError(
        ErrorCode.LIMIT_EXCEEDED,
        "Your answers are too long for a written note. Shorten or remove some, then suggest again.",
        stage=ErrorStage.PROFILE,
        details={"reason": "answers_too_long", "max_prompt_bytes": MAX_PROMPT_BYTES},
    )


def worst_case_nano_usd(model_id: str) -> int:
    """Per activity attempt: both requests at the input and output bounds."""
    per_request = worst_case_cost_nano_usd(
        model_id,
        max_input_tokens=MAX_PROMPT_BYTES
        + SCHEMA_ALLOWANCE_TOKENS
        + MAX_OUTPUT_TOKENS
        + REPAIR_ALLOWANCE_TOKENS,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_web_searches=0,
    )
    return MAX_REQUESTS * per_request
