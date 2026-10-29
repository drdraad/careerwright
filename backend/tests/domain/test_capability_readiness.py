"""Readiness, gaps and the abstract action graph (RDY-1, OUT-1, spec section 9; S4.2, S4.5,
S4.6): on the M0 fixtures (TRACE-01, P04, P05; synthetic) and on the option pack's real
records, which are all proposed (ADR 0012)."""

import uuid
from datetime import UTC, date, datetime

import pytest

from nessa.capability.evidence import Holding, row_evidence
from nessa.capability.matrix import (
    Importance,
    Matrix,
    RowEdit,
    apply_edits,
    build_matrix,
    check_edit,
)
from nessa.capability.outcomes import (
    Confidence,
    EvidenceKind,
    OutcomeReview,
    OutcomeType,
    PlannedOutcome,
    Provenance,
    accept,
    pack_outcomes,
    user_override,
)
from nessa.capability.readiness import (
    Assessment,
    GapKind,
    PrimaryAction,
    Qualification,
    ReadinessState,
    RowStatus,
    assess,
    ensure_current,
)
from nessa.capability.reference import load_reference
from nessa.catalogue.option_pack import load_pack
from nessa.errors import ErrorCode, NessaError
from tests.support.capability import (
    ADA,
    assessed,
    fixture,
    gate_row,
    self_report,
    skill_row,
    statement,
    synthetic_matrix,
    trace_evidence,
    trace_matrix,
    trace_outcomes,
)

PACK = load_pack("0.1.0")
REFERENCE = load_reference("0.1.0", PACK)
OUTCOMES = pack_outcomes(PACK, REFERENCE)
NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
RUBRIC = "fixture-rubric-1"


def pack_matrix(target_id: str) -> Matrix:
    target = next(t for t in PACK.targets if t.target_id == target_id)
    return build_matrix(
        target.title,
        pack=PACK,
        reference=REFERENCE,
        pack_target=target,
        occupation=None,
        exemplars=0,
    )


def rubric_of(matrix: Matrix, row_id: str) -> str:
    row = matrix.row(row_id)
    assert row is not None
    assert row.rubric is not None
    return row.rubric.version_id


def subject_of(matrix: Matrix, row_id: str) -> str:
    row = matrix.row(row_id)
    assert row is not None
    return row.subject


def status(assessment: Assessment, row_id: str) -> RowStatus:
    return next(r.status for r in assessment.rows if r.row_id == row_id)


@pytest.mark.req("RDY1-01", "READINESS-01")
def test_readiness_needs_every_required_row_and_gate_and_unknown_never_passes() -> None:
    gate = gate_row("fixture:registration")
    matrix = synthetic_matrix("Synthetic", [skill_row("fixture:a", 2, RUBRIC), gate])
    met = [self_report("fixture:a", 2, RUBRIC)]
    verified = [statement(gate.subject, Holding.HELD, verified=True)]

    ready = assess(matrix, evidence=met, statements=verified, outcomes=[], evidence_version=1)
    unknown = assess(matrix, evidence=[], statements=verified, outcomes=[], evidence_version=1)
    zero = assess(
        matrix,
        evidence=[self_report("fixture:a", 0, RUBRIC)],
        statements=verified,
        outcomes=[],
        evidence_version=1,
    )
    gate_open = assess(matrix, evidence=met, statements=[], outcomes=[], evidence_version=1)

    assert ready.state is ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS
    assert unknown.state is ReadinessState.NOT_READY
    # Unknown is not level 0: no evidence and "level 0" are different findings.
    assert status(unknown, "fixture:a") is RowStatus.NO_USABLE_EVIDENCE
    assert status(zero, "fixture:a") is RowStatus.BELOW_REQUIRED
    assert next(r for r in zero.rows if r.row_id == "fixture:a").evidence.level == 0  # type: ignore[union-attr]
    assert next(r for r in unknown.rows if r.row_id == "fixture:a").evidence.level is None  # type: ignore[union-attr]
    assert gate_open.state is ReadinessState.NOT_READY
    assert [b.kind for b in gate_open.blockers] == [RowStatus.UNRESOLVED]


@pytest.mark.req("RDY1-03", "READINESS-03")
def test_p05_leads_with_apply_now_and_no_forced_training() -> None:
    p05 = fixture("personas/P05.json")
    rows = [skill_row(s["skill_id"], s["required"], RUBRIC) for s in p05["skills"]]
    evidence = [self_report(s["skill_id"], s["evidenced"], RUBRIC) for s in p05["skills"]]
    matrix = synthetic_matrix("Bookkeeping assistant", rows)

    result = assess(matrix, evidence=evidence, statements=[], outcomes=[], evidence_version=3)

    expected = p05["expected"]
    assert result.state.value == expected["state"].lower()
    assert result.primary_action.value == expected["primary_action"]
    assert result.training_required is expected["forced_training"]
    assert result.show_route_chart is expected["show_degenerate_pareto_chart"]
    assert [a.kind for a in result.actions][:1] == ["review_postings_and_apply"]
    # Evidence recency and the matrix's provisional status come with the lead.
    assert all(r.evidence is not None and r.evidence.last_done == "2026-09" for r in result.rows)
    assert Qualification.PROVISIONAL_MATRIX in result.qualifications
    assert Qualification.SELF_REPORTED_EVIDENCE in result.qualifications


@pytest.mark.req("RDY1-03", "OPTN-09")
def test_apply_now_on_the_pack_is_qualified_and_lists_employer_checks() -> None:
    matrix = pack_matrix("bookkeeping-assistant-leeds")
    reconciliation = "pack:bookkeeping-assistant-leeds:reconciliation"
    records = "pack:bookkeeping-assistant-leeds:records"
    evidence = [
        self_report(subject_of(matrix, row), 2, rubric_of(matrix, row))
        for row in (reconciliation, records)
    ]
    work = [statement("gate:uk-right-to-work", Holding.HELD, verified=True)]

    result = assess(
        matrix, evidence=evidence, statements=work, outcomes=OUTCOMES, evidence_version=1
    )

    assert result.state is ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS
    assert result.primary_action is PrimaryAction.REVIEW_CURRENT_POSTINGS_AND_APPLY
    # Every pack record is proposed (0.1.0), so this result is never unqualified (R9).
    assert Qualification.PROPOSED_RECORDS in result.qualifications
    assert Qualification.PROPOSED_RUBRICS in result.qualifications
    checks = {c.requirement_id for c in result.employer_checks}
    assert {"req:J04.1", "req:J08.1", "req:J08.3"} <= checks  # postings' own essentials
    assert "req:J04.3" not in checks  # a preferred criterion is not a check to pass


@pytest.mark.req("OPTN-09")
def test_only_reviewed_records_lift_the_proposed_qualification() -> None:
    row = skill_row("fixture:a", 2, RUBRIC).model_copy(update={"review_state": "reviewed"})
    matrix = synthetic_matrix("Synthetic", [row])

    result = assess(
        matrix,
        evidence=[self_report("fixture:a", 2, RUBRIC)],
        statements=[],
        outcomes=[],
        evidence_version=1,
    )

    assert Qualification.PROPOSED_RECORDS not in result.qualifications
    assert Qualification.PROVISIONAL_MATRIX in result.qualifications  # M0 matrices stay so


@pytest.mark.req("RDY1-04", "MAP1-05", "READINESS-04")
def test_p04_cannot_become_ready_by_demoting_registration() -> None:
    p04 = fixture("personas/P04.json")
    gate = gate_row(p04["regulatory_gate"]["id"])
    matrix = synthetic_matrix("Registered nurse", [gate])
    edit = p04["requested_edit"]

    with pytest.raises(NessaError) as refused:
        check_edit(
            matrix,
            edit["gate_id"],
            Importance.ESSENTIAL if edit["essential"] else Importance.PREFERRED,
            warning_acknowledged=True,
        )
    # A stored edit that somehow names the gate still cannot demote it.
    demoted = apply_edits(
        matrix,
        [
            RowEdit(
                edit_id=uuid.uuid4(),
                row_id=gate.row_id,
                action="set_importance",
                importance=Importance.PREFERRED,
                reason="I would like to skip it",
                warning_acknowledged=True,
                recorded_by=ADA,
                recorded_at=NOW,
                from_matrix_version=matrix.matrix_version,
                from_definition_version=matrix.definition_version,
            )
        ],
    )
    unverified = assess(
        demoted,
        evidence=[],
        statements=[statement(gate.subject, Holding.HELD, verified=False)],
        outcomes=[],
        evidence_version=1,
    )

    assert refused.value.code is ErrorCode.PROTECTED_GATE
    assert demoted.definition_version == matrix.definition_version
    assert unverified.state is ReadinessState.NOT_READY
    # Unverified is unresolved, never ineligible: no such finding exists.
    assert status(unverified, gate.row_id) is RowStatus.UNRESOLVED
    assert "ineligible" not in unverified.model_dump_json()
    assert [g.kind for g in unverified.gaps] == [GapKind.INFORMATION]


@pytest.mark.req("BND1-08", "RDY1-04", "OUT1-06")
def test_a_registration_pathway_longer_than_the_model_is_outside_it_not_impossible() -> None:
    matrix = pack_matrix("registered-nurse-manchester")
    gate = "pack:registered-nurse-manchester:nmc-registration"
    not_held = [statement("gate:nmc-registration", Holding.NOT_HELD)]

    result = assess(matrix, evidence=[], statements=not_held, outcomes=OUTCOMES, evidence_version=1)

    assert {b.kind for b in result.blockers if b.row_id == gate} == {
        RowStatus.NOT_HELD,
        RowStatus.PATHWAY_OUTSIDE_MODEL,
    }
    [action] = [a for a in result.actions if gate in a.rows]
    assert action.kind == "obtain_credential"
    assert action.state == "outside_planning_model"
    assert action.code is ErrorCode.MODEL_SCOPE_EXCEEDED
    by_option = {c.option_id: c for c in action.candidates}
    # C08's degree leads to eligibility to register, over 3 years: beyond 24 months.
    assert by_option["option:C08"].addresses
    assert by_option["option:C08"].outside_planning_model
    assert by_option["option:C08"].months_minimum == 36
    # C03's "Adult Nursing" title has no formal qualification: it never addresses the gate.
    assert not by_option["option:C03"].addresses


@pytest.mark.req("OUT1-06", "PLN-04")
def test_no_course_ever_satisfies_a_statutory_gate_or_manufactures_a_licence() -> None:
    matrix = pack_matrix("registered-nurse-manchester")
    gate = "pack:registered-nurse-manchester:nmc-registration"
    c08 = next(o for o in OUTCOMES if o.outcome_id == "outcome:C08.1")
    accepted = [accept(o, by=ADA, at=NOW) for o in OUTCOMES if o.skill_id == gate]

    result = assess(
        matrix,
        evidence=[],
        statements=[statement("gate:nmc-registration", Holding.NOT_HELD)],
        outcomes=accepted,
        evidence_version=1,
        completed=frozenset({"offering:C08", "offering:C03"}),
    )

    assert c08.outcome_type is OutcomeType.CREDENTIAL
    assert c08.credential is not None
    assert c08.credential.gate_key == "nmc-registration"
    assert c08.credential.leads_to == "eligibility_to_apply"
    assert c08.level_on_completion is None
    assert status(result, gate) is RowStatus.NOT_HELD
    assert result.state is ReadinessState.NOT_READY
    with pytest.raises(ValueError, match="never has a level"):
        PlannedOutcome.model_validate({**c08.model_dump(), "level_on_completion": 2})


@pytest.mark.req("RDY1-02", "READINESS-02", "OUT1-04")
def test_planned_outcomes_count_only_in_a_conditional_scenario() -> None:
    matrix = trace_matrix()
    evidence = trace_evidence()
    outcomes = trace_outcomes()

    current = assess(
        matrix, evidence=evidence, statements=[], outcomes=outcomes, evidence_version=1
    )
    conditional = assess(
        matrix,
        evidence=evidence,
        statements=[],
        outcomes=outcomes,
        evidence_version=1,
        completed=frozenset({outcomes[0].offering_id}),
    )

    assert current.state is ReadinessState.NOT_READY
    assert conditional.state is ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION
    assert conditional.scenario == "conditional"
    assert Qualification.PLANNED_OUTCOME_ASSUMPTION in conditional.qualifications
    query = next(r for r in conditional.rows if r.row_id == "fixture:query-data")
    assert query.evidence is not None
    assert query.evidence.level == 1
    assert query.planned_level == 2


@pytest.mark.req("TRACE01-06", "OUT1-05")
def test_enrolment_or_completion_never_overwrites_current_evidence() -> None:
    matrix = trace_matrix()
    evidence = trace_evidence()
    outcome = trace_outcomes()[0]

    completed = assess(
        matrix,
        evidence=evidence,
        statements=[],
        outcomes=trace_outcomes(),
        evidence_version=1,
        completed=frozenset({outcome.offering_id}),
    )
    unreviewed = [
        *evidence,
        assessed("fixture:query-data", 2, RUBRIC, outcome_id=outcome.outcome_id),
    ]
    reviewed = [
        *evidence,
        assessed(
            "fixture:query-data",
            2,
            RUBRIC,
            outcome_id=outcome.outcome_id,
            reviewed_on=date(2027, 3, 1),
        ),
    ]

    assert row_evidence("fixture:query-data", RUBRIC, evidence).level == 1
    # The completed course leaves the person's evidence as it was.
    assert next(r for r in completed.rows if r.row_id == "fixture:query-data").evidence.level == 1  # type: ignore[union-attr]
    # An assessed completion counts only once its evidence is reviewed.
    assert row_evidence("fixture:query-data", RUBRIC, unreviewed).level == 1
    assert row_evidence("fixture:query-data", "fixture-rubric-1", reviewed).level == 2
    assert row_evidence("fixture:validate-data", RUBRIC, reviewed).level == 1


@pytest.mark.req("OUT1-07")
def test_two_introductory_courses_never_add_up_to_competence() -> None:
    matrix = trace_matrix()
    intro = trace_outcomes()[0]
    first, second = (
        intro.model_copy(
            update={
                "outcome_id": f"intro-{n}",
                "offering_id": f"offering-{n}",
                "evidence_kind": EvidenceKind.EXAM,
                "level_on_completion": 1,
            }
        )
        for n in (1, 2)
    )

    result = assess(
        matrix,
        evidence=[],
        statements=[],
        outcomes=[first, second],
        evidence_version=1,
        completed=frozenset({"offering-1", "offering-2"}),
    )

    query = next(r for r in result.rows if r.row_id == "fixture:query-data")
    assert query.planned_level == 1  # ordinal levels are never added
    assert query.status is RowStatus.BELOW_REQUIRED


@pytest.mark.req("OUT1-07", "OUT1-02")
def test_topic_mentions_and_practice_in_the_pack_add_no_level_even_together() -> None:
    matrix = pack_matrix("data-quality-analyst-manchester")
    querying = "pack:data-quality-analyst-manchester:independent-querying"
    # C01 mentions SQL as a topic; C04 names SQL project work without assessing it.
    both = [accept(o, by=ADA, at=NOW) for o in OUTCOMES if o.skill_id == querying]

    result = assess(
        matrix,
        evidence=[self_report(subject_of(matrix, querying), 1, rubric_of(matrix, querying))],
        statements=[],
        outcomes=both,
        evidence_version=1,
        completed=frozenset(o.offering_id for o in both),
    )

    assert {o.option_id for o in both} == {"option:C01", "option:C04"}
    row = next(r for r in result.rows if r.row_id == querying)
    assert row.planned_level is None
    assert row.status is RowStatus.BELOW_REQUIRED


@pytest.mark.req("OUT1-02", "OUT1-04", "OUT1-10")
def test_an_unsupported_outcome_level_stays_null_and_leaves_a_partial_sketch() -> None:
    # Every planned outcome in pack 0.1.0 is null: topic mentions and unsupported ones must
    # be, and no stated assessment supports a rubric anchor.
    assert len(OUTCOMES) == 18
    assert all(o.level_on_completion is None for o in OUTCOMES)
    unsupported = next(o for o in OUTCOMES if o.confidence is Confidence.UNSUPPORTED)
    for kind in (EvidenceKind.TOPIC_MENTION, EvidenceKind.PRACTICE):
        with pytest.raises(ValueError, match="assessed"):
            PlannedOutcome.model_validate(
                {
                    **unsupported.model_dump(),
                    "evidence_kind": kind,
                    "confidence": "provisional",
                    "level_on_completion": 2,
                    "rubric_version": "r",
                }
            )
    with pytest.raises(ValueError, match="unsupported"):
        PlannedOutcome.model_validate(
            {
                **unsupported.model_dump(),
                "evidence_kind": "exam",
                "level_on_completion": 2,
                "rubric_version": "r",
            }
        )

    matrix = pack_matrix("data-quality-analyst-manchester")
    below = [
        self_report(r.subject, 1, r.rubric.version_id) for r in matrix.rows if r.rubric is not None
    ]
    result = assess(matrix, evidence=below, statements=[], outcomes=OUTCOMES, evidence_version=1)
    candidates = [c for a in result.actions for c in a.candidates]
    assert {g.kind for g in result.gaps} == {GapKind.LEARN}
    assert {c.option_id for c in candidates} == {"option:C01", "option:C04"}
    assert all(c.numeric_use == "excluded_missing_level" for c in candidates)


@pytest.mark.req("ASSESS-06")
def test_no_course_is_offered_before_the_person_has_said_where_they_are() -> None:
    matrix = pack_matrix("data-quality-analyst-manchester")

    result = assess(matrix, evidence=[], statements=[], outcomes=OUTCOMES, evidence_version=1)

    assert {g.kind for g in result.gaps} == {GapKind.INFORMATION}
    assert all(a.kind == "verify" and a.candidates == [] for a in result.actions)


@pytest.mark.req("OUT1-01")
def test_a_pack_outcome_carries_the_out_1_record() -> None:
    outcome = next(o for o in OUTCOMES if o.outcome_id == "outcome:C06.1")

    assert outcome.skill_id == "pack:bookkeeping-assistant-leeds:records"
    assert outcome.evidence_kind is EvidenceKind.EXAM
    assert outcome.confidence is Confidence.PROVISIONAL
    assert outcome.claim_state == "planned_conditional"
    assert outcome.review_state is OutcomeReview.PROPOSED
    assert outcome.provenance is Provenance.PROVIDER_CLAIM
    span = outcome.source_span
    assert span.source_id == "C06"
    assert len(span.source_hash) == 64
    assert span.start is not None
    assert span.end is not None
    assert span.excerpt
    assert span.retrieved_at is not None
    assert span.retrieved_at.date() == date(2026, 10, 29)
    assert outcome.months_minimum == 12


@pytest.mark.req("OUT1-03")
def test_a_user_override_is_an_assumption_never_a_provider_claim() -> None:
    matrix = trace_matrix()
    provider = trace_outcomes()[0].model_copy(update={"review_state": OutcomeReview.PROPOSED})

    override = user_override(
        provider,
        evidence_kind=EvidenceKind.ASSESSED_WORK_SAMPLE,
        level_on_completion=2,
        rubric_version=RUBRIC,
        reason="The tutor told me the project is marked against these tasks",
        by=ADA,
        at=NOW,
    )
    result = assess(
        matrix,
        evidence=trace_evidence(),
        statements=[],
        outcomes=[provider, override],
        evidence_version=1,
        completed=frozenset({provider.offering_id}),
    )

    assert override.provenance is Provenance.USER_OVERRIDE
    assert override.review_state is OutcomeReview.ACCEPTED_ASSUMPTION
    assert override.overrides == provider.outcome_id
    assert override.assumption is not None
    assert override.assumption.recorded_by == ADA
    assert provider.review_state is OutcomeReview.PROPOSED  # the provider's claim unchanged
    assert Qualification.USER_ASSUMPTION in result.qualifications
    with pytest.raises(ValueError, match="reviewed"):
        PlannedOutcome.model_validate(
            {**override.model_dump(), "review_state": OutcomeReview.REVIEWED}
        )


@pytest.mark.req("ASSESS-01", "ASSESS-06")
def test_an_unsupported_claim_stays_self_reported_and_asks_for_a_small_demonstration() -> None:
    matrix = synthetic_matrix("Synthetic", [skill_row("fixture:a", 2, RUBRIC)])
    claim = self_report("fixture:a", 3, RUBRIC, example=None, last_done=None)

    result = assess(matrix, evidence=[claim], statements=[], outcomes=[], evidence_version=1)

    row = result.rows[0]
    assert row.evidence is not None
    assert (row.evidence.self_assessed_level, row.evidence.demonstrated_level) == (3, None)
    assert row.evidence.confidence is Confidence.UNSUPPORTED
    assert row.evidence.basis == "self_reported"
    assert row.status is RowStatus.NO_USABLE_EVIDENCE
    [gap] = result.gaps
    assert gap.kind is GapKind.DEMONSTRATE
    # No course for an evidence gap a small assessment could close.
    assert [a.candidates for a in result.actions] == [[]]


@pytest.mark.req("ASSESS-06")
def test_gaps_are_classified_and_work_rights_never_get_a_course() -> None:
    matrix = pack_matrix("it-support-technician-bristol")
    hardware = "pack:it-support-technician-bristol:hardware-troubleshooting"
    windows = "pack:it-support-technician-bristol:windows-m365-support"
    evidence = [
        self_report(subject_of(matrix, hardware), 1, rubric_of(matrix, hardware)),
        self_report(subject_of(matrix, windows), 2, rubric_of(matrix, windows)),
    ]
    statements = [statement("gate:uk-right-to-work", Holding.NOT_HELD)]

    result = assess(
        matrix, evidence=evidence, statements=statements, outcomes=OUTCOMES, evidence_version=1
    )

    kinds = {g.row_id: g.kind for g in result.gaps}
    assert kinds[hardware] is GapKind.LEARN
    assert windows not in kinds
    assert kinds["gate:uk-right-to-work"] is GapKind.ELIGIBILITY
    assert kinds["pack:it-support-technician-bristol:service-desk-ticketing"] is GapKind.INFORMATION
    work = next(a for a in result.actions if "gate:uk-right-to-work" in a.rows)
    assert work.kind == "resolve_eligibility"
    assert work.candidates == []
    learn = next(a for a in result.actions if hardware in a.rows)
    assert {c.option_id for c in learn.candidates} == {"option:C07", "option:C10"}


@pytest.mark.req("ASSESS-04")
def test_evidence_keeps_recency_independence_and_ai_assistance() -> None:
    evidence = [self_report("fixture:a", 2, RUBRIC, ai_assisted=True, last_done="2025-11")]

    seen = row_evidence("fixture:a", RUBRIC, evidence)

    assert seen.last_done == "2025-11"
    assert seen.independence == "independent"
    assert seen.ai_assisted is True
    assert seen.tools
    assert seen.evidence_ids == [evidence[0].evidence_id]


@pytest.mark.req("ASSESS-05")
def test_an_evidence_change_recomputes_only_the_gaps_it_affects() -> None:
    matrix = trace_matrix()
    before = trace_evidence()
    after = [*before, self_report("fixture:validate-data", 2, RUBRIC)]

    first = assess(matrix, evidence=before, statements=[], outcomes=[], evidence_version=1)
    second = assess(matrix, evidence=after, statements=[], outcomes=[], evidence_version=2)

    changed = {
        gap.row_id
        for gap in [*first.gaps, *second.gaps]
        if gap not in first.gaps or gap not in second.gaps
    }
    assert changed == {"fixture:validate-data"}
    query_before = next(g for g in first.gaps if g.row_id == "fixture:query-data")
    query_after = next(g for g in second.gaps if g.row_id == "fixture:query-data")
    assert query_before == query_after
    assert query_before.evidence_ids


def test_evidence_is_shared_across_targets_but_never_reused_for_another_rubric() -> None:
    first = skill_row("fixture:shared", 2, "rubric-a")
    other = skill_row("fixture:shared", 2, "rubric-b")
    evidence = [self_report("fixture:shared", 2, "rubric-a")]

    seen_first = row_evidence(first.subject, "rubric-a", evidence)
    seen_other = row_evidence(other.subject, "rubric-b", evidence)

    assert seen_first.level == 2
    assert seen_other.level is None
    assert seen_other.shared_from_other_rubric


@pytest.mark.req("RDY1-05", "VERSIONS-04", "MAP1-04")
def test_results_carry_their_versions_and_an_essential_edit_makes_them_stale() -> None:
    matrix = pack_matrix("data-quality-analyst-manchester")
    result = assess(matrix, evidence=[], statements=[], outcomes=OUTCOMES, evidence_version=4)
    validation = "pack:data-quality-analyst-manchester:data-validation"
    edited = apply_edits(
        matrix,
        [
            RowEdit(
                edit_id=uuid.uuid4(),
                row_id=validation,
                action="set_importance",
                importance=Importance.PREFERRED,
                reason="r",
                warning_acknowledged=True,
                recorded_by=ADA,
                recorded_at=NOW,
                from_matrix_version=matrix.matrix_version,
                from_definition_version=matrix.definition_version,
            )
        ],
    )

    assert (result.target_key, result.matrix_version, result.definition_version) == (
        matrix.target_key,
        matrix.matrix_version,
        matrix.definition_version,
    )
    assert (result.evidence_version, result.pack_version, result.reference_version) == (
        4,
        "0.1.0",
        "0.1.0",
    )
    ensure_current(result, matrix)
    with pytest.raises(NessaError) as stale:
        ensure_current(result, edited)
    assert stale.value.code is ErrorCode.STALE_INPUT_VERSION
    relaxed = assess(edited, evidence=[], statements=[], outcomes=[], evidence_version=5)
    assert {g.kind for g in relaxed.gaps if g.row_id == validation} == {GapKind.PREFERENCE_CONFLICT}
