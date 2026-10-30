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

from careerwright.catalogue.esco import (
    ADAPTATION,
    ATTRIBUTION,
    LICENCE,
    TRANSFORMATION_VERSION,
    EscoCatalogue,
)
from careerwright.catalogue.esco import label_rows as esco_label_rows
from careerwright.catalogue.records import (
    IscoGroupRef,
    LabelMatch,
    OccupationDetail,
    OccupationFacts,
    OccupationHit,
    ProvisionalConcept,
    SkillNeighbour,
    SkillRef,
    TaxonomyRelease,
    TitleMatch,
)
from careerwright.db import Tx, is_unique_violation

_RELEASE_COLUMNS = (
    "release_id, dataset_id, version, language, source_url, sha256, size_bytes, "
    "native_code_version, transformation_version, licence, attribution, adaptation, sample, "
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
        tx.execute(sa.text(f"SELECT {_RELEASE_COLUMNS} FROM careerwright.taxonomy_releases"))
        .mappings()
        .one_or_none()
    )
    return None if row is None else TaxonomyRelease(**dict(row))


def lock_releases(tx: Tx) -> None:
    """Setup only: serialise imports for the rest of the transaction."""
    tx.execute(sa.text("LOCK TABLE careerwright.taxonomy_releases IN EXCLUSIVE MODE"))


def import_catalogue(tx: Tx, catalogue: EscoCatalogue) -> uuid.UUID:
    """Setup only: write the whole release; the caller's transaction makes it all or nothing."""
    pin = catalogue.pin
    release_id = uuid.uuid4()
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.taxonomy_releases (release_id, taxonomy, dataset_id, "
            "version, "
            "language, source_url, sha256, size_bytes, native_code_version, "
            "transformation_version, licence, attribution, adaptation, sample, "
            "isco_group_count, occupation_count, skill_count, repeated_rows_collapsed) VALUES "
            "(:id, 'esco', :dataset, :version, :language, :url, :sha, :size, :native, "
            ":transform, :licence, :attribution, :adaptation, :sample, :groups, :occupations, "
            ":skills, :collapsed)"
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
            "adaptation": ADAPTATION,
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
        "COPY careerwright.isco_groups (code, release_id, uri, label, broader_code) FROM STDIN",
        ((g.code, release_id, g.uri, g.label, g.broader_code) for g in groups),
    )
    _copy(
        tx,
        "COPY careerwright.occupation_concepts (concept_id, release_id, esco_uri, isco_code, "
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
        "COPY careerwright.occupation_labels (concept_id, label, kind, normalised) FROM STDIN",
        ((i, t, k.value, n) for i, t, k, n in esco_label_rows(catalogue.occupations)),
    )
    _copy(
        tx,
        "COPY careerwright.occupation_broader (concept_id, broader_concept_id, broader_isco_code) "
        "FROM STDIN",
        ((b.concept_id, b.broader_concept_id, b.broader_isco_code) for b in catalogue.broader),
    )
    _copy(
        tx,
        "COPY careerwright.skills (skill_id, release_id, esco_uri, skill_type, reuse_level, "
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
        "COPY careerwright.skill_labels (skill_id, label, kind, normalised) FROM STDIN",
        ((i, t, k.value, n) for i, t, k, n in esco_label_rows(catalogue.skills)),
    )
    _copy(
        tx,
        "COPY careerwright.occupation_skills (concept_id, skill_id, relation) FROM STDIN",
        ((r.concept_id, r.skill_id, r.relation.value) for r in catalogue.occupation_skills),
    )
    _copy(
        tx,
        "COPY careerwright.skill_relations (skill_id, related_skill_id, relation) FROM STDIN",
        ((r.skill_id, r.related_skill_id, r.relation.value) for r in catalogue.skill_relations),
    )
    tx.execute(
        sa.text(
            "WITH labels AS (SELECT concept_id, "
            "string_agg(label, ' ') FILTER (WHERE kind = 'alternative') AS alternative, "
            "string_agg(label, ' ') FILTER (WHERE kind = 'hidden') AS hidden "
            "FROM careerwright.occupation_labels GROUP BY concept_id), "
            "essential AS (SELECT r.concept_id, string_agg(k.preferred_label, ' ') AS skills "
            "FROM careerwright.occupation_skills r JOIN careerwright.skills k ON k.skill_id = "
            "r.skill_id "
            "WHERE r.relation = 'essential' GROUP BY r.concept_id), "
            "vectors AS (SELECT o.concept_id, "
            "setweight(to_tsvector('english', o.preferred_label), 'A') || "
            "setweight(to_tsvector('english', coalesce(l.alternative, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(l.hidden, '') || ' ' || "
            "coalesce(e.skills, '')), 'C') || "
            "setweight(to_tsvector('english', o.description || ' ' || g.label), 'D') AS vector "
            "FROM careerwright.occupation_concepts o JOIN careerwright.isco_groups g ON g.code = "
            "o.isco_code "
            "LEFT JOIN labels l ON l.concept_id = o.concept_id "
            "LEFT JOIN essential e ON e.concept_id = o.concept_id) "
            "UPDATE careerwright.occupation_concepts o SET search_vector = vectors.vector "
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


# Rank weights for the vector's {D, C, B, A} parts (PostgreSQL's order): its defaults, and
# the same with the preferred (A) and alternative (B) labels weighing nothing, so a match on
# a title's words alone ranks 0 (Sprint W: never joined by shared words in a title).
_ALL_PARTS = "'{0.1, 0.2, 0.4, 1.0}'"
_NOT_TITLES = "'{0.1, 0.2, 0, 0}'"


def full_text(
    tx: Tx,
    query: str,
    limit: int,
    *,
    any_word: bool,
    exclude: set[uuid.UUID],
    titles: bool = True,
) -> tuple[list[OccupationHit], int]:
    """The best `limit` full-text matches outside `exclude`, ranked, and how many such
    occupations match in all. `titles=False`: an occupation whose preferred or alternative
    label is all that matches is no match."""
    weights = _ALL_PARTS if titles else _NOT_TITLES
    rows = tx.execute(
        sa.text(
            f"WITH q AS (SELECT {_ANY_WORD if any_word else _ALL_WORDS} AS query), "
            "ranked AS (SELECT o.concept_id, o.preferred_label, o.isco_code, "
            f"ts_rank_cd({weights}, o.search_vector, q.query, 32) AS text_rank "
            "FROM careerwright.occupation_concepts o, q WHERE o.search_vector @@ q.query "
            "AND o.concept_id <> ALL(CAST(:exclude AS uuid[]))) "
            "SELECT r.concept_id, r.preferred_label, r.isco_code, g.label AS isco_label, "
            "r.text_rank, count(*) OVER () AS total "
            "FROM ranked r JOIN careerwright.isco_groups g ON g.code = r.isco_code "
            "WHERE r.text_rank > 0 OR :titles "
            "ORDER BY r.text_rank DESC, r.preferred_label, r.concept_id LIMIT :limit"
        ),
        {
            "q": query,
            "limit": limit,
            "exclude": [str(i) for i in sorted(exclude)],
            "titles": titles,
        },
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
            "FROM careerwright.occupation_labels l "
            "JOIN careerwright.occupation_concepts o ON o.concept_id = l.concept_id "
            "JOIN careerwright.isco_groups g ON g.code = o.isco_code "
            "WHERE l.normalised = :n ORDER BY o.preferred_label, l.concept_id"
        ),
        {"n": normalised},
    ).mappings()
    return [LabelMatch(**dict(row)) for row in rows]


def concept_key_matches(tx: Tx, title: str) -> list[LabelMatch]:
    """Every occupation with a label that is this title as a concept (`careerwright.concept_key`:
    case, punctuation, hyphens and simple plurals folded). Hidden labels match but their
    text is not returned."""
    rows = tx.execute(
        sa.text(
            "SELECT l.concept_id, CASE WHEN l.kind = 'hidden' THEN NULL ELSE l.label END "
            "AS label, l.kind, o.preferred_label, o.isco_code, g.label AS isco_label "
            "FROM careerwright.occupation_labels l "
            "JOIN careerwright.occupation_concepts o ON o.concept_id = l.concept_id "
            "JOIN careerwright.isco_groups g ON g.code = o.isco_code "
            "WHERE careerwright.concept_key(l.label) = careerwright.concept_key(:title) "
            "ORDER BY o.preferred_label, l.concept_id"
        ),
        {"title": title},
    ).mappings()
    return [LabelMatch(**dict(row)) for row in rows]


def title_matches(
    tx: Tx, words: Sequence[str], typed: str, limit: int
) -> tuple[list[TitleMatch], int]:
    """Occupations with a preferred or alternative label holding a word that begins with
    each of `words` (whole words of the label, any order), one per occupation by its best
    label, and how many occupations match in all. Best first: the label is what was typed,
    then begins with it, then a preferred label, then the shorter label, then by label.
    Hidden labels are never offered."""
    prefix = "".join(f"\\{c}" if c in "\\%_" else c for c in typed) + "%"
    query = " & ".join(f"'{word}':*" for word in words)
    rows = tx.execute(
        sa.text(
            "WITH hits AS (SELECT l.concept_id, l.label, l.kind, "
            "l.normalised = :typed AS exact, l.normalised LIKE :prefix AS starts, "
            "row_number() OVER (PARTITION BY l.concept_id ORDER BY l.normalised = :typed DESC, "
            "l.normalised LIKE :prefix DESC, l.kind = 'preferred' DESC, char_length(l.label), "
            "l.label) AS best "
            "FROM careerwright.occupation_labels l "
            "WHERE l.kind <> 'hidden' AND to_tsvector('simple', l.label) @@ "
            "to_tsquery('simple', :query)) "
            "SELECT h.concept_id, h.label, h.kind, o.preferred_label, o.isco_code, "
            "g.label AS isco_label, count(*) OVER () AS total "
            "FROM hits h JOIN careerwright.occupation_concepts o ON o.concept_id = h.concept_id "
            "JOIN careerwright.isco_groups g ON g.code = o.isco_code WHERE h.best = 1 "
            "ORDER BY h.exact DESC, h.starts DESC, h.kind = 'preferred' DESC, "
            "char_length(h.label), h.label, h.concept_id LIMIT :limit"
        ),
        {"typed": typed, "prefix": prefix, "query": query, "limit": limit},
    ).mappings()
    matches, total = [], 0
    for row in rows:
        total = int(row["total"])
        matches.append(TitleMatch(**{k: v for k, v in row.items() if k != "total"}))
    return matches, total


def skill_neighbours(
    tx: Tx, anchors: Iterable[uuid.UUID], minimum: int
) -> tuple[int, list[SkillNeighbour]]:
    """How many distinct essential skills the anchor occupations have together, and every
    other occupation sharing at least `minimum` of them, with its own count."""
    ids = [str(i) for i in sorted(set(anchors))]
    mine = int(
        tx.execute(
            sa.text(
                "SELECT count(DISTINCT skill_id) FROM careerwright.occupation_skills "
                "WHERE concept_id = ANY(CAST(:ids AS uuid[])) AND relation = 'essential'"
            ),
            {"ids": ids},
        ).scalar_one()
    )
    rows = tx.execute(
        sa.text(
            "WITH mine AS (SELECT DISTINCT skill_id FROM careerwright.occupation_skills "
            "WHERE concept_id = ANY(CAST(:ids AS uuid[])) AND relation = 'essential'), "
            "shared AS (SELECT r.concept_id, count(*) AS shared "
            "FROM careerwright.occupation_skills r JOIN mine m ON m.skill_id = r.skill_id "
            "WHERE r.relation = 'essential' AND r.concept_id <> ALL(CAST(:ids AS uuid[])) "
            "GROUP BY r.concept_id HAVING count(*) >= :minimum) "
            "SELECT s.concept_id, s.shared, count(*) AS essential FROM shared s "
            "JOIN careerwright.occupation_skills e ON e.concept_id = s.concept_id "
            "AND e.relation = 'essential' GROUP BY s.concept_id, s.shared"
        ),
        {"ids": ids, "minimum": minimum},
    )
    return mine, [SkillNeighbour(r.concept_id, int(r.shared), int(r.essential)) for r in rows]


def shared_essential_skills(
    tx: Tx, anchors: Iterable[uuid.UUID], other: uuid.UUID
) -> list[SkillRef]:
    """The essential skills `other` shares with the anchor occupations, by label."""
    rows = tx.execute(
        sa.text(
            "SELECT DISTINCT s.skill_id, s.preferred_label, s.skill_type, r.relation "
            "FROM careerwright.occupation_skills r JOIN careerwright.skills s ON s.skill_id = "
            "r.skill_id WHERE r.concept_id = :other AND r.relation = 'essential' "
            "AND r.skill_id IN (SELECT a.skill_id FROM careerwright.occupation_skills a "
            "WHERE a.concept_id = ANY(CAST(:ids AS uuid[])) AND a.relation = 'essential') "
            "ORDER BY s.preferred_label, s.skill_id"
        ),
        {"other": other, "ids": [str(i) for i in sorted(set(anchors))]},
    ).mappings()
    return [SkillRef(**dict(row)) for row in rows]


def concepts_by_uri(tx: Tx, uris: Iterable[str]) -> dict[str, uuid.UUID]:
    """The held release's occupations with these ESCO URIs (unknown URIs are absent)."""
    rows = tx.execute(
        sa.text(
            "SELECT esco_uri, concept_id FROM careerwright.occupation_concepts "
            "WHERE esco_uri = ANY(CAST(:uris AS text[]))"
        ),
        {"uris": sorted(set(uris))},
    )
    return {row.esco_uri: row.concept_id for row in rows}


def occupation(tx: Tx, concept_id: uuid.UUID) -> OccupationDetail | None:
    row = (
        tx.execute(
            sa.text(
                "SELECT o.concept_id, o.esco_uri, o.esco_code, o.preferred_label, "
                "o.description, o.regulated, o.isco_code, b.broader_concept_id "
                "FROM careerwright.occupation_concepts o "
                "LEFT JOIN careerwright.occupation_broader b ON b.concept_id = o.concept_id "
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
            "SELECT label FROM careerwright.occupation_labels WHERE concept_id = :id "
            "AND kind = 'alternative' ORDER BY label"
        ),
        {"id": concept_id},
    ).scalars()
    groups = tx.execute(
        sa.text(
            "SELECT code, label FROM careerwright.isco_groups WHERE :code LIKE code || '%' "
            "ORDER BY char_length(code)"
        ),
        {"code": row["isco_code"]},
    )
    skills = tx.execute(
        sa.text(
            "SELECT s.skill_id, s.preferred_label, s.skill_type, r.relation "
            "FROM careerwright.occupation_skills r JOIN careerwright.skills s ON s.skill_id = "
            "r.skill_id "
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


def occupation_facts(
    tx: Tx, concept_ids: Iterable[uuid.UUID], *, skills_shown: int
) -> dict[uuid.UUID, OccupationFacts]:
    """Discovery's facts for each of these occupations (missing IDs are simply absent): the
    ISCO family is the unit group's minor group (3 digits), the sector its major group."""
    ids = sorted(set(concept_ids))
    if not ids:
        return {}
    rows = tx.execute(
        sa.text(
            "SELECT o.concept_id, o.preferred_label, careerwright.concept_key(o.preferred_label) "
            "AS "
            "preferred_key, o.esco_uri, o.esco_code, o.description, "
            "o.regulated, o.isco_code, unit.label AS unit_label, minor.code AS family_code, "
            "minor.label AS family_label, major.code AS sector_code, major.label AS sector_label "
            "FROM careerwright.occupation_concepts o "
            "JOIN careerwright.isco_groups unit ON unit.code = o.isco_code "
            "JOIN careerwright.isco_groups minor ON minor.code = left(o.isco_code, 3) "
            "JOIN careerwright.isco_groups major ON major.code = left(o.isco_code, 1) "
            "WHERE o.concept_id = ANY(CAST(:ids AS uuid[]))"
        ),
        {"ids": [str(i) for i in ids]},
    ).mappings()
    keys: dict[uuid.UUID, set[str]] = {}
    for label in tx.execute(
        sa.text(
            "SELECT concept_id, careerwright.concept_key(label) AS key FROM "
            "careerwright.occupation_labels "
            "WHERE concept_id = ANY(CAST(:ids AS uuid[])) AND kind <> 'hidden'"
        ),
        {"ids": [str(i) for i in ids]},
    ):
        keys.setdefault(label.concept_id, set()).add(label.key)
    skills: dict[uuid.UUID, list[str]] = {}
    for skill in tx.execute(
        sa.text(
            "SELECT r.concept_id, s.preferred_label FROM careerwright.occupation_skills r "
            "JOIN careerwright.skills s ON s.skill_id = r.skill_id "
            "WHERE r.concept_id = ANY(CAST(:ids AS uuid[])) AND r.relation = 'essential' "
            "ORDER BY r.concept_id, s.preferred_label"
        ),
        {"ids": [str(i) for i in ids]},
    ):
        skills.setdefault(skill.concept_id, []).append(skill.preferred_label)
    facts: dict[uuid.UUID, OccupationFacts] = {}
    for row in rows:
        essential = skills.get(row["concept_id"], [])
        facts[row["concept_id"]] = OccupationFacts(
            concept_id=row["concept_id"],
            preferred_label=row["preferred_label"],
            esco_uri=row["esco_uri"],
            esco_code=row["esco_code"],
            description=row["description"],
            regulated=row["regulated"],
            unit=IscoGroupRef(row["isco_code"], row["unit_label"]),
            family=IscoGroupRef(row["family_code"], row["family_label"]),
            sector=IscoGroupRef(row["sector_code"], row["sector_label"]),
            preferred_key=row["preferred_key"],
            label_keys=frozenset(keys.get(row["concept_id"], ())),
            essential_skills=tuple(essential[:skills_shown]),
            essential_skill_count=len(essential),
        )
    return facts


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
                        "INSERT INTO careerwright.provisional_concepts (concept_id, workspace_id, "
                        "title, "
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
                f"SELECT {_PROVISIONAL_COLUMNS} FROM careerwright.provisional_concepts "
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
            f"SELECT {_PROVISIONAL_COLUMNS} FROM careerwright.provisional_concepts "
            f"WHERE workspace_id = :ws {cursor}ORDER BY created_at, concept_id LIMIT :limit"
        ),
        {
            "ws": workspace_id,
            "limit": limit,
            **({"after_at": after[0], "after_id": after[1]} if after else {}),
        },
    ).mappings()
    return [ProvisionalConcept(**dict(row)) for row in rows]
