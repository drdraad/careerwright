"""The ten course pages' readiness mappings, reviewed one by one (Task 10, backend half; S4.5,
Sprint 4 acceptance: "Review false-positive readiness mappings individually; any unsupported
consequential outcome blocks publication of the affected route"; OUT-1; ADR 0012 decision 6).

Each of the option pack's planned outcomes (C01-C10, in the reviewed pack 0.2.0 and in 0.1.0,
which the app still reads) is listed below with what its page shows and why it gives no level
on completion. Then each is checked in the capability model: completing its offering, even
with the mapping accepted as the person's own assumption, never raises the row it maps to,
never satisfies a protected gate, and never makes its target ready or conditionally ready, so
a route resting on it reads "readiness not reached in this model" (the checker asks this same
`assess`). A mapping that changes in a new pack version fails here until it is reviewed again.
"""

from datetime import UTC, datetime

import pytest

from careerwright.capability.evidence import Holding, SkillEvidence
from careerwright.capability.matrix import LEVELLED_KINDS, Matrix, build_matrix
from careerwright.capability.outcomes import (
    Confidence,
    EvidenceKind,
    OutcomeReview,
    OutcomeType,
    accept,
    pack_outcomes,
)
from careerwright.capability.readiness import ReadinessState, RowStatus, assess
from careerwright.capability.reference import load_reference
from careerwright.catalogue.option_pack import load_pack
from tests.support.capability import ADA, self_report, statement

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
READY = {
    ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS,
    ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION,
}
TOPIC = EvidenceKind.TOPIC_MENTION
PRACTICE = EvidenceKind.PRACTICE
EXAM = EvidenceKind.EXAM
WORK_SAMPLE = EvidenceKind.ASSESSED_WORK_SAMPLE
UNSUPPORTED = Confidence.UNSUPPORTED
PROVISIONAL = Confidence.PROVISIONAL

# outcome ID: (evidence kind, confidence, outcome type, why it gives no level on completion)
REVIEWED: dict[str, tuple[EvidenceKind, Confidence, OutcomeType, str]] = {
    # C01 "Certificate in Data": a course page whose title promises more than its syllabus
    # shows; the topics are named, nothing is assessed.
    "outcome:C01.1": (TOPIC, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "topic named, not assessed"),
    "outcome:C01.2": (TOPIC, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "topic named, not assessed"),
    "outcome:C01.3": (PRACTICE, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "practised, not assessed"),
    # C02 "AAT Award in Bookkeeping": the units are named; no assessed level is stated.
    "outcome:C02.1": (TOPIC, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "topic named, not assessed"),
    "outcome:C02.2": (TOPIC, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "topic named, not assessed"),
    # C03 "Safeguarding Level 3 Course": "Level 3" is not a nursing qualification, and the
    # page never leads to NMC registration (a misleading title for this target).
    "outcome:C03.1": (TOPIC, UNSUPPORTED, OutcomeType.CREDENTIAL, "no route to the register"),
    # C04 "Junior Data Analyst": a course titled like a job; practice without assessment.
    "outcome:C04.1": (PRACTICE, PROVISIONAL, OutcomeType.SKILL_LEVEL, "practised, not assessed"),
    "outcome:C04.2": (PRACTICE, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "practised, not assessed"),
    # C05 "Accounting (AAT Diploma, Level 3)": examined, but the page does not support the
    # mapping to this row.
    "outcome:C05.1": (EXAM, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "assessed, mapping unsupported"),
    # C06 "Accounting (AAT2 Certificate, Level 2)": examined; no level stated against the rubric.
    "outcome:C06.1": (EXAM, PROVISIONAL, OutcomeType.SKILL_LEVEL, "assessed, no level stated"),
    "outcome:C06.2": (EXAM, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "assessed, mapping unsupported"),
    # C07 "IT Technician" (apprenticeship): end-point assessed; no level stated.
    "outcome:C07.1": (EXAM, PROVISIONAL, OutcomeType.SKILL_LEVEL, "assessed, no level stated"),
    "outcome:C07.2": (EXAM, PROVISIONAL, OutcomeType.SKILL_LEVEL, "assessed, no level stated"),
    # C08 "BNurs Adult Nursing": leads to eligibility to apply to the NMC, never to the
    # registration itself, and its three years lie beyond the 24-month model.
    "outcome:C08.1": (WORK_SAMPLE, PROVISIONAL, OutcomeType.CREDENTIAL, "eligibility to apply"),
    # C09 the AAT accounts apprenticeship: on-the-job practice; no assessed level stated.
    "outcome:C09.1": (PRACTICE, PROVISIONAL, OutcomeType.SKILL_LEVEL, "practised, not assessed"),
    "outcome:C09.2": (PRACTICE, PROVISIONAL, OutcomeType.SKILL_LEVEL, "practised, not assessed"),
    # C10 "CompTIA A+ (New Version)": examined, but the page does not support the mapping.
    "outcome:C10.1": (EXAM, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "assessed, mapping unsupported"),
    "outcome:C10.2": (EXAM, UNSUPPORTED, OutcomeType.SKILL_LEVEL, "assessed, mapping unsupported"),
}
VERSIONS = ("0.1.0", "0.2.0")
# Pack 0.1.0, before session 2's corrections (Task 7c), differs on five mappings: none of
# them stated a level either.
BEFORE_SESSION_2: dict[str, tuple[EvidenceKind, Confidence]] = {
    "outcome:C01.3": (TOPIC, UNSUPPORTED),
    "outcome:C05.1": (TOPIC, UNSUPPORTED),
    "outcome:C06.2": (EXAM, PROVISIONAL),
    "outcome:C10.1": (EXAM, PROVISIONAL),
    "outcome:C10.2": (EXAM, PROVISIONAL),
}


def _matrix(version: str, row_id: str) -> Matrix:
    pack = load_pack(version)
    reference = load_reference(version, pack)
    target = next(t for t in pack.targets if row_id.startswith(f"pack:{t.target_id}:"))
    return build_matrix(
        target.title,
        pack=pack,
        reference=reference,
        pack_target=target,
        occupation=None,
        exemplars=0,
        synthetic=False,
    )


def _below_the_level(matrix: Matrix) -> list[SkillEvidence]:
    """A concrete self-report one level below every required level: a known shortfall a
    course would have to close."""
    return [
        self_report(r.subject, r.required_level - 1, r.rubric.version_id, at=NOW)
        for r in matrix.rows
        if r.kind in LEVELLED_KINDS
        and r.rubric is not None
        and r.required_level is not None
        and r.required_level > 0
    ]


@pytest.mark.req("OUT1-02", "OUT1-03", "OUT1-11")
@pytest.mark.parametrize("version", VERSIONS)
def test_every_course_outcome_is_reviewed_and_none_states_a_level(version: str) -> None:
    pack = load_pack(version)
    outcomes = {o.outcome_id: o for o in pack_outcomes(pack, load_reference(version, pack))}

    assert set(outcomes) == set(REVIEWED)
    assert {o.option_id for o in outcomes.values()} == {f"option:C{n:02}" for n in range(1, 11)}
    for outcome_id, (kind, confidence, outcome_type, _why) in REVIEWED.items():
        if version == "0.1.0" and outcome_id in BEFORE_SESSION_2:
            kind, confidence = BEFORE_SESSION_2[outcome_id]
        found = outcomes[outcome_id]
        assert (found.evidence_kind, found.confidence, found.outcome_type) == (
            kind,
            confidence,
            outcome_type,
        ), outcome_id
        assert found.level_on_completion is None, outcome_id
        assert found.credential is None or found.credential.leads_to == "eligibility_to_apply"


@pytest.mark.req("OUT1-02", "OUT1-03", "OUT1-11", "RDY1-03", "TRACE01-06")
@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("outcome_id", sorted(REVIEWED))
@pytest.mark.parametrize("accepted", [False, True], ids=["as_stated", "accepted_by_person"])
def test_completing_a_course_never_raises_its_row_or_makes_its_target_ready(
    version: str, outcome_id: str, accepted: bool
) -> None:
    pack = load_pack(version)
    outcomes = pack_outcomes(pack, load_reference(version, pack))
    outcome = next(o for o in outcomes if o.outcome_id == outcome_id)
    if accepted:  # the person accepts the provider's mapping as their own assumption
        outcomes = [accept(o, by=ADA, at=NOW) if o is outcome else o for o in outcomes]
        assert next(o for o in outcomes if o.outcome_id == outcome_id).review_state is (
            OutcomeReview.ACCEPTED_ASSUMPTION
        )
    matrix = _matrix(version, outcome.skill_id)
    evidence = _below_the_level(matrix)
    # Every other gate held and verified, so only the course's own row can stand in the way.
    mapped = matrix.row(outcome.skill_id)
    assert mapped is not None, outcome.skill_id
    gates = [
        statement(r.subject, Holding.HELD, verified=True, at=NOW)
        for r in matrix.rows
        if r.gate is not None and r.gate.modelled and r.subject != mapped.subject
    ]

    current = assess(
        matrix, evidence=evidence, statements=gates, outcomes=outcomes, evidence_version=1
    )
    after = assess(
        matrix,
        evidence=evidence,
        statements=gates,
        outcomes=outcomes,
        evidence_version=1,
        completed=frozenset({outcome.offering_id}),
    )

    row_now = next(r for r in current.rows if r.row_id == outcome.skill_id)
    row_after = next(r for r in after.rows if r.row_id == outcome.skill_id)
    assert row_after.planned_level is None
    assert row_after.status is row_now.status
    assert row_after.status not in {RowStatus.MET, RowStatus.SATISFIED}
    assert after.state not in READY
    assert current.state not in READY
