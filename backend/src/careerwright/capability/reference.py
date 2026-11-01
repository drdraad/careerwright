"""The capability reference: what this module adds to the option pack's pack-local rows
(ADR 0011 decision 10; ADR 0012). Pure: no SQL, no network, no model.

The pack's requirement rows (`pack:<target>:<row>`) carry a label and a kind, and their
outcomes have no level, because no rubric existed (Task 7b). This reference gives each skill
row a role-specific rubric (an observable task, five behavioural anchors for levels 0-4, a
proposed required level, acceptable proof and prerequisites) and an ESCO skill crosswalk; it
types each gate the pack's postings name (legal practice, recognition, admission or
eligibility: spec section 8, "Protected gates cannot be toggled away"); and it crosswalks each
pack target to an ESCO occupation, the seed of that target's matrix.

Everything here was written by an agent (Task 9) and is `proposed`: a rubric is a proposed
rubric level, not an equal-interval measurement, and no reviewed status is inherited (spec
section 8, "M0 matrices must not inherit that process's reviewed status"). The domain
review is not run - requires human. A version is committed beside this module and pinned by
the SHA-256 of its bytes, like the option pack: a change is a new version.

The loader also checks the pack references the capability model reads and the pack's own
validator does not (Task 7b M3, dispatch ruling 4): option targets, skill-row targets, a
requirement's target against its posting's, and the sources postings and options name.
"""

import hashlib
import json
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from careerwright.catalogue.option_pack import Pack, SourceKind

# The format's name from before the product was renamed: the pinned versions carry it, so it
# stays as written.
REFERENCE_NAME = "nessa-capability-reference"
FORMAT_VERSION = 1
REFERENCE_DIR = Path(__file__).parent / "reference"
# Every committed version, pinned by the SHA-256 of its file's bytes. 0.2.0 carries 0.1.0's
# rubrics and gates unchanged to the reviewed option pack 0.2.0, with session 2's answers on
# them recorded (R1-R40, Task 7c).
PINS: dict[str, str] = {
    "0.1.0": "906b4e9670bd930213c8a9a6d95c78af342e1fd1b2023e5a68d8902d911bb640",
    "0.2.0": "2df1c70d156ee036c990be688b9722dea496a6a699d76ce0e16ac82b01c72e86",
}
ESCO_OCCUPATION_URI = r"^http://data\.europa\.eu/esco/occupation/[0-9a-f-]{36}$"
ESCO_SKILL_URI = r"^http://data\.europa\.eu/esco/skill/[0-9a-f-]{36}$"
LEVELS = (0, 1, 2, 3, 4)

Level = Annotated[int, Field(ge=0, le=4)]
Text = Annotated[str, Field(min_length=1, max_length=400)]


class ReferenceError(ValueError):
    """A reference that does not parse, fails its checks, or is not its pinned bytes."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GateKind(StrEnum):
    """The protected gate types (spec section 8): a preference toggle never removes one."""

    LEGAL_PRACTICE = "legal_practice"  # a legal right to practise: statutory registration
    RECOGNITION = "recognition"  # recognition of a credential gained elsewhere
    ADMISSION = "admission"  # a confirmed admission requirement
    ELIGIBILITY = "eligibility"  # a confirmed eligibility rule: the right to work


class TargetCrosswalk(StrictModel):
    """The ESCO occupation a pack target's matrix is seeded from (proposed)."""

    target_id: str
    esco_occupation: str = Field(pattern=ESCO_OCCUPATION_URI)
    esco_label: Text
    note: Text | None = None


class Rubric(StrictModel):
    """A role-specific rubric for one pack row: proposed rubric levels, not measurements."""

    skill_id: str = Field(pattern=r"^pack:[a-z0-9-]+:[a-z0-9-]+$")
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    observable_task: Text
    required_level: int = Field(ge=1, le=4)
    # 0 no evidence of performance; 1 performs with guidance; 2 independently handles
    # routine tasks; 3 handles complex or non-routine tasks; 4 designs or leads and can
    # justify trade-offs (spec section 8). Unknown is not a level.
    anchors: dict[Level, Text]
    acceptable_proof: Annotated[list[Text], Field(min_length=1)]
    prerequisites: list[str] = Field(default_factory=list)  # other rows of its target
    esco_skill: str | None = Field(default=None, pattern=ESCO_SKILL_URI)
    esco_label: Text | None = None
    note: Text | None = None

    @property
    def version_id(self) -> str:
        """What evidence and outcomes cite: a level means something only against these
        anchors, so evidence is never reused for another rubric's level."""
        return f"{self.skill_id}@{self.version}"


class Gate(StrictModel):
    """A typed protected gate: never a skill level, never satisfied by course levels."""

    gate_key: str = Field(pattern=r"^[a-z0-9-]+$")
    kind: GateKind
    label: Text
    issuing_body: Text
    jurisdiction: Literal["GB", "GB-ENG"]
    verification: Text  # how the person verifies it: an unverified gate stays unresolved
    acceptable_proof: Annotated[list[Text], Field(min_length=1)]
    pack_rows: list[str] = Field(default_factory=list)  # pack credential rows it types
    gate_words: list[str] = Field(default_factory=list)  # a requirement's `gate` words


class Reference(StrictModel):
    reference: Literal["nessa-capability-reference"]
    format_version: Literal[1]
    reference_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    dated: date
    pack_version: str  # the option pack version it was written for
    esco_release: str  # the ESCO release its crosswalks name
    review_state: Literal["proposed", "reviewed"]
    label_review: Text
    notes: list[str]
    targets: list[TargetCrosswalk]
    rubrics: list[Rubric]
    gates: list[Gate]

    def rubric_for(self, skill_id: str) -> Rubric | None:
        return next((r for r in self.rubrics if r.skill_id == skill_id), None)

    def gate_for_row(self, skill_id: str) -> Gate | None:
        return next((g for g in self.gates if skill_id in g.pack_rows), None)

    def gate_for_words(self, words: str) -> Gate | None:
        return next((g for g in self.gates if words in g.gate_words), None)

    def crosswalk_for(self, target_id: str) -> TargetCrosswalk | None:
        return next((t for t in self.targets if t.target_id == target_id), None)


def parse_reference(data: object) -> Reference:
    try:
        return Reference.model_validate(data)
    except ValidationError as error:
        first = error.errors()[0]
        where = ".".join(str(part) for part in first["loc"])
        raise ReferenceError(f"{where}: {first['msg']}") from None


def check_reference(reference: Reference, pack: Pack) -> list[str]:
    """Every problem, each named; an empty list is a reference that fits its pack."""
    found: list[str] = []
    if reference.pack_version != pack.pack_version:
        found.append(f"written for option pack {reference.pack_version}, not {pack.pack_version}")
    found += _pack_references(pack)
    found += _targets(reference, pack)
    found += _rubrics(reference, pack)
    found += _gates(reference, pack)
    return found


def _pack_references(pack: Pack) -> list[str]:
    """The references this module reads that the pack's own validator leaves unchecked."""
    found: list[str] = []
    targets = {t.target_id for t in pack.targets}
    sources = {s.source_id: s.kind for s in pack.sources}
    postings = {p.record_id: p for p in pack.job_postings}
    for skill in pack.skills:
        if skill.target_id not in targets:
            found.append(f"{skill.skill_id} names target {skill.target_id}, not a pack target")
        elif not skill.skill_id.startswith(f"pack:{skill.target_id}:"):
            found.append(f"{skill.skill_id} is not named for its target {skill.target_id}")
    for option in pack.learning_options:
        found += [
            f"{option.record_id} names target {t}, not a pack target"
            for t in option.target_ids
            if t not in targets
        ]
        if sources.get(option.source_id) is not SourceKind.COURSE_PAGE:
            found.append(f"{option.record_id} names {option.source_id}, not a course page")
    for posting in pack.job_postings:
        if sources.get(posting.source_id) is not SourceKind.JOB_POSTING:
            found.append(f"{posting.record_id} names {posting.source_id}, not a job posting")
    for requirement in pack.skill_requirements:
        owner = postings.get(requirement.job_posting_id)
        if owner is not None and requirement.target_id != owner.target_id:
            found.append(
                f"{requirement.record_id} is for {requirement.target_id}, but its posting "
                f"{owner.record_id} is for {owner.target_id}"
            )
    return found


def _targets(reference: Reference, pack: Pack) -> list[str]:
    targets = {t.target_id for t in pack.targets}
    named = [t.target_id for t in reference.targets]
    found = [f"crosswalk for {t}, not a pack target" for t in named if t not in targets]
    found += [f"pack target {t} has no ESCO crosswalk" for t in sorted(targets - set(named))]
    found += [f"two crosswalks for {t}" for t in sorted({t for t in named if named.count(t) > 1})]
    return found


def _rubrics(reference: Reference, pack: Pack) -> list[str]:
    found: list[str] = []
    skills = {s.skill_id: s for s in pack.skills}
    named = [r.skill_id for r in reference.rubrics]
    for rubric in reference.rubrics:
        skill = skills.get(rubric.skill_id)
        if skill is None:
            found.append(f"rubric for {rubric.skill_id}, not a pack row")
            continue
        if skill.kind != "skill":
            found.append(f"rubric for {rubric.skill_id}, a {skill.kind} row: it is a gate")
        if tuple(sorted(rubric.anchors)) != LEVELS:
            found.append(f"{rubric.skill_id} needs anchors for levels 0 to 4")
        for prerequisite in rubric.prerequisites:
            other = skills.get(prerequisite)
            if (
                other is None
                or other.target_id != skill.target_id
                or prerequisite == skill.skill_id
            ):
                found.append(f"{rubric.skill_id} names prerequisite {prerequisite}, not a row")
    found += [f"two rubrics for {s}" for s in sorted({s for s in named if named.count(s) > 1})]
    for skill in pack.skills:
        if skill.kind == "skill" and skill.skill_id not in named:
            found.append(f"pack row {skill.skill_id} has no rubric")
        if skill.kind != "skill" and reference.gate_for_row(skill.skill_id) is None:
            found.append(f"pack {skill.kind} row {skill.skill_id} has no typed gate")
    return found


def _gates(reference: Reference, pack: Pack) -> list[str]:
    found: list[str] = []
    skills = {s.skill_id: s for s in pack.skills}
    keys = [g.gate_key for g in reference.gates]
    found += [f"two gates named {k}" for k in sorted({k for k in keys if keys.count(k) > 1})]
    for gate in reference.gates:
        for row in gate.pack_rows:
            skill = skills.get(row)
            if skill is None or skill.kind == "skill":
                found.append(f"gate {gate.gate_key} types {row}, not a credential row")
    words = [w for g in reference.gates for w in g.gate_words]
    found += [
        f"gate words {w!r} typed twice" for w in sorted({w for w in words if words.count(w) > 1})
    ]
    for requirement in pack.skill_requirements:
        if requirement.gate is None:
            continue
        typed = reference.gate_for_words(requirement.gate)
        if typed is None:
            found.append(f"{requirement.record_id}: no typed gate for {requirement.gate!r}")
            continue
        row_gate = reference.gate_for_row(requirement.skill_id) if requirement.skill_id else None
        if row_gate is not None and row_gate.gate_key != typed.gate_key:
            found.append(
                f"{requirement.record_id}: {requirement.gate!r} is {typed.gate_key}, but its row "
                f"is {row_gate.gate_key}"
            )
    return found


def reference_path(version: str) -> Path:
    return REFERENCE_DIR / f"capability-reference-{version}.json"


def load_reference(version: str, pack: Pack, *, pins: dict[str, str] | None = None) -> Reference:
    """A committed version, its bytes checked against its pin, parsed and checked against the
    pack it is used with."""
    pinned = (PINS if pins is None else pins).get(version)
    if pinned is None:
        raise ReferenceError(f"no committed capability reference {version}")
    data = reference_path(version).read_bytes()
    if hashlib.sha256(data).hexdigest() != pinned:
        raise ReferenceError(f"capability reference {version} is not its pinned bytes")
    reference = parse_reference(json.loads(data))
    if reference.reference_version != version:
        raise ReferenceError(f"the file of version {version} says {reference.reference_version}")
    problems = check_reference(reference, pack)
    if problems:
        raise ReferenceError(f"capability reference {version}: {problems[0]}")
    return reference
