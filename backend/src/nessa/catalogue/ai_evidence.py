"""The pinned AI-evidence releases and the ESCO to O*NET mapping, and their parsers (spec
section 5, AIR-1 step 1, TAX-1; AIR1-11, TAX1-07; ruling R7).

Each is a static import into its own native-code table, never a live API, and none of them
is a resilience score (AIR1-03):

- ILO exposure: the ILO-NASK refined global index of occupational exposure to generative AI
  (ILO Working Paper 140, 2025), by ISCO-08 unit group: the mean and standard deviation of
  its task scores (0 to 1, technical potential, never a prediction of job loss) and the
  exposure gradient the paper defines. The ILO's publication page offers only the paper;
  the scores are published, CC BY 4.0 with the ILO's attribution, in the lead author's
  repository, pinned here by commit and hash.
- Anthropic observed use: the Anthropic Economic Index release of 2025-03-27, by O*NET task:
  each task's share of the Claude conversations the release mapped to tasks (`task_pct_v2`)
  and the release's own O*NET-SOC 2019 task statements. Observed use is not replacement,
  and a task the release did not observe is "not observed", never zero use and never
  protection.
- The ESCO to O*NET crosswalk (European Commission with the US Department of Labor, version 1,
  September 2022): O*NET-SOC 2019 occupations matched to ESCO v1.1.0 occupations (or ISCO
  groups), each with its match type. The version bridge to the held ESCO v1.2.1 is by URI
  identity and is checked at import (`reference.import_reference`): a URI the held release
  lacks is counted, never matched by title.
"""

import csv
import io
import re
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from enum import StrEnum

from nessa.catalogue import xlsx
from nessa.catalogue.releases import ReleaseIntegrityError, ReleasePin

TRANSFORMATION_VERSION = "nessa-ai-evidence-import-1"

ILO_RELEASE = ReleasePin(
    dataset_id="ilo-genai-exposure-2025-wp140",
    version="2025 (ILO Working Paper 140), scores repository commit ce5fc25",
    language="en",
    url=(
        "https://raw.githubusercontent.com/pgmyrek/2025_GenAI_scores_ISCO08/"
        "ce5fc25c2a0db2757c5bfa797c4cfc8b408431ea/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"
    ),
    file_name="ilo-genai-exposure-2025-final-scores.xlsx",
    sha256="c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a",
    size_bytes=2_598_951,
    native_code_version="ISCO-08 unit groups (four-digit)",
)
ILO_LICENCE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
ILO_ATTRIBUTION = (
    "Gmyrek, P., Berg, J., Kamiński, K., Konopczyński, F., Ładna, A., Nafradi, B., "
    "Rosłaniec, K., Troszyński, M. 2025. Generative AI and Jobs: A Refined Global Index of "
    "Occupational Exposure. ILO Working Paper 140. Geneva: International Labour Office. "
    "© ILO. https://doi.org/10.54394/HETP0387. This is an adaptation of a copyrighted work "
    "of the International Labour Organization (ILO). This adaptation has not been prepared, "
    "reviewed or endorsed by the ILO and should not be considered an official ILO "
    "adaptation. The ILO disclaims all responsibility for its content and accuracy. "
    "Responsibility rests solely with the author(s) of the adaptation."
)

_ECONOMIC_INDEX = (
    "https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/"
    "4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2025_03_27/"
)
TASK_USAGE_RELEASE = ReleasePin(
    dataset_id="anthropic-economic-index-2025-03-27-task-pct-v2",
    version="release 2025-03-27 (task_pct_v2), dataset commit 4e5f69f",
    language="en",
    url=_ECONOMIC_INDEX + "task_pct_v2.csv",
    file_name="anthropic-economic-index-2025-03-27-task-pct-v2.csv",
    sha256="0c20f184cd4a1e3d8ef3d77f500b32b62431ce61a3c2f133c3af7fa8429f97db",
    size_bytes=435_372,
    native_code_version="O*NET task statements (O*NET-SOC 2019 taxonomy)",
)
ONET_TASKS_RELEASE = ReleasePin(
    dataset_id="anthropic-economic-index-2025-03-27-onet-tasks",
    version="release 2025-03-27 (onet_task_statements), dataset commit 4e5f69f",
    language="en",
    url=_ECONOMIC_INDEX + "onet_task_statements.csv",
    file_name="anthropic-economic-index-2025-03-27-onet-task-statements.csv",
    sha256="82e4c418dc08475ef1263ad1e8c66ffa3357291370cd35ee1065ecea590597ec",
    size_bytes=3_592_256,
    # The release names the O*NET-SOC 2019 taxonomy (its SOC_Structure.csv); it does not
    # state which O*NET database release its task statements come from.
    native_code_version="O*NET-SOC 2019 (O*NET database release not stated by the publisher)",
)
ANTHROPIC_LICENCE = "Creative Commons Attribution (CC BY; the publisher states no version)"
ANTHROPIC_ATTRIBUTION = (
    "Anthropic Economic Index, release 2025-03-27 (Handa et al., 2025, Which Economic Tasks "
    "are Performed with AI? Evidence from Millions of Claude Conversations, "
    "arXiv:2503.04761). Its task statements are O*NET content of the U.S. Department of "
    "Labor, Employment and Training Administration (USDOL/ETA), used under CC BY 4.0; "
    "O*NET is a trademark of USDOL/ETA."
)

CROSSWALK_RELEASE = ReleasePin(
    dataset_id="esco-onet-crosswalk-v1-2022-09",
    version="version 1, September 2022",
    language="en",
    url="https://esco.ec.europa.eu/system/files/2023-08/ONET_%28Occupations%29_0_updated.csv",
    file_name="esco-onet-crosswalk-v1-2022-09.csv",
    sha256="82179a0a3340da97b63df90134d8d941ec3c2c478334d855b69e4dd57a91b620",
    size_bytes=2_986_823,
    native_code_version="O*NET-SOC 2019 to ESCO v1.1.0 occupations",
)
CROSSWALK_LICENCE = (
    "Commission Decision 2011/833/EU on the reuse of Commission documents; its O*NET content "
    "CC BY 4.0 (USDOL/ETA)"
)
CROSSWALK_ATTRIBUTION = (
    "ESCO-O*NET Crosswalk, version 1 (September 2022), ESCO Secretariat of the European "
    "Commission in collaboration with the U.S. Department of Labor, Employment and Training "
    "Administration. This service uses the ESCO classification of the European Commission. "
    "O*NET is a trademark of USDOL/ETA."
)
CROSSWALK_ONET_VERSION = "O*NET-SOC 2019"
CROSSWALK_ESCO_VERSION = "v1.1.0"

_ISCO_CODE = re.compile(r"^[0-9]{4}$")
_ONET_CODE = re.compile(r"^[0-9]{2}-[0-9]{4}\.[0-9]{2}$")
_ESCO_OCCUPATION = re.compile(r"^http://data\.europa\.eu/esco/occupation/[0-9a-f-]{36}$")
_ISCO_URI = re.compile(r"^http://data\.europa\.eu/esco/isco/C(?P<code>[0-9]{1,4})$")
_SCORE = Decimal("0.0001")
MAX_TASK_TEXT = 1000
MAX_TITLE = 200


def normalise_task(text: str) -> str:
    """How the Economic Index names a task (`task_pct_v2.task_name`): lower case, spaced."""
    return " ".join(text.casefold().split())


def _score(value: str | None, what: str) -> Decimal:
    try:
        number = Decimal((value or "").strip())
    except InvalidOperation:
        raise ReleaseIntegrityError(f"an unexpected {what} {str(value)[:20]!r}") from None
    if not number.is_finite() or not 0 <= number <= 1:
        raise ReleaseIntegrityError(f"a {what} outside 0 to 1")
    return number.quantize(_SCORE, rounding=ROUND_HALF_EVEN)


class ExposureGradient(StrEnum):
    """The occupation's exposure category in the 2025 index (Table 5 of the paper)."""

    GRADIENT_4 = "Exposed: Gradient 4"
    GRADIENT_3 = "Exposed: Gradient 3"
    GRADIENT_2 = "Exposed: Gradient 2"
    GRADIENT_1 = "Exposed: Gradient 1"
    MINIMAL = "Minimal Exposure"
    NOT_EXPOSED = "Not Exposed"


@dataclass(frozen=True)
class IloExposure:
    isco_code: str
    title: str
    tasks: int
    mean_score: Decimal  # the occupation's mean 2025 task score, 0 to 1
    sd_score: Decimal
    gradient: ExposureGradient


_ILO_COLUMNS = ("ISCO_08", "Title", "score_2025", "mean_score_2025", "SD_2025", "potential25")


def parse_ilo(data: bytes) -> tuple[IloExposure, ...]:
    """One record per ISCO-08 unit group the index scores. The task rows repeat the
    occupation's mean, deviation and gradient; rows that disagree are refused."""
    rows = xlsx.sheet_rows(data, "Sheet1")
    header = next(rows, [])
    column = {name: i for i, name in enumerate(header) if name}
    missing = [c for c in _ILO_COLUMNS if c not in column]
    if missing:
        raise ReleaseIntegrityError(f"the ILO scores lack columns {missing}")
    grouped: dict[str, list[list[str | None]]] = defaultdict(list)
    for row in rows:
        cells = row + [None] * (len(header) - len(row))
        code = (cells[column["ISCO_08"]] or "").strip()
        if not _ISCO_CODE.match(code):
            raise ReleaseIntegrityError(f"an ILO row names ISCO-08 code {code[:8]!r}")
        _score(cells[column["score_2025"]], "task score")
        grouped[code].append(cells)
    exposures = []
    for code, task_rows in sorted(grouped.items()):
        shared = {
            (r[column["Title"]], r[column["mean_score_2025"]], r[column["SD_2025"]])
            for r in task_rows
        }
        gradients = {r[column["potential25"]] for r in task_rows}
        if len(shared) != 1 or len(gradients) != 1:
            raise ReleaseIntegrityError(f"ILO occupation {code} rows disagree")
        [(title, mean, sd)] = shared
        [gradient] = gradients
        try:
            category = ExposureGradient(gradient or "")
        except ValueError:
            raise ReleaseIntegrityError(f"an unexpected ILO gradient {gradient!r}") from None
        exposures.append(
            IloExposure(
                isco_code=code,
                title=(title or "").strip()[:MAX_TITLE],
                tasks=len(task_rows),
                mean_score=_score(mean, "mean score"),
                sd_score=_score(sd, "standard deviation"),
                gradient=category,
            )
        )
    if not exposures:
        raise ReleaseIntegrityError("the ILO scores hold no occupation")
    return tuple(exposures)


@dataclass(frozen=True)
class OnetTask:
    onet_code: str
    occupation_title: str
    task_id: int
    task: str
    task_type: str | None  # Core, Supplemental, or not stated


@dataclass(frozen=True)
class TaskUsage:
    task_name: str  # normalised task text, as the release names it
    share_pct: Decimal  # its share (percent) of the conversations the release mapped


def _csv(data: bytes, what: str) -> Iterator[dict[str, str]]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ReleaseIntegrityError(f"the {what} is not UTF-8") from None
    yield from csv.DictReader(io.StringIO(text, newline=""))


def parse_onet_tasks(data: bytes) -> tuple[OnetTask, ...]:
    tasks = []
    seen: set[tuple[str, int]] = set()
    for row in _csv(data, "O*NET task file"):
        code = (row.get("O*NET-SOC Code") or "").strip()
        if not _ONET_CODE.match(code):
            raise ReleaseIntegrityError(f"an O*NET task names code {code[:12]!r}")
        try:
            task_id = int(row.get("Task ID") or "")
        except ValueError:
            raise ReleaseIntegrityError("an O*NET task has no task ID") from None
        text = (row.get("Task") or "").strip()
        if not text or len(text) > MAX_TASK_TEXT or (code, task_id) in seen:
            raise ReleaseIntegrityError(f"O*NET task {code}/{task_id} is empty, long or repeated")
        seen.add((code, task_id))
        tasks.append(
            OnetTask(
                onet_code=code,
                occupation_title=(row.get("Title") or "").strip()[:MAX_TITLE],
                task_id=task_id,
                task=text,
                task_type=(row.get("Task Type") or "").strip() or None,
            )
        )
    if not tasks:
        raise ReleaseIntegrityError("the O*NET task file holds no task")
    return tuple(tasks)


# The release lists one row, "none", for conversations it mapped to no task: not a task.
_NO_TASK = "none"


def parse_task_usage(data: bytes) -> tuple[TaskUsage, ...]:
    usage = []
    seen: set[str] = set()
    for row in _csv(data, "task share file"):
        name = normalise_task(row.get("task_name") or "")
        if not name or len(name) > MAX_TASK_TEXT or name in seen:
            raise ReleaseIntegrityError("a task share row is empty, long or repeated")
        seen.add(name)
        try:
            share = Decimal((row.get("pct") or "").strip())
        except InvalidOperation:
            raise ReleaseIntegrityError("a task share is not a number") from None
        if not share.is_finite() or not 0 <= share <= 100:
            raise ReleaseIntegrityError("a task share outside 0 to 100")
        if name != _NO_TASK:
            usage.append(TaskUsage(name, share))
    if not usage:
        raise ReleaseIntegrityError("the task share file holds no task")
    return tuple(usage)


class MatchType(StrEnum):
    """The crosswalk's SKOS match types: how close an O*NET occupation is to its ESCO one."""

    EXACT = "exactMatch"
    CLOSE = "closeMatch"
    BROAD = "broadMatch"  # the ESCO concept is broader than the O*NET one
    NARROW = "narrowMatch"  # the ESCO concept is narrower
    EXACT_ISCO = "exactISCO"  # matched to an ISCO group, not an ESCO occupation


@dataclass(frozen=True)
class CrosswalkRow:
    onet_code: str
    onet_title: str
    esco_uri: str | None  # an ESCO occupation, or None when the row names an ISCO group
    isco_code: str | None
    target_title: str
    match_type: MatchType


_CROSSWALK_HEADER = "O*NET Id"
_CROSSWALK_META = {
    "Classification 1 Version": CROSSWALK_ONET_VERSION,
    "Classification 2 Version": CROSSWALK_ESCO_VERSION,
    "Mapping project version": "1",
}


def parse_crosswalk(data: bytes) -> tuple[CrosswalkRow, ...]:
    """The mapping rows, after checking the file's own statement of the two versions it
    maps between (O*NET-SOC 2019 and ESCO v1.1.0)."""
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError:
        raise ReleaseIntegrityError("the crosswalk is not UTF-8") from None
    meta = {}
    start = None
    for index, line in enumerate(lines):
        if line.startswith(_CROSSWALK_HEADER + ","):
            start = index
            break
        name, _, rest = line.partition(",")
        meta[name] = rest.split(",")[0]
    if start is None:
        raise ReleaseIntegrityError("the crosswalk has no header row")
    for name, expected in _CROSSWALK_META.items():
        if meta.get(name) != expected:
            raise ReleaseIntegrityError(f"the crosswalk's {name} is {meta.get(name)!r}")
    rows = []
    for row in csv.DictReader(io.StringIO("\n".join(lines[start:]), newline="")):
        code = (row.get("O*NET Id") or "").strip()
        uri = (row.get("ESCO or ISCO URI") or "").strip()
        if not _ONET_CODE.match(code):
            raise ReleaseIntegrityError(f"a crosswalk row names O*NET code {code[:12]!r}")
        try:
            match = MatchType((row.get("Type of Match") or "").strip())
        except ValueError:
            raise ReleaseIntegrityError("a crosswalk row has an unknown match type") from None
        isco = _ISCO_URI.match(uri)
        if not (_ESCO_OCCUPATION.match(uri) or isco):
            raise ReleaseIntegrityError(f"a crosswalk row names {uri[:60]!r}")
        if (isco is not None) != (match is MatchType.EXACT_ISCO):
            raise ReleaseIntegrityError("a crosswalk row's match type does not fit its target")
        rows.append(
            CrosswalkRow(
                onet_code=code,
                onet_title=(row.get("O*NET Title") or "").strip()[:MAX_TITLE],
                esco_uri=None if isco else uri,
                isco_code=isco.group("code") if isco else None,
                target_title=(row.get("ESCO or ISCO Title") or "").strip()[:MAX_TITLE],
                match_type=match,
            )
        )
    keys = {(r.onet_code, r.esco_uri or r.isco_code) for r in rows}
    if len(keys) != len(rows) or not rows:
        raise ReleaseIntegrityError("the crosswalk repeats a pair or holds none")
    return tuple(rows)
