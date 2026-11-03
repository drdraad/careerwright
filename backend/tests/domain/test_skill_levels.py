"""The pinned skill-level table (Task 6g): ISCO-08's usual skill level for each sub-major group,
a job group's level, never a person's. Here, offline, its shape and lookups against the
committed ESCO sample; against the pinned release's own group descriptions in
`tests/integration/test_skill_levels.py`."""

import csv
import io
import zipfile

import pytest

from careerwright.catalogue.skill_levels import SUB_MAJOR_SKILL_LEVELS, skill_level
from tests.support.esco import SAMPLE_PATH


@pytest.mark.req("DIV1-16")
def test_the_table_holds_every_isco_08_sub_major_group_once_at_a_level_from_1_to_4() -> None:
    # ISCO-08 has 43 sub-major groups across its 10 major groups (armed forces included).
    assert len(SUB_MAJOR_SKILL_LEVELS) == 43
    assert all(len(code) == 2 and code.isdigit() for code in SUB_MAJOR_SKILL_LEVELS)
    assert {code[0] for code in SUB_MAJOR_SKILL_LEVELS} == set("0123456789")
    assert set(SUB_MAJOR_SKILL_LEVELS.values()) == {1, 2, 3, 4}


@pytest.mark.req("DIV1-16")
def test_every_sub_major_group_in_the_esco_sample_has_a_level() -> None:
    with zipfile.ZipFile(SAMPLE_PATH) as archive:
        rows = csv.DictReader(io.StringIO(archive.read("ISCOGroups_en.csv").decode("utf-8")))
        sub_major = {row["code"] for row in rows if len(row["code"]) == 2}

    assert sub_major
    assert sub_major <= set(SUB_MAJOR_SKILL_LEVELS)


@pytest.mark.req("DIV1-16")
@pytest.mark.parametrize(
    ("code", "level"),
    [
        ("2512", 4),  # a unit group: software developers, in ICT professionals
        ("251", 4),  # its minor group
        ("25", 4),  # its sub-major group
        ("1411", 3),  # hotel managers: hospitality, retail and other services managers
        ("1120", 4),  # managing directors: the rest of the managers
        ("3434", 3),  # chefs
        ("5131", 2),  # waiters
        ("9629", 1),  # elementary workers not elsewhere classified
        ("0110", 4),  # commissioned armed forces officers
        ("0210", 2),
        ("0310", 1),
    ],
)
def test_a_group_s_level_is_its_sub_major_group_s(code: str, level: int) -> None:
    assert skill_level(code) == level


@pytest.mark.req("DIV1-16")
@pytest.mark.parametrize("code", ["1", "", "9a", "99"])
def test_a_code_with_no_sub_major_group_in_isco_08_has_no_level(code: str) -> None:
    # A major group alone has no one level (managers are 4, except group 14 at 3), and a code
    # ISCO-08 does not hold is never given one.
    with pytest.raises(ValueError, match="sub-major group"):
        skill_level(code)
