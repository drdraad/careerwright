"""The discovery contract (spec section 4, REC-1 and DIV-1; S2.4).

A discovery run sends the model the person's confirmed answers that describe work (current
role, targets, the three task fields and work style; never limits, places, money or a
name) and gets back a bounded `DiscoveryOutput`: plain search queries for the ESCO
classification, each tagged with a discovery channel and citing the answers it comes from,
and up to three "surprising but plausible" title hypotheses.

The model proposes searches; it never names a suggestion. `check_discovery` validates the
output deterministically: every query and hypothesis rests on the person's own answer
texts, and none uses a health condition, a personality type or a protected characteristic
the person never gave (`careerwright.profile.safety`). What it returns is the stored
`DiscoveryProposal`. Retrieval, de-duplication and the slate are deterministic code over the
pinned taxonomy (`careerwright.profile.slate`, `careerwright.profile.exploration`); a hypothesis
becomes a suggestion only if ESCO holds it (DIV1-04).
"""

import json
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from careerwright.identity.model_registry import worst_case_cost_nano_usd
from careerwright.profile.document import FieldState, ProfileDocument
from careerwright.profile.interview import ProfileField, ProposalOrigin
from careerwright.profile.safety import inferred_sensitive_terms

PROMPT_VERSION = "discovery-queries-1"
INPUT_FORMAT: Literal["careerwright.discovery-input"] = "careerwright.discovery-input"
MAX_QUERIES = 8
MAX_HYPOTHESES = 3
MAX_BASED_ON = 3
QUERY_CHARS = (3, 80)
# Bounds for the spend reservation (bytes bound tokens for byte-level BPE tokenizers).
MAX_PROMPT_BYTES = 8_000  # instructions plus the rendered evidence, at every list bound
SCHEMA_ALLOWANCE_TOKENS = 1_500
MAX_OUTPUT_TOKENS = 1_500
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
    # The ESCO release held at submission (its dataset ID); None in inputs sealed before
    # it was recorded. Never sent to the model.
    release: str | None = None


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
    release: str | None = None  # the release the searches were chosen for (from the input)


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


def check_discovery(
    output: DiscoveryOutput, context: DiscoveryInput, origin: ProposalOrigin
) -> tuple[DiscoveryProposal | None, list[str]]:
    """The validated proposal, or the problems that prevent it (never both)."""
    problems: list[str] = []
    evidence = {_key(item.text): item for item in context.evidence}
    if not 1 <= len(output.queries) <= MAX_QUERIES:
        problems.append(f"queries: 1-{MAX_QUERIES}")
    if len(output.hypotheses) > MAX_HYPOTHESES:
        problems.append(f"hypotheses: at most {MAX_HYPOTHESES}")
    keys = [_key(q.text) for q in output.queries]
    if len(set(keys)) != len(keys):
        problems.append("queries: each query once")
    inferred = inferred_sensitive_terms(
        [q.text for q in output.queries] + [h.title for h in output.hypotheses],
        [item.text for item in context.evidence],
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
        cited = _cited(model_query.based_on, evidence, f"query {index}", problems)
        queries.append(
            DiscoveryQuery(
                query_id=f"q{index}",
                text=" ".join(model_query.text.split()),
                channel=model_query.channel,
                based_on=cited,
            )
        )
    hypotheses: list[Hypothesis] = []
    for index, model_hypothesis in enumerate(output.hypotheses, start=1):
        if not _bounded(model_hypothesis.title):
            problems.append(f"hypothesis {index}: {QUERY_CHARS[0]}-{QUERY_CHARS[1]} characters")
        cited = _cited(model_hypothesis.based_on, evidence, f"hypothesis {index}", problems)
        hypotheses.append(
            Hypothesis(title=" ".join(model_hypothesis.title.split()), based_on=cited)
        )
    if problems:
        return None, problems
    return (
        DiscoveryProposal(
            origin=origin,
            prompt_version=context.prompt_version,
            profile_version=context.profile_version,
            queries=queries,
            hypotheses=hypotheses,
            release=context.release,
        ),
        [],
    )


INSTRUCTIONS = f"""\
You help Careerwright, a career-planning service for people in England, search the ESCO
classification of occupations. From the person's confirmed answers, write 4-{MAX_QUERIES} search
queries for ESCO's English occupation titles, descriptions and skills: short plain phrases
of 2-6 words naming tasks, skills, work settings or occupations, never a sentence.

Cover different kinds of work, one channel per query: what they enjoy ("tasks"), how and
where they like to work ("environment"), skills they could carry over from what they do or
have done ("transferable"), the same tasks in other industries ("cross_industry"), and
specialist, vocational or less familiar work they may not have considered
("less_familiar"). Do not favour popular, prestigious or well-paid work.

In based_on, quote exactly the answer texts each query comes from. Also give up to
{MAX_HYPOTHESES} surprising but plausible occupation titles ("hypotheses"), with the answers they
come from; Careerwright checks each against ESCO and drops any it cannot find.

A preference informs the search; never use it to exclude work. Never search by age, sex,
health, ethnicity, religion, nationality or personality type. Answer only with the JSON
object.
"""

CONTEXT_MARKER = "Discovery context (JSON):\n"


class PromptEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: ProfileField
    text: str


class PromptDiscoveryContext(BaseModel):
    """What the model reads: answer texts and their fields, nothing else."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answers: list[PromptEvidence]


def render_prompt(context: DiscoveryInput) -> str:
    """The user prompt. The fixture proposer reads the same text."""
    prompt = PromptDiscoveryContext(
        answers=[PromptEvidence(field=item.field, text=item.text) for item in context.evidence]
    )
    payload = json.loads(prompt.model_dump_json())
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
