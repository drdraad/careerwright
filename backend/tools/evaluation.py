"""The Sprint 2 interview and discovery evaluation (plan Sprint 2 acceptance; TEST1-10, DIV1-08,
REC1-09): reviewed synthetic cases with semantic expectations, never exact prose.

`evaluation_cases.json` holds the cases. Each names what it exercises (`kind`), its synthetic
input and its expectations; every expectation has a failure type, so a run reports failures
by type. The same checks read API-shaped JSON, so the offline run (deterministic subjects:
the support screen, the output guard, discovery with the fixture proposer and the slate
explanation with the fixture explainer over the full ESCO release) and the live run
(`tools.live_eval`, the test model through the product) share them. An explanation's
quotations are checked against ESCO's records as the taxonomy serves them, independently
of the product's own span check. Model behaviour is evidenced only by the live run: the
deterministic subjects certify the pipeline and its guards, not the model (plan section 9).

Case review: written and checked against spec section 4 by the implementing agent on
2026-10-28; a human review of the case set is still to do (see the Sprint 2 review).
"""

import json
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.api.discovery_schemas import SlateOut, WrittenExplanationOut
from careerwright.capability.commands import committed_data, pack_targets
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.ai_resilience import committed_packs
from careerwright.catalogue.pay import committed_reviews
from careerwright.db import Tx
from careerwright.identity.model_registry import FIXTURE_DISCOVERY_MODEL_ID
from careerwright.identity.records import Run, RunKind
from careerwright.profile.discovery import (
    DiscoveryInput,
    DiscoveryOutput,
    check_discovery,
    evidence_of,
)
from careerwright.profile.discovery import render_prompt as render_discovery_prompt
from careerwright.profile.document import (
    FIELD_NAMES,
    ProfileDocument,
    ProfileInput,
    apply_profile_input,
    empty_profile,
)
from careerwright.profile.exploration import (
    DiscoveryView,
    HardFilterInput,
    SlateView,
    compute_slate,
)
from careerwright.profile.fixture_discovery import fixture_queries, prompt_context
from careerwright.profile.fixture_explainer import fixture_explanation
from careerwright.profile.fixture_explainer import prompt_context as explainer_context
from careerwright.profile.interview import (
    ContextMessage,
    InterviewTurnOutput,
    ProposalOrigin,
    TurnInput,
    check_turn,
    context_profile,
)
from careerwright.profile.records import TargetRecord
from careerwright.profile.safety import has_risk_stem
from careerwright.profile.slate import MIN_SHARED_SKILLS, Emphasis, SlateControls
from careerwright.profile.slate_explanation import RECORD_STEPS, build_input, check_explanation
from careerwright.profile.slate_explanation import render_prompt as render_explanation_prompt
from careerwright.profile.targets import resolve_target, target_titles
from careerwright.vocabulary import DataMode, WorkState

CASES_PATH = Path(__file__).with_name("evaluation_cases.json")
_LETTERS = re.compile(r"[^\W\d_]+")
# The answers searched as skills; the person's own titles give their own reasons.
_SEARCHED_FIELDS = frozenset({"enjoyed_tasks", "confident_tasks", "evidenced_tasks", "work_style"})
# English function words of three or more letters (the Snowball English stop list): a search
# may hold them and a skill label need not. Written out here, independent of the product.
_FUNCTION_WORDS = frozenset(
    {
        "about", "above", "after", "again", "against", "all", "and", "any", "are", "because",
        "been", "before", "being", "below", "between", "both", "but", "can", "did", "does",
        "doing", "don", "down", "during", "each", "few", "for", "from", "further", "had", "has",
        "have", "having", "her", "here", "hers", "herself", "him", "himself", "his", "how",
        "into", "its", "itself", "just", "more", "most", "myself", "nor", "not", "now", "off",
        "once", "only", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
        "should", "some", "such", "than", "that", "the", "their", "theirs", "them",
        "themselves", "then", "there", "these", "they", "this", "those", "through", "too",
        "under", "until", "very", "was", "were", "what", "when", "where", "which", "while",
        "who", "whom", "why", "will", "with", "you", "your", "yours", "yourself", "yourselves",
    }
)  # fmt: skip
Json = dict[str, Any]


def _every_word_in(text: str, label: str) -> bool:
    """Whether every content word of the text (three or more letters, not a function word)
    appears in the label in some form ("repairing bicycles" in "perform repairs on
    bicycles"): an independent check of the product's English stemming, so loose about
    endings, never about a word left out. Two words agree when they begin alike for at least
    three letters and for all but the last three of the shorter. A text with no such word is
    not shown to be in the label."""

    def agree(a: str, b: str) -> bool:
        shorter = min(len(a), len(b))
        alike = next((i for i in range(shorter) if a[i] != b[i]), shorter)
        return alike >= max(3, shorter - 3)

    words = [
        w for w in _LETTERS.findall(text.casefold()) if len(w) >= 3 and w not in _FUNCTION_WORDS
    ]
    held = _LETTERS.findall(label.casefold())
    return bool(words) and all(any(agree(a, b) for b in held) for a in words)


class CaseKind(StrEnum):
    INTERVIEW = "interview"  # one interview turn: model behaviour (live only)
    DISCOVERY = "discovery"  # the confirmed answers to a slate
    EXPLANATION = "explanation"  # a slate's first view and its written explanation
    SUPPORT = "support"  # the support screen: whether the message triggers the support flow
    GUARD = "guard"  # a canned model output against the deterministic output checks


class FailureType(StrEnum):
    SCHEMA_INVALID = "schema_invalid"  # no validated output
    MISSED_FACT = "missed_fact"  # a stated fact not proposed
    INVENTED_VALUE = "invented_value"  # a value the person never gave (baseline, budget)
    UNKNOWN_AS_VALUE = "unknown_as_value"  # unknown, skipped or declined turned into a value
    QUESTION = "question"  # more than one question, or the wrong kind of question
    REASKED = "reasked"  # asked again for something already known
    INFERENCE = "inference"  # health, type, protected characteristic or percentage inferred
    COUNTERFACTUAL = "counterfactual_drift"  # an irrelevant cue changed the result
    GROUNDING = "grounding"  # a suggestion not grounded in ESCO and the answers
    DIVERSITY = "diversity"  # too few families or a direction missing
    DUPLICATE = "duplicate_alias"  # one occupation counted twice
    UNSUPPORTED_TITLE = "unsupported_title"  # a model title shown as a suggestion
    THIN_EVIDENCE = "thin_evidence"  # filler, or fewer without a reason
    PREFERENCE_EXCLUSION = "preference_exclusion"  # a preference removed work
    LIMIT = "limit"  # a confirmed limit not reported with its counts, or applied to unknowns
    SUPPORT_MISSED = "support_missed"
    SUPPORT_FALSE_POSITIVE = "support_false_positive"
    GUARD = "guard"  # the output check accepted what it should refuse, or the reverse


class Expectation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    check: str
    field: str | None = None
    fields: list[str] = Field(default_factory=list)
    words: list[str] = Field(default_factory=list)
    whole_words: bool = False  # match `words` as whole words, not as word beginnings
    state: str | None = None
    value: Any = None
    count: int | None = None
    direction: str | None = None
    other: str | None = None  # a paired case


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    kind: CaseKind
    title: str
    requirements: list[str]
    synthetic: Literal[True]
    live: bool = False  # one of the representative cases the live run may take
    entry_mode: str | None = None
    conversation_mode: str | None = None
    profile: Json = Field(default_factory=dict)  # field -> value (provided) or {"state": ...}
    message: str | None = None
    output: Json | None = None  # a guard case's canned model output
    # A guard case's canned discovery output; for a discovery case, the searches a model
    # might propose, used offline in place of the fixture proposer's.
    discovery_output: Json | None = None
    expect: list[Expectation]
    note: str | None = None


def profile_input_of(profile: Json) -> Json:
    """A case's profile as the API's whole-profile input: every other field not asked."""
    fields: Json = {name: {"state": "unasked"} for name in FIELD_NAMES}
    for name, value in profile.items():
        stated = isinstance(value, dict) and set(value) == {"state"}
        fields[name] = value if stated else {"state": "provided", "value": value}
    return fields


def load_cases(path: Path = CASES_PATH) -> list[Case]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Case.model_validate(item) for item in raw["cases"]]


@dataclass(frozen=True)
class Failure:
    type: FailureType
    detail: str


def _has(text: str, words: list[str], *, whole: bool = False) -> bool:
    """Whether a word starts a word of the text ("fix" finds "fixing", "test" not "contest");
    `whole` words must also end there ("man" does not find "manager")."""
    end = r"(?!\w)" if whole else ""
    return any(
        re.search(rf"(?<!\w){re.escape(word.strip())}{end}", text, re.IGNORECASE) for word in words
    )


def _value_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value


# A second ask joined to the first in one sentence ("..., and would you ...?").
_JOINED_ASK = re.compile(
    r"[,;]\s*(?:and|or)\s+(?:would|could|do|does|did|are|is|have|has|can|what|which|where|"
    r"when|how|who|why)\b",
    re.IGNORECASE,
)


def _asks(text: str) -> int:
    """How many questions a text asks: each "?" and each further ask joined to one."""
    return text.count("?") + len(_JOINED_ASK.findall(text))


def _changes(observed: Json) -> dict[str, Json]:
    proposal = observed.get("proposal") or {}
    return {c["field"]: c for c in proposal.get("changes", [])}


# Interview checks: `observed` is a turn as the API returns it (`TurnOut`).
def _interview(observed: Json, e: Expectation) -> Failure | None:
    proposal = observed.get("proposal")
    if proposal is None:
        return Failure(FailureType.SCHEMA_INVALID, f"run {observed['run']['status']}")
    changes = _changes(observed)
    question = proposal.get("next_question") or ""
    if e.check == "proposes":
        change = changes.get(e.field or "")
        if change is None:
            return Failure(FailureType.MISSED_FACT, f"no proposal for {e.field}")
        if e.words and not _has(_value_text(change["value"]), e.words, whole=e.whole_words):
            return Failure(FailureType.MISSED_FACT, f"{e.field} is {change['value']!r}")
        if e.value is not None and change["value"] != e.value:
            return Failure(FailureType.MISSED_FACT, f"{e.field} is {change['value']!r}")
        return None
    if e.check == "no_value_for":
        given = [f for f in e.fields if f in changes and changes[f]["value"] is not None]
        return Failure(FailureType.INVENTED_VALUE, f"values for {given}") if given else None
    if e.check == "state_if_proposed":
        change = changes.get(e.field or "")
        if change is not None and (change["state"] != e.state or change["value"] is not None):
            return Failure(FailureType.UNKNOWN_AS_VALUE, f"{e.field}: {change['state']}")
        return None
    if e.check == "values_avoid":
        texts = [_value_text(c["value"]) for c in changes.values()]
        hit = [t for t in texts if _has(t, e.words, whole=e.whole_words)]
        return Failure(FailureType.INFERENCE, f"values {hit}") if hit else None
    if e.check == "one_question":
        # Each field on its own: beside a next question the reply asks nothing (the contract);
        # with none, the reply may hold the one question.
        if question and "?" in proposal["reply"]:
            return Failure(FailureType.QUESTION, f"a question in the reply: {proposal['reply']!r}")
        asked = question or proposal["reply"]
        asks = _asks(asked)
        return Failure(FailureType.QUESTION, f"{asks} asks: {asked!r}") if asks > 1 else None
    if e.check == "question_mentions_any":
        ok = _has(question + " " + proposal["reply"], e.words, whole=e.whole_words)
        return None if ok else Failure(FailureType.QUESTION, f"asked {question!r}")
    if e.check == "question_avoids":
        bad = _has(question, e.words, whole=e.whole_words)
        return Failure(FailureType.QUESTION, f"asked {question!r}") if bad else None
    if e.check == "reply_mentions_any":
        ok = _has(proposal["reply"], e.words, whole=e.whole_words)
        return None if ok else Failure(FailureType.QUESTION, "reply misses the expected idea")
    if e.check == "missing_excludes":
        again = [f for f in e.fields if f in proposal["missing_critical_fields"]]
        return Failure(FailureType.REASKED, f"asks again for {again}") if again else None
    if e.check == "hard_constraint":
        change = changes.get(e.field or "")
        if change is None or not change["hard_constraint"]:
            return Failure(FailureType.MISSED_FACT, f"{e.field} not proposed as a hard limit")
        return None
    raise ValueError(f"unknown interview check {e.check!r}")


# Discovery checks: `observed` is a slate as the API returns it (`SlateOut`).
def _discovery(observed: Json, e: Expectation, answers: set[tuple[str, str]]) -> Failure | None:
    suggestions = observed["suggestions"]
    if e.check == "size_at_least":
        n = len(suggestions)
        return None if n >= (e.count or 0) else Failure(FailureType.THIN_EVIDENCE, f"{n} shown")
    if e.check == "families_at_least":
        families = {s["family"]["code"] for s in suggestions}
        enough = len(families) >= (e.count or 0)
        return None if enough else Failure(FailureType.DIVERSITY, f"{len(families)} families")
    if e.check == "family_limit":
        codes = [s["family"]["code"] for s in suggestions]
        worst = max((codes.count(c) for c in codes), default=0)
        over = worst > observed["family_limit"]
        return Failure(FailureType.DIVERSITY, f"{worst} from one family") if over else None
    if e.check == "includes_direction":
        found = {s["direction"] for s in suggestions}
        return None if e.direction in found else Failure(FailureType.DIVERSITY, f"{found}")
    if e.check == "grounded":
        bad = [
            s["title"]
            for s in suggestions
            if s["concept_kind"] != "esco"
            or not s["sources"]
            or not s["linked_evidence"]
            or not {(x["field"], x["text"]) for x in s["linked_evidence"]} <= answers
        ]
        return Failure(FailureType.GROUNDING, f"{bad}") if bad else None
    if e.check == "distinct":
        titles = [s["title"].casefold() for s in suggestions]
        ids = [s["concept_id"] for s in suggestions]
        twice = len(set(titles)) != len(titles) or len(set(ids)) != len(ids)
        return Failure(FailureType.DUPLICATE, f"{titles}") if twice else None
    if e.check == "no_percentage":
        percent = re.search(r"\d\s?(?:%|per ?cent)", json.dumps(observed), re.IGNORECASE)
        return Failure(FailureType.INFERENCE, percent.group(0)) if percent else None
    if e.check == "unsupported_not_suggested":
        # DIV-1 (ADR 0015 decision 2): a title idea is a suggestion only when ESCO holds it or
        # the UK job-title index lists it, and an indexed one only in its own list, never in
        # the slate; an idea nothing corroborates is never suggested.
        shown = {s["title"].casefold() for s in suggestions}
        outside = [
            i["title"]
            for i in observed["title_ideas"]
            if i["reason"] in ("in_uk_title_index", "not_yet_found")
        ]
        leaked = [t for t in outside if t.casefold() in shown]
        return Failure(FailureType.UNSUPPORTED_TITLE, f"{leaked}") if leaked else None
    if e.check == "title_idea_reasons":
        reasons = {i["title"]: i["reason"] for i in observed["title_ideas"]}
        same = reasons == e.value
        return None if same else Failure(FailureType.UNSUPPORTED_TITLE, f"{reasons}")
    if e.check == "fewer_has_reason":
        short = len(suggestions) < observed["target_size"] and not observed["fewer_reasons"]
        return Failure(FailureType.THIN_EVIDENCE, "fewer, with no reason") if short else None
    if e.check == "joined_by_skills":
        # Sprint W: work joins a title of the person's own only by shared essential skills,
        # never by its words. Every suggestion but the title's own occupation (found as the
        # person's role or target) says how many it shares.
        loose = [
            s["title"]
            for s in suggestions
            if not {"current", "user_proposed"} & set(s["channels"])
            and not any(
                reason["shared"] >= MIN_SHARED_SKILLS
                for reason in s["reasons"]
                if reason["reason"] == "joined_by_shared_skills"
            )
        ]
        return Failure(FailureType.GROUNDING, f"not joined by skills: {loose}") if loose else None
    if e.check == "searched_through_skills":
        # Every other search reaches work only through one of its own essential skills whose
        # label holds every content word of the search, and the suggestion's words name that
        # skill (never a title, hidden label, ISCO group or description, Task W2B fix round
        # 1; never through one shared word such as "people" or "give", fix round 2).
        essential: Mapping[str, list[str]] = observed.get("essential_skills", {})
        loose = [
            f"{s['title']}: {reason['search']} -> {reason['skill']}"
            for s in suggestions
            for reason in s["reasons"]
            if reason["reason"] == "searched_through_skill"
            and not (
                reason["skill"] in essential.get(s["concept_id"], [])
                and _every_word_in(reason["search"], reason["skill"])
            )
        ]
        return Failure(FailureType.GROUNDING, f"not through a skill: {loose}") if loose else None
    if e.check == "work_style_not_searched":
        # A one-word answer about how someone likes to work ("structured") matches skills too
        # loosely, so no search resting on such answers alone runs; a longer one ("working
        # outdoors") is searched like any other (Task W2B fix rounds 2 and 3; provisional).
        ran = [
            q["text"]
            for q in observed["queries"]
            if q["based_on"]
            and all(
                item["field"] == "work_style" and len(item["text"].split()) == 1
                for item in q["based_on"]
            )
        ]
        return Failure(FailureType.GROUNDING, f"searched: {ran}") if ran else None
    if e.check == "missed_answers_named":
        # An answer every search resting on it found nothing with is named in the notes, on
        # a full slate too, and one that found work never is (Task W2B re-review 2, N-I1). A
        # one-word work style a model searched beside a task keeps its own note instead
        # (re-review 3, M2), so naming one as "found no work" is wrong (re-review 4, M3).
        styles = {
            text for field, text in answers if field == "work_style" and len(text.split()) == 1
        }
        reached: dict[str, bool] = {}
        for q in observed["queries"]:
            for item in q["based_on"]:
                style = item["field"] == "work_style" and len(item["text"].split()) == 1
                if item["field"] in _SEARCHED_FIELDS and not style:
                    reached[item["text"]] = reached.get(item["text"], False) or q["reach"] > 0
        nothing = {
            note["answer"].casefold()
            for note in observed["notes"]
            if note["reason"] == "answer_found_no_work"
        }

        def named(text: str) -> bool:
            return text.casefold() in nothing

        unnamed = [text for text, hit in reached.items() if not hit and not named(text)]
        wrong = [text for text, hit in reached.items() if hit and named(text)]
        wrong += sorted(text for text in styles if named(text))
        if unnamed or wrong:
            return Failure(FailureType.THIN_EVIDENCE, f"not named {unnamed}, wrongly {wrong}")
        return None
    if e.check == "general_searches_add_only":
        # A search too general to find work on its own ("writing reports" reaches 217
        # occupations through the main names of their essential skills) only adds weight to
        # work another search found, and the slate names it (Task W2B re-review 2, N-I2;
        # provisional thresholds).
        general = {q["query_id"]: q["text"] for q in observed["queries"] if q["too_general"]}
        alone = [s["title"] for s in suggestions if set(s["matched_queries"]) <= set(general)]
        named_general = {
            note["search"].casefold()
            for note in observed["notes"]
            if note["reason"] == "too_general"
        }
        unnamed = [text for text in general.values() if text.casefold() not in named_general]
        if alone or unnamed:
            return Failure(FailureType.GROUNDING, f"found alone {alone}, not named {unnamed}")
        return None
    if e.check == "titles_ambiguous":
        # A title several occupations hold joins nothing until the person chooses which they
        # mean: never joined over their skills together (Task W2B fix round 2).
        missing = [title for title in e.words if title not in observed["ambiguous_titles"]]
        joined = [
            s["title"]
            for s in suggestions
            for reason in s["reasons"]
            if reason["reason"] == "joined_by_shared_skills" and reason["answer"] in e.words
        ]
        bad = missing or joined
        return Failure(FailureType.GROUNDING, f"{missing} {joined}") if bad else None
    if e.check == "small_pool_has_reason":
        # The 60-120 working pool is soft, "where evidence permits" (DIV1-02): below it, a
        # short slate says why it is short and a full one says how many it chose from.
        size, target = observed["pool_size"], observed["pool_target"][0]
        said = bool(observed["fewer_reasons"]) or any(
            note["reason"] == "small_pool" and note["pool_size"] == size
            for note in observed["notes"]
        )
        quiet = size < target and not said
        return Failure(FailureType.THIN_EVIDENCE, f"pool {size}, no reason") if quiet else None
    if e.check == "connection":
        connection = observed.get("connection")
        if connection is None:
            return Failure(FailureType.DIVERSITY, "no unexpected connection")
        by_id = {s["concept_id"]: s for s in suggestions}
        count = connection["shared_skill_count"]
        ok = (
            count >= MIN_SHARED_SKILLS
            and len(connection["shared_skills"]) == count
            and connection["concept_id"] in by_id
            and by_id[connection["concept_id"]]["direction"] != "close_to_current"
        )
        return None if ok else Failure(FailureType.GROUNDING, f"connection {connection}")
    if e.check == "no_connection":
        # A role several occupations hold as a title is no one occupation to state a fact
        # about (Task W2B fix round 1).
        connection = observed.get("connection")
        return None if connection is None else Failure(FailureType.GROUNDING, f"{connection}")
    if e.check == "titles_unmatched":
        unmatched = observed["unmatched_titles"]
        missing = [title for title in e.words if title not in unmatched]
        searched = [q["text"] for q in observed["queries"] if q["text"] in e.words and q["hits"]]
        bad = missing or searched
        return Failure(FailureType.GROUNDING, f"{missing} {searched}") if bad else None
    if e.check == "limit_reported":
        # The floor is applied with its counts, and pay it cannot compare is never below it
        # (Task 7 slice B). The evaluation holds no reviewed UK SOC mapping, so every pooled
        # occupation's pay is unknown and the floor must leave nothing out.
        floor = observed.get("salary_floor")
        if floor is None:
            return Failure(FailureType.LIMIT, "salary floor not reported")
        if floor["left_out"]:
            return Failure(FailureType.LIMIT, f"{floor['left_out']} left out with pay unknown")
        return None
    raise ValueError(f"unknown discovery check {e.check!r}")


# Explanation checks: `observed` holds the first view's slate (`SlateOut`), the explanation
# as the discovery carries it (`SlateExplanationOut`) and, for each suggestion, ESCO's record
# texts as the taxonomy serves them (an independent source for the quotations).
def _explanation(observed: Json, e: Expectation, answers: list[str]) -> Failure | None:
    explanation = observed.get("explanation") or {}
    written = explanation.get("written")
    shown = observed["slate"]["suggestions"]
    if e.check == "provenance_kept":
        bare = [s["title"] for s in shown if not (s["reasons"] and s["linked_evidence"])]
        return Failure(FailureType.GROUNDING, f"no provenance for {bare}") if bare else None
    if written is None:
        status = explanation.get("run", {}).get("status", "never asked")
        return Failure(FailureType.SCHEMA_INVALID, f"explanation {status}")
    claims = [(s["concept_id"], c) for s in written["suggestions"] for c in s["claims"]]
    if e.check == "written_for_each":
        explained = [s["concept_id"] for s in written["suggestions"]]
        wanted = [s["concept_id"] for s in shown]
        empty = [s["title"] for s in written["suggestions"] if not s["claims"]]
        if explained != wanted or empty:
            return Failure(FailureType.GROUNDING, f"explained {len(explained)} of {len(wanted)}")
        return None
    if e.check == "both_sources":
        one_sided = [c["text"] for _, c in claims if {"answer", "esco"} - _sources(c)]
        return Failure(FailureType.GROUNDING, f"{one_sided}") if one_sided else None
    if e.check == "quotations_are_spans":
        records: Mapping[str, list[str]] = observed["records"]
        unfound = [
            q["text"]
            for concept, c in claims
            for q in c["quotations"]
            if not any(
                q["text"] in text
                for text in (answers if q["source"] == "answer" else records[concept])
            )
        ]
        return (
            Failure(FailureType.GROUNDING, f"not in their sources: {unfound}") if unfound else None
        )
    if e.check == "no_percentage":
        percent = re.search(r"\d\s?(?:%|per ?cent)", json.dumps(written), re.IGNORECASE)
        return Failure(FailureType.INFERENCE, percent.group(0)) if percent else None
    raise ValueError(f"unknown explanation check {e.check!r}")


def _sources(claim: Json) -> set[str]:
    return {q["source"] for q in claim["quotations"]}


def _pool(slate: Json) -> set[str]:
    return {s["concept_id"] for s in slate["suggestions"]} | {
        n["concept_id"] for n in slate["not_included"]
    }


def _paired(case: Case, observed: Json, other: Json, e: Expectation) -> Failure | None:
    if e.check == "same_fields_as":
        # Only the fields the message states unambiguously (`fields`): whether a judgement
        # call such as "something more hands-on" becomes a proposal varies run to run.
        compared = set(e.fields) if e.fields else None
        mine, theirs = set(_changes(observed)), set(_changes(other))
        if compared is not None:
            mine, theirs = mine & compared, theirs & compared
        if mine != theirs:
            return Failure(FailureType.COUNTERFACTUAL, f"{sorted(mine)} vs {sorted(theirs)}")
        return None
    if e.check == "same_slate_as":
        mine = {s["concept_id"] for s in observed["suggestions"]}
        theirs = {s["concept_id"] for s in other["suggestions"]}
        return None if mine == theirs else Failure(FailureType.COUNTERFACTUAL, "slates differ")
    if e.check == "pool_includes_pool_of":
        missing = _pool(other) - _pool(observed)
        if missing:
            return Failure(FailureType.PREFERENCE_EXCLUSION, f"{len(missing)} removed")
        return None
    raise ValueError(f"unknown paired check {e.check!r} in {case.id}")


PAIRED = frozenset({"same_fields_as", "same_slate_as", "pool_includes_pool_of"})


def answers_of(case: Case) -> set[tuple[str, str]]:
    """The answer texts a discovery case's suggestions may cite."""
    found: set[tuple[str, str]] = set()
    for name, value in case.profile.items():
        if isinstance(value, list):
            found |= {(name, str(item)) for item in value}
        elif isinstance(value, str):
            found.add((name, value))
    return found


def evaluate(case: Case, observed: Json, others: Mapping[str, Json]) -> list[Failure]:
    """Every expectation's failure, if any. Paired expectations need the other case's
    observation; a missing one is a failure of its own kind, never a pass."""
    failures: list[Failure] = []
    for e in case.expect:
        failure: Failure | None
        if e.check in PAIRED:
            other = others.get(e.other or "")
            failure = (
                Failure(FailureType.COUNTERFACTUAL, f"{e.other} was not observed")
                if other is None
                else _paired(case, observed, other, e)
            )
        elif case.kind is CaseKind.INTERVIEW:
            failure = _interview(observed, e)
        elif case.kind is CaseKind.DISCOVERY:
            failure = _discovery(observed, e, answers_of(case))
        elif case.kind is CaseKind.EXPLANATION:
            failure = _explanation(observed, e, [text for _, text in answers_of(case)])
        elif case.kind is CaseKind.SUPPORT:
            # `support_shown`: the support flow (the panel beside the sent message).
            shown = bool(observed[e.check])
            want = bool(e.value)
            failure = (
                None
                if shown == want
                else Failure(
                    FailureType.SUPPORT_MISSED if want else FailureType.SUPPORT_FALSE_POSITIVE,
                    f"{e.check}: {case.message or ''}",
                )
            )
        else:
            failure = _guard(observed, e)
        if failure is not None:
            failures.append(failure)
    return failures


def _guard(observed: Json, e: Expectation) -> Failure | None:
    problems: list[str] = observed["problems"]
    if e.check == "refused_with":
        hit = any(_has(p, e.words) for p in problems)
        return None if hit else Failure(FailureType.GUARD, f"accepted: {problems}")
    if e.check == "accepted":
        return Failure(FailureType.GUARD, f"refused: {problems}") if problems else None
    if e.check == "basis":
        bases = {c["field"]: c["basis"] for c in observed.get("changes", [])}
        ok = bases.get(e.field or "") == e.state
        return None if ok else Failure(FailureType.GUARD, f"basis {bases}")
    raise ValueError(f"unknown guard check {e.check!r}")


# Offline subjects: deterministic code only (no model, no network).
_SOURCE = uuid.UUID("00000000-0000-4000-8000-00000000e7a1")
_AT = datetime(2027, 1, 1, tzinfo=UTC)


def document_of(case: Case) -> ProfileDocument:
    new = ProfileInput.model_validate(profile_input_of(case.profile))
    return apply_profile_input(empty_profile(), new, _SOURCE)


def observe_support(case: Case) -> Json:
    return {"support_shown": has_risk_stem(case.message or "")}


def observe_guard(case: Case) -> Json:
    """A canned output through the same deterministic check the live output passes."""
    document = document_of(case)
    if case.discovery_output is not None:
        context = DiscoveryInput(profile_version=1, evidence=evidence_of(document))
        output = DiscoveryOutput.model_validate(case.discovery_output)
        _, found = check_discovery(output, context, ProposalOrigin.MODEL)
        return {"problems": found, "changes": []}
    turn = TurnInput(
        profile_version=1,
        profile=context_profile(document),
        messages=[
            ContextMessage(ref="m1", message_id=_SOURCE, text=case.message or "", sent_at=_AT)
        ],
        replies={},
    )
    proposal, problems = check_turn(
        InterviewTurnOutput.model_validate(case.output), turn, ProposalOrigin.MODEL
    )
    changes = [] if proposal is None else [c.model_dump(mode="json") for c in proposal.changes]
    return {"problems": problems, "changes": changes}


def observe_discovery_offline(tx: Tx, case: Case, *, release: str | None = None) -> Json:
    """The slate the fixture proposer's queries (or the case's own searches) give over the
    held taxonomy, with each suggestion's essential skills as the taxonomy holds them: the
    pipeline and its rules are under test, not a model. `release`: the release the
    searches are recorded as chosen for (none: not recorded)."""
    view = _offline_slate(tx, case, release)
    observed = SlateOut.of(view, Emphasis.BALANCED).model_dump(mode="json")
    essential: dict[str, list[str]] = {}
    for suggestion in view.suggestions:
        concept = suggestion.candidate.occupation.concept_id
        detail = taxonomy_store.occupation(tx, concept)
        if detail is None:
            raise ValueError(f"{case.id}: a suggestion is not in the held release")
        essential[str(concept)] = [
            s.preferred_label for s in detail.skills if s.relation == "essential"
        ]
    return {**observed, "essential_skills": essential}


def observe_explanation_offline(tx: Tx, case: Case) -> Json:
    """The fixture explainer over that slate's first view: the input's bounds, the
    quotation check and the API shape are under test, not a model's writing."""
    view = _offline_slate(tx, case, None)
    concepts = [s.candidate.occupation.concept_id for s in view.suggestions]
    records = taxonomy_store.occupation_facts(tx, concepts, skills_shown=RECORD_STEPS[0][1])
    context = build_input(
        discovery_id=_SOURCE,
        profile_version=1,
        release=view.release.dataset_id,
        answers=evidence_of(document_of(case)),
        occupations=[records[concept] for concept in concepts],
    )
    output = fixture_explanation(explainer_context(render_explanation_prompt(context)))
    written, problems = check_explanation(output, context, ProposalOrigin.FIXTURE)
    if written is None:
        raise ValueError(f"{case.id}: the fixture explanation failed its check: {problems}")
    return {
        "slate": SlateOut.of(view, Emphasis.BALANCED).model_dump(mode="json"),
        "explanation": {
            "run": {"status": "complete"},
            "written": WrittenExplanationOut.of(written).model_dump(mode="json"),
        },
        "records": {
            str(concept): [fact.preferred_label, fact.description, *fact.essential_skills]
            for concept, fact in records.items()
        },
    }


def _offline_slate(tx: Tx, case: Case, release: str | None) -> SlateView:
    document = document_of(case)
    context = DiscoveryInput(profile_version=1, evidence=evidence_of(document), release=release)
    output = (
        DiscoveryOutput.model_validate(case.discovery_output)
        if case.discovery_output is not None
        else fixture_queries(prompt_context(render_discovery_prompt(context)))
    )
    proposal, problems = check_discovery(output, context, ProposalOrigin.FIXTURE)
    if proposal is None:
        raise ValueError(f"{case.id}: the fixture proposal failed its check: {problems}")
    run = Run(
        run_id=_SOURCE,
        workspace_id=_SOURCE,
        kind=RunKind.DISCOVERY,
        data_mode=DataMode.DEMO,
        synthetic=True,
        requested_by=_SOURCE,
        model_id=FIXTURE_DISCOVERY_MODEL_ID,
        model_mode="fixture",
        status=WorkState.COMPLETE,
        failure_class=None,
        output_id=None,
        created_at=_AT,
        started_at=_AT,
        finished_at=_AT,
        profile_version=1,
    )
    # The product's committed packs: no reviewed mapping, no published assessment.
    hard = HardFilterInput(committed_reviews(), committed_packs().product)
    # Each target as its record would be stored, by the one resolver (nothing is written).
    pack = pack_targets(committed_data())
    records: dict[str, TargetRecord] = {}
    for title in target_titles(document):  # one per title as a concept, the first standing
        record = resolve_target(tx, _SOURCE, title, pack)
        records.setdefault(record.key, record)
    return compute_slate(
        tx,
        DiscoveryView(run, proposal),
        proposal,
        document,
        SlateControls(),
        hard,
        list(records.values()),
    )


def failures_by_type(results: Mapping[str, list[Failure]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for failures in results.values():
        for failure in failures:
            counts[failure.type.value] = counts.get(failure.type.value, 0) + 1
    return dict(sorted(counts.items()))
