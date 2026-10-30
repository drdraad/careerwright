"""Session 2's new question sets (Task 11; dispatch ruling 3): the TRACE-01 checker run on
P01's real option set (TEST1-14, the T questions) and the capability reference with proposed
outcome levels (the R questions). Both are exactly what `tools.session_2_files` writes, so
their numbers stay stable; Q1-Q344 are untouched."""

import re

import pytest

from careerwright.capability.reference import load_reference
from careerwright.catalogue.option_pack import PINS, load_pack, pack_path
from careerwright.planning.checker import (
    Feasibility,
    FindingCode,
    FindingKind,
    RouteQualification,
    Scenario,
    Verdict,
)
from tests.support.planning import trace_inputs
from tools import session_2_files
from tools.option_pack_files import PACKAGE_PATH, pounds
from tools.session_2_files import (
    CAPABILITY_PATH,
    CHECKER_PATH,
    capability_questions,
    checker_questions,
    limit_text,
    p01_inputs,
    p01_run,
    proposed_levels,
)

PACK = load_pack("0.1.0")
REFERENCE = load_reference("0.1.0", PACK)


def numbers(text: str, prefix: str) -> list[int]:
    return [int(n) for n in re.findall(rf"^\| {prefix}([0-9]+) \|", text, flags=re.MULTILINE)]


@pytest.mark.req("TEST1-14")
def test_the_run_uses_p01_s_trace_01_inputs_unchanged() -> None:
    assert p01_inputs() == trace_inputs()


@pytest.mark.req("TEST1-14", "OPTN-09", "FIN1-06")
def test_the_checker_runs_on_p01_s_real_option_set_and_keeps_every_unknown() -> None:
    run = p01_run()
    base = {e.route[0]: e.scenario(Scenario.BASE) for e in run.evaluations}

    assert sorted(base) == [
        "offering:C01#full_time",
        "offering:C01#part_time",
        "offering:C04~instalments",
        "offering:C04~pay-in-full",
    ]
    full = base["offering:C04~pay-in-full"]
    # £2,995 paid in full: above P01's £1,500 direct-spend cap and, in whatever month it
    # falls, above the £1,500 monthly payment cap.
    assert full.verdict is Verdict.NOT_FEASIBLE_IN_MODEL
    violations = {
        (f.code, f.amount, f.limit) for f in full.findings if f.kind is FindingKind.VIOLATION
    }
    assert violations == {
        (FindingCode.DIRECT_SPEND_CAP, 299500, 150000),
        (FindingCode.MONTHLY_PAYMENT_CAP, 299500, 150000),
    }
    for name in ("offering:C04~instalments", "offering:C01#full_time", "offering:C01#part_time"):
        result = base[name]
        assert result.feasibility is Feasibility.UNRESOLVED
        assert {FindingCode.DATES_UNKNOWN, FindingCode.COST_UNKNOWN} <= {
            f.code for f in result.findings
        }
        assert result.direct_cost is None  # unknown, never £0
        assert result.conditions == []  # C01's funding is not assumed: insufficient information
    for result in base.values():
        assert RouteQualification.PROPOSED_RECORDS in result.qualifications
        assert RouteQualification.SYNTHETIC in result.qualifications  # P01 is synthetic
        assert result.months_to_readiness is None  # a partial sketch on readiness
        assert result.verdict is not Verdict.AFFORDABLE_AND_FEASIBLE
    # No condition in this set, so every fixed scenario reads as the base one.
    for evaluation in run.evaluations:
        verdicts = {c.verdict for c in evaluation.checks}
        assert len(verdicts) == 1


@pytest.mark.req("TEST1-14", "OUT1-10")
def test_no_pack_option_counts_towards_readiness_until_its_outcome_levels_are_reviewed() -> None:
    run = p01_run()

    assert all(o.level_on_completion is None for o in PACK.outcomes)
    for evaluation in run.evaluations:
        assert evaluation.scenario(Scenario.BASE).readiness_month is None
    # The run's own readiness basis: P01's levels on the pack rows, outcomes as proposed.
    assert {o.review_state.value for o in run.readiness.outcomes} == {"proposed"}


@pytest.mark.req("TEST1-14", "TEST1-09")
def test_the_committed_checker_questions_are_the_tool_s_output() -> None:
    assert CHECKER_PATH.read_text(encoding="utf-8") == checker_questions()


@pytest.mark.req("TEST1-14")
def test_every_field_the_checker_used_is_asked_beside_its_span() -> None:
    text = checker_questions()
    cited = set(re.findall(r"\(([JCF][0-9]{2}\.[a-z0-9_.]+), (?:offsets|pointer)", text))

    assert {
        "C04.fee_total",
        "C04.instalment",
        "C04.duration",
        "C01.fee_total",
        "C01.duration",
        "C01.funding_route",
        "C01.eligibility_earnings",
    } <= cited
    assert numbers(text, "T") == list(range(1, len(numbers(text, "T")) + 1))
    assert numbers(text, "Q") == []  # its own numbering: Q1-Q344 never move
    assert "partial sketch" in text
    assert "not run - requires human" in text


@pytest.mark.req("TEST1-09", "OUT1-10")
def test_the_committed_capability_questions_are_the_tool_s_output() -> None:
    assert CAPABILITY_PATH.read_text(encoding="utf-8") == capability_questions()


@pytest.mark.req("OUT1-10", "MAP1-02")
def test_the_reference_and_every_pack_outcome_s_proposed_level_are_asked() -> None:
    text = capability_questions()

    assert numbers(text, "R") == list(range(1, len(numbers(text, "R")) + 1))
    for rubric in REFERENCE.rubrics:
        assert rubric.version_id in text
    for gate in REFERENCE.gates:
        assert gate.label in text
    for target in REFERENCE.targets:
        assert target.esco_label in text
    for outcome in PACK.outcomes:
        assert f"`{outcome.record_id}`" in text
        assert f"({outcome.source_span}, offsets" in text


@pytest.mark.req("OUT1-02", "OUT1-10")
def test_a_level_is_proposed_only_for_an_assessed_supported_skill_outcome() -> None:
    proposals = proposed_levels(PACK, REFERENCE)
    skills = {s.skill_id: s.kind for s in PACK.skills}

    assert len(proposals) == len(PACK.outcomes)
    for outcome in PACK.outcomes:
        level, why = proposals[outcome.record_id]
        assert why
        ruled_out = (
            outcome.evidence_kind in ("topic_mention", "practice")
            or outcome.confidence == "unsupported"
            or skills[outcome.skill_id] != "skill"
        )
        if ruled_out:
            assert level is None
    assert {k for k, (level, _) in proposals.items() if level is not None} == {
        "outcome:C06.1",
        "outcome:C06.2",
    }


@pytest.mark.req("OPTN-10")
def test_the_proposals_never_touch_the_frozen_pack() -> None:
    capability_questions()
    checker_questions()

    assert load_pack("0.1.0", pins=PINS).pack_version == "0.1.0"
    assert 'level_on_completion": 2' not in pack_path("0.1.0").read_text(encoding="utf-8")
    assert PACKAGE_PATH.exists()  # the Q package stays as Task 7b left it


@pytest.mark.req("TEST1-14")
def test_the_checker_questions_read_plainly() -> None:
    # Review M6: money as pounds, never JSON or minor units; words, never codes.
    text = checker_questions()

    assert "minor_units" not in text
    assert '{"' not in text
    for code in ("dates_unknown", "cost_unknown", "workload_unknown", "direct_spend_cap"):
        assert code not in text
    assert "not_ready" not in text
    assert "topic_mention" not in text
    assert "£32,400.00" in text  # C01's earnings rule
    assert not re.search(r"unknown: [^|]*: unknown", text)  # T14 said "unknown" twice
    # The partial sketch's whole reason.
    assert "no variant has dates" in text
    assert "topic mentions or practice without an assessment" in text


@pytest.mark.req("TEST1-14")
def test_an_absent_limit_reads_unknown_never_zero() -> None:
    assert limit_text(None) == "unknown"
    assert limit_text(150000) == "£1,500.00"


def test_money_is_formatted_with_whole_numbers_in_one_helper() -> None:
    # Review M11: no float division for money (Global Constraint 4), one helper for both tools.
    assert pounds(123456789012345678) == "£1,234,567,890,123,456.78"
    assert pounds(5) == "£0.05"
    assert pounds(-15000) == "-£150.00"
    assert vars(session_2_files)["pounds"] is pounds  # the session 2 tool uses the same one
