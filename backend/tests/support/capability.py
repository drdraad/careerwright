"""Test builders for the capability model: synthetic matrices from the M0 fixture pack
(TRACE-01, P04, P05), labelled synthetic, and evidence records. Fixture IDs are never real
ESCO or regulator IDs; nothing here enters the product."""

import json
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from nessa.capability.evidence import (
    Answer,
    Holding,
    Method,
    RequirementStatement,
    SkillEvidence,
)
from nessa.capability.matrix import (
    Coverage,
    GateInfo,
    Importance,
    Matrix,
    MatrixRow,
    MatrixSources,
    RowKind,
    RubricView,
    apply_edits,
)
from nessa.capability.outcomes import (
    Confidence,
    EvidenceKind,
    OutcomeReview,
    OutcomeSpan,
    OutcomeType,
    PlannedOutcome,
    Provenance,
)
from nessa.capability.reference import GateKind

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "m0"
ADA = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
NOW = datetime(2027, 1, 1, 9, 0, tzinfo=UTC)


def fixture(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return data


def skill_row(
    skill_id: str, required: int, rubric: str, *, importance: str = "essential"
) -> MatrixRow:
    return MatrixRow(
        row_id=skill_id,
        subject=skill_id,
        label=skill_id.removeprefix("fixture:"),
        kind=RowKind.SKILL,
        importance=Importance(importance),
        source_importance=Importance(importance),
        observable_task=f"synthetic task for {skill_id}",
        required_level=required,
        rubric=RubricView(version_id=rubric, anchors={}, review_state="proposed"),
    )


def gate_row(gate_id: str) -> MatrixRow:
    return MatrixRow(
        row_id=gate_id,
        subject=f"gate:{gate_id}",
        label="Synthetic statutory registration",
        kind=RowKind.CREDENTIAL,
        importance=Importance.ESSENTIAL,
        source_importance=Importance.ESSENTIAL,
        gate=GateInfo(
            gate_key=gate_id.removeprefix("fixture:"),
            kind=GateKind.LEGAL_PRACTICE,
            label="Synthetic statutory registration",
            issuing_body="synthetic regulator fixture",
            jurisdiction="GB",
            verification="synthetic register check",
            acceptable_proof=["synthetic"],
        ),
    )


def synthetic_matrix(title: str, rows: list[MatrixRow]) -> Matrix:
    matrix = Matrix(
        target_key=title.casefold(),
        target_title=title,
        synthetic=True,
        sources=MatrixSources(
            pack_version="fixture",
            pack_dated=date(2027, 1, 1),
            reference_version="fixture",
            reference_dated=date(2027, 1, 1),
            reference_review_state="proposed",
            esco_release=None,
            occupation=None,
            occupation_note=None,
            pack_target=None,
        ),
        coverage=Coverage(
            exemplars=0,
            full_text_vacancies=0,
            snippet_vacancies=0,
            unknown_description_vacancies=0,
            posting_copies=0,
            esco_essential=0,
            esco_optional=0,
            modelled_rows=sum(r.rubric is not None for r in rows),
            not_modelled_rows=0,
        ),
        rows=rows,
    )
    return apply_edits(matrix, [])


def self_report(
    subject: str,
    level: int | None,
    rubric: str | None,
    *,
    example: str | None = "A recent piece of work, described",
    last_done: str | None = "2026-09",
    answer: Answer = Answer.DONE_INDEPENDENTLY,
    at: datetime = NOW,
    ai_assisted: bool | None = None,
) -> SkillEvidence:
    return SkillEvidence(
        evidence_id=uuid.uuid4(),
        subject=subject,
        rubric_version=rubric,
        answer=answer if level is not None else Answer.UNSURE,
        self_assessed_level=level,
        example=example,
        last_done=last_done,
        independence="independent" if answer is Answer.DONE_INDEPENDENTLY else None,
        tools="spreadsheet; an AI assistant for drafting" if ai_assisted else None,
        ai_assisted=ai_assisted,
        recorded_by=ADA,
        recorded_at=at,
    )


def assessed(
    subject: str,
    level: int,
    rubric: str,
    *,
    outcome_id: str | None = None,
    reviewed_on: date | None = None,
    at: datetime = NOW,
) -> SkillEvidence:
    return SkillEvidence(
        evidence_id=uuid.uuid4(),
        subject=subject,
        rubric_version=rubric,
        answer=Answer.DONE_INDEPENDENTLY,
        self_assessed_level=None,
        method=Method.ASSESSMENT,
        demonstrated_level=level,
        assessed_by="synthetic course assessment",
        reviewed_on=reviewed_on,
        outcome_id=outcome_id,
        recorded_by=ADA,
        recorded_at=at,
    )


def statement(
    subject: str, holding: Holding, *, verified: bool = False, at: datetime = NOW
) -> RequirementStatement:
    return RequirementStatement(
        statement_id=uuid.uuid4(),
        subject=subject,
        holding=holding,
        verified=verified,
        verification_note="checked the register" if verified else None,
        recorded_by=ADA,
        recorded_at=at,
    )


def trace_matrix() -> Matrix:
    target = fixture("worked_trace.json")["target"]
    return synthetic_matrix(
        target["title"],
        [
            skill_row(s["skill_id"], s["required_level"], "fixture-rubric-1")
            for s in target["skills"]
        ],
    )


def trace_evidence() -> list[SkillEvidence]:
    return [
        self_report(s["skill_id"], s["current_evidence_level"], "fixture-rubric-1")
        for s in fixture("worked_trace.json")["target"]["skills"]
    ]


def trace_outcomes(course: str = "fixture:course:A") -> list[PlannedOutcome]:
    trace = fixture("worked_trace.json")
    action = next(a for a in trace["catalogue"]["actions"] if a["id"] == course)
    outcomes = []
    for n, raw in enumerate(action["outcomes"]):
        span = raw["source_span"]
        outcomes.append(
            PlannedOutcome(
                outcome_id=f"{course}:outcome:{n}",
                offering_id=action["intakes"][0]["id"],
                option_id=course,
                option_title=course,
                skill_id=raw["skill_id"],
                outcome_type=OutcomeType.SKILL_LEVEL,
                level_on_completion=raw["level_on_completion"],
                evidence_kind=EvidenceKind(raw["evidence_kind"]),
                confidence=Confidence(raw["confidence"]),
                source_span=OutcomeSpan(
                    claim_id=None,
                    source_id=span["source_id"],
                    source_hash=span["source_hash"],
                    start=span["start"],
                    end=span["end"],
                    pointer=None,
                    retrieved_at=None,
                    excerpt=trace["syllabus_text"][span["start"] : span["end"]][:200],
                ),
                rubric_version=raw["rubric_version"],
                review_state=OutcomeReview(raw["review_state"]),
                provenance=Provenance.PROVIDER_CLAIM,
                months_minimum=2,
                as_of=date(2027, 1, 1),
            )
        )
    return outcomes
