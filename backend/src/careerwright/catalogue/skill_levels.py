"""ISCO-08's skill levels by sub-major group (Task 6g): the usual level of training a job
group's work needs. Pure; pinned here.

ISCO-08 grades work on four skill levels by the education it usually needs, from 1 (the
least) to 4 (a first degree or more, or equivalent training), and states the level of most
occupations in each group: 4 for managers, except sub-major group 14 (hospitality, retail and
other services managers) at 3; 4 for professionals; 3 for technicians and associate
professionals; 2 for major groups 4 to 8; 1 for elementary occupations; and 4, 2 and 1 for the
three armed forces sub-major groups. The pinned ESCO release carries those statements in its
group descriptions, and `tests/integration/test_skill_levels.py` checks this table against
them.

It is a job group's level, never a person's, and never pay, popularity or status (spec section
4, DIV-1: never optimise for prestige). Discovery places its two sets by it
(`careerwright.profile.horizons`).
"""

from collections.abc import Mapping
from typing import Literal

SkillLevel = Literal[1, 2, 3, 4]

SUB_MAJOR_SKILL_LEVELS: Mapping[str, SkillLevel] = {
    # 0 Armed forces occupations
    "01": 4,
    "02": 2,
    "03": 1,
    # 1 Managers
    "11": 4,
    "12": 4,
    "13": 4,
    "14": 3,
    # 2 Professionals
    "21": 4,
    "22": 4,
    "23": 4,
    "24": 4,
    "25": 4,
    "26": 4,
    # 3 Technicians and associate professionals
    "31": 3,
    "32": 3,
    "33": 3,
    "34": 3,
    "35": 3,
    # 4 Clerical support workers
    "41": 2,
    "42": 2,
    "43": 2,
    "44": 2,
    # 5 Service and sales workers
    "51": 2,
    "52": 2,
    "53": 2,
    "54": 2,
    # 6 Skilled agricultural, forestry and fishery workers
    "61": 2,
    "62": 2,
    "63": 2,
    # 7 Craft and related trades workers
    "71": 2,
    "72": 2,
    "73": 2,
    "74": 2,
    "75": 2,
    # 8 Plant and machine operators and assemblers
    "81": 2,
    "82": 2,
    "83": 2,
    # 9 Elementary occupations
    "91": 1,
    "92": 1,
    "93": 1,
    "94": 1,
    "95": 1,
    "96": 1,
}


def skill_level(isco_code: str) -> SkillLevel:
    """The usual skill level of the ISCO-08 sub-major group an ISCO-08 group is in (a
    sub-major, minor or unit group's code). A major group alone has no one level, so it, like
    any code ISCO-08 doesn't hold, is refused."""
    level = SUB_MAJOR_SKILL_LEVELS.get(isco_code[:2]) if len(isco_code) >= 2 else None
    if level is None or not isco_code.isdigit():
        raise ValueError(f"{isco_code!r} names no ISCO-08 sub-major group")
    return level
