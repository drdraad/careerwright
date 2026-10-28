"""SQL for the ESCO taxonomy and provisional concepts (adapter).

The import runs under the migration owner (setup only), in one transaction, with the bulk
rows sent by COPY. Reads run under the API role: ESCO tables are public reference data;
provisional concepts are workspace-scoped by row-level security.
"""

import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from nessa.catalogue.esco import ATTRIBUTION, LICENCE, TRANSFORMATION_VERSION, EscoCatalogue
from nessa.catalogue.esco import label_rows as esco_label_rows
from nessa.catalogue.records import (
    IscoGroupRef,
    LabelMatch,
    OccupationDetail,
    OccupationHit,
    ProvisionalConcept,
    SkillRef,
    TaxonomyRelease,
)
from nessa.db import Tx, is_unique_violation

_RELEASE_COLUMNS = (
    "release_id, dataset_id, version, language, source_url, sha256, size_bytes, "
    "native_code_version, transformation_version, licence, attribution, sample, "
    "isco_group_count, occupation_count, skill_count, repeated_rows_collapsed, imported_at"
)
_PROVISIONAL_COLUMNS = "concept_id, workspace_id, title, source_ref_id, created_by, created_at"


def _copy(tx: Tx, statement: str, rows: Iterable[Sequence[object]]) -> None:
    raw = tx.connection.driver_connection
    with raw.cursor() as cursor, cursor.copy(statement) as copy:  # type: ignore[union-attr]
        for row in rows:
            copy.write_row(row)


def release(tx: Tx) -> TaxonomyRelease | None:
    row = (
        tx.execute(sa.text(f"SELECT {_RELEASE_COLUMNS} FROM nessa.taxonomy_releases"))
        .mappings()
        .one_or_none()
    )
    return None if row is None else TaxonomyRelease(**dict(row))


def lock_releases(tx: Tx) -> None:
    """Setup only: serialise imports for the rest of the transaction."""
    tx.execute(sa.text("LOCK TABLE nessa.taxonomy_releases IN EXCLUSIVE MODE"))


def import_catalogue(tx: Tx, catalogue: EscoCatalogue) -> uuid.UUID:
    """Setup only: write the whole release; the caller's transaction makes it all or nothing."""
    pin = catalogue.pin
    release_id = uuid.uuid4()
    tx.execute(
        sa.text(
            "INSERT INTO nessa.taxonomy_releases (release_id, taxonomy, dataset_id, version, "
            "language, source_url, sha256, size_bytes, native_code_version, "
            "transformation_version, licence, attribution, sample, isco_group_count, "
            "occupation_count, skill_count, repeated_rows_collapsed) VALUES (:id, 'esco', "
            ":dataset, :version, :language, :url, :sha, :size, :native, :transform, :licence, "
            ":attribution, :sample, :groups, :occupations, :skills, :collapsed)"
        ),
        {
            "id": release_id,
            "dataset": pin.dataset_id,
            "version": pin.version,
            "language": pin.language,
            "url": pin.url,
            "sha": pin.sha256,
            "size": pin.size_bytes,
            "native": pin.native_code_version,
            "transform": TRANSFORMATION_VERSION,
            "licence": LICENCE,
            "attribution": ATTRIBUTION,
            "sample": pin.sample,
            "groups": len(catalogue.isco_groups),
            "occupations": len(catalogue.occupations),
            "skills": len(catalogue.skills),
            "collapsed": catalogue.repeated_rows_collapsed,
        },
    )
    # Parents first: the broader code is a foreign key.
    groups = sorted(catalogue.isco_groups, key=lambda g: (len(g.code), g.code))
    _copy(
        tx,
        "COPY nessa.isco_groups (code, release_id, uri, label, broader_code) FROM STDIN",
        ((g.code, release_id, g.uri, g.label, g.broader_code) for g in groups),
    )
    _copy(
        tx,
        "COPY nessa.occupation_concepts (concept_id, release_id, esco_uri, isco_code, "
        "esco_code, preferred_label, description, regulated) FROM STDIN",
        (
            (
                o.concept_id,
                release_id,
                o.uri,
                o.isco_code,
                o.esco_code,
                o.preferred_label,
                o.description,
                o.regulated,
            )
            for o in catalogue.occupations
        ),
    )
    _copy(
        tx,
        "COPY nessa.occupation_labels (concept_id, label, kind, normalised) FROM STDIN",
        ((i, t, k.value, n) for i, t, k, n in esco_label_rows(catalogue.occupations)),
    )
    _copy(
        tx,
        "COPY nessa.occupation_broader (concept_id, broader_concept_id, broader_isco_code) "
        "FROM STDIN",
        ((b.concept_id, b.broader_concept_id, b.broader_isco_code) for b in catalogue.broader),
    )
    _copy(
        tx,
        "COPY nessa.skills (skill_id, release_id, esco_uri, skill_type, reuse_level, "
        "preferred_label, description) FROM STDIN",
        (
            (
                s.skill_id,
                release_id,
                s.uri,
                s.skill_type,
                s.reuse_level,
                next(label.text for label in s.labels),
                s.description,
            )
            for s in catalogue.skills
        ),
    )
    _copy(
        tx,
        "COPY nessa.skill_labels (skill_id, label, kind, normalised) FROM STDIN",
        ((i, t, k.value, n) for i, t, k, n in esco_label_rows(catalogue.skills)),
    )
    _copy(
        tx,
        "COPY nessa.occupation_skills (concept_id, skill_id, relation) FROM STDIN",
        ((r.concept_id, r.skill_id, r.relation.value) for r in catalogue.occupation_skills),
    )
    _copy(
        tx,
        "COPY nessa.skill_relations (skill_id, related_skill_id, relation) FROM STDIN",
        ((r.skill_id, r.related_skill_id, r.relation.value) for r in catalogue.skill_relations),
    )
    tx.execute(
        sa.text(
            "WITH labels AS (SELECT concept_id, "
            "string_agg(label, ' ') FILTER (WHERE kind = 'alternative') AS alternative, "
            "string_agg(label, ' ') FILTER (WHERE kind = 'hidden') AS hidden "
            "FROM nessa.occupation_labels GROUP BY concept_id), "
            "essential AS (SELECT r.concept_id, string_agg(k.preferred_label, ' ') AS skills "
            "FROM nessa.occupation_skills r JOIN nessa.skills k ON k.skill_id = r.skill_id "
            "WHERE r.relation = 'essential' GROUP BY r.concept_id), "
            "vectors AS (SELECT o.concept_id, "
            "setweight(to_tsvector('english', o.preferred_label), 'A') || "
            "setweight(to_tsvector('english', coalesce(l.alternative, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(l.hidden, '') || ' ' || "
            "coalesce(e.skills, '')), 'C') || "
            "setweight(to_tsvector('english', o.description || ' ' || g.label), 'D') AS vector "
            "FROM nessa.occupation_concepts o JOIN nessa.isco_groups g ON g.code = o.isco_code "
            "LEFT JOIN labels l ON l.concept_id = o.concept_id "
            "LEFT JOIN essential e ON e.concept_id = o.concept_id) "
            "UPDATE nessa.occupation_concepts o SET search_vector = vectors.vector "
            "FROM vectors WHERE vectors.concept_id = o.concept_id"
        )
    )
    return release_id


# Every word (web-search syntax: quotes, "or", "-word"), or any word (ranked by how many
# and how close: for broad task and interest queries).
_ALL_WORDS = "websearch_to_tsquery('english', :q)"
_ANY_WORD = "replace(plainto_tsquery('english', :q)::text, ' & ', ' | ')::tsquery"


def search_terms(tx: Tx, query: str) -> int:
    """How many searchable lexemes the query has (0: only stop words or punctuation)."""
    return int(tx.execute(sa.text(f"SELECT numnode({_ALL_WORDS})"), {"q": query}).scalar_one())


def full_text(
    tx: Tx, query: str, limit: int, *, any_word: bool, exclude: set[uuid.UUID]
) -> tuple[list[OccupationHit], int]:
    """The best `limit` full-text matches outside `exclude`, ranked, and how many such
    occupations match in all."""
    rows = tx.execute(
        sa.text(
            f"WITH q AS (SELECT {_ANY_WORD if any_word else _ALL_WORDS} AS query) "
            "SELECT o.concept_id, o.preferred_label, o.isco_code, g.label AS isco_label, "
            "ts_rank_cd(o.search_vector, q.query, 32) AS text_rank, "
            "count(*) OVER () AS total "
            "FROM nessa.occupation_concepts o JOIN nessa.isco_groups g ON g.code = o.isco_code, "
            "q WHERE o.search_vector @@ q.query "
            "AND o.concept_id <> ALL(CAST(:exclude AS uuid[])) "
            "ORDER BY text_rank DESC, o.preferred_label, o.concept_id LIMIT :limit"
        ),
        {"q": query, "limit": limit, "exclude": [str(i) for i in sorted(exclude)]},
    ).mappings()
    hits, total = [], 0
    for row in rows:
        total = int(row["total"])
        hits.append(
            OccupationHit(
                concept_id=row["concept_id"],
                preferred_label=row["preferred_label"],
                isco_code=row["isco_code"],
                isco_label=row["isco_label"],
                text_rank=float(row["text_rank"]),
            )
        )
    return hits, total


def label_matches(tx: Tx, normalised: str) -> list[LabelMatch]:
    """Every occupation with this exact (normalised) label. Hidden labels match but their
    text is not returned (they exist for search, not display)."""
    rows = tx.execute(
        sa.text(
            "SELECT l.concept_id, CASE WHEN l.kind = 'hidden' THEN NULL ELSE l.label END "
            "AS label, l.kind, o.preferred_label, o.isco_code, g.label AS isco_label "
            "FROM nessa.occupation_labels l "
            "JOIN nessa.occupation_concepts o ON o.concept_id = l.concept_id "
            "JOIN nessa.isco_groups g ON g.code = o.isco_code "
            "WHERE l.normalised = :n ORDER BY o.preferred_label, l.concept_id"
        ),
        {"n": normalised},
    ).mappings()
    return [LabelMatch(**dict(row)) for row in rows]


def occupation(tx: Tx, concept_id: uuid.UUID) -> OccupationDetail | None:
    row = (
        tx.execute(
            sa.text(
                "SELECT o.concept_id, o.esco_uri, o.esco_code, o.preferred_label, "
                "o.description, o.regulated, o.isco_code, b.broader_concept_id "
                "FROM nessa.occupation_concepts o "
                "LEFT JOIN nessa.occupation_broader b ON b.concept_id = o.concept_id "
                "WHERE o.concept_id = :id"
            ),
            {"id": concept_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    labels = tx.execute(
        sa.text(
            "SELECT label FROM nessa.occupation_labels WHERE concept_id = :id "
            "AND kind = 'alternative' ORDER BY label"
        ),
        {"id": concept_id},
    ).scalars()
    groups = tx.execute(
        sa.text(
            "SELECT code, label FROM nessa.isco_groups WHERE :code LIKE code || '%' "
            "ORDER BY char_length(code)"
        ),
        {"code": row["isco_code"]},
    )
    skills = tx.execute(
        sa.text(
            "SELECT s.skill_id, s.preferred_label, s.skill_type, r.relation "
            "FROM nessa.occupation_skills r JOIN nessa.skills s ON s.skill_id = r.skill_id "
            "WHERE r.concept_id = :id ORDER BY r.relation, s.preferred_label"
        ),
        {"id": concept_id},
    ).mappings()
    return OccupationDetail(
        concept_id=row["concept_id"],
        esco_uri=row["esco_uri"],
        esco_code=row["esco_code"],
        preferred_label=row["preferred_label"],
        alternative_labels=tuple(labels),
        description=row["description"],
        regulated=row["regulated"],
        isco_groups=tuple(IscoGroupRef(g.code, g.label) for g in groups),
        broader_concept_id=row["broader_concept_id"],
        skills=tuple(SkillRef(**dict(s)) for s in skills),
    )


def insert_provisional(
    tx: Tx,
    *,
    concept_id: uuid.UUID,
    workspace_id: uuid.UUID,
    title: str,
    normalised_title: str,
    source_ref_id: uuid.UUID,
    created_by: uuid.UUID,
) -> ProvisionalConcept | None:
    """None if the workspace already holds this title."""
    try:
        with tx.begin_nested():
            row = (
                tx.execute(
                    sa.text(
                        "INSERT INTO nessa.provisional_concepts (concept_id, workspace_id, title, "
                        "normalised_title, source_ref_id, created_by) VALUES (:id, :ws, :title, "
                        f":n, :source, :by) RETURNING {_PROVISIONAL_COLUMNS}"
                    ),
                    {
                        "id": concept_id,
                        "ws": workspace_id,
                        "title": title,
                        "n": normalised_title,
                        "source": source_ref_id,
                        "by": created_by,
                    },
                )
                .mappings()
                .one()
            )
    except exc.IntegrityError as error:
        if is_unique_violation(error):
            return None
        raise
    return ProvisionalConcept(**dict(row))


def provisional_by_title(
    tx: Tx, workspace_id: uuid.UUID, normalised_title: str
) -> ProvisionalConcept | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_PROVISIONAL_COLUMNS} FROM nessa.provisional_concepts "
                "WHERE workspace_id = :ws AND normalised_title = :n"
            ),
            {"ws": workspace_id, "n": normalised_title},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else ProvisionalConcept(**dict(row))


def provisional_concepts(
    tx: Tx, workspace_id: uuid.UUID, *, after: tuple[datetime, uuid.UUID] | None, limit: int
) -> list[ProvisionalConcept]:
    cursor = "AND (created_at, concept_id) > (:after_at, :after_id) " if after else ""
    rows = tx.execute(
        sa.text(
            f"SELECT {_PROVISIONAL_COLUMNS} FROM nessa.provisional_concepts "
            f"WHERE workspace_id = :ws {cursor}ORDER BY created_at, concept_id LIMIT :limit"
        ),
        {
            "ws": workspace_id,
            "limit": limit,
            **({"after_at": after[0], "after_id": after[1]} if after else {}),
        },
    ).mappings()
    return [ProvisionalConcept(**dict(row)) for row in rows]
