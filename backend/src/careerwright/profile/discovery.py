"""The discovery contract (spec section 4, REC-1 and DIV-1; S2.4).

A discovery run sends the model the person's confirmed answers that describe work (current
role, targets, the three task fields and work style; never limits, places, money or a
name) and their qualifications, each with its status (Task 6g slice B: an expected one is
never read as achieved), and gets back a bounded `DiscoveryOutput`: short search phrases in
ESCO's own skill wording (an essential skill's name must hold every word of one to reach
work), or the person's own titles, each tagged with a discovery channel and citing the
answers it comes from; up to three "surprising but plausible" title hypotheses; and up to six
"aim higher" title ideas, work that usually needs more training than theirs (the product
owner's two horizons, 3 November 2026).

The model proposes searches and title ideas; it never names a suggestion. `check_discovery`
validates the output deterministically: every query and title idea rests on the person's own
answer texts, and none uses a health condition, a personality type or a protected
characteristic the person never gave (`careerwright.profile.safety`). What it returns is the
stored `DiscoveryProposal`. Retrieval, de-duplication and the slate are deterministic code over
the pinned taxonomy (`careerwright.profile.slate`, `careerwright.profile.exploration`); a title
idea becomes a suggestion only where code confirms it, and code alone places it in a set
(ADR 0015 decision 2; ADR 0007, Task 6g amendments).
"""

import json
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.identity.model_registry import worst_case_cost_nano_usd
from careerwright.profile.dashes import DASH_PROBLEM, DASH_RULE, model_dash
from careerwright.profile.document import (
    FieldState,
    ProfileDocument,
    QualificationAnswer,
    QualificationStatus,
)
from careerwright.profile.interview import ProfileField, ProposalOrigin
from careerwright.profile.safety import inferred_sensitive_terms

# 2 (Task W2B fix round 2): short phrases in ESCO's skill wording, never work style alone.
# 3 (fix round 3): never a phrase too general to find work alone; a one-word work style is
# never searched alone, a longer one may be; "plan shifts" (now too general) leaves the
# examples. 4 (Task W2F slice E, the product owner: "Em-dashes are outlawed!"): queries and
# title ideas are shown in the model's words, so never an em dash or a spaced en dash.
# 5 (Task 6g slice B, the product owner's two horizons): up to six "aim higher" title ideas,
# and the person's qualifications, an expected one never read as achieved.
PROMPT_VERSION = "discovery-queries-5"
INPUT_FORMAT: Literal["careerwright.discovery-input"] = "careerwright.discovery-input"
MAX_QUERIES = 8
MAX_HYPOTHESES = 3
MAX_AIM_HIGHER = 6
MAX_BASED_ON = 3
QUERY_CHARS = (3, 80)
# Bounds for the spend reservation (bytes bound the prompt's tokens for byte-level BPE
# tokenizers). Task 6g slice B: the prompt gained the qualifications (eight of up to 120
# characters, with their status) and a paragraph. The output bound holds the largest answer the
# check accepts (17 items, each quoting three answers of 120 characters: about 8,300 bytes, or
# 2,800 tokens at 3 bytes a token), the reasoning that shares the bound (800 tokens) and a
# tenth more, as the contract test measures; a response cut off at its bound ends the run.
MAX_PROMPT_BYTES = 10_000  # instructions plus the rendered evidence, at every list bound
SCHEMA_ALLOWANCE_TOKENS = 1_500
MAX_OUTPUT_TOKENS = 4_000
REPAIR_ALLOWANCE_TOKENS = 1_000
MAX_REQUESTS = 2  # the first request and at most one repair
# The answers that describe work, in the order the model reads them.
EVIDENCE_FIELDS = (
    ProfileField.CURRENT_ROLE,
    ProfileField.TARGET_TITLES,
    ProfileField.ENJOYED_TASKS,
    ProfileField.CONFIDENT_TASKS,
    ProfileField.EVIDENCED_TASKS,
    ProfileField.WORK_STYLE,
)


class QueryChannel(StrEnum):
    """The model's discovery channels (spec section 4, DIV-1's five channels). Careerwright adds
    the person's current role and their own target titles itself."""

    TASKS = "tasks"  # task and interest retrieval, independent of vacancy frequency
    ENVIRONMENT = "environment"  # how and where they like to work
    TRANSFERABLE = "transferable"  # adjacent roles through transferable skills
    CROSS_INDUSTRY = "cross_industry"  # the same tasks in other workplaces
    LESS_FAMILIAR = "less_familiar"  # specialist, vocational, regional or emerging work


class ModelQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    channel: QueryChannel
    based_on: list[str]  # the person's answer texts, quoted exactly


class ModelHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    based_on: list[str]


class DiscoveryOutput(BaseModel):
    """The model's whole output (sent to Meta as a strict JSON schema)."""

    model_config = ConfigDict(extra="forbid")

    queries: list[ModelQuery]
    hypotheses: list[ModelHypothesis]
    aim_higher: list[ModelHypothesis]


class EvidenceItem(BaseModel):
    """One confirmed answer text and the field that holds it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: ProfileField
    text: str


class DiscoveryInput(BaseModel):
    """Everything a discovery run sends the model: sealed into the run at submission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    format: Literal["careerwright.discovery-input"] = INPUT_FORMAT
    prompt_version: str = PROMPT_VERSION
    profile_version: int
    evidence: list[EvidenceItem]
    # The person's qualifications, each with its status (Task 6g slice B; none in inputs
    # sealed before). The model reads them and may quote one by its name.
    qualifications: list[QualificationAnswer] = Field(default_factory=list)
    # The ESCO release held at submission (its dataset ID); None in inputs sealed before
    # it was recorded. Never sent to the model.
    release: str | None = None

    def quotable(self) -> list[EvidenceItem]:
        """The answer texts a query or title idea may quote: the answers that describe work,
        then each qualification by its name."""
        named = [
            EvidenceItem(field=ProfileField.QUALIFICATIONS, text=q.name)
            for q in self.qualifications
        ]
        return [*self.evidence, *named]


class DiscoveryQuery(BaseModel):
    """One validated query, as stored."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query_id: str
    text: str
    channel: QueryChannel
    based_on: list[EvidenceItem]


class Hypothesis(BaseModel):
    """A title the model thinks plausible: a search hypothesis until ESCO corroborates it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    based_on: list[EvidenceItem]


class DiscoveryProposal(BaseModel):
    """A discovery run's validated output (sealed). It names searches, never suggestions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    origin: ProposalOrigin
    prompt_version: str
    profile_version: int
    queries: list[DiscoveryQuery]
    hypotheses: list[Hypothesis]
    # Task 6g slice B: work that usually needs more training than the person's, in the
    # model's view; code confirms each and places it by level. None in proposals before.
    aim_higher: list[Hypothesis] = Field(default_factory=list)
    release: str | None = None  # the release the searches were chosen for (from the input)

    @property
    def title_ideas(self) -> list[Hypothesis]:
        """Every title the model thought of: its hypotheses, then its aim higher ideas."""
        return [*self.hypotheses, *self.aim_higher]


def _key(text: str) -> str:
    return " ".join(text.casefold().split())


def evidence_of(document: ProfileDocument) -> list[EvidenceItem]:
    """The confirmed answers that describe work: answered fields only, never a limit."""
    items: list[EvidenceItem] = []
    for name in EVIDENCE_FIELDS:
        field = getattr(document, name.value)
        if field.state is not FieldState.PROVIDED or field.value is None:
            continue
        values = field.value if isinstance(field.value, list) else [field.value]
        items += [EvidenceItem(field=name, text=str(value)) for value in values]
    return items


def qualifications_of(document: ProfileDocument) -> list[QualificationAnswer]:
    field = document.qualifications
    if field.state is not FieldState.PROVIDED or not field.value:
        return []
    return list(field.value)


def input_of(
    document: ProfileDocument, *, profile_version: int, release: str | None = None
) -> DiscoveryInput:
    """What a discovery of this profile version sends the model: the answers that describe
    work and the qualifications (`evidence_of` alone decides whether one can start)."""
    return DiscoveryInput(
        profile_version=profile_version,
        evidence=evidence_of(document),
        qualifications=qualifications_of(document),
        release=release,
    )


def _cited(
    texts: list[str], evidence: dict[str, EvidenceItem], where: str, problems: list[str]
) -> list[EvidenceItem]:
    quoted = list(dict.fromkeys(_key(text) for text in texts))
    if not 1 <= len(quoted) <= MAX_BASED_ON or any(key not in evidence for key in quoted):
        problems.append(
            f"{where}: based_on must quote 1-{MAX_BASED_ON} of the person's answer texts exactly"
        )
        return []
    return [evidence[key] for key in quoted]


def _bounded(text: str) -> bool:
    return QUERY_CHARS[0] <= len(text.strip()) <= QUERY_CHARS[1]


def _ideas(
    ideas: list[ModelHypothesis],
    where: str,
    evidence: dict[str, EvidenceItem],
    own_words: list[str],
    problems: list[str],
) -> list[Hypothesis]:
    """Title ideas, each checked as any is: bounded, no dash of the model's, and quoting the
    answers it comes from."""
    checked: list[Hypothesis] = []
    for index, idea in enumerate(ideas, start=1):
        label = f"{where} {index}"
        if not _bounded(idea.title):
            problems.append(f"{label}: {QUERY_CHARS[0]}-{QUERY_CHARS[1]} characters")
        if model_dash(idea.title, own_words):
            problems.append(f"{label}: {DASH_PROBLEM}")
        cited = _cited(idea.based_on, evidence, label, problems)
        checked.append(Hypothesis(title=" ".join(idea.title.split()), based_on=cited))
    return checked


def check_discovery(
    output: DiscoveryOutput, context: DiscoveryInput, origin: ProposalOrigin
) -> tuple[DiscoveryProposal | None, list[str]]:
    """The validated proposal, or the problems that prevent it (never both)."""
    problems: list[str] = []
    quotable = context.quotable()
    evidence: dict[str, EvidenceItem] = {}
    for item in quotable:  # an answer that is also a qualification's name is the answer
        evidence.setdefault(_key(item.text), item)
    if not 1 <= len(output.queries) <= MAX_QUERIES:
        problems.append(f"queries: 1-{MAX_QUERIES}")
    if len(output.hypotheses) > MAX_HYPOTHESES:
        problems.append(f"hypotheses: at most {MAX_HYPOTHESES}")
    if len(output.aim_higher) > MAX_AIM_HIGHER:
        problems.append(f"aim_higher: at most {MAX_AIM_HIGHER}")
    keys = [_key(q.text) for q in output.queries]
    if len(set(keys)) != len(keys):
        problems.append("queries: each query once")
    titles = [_key(idea.title) for idea in [*output.hypotheses, *output.aim_higher]]
    if len(set(titles)) != len(titles):
        problems.append("title ideas: each title once")
    own_words = [item.text for item in quotable]
    inferred = inferred_sensitive_terms(
        [q.text for q in output.queries]
        + [idea.title for idea in [*output.hypotheses, *output.aim_higher]],
        own_words,
        kindred=True,  # a search may name who the work serves (not so a reply)
    )
    if inferred:
        problems.append(
            "do not search by a health condition, personality type or personal characteristic "
            f"the person did not mention ({', '.join(inferred)})"
        )
    queries: list[DiscoveryQuery] = []
    for index, model_query in enumerate(output.queries, start=1):
        if not _bounded(model_query.text):
            problems.append(f"query {index}: {QUERY_CHARS[0]}-{QUERY_CHARS[1]} characters")
        if model_dash(model_query.text, own_words):
            problems.append(f"query {index}: {DASH_PROBLEM}")
        cited = _cited(model_query.based_on, evidence, f"query {index}", problems)
        queries.append(
            DiscoveryQuery(
                query_id=f"q{index}",
                text=" ".join(model_query.text.split()),
                channel=model_query.channel,
                based_on=cited,
            )
        )
    hypotheses = _ideas(output.hypotheses, "hypothesis", evidence, own_words, problems)
    aim_higher = _ideas(output.aim_higher, "aim_higher", evidence, own_words, problems)
    if problems:
        return None, problems
    return (
        DiscoveryProposal(
            origin=origin,
            prompt_version=context.prompt_version,
            profile_version=context.profile_version,
            queries=queries,
            hypotheses=hypotheses,
            aim_higher=aim_higher,
            release=context.release,
        ),
        [],
    )


INSTRUCTIONS = f"""\
You help Careerwright, a career-planning service for people in England, search the ESCO
classification of occupations. From the person's confirmed answers, write 4-{MAX_QUERIES} search
queries. Careerwright finds an occupation only through an essential skill ESCO lists for it
whose name holds every word of a query, so write each query as a short phrase of 2-4 words
in ESCO's own skill wording: a verb and what it acts on, as ESCO names its skills ("stack
goods", "repair bicycles", "care for children", "handle complaints", "perform data
cleansing"). A paraphrase ESCO does not use ("look after children") finds nothing. A phrase
many kinds of work share ("write reports", "solve problems", "work in a team") is too
general to find work on its own: say what it is about ("write inspection reports"). Never
write a sentence or a word on its own. A query may instead be one of the person's own job
titles exactly as they gave it: Careerwright joins it to other work by the essential skills
they share.

Cover different kinds of work, one channel per query: what they enjoy ("tasks"), where they
like to work ("environment"), skills they could carry over from what they do or have done
("transferable"), the same tasks in other industries ("cross_industry"), and specialist,
vocational or less familiar work they may not have considered ("less_familiar"). Base each
query and title on what they do, enjoy, can do or have done, where they like to work ("work
in outdoor conditions"), a role they named, or a qualification: a one-word answer about how
they like to work ("structured") matches too loosely, so Careerwright never searches with it
alone. Do not favour popular, prestigious or well-paid work.

In based_on, quote exactly the answer texts each query or title comes from. Also give up to
{MAX_HYPOTHESES} surprising but plausible occupation titles ("hypotheses"), with the answers they
come from.

Also give up to {MAX_AIM_HIGHER} titles ("aim_higher") of work they could aim for over the next
years: work that usually needs more training, study or experience than what they do now or
have done, even by a long path. Choose each for how well it follows from their answers, never
for its pay or status, and name it as employers in England do. Careerwright checks every title
against ESCO and the UK job-title index, suggests only those it finds, and decides itself how
much training each usually needs.

Qualifications come with their status: "achieved" is held; "expected" is being taken now or
still to be awarded, so never treat an expected one as achieved.

A preference informs the search; never use it to exclude work. Never search by age, sex,
health, ethnicity, religion, nationality or personality type. {DASH_RULE} Answer only with
the JSON object.
"""

CONTEXT_MARKER = "Discovery context (JSON):\n"


class PromptEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: ProfileField
    text: str
    status: QualificationStatus | None = None  # a qualification's only


class PromptDiscoveryContext(BaseModel):
    """What the model reads: answer texts and their fields, a qualification with its status,
    nothing else."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answers: list[PromptEvidence]


def render_prompt(context: DiscoveryInput) -> str:
    """The user prompt. The fixture proposer reads the same text."""
    answers = [PromptEvidence(field=item.field, text=item.text) for item in context.evidence]
    answers += [
        PromptEvidence(field=ProfileField.QUALIFICATIONS, text=q.name, status=q.status)
        for q in context.qualifications
    ]
    payload = json.loads(PromptDiscoveryContext(answers=answers).model_dump_json(exclude_none=True))
    return CONTEXT_MARKER + json.dumps(payload, ensure_ascii=False)


def prompt_bytes(context: DiscoveryInput) -> int:
    return len(INSTRUCTIONS.encode()) + len(render_prompt(context).encode())


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
