"""Two horizons, Next step and Aim higher (Task 6g; the product owner, 3 November 2026: "distinguish
between immediate next job ... and ideal job"): where discovery places work, by its job group's
usual ISCO skill level (`careerwright.catalogue.skill_levels`) against the person's reference
level. Pure.

The reference level comes from the person's current or last role alone: its one ESCO
occupation's job group, else the ISCO-08 groups the UK job-title index codes its title to, when
they are all at one level. Otherwise it is unknown, never a number: no job yet, a skipped role,
a title in the person's own words, one several ESCO occupations hold and none is chosen, or
groups at different levels. Targets never set it: they are where the person is going.

Next step is work at or below the reference level; Aim higher is work above it, and, for a
level-4 reference, level-4 work in another ISCO-08 major group. With the reference unknown,
ISCO's own bands decide: levels 1 and 2 are Next step, 3 and 4 Aim higher. A level is a job
group's usual training, never pay, popularity or status (spec section 4: never optimise for
prestige), and Aim higher says nothing about whether work suits the person or whether they
are ready for it.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from careerwright.catalogue.skill_levels import SkillLevel, skill_level


class Horizon(StrEnum):
    NEXT_STEP = "next_step"  # at or below the reference level
    AIM_HIGHER = "aim_higher"  # above it


class ReferenceBasis(StrEnum):
    """What the person's reference level was read from."""

    ROLE_OCCUPATION = "role_occupation"  # the one ESCO occupation their role names
    UK_TITLE_GROUPS = "uk_title_groups"  # the ISCO-08 groups ONS codes their title to, at one level
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Reference:
    basis: ReferenceBasis
    level: SkillLevel | None = None  # None: unknown
    # The role's ISCO-08 major groups: for a level-4 role, level-4 work in another is Aim higher.
    major_groups: frozenset[str] = frozenset()


UNKNOWN_REFERENCE = Reference(ReferenceBasis.UNKNOWN)
# With the reference unknown, the highest level Next step holds (ISCO's bands: 1 and 2).
BANDS_NEXT_STEP_TOP: SkillLevel = 2


def reference_level(occupation_groups: Sequence[str], uk_title_groups: Sequence[str]) -> Reference:
    """The person's reference level from their role. `occupation_groups`: the ISCO-08 unit
    group of each ESCO occupation the role names (one: its own; several: none is chosen);
    `uk_title_groups`: the ISCO-08 groups the UK job-title index codes its title to."""
    if len(occupation_groups) == 1:
        [code] = occupation_groups
        return Reference(ReferenceBasis.ROLE_OCCUPATION, skill_level(code), frozenset({code[0]}))
    if not occupation_groups:
        levels = {skill_level(code) for code in uk_title_groups}
        if len(levels) == 1:
            [level] = levels
            majors = frozenset(code[0] for code in uk_title_groups)
            return Reference(ReferenceBasis.UK_TITLE_GROUPS, level, majors)
    return UNKNOWN_REFERENCE


def place(isco_code: str, reference: Reference) -> Horizon:
    """Where work in an ISCO-08 group (sub-major, minor or unit) is placed against the person's
    reference level."""
    level = skill_level(isco_code)
    if reference.level is None:
        return Horizon.NEXT_STEP if level <= BANDS_NEXT_STEP_TOP else Horizon.AIM_HIGHER
    above = level > reference.level
    elsewhere_at_the_top = (
        level == reference.level == 4 and isco_code[0] not in reference.major_groups
    )
    return Horizon.AIM_HIGHER if above or elsewhere_at_the_top else Horizon.NEXT_STEP
