"""The essential skills ESCO lists for the kind of work of a person's role (plan section 4,
"Usual is not confirmed"; Sprint W SW.5; ADR 0014 decision 4; ADR 0015 decision 4).

When the person's current or last role names one ESCO occupation, its essential skills are
ESCO's list for that kind of work, "not confirmed yet": a state of their own, for display
only, never the person's skills. Wherever anything is computed (readiness, gaps, ranks) such
a skill is unresolved, so nothing here feeds a computation. The person picking one ("I've used
this", `Answer.USED`) is their own claim, recorded as a self-report through the capability's
one evidence command: it shows as self-reported, never as evidence. A skill they marked "not
part of my job" (`careerwright.profile.title_details`) is flagged for display only.
"""

import uuid
from dataclasses import dataclass
from enum import StrEnum

from careerwright.capability.evidence import Answer, SkillEvidence
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.records import OccupationDetail, SkillRef
from careerwright.db import Tx
from careerwright.profile import titles
from careerwright.profile.commands import current_profile
from careerwright.profile.targets import PackTargets


class UsualState(StrEnum):
    # ESCO lists it as essential to the role's kind of work: not confirmed yet.
    USUAL_IN_ROLE = "usual_in_role"
    SELF_REPORTED = "self_reported"  # the person said they have used or done it


SAID_DONE = frozenset({Answer.USED, Answer.DONE_INDEPENDENTLY, Answer.DONE_WITH_HELP})


@dataclass(frozen=True)
class UsualSkill:
    skill: SkillRef
    subject: str  # what evidence about it is recorded against: `esco:<skill ID>`
    state: UsualState
    answer: Answer | None  # the person's latest answer about it, if any
    evidence_id: uuid.UUID | None  # that answer's record
    # The person marked it "not part of my job": a display state, never evidence.
    not_part_of_job: bool = False


def subject_of(skill_id: uuid.UUID) -> str:
    return f"esco:{skill_id}"


def role_occupation(tx: Tx, workspace_id: uuid.UUID, pack: PackTargets) -> OccupationDetail | None:
    """The occupation the person's current or last role names, when it names exactly one."""
    profile = current_profile(tx, workspace_id)
    role = titles.current_role(tx, workspace_id, profile.document, pack)
    if role is None or len(role.occupations) != 1:
        return None
    return taxonomy_store.occupation(tx, role.occupations[0])


def essential_skills(occupation: OccupationDetail) -> list[SkillRef]:
    return [s for s in occupation.skills if s.relation == "essential"]


def usual_skills(
    occupation: OccupationDetail,
    evidence: list[SkillEvidence],
    not_part_of_job: frozenset[uuid.UUID] = frozenset(),
) -> list[UsualSkill]:
    """The role's essential skills, each ESCO's for its kind of work unless the person's latest
    answer about it says they have used or done it (self-reported), each flagged when the
    person marked it not part of their job (`not_part_of_job`, display only)."""
    latest: dict[str, SkillEvidence] = {}
    for record in sorted(evidence, key=lambda e: e.recorded_at):
        latest[record.subject] = record
    found: list[UsualSkill] = []
    for skill in essential_skills(occupation):
        subject = subject_of(skill.skill_id)
        said = latest.get(subject)
        state = (
            UsualState.SELF_REPORTED
            if said is not None and said.answer in SAID_DONE
            else UsualState.USUAL_IN_ROLE
        )
        found.append(
            UsualSkill(
                skill,
                subject,
                state,
                said.answer if said else None,
                said.evidence_id if said else None,
                skill.skill_id in not_part_of_job,
            )
        )
    return found
