"""API contract for the taxonomy, the English city list and provisional concepts."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from careerwright.api.interview_schemas import SupportNoteOut
from careerwright.api.schemas import ResponseModel
from careerwright.catalogue.places import (
    COUNTRY_CODE,
    LIST_LICENCE,
    LIST_RETRIEVED,
    LIST_SHA256,
    LIST_SOURCE_URL,
    SUBDIVISION_CODE,
    Place,
)
from careerwright.catalogue.records import (
    ConceptKind,
    IscoGroupRef,
    LabelMatch,
    OccupationDetail,
    OccupationHit,
    ProvisionalConcept,
    SkillRef,
    TaxonomyRelease,
    TitleMatch,
    UkGroup,
    UkTitle,
)
from careerwright.catalogue.taxonomy import OccupationSearch, TitleMatches


class SearchMatch(StrEnum):
    ALL = "all"  # every word (web-search syntax: quotes, "or", "-word")
    ANY = "any"  # any word, ranked by how many match: for broad task and interest queries


EscoKind = Literal[ConceptKind.ESCO]  # "esco": an occupation of the pinned ESCO release


class TaxonomyReleaseOut(ResponseModel):
    """The import manifest of the ESCO release in use (TAX1-04). Show `attribution` and
    `adaptation` wherever ESCO content appears (ESCO's two reuse conditions)."""

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
    adaptation: str = Field(description="How this import adapts the release: it is marked so.")
    sample: bool = Field(description="A reduced test copy: never the catalogue a person sees.")
    isco_group_count: int
    occupation_count: int
    skill_count: int
    repeated_rows_collapsed: int = Field(
        description="Concept rows the release repeats with only their modified date changed, "
        "imported once (part of the transformation)."
    )
    imported_at: datetime

    @classmethod
    def of(cls, release: TaxonomyRelease) -> "TaxonomyReleaseOut":
        return cls(
            dataset_id=release.dataset_id,
            version=release.version,
            language=release.language,
            source_url=release.source_url,
            sha256=release.sha256,
            size_bytes=release.size_bytes,
            native_code_version=release.native_code_version,
            transformation_version=release.transformation_version,
            licence=release.licence,
            attribution=release.attribution,
            adaptation=release.adaptation,
            sample=release.sample,
            isco_group_count=release.isco_group_count,
            occupation_count=release.occupation_count,
            skill_count=release.skill_count,
            repeated_rows_collapsed=release.repeated_rows_collapsed,
            imported_at=release.imported_at,
        )


class LabelMatchOut(ResponseModel):
    concept_id: uuid.UUID
    concept_kind: EscoKind
    label: str | None = Field(description="null when a hidden (search-only) label matched.")
    label_kind: str
    preferred_label: str
    isco_code: str
    isco_label: str

    @classmethod
    def of(cls, match: LabelMatch) -> "LabelMatchOut":
        return cls(
            concept_id=match.concept_id,
            concept_kind=ConceptKind.ESCO,
            label=match.label,
            label_kind=match.kind,
            preferred_label=match.preferred_label,
            isco_code=match.isco_code,
            isco_label=match.isco_label,
        )


class OccupationHitOut(ResponseModel):
    concept_id: uuid.UUID
    concept_kind: EscoKind
    preferred_label: str
    isco_code: str
    isco_label: str
    text_rank: float = Field(description="PostgreSQL ts_rank_cd; orders this result only.")

    @classmethod
    def of(cls, hit: OccupationHit) -> "OccupationHitOut":
        return cls(
            concept_id=hit.concept_id,
            concept_kind=ConceptKind.ESCO,
            preferred_label=hit.preferred_label,
            isco_code=hit.isco_code,
            isco_label=hit.isco_label,
            text_rank=hit.text_rank,
        )


class OccupationSearchOut(ResponseModel):
    """Exact label matches (all of them, when several occupations share a label), then
    ranked full-text matches. `full_text_total` counts every other full-text match, so a
    limited page is never mistaken for the whole result."""

    release: TaxonomyReleaseOut
    match: SearchMatch
    label_matches: list[LabelMatchOut]
    full_text: list[OccupationHitOut]
    full_text_total: int | None = Field(
        description="null: full-text search did not run (the query has no searchable word "
        "but matched a label), which is not the same as no match."
    )
    limit: int

    @classmethod
    def of(cls, search: OccupationSearch) -> "OccupationSearchOut":
        return cls(
            release=TaxonomyReleaseOut.of(search.release),
            match=SearchMatch.ANY if search.any_word else SearchMatch.ALL,
            label_matches=[LabelMatchOut.of(m) for m in search.label_matches],
            full_text=[OccupationHitOut.of(h) for h in search.full_text],
            full_text_total=search.full_text_total,
            limit=search.limit,
        )


class IscoGroupOut(ResponseModel):
    code: str
    label: str

    @classmethod
    def of(cls, group: IscoGroupRef) -> "IscoGroupOut":
        return cls(code=group.code, label=group.label)


class TitleMatchOut(ResponseModel):
    source: Literal["esco"] = Field(description="An occupation of the pinned ESCO release.")
    concept_id: uuid.UUID
    concept_kind: EscoKind
    title: str = Field(description="The occupation's ESCO title (its preferred label).")
    matched_label: str = Field(description="The label that matched what was typed.")
    label_kind: Literal["preferred", "alternative"]
    isco_group: IscoGroupOut = Field(description="Its ISCO-08 unit group.")

    @classmethod
    def of(cls, match: TitleMatch) -> "TitleMatchOut":
        return cls(
            source="esco",
            concept_id=match.concept_id,
            concept_kind=ConceptKind.ESCO,
            title=match.preferred_label,
            matched_label=match.label,
            label_kind="preferred" if match.kind == "preferred" else "alternative",
            isco_group=IscoGroupOut(code=match.isco_code, label=match.isco_label),
        )


class UkGroupOut(ResponseModel):
    code: str = Field(description="An ISCO-08 unit group, as the UK job-title index codes it.")
    label: str | None = Field(
        description="The held ESCO release's name for the group; null: it names none."
    )

    @classmethod
    def of(cls, group: UkGroup) -> "UkGroupOut":
        return cls(code=group.code, label=group.label)


class UkTitleOut(ResponseModel):
    """A UK job title the pinned ONS SOC 2020 coding index lists (ADR 0015): mark it "UK job
    title (ONS)". Picked, it stays the person's words (`POST .../origin/role/title`)."""

    source: Literal["uk_title_index"] = Field(description="A title of the UK job-title index.")
    title: str = Field(description="As the index writes it.")
    soc_codes: list[str] = Field(description="Every SOC 2020 unit group ONS codes it to.")
    isco_groups: list[UkGroupOut] = Field(
        description="Every ISCO-08 unit group ONS codes it to, none picked."
    )

    @classmethod
    def of(cls, title: UkTitle) -> "UkTitleOut":
        return cls(
            source="uk_title_index",
            title=title.title,
            soc_codes=list(title.soc_codes),
            isco_groups=[UkGroupOut.of(g) for g in title.isco_groups],
        )


TitleOption = Annotated[TitleMatchOut | UkTitleOut, Field(discriminator="source")]


class TitleMatchesOut(ResponseModel):
    """The first question's type-ahead: occupations whose ESCO titles (preferred and
    alternative labels) have a word beginning with each word typed, one per occupation, and
    the UK job-title index's titles that do (ONS's SOC 2020 coding index, other than titles
    ESCO itself offers), best first: what was typed, then a title beginning with it, then the
    rest, ESCO first on ties. When neither holds a title with every word, the ESCO occupations
    whose titles hold the most of them, with `partial` true. Deterministic, no model call. No
    match is an honest empty list: nothing is invented, and the person's own words are always
    theirs to keep (`POST .../origin/role/title`). `total` counts every ESCO occupation that
    matched, `uk_total` every title of the index."""

    release: TaxonomyReleaseOut
    query: str | None = Field(
        description="What was searched, its spaces collapsed; null when the support screen "
        "answered, since what was typed is never returned."
    )
    matches: list[TitleOption]
    total: int
    uk_total: int
    limit: int
    partial: bool = Field(
        description="True: neither ESCO nor the UK job-title index lists a title with every word "
        "typed, and these ESCO occupations hold the most of them, rarer words first. Ask "
        '"Careerwright couldn\'t match that title in ESCO. Is it one of these?", with "None of '
        "these is my job\", which keeps the person's own words: the person chooses one or "
        "none, and nothing is joined to the typed words."
    )
    support_note: SupportNoteOut | None = Field(
        description="The calm support panel, when what was typed triggers the support screen "
        "(`careerwright.profile.safety`), as a message does: then nothing is matched, nothing "
        "is offered in those words, and nothing about it is kept. Null otherwise."
    )

    @classmethod
    def of(cls, found: TitleMatches) -> "TitleMatchesOut":
        return cls(
            release=TaxonomyReleaseOut.of(found.release),
            query=found.query,
            matches=[
                TitleMatchOut.of(o) if isinstance(o, TitleMatch) else UkTitleOut.of(o)
                for o in found.options
            ],
            total=found.total,
            uk_total=found.uk_total,
            limit=found.limit,
            partial=found.partial,
            support_note=None,
        )

    @classmethod
    def screened(cls, release: TaxonomyRelease, limit: int) -> "TitleMatchesOut":
        """What was typed triggers the support screen: no match, and the panel. The words are
        not returned (`CLAUDE.md`: never echo request input); only the fact is."""
        return cls(
            release=TaxonomyReleaseOut.of(release),
            query=None,
            matches=[],
            total=0,
            uk_total=0,
            limit=limit,
            partial=False,
            support_note=SupportNoteOut.beside_a_title(),
        )


class SkillRefOut(ResponseModel):
    skill_id: uuid.UUID
    preferred_label: str
    skill_type: str | None
    relation: str = Field(description="essential or optional (ESCO's occupation-skill link).")

    @classmethod
    def of(cls, skill: SkillRef) -> "SkillRefOut":
        return cls(
            skill_id=skill.skill_id,
            preferred_label=skill.preferred_label,
            skill_type=skill.skill_type,
            relation=skill.relation,
        )


class OccupationOut(ResponseModel):
    concept_id: uuid.UUID = Field(
        description="Careerwright's internal concept ID (stable per URI)."
    )
    concept_kind: EscoKind
    esco_uri: str
    esco_code: str
    preferred_label: str
    alternative_labels: list[str]
    description: str
    regulated: bool | None = Field(description="null: ESCO records no regulation note.")
    isco_groups: list[IscoGroupOut] = Field(
        description="ISCO-08 from the major group down to the unit group (the grouping pivot)."
    )
    broader_concept_id: uuid.UUID | None
    skills: list[SkillRefOut]
    attribution: str
    adaptation: str

    @classmethod
    def of(cls, detail: OccupationDetail, release: TaxonomyRelease) -> "OccupationOut":
        return cls(
            concept_id=detail.concept_id,
            concept_kind=ConceptKind.ESCO,
            esco_uri=detail.esco_uri,
            esco_code=detail.esco_code,
            preferred_label=detail.preferred_label,
            alternative_labels=list(detail.alternative_labels),
            description=detail.description,
            regulated=detail.regulated,
            isco_groups=[IscoGroupOut.of(g) for g in detail.isco_groups],
            broader_concept_id=detail.broader_concept_id,
            skills=[SkillRefOut.of(s) for s in detail.skills],
            attribution=release.attribution,
            adaptation=release.adaptation,
        )


class PlaceOut(ResponseModel):
    place_id: str
    label: str
    aliases: list[str]
    country_code: str
    subdivision_code: str
    region_code: str = Field(description="ONS region (E12) code.")
    region: str
    timezone: str

    @classmethod
    def of(cls, place: Place) -> "PlaceOut":
        return cls(
            place_id=place.place_id,
            label=place.label,
            aliases=list(place.aliases),
            country_code=place.country_code,
            subdivision_code=place.subdivision_code,
            region_code=place.region_code,
            region=place.region,
            timezone=place.timezone,
        )


class PlaceList(ResponseModel):
    """The finite list of English cities a work area can name. A city is geography only:
    it never implies residence or the right to work."""

    country_code: str = COUNTRY_CODE
    subdivision_code: str = SUBDIVISION_CODE
    source_url: str = LIST_SOURCE_URL
    retrieved: str = LIST_RETRIEVED
    source_sha256: str = LIST_SHA256
    licence: str = LIST_LICENCE
    items: list[PlaceOut]


class ProvisionalConceptOut(ResponseModel):
    """A title the person confirmed that Careerwright couldn't match in ESCO: no ESCO URI, no
    ISCO group."""

    concept_id: uuid.UUID
    concept_kind: Literal[ConceptKind.PROVISIONAL] = Field(
        description="provisional: Careerwright's own concept for a verified title, never an ESCO "
        "one."
    )
    title: str
    source_ref_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    @classmethod
    def of(cls, concept: ProvisionalConcept) -> "ProvisionalConceptOut":
        return cls(
            concept_id=concept.concept_id,
            concept_kind=ConceptKind.PROVISIONAL,
            title=concept.title,
            source_ref_id=concept.source_ref_id,
            created_by=concept.created_by,
            created_at=concept.created_at,
        )


class ProvisionalConceptPage(ResponseModel):
    items: list[ProvisionalConceptOut]
    next_cursor: str | None
