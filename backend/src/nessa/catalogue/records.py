"""Records of the capability and catalogue module, as returned by its store."""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TaxonomyRelease:
    """The import manifest of the ESCO release held (TAX1-04)."""

    release_id: uuid.UUID
    dataset_id: str
    version: str
    language: str
    source_url: str
    sha256: str
    size_bytes: int
    native_code_version: str
    transformation_version: str
    licence: str
    attribution: str
    sample: bool
    isco_group_count: int
    occupation_count: int
    skill_count: int
    repeated_rows_collapsed: int
    imported_at: datetime


@dataclass(frozen=True)
class OccupationHit:
    concept_id: uuid.UUID
    preferred_label: str
    isco_code: str
    isco_label: str
    text_rank: float


@dataclass(frozen=True)
class LabelMatch:
    concept_id: uuid.UUID
    label: str | None  # None for a hidden label: it matched, but is not for display
    kind: str
    preferred_label: str
    isco_code: str
    isco_label: str


@dataclass(frozen=True)
class IscoGroupRef:
    code: str
    label: str


@dataclass(frozen=True)
class SkillRef:
    skill_id: uuid.UUID
    preferred_label: str
    skill_type: str | None
    relation: str


@dataclass(frozen=True)
class OccupationDetail:
    concept_id: uuid.UUID
    esco_uri: str
    esco_code: str
    preferred_label: str
    alternative_labels: tuple[str, ...]
    description: str
    regulated: bool | None
    isco_groups: tuple[IscoGroupRef, ...]  # ISCO-08 major group down to the unit group
    broader_concept_id: uuid.UUID | None
    skills: tuple[SkillRef, ...]


@dataclass(frozen=True)
class ProvisionalConcept:
    """A verified title outside ESCO: an internal concept with no ESCO URI or ISCO group."""

    concept_id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    source_ref_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
