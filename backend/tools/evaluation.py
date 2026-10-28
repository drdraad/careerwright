"""The Sprint 2 interview and discovery evaluation (plan Sprint 2 acceptance; TEST1-10, DIV1-08,
REC1-09): reviewed synthetic cases with semantic expectations, never exact prose.

`evaluation_cases.json` holds the cases. Each names what it exercises (`kind`), its synthetic
input and its expectations; every expectation has a failure type, so a run reports failures
by type. The same checks read API-shaped JSON, so the offline run (deterministic subjects:
the support screen, the output guard, and discovery with the fixture proposer over the full
ESCO release) and the live run (`tools.live_eval`, the test model through the product) share
them. Model behaviour is evidenced only by the live run: the deterministic subjects certify
the pipeline and its guards, not the model (plan section 9).

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

from nessa.api.discovery_schemas import SlateOut
from nessa.db import Tx
from nessa.identity.model_registry import FIXTURE_DISCOVERY_MODEL_ID
from nessa.identity.records import Run, RunKind
from nessa.profile.discovery import (
    DiscoveryInput,
    DiscoveryOutput,
    check_discovery,
    evidence_of,
)
from nessa.profile.discovery import render_prompt as render_discovery_prompt
from nessa.profile.document import (
    FIELD_NAMES,
    ProfileDocument,
    ProfileInput,
    apply_profile_input,
    empty_profile,
)
from nessa.profile.exploration import DiscoveryView, compute_slate
from nessa.profile.fixture_discovery import fixture_queries, prompt_context
from nessa.profile.interview import (
    ContextMessage,
    InterviewTurnOutput,
    ProposalOrigin,
    TurnInput,
    check_turn,
    context_profile,
)
from nessa.profile.safety import screen_message
from nessa.profile.slate import Emphasis, SlateControls
from nessa.vocabulary import DataMode, WorkState

CASES_PATH = Path(__file__).with_name("evaluation_cases.json")
Json = dict[str, Any]


class CaseKind(StrEnum):
    INTERVIEW = "interview"  # one interview turn: model behaviour (live only)
    DISCOVERY = "discovery"  # the confirmed answers to a slate
    SUPPORT = "support"  # the acute-distress screen, before any model call
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
    LIMIT = "limit"  # a recorded limit not reported as unapplied
    SUPPORT_MISSED = "support_missed"
    SUPPORT_FALSE_POSITIVE = "support_false_positive"
    GUARD = "guard"  # the output check accepted what it should refuse, or the reverse


class Expectation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    check: str
    field: str | None = None
    fields: list[str] = Field(default_factory=list)
    words: list[str] = Field(default_factory=list)
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
    discovery_output: Json | None = None  # a guard case's canned discovery output
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


def _has(text: str, words: list[str]) -> bool:
    folded = text.casefold()
    return any(word.casefold() in folded for word in words)


def _value_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value


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
        if e.words and not _has(_value_text(change["value"]), e.words):
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
        hit = [t for t in texts if _has(t, e.words)]
        return Failure(FailureType.INFERENCE, f"values {hit}") if hit else None
    if e.check == "one_question":
        asked = question.count("?") + proposal["reply"].count("?")
        return Failure(FailureType.QUESTION, f"{asked} questions") if asked > 1 else None
    if e.check == "question_mentions_any":
        ok = _has(question + " " + proposal["reply"], e.words)
        return None if ok else Failure(FailureType.QUESTION, f"asked {question!r}")
    if e.check == "question_avoids":
        bad = _has(question, e.words)
        return Failure(FailureType.QUESTION, f"asked {question!r}") if bad else None
    if e.check == "reply_mentions_any":
        ok = _has(proposal["reply"], e.words)
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
        percent = re.search(r"\d\s?%|per ?cent", json.dumps(observed), re.IGNORECASE)
        return Failure(FailureType.INFERENCE, percent.group(0)) if percent else None
    if e.check == "unsupported_not_suggested":
        shown = {s["title"].casefold() for s in suggestions}
        leaked = [t for t in observed["unsupported_hypotheses"] if t.casefold() in shown]
        return Failure(FailureType.UNSUPPORTED_TITLE, f"{leaked}") if leaked else None
    if e.check == "fewer_has_reason":
        short = len(suggestions) < observed["target_size"] and not observed["fewer_reasons"]
        return Failure(FailureType.THIN_EVIDENCE, "fewer, with no reason") if short else None
    if e.check == "limit_reported":
        given = bool(observed["limits_not_applied"])
        return None if given else Failure(FailureType.LIMIT, "salary floor not reported")
    raise ValueError(f"unknown discovery check {e.check!r}")


def _pool(slate: Json) -> set[str]:
    return {s["concept_id"] for s in slate["suggestions"]} | {
        n["concept_id"] for n in slate["not_included"]
    }


def _paired(case: Case, observed: Json, other: Json, e: Expectation) -> Failure | None:
    if e.check == "same_fields_as":
        mine, theirs = set(_changes(observed)), set(_changes(other))
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
        elif case.kind is CaseKind.SUPPORT:
            shown = bool(observed["support_shown"])
            want = bool(e.value)
            failure = (
                None
                if shown == want
                else Failure(
                    FailureType.SUPPORT_MISSED if want else FailureType.SUPPORT_FALSE_POSITIVE,
                    case.message or "",
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
    return {"support_shown": screen_message(case.message or "") is not None}


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


def observe_discovery_offline(tx: Tx, case: Case) -> Json:
    """The slate the fixture proposer's queries give over the held taxonomy: the pipeline
    and its rules are under test, not a model."""
    document = document_of(case)
    context = DiscoveryInput(profile_version=1, evidence=evidence_of(document))
    output = fixture_queries(prompt_context(render_discovery_prompt(context)))
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
    view = compute_slate(tx, DiscoveryView(run, proposal), proposal, document, SlateControls())
    return SlateOut.of(view, Emphasis.BALANCED).model_dump(mode="json")


def failures_by_type(results: Mapping[str, list[Failure]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for failures in results.values():
        for failure in failures:
            counts[failure.type.value] = counts.get(failure.type.value, 0) + 1
    return dict(sorted(counts.items()))
