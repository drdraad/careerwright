"""The pinned skill-level table against the pinned ESCO release (Task 6g): each ISCO-08
sub-major group's level is the one its own description in `ISCOGroups_en.csv` states, or, where
it states none, the one its major group's description states. Read from the release file
`make setup` fetches, independent of the product's import (which keeps no descriptions). No
database is needed."""

import csv
import hashlib
import io
import re
import zipfile
from pathlib import Path

import pytest

from careerwright.catalogue.esco import ESCO_RELEASE
from careerwright.catalogue.skill_levels import SUB_MAJOR_SKILL_LEVELS
from tools.datasets import DATASETS_DIR

pytestmark = pytest.mark.integration

ORDINAL = {"first": 1, "second": 2, "third": 3, "fourth": 4}
# "Competent performance in most occupations in this sub-major group requires skills at the
# fourth ISCO skill level", or "Most occupations in this major group require skills at the
# first ISCO skill level". Major group 1's names its exception (sub-major group 14) after this.
STATED = re.compile(r"\brequires? skills at the (first|second|third|fourth) ISCO skill level")


def _groups() -> dict[str, str]:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    data = release.read_bytes()
    assert hashlib.sha256(data).hexdigest() == ESCO_RELEASE.sha256  # the pinned release
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        rows = csv.DictReader(io.StringIO(archive.read("ISCOGroups_en.csv").decode("utf-8")))
        return {row["code"]: row["description"] for row in rows if len(row["code"]) <= 2}


def _stated(description: str) -> int | None:
    found = STATED.search(description)
    return None if found is None else ORDINAL[found.group(1)]


@pytest.mark.req("DIV1-16")
def test_every_sub_major_group_s_level_is_the_one_the_pinned_release_states() -> None:
    groups = _groups()
    sub_major = sorted(code for code in groups if len(code) == 2)
    derived = {code: _stated(groups[code]) or _stated(groups[code[0]]) for code in sub_major}
    unstated = [code for code in sub_major if _stated(groups[code]) is None]

    assert len(sub_major) == 43
    assert derived == dict(SUB_MAJOR_SKILL_LEVELS)
    # Only ICT professionals (25) states no level of its own: professionals' (4) holds.
    assert unstated == ["25"]
    # Managers state 4 with one exception, which its own description states as 3.
    assert _stated(groups["1"]) == 4
    assert "Sub-major Group 14" in groups["1"]
    assert SUB_MAJOR_SKILL_LEVELS["14"] == 3
