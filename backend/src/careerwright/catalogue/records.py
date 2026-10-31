"""Records of the capability and catalogue module, as returned by its store."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ConceptKind(StrEnum):
    """Which kind of occupation concept an ID names (spec section 4: a suggestion holds a
    canonical concept or a provisional concept)."""

    ESCO = "esco"  # an occupation of the pinned ESCO release
    PROVISIONAL = "provisional"  # a title a person verified that ESCO does not hold


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
    adaptation: str  # how this import adapts the release (ESCO's second reuse condition)
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
class SkillReach:
    """An occupation a search reached through one of its essential skills: the one whose
    preferred label matches the search best."""

    concept_id: uuid.UUID
    skill_id: uuid.UUID
    skill_label: str
    text_rank: float  # that label's rank for the search


@dataclass(frozen=True)
class LabelMatch:
    concept_id: uuid.UUID
    label: str | None  # None for a hidden label: it matched, but is not for display
    kind: str
    preferred_label: str
    isco_code: str
    isco_label: str


@dataclass(frozen=True)
class TitleMatch:
    """An occupation whose preferred or alternative label matches what the person typed:
    the label that matched best, and the occupation's own title."""

    concept_id: uuid.UUID
    label: str
    kind: str  # preferred or alternative (hidden labels are never offered)
    preferred_label: str
    isco_code: str
    isco_label: str


@dataclass(frozen=True)
class SkillNeighbour:
    """An occupation sharing essential skills with another's (ESCO)."""

    concept_id: uuid.UUID
    shared: int  # essential skills both have
    essential: int  # its own essential skills


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
class OccupationFacts:
    """What discovery shows about an occupation: its ESCO identity, its ISCO-08 unit, minor
    (family) and major (sector) groups, and its essential skills (the first few, and how
    many there are)."""

    concept_id: uuid.UUID
    preferred_label: str
    esco_uri: str
    esco_code: str
    description: str
    regulated: bool | None
    unit: IscoGroupRef
    family: IscoGroupRef
    sector: IscoGroupRef
    preferred_key: str  # the preferred label as `careerwright.concept_key`
    label_keys: frozenset[str]  # non-hidden labels as `careerwright.concept_key`
    essential_skills: tuple[str, ...]
    essential_skill_count: int


@dataclass(frozen=True)
class ProvisionalConcept:
    """A verified title outside ESCO: an internal concept with no ESCO URI or ISCO group."""

    concept_id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    source_ref_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
