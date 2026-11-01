"""The pinned ONS ASHE release and its parser (spec section 5, evidence hierarchy: "Official
pay benchmark"; TAX-1; ruling R7).

ASHE Table 15 gives pay by work region and UK SOC 2020 unit group. Careerwright imports three of
its tables, gross weekly (15.1), hourly (15.5) and annual (15.7) pay, for full-time employee
jobs (a provisional product decision, R6: a person's salary floor usually means a full-time
salary), with each table's coefficients of variation (the "b" files). Each estimate keeps
ONS's native code (SOC 2020), its geography (a work region, never a city), its period and
pay definition, the number of jobs, and every published statistic with its own
coefficient of variation, and ONS's own marker where one is withheld, so missingness is kept
and never read as zero.

ONS writes its figures as binary numbers in the workbook; each is read as its decimal text
and rounded to the penny (pay is integer pence, Global Constraint 4).

Licence (https://www.ons.gov.uk/methodology/geography/licences, read 2026-10-29; session 1
rights policy line A2): the Open Government Licence v3.0, with the attribution below.
"""

import io
import re
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from enum import StrEnum

from careerwright.catalogue import xlsx
from careerwright.catalogue.releases import ReleaseIntegrityError, ReleasePin

# 2: every statistic's CV is kept, not the median's only (slice 7B fix round 1, migration 0028).
TRANSFORMATION_VERSION = "careerwright-ashe-import-2"
LICENCE = "Open Government Licence v3.0"
ATTRIBUTION = (
    "Source: Office for National Statistics, Annual Survey of Hours and Earnings, licensed "
    "under the Open Government Licence v3.0."
)

ASHE_RELEASE = ReleasePin(
    dataset_id="ons-ashe-table15-2026-provisional",
    version="2026 provisional",
    language="en",
    url=(
        "https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/"
        "earningsandworkinghours/datasets/regionbyoccupation4digitsoc2010ashetable15/"
        "2026provisional/ashetable152026provisional.zip"
    ),
    file_name="ons-ashe-table15-2026-provisional.zip",
    sha256="fefd20c5a746a9ad6a563a0edf6c3ac204b093c9d23a500b7d4234122595f081",
    size_bytes=67_460_310,
    native_code_version="UK SOC 2020 unit groups (four-digit) by ONS work region",
)
SURVEY_YEAR = "2026"
POPULATION = "full_time"
SHEET = "Full-Time"


class AshePeriod(StrEnum):
    """The period a table gives pay per. A month has no ASHE table, and no figure is ever
    converted between periods (annualising needs hours; spec section 5)."""

    YEAR = "year"
    WEEK = "week"
    HOUR = "hour"


# Table number -> (period, the words its title must hold, the pay definition shown).
_TABLES = {
    "1": (
        AshePeriod.WEEK,
        "weekly pay - gross",
        "Gross weekly pay in the April 2026 pay period, full-time employee jobs",
    ),
    "5": (
        AshePeriod.HOUR,
        "hourly pay - gross",
        "Gross hourly pay (overtime included) in the April 2026 pay period, full-time "
        "employee jobs",
    ),
    "7": (
        AshePeriod.YEAR,
        "annual pay - gross",
        "Gross annual pay for the year to April 2026, full-time employee jobs of employees "
        "in the same job for at least a year",
    ),
}
PAY_DEFINITION = {period: words for period, _, words in _TABLES.values()}

# ONS work regions as Table 15 names them -> their GSS codes (the city list's regions are
# England's; Wales and Scotland are kept as published).
WORK_REGIONS = {
    "North East": "E12000001",
    "North West": "E12000002",
    "Yorkshire and The Humber": "E12000003",
    "East Midlands": "E12000004",
    "West Midlands": "E12000005",
    "East": "E12000006",
    "London": "E12000007",
    "South East": "E12000008",
    "South West": "E12000009",
    "Wales": "W92000004",
    "Scotland": "S92000003",
}

PERCENTILES = ("p10", "p20", "p25", "p30", "p40", "p60", "p70", "p75", "p80", "p90")
STATISTICS = ("median", "mean", *PERCENTILES)
_HEADER = [
    "Description",
    "Code",
    "(thousand)",
    "Median",
    "change",
    "Mean",
    "change",
    "10",
    "20",
    "25",
    "30",
    "40",
    "60",
    "70",
    "75",
    "80",
    "90",
]
# The column of each statistic (the two "change" columns are not imported).
_COLUMNS = {"median": 3, "mean": 5, **{p: 7 + i for i, p in enumerate(PERCENTILES)}}
_JOBS_COLUMN = 2


class Marker(StrEnum):
    """ONS's markers for a value it does not publish (Table 15's key)."""

    UNRELIABLE = "x"  # CV above 20%: "unreliable for practical purposes"
    DISCLOSIVE = ".."
    NOT_APPLICABLE = ":"
    NEGLIGIBLE = "-"  # nil or negligible


class Reliability(StrEnum):
    """ONS's quality bands for an estimate's coefficient of variation (CV)."""

    PRECISE = "precise"  # CV <= 5%
    REASONABLY_PRECISE = "reasonably_precise"  # 5% < CV <= 10%
    ACCEPTABLE = "acceptable"  # 10% < CV <= 20%
    UNRELIABLE = "unreliable"  # CV > 20%: ONS withholds the estimate
    UNKNOWN = "unknown"  # no CV published


def reliability(cv: Decimal | None) -> Reliability:
    if cv is None:
        return Reliability.UNKNOWN
    if cv <= 5:
        return Reliability.PRECISE
    if cv <= 10:
        return Reliability.REASONABLY_PRECISE
    if cv <= 20:
        return Reliability.ACCEPTABLE
    return Reliability.UNRELIABLE


@dataclass(frozen=True)
class AsheEstimate:
    soc_code: str
    soc_title: str
    region_code: str
    region_name: str
    period: AshePeriod
    jobs_thousands: Decimal | None
    figures: dict[str, int | None]  # statistic -> pence, None when ONS withholds it
    markers: dict[str, str]  # statistic -> ONS's marker for a withheld value
    # statistic -> its coefficient of variation (%) from the "b" table, None when withheld:
    # each statistic's own, so a P90's band is never the median's (fix round 1, review A M4)
    cvs: dict[str, Decimal | None]


@dataclass(frozen=True)
class AsheRelease:
    pin: ReleasePin
    estimates: tuple[AsheEstimate, ...]


_MEMBER = re.compile(
    r"^Table 15 \(4\)/Work Region Occupation SOC20 \(4\) Table 15\.(?P<table>\d+)(?P<kind>[ab])"
    r"\s.*\.xlsx$"
)
_NUMBER = re.compile(r"^-?[0-9]+(\.[0-9]+)?([eE]-?[0-9]+)?$")
_PENNY = Decimal("0.01")


def _decimal(value: str | None) -> Decimal | str | None:
    """A published number, ONS's marker for a withheld one, or None for an empty cell."""
    text = (value or "").strip()
    if not text:
        return None
    if text in {m.value for m in Marker}:
        return text
    if not _NUMBER.match(text):
        raise ReleaseIntegrityError(f"unexpected ASHE value {text[:20]!r}")
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ReleaseIntegrityError(f"unexpected ASHE value {text[:20]!r}") from None


def _pence(amount: Decimal) -> int:
    if amount < 0:
        raise ReleaseIntegrityError("ASHE pay is never negative")
    return int(amount.quantize(_PENNY, rounding=ROUND_HALF_EVEN) * 100)


@dataclass(frozen=True)
class _Row:
    soc_code: str
    soc_title: str
    region_name: str
    cells: list[str | None]


def _rows(data: bytes, expect_title: str, *, cv: bool) -> Iterator[_Row]:
    rows = xlsx.sheet_rows(data, SHEET)
    title = next(rows, [None])[0] or ""
    words = title.casefold()
    if expect_title not in words or "full-time employee jobs" not in words:
        raise ReleaseIntegrityError(f"unexpected ASHE table {title[:80]!r}")
    if SURVEY_YEAR not in words or ("coefficients of variation" in words) != cv:
        raise ReleaseIntegrityError(f"unexpected ASHE table {title[:80]!r}")
    header = None
    for row in rows:
        if header is None:
            if row[:1] == ["Description"]:
                if [(c or "").strip() for c in row[: len(_HEADER)]] != _HEADER:
                    raise ReleaseIntegrityError("an ASHE table has unexpected columns")
                header = row
            continue
        code = (row[1] or "").strip() if len(row) > 1 else ""
        if not code:
            continue  # notes and the source line after the table
        code = code.removeprefix("'")
        if not re.fullmatch(r"[0-9]{4}", code):
            raise ReleaseIntegrityError(f"unexpected SOC 2020 code {code[:8]!r}")
        description = (row[0] or "").strip()
        region, _, soc_title = description.partition(", ")
        if region not in WORK_REGIONS or not soc_title:
            raise ReleaseIntegrityError(f"unexpected ASHE row {description[:60]!r}")
        yield _Row(code, soc_title.strip(), region, row + [None] * (len(_HEADER) - len(row)))
    if header is None:
        raise ReleaseIntegrityError("an ASHE table has no header row")


def _estimates(table: str, pay: bytes, variation: bytes) -> Iterator[AsheEstimate]:
    period, title, _ = _TABLES[table]
    cvs: dict[tuple[str, str], dict[str, Decimal | None]] = {}
    for row in _rows(variation, title, cv=True):
        cells = {statistic: _decimal(row.cells[column]) for statistic, column in _COLUMNS.items()}
        cvs[(row.region_name, row.soc_code)] = {
            statistic: value if isinstance(value, Decimal) else None
            for statistic, value in cells.items()
        }
    for row in _rows(pay, title, cv=False):
        figures: dict[str, int | None] = {}
        markers: dict[str, str] = {}
        for statistic, column in _COLUMNS.items():
            value = _decimal(row.cells[column])
            figures[statistic] = _pence(value) if isinstance(value, Decimal) else None
            if isinstance(value, str):
                markers[statistic] = value
        jobs = _decimal(row.cells[_JOBS_COLUMN])
        key = (row.region_name, row.soc_code)
        if key not in cvs:
            raise ReleaseIntegrityError(f"ASHE row {row.soc_code} has no coefficient of variation")
        yield AsheEstimate(
            soc_code=row.soc_code,
            soc_title=row.soc_title,
            region_code=WORK_REGIONS[row.region_name],
            region_name=row.region_name,
            period=period,
            jobs_thousands=jobs if isinstance(jobs, Decimal) else None,
            figures=figures,
            markers=markers,
            cvs=cvs[key],
        )


def parse_release(data: bytes, pin: ReleasePin) -> AsheRelease:
    """The three full-time gross pay tables as typed estimates. `data` must already be
    verified (`releases.read_verified`)."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ReleaseIntegrityError(f"{pin.file_name} is not a zip archive") from None
    members: dict[tuple[str, str], str] = {}
    with archive:
        for name in archive.namelist():
            match = _MEMBER.match(name)
            if match and match.group("table") in _TABLES:
                members[(match.group("table"), match.group("kind"))] = name
        missing = [f"15.{t}{k}" for t in _TABLES for k in "ab" if (t, k) not in members]
        if missing:
            raise ReleaseIntegrityError(f"the ASHE package lacks tables {missing}")
        read = {key: _inflated(archive, name) for key, name in members.items()}
    estimates = [e for t in _TABLES for e in _estimates(t, read[(t, "a")], read[(t, "b")])]
    keys = {(e.soc_code, e.region_code, e.period) for e in estimates}
    if len(keys) != len(estimates):
        raise ReleaseIntegrityError("an ASHE table lists one region and code twice")
    return AsheRelease(pin, tuple(estimates))


def _inflated(archive: zipfile.ZipFile, name: str) -> bytes:
    if archive.getinfo(name).file_size > xlsx.MAX_MEMBER_BYTES:
        raise ReleaseIntegrityError(f"{name} inflates past {xlsx.MAX_MEMBER_BYTES} bytes")
    return archive.read(name)
