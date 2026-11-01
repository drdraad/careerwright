"""The Skills chapter's facts (Task 10, backend half; MAP1-01, ASSESS-03, RDY1-03, PROF-13,
STATE-11; ADR 0012 as amended): readiness only where a reviewed rubric exists, "not part of
my job" never evidence, an expected qualification never met, and the person's chosen advert
spans checked against their own text."""

import uuid
from datetime import UTC, datetime

import pytest

from careerwright.capability.adverts import (
    MAX_SPAN_CHARS,
    MAX_SPANS_PER_EXAMPLE,
    AdvertSpan,
    check_spans,
    read_spans,
)
from careerwright.capability.evidence import Holding
from careerwright.capability.matrix import (
    EscoSeed,
    EscoSkillRelation,
    Matrix,
    MatrixRow,
    PostingCitation,
    RubricView,
    build_matrix,
)
from careerwright.capability.outcomes import pack_outcomes
from careerwright.capability.readiness import Assessment, ReadinessState, assess
from careerwright.capability.reference import load_reference
from careerwright.capability.skills import (
    EntryStanding,
    NotAssessedReason,
    PersonQualification,
    SeedState,
    SkillsAssessmentState,
    TargetSkills,
    entry_facts,
    names,
    target_skills,
)
from careerwright.catalogue.option_pack import load_pack
from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.profile.document import QualificationStatus
from tests.support.capability import gate_row, self_report, skill_row, statement, synthetic_matrix

PACK = load_pack("0.1.0")
REFERENCE = load_reference("0.1.0", PACK)
OUTCOMES = pack_outcomes(PACK, REFERENCE)
NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
RUBRIC = "fixture-rubric-1"
SQL = uuid.UUID("00000000-0000-4000-8000-00000000c001")
EXCEL = uuid.UUID("00000000-0000-4000-8000-00000000c002")
SEED = EscoSeed(
    release="esco-fixture",
    concept_id=uuid.UUID("00000000-0000-4000-8000-00000000e001"),
    label="synthetic analyst occupation",
    regulated=False,
    basis="occupation_choice",
    skills=[
        EscoSkillRelation(skill_id=SQL, label="SQL", skill_type="skill", relation="essential"),
        EscoSkillRelation(skill_id=EXCEL, label="Excel", skill_type="skill", relation="optional"),
    ],
)


def current(matrix: Matrix) -> Assessment:
    return assess(matrix, evidence=[], statements=[], outcomes=OUTCOMES, evidence_version=1)


def facts(
    matrix: Matrix, *, marks: frozenset[uuid.UUID] = frozenset(), none: bool = False
) -> TargetSkills:
    return target_skills(
        matrix,
        current(matrix),
        none_of_these=none,
        marks=marks,
        details_version=0,
        examples=[],
        qualifications=[],
        keys={},
    )


def outside_the_pack(occupation: EscoSeed | None) -> Matrix:
    return build_matrix(
        "Data wrangler",
        pack=PACK,
        reference=REFERENCE,
        pack_target=None,
        occupation=occupation,
        exemplars=0,
        synthetic=False,
    )


def reviewed(row: MatrixRow) -> MatrixRow:
    assert row.rubric is not None
    rubric = RubricView(version_id=row.rubric.version_id, anchors={}, review_state="reviewed")
    return row.model_copy(update={"rubric": rubric})


# --- readiness only where a reviewed rubric exists ---------------------------------------


@pytest.mark.req("RDY1-03", "ASSESS-03", "MAP1-09")
def test_a_target_outside_the_pack_is_not_assessed_and_shows_what_esco_lists() -> None:
    found = facts(outside_the_pack(SEED))

    assert found.assessment_state is SkillsAssessmentState.NOT_ASSESSED
    assert found.not_assessed_reason is NotAssessedReason.NO_RUBRIC
    assert found.readiness is None
    assert found.seed is SeedState.ESCO_OCCUPATION
    assert [(s.label, s.relation) for s in found.esco_listed] == [
        ("SQL", "essential"),
        ("Excel", "optional"),
    ]
    assert found.requirements == []  # ESCO's list is a seed, never what the target requires


@pytest.mark.req("RDY1-03", "MAP1-09")
def test_none_of_these_is_my_job_means_no_esco_list_and_never_a_readiness_result() -> None:
    found = facts(outside_the_pack(None), none=True)

    assert found.seed is SeedState.NONE_OF_THESE
    assert (found.esco_listed, found.readiness) == ([], None)
    assert found.not_assessed_reason is NotAssessedReason.NO_RUBRIC
    assert facts(outside_the_pack(None)).seed is SeedState.NO_OCCUPATION


@pytest.mark.req("RDY1-03", "OPTN-08")
@pytest.mark.parametrize(
    ("target", "reason"),
    [
        ("data-quality-analyst-manchester", NotAssessedReason.RUBRICS_NOT_REVIEWED),
        ("it-support-technician-bristol", NotAssessedReason.RUBRICS_NOT_REVIEWED),
        ("bookkeeping-assistant-leeds", NotAssessedReason.RUBRICS_NOT_REVIEWED),
        # Only the registration gate is required: no rubric, so never a readiness result.
        ("registered-nurse-manchester", NotAssessedReason.NO_RUBRIC),
    ],
)
def test_no_pack_target_is_assessed_while_its_rubrics_are_proposed(
    target: str, reason: NotAssessedReason
) -> None:
    pack_target = next(t for t in PACK.targets if t.target_id == target)
    matrix = build_matrix(
        pack_target.title,
        pack=PACK,
        reference=REFERENCE,
        pack_target=pack_target,
        occupation=None,
        exemplars=0,
        synthetic=False,
    )

    found = facts(matrix)

    assert found.assessment_state is SkillsAssessmentState.NOT_ASSESSED
    assert found.not_assessed_reason is reason
    assert found.readiness is None
    # What it asks: every required row, its review state and its pack records' date (R9).
    assert {r.row_id for r in found.requirements} == {r.row_id for r in matrix.rows if r.required}
    assert all(r.review_state == "proposed" for r in found.requirements)
    assert all(r.as_of == PACK.dated for r in found.requirements if r.employer_specific)
    assert all(r.gate.protected for r in found.requirements if r.gate is not None)


@pytest.mark.req("RDY1-03")
def test_a_rubric_beside_a_row_no_answer_can_settle_is_insufficient_coverage() -> None:
    no_rubric = skill_row("fixture:b", 2, RUBRIC).model_copy(
        update={"rubric": None, "required_level": None}
    )
    matrix = synthetic_matrix(
        "Synthetic target", [reviewed(skill_row("fixture:a", 2, RUBRIC)), no_rubric]
    )

    assert facts(matrix).not_assessed_reason is NotAssessedReason.INSUFFICIENT_COVERAGE


@pytest.mark.req("RDY1-03", "MAP1-04")
def test_readiness_is_shown_with_its_versions_where_every_rubric_is_reviewed() -> None:
    matrix = synthetic_matrix("Synthetic target", [reviewed(skill_row("fixture:a", 2, RUBRIC))])
    evidence = [self_report("fixture:a", 2, RUBRIC)]
    assessment = assess(matrix, evidence=evidence, statements=[], outcomes=[], evidence_version=3)

    found = target_skills(
        matrix,
        assessment,
        none_of_these=False,
        marks=frozenset(),
        details_version=0,
        examples=[],
        qualifications=[],
        keys={},
    )

    assert found.assessment_state is SkillsAssessmentState.ASSESSED
    assert found.readiness == assessment
    assert found.readiness.state is ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS
    assert (found.matrix_version, found.definition_version) == (
        matrix.matrix_version,
        matrix.definition_version,
    )
    assert (found.readiness.matrix_version, found.readiness.definition_version) == (
        matrix.matrix_version,
        matrix.definition_version,
    )


def test_one_proposed_rubric_beside_reviewed_ones_keeps_the_target_not_assessed() -> None:
    matrix = synthetic_matrix(
        "Synthetic target",
        [reviewed(skill_row("fixture:a", 2, RUBRIC)), skill_row("fixture:b", 2, RUBRIC)],
    )

    assert facts(matrix).not_assessed_reason is NotAssessedReason.RUBRICS_NOT_REVIEWED


def test_an_assessment_of_another_matrix_is_refused() -> None:
    one = synthetic_matrix("One", [reviewed(skill_row("fixture:a", 2, RUBRIC))])
    other = synthetic_matrix("Other", [reviewed(skill_row("fixture:a", 3, RUBRIC))])

    with pytest.raises(ValueError, match="another matrix"):
        target_skills(
            one,
            current(other),
            none_of_these=False,
            marks=frozenset(),
            details_version=0,
            examples=[],
            qualifications=[],
            keys={},
        )


# --- "not part of my job" is a display state ---------------------------------------------


@pytest.mark.req("MAP1-09", "ASSESS-02")
def test_not_part_of_my_job_is_shown_and_is_never_evidence() -> None:
    matrix = outside_the_pack(SEED)

    marked = facts(matrix, marks=frozenset({SQL}))
    unmarked = facts(matrix)

    assert [s.not_part_of_job for s in marked.esco_listed] == [True, False]
    assert [s.not_part_of_job for s in unmarked.esco_listed] == [False, False]
    # Nothing computed reads the mark: what the target asks and its result are unchanged.
    assert marked.model_dump(exclude={"esco_listed"}) == unmarked.model_dump(
        exclude={"esco_listed"}
    )


# --- entry facts: the person's qualifications beside the requirements naming them ---------


def _cited(row: MatrixRow, text: str) -> MatrixRow:
    citation = PostingCitation.model_validate(
        {
            "requirement_id": "fixture:req",
            "posting_id": "fixture:posting",
            "vacancy_id": "fixture:vacancy",
            "posting_title": None,
            "stated_kind": "credential",
            "stated_importance": "essential",
            "gate_words": None,
            "text": text,
            "description_kind": "full",
            "review_state": "proposed",
            "as_of": "2026-10-29",
            "claim": {
                "claim_id": "fixture:claim",
                "source_id": "fixture:source",
                "url": "https://example.org/advert",
                "sha256": "0" * 64,
                "start": 0,
                "end": len(text),
                "pointer": None,
                "excerpt": text,
                "retrieved_at": "2026-10-29T00:00:00Z",
                "occurrences": 1,
            },
        }
    )
    return row.model_copy(update={"citations": [citation]})


A_LEVELS = PersonQualification(name="A levels", status=QualificationStatus.EXPECTED)
GCSE = PersonQualification(name="GCSE Maths", status=QualificationStatus.ACHIEVED)
KEYS = {
    "A levels": "a level",
    "GCSE Maths": "gcse math",
    "Three A levels or equivalent": "three a level or equivalent",
    "Synthetic statutory registration": "synthetic statutory registration",
    "GCSE Maths and English at grade 4": "gcse math and english at grade 4",
    "a": "a",  # the synthetic skill row's label
    "Leveller": "leveller",
}


@pytest.mark.req("PROF-13", "RDY1-04")
def test_an_expected_qualification_is_never_met() -> None:
    row = _cited(skill_row("fixture:a", 2, RUBRIC), "Three A levels or equivalent")

    [fact] = entry_facts(row, [A_LEVELS], KEYS)

    assert (fact.qualification, fact.standing) == ("A levels", EntryStanding.EXPECTED_NOT_MET)


@pytest.mark.req("PROF-13", "RDY1-04", "READINESS-04")
def test_an_achieved_qualification_beside_a_protected_gate_stays_unresolved() -> None:
    gate = _cited(gate_row("fixture:gate"), "GCSE Maths and English at grade 4")
    plain = _cited(skill_row("fixture:a", 2, RUBRIC), "GCSE Maths and English at grade 4")

    assert [f.standing for f in entry_facts(gate, [GCSE], KEYS)] == [
        EntryStanding.ACHIEVED_UNVERIFIED
    ]
    assert [f.standing for f in entry_facts(plain, [GCSE], KEYS)] == [EntryStanding.ACHIEVED_STATED]
    # The fact sits beside the gate; it never satisfies it. The gate is settled only by the
    # person's own statement, verified at its source.
    matrix = synthetic_matrix("Synthetic target", [gate])
    found = assess(matrix, evidence=[], statements=[], outcomes=[], evidence_version=1)
    assert found.state is not ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS
    held = statement(gate.subject, Holding.HELD, verified=False)
    unverified = assess(matrix, evidence=[], statements=[held], outcomes=[], evidence_version=1)
    assert unverified.rows[0].status.value == "unresolved"


def test_a_qualification_names_a_requirement_only_by_its_whole_words() -> None:
    assert names("a level", ["three a level or equivalent"])
    assert names("gcse math", ["gcse math and english at grade 4"])
    assert not names("level", ["leveller"])
    assert not names("math english", ["gcse math and english at grade 4"])
    assert not names("", ["anything"])
    row = _cited(skill_row("fixture:a", 2, RUBRIC), "GCSE Maths and English at grade 4")
    assert entry_facts(row, [A_LEVELS], KEYS) == []


# --- the person's chosen spans in their own examples --------------------------------------

TEXT = "We need a data analyst.\nYou will write SQL daily.\nExcel is a plus."


def test_chosen_spans_are_kept_in_text_order_and_read_back_as_the_advert_s_words() -> None:
    sql = TEXT.index("write SQL daily")
    excel = TEXT.index("Excel is a plus")
    spans = [AdvertSpan(start=excel, end=excel + 15), AdvertSpan(start=sql, end=sql + 15)]

    ordered = check_spans(TEXT, spans)

    assert [s.start for s in ordered] == [sql, excel]
    assert [s.excerpt for s in read_spans(TEXT, ordered)] == ["write SQL daily", "Excel is a plus"]
    assert check_spans(TEXT, []) == []  # an empty selection clears it


@pytest.mark.parametrize(
    ("spans", "reason"),
    [
        ([AdvertSpan(start=3, end=3)], "span_empty"),
        ([AdvertSpan(start=0, end=len(TEXT) + 1)], "span_outside_text"),
        ([AdvertSpan(start=0, end=10), AdvertSpan(start=5, end=12)], "spans_overlap"),
        ([AdvertSpan(start=23, end=24)], "span_blank"),
        (
            [AdvertSpan(start=n, end=n + 1) for n in range(MAX_SPANS_PER_EXAMPLE + 1)],
            "too_many_spans",
        ),
    ],
)
def test_a_span_outside_the_rules_is_refused_with_its_reason(
    spans: list[AdvertSpan], reason: str
) -> None:
    with pytest.raises(CareerwrightError) as refused:
        check_spans(TEXT, spans)

    assert refused.value.code is ErrorCode.VALIDATION_FAILED
    assert refused.value.details == {"field": "spans", "reason": reason}


def test_a_span_longer_than_a_requirement_line_is_refused() -> None:
    text = "x" * (MAX_SPAN_CHARS + 10)

    with pytest.raises(CareerwrightError) as refused:
        check_spans(text, [AdvertSpan(start=0, end=MAX_SPAN_CHARS + 1)])

    assert refused.value.details == {"field": "spans", "reason": "span_too_long"}
    assert check_spans(text, [AdvertSpan(start=0, end=MAX_SPAN_CHARS)])
