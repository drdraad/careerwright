"""The pinned UK SOC 2020 coding index and its parser (spec section 5, TAX-1: "ONS explicitly
describes split mappings and supplies an ISCO-coded job-title index"; TAX1-02, TAX1-03).

ONS's SOC 2020 Volume 2 coding index lists about 32,700 job titles, each coded to a SOC 2020
unit group and, by ONS, to an ISCO-08 unit group. There is no one-to-one mapping between
the two classifications (ONS: "many job titles classified to a single unit group within SOC
2020 are split across two or more unit groups in ISCO-08"), so Careerwright keeps the index's
title-level links and never collapses them: an ISCO-08 group can lead to several SOC 2020
candidates, all of which stay visible (`pay.uk_soc_mapping`).

Licence: the Open Government Licence v3.0 (the index page's footer, read 2026-10-29;
session 1 rights policy line A2), with the attribution below.
"""

import re
from dataclasses import dataclass

from careerwright.catalogue import xlsx
from careerwright.catalogue.esco import normalise_label
from careerwright.catalogue.releases import ReleaseIntegrityError, ReleasePin

TRANSFORMATION_VERSION = "careerwright-soc-index-import-1"
LICENCE = "Open Government Licence v3.0"
ATTRIBUTION = (
    "Source: Office for National Statistics, SOC 2020 Volume 2: the coding index (version "
    "14), licensed under the Open Government Licence v3.0."
)
SOC_INDEX_RELEASE = ReleasePin(
    dataset_id="ons-soc2020-coding-index-v14",
    version="SOC 2020 Volume 2 coding index, version 14 (2026-08-27)",
    language="en",
    url=(
        "https://www.ons.gov.uk/file?uri=/methodology/classificationsandstandards/"
        "standardoccupationalclassificationsoc/soc2020/soc2020volume2codingrulesandconventions/"
        "soc2020volume2thecodingindexexcel20260827v2.xlsx"
    ),
    file_name="ons-soc2020-volume2-coding-index-v14.xlsx",
    sha256="59d3ec71d0e9eef2a27d7d0f4720f5c4bd584b61dc6902cc33dd8ee2ced40b9a",
    size_bytes=3_717_451,
    native_code_version="UK SOC 2020 unit groups, with ONS's ISCO-08 code per index entry",
)
INDEX_VERSION = "Version 14"
MAX_TITLE = 200

_CODE = re.compile(r"^[0-9]{4}$")
_COLUMNS = {
    "soc": "SOC_2020",
    "isco": "ISCO-08 code based on SOC2020",
    "title": "INDEXOCC_-_natural_word_order",
}


@dataclass(frozen=True)
class UnitGroup:
    code: str
    title: str


@dataclass(frozen=True)
class IndexEntry:
    title: str
    normalised: str
    soc_code: str
    isco_code: str


@dataclass(frozen=True)
class SocIndex:
    pin: ReleasePin
    unit_groups: tuple[UnitGroup, ...]
    entries: tuple[IndexEntry, ...]
    uncoded: int  # entries the index codes to no unit group (a "see" reference, say)


def _unit_groups(data: bytes) -> tuple[UnitGroup, ...]:
    rows = xlsx.sheet_rows(data, "SOC2020 framework")
    header = next(rows, [])
    if header[4:6] != ["SOC2020 Unit Group", "SOC2020 Group Title"]:
        raise ReleaseIntegrityError("the SOC 2020 framework has unexpected columns")
    groups = []
    for row in rows:
        code = (row[4] if len(row) > 4 else None) or ""
        if not code:
            continue
        title = (row[5] if len(row) > 5 else None) or ""
        if not _CODE.match(code.strip()) or not title.strip():
            raise ReleaseIntegrityError(f"an unexpected SOC 2020 unit group {code[:8]!r}")
        groups.append(UnitGroup(code.strip(), title.strip()[:MAX_TITLE]))
    if len({g.code for g in groups}) != len(groups):
        raise ReleaseIntegrityError("the SOC 2020 framework lists a unit group twice")
    return tuple(groups)


def parse_index(data: bytes, pin: ReleasePin) -> SocIndex:
    """The unit groups and every coded index entry. `data` must already be verified."""
    info = list(xlsx.sheet_rows(data, "INFO"))
    if not any(INDEX_VERSION in (cell or "") for row in info[:3] for cell in row):
        raise ReleaseIntegrityError(f"the coding index is not {INDEX_VERSION}")
    groups = _unit_groups(data)
    known = {g.code for g in groups}
    rows = xlsx.sheet_rows(data, "SOC2020 coding index")
    header = next(rows, [])
    column = {name: i for i, name in enumerate(header) if name}
    missing = [name for name in _COLUMNS.values() if name not in column]
    if missing:
        raise ReleaseIntegrityError(f"the coding index lacks columns {missing}")
    entries = []
    uncoded = 0
    for row in rows:
        cells = row + [None] * (len(header) - len(row))
        soc = (cells[column[_COLUMNS["soc"]]] or "").strip()
        isco = (cells[column[_COLUMNS["isco"]]] or "").strip()
        title = (cells[column[_COLUMNS["title"]]] or "").strip()
        if not (_CODE.match(soc) and _CODE.match(isco)):
            uncoded += 1  # ONS writes "}}}}" where an entry has no code
            continue
        if soc not in known or not title:
            raise ReleaseIntegrityError(f"an index entry names SOC 2020 code {soc}")
        entries.append(IndexEntry(title[:MAX_TITLE], normalise_label(title), soc, isco))
    if not entries:
        raise ReleaseIntegrityError("the coding index holds no coded entry")
    return SocIndex(pin, groups, tuple(entries), uncoded)
