"""SQL for the pinned reference datasets: ASHE, the SOC 2020 coding index and the AI evidence
(adapter; migration 0027).

Imports run under the migration owner (setup only), one dataset per transaction, the bulk
rows sent by COPY. Reads run under the API role: public reference data, every row readable.
"""

import json
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa

from careerwright.catalogue.ai_evidence import (
    CrosswalkRow,
    ExposureGradient,
    IloExposure,
    MatchType,
    OnetTask,
    TaskUsage,
    normalise_task,
)
from careerwright.catalogue.ashe import AshePeriod, AsheRelease
from careerwright.catalogue.pay import PayBenchmark, SocLink
from careerwright.catalogue.records import UkGroup, UkTitle
from careerwright.catalogue.releases import ReleasePin
from careerwright.catalogue.soc import SocIndex
from careerwright.db import Tx

_RELEASE_COLUMNS = (
    "dataset, dataset_id, version, language, source_url, sha256, size_bytes, "
    "native_code_version, transformation_version, licence, attribution, sample, record_count, "
    "counts, imported_at"
)
TOP_TASKS = 3  # the observed tasks shown per O*NET occupation, largest share first


@dataclass(frozen=True)
class ReferenceRelease:
    """A pinned reference dataset's import manifest (TAX1-04)."""

    dataset: str
    dataset_id: str
    version: str
    language: str
    source_url: str
    sha256: str
    size_bytes: int
    native_code_version: str
    transformation_version: str
    licence: str
    attribution: str
    sample: bool
    record_count: int
    counts: dict[str, int]
    imported_at: datetime


def _copy(tx: Tx, statement: str, rows: Iterable[Sequence[object]]) -> None:
    raw = tx.connection.driver_connection
    with raw.cursor() as cursor, cursor.copy(statement) as copy:  # type: ignore[union-attr]
        for row in rows:
            copy.write_row(row)


def lock(tx: Tx) -> None:
    """Setup only: serialise imports for the rest of the transaction."""
    tx.execute(sa.text("LOCK TABLE careerwright.reference_releases IN EXCLUSIVE MODE"))


def held(tx: Tx, dataset: str) -> ReferenceRelease | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_RELEASE_COLUMNS} FROM careerwright.reference_releases WHERE dataset = :d"
            ),
            {"d": dataset},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else ReferenceRelease(**dict(row))


def releases(tx: Tx) -> list[ReferenceRelease]:
    rows = tx.execute(
        sa.text(f"SELECT {_RELEASE_COLUMNS} FROM careerwright.reference_releases ORDER BY dataset")
    ).mappings()
    return [ReferenceRelease(**dict(r)) for r in rows]


def insert_release(
    tx: Tx,
    dataset: str,
    pin: ReleasePin,
    *,
    transformation: str,
    licence: str,
    attribution: str,
    record_count: int,
    counts: dict[str, int],
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.reference_releases (dataset, dataset_id, version, language, "
            "source_url, sha256, size_bytes, native_code_version, transformation_version, "
            "licence, attribution, sample, record_count, counts) VALUES (:dataset, :id, "
            ":version, :language, :url, :sha, :size, :native, :transform, :licence, "
            ":attribution, :sample, :records, CAST(:counts AS jsonb))"
        ),
        {
            "dataset": dataset,
            "id": pin.dataset_id,
            "version": pin.version,
            "language": pin.language,
            "url": pin.url,
            "sha": pin.sha256,
            "size": pin.size_bytes,
            "native": pin.native_code_version,
            "transform": transformation,
            "licence": licence,
            "attribution": attribution,
            "sample": pin.sample,
            "records": record_count,
            "counts": json.dumps(counts),
        },
    )


def insert_ashe(tx: Tx, release: AsheRelease) -> None:
    _copy(
        tx,
        "COPY careerwright.ashe_estimates (soc_code, region_code, period, population, soc_title, "
        "region_name, jobs_thousands, figures, markers, cvs) FROM STDIN",
        (
            (
                e.soc_code,
                e.region_code,
                e.period.value,
                "full_time",
                e.soc_title,
                e.region_name,
                e.jobs_thousands,
                json.dumps(e.figures),
                json.dumps(e.markers),
                # Decimal text, so no CV passes through a float.
                json.dumps({s: None if cv is None else format(cv, "f") for s, cv in e.cvs.items()}),
            )
            for e in release.estimates
        ),
    )


def insert_soc_index(tx: Tx, index: SocIndex) -> None:
    _copy(
        tx,
        "COPY careerwright.soc2020_unit_groups (code, title) FROM STDIN",
        ((g.code, g.title) for g in index.unit_groups),
    )
    _copy(
        tx,
        "COPY careerwright.soc2020_index_entries (entry_id, soc_code, isco_code, title, "
        "normalised) "
        "FROM STDIN",
        (
            (n, e.soc_code, e.isco_code, e.title, e.normalised)
            for n, e in enumerate(index.entries, start=1)
        ),
    )


def insert_ilo(tx: Tx, exposures: Iterable[IloExposure]) -> None:
    _copy(
        tx,
        "COPY careerwright.ilo_genai_exposure (isco_code, title, tasks, mean_score, sd_score, "
        "gradient) FROM STDIN",
        (
            (e.isco_code, e.title, e.tasks, e.mean_score, e.sd_score, e.gradient.value)
            for e in exposures
        ),
    )


def insert_onet_tasks(tx: Tx, tasks: Iterable[OnetTask]) -> None:
    _copy(
        tx,
        "COPY careerwright.onet_tasks (onet_code, task_id, occupation_title, task, task_type, "
        "normalised_task) FROM STDIN",
        (
            (
                t.onet_code,
                t.task_id,
                t.occupation_title,
                t.task,
                t.task_type,
                normalise_task(t.task),
            )
            for t in tasks
        ),
    )


def insert_task_usage(tx: Tx, usage: Iterable[TaskUsage]) -> None:
    _copy(
        tx,
        "COPY careerwright.observed_task_use (task_name, share_pct) FROM STDIN",
        ((u.task_name, u.share_pct) for u in usage),
    )


def insert_crosswalk(tx: Tx, rows: Iterable[CrosswalkRow]) -> None:
    _copy(
        tx,
        "COPY careerwright.esco_onet_crosswalk (onet_code, onet_title, esco_uri, isco_code, "
        "target_title, match_type) FROM STDIN",
        (
            (r.onet_code, r.onet_title, r.esco_uri, r.isco_code, r.target_title, r.match_type.value)
            for r in rows
        ),
    )


def crosswalk_bridge(tx: Tx) -> dict[str, int]:
    """The version bridge as counted after import: rows whose ESCO v1.1.0 occupation the
    held ESCO release lacks, O*NET codes the held task file lacks, and rows naming an ISCO
    group rather than an occupation (TAX1-07)."""
    row = tx.execute(
        sa.text(
            "SELECT count(*) FILTER (WHERE c.esco_uri IS NOT NULL AND o.concept_id IS NULL) "
            "AS esco_rows_not_in_held_release, "
            "count(DISTINCT c.onet_code) FILTER (WHERE NOT EXISTS (SELECT 1 FROM "
            "careerwright.onet_tasks t WHERE t.onet_code = c.onet_code)) AS "
            "onet_codes_without_tasks, "
            "count(*) FILTER (WHERE c.isco_code IS NOT NULL) AS isco_rows "
            "FROM careerwright.esco_onet_crosswalk c "
            "LEFT JOIN careerwright.occupation_concepts o ON o.esco_uri = c.esco_uri"
        )
    ).one()
    return {
        "esco_rows_not_in_held_release": int(row.esco_rows_not_in_held_release),
        "onet_codes_without_tasks": int(row.onet_codes_without_tasks),
        "isco_rows": int(row.isco_rows),
    }


# --- reads ------------------------------------------------------------------------------


@dataclass(frozen=True)
class OccupationIdentity:
    concept_id: uuid.UUID
    esco_uri: str
    isco_code: str
    preferred_label: str
    labels: frozenset[str]  # preferred and alternative labels, normalised


def occupation_identities(
    tx: Tx, concept_ids: Iterable[uuid.UUID]
) -> dict[uuid.UUID, OccupationIdentity]:
    ids = [str(i) for i in sorted(set(concept_ids))]
    if not ids:
        return {}
    labels: dict[uuid.UUID, set[str]] = {}
    for row in tx.execute(
        sa.text(
            "SELECT concept_id, normalised FROM careerwright.occupation_labels "
            "WHERE concept_id = ANY(CAST(:ids AS uuid[])) AND kind <> 'hidden'"
        ),
        {"ids": ids},
    ):
        labels.setdefault(row.concept_id, set()).add(row.normalised)
    rows = tx.execute(
        sa.text(
            "SELECT concept_id, esco_uri, isco_code, preferred_label "
            "FROM careerwright.occupation_concepts WHERE concept_id = ANY(CAST(:ids AS uuid[]))"
        ),
        {"ids": ids},
    )
    return {
        r.concept_id: OccupationIdentity(
            r.concept_id,
            r.esco_uri,
            r.isco_code,
            r.preferred_label,
            frozenset(labels.get(r.concept_id, ())),
        )
        for r in rows
    }


def soc_links(tx: Tx, isco_code: str) -> list[SocLink]:
    rows = tx.execute(
        sa.text(
            "SELECT e.soc_code, g.title, count(*) AS entries FROM "
            "careerwright.soc2020_index_entries e "
            "JOIN careerwright.soc2020_unit_groups g ON g.code = e.soc_code WHERE e.isco_code = "
            ":isco "
            "GROUP BY e.soc_code, g.title"
        ),
        {"isco": isco_code},
    )
    return [SocLink(r.soc_code, r.title, int(r.entries)) for r in rows]


# One row per title of the coding index (its normalised form), however many entries give it:
# every unit group and ISCO-08 group it is coded to, and the held ESCO release's name for each
# ISCO-08 group.
_UK_TITLE = (
    "SELECT h.normalised, h.title, h.soc_codes, h.isco_codes, "
    "array(SELECT g.label FROM unnest(h.isco_codes) AS c(code) "
    "LEFT JOIN careerwright.isco_groups g ON g.code = c.code ORDER BY c.code) AS isco_labels"
)


def _uk_title(row: Any) -> UkTitle:
    return UkTitle(
        title=row.title,
        normalised=row.normalised,
        soc_codes=tuple(row.soc_codes),
        isco_groups=tuple(
            UkGroup(code, label)
            for code, label in zip(row.isco_codes, row.isco_labels, strict=True)
        ),
    )


def uk_titles(tx: Tx, normalised: Iterable[str]) -> dict[str, UkTitle]:
    """The coding index's titles that are exactly these normalised titles, by normalised
    title (absent: the index lists no such title)."""
    rows = tx.execute(
        sa.text(
            "WITH h AS (SELECT normalised, min(title) AS title, "
            "array_agg(DISTINCT soc_code ORDER BY soc_code) AS soc_codes, "
            "array_agg(DISTINCT isco_code ORDER BY isco_code) AS isco_codes "
            "FROM careerwright.soc2020_index_entries "
            "WHERE normalised = ANY(CAST(:titles AS text[])) GROUP BY normalised) "
            f"{_UK_TITLE} FROM h"
        ),
        {"titles": sorted(set(normalised))},
    )
    return {row.normalised: _uk_title(row) for row in rows}


def uk_title_matches(
    tx: Tx, words: Sequence[str], typed: str, limit: int
) -> tuple[list[UkTitle], int]:
    """The coding index's titles holding a word that begins with each of `words` (whole words
    of the title, any order), one per title, that are not a preferred or alternative label of
    an ESCO occupation as a concept (the type-ahead offers those as ESCO's), and how many there
    are. Best first: the title is what was typed, then begins with it, then the shorter title,
    then by title."""
    prefix = "".join(f"\\{c}" if c in "\\%_" else c for c in typed) + "%"
    rows = tx.execute(
        sa.text(
            "WITH found AS (SELECT normalised, min(title) AS title, "
            "array_agg(DISTINCT soc_code ORDER BY soc_code) AS soc_codes, "
            "array_agg(DISTINCT isco_code ORDER BY isco_code) AS isco_codes "
            "FROM careerwright.soc2020_index_entries "
            "WHERE to_tsvector('simple', title) @@ to_tsquery('simple', :query) "
            "GROUP BY normalised), "
            "h AS (SELECT f.*, count(*) OVER () AS total FROM found f WHERE NOT EXISTS ("
            "SELECT 1 FROM careerwright.occupation_labels l WHERE l.kind <> 'hidden' "
            "AND careerwright.concept_key(l.label) = careerwright.concept_key(f.title))) "
            f"{_UK_TITLE}, h.total FROM h "
            "ORDER BY h.normalised = :typed DESC, h.normalised LIKE :prefix DESC, "
            "char_length(h.title), h.title LIMIT :limit"
        ),
        {
            "query": " & ".join(f"'{word}':*" for word in words),
            "typed": typed,
            "prefix": prefix,
            "limit": limit,
        },
    )
    titles, total = [], 0
    for row in rows:
        total = int(row.total)
        titles.append(_uk_title(row))
    return titles, total


def soc_title_matches(tx: Tx, isco_code: str, labels: Iterable[str]) -> set[str]:
    """The unit groups whose index titles, within the ISCO group, equal one of `labels`."""
    wanted = sorted(set(labels))
    if not wanted:
        return set()
    rows = tx.execute(
        sa.text(
            "SELECT DISTINCT soc_code FROM careerwright.soc2020_index_entries "
            "WHERE isco_code = :isco AND normalised = ANY(:labels)"
        ),
        {"isco": isco_code, "labels": wanted},
    )
    return {r.soc_code for r in rows}


def _benchmark(row: Any) -> PayBenchmark:
    return PayBenchmark(
        soc_code=row.soc_code,
        soc_title=row.soc_title,
        region_code=row.region_code,
        region_name=row.region_name,
        period=AshePeriod(row.period),
        figures=dict(row.figures),
        markers=dict(row.markers),
        jobs_thousands=row.jobs_thousands,
        cvs={s: None if cv is None else Decimal(cv) for s, cv in row.cvs.items()},
    )


def ashe_benchmarks(
    tx: Tx, soc_codes: Iterable[str], region_codes: Iterable[str]
) -> list[PayBenchmark]:
    codes, regions = sorted(set(soc_codes)), sorted(set(region_codes))
    if not codes or not regions:
        return []
    rows = tx.execute(
        sa.text(
            "SELECT soc_code, soc_title, region_code, region_name, period, figures, markers, "
            "jobs_thousands, cvs FROM careerwright.ashe_estimates WHERE soc_code = ANY(:codes) "
            "AND region_code = ANY(:regions) ORDER BY soc_code, region_code, period"
        ),
        {"codes": codes, "regions": regions},
    )
    return [_benchmark(r) for r in rows]


def ilo_exposure(tx: Tx, isco_code: str) -> IloExposure | None:
    row = tx.execute(
        sa.text(
            "SELECT isco_code, title, tasks, mean_score, sd_score, gradient "
            "FROM careerwright.ilo_genai_exposure WHERE isco_code = :isco"
        ),
        {"isco": isco_code},
    ).one_or_none()
    if row is None:
        return None
    return IloExposure(
        row.isco_code,
        row.title,
        row.tasks,
        row.mean_score,
        row.sd_score,
        ExposureGradient(row.gradient),
    )


def crosswalk_matches(tx: Tx, esco_uri: str) -> list[CrosswalkRow]:
    rows = tx.execute(
        sa.text(
            "SELECT onet_code, onet_title, esco_uri, isco_code, target_title, match_type "
            "FROM careerwright.esco_onet_crosswalk WHERE esco_uri = :uri ORDER BY onet_code"
        ),
        {"uri": esco_uri},
    )
    return [
        CrosswalkRow(
            r.onet_code,
            r.onet_title,
            r.esco_uri,
            r.isco_code,
            r.target_title,
            MatchType(r.match_type),
        )
        for r in rows
    ]


@dataclass(frozen=True)
class ObservedTask:
    task: str
    share_pct: Decimal


@dataclass(frozen=True)
class ObservedUse:
    """One O*NET occupation's tasks in the Economic Index release: how many it lists, how
    many the release observed, and the largest observed shares, each as published."""

    onet_code: str
    tasks_listed: int
    tasks_observed: int
    top_tasks: tuple[ObservedTask, ...]


def observed_use(tx: Tx, onet_codes: Iterable[str]) -> dict[str, ObservedUse]:
    codes = sorted(set(onet_codes))
    if not codes:
        return {}
    rows = tx.execute(
        sa.text(
            "SELECT t.onet_code, t.task, u.share_pct FROM careerwright.onet_tasks t "
            "LEFT JOIN careerwright.observed_task_use u ON u.task_name = t.normalised_task "
            "WHERE t.onet_code = ANY(:codes) ORDER BY t.onet_code, u.share_pct DESC NULLS LAST, "
            "t.task_id"
        ),
        {"codes": codes},
    )
    listed: dict[str, int] = {}
    observed: dict[str, list[ObservedTask]] = {}
    for r in rows:
        listed[r.onet_code] = listed.get(r.onet_code, 0) + 1
        if r.share_pct is not None:
            observed.setdefault(r.onet_code, []).append(ObservedTask(r.task, r.share_pct))
    return {
        code: ObservedUse(
            code,
            listed[code],
            len(observed.get(code, [])),
            tuple(observed.get(code, [])[:TOP_TASKS]),
        )
        for code in listed
    }
