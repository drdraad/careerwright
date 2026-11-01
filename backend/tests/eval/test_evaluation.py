"""The Sprint 2 evaluation: the case set is well formed, the deterministic subjects (the
support screen and the output guard) pass their cases, and the semantic checks catch the
failures they name (TEST1-10). Discovery cases run against the full ESCO release in
`tests/integration/test_evaluation.py`; interview cases need a model and run live only."""

import json
from typing import Any

import pytest

from tools.evaluation import (
    PAIRED,
    SCHOOL_LEAVER,
    Case,
    CaseKind,
    FailureType,
    _discovery,
    evaluate,
    failures_by_type,
    load_cases,
    observe_guard,
    observe_interview_demo,
    observe_strength,
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


@pytest.mark.req("STATE-11", "PROF-13", "PROF-14")
@pytest.mark.parametrize("case", [c for c in CASES if c.demo], ids=str)
def test_every_demo_interview_case_passes_on_the_demo_interviewer(case: Case) -> None:
    # Task 6f: offline, the demo interviewer's fixed patterns through the same check; the live
    # model's run of the same case is Task 6e's (R5).
    assert case.kind is CaseKind.INTERVIEW
    assert evaluate(case, observe_interview_demo(case), {}) == []


@pytest.mark.req("TEST1-16")
@pytest.mark.parametrize("case", [c for c in CASES if c.kind is CaseKind.STRENGTH], ids=str)
def test_every_strength_case_passes(case: Case) -> None:
    # Task 6e: a canned strength proposal through the same deterministic check a model's
    # passes: a quotation of the person's own words is accepted, anything else refused.
    assert evaluate(case, observe_strength(case), {}) == []


@pytest.mark.req("TEST1-16")
def test_the_synthetic_school_leaver_is_labelled_kept_apart_and_has_her_cases() -> None:
    card = json.loads(SCHOOL_LEAVER.read_text(encoding="utf-8"))
    hers = [case for case in CASES if case.persona == card["id"]]

    assert card["synthetic"] is True
    assert card["label"].startswith("Synthetic")
    assert "m0" not in SCHOOL_LEAVER.parts  # never in the supplied pack
    assert card["current_role"] == {"state": "no_job_yet"}  # no invented job title
    assert not {"income", "current_net_income_minor", "salary"} & set(card)  # no income
    # Four to six cases with the browser test of the no-job first answer (Task 6f's).
    assert 4 <= len(hers) + 1 <= 6
    assert {case.kind for case in hers} == {
        CaseKind.INTERVIEW,
        CaseKind.DISCOVERY,
        CaseKind.STRENGTH,
    }
    assert all(case.synthetic and "TEST1-16" in case.requirements for case in hers)
    assert [c.id for c in hers if c.kind is CaseKind.INTERVIEW] == card["evaluation_cases"][:2]
    assert {c.id for c in hers} == set(card["evaluation_cases"])


@pytest.mark.req("TEST1-16")
def test_a_strength_that_is_not_her_words_fails_its_check() -> None:
    case = BY_ID["STR-01"]
    accepted = observe_strength(case)
    paraphrase = {**accepted, "strength": {**accepted["strength"], "quotation": "lab skills"}}

    assert evaluate(case, accepted, {}) == []
    assert [f.type for f in evaluate(case, paraphrase, {})] == [FailureType.GROUNDING]
    assert [f.type for f in evaluate(case, {"problems": ["x"], "strength": None}, {})] == [
        FailureType.GUARD
    ]


@pytest.mark.req("TEST1-16", "REC1-05")
def test_nothing_close_to_now_fails_a_suggestion_close_to_a_job_she_never_had() -> None:
    case = BY_ID["DSC-21"]
    [check] = [e for e in case.expect if e.check == "nothing_close_to_now"]
    close = {
        "direction": "close_to_current",
        "reasons": [{"reason": "searched_through_skill", "field": "enjoyed_tasks"}],
    }
    joined = {
        "direction": "transferable",
        "reasons": [{"reason": "joined_by_shared_skills", "field": "current_role"}],
    }
    far = {
        "direction": "less_familiar",
        "reasons": [{"reason": "searched_through_skill", "field": "enjoyed_tasks"}],
    }

    for shown, failed in (([close], True), ([joined], True), ([far], False)):
        found = _discovery({"suggestions": shown}, check, set())
        assert (found is not None) is failed
        assert found is None or found.type is FailureType.GROUNDING


def test_state_is_fails_a_job_title_or_a_skip_for_no_job_yet() -> None:
    case = BY_ID["INT-15"]
    [expectation] = [e for e in case.expect if e.check == "state_is"]
    as_title = turn([change("current_role", "student")])
    as_skip = turn([change("current_role", None, state="skipped")])
    field = expectation.field or ""
    for observed in (as_title, as_skip, turn([])):
        failures = [f for f in evaluate(case, observed, {}) if field in f.detail]
        assert [f.type for f in failures][:1] == [FailureType.MISSED_FACT]


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


@pytest.mark.req("PROF-08")
def test_the_question_is_counted_where_it_lives_one_in_next_question_none_in_the_reply() -> None:
    # Task 6 review A-I-6: each field is checked on its own, so a paraphrase is not two
    # questions and two asks in one sentence are not one.
    p02 = BY_ID["INT-01"]
    noted = [change("enjoyed_tasks", ["fixing machines"])]
    one = turn(noted, reply="Thanks, that helps.", question="Which machines did you like fixing?")
    in_reply = turn(noted, reply="Which machines?", question="Which machines did you fix?")
    two_asks = turn(noted, question="Which machines did you fix, and would you work outdoors?")
    two = turn(noted, question="Which machines? And would you work outdoors?")

    assert evaluate(p02, one, {}) == []
    for observed in (in_reply, two, two_asks):
        assert [f.type for f in evaluate(p02, observed, {})] == [FailureType.QUESTION]
    # With no next question the reply may hold the one question, but not two (N-M7).
    only_reply = turn(noted, reply="Which machines did you fix?", question="")
    assert evaluate(p02, only_reply, {}) == []
    two_in_reply = turn(noted, reply="Which machines? Outdoors?", question="")
    assert [f.type for f in evaluate(p02, two_in_reply, {})] == [FailureType.QUESTION]


@pytest.mark.req("TEST1-10")
def test_words_are_matched_as_words_not_inside_other_words() -> None:
    p02 = BY_ID["INT-01"]  # its question must avoid "test" and "type"
    noted = [change("enjoyed_tasks", ["fixing machines"])]

    contest = turn(noted, question="Which prototypes or contests did you enjoy?")
    typed = turn(noted, question="Would a skills test suit you?")

    assert evaluate(p02, contest, {}) == []
    assert [f.type for f in evaluate(p02, typed, {})] == [FailureType.QUESTION]
    manager = turn([change("current_role", "Payroll manager")])
    found = evaluate(BY_ID["INT-05"], manager, {"INT-04": manager})
    assert FailureType.INFERENCE not in {f.type for f in found}  # "manager" is not "man"


@pytest.mark.req("REC1-09")
def test_a_counterfactual_pair_compares_the_unambiguous_fields_and_needs_both_arms() -> None:
    first, second = BY_ID["INT-04"], BY_ID["INT-05"]
    base = [change("current_role", "Payroll officer"), change("weekly_study_hours", 6.0)]
    judgement = [*base, change("enjoyed_tasks", ["something more hands-on"])]
    dropped = [change("current_role", "Payroll officer")]

    same = evaluate(first, turn(base), {"INT-05": turn(judgement)})
    differs = evaluate(first, turn(base), {"INT-05": turn(dropped)})
    unseen = evaluate(second, turn(base), {})

    assert same == []  # a judgement-call field is not a demographic effect
    assert FailureType.COUNTERFACTUAL in {f.type for f in differs}
    assert [f.type for f in unseen] == [FailureType.COUNTERFACTUAL]  # missing is never a pass


def slate(*suggestions: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "suggestions": list(suggestions),
        "not_included": [],
        "family_limit": 2,
        "target_size": 6,
        "fewer_reasons": [],
        "notes": [],
        "pool_size": 60,
        "pool_target": [60, 120],
        "queries": [],
        "ambiguous_titles": [],
        "salary_floor": None,
        "title_ideas": [],
        **extra,
    }


# The slate's facts (Task 6d slice A): what each search or match did, as the API serves them.
def found_none(answer: str) -> dict[str, Any]:
    return {"reason": "answer_found_no_work", "outcome": "found_none", "answer": answer}


def small_pool(size: int) -> dict[str, Any]:
    return {"reason": "small_pool", "outcome": "found_work", "pool_size": size, "pool_target": 60}


def few_matched(count: int) -> dict[str, Any]:
    return {"reason": "few_matched", "count": count}


def suggestion(title: str, family: str, direction: str, **extra: Any) -> dict[str, Any]:
    return {
        "concept_id": title,
        "concept_kind": "esco",
        "title": title,
        "family": {"code": family, "label": family},
        "direction": direction,
        "sources": [{"kind": "esco", "uri": f"http://data.europa.eu/esco/occupation/{title}"}],
        "linked_evidence": [{"field": "enjoyed_tasks", "text": "repairing physical objects"}],
        "reasons": [],
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
        title_ideas=[
            {
                "title": "Bicycle mechanic",
                "reason": "not_yet_found",
                "outcome": "not_matched",
                "occupations": 0,
            }
        ],
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


@pytest.mark.req("TEST1-15", "DIV1-04")
def test_a_title_idea_s_reason_must_be_what_careerwright_did_with_it() -> None:
    # Task 6d slice B fix round 1, app review M-8: the failure path of `title_idea_reasons`.
    dsc20 = BY_ID["DSC-20"]

    def idea(title: str, reason: str) -> dict[str, Any]:
        matched = reason == "in_esco"
        return {
            "title": title,
            "reason": reason,
            "outcome": "matched" if matched else "not_matched",
            "occupations": 1 if matched else 0,
        }

    analyst = suggestion(
        "data analyst",
        "251",
        "close_to_current",
        linked_evidence=[{"field": "enjoyed_tasks", "text": "analysing data"}],
    )
    right = [
        idea("data analyst", "in_esco"),
        idea("Prompt engineer", "in_uk_title_index"),
        idea("Orbital gardener", "not_yet_found"),
    ]
    # "Prompt engineer" said to be not yet found, though the UK job-title index lists it.
    wrong = [*right[:1], idea("Prompt engineer", "not_yet_found"), right[2]]
    # An idea the case never had is not what Careerwright did with the case's ideas either.
    extra = [*right, idea("Wind whisperer", "not_yet_found")]

    assert evaluate(dsc20, slate(analyst, title_ideas=right), {}) == []
    for ideas in (wrong, extra, right[:2]):
        failed = evaluate(dsc20, slate(analyst, title_ideas=ideas), {})
        assert [f.type for f in failed] == [FailureType.UNSUPPORTED_TITLE], ideas


def searched(query: str, skill: str) -> dict[str, Any]:
    return {
        "reason": "searched_through_skill",
        "outcome": "found_work",
        "field": "enjoyed_tasks",
        "answer": "repairing physical objects",
        "search": query,
        "skill": skill,
    }


@pytest.mark.req("DIV1-08", "TEST1-10")
def test_a_search_must_reach_work_through_an_essential_skill_that_holds_all_its_words() -> None:
    # Task W2B fix round 1: never a title, hidden label, ISCO group or description. Fix round
    # 2: every content word of the search, never one shared word ("people", "give", "write"),
    # which is the keyword matching the product owner rejected.
    p02 = BY_ID["DSC-01"]
    essential = {
        "bicycle mechanic": ["perform repairs on bicycles", "tune bicycles", "entertain people"]
    }

    def found(*why: dict[str, Any]) -> dict[str, Any]:
        return slate(
            suggestion("bicycle mechanic", "723", "less_familiar", reasons=list(why)),
            suggestion("tree surgeon", "621", "less_familiar"),
            suggestion("groundsperson", "921", "less_familiar"),
            essential_skills=essential,
        )

    through_skill = found(searched("repairing bicycles", "perform repairs on bicycles"))
    function_words = found(searched("repairing the bicycles", "perform repairs on bicycles"))
    one_word = found(searched("repairing physical objects", "perform repairs on bicycles"))
    one_shared = found(searched("looking after people", "entertain people"))
    other_skill = found(searched("repairing bicycles", "repair engines"))
    other_words = found(searched("repairing physical objects", "tune bicycles"))
    # A fact naming no essential skill of the work (its record matched instead).
    description = found(searched("repairing physical objects", "ESCO's record for this work"))

    assert evaluate(p02, through_skill, {}) == []
    assert evaluate(p02, function_words, {}) == []
    for loose in (one_word, one_shared, other_skill, other_words, description):
        assert [f.type for f in evaluate(p02, loose, {})] == [FailureType.GROUNDING]


@pytest.mark.req("REC1-03", "TEST1-10")
def test_no_search_may_rest_on_a_one_word_answer_about_how_the_person_likes_to_work() -> None:
    # Task W2B fix round 2: "structured" found soil structure and wood elements in structures.
    # Fix round 3: a longer answer ("working outdoors") is searched like any other.
    p01 = BY_ID["DSC-12"]
    style = {"field": "work_style", "text": "structured"}
    longer = {"field": "work_style", "text": "working outdoors"}
    task = {"field": "enjoyed_tasks", "text": "finding inconsistencies"}

    def ran(*based_on: dict[str, str]) -> dict[str, Any]:
        query = {"text": "structured", "based_on": list(based_on), "hits": 3}
        return slate(
            queries=[query],
            unmatched_titles=["Data quality analyst"],
            fewer_reasons=[few_matched(0)],
        )

    assert evaluate(p01, ran(task, style), {}) == []  # a task with it: the task's search
    assert evaluate(p01, ran(longer), {}) == []
    assert [f.type for f in evaluate(p01, ran(style), {})] == [FailureType.GROUNDING]


@pytest.mark.req("DIV1-06", "TEST1-10")
def test_an_answer_whose_every_search_found_nothing_must_be_named() -> None:
    # Task W2B re-review 2, N-I1: P02's slate never said "repairing physical objects" found
    # nothing. One that found work must never be named as having found none.
    p02 = BY_ID["DSC-01"]
    six = [suggestion(f"o{n}", f"{n}21", "less_familiar") for n in range(1, 7)]
    repairing = {"field": "enjoyed_tasks", "text": "repairing physical objects"}
    outdoors = {"field": "enjoyed_tasks", "text": "working outdoors"}
    reports = {"field": "enjoyed_tasks", "text": "writing reports"}

    def query(query_id: str, text: str, answer: dict[str, str], reach: int) -> dict[str, Any]:
        return {"query_id": query_id, "text": text, "based_on": [answer], "reach": reach}

    queries = [
        query("q1", "repairing physical objects", repairing, 0),
        query("q2", "fixing machines", repairing, 0),
        query("q3", "working outdoors", outdoors, 12),
        # Too general to find work alone, it added weight nowhere (no hits kept), but it
        # found work, so it is never "found no work".
        {**query("q5", "writing reports", reports, 217), "hits": 0},
    ]
    missed = found_none("repairing physical objects")
    pool = small_pool(12)

    def shown(
        *notes: dict[str, Any], reach: int = 0, more: tuple[dict[str, Any], ...] = ()
    ) -> dict[str, Any]:
        found = [*queries, query("q4", "fixing machines", repairing, reach), *more]
        return slate(*six, pool_size=12, queries=found, notes=[*notes, pool])

    wrongly = found_none("working outdoors")
    assert evaluate(p02, shown(missed), {}) == []
    assert [f.type for f in evaluate(p02, shown(), {})] == [FailureType.THIN_EVIDENCE]
    assert [f.type for f in evaluate(p02, shown(missed, wrongly), {})] == [
        FailureType.THIN_EVIDENCE
    ]
    # Named only when every search resting on it found nothing.
    assert [f.type for f in evaluate(p02, shown(missed, reach=2), {})] == [
        FailureType.THIN_EVIDENCE
    ]
    assert evaluate(p02, shown(reach=2), {}) == []
    # Task W2B re-review 3, M2: a one-word work style a model searched beside a task keeps
    # its own note, never "found no work".
    practical = {"field": "work_style", "text": "practical"}
    beside = {**query("q6", "repair machinery", repairing, 0), "based_on": [repairing, practical]}
    style = {"reason": "one_word_work_style", "outcome": "not_searched", "answers": ["practical"]}
    assert evaluate(p02, shown(missed, style, more=(beside,)), {}) == []
    # Re-review 4, M3: naming that style as "found no work" is the bug round 4 fixed, so the
    # check must catch it.
    named = found_none("practical")
    assert [f.type for f in evaluate(p02, shown(missed, named, more=(beside,)), {})] == [
        FailureType.THIN_EVIDENCE
    ]


@pytest.mark.req("DIV1-06", "DIV1-08", "TEST1-10")
def test_a_search_too_general_to_find_work_alone_may_only_add_weight_and_is_named() -> None:
    # Task W2B re-review 2, N-I2: "writing reports" alone offered an ambulance driver, a
    # chiropractor and a city councillor.
    case = BY_ID["DSC-19"]
    children = {"field": "enjoyed_tasks", "text": "caring for children"}
    reports = {"field": "enjoyed_tasks", "text": "writing reports"}
    queries = [
        {"query_id": "q1", "text": "caring for children", "based_on": [children], "hits": 16,
         "too_general": False},
        {"query_id": "q2", "text": "writing reports", "based_on": [reports], "hits": 120,
         "too_general": True},
    ]  # fmt: skip
    note = {"reason": "too_general", "outcome": "found_none", "search": "writing reports"}
    reason = {"pool_size": 16, "fewer_reasons": [few_matched(2)]}

    def found(title: str, *matched: str) -> dict[str, Any]:
        evidence = [children if q == "q1" else reports for q in matched]
        return suggestion(
            title, "531", "less_familiar", matched_queries=list(matched), linked_evidence=evidence
        )

    def shown(first: dict[str, Any], notes: list[dict[str, Any]]) -> dict[str, Any]:
        return slate(first, found("nanny", "q1"), queries=queries, notes=notes, **reason)

    both = shown(found("child care worker", "q1", "q2"), [note])
    alone = shown(found("chiropractor", "q2"), [note])
    silent = shown(found("child care worker", "q1", "q2"), [])

    assert evaluate(case, both, {}) == []
    assert [f.type for f in evaluate(case, alone, {})] == [FailureType.GROUNDING]
    assert [f.type for f in evaluate(case, silent, {})] == [FailureType.GROUNDING]


@pytest.mark.req("DIV1-03", "DIV1-12", "TEST1-10")
def test_a_title_several_occupations_hold_must_wait_for_the_person_s_choice() -> None:
    # Task W2B fix round 2: never joined over the occupations' skills together.
    case = BY_ID["DSC-16"]
    answer = {"field": "current_role", "answer": "bus operator"}
    named = {"reason": "own_title_matched", "outcome": "matched", **answer}
    joined = {"reason": "joined_by_shared_skills", "outcome": "found_work", "shared": 14, **answer}
    reason = [
        {
            "reason": "title_matched_several",
            "outcome": "matched_several",
            "title": "bus operator",
            "occupations": 2,
        }
    ]
    role = [{"field": "current_role", "text": "bus operator"}]

    def found(title: str, family: str, direction: str, why: dict[str, Any]) -> dict[str, Any]:
        return suggestion(title, family, direction, reasons=[why], linked_evidence=role)

    def shown(why: dict[str, Any], ambiguous: list[str]) -> dict[str, Any]:
        return slate(
            found("bus driver", "833", "close_to_current", named),
            found("taxi driver", "832", "transferable", why),
            ambiguous_titles=ambiguous,
            fewer_reasons=reason,
        )

    waiting = slate(
        found("bus driver", "833", "close_to_current", named),
        ambiguous_titles=["bus operator"],
        fewer_reasons=reason,
    )

    assert evaluate(case, waiting, {}) == []
    assert [f.type for f in evaluate(case, shown(joined, ["bus operator"]), {})] == [
        FailureType.GROUNDING
    ]
    assert [f.type for f in evaluate(case, shown(named, []), {})] == [FailureType.GROUNDING]


@pytest.mark.req("DIV1-02", "TEST1-10")
def test_a_pool_below_its_soft_target_must_say_why() -> None:
    # DIV1-02: 60-120 "where evidence permits". Below it, a full slate says how many it chose
    # from; a short slate's own reasons say why it is short.
    case = BY_ID["DSC-01"]
    six = [suggestion(f"o{n}", f"{n}21", "less_familiar") for n in range(1, 7)]
    said = slate(*six, pool_size=12, notes=[small_pool(12)])
    silent = slate(*six, pool_size=12)
    short = slate(*six[:3], pool_size=3, fewer_reasons=[few_matched(3)])

    assert evaluate(case, said, {}) == []
    assert evaluate(case, short, {}) == []
    assert [f.type for f in evaluate(case, silent, {})] == [FailureType.THIN_EVIDENCE]


def explained(*quotations: tuple[str, str], status: str = "complete") -> dict[str, Any]:
    """A slate of one suggestion, its explanation (one claim) and ESCO's record of it."""
    shown = suggestion(
        "bicycle mechanic",
        "723",
        "less_familiar",
        reasons=[searched("repairing bicycles", "perform repairs on bicycles")],
    )
    written = {
        "suggestions": [
            {
                "concept_id": "bicycle mechanic",
                "title": "bicycle mechanic",
                "claims": [
                    {
                        "text": "You enjoy repairs, and this work repairs bicycles.",
                        "quotations": [{"source": s, "text": t} for s, t in quotations],
                    }
                ],
            }
        ]
    }
    return {
        "slate": slate(shown),
        "explanation": {
            "run": {"status": status},
            "written": written if status == "complete" else None,
        },
        "records": {"bicycle mechanic": ["bicycle mechanic", "Mechanics repair bicycles."]},
    }


@pytest.mark.req("REC1-11", "TEST1-10")
def test_the_explanation_checks_name_the_failure_they_find() -> None:
    p02 = BY_ID["EXP-01"]
    good = explained(("answer", "repairing physical objects"), ("esco", "repair bicycles"))
    misquoted = explained(("answer", "repairing physical objects"), ("esco", "repairs bikes"))
    one_sided = explained(("esco", "repair bicycles"))
    failed = explained(status="failed")

    assert evaluate(p02, good, {}) == []
    assert [f.type for f in evaluate(p02, misquoted, {})] == [FailureType.GROUNDING]
    assert [f.type for f in evaluate(p02, one_sided, {})] == [FailureType.GROUNDING]
    # A failed explanation fails every check but the deterministic provenance, which stays.
    assert failures_by_type({"failed": evaluate(p02, failed, {})}) == {"schema_invalid": 4}
