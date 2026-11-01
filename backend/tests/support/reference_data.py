"""Synthetic samples of the pinned reference datasets, in each publisher's own file layout,
so tests import pay and AI evidence without the network (ADR 0010).

Every figure here is **synthetic**: invented for tests, labelled so in each sample pin
(`sample=True`, a `-synthetic-sample` dataset ID) and never shown as evidence about a real
occupation. The layouts (sheet names, title rows, header rows, ONS's markers, the
crosswalk's metadata lines) copy the real files, which `make setup` fetches and the
full-release tests import, and so does what ASHE withholds: no percentile at region x unit
group, except one labelled synthetic exception (`P90_EXCEPTION`) for the floor's mechanism
test, which the real release never has. The occupations are the ESCO sample's
(`fixtures/esco-sample`).
"""

import csv
import dataclasses
import hashlib
import io
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from xml.sax.saxutils import escape

from careerwright.catalogue.ai_resilience import (
    FIXTURE_PACK,
    AssessmentPacks,
    check_pack,
    load_pack,
)
from careerwright.catalogue.reference import DATASETS, Dataset
from careerwright.catalogue.releases import ReleasePin

DATA_ANALYST = "http://data.europa.eu/esco/occupation/d3edb8f8-3a06-47a0-8fb9-9b212c006aa2"
ICT_SYSTEM_ANALYST = "http://data.europa.eu/esco/occupation/a6a0b60f-08da-4faa-bf54-942987efb471"
BOOKKEEPER = "http://data.europa.eu/esco/occupation/c3aae59e-1441-4b3e-bdd1-6da50dc7cf42"
BICYCLE_MECHANIC = "http://data.europa.eu/esco/occupation/336cf331-8082-4a0c-bf5f-e7c54706211c"
DATA_QUALITY_SPECIALIST = (
    "http://data.europa.eu/esco/occupation/7086d0ca-1e77-4690-89c9-7ed1a0478fa3"
)
NORTH_WEST = "E12000002"
LONDON = "E12000007"

Cell = str | int | None


def workbook(sheets: dict[str, Sequence[Sequence[Cell]]]) -> bytes:
    """A minimal .xlsx: text as inline strings, numbers as numbers, as ONS writes them."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        entries, relations = [], []
        for n, (name, rows) in enumerate(sheets.items(), start=1):
            entries.append(f'<sheet name="{escape(name)}" sheetId="{n}" r:id="rId{n}"/>')
            relations.append(
                f'<Relationship Id="rId{n}" Type="http://schemas.openxmlformats.org/'
                f'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{n}.xml"/>'
            )
            archive.writestr(f"xl/worksheets/sheet{n}.xml", _sheet(rows))
        archive.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{''.join(entries)}</sheets></workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            f'relationships">{"".join(relations)}</Relationships>',
        )
    return buffer.getvalue()


def _column(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def _sheet(rows: Sequence[Sequence[Cell]]) -> str:
    out = []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, value in enumerate(row):
            ref = f"{_column(c)}{r}"
            if value is None:
                continue
            if isinstance(value, int) or (
                isinstance(value, str) and value.replace(".", "", 1).isdigit()
            ):
                cells.append(f'<c r="{ref}" t="n"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
        out.append(f'<row r="{r}">{"".join(cells)}</row>')
    return (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(out)}</sheetData></worksheet>"
    )


# --- ASHE Table 15 -----------------------------------------------------------------------

_HEADER_ROWS: list[list[Cell]] = [
    [None, None, "Number", None, "Annual", None, "Annual"],
    [None, None, "of jobsb", None, "percentage", None, "percentage", "Percentiles"],
    [
        "Description", "Code", "(thousand)", "Median", "change", "Mean", "change",
        "10", "20", "25", "30", "40", "60", "70", "75", "80", "90",
    ],
]  # fmt: skip
_TITLES = {"1": "Weekly pay - Gross", "5": "Hourly Pay - Gross", "7": "Annual pay - Gross"}
P90_CV = "14.2"  # synthetic: an "acceptable" band, worse than its median's

# (region, SOC code, SOC title, {table: (median, p90, CV)}): synthetic. As in the real
# 2026 provisional Table 15 (4), no percentile is published at region x unit group: every
# P90 (and every other percentile) is "x" (slice 7B fix round 2, re-review 1-A N1).
ASHE_ROWS = [
    ("North West", "3544", "Data analysts", {"7": ("38063.1", "x", "9.6"),
                                            "1": ("760.4", "x", "7.2"),
                                            "5": ("20.54", "x", "7.6")}),
    ("London", "3544", "Data analysts", {"7": ("46000.4", "x", "6.1"),
                                        "1": ("890", "x", "5.5"),
                                        "5": ("24.1", "x", "5.9")}),
    # A median written as a binary-float artefact, as ONS's workbooks store figures.
    ("North West", "4122", "Book-keepers, payroll managers and wages clerks",
     {"7": ("24000.49999999999", "x", "4.8"), "1": ("460", "x", "4.1"),
      "5": ("12.5", "x", "4.4")}),
    ("North West", "2135", "IT business analysts, architects and systems designers",
     {"7": ("x", "x", "x"), "1": ("x", "x", "x"), "5": ("x", "x", "x")}),
    # SYNTHETIC EXCEPTION: a published annual P90 (and its own CV), which the real Table
    # 15 (4) never has. It exists only so the floor's mechanism can be tested end to end
    # (`test_discovery.py`) and a percentile's own CV read (`test_reference_parsers.py`).
    ("Yorkshire and The Humber", "5231", "Vehicle technicians, mechanics and electricians",
     {"7": ("21000", "24000", "8.4"), "1": ("420", "x", "7.0"), "5": ("11.2", "x", "7.3")}),
]  # fmt: skip
P90_EXCEPTION = ("5231", "E12000003")  # the one row above with a published P90


def _ashe_table(table: str, *, cv: bool) -> bytes:
    title = (
        f"Table 15 (4) .{table}{'b' if cv else 'a'}   "
        + ("Coefficients of variation for " if cv else "")
        + f"{_TITLES[table]} (£) - For full-time employee jobsa: United Kingdom 2026"
    )
    rows: list[list[Cell]] = [[title], [], *_HEADER_ROWS]
    for region, code, label, figures in ASHE_ROWS:
        median, p90, cv_value = figures[table]
        # Each statistic has its own CV in the "b" table: the median's and the mean's are
        # `cv_value`; a published P90's is P90_CV, a withheld one's "x".
        p90_cv = P90_CV if p90 != "x" else "x"
        value = cv_value if cv else median
        rows.append(
            [f"      {region}, {label}", f"'{code}", "8", value, None, value if cv else "x",
             None, "x", "x", "x", "x", "x", "x", "x", "x", "x", p90_cv if cv else p90]
        )  # fmt: skip
    rows += [[], ["Source: Annual Survey of Hours and Earnings, Office for National Statistics."]]
    return workbook({"Notes": [["Synthetic sample: not ONS data"]], "Full-Time": rows})


def ashe_package() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for table, title in _TITLES.items():
            for kind in "ab":
                name = (
                    f"Table 15 (4)/Work Region Occupation SOC20 (4) Table 15.{table}{kind}   "
                    f"{title} 2026{' CV' if kind == 'b' else ''}.xlsx"
                )
                archive.writestr(name, _ashe_table(table, cv=kind == "b"))
    return buffer.getvalue()


# --- the SOC 2020 coding index -----------------------------------------------------------

UNIT_GROUPS = [
    ("2134", "Programmers and software development professionals"),
    ("2135", "IT business analysts, architects and systems designers"),
    ("2235", "Registered mental health nurses"),
    ("2237", "Other registered nursing professionals"),
    ("3132", "IT user support technicians"),
    ("3544", "Data analysts"),
    ("4122", "Book-keepers, payroll managers and wages clerks"),
    ("5231", "Vehicle technicians, mechanics and electricians"),
    ("6131", "Nursing auxiliaries and assistants"),
]
INDEX_ENTRIES = [  # (natural-word-order title, SOC 2020, ISCO-08): synthetic links
    ("Data analyst", "3544", "2511"),
    ("Analyst, data", "3544", "2511"),
    ("Systems analyst", "2135", "2511"),
    ("Bookkeeper", "4122", "3313"),
    ("Accounts clerk", "4122", "3313"),
    ("Cycle mechanic", "5231", "7234"),
    ("Data analyst (see notes)", "}}}}", "}}}}"),
    # The role space's titles (Task 6d slice B), each no ESCO title in the sample. As in the
    # real index, "Registered nurse" has two entries (two SOC groups, one ISCO group) and
    # "Nurse" is coded to more than one ISCO group; the links to 5322 (the sample's home care
    # aide) stand in for the real 5321, which the ESCO sample lacks. "Data quality analyst"
    # keeps the real 2421, a group the sample holds no occupation in; "IT support technician"
    # is an ESCO title too (the help desk agent's), so the type-ahead offers it as ESCO's.
    ("Registered nurse", "2235", "2221"),
    ("Registered nurse", "2237", "2221"),
    ("Nurse", "2237", "2221"),
    ("Nurse", "6131", "5322"),
    ("Prompt engineer", "2134", "2512"),
    ("Doula", "6131", "5322"),
    ("Data quality analyst", "3544", "2421"),
    ("IT support technician", "3132", "3512"),
]
YORKSHIRE = "E12000003"
_INDEX_HEADER = [
    "UNIQUE ID", "RECNO", "D", "SOC_90", "SOC_2000", "SOC_2010", "SOC_2020", "SOC_2020_ext",
    "INDEXOCC", "ADD", "IND", "SEE", "ISCO-08 code based on SOC2020", "VERSNO", "CHANGE",
    "SOC2020_ext_SUG_title", "SOC90_unit_group_title", "SOC2000_unit_group_title",
    "SOC2010_unit_group_title", "SOC2020_unit_group_title", "ISCO08_unit_group_title",
    "INDEXOCC_-_natural_word_order",
]  # fmt: skip


def soc_index_workbook(version: str = "Version 14") -> bytes:
    index_rows: list[list[Cell]] = [list(_INDEX_HEADER)]
    for n, (title, code, isco) in enumerate(INDEX_ENTRIES, start=1):
        row: list[Cell] = [None] * len(_INDEX_HEADER)
        row[0], row[1], row[6], row[12], row[21] = f"x{n}", str(n), code, isco, title
        index_rows.append(row)
    framework: list[list[Cell]] = [
        ["Unique ID", "SOC2020 Major Group", "SOC2020 Sub-Major Group", "SOC2020 Minor Group",
         "SOC2020 Unit Group", "SOC2020 Group Title", "Change", "VERNO"],
        [None, "2", None, None, None, "PROFESSIONAL OCCUPATIONS"],
    ]  # fmt: skip
    framework += [[None, None, None, None, code, title] for code, title in UNIT_GROUPS]
    return workbook(
        {
            "INFO": [[], [None, f"{version} Of The Standard Occupational Classification 2020"]],
            "SOC2020 coding index": index_rows,
            "SOC2020 framework": framework,
        }
    )


# --- the AI evidence ---------------------------------------------------------------------

ILO_ROWS = [  # (ISCO-08, title, task score, mean, SD, gradient): synthetic
    ("2511", "Systems Analysts", "0.5", "0.49", "0.12", "Exposed: Gradient 2"),
    ("2511", "Systems Analysts", "0.48", "0.49", "0.12", "Exposed: Gradient 2"),
    ("3313", "Accounting Associate Professionals", "0.7", "0.62", "0.08", "Exposed: Gradient 4"),
]
_ILO_HEADER = [
    "label4d", "label1d", "ISCO_08", "Title", "taskID", "Task_ISCO", "score_2023",
    "Weaviate Status", "predicted_score_2025_gpt4o", "prediction_justification_gpt4o",
    "weaviate_status_gemini", "predicted_score_2025_gemini", "prediction_justification_gemini",
    "score_2025", "source", "mean_score_2023", "mean_score_2025", "SD_2023", "SD_2025",
    "potential25", "potential23",
]  # fmt: skip


def ilo_workbook(rows: Iterable[tuple[str, str, str, str, str, str]] = ILO_ROWS) -> bytes:
    sheet: list[list[Cell]] = [list(_ILO_HEADER)]
    for n, (code, title, score, mean, sd, gradient) in enumerate(rows, start=1):
        row: list[Cell] = [None] * len(_ILO_HEADER)
        row[2], row[3], row[4], row[5] = code, title, str(n), "Synthetic task"
        row[13], row[16], row[18], row[19] = score, mean, sd, gradient
        sheet.append(row)
    return workbook({"Sheet1": sheet})


ONET_TASKS = [  # (O*NET-SOC 2019, title, task ID, task): synthetic tasks
    ("15-2051.01", "Business Intelligence Analysts", 1, "Synthetic task: build dashboards."),
    ("15-2051.01", "Business Intelligence Analysts", 2, "Synthetic task: query databases."),
    ("43-3031.00", "Bookkeeping Clerks", 3, "Synthetic task: reconcile ledgers."),
]
TASK_SHARES = [("synthetic task: build dashboards.", "0.25"), ("none", "1.5")]


def _csv(header: Sequence[str], rows: Iterable[Sequence[object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode()


def onet_tasks_csv() -> bytes:
    return _csv(
        ["O*NET-SOC Code", "Title", "Task ID", "Task", "Task Type", "Incumbents Responding"],
        ((code, title, task_id, task, "Core", "") for code, title, task_id, task in ONET_TASKS),
    )


def task_usage_csv() -> bytes:
    return _csv(["task_name", "pct"], TASK_SHARES)


CROSSWALK_ROWS = [  # (O*NET, O*NET title, ESCO or ISCO URI, title, match): synthetic links
    ("15-2051.01", "Business Intelligence Analysts", DATA_ANALYST, "data analyst", "closeMatch"),
    ("15-2041.00", "Statisticians", DATA_ANALYST, "data analyst", "broadMatch"),
    ("43-3031.00", "Bookkeeping Clerks", BOOKKEEPER, "bookkeeper", "exactMatch"),
    ("11-1011.00", "Chief Executives", "http://data.europa.eu/esco/isco/C1120",
     "Managing directors and chief executives", "exactISCO"),
]  # fmt: skip


def crosswalk_csv(esco_version: str = "v1.1.0") -> bytes:
    meta = [
        "Mapping project name,ESCO-O*NET Crosswalk,,,,,",
        "Mapping project version,1,,,,,",
        "Classification 1 Name,O*NET,,,,,",
        "Classification 1 Version,O*NET-SOC 2019,,,,,",
        "Classification 2 Name,ESCO,,,,,",
        f"Classification 2 Version,{esco_version},,,,,",
        ",,,,,,",
    ]
    table = _csv(
        ["O*NET Id", "O*NET Title", "O*NET Description", "ESCO or ISCO URI",
         "ESCO or ISCO Title", "ESCO or ISCO Description", "Type of Match"],
        ((c, t, "Synthetic.", u, ut, "Synthetic.", m) for c, t, u, ut, m in CROSSWALK_ROWS),
    )  # fmt: skip
    return ("﻿" + "\n".join(meta) + "\n").encode() + table


SAMPLE_BYTES = {
    "ashe": ashe_package,
    "soc_index": soc_index_workbook,
    "ilo_exposure": ilo_workbook,
    "onet_tasks": onet_tasks_csv,
    "task_usage": task_usage_csv,
    "crosswalk": crosswalk_csv,
}


def packs_scoring(esco_uri: str) -> AssessmentPacks:
    """Assessment packs whose product slot holds the committed synthetic fixture record moved
    to `esco_uri`: for tests that run a published range through a workspace that is not the
    fixture's. Tests only: the committed product pack is never synthetic."""
    fixture = load_pack(FIXTURE_PACK)
    moved = fixture.model_copy(
        update={"records": [r.model_copy(update={"esco_uri": esco_uri}) for r in fixture.records]}
    )
    return AssessmentPacks(product=check_pack(moved), fixture=check_pack(fixture))


def sample_pin(pin: ReleasePin, data: bytes) -> ReleasePin:
    return dataclasses.replace(
        pin,
        dataset_id=f"{pin.dataset_id}-synthetic-sample",
        url=f"tests/support/reference_data.py ({pin.dataset_id})",
        file_name=f"synthetic-{pin.file_name}",
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        native_code_version=f"{pin.native_code_version}; synthetic test sample",
        sample=True,
    )


def sample_files(directory: Path) -> list[tuple[Dataset, Path]]:
    """Every dataset's synthetic sample written under `directory`, with its sample pin."""
    files = []
    for dataset in DATASETS:
        data = SAMPLE_BYTES[dataset.name]()
        sample = dataclasses.replace(dataset, pin=sample_pin(dataset.pin, data))
        path = directory / sample.pin.file_name
        path.write_bytes(data)
        files.append((sample, path))
    return files
