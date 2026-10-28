"""The Sprint 2 evaluation: the case set is well formed, the deterministic subjects (the
support screen and the output guard) pass their cases, and the semantic checks catch the
failures they name (TEST1-10). Discovery cases run against the full ESCO release in
`tests/integration/test_evaluation.py`; interview cases need a model and run live only."""

from typing import Any

import pytest

from tools.evaluation import (
    PAIRED,
    Case,
    CaseKind,
    FailureType,
    evaluate,
    failures_by_type,
    load_cases,
    observe_guard,
    observe_support,
)

CASES = load_cases()
BY_ID = {case.id: case for case in CASES}
LIVE_CASES_ALLOWED = 6  # the controller's cap for this task's live run (R5)


@pytest.mark.req("TEST1-10")
def test_there_are_at_least_thirty_reviewed_synthetic_cases_with_semantic_expectations() -> None:
    assert len(CASES) >= 30
    assert len(BY_ID) == len(CASES)  # unique IDs
    assert all(case.synthetic and case.expect and case.requirements for case in CASES)
    assert {case.kind for case in CASES} == set(CaseKind)
    for case in CASES:
        for expectation in case.expect:
            if expectation.check in PAIRED:
                partner = BY_ID[expectation.other or ""]
                assert partner.kind is case.kind
    live = [case for case in CASES if case.live]
    assert len(live) <= LIVE_CASES_ALLOWED
    assert {case.kind for case in live} <= {CaseKind.INTERVIEW, CaseKind.DISCOVERY}
    for case in CASES:
        if case.kind is CaseKind.INTERVIEW:
            assert case.message is not None
            assert case.message.startswith("Synthetic persona:")  # labelled where it is sent


@pytest.mark.req("PROF-09")
@pytest.mark.parametrize("case", [c for c in CASES if c.kind is CaseKind.SUPPORT], ids=str)
def test_every_support_case_passes(case: Case) -> None:
    assert evaluate(case, observe_support(case), {}) == []


@pytest.mark.req("REC1-02", "REC1-05", "REC1-09", "PROF-09")
@pytest.mark.parametrize("case", [c for c in CASES if c.kind is CaseKind.GUARD], ids=str)
def test_every_guard_case_passes(case: Case) -> None:
    assert evaluate(case, observe_guard(case), {}) == []


def turn(
    changes: list[dict[str, Any]], *, question: str = "What next?", reply: str = "Thanks."
) -> dict[str, Any]:
    return {
        "run": {"status": "complete"},
        "proposal": {
            "reply": reply,
            "changes": changes,
            "next_question": question,
            "missing_critical_fields": [],
        },
    }


def change(field: str, value: Any, *, state: str = "provided") -> dict[str, Any]:
    return {"field": field, "state": state, "value": value, "hard_constraint": False}


@pytest.mark.req("TEST1-10")
def test_the_interview_checks_name_the_failure_they_find() -> None:
    p02 = BY_ID["INT-01"]
    good = turn([change("enjoyed_tasks", ["fixing machines"])])
    invented = turn(
        [
            change("enjoyed_tasks", ["fixing machines"]),
            change("direct_spend_cap", {"minor_units": 200000, "currency": "GBP"}),
        ],
        question="How much could you spend? And which city?",
    )
    failed = {"run": {"status": "failed"}, "proposal": None}

    assert evaluate(p02, good, {}) == []
    found = {f.type for f in evaluate(p02, invented, {})}
    assert found == {FailureType.INVENTED_VALUE, FailureType.QUESTION}
    assert {f.type for f in evaluate(p02, failed, {})} == {FailureType.SCHEMA_INVALID}


@pytest.mark.req("REC1-09")
def test_a_counterfactual_pair_fails_when_the_cue_changes_the_fields_or_one_is_missing() -> None:
    first, second = BY_ID["INT-04"], BY_ID["INT-05"]
    base = [change("current_role", "Payroll officer"), change("weekly_study_hours", 6.0)]
    drift = [*base, change("enjoyed_tasks", ["caring for others"])]

    same = evaluate(first, turn(base), {"INT-05": turn(base)})
    differs = evaluate(first, turn(base), {"INT-05": turn(drift)})
    unseen = evaluate(second, turn(base), {})

    assert same == []
    assert [f.type for f in differs] == [FailureType.COUNTERFACTUAL]
    assert [f.type for f in unseen] == [FailureType.COUNTERFACTUAL]  # missing is never a pass


def slate(*suggestions: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "suggestions": list(suggestions),
        "not_included": [],
        "family_limit": 2,
        "target_size": 6,
        "fewer_reasons": [],
        "limits_not_applied": [],
        "unsupported_hypotheses": [],
        **extra,
    }


def suggestion(title: str, family: str, direction: str, **extra: Any) -> dict[str, Any]:
    return {
        "concept_id": title,
        "concept_kind": "esco",
        "title": title,
        "family": {"code": family, "label": family},
        "direction": direction,
        "sources": [{"kind": "esco", "uri": f"http://data.europa.eu/esco/occupation/{title}"}],
        "linked_evidence": [{"field": "enjoyed_tasks", "text": "repairing physical objects"}],
        **extra,
    }


@pytest.mark.req("DIV1-08", "TEST1-10")
def test_the_discovery_checks_name_the_failure_they_find() -> None:
    p02 = BY_ID["DSC-01"]
    varied = slate(
        suggestion("bicycle mechanic", "723", "less_familiar"),
        suggestion("tree surgeon", "621", "less_familiar"),
        suggestion("groundsperson", "921", "less_familiar"),
    )
    narrow = slate(
        suggestion("bicycle mechanic", "723", "close_to_current"),
        suggestion("bicycle mechanic", "723", "close_to_current"),
        suggestion("motor mechanic", "723", "close_to_current"),
        unsupported_hypotheses=["Bicycle mechanic"],
    )
    ungrounded = slate(
        suggestion("bicycle mechanic", "723", "less_familiar", linked_evidence=[]),
        suggestion("wind whisperer", "999", "less_familiar", concept_kind="provisional"),
        suggestion("tree surgeon", "621", "less_familiar"),
    )

    assert evaluate(p02, varied, {}) == []
    assert failures_by_type({"narrow": evaluate(p02, narrow, {})}) == {
        "diversity": 3,
        "duplicate_alias": 1,
        "unsupported_title": 1,
    }
    assert [f.type for f in evaluate(p02, ungrounded, {})] == [FailureType.GROUNDING]
    assert [f.type for f in evaluate(BY_ID["DSC-06"], slate(), {})] == [
        FailureType.THIN_EVIDENCE
    ]  # fewer than six with no reason given
