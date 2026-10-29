"""The combined question graph (spec section 9, "Adaptive question budget"; S4.3; ADR 0012).
Pure: no SQL, no network, no model.

One graph spans the active targets: a subject several targets share is one prompt, with each
target's row and rubric beside it, so an answer is given once and only the level is asked
again where a rubric differs. Requirements and protected gates are asked first. Skills
follow in order of a decision-impact heuristic:

    priority = importance x uncertainty x route impact / burden

These are operational priorities, not psychometric quantities or a value of information
(spec section 9). Importance is 3 for essential, 2 for disputed, 1 for preferred; uncertainty
is 4 with no answer, 3 for an unsupported claim, 2 where an answer exists for another rubric
or disagrees with a demonstration, and 0 once the row has usable evidence; route impact is the
number of targets the subject serves; burden is 1 for a question. A row with no rubric is not
asked: there are no anchors to answer against.

The first 8 to 12 prompts are the initial set (`INITIAL_PROMPTS`); the rest wait until a
consequential uncertainty remains. Asking is `enough` once every gate is known or marked
unresolved and about 80% of the weighted required rows have usable evidence, and `stopped`
whenever the person stops or pauses: every open question is kept, unasked. Coverage is
reported as counts, never as a percentage and never as employability.
"""

import uuid
from collections.abc import Sequence
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from nessa.capability.evidence import (
    Holding,
    RequirementStatement,
    SkillEvidence,
    latest_statement,
    row_evidence,
)
from nessa.capability.matrix import LEVELLED_KINDS, GateInfo, Importance, Matrix, MatrixRow
from nessa.capability.outcomes import Confidence

INITIAL_PROMPTS = 12  # "approximately 8 to 12 high-value prompts across all roles"
ENOUGH_COVERED, ENOUGH_OF = 4, 5  # roughly 80% of weighted high-priority requirements
IMPORTANCE_WEIGHT = {
    Importance.ESSENTIAL: 3,
    Importance.DISPUTED: 2,
    Importance.PREFERRED: 1,
    Importance.UNKNOWN: 0,
}
QUESTION_BURDEN = 1


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class QuestionReason(StrEnum):
    NOT_STATED = "not_stated"  # a requirement or gate nobody has answered
    UNVERIFIED = "unverified"  # a protected gate held but not checked at its source
    NO_EVIDENCE = "no_evidence"
    UNSUPPORTED_CLAIM = "unsupported_claim"  # a level given without an example
    OTHER_RUBRIC = "other_rubric"  # answered for another target: reuse it, ask the level
    CONFLICT = "conflict"  # a self-report and a demonstration disagree: clarify


UNCERTAINTY_WEIGHT = {
    QuestionReason.NOT_STATED: 4,
    QuestionReason.NO_EVIDENCE: 4,
    QuestionReason.UNSUPPORTED_CLAIM: 3,
    QuestionReason.UNVERIFIED: 2,
    QuestionReason.OTHER_RUBRIC: 2,
    QuestionReason.CONFLICT: 2,
}


class PromptRow(StrictModel):
    target_key: str
    target_title: str
    row_id: str
    importance: Importance
    rubric_version: str | None
    required_level: int | None
    observable_task: str | None
    anchors: dict[int, str]


class Prompt(StrictModel):
    prompt_id: str
    kind: Literal["requirement", "skill"]
    subject: str
    label: str
    reason: QuestionReason
    priority: int
    importance_weight: int
    uncertainty_weight: int
    route_impact: int
    burden: int
    rows: list[PromptRow]  # the rows still needing this answer, one per target
    gate: GateInfo | None
    reuse_evidence_ids: list[uuid.UUID]  # an earlier answer on this subject to start from


class TargetVersions(StrictModel):
    target_key: str
    target_title: str
    matrix_version: str
    definition_version: str


class QuestionCoverage(StrictModel):
    gates_known: int  # answered, or marked unresolved by the person
    gates: int
    required_rows_with_usable_evidence: int
    required_rows: int
    weighted_with_usable_evidence: int
    weighted_required: int
    unresolved: list[str]  # subjects still unknown, kept as assumptions to resolve


class QuestionGraph(StrictModel):
    state: Literal["asking", "enough", "stopped"]
    evidence_version: int
    targets: list[TargetVersions]
    prompts: list[Prompt]  # every open question: requirements and gates first
    initial: list[str]  # prompt IDs of the first set
    coverage: QuestionCoverage


def question_graph(
    matrices: Sequence[Matrix],
    *,
    evidence: Sequence[SkillEvidence],
    statements: Sequence[RequirementStatement],
    evidence_version: int,
    stopped: bool = False,
) -> QuestionGraph:
    known = list(evidence)
    stated = list(statements)
    open_rows: dict[str, list[tuple[Matrix, MatrixRow, QuestionReason]]] = {}
    gates = gates_known = rows_total = rows_covered = weight_total = weight_covered = 0
    unresolved: list[str] = []
    for matrix in matrices:
        for row in matrix.rows:
            levelled = row.kind in LEVELLED_KINDS and row.gate is None
            if not levelled and row.required:
                reason, answered, resolved = _requirement(row, stated)
                gates += 1
                gates_known += answered
                if not resolved:
                    unresolved.append(row.subject)
            elif levelled and row.rubric is not None and row.importance is not Importance.UNKNOWN:
                reason, usable = _skill(row, known)
                if row.required:
                    weight = IMPORTANCE_WEIGHT[row.importance]
                    rows_total += 1
                    weight_total += weight
                    rows_covered += usable
                    weight_covered += weight * usable
                    if not usable:
                        unresolved.append(row.subject)
            else:
                continue
            if reason is not None:
                open_rows.setdefault(row.subject, []).append((matrix, row, reason))
    prompts = sorted(
        (_prompt(subject, found, known) for subject, found in open_rows.items()),
        key=lambda p: (p.kind != "requirement", -p.priority, p.label, p.subject),
    )
    enough = gates_known == gates and weight_covered * ENOUGH_OF >= weight_total * ENOUGH_COVERED
    return QuestionGraph(
        state="stopped" if stopped else "enough" if enough else "asking",
        evidence_version=evidence_version,
        targets=[
            TargetVersions(
                target_key=m.target_key,
                target_title=m.target_title,
                matrix_version=m.matrix_version,
                definition_version=m.definition_version,
            )
            for m in matrices
        ],
        prompts=prompts,
        initial=[p.prompt_id for p in prompts[:INITIAL_PROMPTS]],
        coverage=QuestionCoverage(
            gates_known=gates_known,
            gates=gates,
            required_rows_with_usable_evidence=rows_covered,
            required_rows=rows_total,
            weighted_with_usable_evidence=weight_covered,
            weighted_required=weight_total,
            unresolved=list(dict.fromkeys(unresolved)),
        ),
    )


def _requirement(
    row: MatrixRow, statements: list[RequirementStatement]
) -> tuple[QuestionReason | None, bool, bool]:
    """(why to ask, whether it is known or marked unresolved, whether it is resolved)."""
    statement = latest_statement(row.subject, statements)
    if statement is None:
        return QuestionReason.NOT_STATED, False, False
    if statement.holding is Holding.UNKNOWN:
        return None, True, False  # the person's own "don't know": not asked again
    if row.gate is not None and statement.holding is Holding.HELD and not statement.verified:
        return QuestionReason.UNVERIFIED, True, False
    return None, True, True


def _skill(row: MatrixRow, evidence: list[SkillEvidence]) -> tuple[QuestionReason | None, bool]:
    """(why to ask, whether the row has usable evidence)."""
    seen = row_evidence(row.subject, row.rubric.version_id if row.rubric else None, evidence)
    if seen.conflict:
        return QuestionReason.CONFLICT, seen.level is not None
    if seen.level is not None:
        return None, True
    if seen.confidence is Confidence.UNSUPPORTED:
        return QuestionReason.UNSUPPORTED_CLAIM, False
    if seen.shared_from_other_rubric:
        return QuestionReason.OTHER_RUBRIC, False
    return QuestionReason.NO_EVIDENCE, False


def _prompt(
    subject: str,
    found: list[tuple[Matrix, MatrixRow, QuestionReason]],
    evidence: list[SkillEvidence],
) -> Prompt:
    reason = max((r for _, _, r in found), key=lambda r: UNCERTAINTY_WEIGHT[r])
    first = found[0][1]
    importance = max(IMPORTANCE_WEIGHT[row.importance] for _, row, _ in found)
    uncertainty = UNCERTAINTY_WEIGHT[reason]
    impact = len({matrix.target_key for matrix, _, _ in found})
    rubrics = {row.rubric.version_id for _, row, _ in found if row.rubric is not None}
    return Prompt(
        prompt_id=f"prompt:{subject}",
        kind="skill" if first.kind in LEVELLED_KINDS and first.gate is None else "requirement",
        subject=subject,
        label=first.label,
        reason=reason,
        priority=importance * uncertainty * impact // QUESTION_BURDEN,
        importance_weight=importance,
        uncertainty_weight=uncertainty,
        route_impact=impact,
        burden=QUESTION_BURDEN,
        rows=[
            PromptRow(
                target_key=matrix.target_key,
                target_title=matrix.target_title,
                row_id=row.row_id,
                importance=row.importance,
                rubric_version=row.rubric.version_id if row.rubric else None,
                required_level=row.required_level,
                observable_task=row.observable_task,
                anchors=dict(row.rubric.anchors) if row.rubric else {},
            )
            for matrix, row, _ in found
        ],
        gate=first.gate,
        reuse_evidence_ids=[
            e.evidence_id
            for e in evidence
            if e.subject == subject and e.rubric_version not in rubrics
        ],
    )
