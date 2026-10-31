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
        "why_it_could_suit": [],
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


def searched(query: str, skill: str) -> str:
    return (
        f"What you enjoy: “repairing physical objects”. Careerwright searched for “{query}”, "
        f"and ESCO lists “{skill}” as an essential skill for this work."
    )


@pytest.mark.req("DIV1-08", "TEST1-10")
def test_a_search_must_reach_work_through_an_essential_skill_that_holds_all_its_words() -> None:
    # Task W2B fix round 1: never a title, hidden label, ISCO group or description. Fix round
    # 2: every content word of the search, never one shared word ("people", "give", "write"),
    # which is the keyword matching the product owner rejected.
    p02 = BY_ID["DSC-01"]
    essential = {
        "bicycle mechanic": ["perform repairs on bicycles", "tune bicycles", "entertain people"]
    }

    def found(*why: str) -> dict[str, Any]:
        return slate(
            suggestion("bicycle mechanic", "723", "less_familiar", why_it_could_suit=list(why)),
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
    description = found(
        "What you enjoy: “repairing physical objects”. Careerwright searched for “repairing "
        "physical objects”, and ESCO's record for this occupation matched."
    )

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
            queries=[query], unmatched_titles=["Data quality analyst"], fewer_reasons=["x"]
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
    nowhere = "No main name of a skill ESCO lists as essential holds all the words of"
    missed = f"{nowhere} “repairing physical objects”, so it found no work."
    pool = "Careerwright chose these from 12 occupations."

    def shown(*notes: str, reach: int = 0, more: tuple[dict[str, Any], ...] = ()) -> dict[str, Any]:
        found = [*queries, query("q4", "fixing machines", repairing, reach), *more]
        return slate(*six, pool_size=12, queries=found, notes=[*notes, pool])

    wrongly = f"{nowhere} “working outdoors”, so it found no work."
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
    style = "How you like to work (“practical”) isn't searched on its own."
    assert evaluate(p02, shown(missed, style, more=(beside,)), {}) == []
    # Re-review 4, M3: naming that style as "found no work" is the bug round 4 fixed, so the
    # check must catch it.
    named = (
        "“Practical” found no work: no main name of a skill ESCO lists as essential holds all "
        "the words of its search “repair machinery”."
    )
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
    note = (
        "“Writing reports” reached 217 occupations in ESCO through the main names of their "
        "essential skills, too many to choose from on its own."
    )
    reason = {"pool_size": 16, "fewer_reasons": ["Only 2 occupations matched."]}

    def found(title: str, *matched: str) -> dict[str, Any]:
        evidence = [children if q == "q1" else reports for q in matched]
        return suggestion(
            title, "531", "less_familiar", matched_queries=list(matched), linked_evidence=evidence
        )

    def shown(first: dict[str, Any], notes: list[str]) -> dict[str, Any]:
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
    named = "Your current role: “bus operator”. Careerwright matched it to this occupation in ESCO."
    joined = (
        "Your current role: “bus operator”. ESCO lists 14 of the same essential skills for "
        "both, so Careerwright joined them by those skills."
    )
    reason = ["Careerwright matched “bus operator” to 2 occupations in ESCO."]
    role = [{"field": "current_role", "text": "bus operator"}]

    def found(title: str, family: str, direction: str, why: str) -> dict[str, Any]:
        return suggestion(title, family, direction, why_it_could_suit=[why], linked_evidence=role)

    def shown(why: str, ambiguous: list[str]) -> dict[str, Any]:
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
    said = slate(*six, pool_size=12, notes=["Careerwright chose these from 12 occupations."])
    silent = slate(*six, pool_size=12)
    short = slate(*six[:3], pool_size=3, fewer_reasons=["Only 3 occupations matched."])

    assert evaluate(case, said, {}) == []
    assert evaluate(case, short, {}) == []
    assert [f.type for f in evaluate(case, silent, {})] == [FailureType.THIN_EVIDENCE]


def explained(*quotations: tuple[str, str], status: str = "complete") -> dict[str, Any]:
    """A slate of one suggestion, its explanation (one claim) and ESCO's record of it."""
    shown = suggestion("bicycle mechanic", "723", "less_familiar", why_it_could_suit=["Found"])
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
