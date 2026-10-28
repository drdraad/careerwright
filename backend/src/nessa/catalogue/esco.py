"""The pinned ESCO release and its parser (spec section 5, TAX-1; ruling R7).

ESCO is not committed: `make setup` fetches the release below and checks its size and
SHA-256, and the import reads it only after checking them again. Parsing turns the CSV
package into typed records and refuses anything that does not match the documented
structure (spec section 5: the manifest records release, URL, licence, hash, native code
version and transformation version). It assigns each ESCO occupation a stable internal
concept ID derived from its URI, so specialist occupations in one ISCO-08 group stay
distinct (ISCO is the grouping pivot, not the identity; TAX1-01).

Licence (https://esco.ec.europa.eu/en/about-esco/faq, checked 2026-10-28): reuse is free
under Commission Decision 2011/833/EU, on condition that the service acknowledges ESCO with
the statement below and marks any modified or adapted version as such.
"""

import csv
import hashlib
import io
import re
import uuid
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

# Transformation: 6 of the release's 19 CSV files (ISCO groups, occupations, skills,
# occupation-skill and skill-skill relations, the occupation hierarchy; left out: skill
# groups, the skills hierarchy and skill-pillar broader relations, the seven collections, the
# dictionary, concept schemes and the green share of occupations); released concepts only;
# labels trimmed and de-duplicated per concept (case- and space-insensitively); concept
# rows repeated with only `modifiedDate` changed collapsed to the latest; internal IDs
# derived from URIs; full-text vectors built at import.
TRANSFORMATION_VERSION = "nessa-esco-import-1"
ATTRIBUTION = "This service uses the ESCO classification of the European Commission."
# ESCO's second reuse condition: an adapted version is marked as such, wherever it is shown.
ADAPTATION = (
    "Adapted from ESCO: Nessa imports occupations, skills, their relations and ISCO-08 "
    "groups only (not skill groups, the skill hierarchy, collections, the dictionary or "
    "green-share data), with labels trimmed and de-duplicated and repeated rows merged "
    f"(transformation {TRANSFORMATION_VERSION}). It is not the official ESCO release."
)
LICENCE = (
    "Commission Decision 2011/833/EU on the reuse of Commission documents: free reuse with "
    "the ESCO acknowledgement; modified or adapted versions must be marked as such"
)
# Internal concept and skill IDs are UUIDv5 of the ESCO URI in this namespace: stable across
# re-imports, and never confused with a provisional concept (random UUIDv4).
CONCEPT_NAMESPACE = uuid.UUID("2b8c7e14-1f0a-4d7e-9a3c-5e6f70819a2b")
MAX_RELEASE_BYTES = 64 * 1024 * 1024
MAX_LABEL = 200
MAX_TEXT = 4000


@dataclass(frozen=True)
class ReleasePin:
    """One exact ESCO package: where it comes from and the bytes it must be."""

    dataset_id: str
    version: str
    language: str
    url: str
    file_name: str
    sha256: str
    size_bytes: int
    native_code_version: str
    sample: bool = False


ESCO_RELEASE = ReleasePin(
    dataset_id="esco-v1.2.1-en-csv",
    version="v1.2.1",
    language="en",
    url=(
        "https://ec.europa.eu/esco/download/"
        "ESCO%20dataset%20-%20v1.2.1%20-%20classification%20-%20en%20-%20csv.zip"
    ),
    file_name="esco-v1.2.1-classification-en-csv.zip",
    sha256="f9761b0b52be1828b38a3e5e0ae59a93a7b0ce358bc800f52f57a8b002adeb3e",
    size_bytes=10_045_670,
    native_code_version="ESCO v1.2.1 (occupations grouped by ISCO-08)",
)


class ReleaseIntegrityError(ValueError):
    """The file is not the pinned release, or its contents do not have ESCO's structure."""


class LabelKind(StrEnum):
    PREFERRED = "preferred"
    ALTERNATIVE = "alternative"
    HIDDEN = "hidden"  # for search only, never displayed (SKOS hiddenLabel)


class Relation(StrEnum):
    ESSENTIAL = "essential"
    OPTIONAL = "optional"


@dataclass(frozen=True)
class Label:
    text: str
    kind: LabelKind

    @property
    def normalised(self) -> str:
        return normalise_label(self.text)


@dataclass(frozen=True)
class IscoGroup:
    code: str
    uri: str
    label: str

    @property
    def broader_code(self) -> str | None:
        return self.code[:-1] or None


@dataclass(frozen=True)
class Occupation:
    concept_id: uuid.UUID
    uri: str
    isco_code: str
    esco_code: str
    labels: tuple[Label, ...]
    description: str
    regulated: bool | None  # None: ESCO records no regulation note

    @property
    def preferred_label(self) -> str:
        return next(label.text for label in self.labels if label.kind is LabelKind.PREFERRED)


@dataclass(frozen=True)
class Skill:
    skill_id: uuid.UUID
    uri: str
    skill_type: str | None  # "skill/competence" or "knowledge"; a few ESCO skills have none
    reuse_level: str | None
    labels: tuple[Label, ...]
    description: str


@dataclass(frozen=True)
class OccupationSkill:
    concept_id: uuid.UUID
    skill_id: uuid.UUID
    relation: Relation


@dataclass(frozen=True)
class SkillRelation:
    skill_id: uuid.UUID
    related_skill_id: uuid.UUID
    relation: Relation


@dataclass(frozen=True)
class Broader:
    """An occupation's parent: another (more general) ESCO occupation, or an ISCO group."""

    concept_id: uuid.UUID
    broader_concept_id: uuid.UUID | None
    broader_isco_code: str | None


@dataclass(frozen=True)
class EscoCatalogue:
    pin: ReleasePin
    isco_groups: tuple[IscoGroup, ...]
    occupations: tuple[Occupation, ...]
    skills: tuple[Skill, ...]
    occupation_skills: tuple[OccupationSkill, ...]
    skill_relations: tuple[SkillRelation, ...]
    broader: tuple[Broader, ...]
    repeated_rows_collapsed: int  # concept rows repeated with only `modifiedDate` changed


def normalise_label(text: str) -> str:
    """The form used for alias lookup: case-folded, single-spaced."""
    return " ".join(text.casefold().split())


def concept_id(uri: str) -> uuid.UUID:
    return uuid.uuid5(CONCEPT_NAMESPACE, uri)


def read_verified(path: Path, pin: ReleasePin) -> bytes:
    """The release's bytes, only if they are exactly the pinned file."""
    if not path.is_file():
        raise ReleaseIntegrityError(f"{pin.dataset_id} is not at {path}; run `make setup`")
    size = path.stat().st_size
    if size != pin.size_bytes or size > MAX_RELEASE_BYTES:
        raise ReleaseIntegrityError(f"{path.name} is {size} bytes, not {pin.size_bytes}")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != pin.sha256:
        raise ReleaseIntegrityError(f"{path.name} has SHA-256 {digest}, not {pin.sha256}")
    return data


_OCCUPATION_URI = re.compile(r"^http://data\.europa\.eu/esco/occupation/[0-9a-f-]{36}$")
_SKILL_URI = re.compile(r"^http://data\.europa\.eu/esco/skill/[0-9a-f-]{36}$")
_ISCO_URI = re.compile(r"^http://data\.europa\.eu/esco/isco/C(?P<code>[0-9]{1,4})$")
_REGULATED = "http://data.europa.eu/esco/regulated-professions/"


def _rows(archive: zipfile.ZipFile, name: str, columns: set[str]) -> Iterator[dict[str, str]]:
    try:
        raw = archive.read(name)
    except KeyError:
        raise ReleaseIntegrityError(f"the release has no {name}") from None
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
    missing = columns - set(reader.fieldnames or ())
    if missing:
        raise ReleaseIntegrityError(f"{name} lacks columns {sorted(missing)}")
    yield from reader


def _concept_rows(
    archive: zipfile.ZipFile, name: str, columns: set[str]
) -> tuple[list[dict[str, str]], int]:
    """One row per concept URI, and how many repeated rows were collapsed. ESCO v1.2.1 lists
    a few concepts twice, identical but for `modifiedDate`; such a repeat is collapsed (the
    later date kept). A repeat that differs in anything else is conflicting data: refused."""
    kept: dict[str, dict[str, str]] = {}
    collapsed = 0
    for row in _rows(archive, name, columns | {"modifiedDate"}):
        uri = row["conceptUri"]
        first = kept.get(uri)
        if first is None:
            kept[uri] = row
            continue
        if {k: v for k, v in first.items() if k != "modifiedDate"} != {
            k: v for k, v in row.items() if k != "modifiedDate"
        }:
            raise ReleaseIntegrityError(f"{name} lists {uri[-36:]} twice with different content")
        if row["modifiedDate"] > first["modifiedDate"]:
            kept[uri] = row
        collapsed += 1
    return list(kept.values()), collapsed


def _text(value: str, *, limit: int, what: str) -> str:
    text = value.strip()
    if len(text) > limit:
        raise ReleaseIntegrityError(f"a {what} is longer than {limit} characters")
    return text


def _labels(row: dict[str, str]) -> tuple[Label, ...]:
    preferred = _text(row["preferredLabel"], limit=MAX_LABEL, what="label")
    if not preferred:
        raise ReleaseIntegrityError("a concept has no preferred label")
    labels = [Label(preferred, LabelKind.PREFERRED)]
    seen = {normalise_label(preferred)}
    for column, kind in (("altLabels", LabelKind.ALTERNATIVE), ("hiddenLabels", LabelKind.HIDDEN)):
        for line in row[column].split("\n"):
            text = _text(line, limit=MAX_LABEL, what="label")
            if text and normalise_label(text) not in seen:
                seen.add(normalise_label(text))
                labels.append(Label(text, kind))
    return tuple(labels)


def _match(pattern: re.Pattern[str], value: str, what: str) -> re.Match[str]:
    match = pattern.match(value)
    if match is None:
        raise ReleaseIntegrityError(f"unexpected {what} URI {value[:80]!r}")
    return match


def _isco_groups(archive: zipfile.ZipFile) -> tuple[IscoGroup, ...]:
    groups = []
    for row in _rows(archive, "ISCOGroups_en.csv", {"conceptUri", "code", "preferredLabel"}):
        code = _match(_ISCO_URI, row["conceptUri"], "ISCO group").group("code")
        if row["code"] != code:
            raise ReleaseIntegrityError(f"ISCO group {code} has code {row['code']!r}")
        groups.append(
            IscoGroup(
                code, row["conceptUri"], _text(row["preferredLabel"], limit=MAX_LABEL, what="label")
            )
        )
    return tuple(groups)


def _occupations(archive: zipfile.ZipFile, isco: set[str]) -> tuple[tuple[Occupation, ...], int]:
    columns = {"conceptUri", "iscoGroup", "preferredLabel", "altLabels", "hiddenLabels",
               "status", "regulatedProfessionNote", "description", "code"}  # fmt: skip
    occupations = []
    rows, collapsed = _concept_rows(archive, "occupations_en.csv", columns)
    for row in rows:
        _match(_OCCUPATION_URI, row["conceptUri"], "occupation")
        if row["status"] != "released":
            continue  # ESCO's CSV holds released concepts; anything else is not imported
        if row["iscoGroup"] not in isco or len(row["iscoGroup"]) != 4:
            raise ReleaseIntegrityError(f"an occupation names ISCO group {row['iscoGroup']!r}")
        note = row["regulatedProfessionNote"].strip()
        occupations.append(
            Occupation(
                concept_id=concept_id(row["conceptUri"]),
                uri=row["conceptUri"],
                isco_code=row["iscoGroup"],
                esco_code=_text(row["code"], limit=40, what="code"),
                labels=_labels(row),
                description=_text(row["description"], limit=MAX_TEXT, what="description"),
                regulated=None if not note.startswith(_REGULATED) else note.endswith("/regulated"),
            )
        )
    return tuple(occupations), collapsed


def _skills(archive: zipfile.ZipFile) -> tuple[tuple[Skill, ...], int]:
    columns = {"conceptUri", "skillType", "reuseLevel", "preferredLabel", "altLabels",
               "hiddenLabels", "status", "description"}  # fmt: skip
    skills = []
    rows, collapsed = _concept_rows(archive, "skills_en.csv", columns)
    for row in rows:
        _match(_SKILL_URI, row["conceptUri"], "skill")
        if row["status"] != "released":
            continue
        skills.append(
            Skill(
                skill_id=concept_id(row["conceptUri"]),
                uri=row["conceptUri"],
                skill_type=row["skillType"].strip() or None,
                reuse_level=row["reuseLevel"].strip() or None,
                labels=_labels(row),
                description=_text(row["description"], limit=MAX_TEXT, what="description"),
            )
        )
    return tuple(skills), collapsed


def _relation(value: str) -> Relation:
    try:
        return Relation(value)
    except ValueError:
        raise ReleaseIntegrityError(f"unexpected relation type {value[:40]!r}") from None


def _occupation_skills(
    archive: zipfile.ZipFile, occupations: set[str], skills: set[str]
) -> tuple[OccupationSkill, ...]:
    relations = []
    for row in _rows(
        archive, "occupationSkillRelations_en.csv", {"occupationUri", "relationType", "skillUri"}
    ):
        if row["occupationUri"] not in occupations or row["skillUri"] not in skills:
            raise ReleaseIntegrityError("an occupation-skill relation names an unknown concept")
        relations.append(
            OccupationSkill(
                concept_id(row["occupationUri"]),
                concept_id(row["skillUri"]),
                _relation(row["relationType"]),
            )
        )
    return tuple(relations)


def _skill_relations(archive: zipfile.ZipFile, skills: set[str]) -> tuple[SkillRelation, ...]:
    relations = []
    for row in _rows(
        archive,
        "skillSkillRelations_en.csv",
        {"originalSkillUri", "relationType", "relatedSkillUri"},
    ):
        if row["originalSkillUri"] not in skills or row["relatedSkillUri"] not in skills:
            raise ReleaseIntegrityError("a skill-skill relation names an unknown skill")
        relations.append(
            SkillRelation(
                concept_id(row["originalSkillUri"]),
                concept_id(row["relatedSkillUri"]),
                _relation(row["relationType"]),
            )
        )
    return tuple(relations)


def _broader(
    archive: zipfile.ZipFile, occupations: set[str], isco: set[str]
) -> tuple[Broader, ...]:
    parents = []
    for row in _rows(
        archive, "broaderRelationsOccPillar_en.csv", {"conceptType", "conceptUri", "broaderUri"}
    ):
        if row["conceptType"] != "Occupation":
            continue  # ISCO's own hierarchy is implied by its codes
        if row["conceptUri"] not in occupations:
            raise ReleaseIntegrityError("a broader relation names an unknown occupation")
        broader = row["broaderUri"]
        if broader in occupations:
            parents.append(Broader(concept_id(row["conceptUri"]), concept_id(broader), None))
            continue
        code = _match(_ISCO_URI, broader, "broader").group("code")
        if code not in isco:
            raise ReleaseIntegrityError(f"a broader relation names ISCO group {code}")
        parents.append(Broader(concept_id(row["conceptUri"]), None, code))
    return tuple(parents)


def parse_release(data: bytes, pin: ReleasePin) -> EscoCatalogue:
    """The release as typed records. `data` must already be verified (`read_verified`)."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ReleaseIntegrityError(f"{pin.file_name} is not a zip archive") from None
    with archive:
        isco = _isco_groups(archive)
        isco_codes = {group.code for group in isco}
        occupations, repeated_occupations = _occupations(archive, isco_codes)
        skills, repeated_skills = _skills(archive)
        occupation_uris = {o.uri for o in occupations}
        skill_uris = {s.uri for s in skills}
        return EscoCatalogue(
            pin=pin,
            isco_groups=isco,
            occupations=occupations,
            skills=skills,
            occupation_skills=_occupation_skills(archive, occupation_uris, skill_uris),
            skill_relations=_skill_relations(archive, skill_uris),
            broader=_broader(archive, occupation_uris, isco_codes),
            repeated_rows_collapsed=repeated_occupations + repeated_skills,
        )


def label_rows(
    owners: Iterable[Occupation | Skill],
) -> Iterator[tuple[uuid.UUID, str, LabelKind, str]]:
    """(owner ID, label, kind, normalised) for every label of `owners`."""
    for owner in owners:
        owner_id = owner.concept_id if isinstance(owner, Occupation) else owner.skill_id
        for label in owner.labels:
            yield owner_id, label.text, label.kind, label.normalised
