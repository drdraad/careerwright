"""Provisional skills matrices (spec section 8, MAP-1; S4.1, S4.4; ADR 0012). Pure: no SQL,
no network, no model.

A target's matrix is built from three inputs, each kept visible:

- **The option pack's postings** for the pack target with the person's target title: each
  requirement row the curator mapped to a pack row (`pack:<target>:<row>`) becomes a
  target row with its rubric (`careerwright.capability.reference`); a requirement naming a gate
  becomes a typed protected gate; any other requirement stays one posting's own row
  (employer-specific). Every row cites its claims with their spans. Job-board postings are
  never the person's exemplars and never a full-description employer sample.
- **The ESCO seed**: the occupation's essential and optional skill relations. A relation is
  a seed, not a statutory rule or a proficiency level, so an ESCO-only row's importance for
  this target is unknown and it has no rubric (it is not modelled).
- **The person's edits**: importance set at the checkpoint, with actor, reason and the old
  and new versions. A protected gate is never demoted, and relaxing an employer's
  requirement needs the explicit warning.

Importance is derived from what the postings state: all essential is essential, all
preferred is preferred, a mix is disputed, none is unknown. A disputed row counts as
required until the person decides (ADR 0012, provisional). Two versions identify a matrix:
`matrix_version` changes with any content, and `definition_version` only with the target
definition (the required rows, their levels, rubrics and gate types). A changed definition
is a different target, so results computed for the old one are stale (MAP1-04).
"""

import hashlib
import json
import uuid
from collections.abc import Iterable, Sequence
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from careerwright.capability.reference import Gate, GateKind, Reference, Rubric
from careerwright.catalogue.esco import concept_id
from careerwright.catalogue.option_pack import (
    Claim,
    JobPosting,
    Pack,
    Skill,
    SkillRequirement,
    Source,
    Target,
)
from careerwright.catalogue.records import LabelMatch
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence.jobs import title_key

MATRIX_STATUS: Literal["provisional_no_specialist_review"] = "provisional_no_specialist_review"
JURISDICTION: Literal["GB-ENG"] = "GB-ENG"
VERSION_DIGITS = 16


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Importance(StrEnum):
    ESSENTIAL = "essential"
    PREFERRED = "preferred"
    DISPUTED = "disputed"  # the sources disagree
    UNKNOWN = "unknown"  # no source states it for this target


# Disputed counts as required until the person decides: some postings require it, so a
# readiness result never rests on leaving it out (ADR 0012, provisional).
REQUIRED_IMPORTANCE = frozenset({Importance.ESSENTIAL, Importance.DISPUTED})


class RowKind(StrEnum):
    """Credentials, experience and eligibility are distinct from learnable skills (spec
    section 8): only skills and tasks have levels."""

    SKILL = "skill"
    TASK = "task"
    CREDENTIAL = "credential"
    EXPERIENCE = "experience"
    ELIGIBILITY = "eligibility"


LEVELLED_KINDS = frozenset({RowKind.SKILL, RowKind.TASK})
_KIND_RANK: dict[str | None, int] = {"full": 2, "snippet": 1, None: 0}
_GATE_ROW_KIND = {
    GateKind.LEGAL_PRACTICE: RowKind.CREDENTIAL,
    GateKind.RECOGNITION: RowKind.CREDENTIAL,
    GateKind.ADMISSION: RowKind.ELIGIBILITY,
    GateKind.ELIGIBILITY: RowKind.ELIGIBILITY,
}


class RowScope(StrEnum):
    TARGET = "target"  # a requirement of the target role
    POSTING = "posting"  # one posting's own requirement: employer-specific


class Uncertainty(StrEnum):
    ESCO_SEED_ONLY = "esco_seed_only"  # only ESCO lists it; no local source states it
    IMPORTANCE_DISPUTED = "importance_disputed"
    IMPORTANCE_UNKNOWN = "importance_unknown"
    NO_RUBRIC = "no_rubric"  # not modelled: no observable task or required level
    SNIPPET_SIGNAL_ONLY = "snippet_signal_only"  # named only where a posting was a snippet
    ONE_POSTING_ONLY = "one_posting_only"
    PROPOSED_SOURCES = "proposed_sources"  # its pack records are not reviewed
    PROPOSED_RUBRIC = "proposed_rubric"
    PROPOSED_CROSSWALK = "proposed_crosswalk"
    SET_BY_PERSON = "set_by_person"
    RELAXED_BY_PERSON = "relaxed_by_person"  # an employer's requirement the person relaxed
    CHALLENGED = "challenged"
    REGULATION_NOT_MODELLED = "regulation_not_modelled"  # a regulated occupation, no typed gate


def derived_importance(stated: Iterable[str]) -> Importance:
    seen = {Importance(s) for s in stated} - {Importance.UNKNOWN}
    if not seen:
        return Importance.UNKNOWN
    if seen == {Importance.ESSENTIAL}:
        return Importance.ESSENTIAL
    if seen == {Importance.PREFERRED}:
        return Importance.PREFERRED
    return Importance.DISPUTED


class ClaimSpan(StrictModel):
    """A SourceClaim's location: offsets into the hashed text, or a JSON pointer."""

    claim_id: str
    source_id: str
    url: str
    sha256: str
    start: int | None
    end: int | None
    pointer: str | None
    excerpt: str
    retrieved_at: datetime
    occurrences: int | None


class PostingCitation(StrictModel):
    """One posting's requirement row behind a matrix row, as the pack records it."""

    requirement_id: str
    posting_id: str
    vacancy_id: str
    posting_title: str | None
    stated_kind: str
    stated_importance: Importance
    gate_words: str | None
    text: str | None
    description_kind: Literal["full", "snippet"] | None
    review_state: Literal["proposed", "reviewed"]  # the pack record's
    as_of: date  # its retrieval date: never "current"
    claim: ClaimSpan


class EscoLink(StrictModel):
    skill_id: uuid.UUID
    label: str
    skill_type: str | None
    relation: Literal["essential", "optional"]


class GateInfo(StrictModel):
    gate_key: str
    kind: GateKind
    protected: Literal[True] = True
    # False: ESCO records the occupation as regulated and no typed gate models what it
    # requires, so nothing the person states can satisfy it (never silence).
    modelled: bool = True
    label: str
    issuing_body: str | None  # None only for a gate that is not modelled
    jurisdiction: str
    verification: str | None  # None only for a gate that is not modelled
    acceptable_proof: list[str]
    notes: list[str] = Field(default_factory=list)  # a posting's own wording of the gate


class RubricView(StrictModel):
    version_id: str
    anchors: dict[int, str]
    review_state: Literal["proposed", "reviewed"]


class Count(StrictModel):
    mentioned: int = Field(ge=0)
    of: int = Field(ge=0)


class Prevalence(StrictModel):
    """Distinct vacancies naming the row. `full_text` counts vacancies with a full
    description; `snippet` counts the rest (snippets, or a description of unknown kind):
    snippet prevalence, never evidence of absence and never requirement frequency."""

    full_text: Count
    snippet: Count


class Challenge(StrictModel):
    reason: str
    recorded_by: uuid.UUID
    recorded_at: datetime


class MatrixRow(StrictModel):
    row_id: str
    subject: str  # what evidence about it is recorded against, shared across targets
    label: str
    kind: RowKind
    scope: RowScope = RowScope.TARGET
    importance: Importance  # after the person's edits
    source_importance: Importance  # as the sources state it
    gate: GateInfo | None = None
    observable_task: str | None = None
    required_level: int | None = Field(default=None, ge=0, le=4)
    rubric: RubricView | None = None
    acceptable_proof: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)  # row IDs
    prevalence: Prevalence | None = None
    citations: list[PostingCitation] = Field(default_factory=list)
    esco: EscoLink | None = None
    uncertainty: list[Uncertainty] = Field(default_factory=list)
    challenges: list[Challenge] = Field(default_factory=list)
    jurisdiction: str = JURISDICTION
    review_state: Literal["proposed", "reviewed"] = "proposed"
    employer_specific: bool = False  # a non-statutory requirement from postings

    @computed_field  # type: ignore[prop-decorator]
    @property
    def required(self) -> bool:
        """In the target definition: a protected gate, or essential or disputed."""
        return self.gate is not None or self.importance in REQUIRED_IMPORTANCE


OccupationBasis = Literal["occupation_choice", "esco_label", "pack_crosswalk"]


class OccupationLink(StrictModel):
    concept_id: uuid.UUID
    label: str
    # occupation_choice: the occupation the person chose, read from the choice's own source
    # (its ESCO URI); esco_label: the occupation ESCO labels with the title; pack_crosswalk:
    # the pack target's crosswalk.
    basis: OccupationBasis
    regulated: bool | None


class PackTargetLink(StrictModel):
    target_id: str
    title: str
    city: str  # where its postings are: a target in another city still reads them
    # How it was found: the same title, or the target's ESCO occupation named by the pack
    # target's crosswalk (a target chosen in the product is stored by ESCO's label).
    basis: Literal["title", "esco_crosswalk"]


class OccupationNote(StrEnum):
    """Why a matrix has no ESCO seed."""

    NO_EXACT_LABEL = "no_exact_esco_label"
    AMBIGUOUS_LABEL = "ambiguous_esco_label"
    NOT_IN_HELD_TAXONOMY = "not_in_held_taxonomy"


class PackTargetNote(StrEnum):
    """Why a matrix has no pack target although one could apply."""

    # Several pack targets' crosswalks name the target's occupation: never guessed between,
    # so the person chooses (spec section 8: a title mapping to several is asked about).
    AMBIGUOUS_CROSSWALK = "ambiguous_crosswalk"


class MatrixSources(StrictModel):
    pack_version: str
    pack_dated: date
    reference_version: str
    reference_dated: date
    reference_review_state: Literal["proposed", "reviewed"]
    esco_release: str | None
    occupation: OccupationLink | None
    occupation_note: OccupationNote | None
    pack_target: PackTargetLink | None
    pack_target_note: PackTargetNote | None = None


class MatrixCoverage(StrictModel):
    exemplars: int = Field(ge=0, le=3)  # the person's own full-text examples
    # Requirement rows are not yet read from the person's examples (ADR 0012): counted only.
    exemplar_rows_read: Literal[False] = False
    full_text_vacancies: int
    snippet_vacancies: int
    unknown_description_vacancies: int
    posting_copies: int
    esco_essential: int
    esco_optional: int
    modelled_rows: int  # rows with a rubric
    not_modelled_rows: int  # skill and task rows without one


class RowEdit(StrictModel):
    """A person's edit at the checkpoint, as recorded."""

    edit_id: uuid.UUID
    row_id: str
    action: Literal["set_importance", "challenge"]
    importance: Importance | None
    reason: str
    warning_acknowledged: bool
    recorded_by: uuid.UUID
    recorded_at: datetime
    from_matrix_version: str
    from_definition_version: str
    to_matrix_version: str | None = None
    to_definition_version: str | None = None


class AppliedEdit(RowEdit):
    status: Literal["applied", "row_missing"]  # a row the sources no longer give


class Matrix(StrictModel):
    target_key: str
    target_title: str
    status: Literal["provisional_no_specialist_review"] = MATRIX_STATUS
    synthetic: bool = False
    jurisdiction: Literal["GB-ENG"] = JURISDICTION
    matrix_version: str = ""
    definition_version: str = ""
    sources: MatrixSources
    coverage: MatrixCoverage
    rows: list[MatrixRow]
    edits: list[AppliedEdit] = Field(default_factory=list)

    def row(self, row_id: str) -> MatrixRow | None:
        return next((r for r in self.rows if r.row_id == row_id), None)


class EscoSkillRelation(StrictModel):
    skill_id: uuid.UUID
    label: str
    skill_type: str | None
    relation: Literal["essential", "optional"]


class EscoSeed(StrictModel):
    """An ESCO occupation and its skill relations, as the taxonomy store holds them."""

    release: str
    concept_id: uuid.UUID
    label: str
    regulated: bool | None
    basis: OccupationBasis
    skills: list[EscoSkillRelation]


def build_matrix(
    target_title: str,
    *,
    pack: Pack,
    reference: Reference,
    pack_target: Target | None,
    occupation: EscoSeed | None,
    exemplars: int,
    synthetic: bool,
    pack_target_basis: Literal["title", "esco_crosswalk"] = "title",
    pack_target_note: PackTargetNote | None = None,
    edits: Sequence[RowEdit] = (),
    occupation_note: OccupationNote | None = None,
) -> Matrix:
    """`synthetic`: the workspace's label (or a fixture's), carried by every result."""
    rows: list[MatrixRow] = []
    vacancies: dict[str, str | None] = {}
    copies = 0
    if pack_target is not None:
        found = _PackRows(pack, reference, pack_target, occupation)
        rows, vacancies, copies = found.rows(), found.vacancy_kinds, len(found.postings)
    covered = {r.subject for r in rows}
    rows = _ordered([*rows, *_regulation(occupation, rows), *_esco_rows(occupation, covered)])
    relations = occupation.skills if occupation is not None else []
    matrix = Matrix(
        target_key=title_key(target_title),
        target_title=target_title,
        synthetic=synthetic,
        sources=MatrixSources(
            pack_version=pack.pack_version,
            pack_dated=pack.dated,
            reference_version=reference.reference_version,
            reference_dated=reference.dated,
            reference_review_state=reference.review_state,
            esco_release=occupation.release if occupation is not None else None,
            occupation=(
                OccupationLink(
                    concept_id=occupation.concept_id,
                    label=occupation.label,
                    basis=occupation.basis,
                    regulated=occupation.regulated,
                )
                if occupation is not None
                else None
            ),
            occupation_note=None if occupation is not None else occupation_note,
            pack_target=(
                PackTargetLink(
                    target_id=pack_target.target_id,
                    title=pack_target.title,
                    city=pack_target.city,
                    basis=pack_target_basis,
                )
                if pack_target is not None
                else None
            ),
            pack_target_note=None if pack_target is not None else pack_target_note,
        ),
        coverage=MatrixCoverage(
            exemplars=exemplars,
            full_text_vacancies=sum(k == "full" for k in vacancies.values()),
            snippet_vacancies=sum(k == "snippet" for k in vacancies.values()),
            unknown_description_vacancies=sum(k is None for k in vacancies.values()),
            posting_copies=copies,
            esco_essential=sum(r.relation == "essential" for r in relations),
            esco_optional=sum(r.relation == "optional" for r in relations),
            modelled_rows=sum(r.rubric is not None for r in rows),
            not_modelled_rows=sum(r.rubric is None and r.kind in LEVELLED_KINDS for r in rows),
        ),
        rows=rows,
    )
    return apply_edits(matrix, edits)


def _ordered(rows: list[MatrixRow]) -> list[MatrixRow]:
    """Gates first, then the target's rows (pack order), ESCO seeds, one posting's rows."""

    def rank(row: MatrixRow) -> int:
        if row.gate is not None:
            return 0
        if row.scope is RowScope.POSTING:
            return 3
        return 2 if row.esco is not None and not row.citations else 1

    return sorted(rows, key=rank)  # stable: each group keeps its order


class _PackRows:
    """The rows a pack target's postings give."""

    def __init__(
        self, pack: Pack, reference: Reference, target: Target, occupation: EscoSeed | None
    ) -> None:
        self.pack = pack
        self.reference = reference
        self.target = target
        self.esco = {r.skill_id: r for r in occupation.skills} if occupation is not None else {}
        self.claims = {c.claim_id: c for c in pack.claims}
        self.sources = {s.source_id: s for s in pack.sources}
        self.postings = [p for p in pack.job_postings if p.target_id == target.target_id]
        # A vacancy's copies count once, as their best description: full, snippet, unknown.
        self.vacancy_kinds: dict[str, str | None] = {}
        for posting in self.postings:
            value = pack.value(posting.description_kind)
            kind = value if value in ("full", "snippet") else None
            held = self.vacancy_kinds.get(posting.vacancy_id)
            if posting.vacancy_id not in self.vacancy_kinds or _KIND_RANK[kind] > _KIND_RANK[held]:
                self.vacancy_kinds[posting.vacancy_id] = kind
        self.full = {v for v, k in self.vacancy_kinds.items() if k == "full"}

    def rows(self) -> list[MatrixRow]:
        requirements = {q.record_id: q for q in self.pack.skill_requirements}
        by_row: dict[str, list[PostingCitation]] = {}
        own: list[MatrixRow] = []
        for posting in self.postings:
            for requirement_id in posting.requirement_ids:
                requirement = requirements[requirement_id]
                citation = self._citation(posting, requirement)
                if requirement.skill_id is not None:
                    by_row.setdefault(requirement.skill_id, []).append(citation)
                elif requirement.gate is not None:
                    gate = self._gate_words(requirement.gate)
                    by_row.setdefault(f"gate:{gate.gate_key}", []).append(citation)
                else:
                    own.append(self._posting_row(requirement, citation))
        rows = [
            self._pack_row(skill, by_row.get(skill.skill_id, []))
            for skill in self.pack.skills
            if skill.target_id == self.target.target_id
        ]
        rows += [
            self._gate_row(self._gate_key(key), citations)
            for key, citations in by_row.items()
            if key.startswith("gate:")
        ]
        return [*rows, *own]

    def _gate_words(self, words: str) -> Gate:
        gate = self.reference.gate_for_words(words)
        if gate is None:  # `load_reference` refuses a pack with such a requirement
            raise ValueError(f"no typed gate for {words!r}")
        return gate

    def _gate_key(self, key: str) -> Gate:
        return next(g for g in self.reference.gates if f"gate:{g.gate_key}" == key)

    def _citation(self, posting: JobPosting, requirement: SkillRequirement) -> PostingCitation:
        claim: Claim = self.claims[requirement.text]
        source: Source = self.sources[claim.source_id]
        title = self.pack.value(posting.title)
        text = claim.value
        kind = self.pack.value(posting.description_kind)
        return PostingCitation(
            requirement_id=requirement.record_id,
            posting_id=posting.record_id,
            vacancy_id=posting.vacancy_id,
            posting_title=title if isinstance(title, str) else None,
            stated_kind=requirement.kind,
            stated_importance=Importance(requirement.importance),
            gate_words=requirement.gate,
            text=text if isinstance(text, str) else None,
            description_kind="full" if kind == "full" else "snippet" if kind == "snippet" else None,
            review_state=requirement.review_state.value,
            as_of=requirement.as_of,
            claim=ClaimSpan(
                claim_id=claim.claim_id,
                source_id=source.source_id,
                url=source.url,
                sha256=source.sha256,
                start=claim.span.start,
                end=claim.span.end,
                pointer=claim.span.pointer,
                excerpt=claim.excerpt,
                retrieved_at=source.retrieved_at,
                occurrences=claim.occurrences,
            ),
        )

    def _prevalence(self, citations: list[PostingCitation]) -> Prevalence:
        named = {c.vacancy_id for c in citations}
        others = set(self.vacancy_kinds) - self.full
        return Prevalence(
            full_text=Count(mentioned=len(named & self.full), of=len(self.full)),
            snippet=Count(mentioned=len(named & others), of=len(others)),
        )

    def _common(self, citations: list[PostingCitation], prevalence: Prevalence) -> set[Uncertainty]:
        found: set[Uncertainty] = set()
        if any(c.review_state != "reviewed" for c in citations):
            found.add(Uncertainty.PROPOSED_SOURCES)
        if prevalence.full_text.mentioned == 0 and prevalence.snippet.mentioned > 0:
            found.add(Uncertainty.SNIPPET_SIGNAL_ONLY)
        return found

    def _pack_row(self, skill: Skill, citations: list[PostingCitation]) -> MatrixRow:
        gate = self.reference.gate_for_row(skill.skill_id)
        if gate is not None:
            return self._gate_row(gate, citations, row_id=skill.skill_id, label=skill.label)
        rubric = self.reference.rubric_for(skill.skill_id)
        source_importance = derived_importance(c.stated_importance for c in citations)
        prevalence = self._prevalence(citations)
        uncertainty = self._common(citations, prevalence)
        uncertainty |= _importance_uncertainty(source_importance)
        esco_id = concept_id(rubric.esco_skill) if rubric and rubric.esco_skill else None
        if rubric is None:
            uncertainty.add(Uncertainty.NO_RUBRIC)
        elif self.reference.review_state == "proposed":
            uncertainty.add(Uncertainty.PROPOSED_RUBRIC)
            if esco_id is not None:
                uncertainty.add(Uncertainty.PROPOSED_CROSSWALK)
        relation = self.esco.get(esco_id) if esco_id is not None else None
        return MatrixRow(
            row_id=skill.skill_id,
            subject=f"esco:{esco_id}" if esco_id is not None else skill.skill_id,
            label=skill.label,
            kind=RowKind(skill.kind),
            importance=source_importance,
            source_importance=source_importance,
            observable_task=rubric.observable_task if rubric else None,
            required_level=rubric.required_level if rubric else None,
            rubric=_rubric_view(rubric, self.reference) if rubric else None,
            acceptable_proof=list(rubric.acceptable_proof) if rubric else [],
            prerequisites=list(rubric.prerequisites) if rubric else [],
            prevalence=prevalence,
            citations=citations,
            esco=_esco_link(relation) if relation is not None else None,
            uncertainty=sorted(uncertainty),
            review_state=_review_state(citations, self.reference),
            employer_specific=bool(citations),
        )

    def _gate_row(
        self,
        gate: Gate,
        citations: list[PostingCitation],
        *,
        row_id: str | None = None,
        label: str | None = None,
    ) -> MatrixRow:
        source_importance = derived_importance(c.stated_importance for c in citations)
        prevalence = self._prevalence(citations)
        canonical = gate.gate_words[0] if gate.gate_words else None
        notes = sorted(
            {
                f"{c.posting_id}: {c.gate_words}"
                for c in citations
                if c.gate_words is not None and c.gate_words != canonical
            }
        )
        return MatrixRow(
            row_id=row_id or f"gate:{gate.gate_key}",
            subject=f"gate:{gate.gate_key}",
            label=label or gate.label,
            kind=_GATE_ROW_KIND[gate.kind],
            importance=Importance.ESSENTIAL,  # a protected gate is always required
            source_importance=source_importance,
            gate=GateInfo(
                gate_key=gate.gate_key,
                kind=gate.kind,
                label=gate.label,
                issuing_body=gate.issuing_body,
                jurisdiction=gate.jurisdiction,
                verification=gate.verification,
                acceptable_proof=list(gate.acceptable_proof),
                notes=notes,
            ),
            acceptable_proof=list(gate.acceptable_proof),
            prevalence=prevalence,
            citations=citations,
            uncertainty=sorted(self._common(citations, prevalence)),
            jurisdiction=gate.jurisdiction,
            review_state=_review_state(citations, self.reference),
        )

    def _posting_row(self, requirement: SkillRequirement, citation: PostingCitation) -> MatrixRow:
        kind = RowKind(requirement.kind)
        uncertainty = {Uncertainty.ONE_POSTING_ONLY, Uncertainty.IMPORTANCE_UNKNOWN}
        if citation.review_state != "reviewed":
            uncertainty.add(Uncertainty.PROPOSED_SOURCES)
        if kind in LEVELLED_KINDS:
            uncertainty.add(Uncertainty.NO_RUBRIC)
        row_id = f"posting:{requirement.record_id}"
        return MatrixRow(
            row_id=row_id,
            subject=row_id,
            label=citation.text or requirement.record_id,
            kind=kind,
            scope=RowScope.POSTING,
            # One posting's statement says nothing about the target as a whole: its own
            # importance stays in its citation.
            importance=Importance.UNKNOWN,
            source_importance=Importance.UNKNOWN,
            citations=[citation],
            uncertainty=sorted(uncertainty),
            review_state=_review_state([citation], self.reference),
            employer_specific=True,
        )


def _importance_uncertainty(importance: Importance) -> set[Uncertainty]:
    if importance is Importance.DISPUTED:
        return {Uncertainty.IMPORTANCE_DISPUTED}
    if importance is Importance.UNKNOWN:
        return {Uncertainty.IMPORTANCE_UNKNOWN}
    return set()


def _rubric_view(rubric: Rubric, reference: Reference) -> RubricView:
    return RubricView(
        version_id=rubric.version_id,
        anchors=dict(rubric.anchors),
        review_state=reference.review_state,
    )


def _review_state(
    citations: Sequence[PostingCitation], reference: Reference
) -> Literal["proposed", "reviewed"]:
    reviewed = reference.review_state == "reviewed" and all(
        c.review_state == "reviewed" for c in citations
    )
    return "reviewed" if reviewed else "proposed"


def _esco_link(relation: EscoSkillRelation) -> EscoLink:
    return EscoLink(
        skill_id=relation.skill_id,
        label=relation.label,
        skill_type=relation.skill_type,
        relation=relation.relation,
    )


def _esco_rows(occupation: EscoSeed | None, covered: set[str]) -> list[MatrixRow]:
    if occupation is None:
        return []
    relations = sorted(
        (r for r in occupation.skills if f"esco:{r.skill_id}" not in covered),
        key=lambda r: (r.relation != "essential", r.label),
    )
    return [
        MatrixRow(
            row_id=f"esco:{r.skill_id}",
            subject=f"esco:{r.skill_id}",
            label=r.label,
            kind=RowKind.SKILL,
            importance=Importance.UNKNOWN,
            source_importance=Importance.UNKNOWN,
            esco=_esco_link(r),
            uncertainty=[Uncertainty.ESCO_SEED_ONLY, Uncertainty.NO_RUBRIC],
        )
        for r in relations
    ]


REGULATION_ROW = "gate:occupation-regulation"
_PRACTICE_GATES = frozenset({GateKind.LEGAL_PRACTICE, GateKind.RECOGNITION})


def _regulation(occupation: EscoSeed | None, rows: list[MatrixRow]) -> list[MatrixRow]:
    """An unresolved protected gate for an occupation ESCO records as regulated when no
    typed gate models its right to practise: the regulation is never silence (spec section
    8, "Unverified gates remain unresolved"; C1)."""
    if occupation is None or occupation.regulated is not True:
        return []
    if any(r.gate is not None and r.gate.kind in _PRACTICE_GATES for r in rows):
        return []
    return [
        MatrixRow(
            row_id=REGULATION_ROW,
            subject=REGULATION_ROW,
            label=f"Registration to practise as {occupation.label} (not yet modelled)",
            kind=RowKind.CREDENTIAL,
            importance=Importance.ESSENTIAL,
            source_importance=Importance.UNKNOWN,
            gate=GateInfo(
                gate_key="occupation-regulation",
                kind=GateKind.LEGAL_PRACTICE,
                modelled=False,
                label=f"Registration to practise as {occupation.label} (not yet modelled)",
                issuing_body=None,
                jurisdiction=JURISDICTION,
                verification=None,
                acceptable_proof=[],
            ),
            uncertainty=[Uncertainty.REGULATION_NOT_MODELLED],
        )
    ]


def find_pack_target(
    title: str, pack: Pack, reference: Reference, occupation: EscoSeed | None
) -> tuple[Target | None, Literal["title", "esco_crosswalk"] | None, PackTargetNote | None]:
    """The pack target with the same title; otherwise the one pack target whose crosswalk
    names the target's ESCO occupation. Several such targets are never guessed between."""
    key = title_key(title)
    by_title = next((t for t in pack.targets if title_key(t.title) == key), None)
    if by_title is not None:
        return by_title, "title", None
    if occupation is None:
        return None, None, None
    crosswalked = [
        t
        for t in pack.targets
        if (crosswalk := reference.crosswalk_for(t.target_id)) is not None
        and concept_id(crosswalk.esco_occupation) == occupation.concept_id
    ]
    if len(crosswalked) > 1:
        return None, None, PackTargetNote.AMBIGUOUS_CROSSWALK
    if not crosswalked:
        return None, None, None
    return crosswalked[0], "esco_crosswalk", None


def pick_occupation(
    title: str, *, chosen: uuid.UUID | None, matches: Sequence[LabelMatch]
) -> tuple[
    uuid.UUID | None, Literal["occupation_choice", "esco_label"] | None, OccupationNote | None
]:
    """A target's ESCO occupation. The person's own choice, read from its source, wins;
    otherwise the one occupation ESCO labels with the title; otherwise, where several do,
    the one whose preferred label is the title (as the product stores a choice). Two equal
    matches stay ambiguous: never guessed between."""
    if chosen is not None:
        return chosen, "occupation_choice", None
    labelled = {m.concept_id for m in matches if m.kind != "hidden"}
    if len(labelled) == 1:
        return next(iter(labelled)), "esco_label", None
    wanted = " ".join(title.casefold().split())
    preferred = {
        m.concept_id
        for m in matches
        if m.kind == "preferred" and " ".join(m.preferred_label.casefold().split()) == wanted
    }
    if len(preferred) == 1:
        return next(iter(preferred)), "esco_label", None
    return None, None, OccupationNote.AMBIGUOUS_LABEL if labelled else OccupationNote.NO_EXACT_LABEL


def _digest(prefix: str, payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}-{hashlib.sha256(text.encode()).hexdigest()[:VERSION_DIGITS]}"


def _versioned(matrix: Matrix) -> Matrix:
    content = matrix.model_dump(
        mode="json", exclude={"matrix_version", "definition_version", "edits"}
    )
    definition = [
        [
            r.row_id,
            r.kind.value,
            r.required_level,
            r.rubric.version_id if r.rubric else None,
            r.gate.kind.value if r.gate else None,
        ]
        for r in matrix.rows
        if r.required
    ]
    return matrix.model_copy(
        update={
            "matrix_version": _digest("m", content),
            "definition_version": _digest("d", {"target": matrix.target_key, "rows": definition}),
        }
    )


def apply_edits(matrix: Matrix, edits: Sequence[RowEdit]) -> Matrix:
    """The matrix with each edit applied in order, and its versions stamped. An edit whose
    row the sources no longer give is reported, never dropped silently."""
    current = _versioned(matrix)
    applied = list(matrix.edits)
    for edit in edits:
        rows = list(current.rows)
        index = next((i for i, r in enumerate(rows) if r.row_id == edit.row_id), None)
        if index is None:
            applied.append(AppliedEdit(**edit.model_dump(), status="row_missing"))
            continue
        rows[index] = _edited(rows[index], edit)
        current = _versioned(current.model_copy(update={"rows": rows}))
        recorded = edit.model_dump()
        recorded["to_matrix_version"] = edit.to_matrix_version or current.matrix_version
        recorded["to_definition_version"] = edit.to_definition_version or current.definition_version
        applied.append(AppliedEdit(**recorded, status="applied"))
    return current.model_copy(update={"edits": applied})


def _edited(row: MatrixRow, edit: RowEdit) -> MatrixRow:
    uncertainty = set(row.uncertainty)
    if edit.action == "challenge":
        uncertainty.add(Uncertainty.CHALLENGED)
        challenge = Challenge(
            reason=edit.reason, recorded_by=edit.recorded_by, recorded_at=edit.recorded_at
        )
        return row.model_copy(
            update={"challenges": [*row.challenges, challenge], "uncertainty": sorted(uncertainty)}
        )
    if row.gate is not None or edit.importance is None:
        return row  # a protected gate is never demoted, whatever was recorded
    if relaxes(row, edit.importance):
        uncertainty.add(Uncertainty.RELAXED_BY_PERSON)
    elif edit.importance in REQUIRED_IMPORTANCE:
        uncertainty.discard(Uncertainty.RELAXED_BY_PERSON)  # back in the definition
    uncertainty.add(Uncertainty.SET_BY_PERSON)
    return row.model_copy(
        update={"importance": edit.importance, "uncertainty": sorted(uncertainty)}
    )


def relaxes(row: MatrixRow, importance: Importance) -> bool:
    """Whether setting this importance takes an employer's requirement out of the target
    definition: allowed only with an explicit warning (spec section 8)."""
    return (
        row.employer_specific
        and row.importance in REQUIRED_IMPORTANCE
        and importance not in REQUIRED_IMPORTANCE
    )


def check_edit(
    matrix: Matrix, row_id: str, importance: Importance, *, warning_acknowledged: bool
) -> bool:
    """Whether setting a row's importance changes it; refuses what may not be done."""
    row = matrix.row(row_id)
    if row is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND,
            "That requirement is not in this matrix.",
            stage=ErrorStage.CAPABILITY,
        )
    if row.gate is not None and importance is not Importance.ESSENTIAL:
        raise CareerwrightError(
            ErrorCode.PROTECTED_GATE,
            "A legal or entry requirement can't be switched off. Challenge its source, or "
            "choose a different target.",
            stage=ErrorStage.CAPABILITY,
            details={"row_id": row_id, "gate": row.gate.kind.value},
        )
    if row.importance is importance:
        return False
    if relaxes(row, importance) and not warning_acknowledged:
        raise CareerwrightError(
            ErrorCode.CONFIRMATION_REQUIRED,
            "Employers ask for this. Confirm that your plan may not satisfy their postings.",
            stage=ErrorStage.CAPABILITY,
            details={
                "reason": "relaxes_employer_requirement",
                "postings": sorted({c.posting_id for c in row.citations}),
            },
        )
    return True
