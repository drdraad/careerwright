"""Provisional skills matrices (MAP-1; S4.1, S4.4): built from the option pack's postings and
the ESCO seed, with the person's edits on top, versioned (ADR 0012)."""

import uuid
from datetime import UTC, datetime

import pytest

from nessa.capability.matrix import (
    EscoSeed,
    EscoSkillRelation,
    Importance,
    Matrix,
    RowEdit,
    RowScope,
    apply_edits,
    build_matrix,
    check_edit,
    derived_importance,
)
from nessa.capability.reference import load_reference
from nessa.catalogue.esco import concept_id
from nessa.catalogue.option_pack import load_pack
from nessa.errors import ErrorCode, NessaError

PACK = load_pack("0.1.0")
REFERENCE = load_reference("0.1.0", PACK)
ADA = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
QUERY_LANGUAGES = "http://data.europa.eu/esco/skill/9cf681c7-89ec-470c-b651-7fe03786f586"


def target(target_id: str) -> str:
    return next(t.title for t in PACK.targets if t.target_id == target_id)


def matrix_for(target_id: str, *, esco: EscoSeed | None = None, exemplars: int = 0) -> Matrix:
    title = target(target_id)
    pack_target = next(t for t in PACK.targets if t.target_id == target_id)
    return build_matrix(
        title,
        pack=PACK,
        reference=REFERENCE,
        pack_target=pack_target,
        occupation=esco,
        exemplars=exemplars,
    )


def seed() -> EscoSeed:
    """A data quality specialist seed: one crosswalked skill and two others (ESCO's own
    relations, as the taxonomy store gives them)."""
    return EscoSeed(
        release="esco-v1.2.1-en-csv",
        concept_id=uuid.uuid4(),
        label="data quality specialist",
        regulated=False,
        basis="pack_crosswalk",
        skills=[
            EscoSkillRelation(
                skill_id=concept_id(QUERY_LANGUAGES),
                label="query languages",
                skill_type="knowledge",
                relation="essential",
            ),
            EscoSkillRelation(
                skill_id=uuid.uuid4(), label="normalise data", skill_type=None, relation="essential"
            ),
            EscoSkillRelation(
                skill_id=uuid.uuid4(),
                label="statistics",
                skill_type="knowledge",
                relation="optional",
            ),
        ],
    )


def row(matrix: Matrix, row_id: str):  # type: ignore[no-untyped-def]
    return next(r for r in matrix.rows if r.row_id == row_id)


@pytest.mark.req("MAP1-03")
def test_essential_preferred_disputed_and_unknown_stay_distinct() -> None:
    assert derived_importance(["essential", "essential"]) is Importance.ESSENTIAL
    assert derived_importance(["preferred"]) is Importance.PREFERRED
    assert derived_importance(["essential", "preferred"]) is Importance.DISPUTED
    assert derived_importance(["unknown"]) is Importance.UNKNOWN
    assert derived_importance([]) is Importance.UNKNOWN

    matrix = matrix_for("data-quality-analyst-manchester", esco=seed())

    # J05, J18 and J20 list SQL as essential, J12 as preferred: the postings disagree.
    assert row(matrix, "pack:data-quality-analyst-manchester:independent-querying").importance is (
        Importance.DISPUTED
    )
    assert row(matrix, "pack:data-quality-analyst-manchester:data-validation").importance is (
        Importance.ESSENTIAL
    )
    # An ESCO relation is a seed, not a requirement of this target: its importance is unknown.
    esco_only = next(r for r in matrix.rows if r.label == "normalise data")
    assert esco_only.importance is Importance.UNKNOWN
    assert esco_only.esco is not None
    assert esco_only.esco.relation == "essential"
    assert "esco_seed_only" in esco_only.uncertainty
    assert not esco_only.required


@pytest.mark.req("MAP1-02")
def test_a_snippet_is_never_evidence_of_absence_and_its_prevalence_is_labelled() -> None:
    matrix = matrix_for("it-support-technician-bristol")
    windows = row(matrix, "pack:it-support-technician-bristol:windows-m365-support")

    # Vacancies: one advert seen three times (J01 full, J02 and J07 snippets) counts once and
    # as full; J14 and J15 are full; J03 is a snippet only and is left out of the absence
    # denominator. J14 and J15 ask for Windows and Microsoft 365 support.
    assert windows.prevalence is not None
    assert (windows.prevalence.full_text.mentioned, windows.prevalence.full_text.of) == (2, 3)
    assert (windows.prevalence.snippet.mentioned, windows.prevalence.snippet.of) == (0, 1)
    assert (matrix.coverage.full_text_vacancies, matrix.coverage.snippet_vacancies) == (3, 1)
    assert matrix.coverage.posting_copies == 6


@pytest.mark.req("MAP1-01")
def test_a_matrix_is_labelled_provisional_with_its_sources_counts_and_date() -> None:
    matrix = matrix_for("data-quality-analyst-manchester", esco=seed(), exemplars=2)

    assert matrix.status == "provisional_no_specialist_review"
    assert matrix.sources.pack_version == "0.1.0"
    assert matrix.sources.pack_dated.isoformat() == "2026-10-29"
    assert matrix.sources.reference_version == "0.1.0"
    assert matrix.sources.esco_release == "esco-v1.2.1-en-csv"
    assert matrix.sources.occupation is not None
    assert matrix.sources.occupation.basis == "pack_crosswalk"
    # The person's own full-text examples are counted as such; the pack's postings are job
    # boards' excerpts and are never counted as exemplars or as a full-description sample.
    assert matrix.coverage.exemplars == 2
    assert matrix.coverage.exemplar_rows_read is False
    assert matrix.coverage.esco_essential == 2
    assert matrix.coverage.esco_optional == 1
    assert matrix.synthetic is False


@pytest.mark.req("MAP1-07")
def test_each_modelled_row_carries_the_matrix_contract_fields() -> None:
    matrix = matrix_for("data-quality-analyst-manchester", esco=seed())
    querying = row(matrix, "pack:data-quality-analyst-manchester:independent-querying")

    assert querying.kind == "skill"
    assert querying.scope is RowScope.TARGET
    assert querying.observable_task
    assert querying.required_level == 2
    assert querying.rubric is not None
    assert querying.rubric.version_id.endswith("@0.1.0")
    assert sorted(querying.rubric.anchors) == [0, 1, 2, 3, 4]
    assert querying.acceptable_proof
    assert querying.prerequisites == []
    assert querying.jurisdiction == "GB-ENG"
    assert querying.review_state == "proposed"
    assert "importance_disputed" in querying.uncertainty
    # Every citation is span-located in its source, with the excerpt and retrieval date.
    assert {c.requirement_id for c in querying.citations} == {
        "req:J05.1",
        "req:J12.1",
        "req:J18.1",
        "req:J20.1",
    }
    for citation in querying.citations:
        assert len(citation.claim.sha256) == 64
        assert citation.claim.excerpt
        assert citation.claim.retrieved_at.date().isoformat() == "2026-10-29"
        assert (citation.claim.start is None) != (citation.claim.pointer is None)
    # The crosswalked ESCO skill is folded into the row, not listed twice.
    assert querying.subject == f"esco:{concept_id(QUERY_LANGUAGES)}"
    assert querying.esco is not None
    assert querying.esco.relation == "essential"
    assert not any(r.label == "query languages" for r in matrix.rows)


@pytest.mark.req("MAP1-05")
def test_statutory_registration_is_a_typed_protected_gate_on_every_nurse_posting() -> None:
    matrix = matrix_for("registered-nurse-manchester")
    gate_row = row(matrix, "pack:registered-nurse-manchester:nmc-registration")

    assert gate_row.gate is not None
    assert gate_row.gate.kind == "legal_practice"
    assert gate_row.gate.protected is True
    assert gate_row.kind == "credential"
    assert gate_row.required
    assert gate_row.importance is Importance.ESSENTIAL
    assert gate_row.rubric is None
    assert gate_row.required_level is None
    assert {c.posting_id for c in gate_row.citations} == {
        "job:J06",
        "job:J09",
        "job:J10",
        "job:J11",
        "job:J19",
    }
    # J10 accepts registration pending within two months: a posting's own note, never a
    # relaxation of the gate.
    assert any("J10" in note and "pending" in note for note in gate_row.gate.notes)


@pytest.mark.req("MAP1-05")
def test_a_gated_requirement_with_no_pack_row_becomes_a_target_gate() -> None:
    matrix = matrix_for("bookkeeping-assistant-leeds")
    work = row(matrix, "gate:uk-right-to-work")

    assert work.gate is not None
    assert work.gate.kind == "eligibility"
    assert work.subject == "gate:uk-right-to-work"
    assert [c.requirement_id for c in work.citations] == ["req:J17.1"]
    assert work.required


@pytest.mark.req("MAP1-06")
def test_one_posting_s_own_requirement_is_employer_specific_and_not_required_for_the_target() -> (
    None
):
    matrix = matrix_for("data-quality-analyst-manchester")
    degree = row(matrix, "posting:req:J05.5")

    assert degree.scope is RowScope.POSTING
    assert degree.employer_specific
    assert degree.importance is Importance.UNKNOWN
    assert [c.stated_importance for c in degree.citations] == ["essential"]
    assert not degree.required


@pytest.mark.req("MAP1-05", "RDY1-04", "READINESS-04")
def test_a_protected_gate_cannot_be_demoted() -> None:
    matrix = matrix_for("registered-nurse-manchester")

    for importance in (Importance.PREFERRED, Importance.UNKNOWN, Importance.DISPUTED):
        with pytest.raises(NessaError) as refused:
            check_edit(
                matrix,
                "pack:registered-nurse-manchester:nmc-registration",
                importance,
                warning_acknowledged=True,
            )
        assert refused.value.code is ErrorCode.PROTECTED_GATE


@pytest.mark.req("MAP1-06")
def test_relaxing_an_employer_requirement_needs_the_explicit_warning() -> None:
    matrix = matrix_for("data-quality-analyst-manchester")
    validation = "pack:data-quality-analyst-manchester:data-validation"

    with pytest.raises(NessaError) as refused:
        check_edit(matrix, validation, Importance.PREFERRED, warning_acknowledged=False)

    assert refused.value.code is ErrorCode.CONFIRMATION_REQUIRED
    assert refused.value.details["postings"] == ["job:J05", "job:J18"]
    assert check_edit(matrix, validation, Importance.PREFERRED, warning_acknowledged=True)


@pytest.mark.req("MAP1-04", "VERSIONS-04")
def test_changing_an_essential_row_creates_a_new_target_definition_and_keeps_its_history() -> None:
    before = matrix_for("data-quality-analyst-manchester", esco=seed())
    validation = "pack:data-quality-analyst-manchester:data-validation"
    edit = RowEdit(
        edit_id=uuid.uuid4(),
        row_id=validation,
        action="set_importance",
        importance=Importance.PREFERRED,
        reason="My target employers do not list it",
        warning_acknowledged=True,
        recorded_by=ADA,
        recorded_at=NOW,
        from_matrix_version=before.matrix_version,
        from_definition_version=before.definition_version,
    )

    after = apply_edits(before, [edit])

    assert after.definition_version != before.definition_version
    assert after.matrix_version != before.matrix_version
    edited = row(after, validation)
    assert edited.importance is Importance.PREFERRED
    assert edited.source_importance is Importance.ESSENTIAL  # the sources still say essential
    assert edited.citations == row(before, validation).citations
    assert "relaxed_by_person" in edited.uncertainty
    [applied] = after.edits
    assert applied.status == "applied"
    assert (applied.recorded_by, applied.reason) == (ADA, "My target employers do not list it")
    assert applied.from_definition_version == before.definition_version
    assert applied.to_definition_version == after.definition_version


@pytest.mark.req("MAP1-04")
def test_changing_a_row_outside_the_definition_keeps_the_definition() -> None:
    before = matrix_for("data-quality-analyst-manchester", esco=seed())
    statistics = next(r for r in before.rows if r.label == "statistics")
    edit = RowEdit(
        edit_id=uuid.uuid4(),
        row_id=statistics.row_id,
        action="set_importance",
        importance=Importance.PREFERRED,
        reason="Useful to me",
        warning_acknowledged=False,
        recorded_by=ADA,
        recorded_at=NOW,
        from_matrix_version=before.matrix_version,
        from_definition_version=before.definition_version,
    )

    after = apply_edits(before, [edit])

    assert after.matrix_version != before.matrix_version
    assert after.definition_version == before.definition_version


def test_an_edit_whose_row_is_gone_is_reported_never_dropped() -> None:
    before = matrix_for("bookkeeping-assistant-leeds")
    edit = RowEdit(
        edit_id=uuid.uuid4(),
        row_id="pack:bookkeeping-assistant-leeds:no-longer-here",
        action="set_importance",
        importance=Importance.ESSENTIAL,
        reason="r",
        warning_acknowledged=False,
        recorded_by=ADA,
        recorded_at=NOW,
        from_matrix_version=before.matrix_version,
        from_definition_version=before.definition_version,
    )

    after = apply_edits(before, [edit])

    assert [e.status for e in after.edits] == ["row_missing"]
    assert after.definition_version == before.definition_version


def test_the_same_inputs_give_the_same_versions() -> None:
    first = matrix_for("it-support-technician-bristol")
    second = matrix_for("it-support-technician-bristol")

    assert (first.matrix_version, first.definition_version) == (
        second.matrix_version,
        second.definition_version,
    )
    assert first.matrix_version.startswith("m-")
    assert first.definition_version.startswith("d-")


def test_a_target_with_no_pack_target_and_no_seed_has_no_rows_and_says_why() -> None:
    matrix = build_matrix(
        "Marine biologist",
        pack=PACK,
        reference=REFERENCE,
        pack_target=None,
        occupation=None,
        exemplars=0,
    )

    assert matrix.rows == []
    assert matrix.sources.pack_target is None
    assert matrix.sources.occupation is None
    assert matrix.coverage.full_text_vacancies == 0
