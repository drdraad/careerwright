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
    SkillReach,
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
            "FROM careerwright.occupation_concepts o JOIN careerwright.isco_groups g ON g.code = "
            "o.isco_code, "
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


def _skill_words(query: str) -> str:
    """A search's words as a skill's name is read: a hyphen is read as a space. The English
    parser keeps "first-aid" whole beside its parts, so its query would also need that whole
    word, which no skill named "provide first aid" holds (Task W2C). A hyphenated name keeps
    its parts in its vector, so "e learning" still reaches "use e-learning platforms". Ranking
    is unchanged; but such a name typed with its hyphen no longer counts as named by exactly
    the search's words, since its vector keeps the whole hyphenated word the search drops."""
    return query.replace("-", " ")


def essential_skill_reach(
    tx: Tx, query: str, limit: int
) -> tuple[list[SkillReach], int, int, bool]:
    """The occupations reached through an essential skill whose preferred label holds every
    word of the query (`skills.search_vector`, the label alone; English stems, stop words
    dropped, a hyphen read as a space, no search operators), each by its best-ranked such
    skill; how many occupations
    are reached in all; how many different essential skills reach them; and whether one of
    those skills is named by exactly the query's words ("sell products" for "selling
    products"; a hyphenated name typed with its hyphen is not, `_skill_words`). Best first:
    equal ranks go to the occupation whose essential skills the
    query matches the larger share of. The best `limit` and every occupation tied with the
    last of them on both (a cut never falls inside an exact tie), the title ordering only
    what is kept. No title, hidden label, ISCO group or description is searched."""
    rows = tx.execute(
        sa.text(
            "WITH q AS (SELECT plainto_tsquery('english', :q) AS query, "
            "strip(to_tsvector('english', :q)) AS words), "
            "matched AS (SELECT s.skill_id, s.preferred_label, "
            "ts_rank_cd(s.search_vector, q.query, 32) AS text_rank, "
            "strip(s.search_vector) = q.words AS exact "
            "FROM careerwright.skills s, q WHERE s.search_vector @@ q.query), "
            "reached AS (SELECT r.concept_id, m.skill_id, m.preferred_label, m.text_rank, "
            "m.exact, row_number() OVER (PARTITION BY r.concept_id ORDER BY m.text_rank DESC, "
            "m.preferred_label, m.skill_id) AS best, "
            "array_agg(m.skill_id) OVER (PARTITION BY r.concept_id) AS skills "
            "FROM matched m JOIN careerwright.occupation_skills r ON r.skill_id = m.skill_id "
            "AND r.relation = 'essential'), "
            "essential AS (SELECT e.concept_id, count(*) AS skills "
            "FROM careerwright.occupation_skills e WHERE e.relation = 'essential' "
            "AND e.concept_id IN (SELECT concept_id FROM reached) GROUP BY e.concept_id), "
            "spread AS (SELECT count(DISTINCT skill_id) AS skills, "
            "coalesce(bool_or(exact), false) AS exact FROM reached), "
            "kept AS (SELECT r.concept_id, r.skill_id, r.preferred_label AS skill_label, "
            "r.text_rank, r.skills, cardinality(r.skills)::float8 / e.skills AS share, "
            "count(*) OVER () AS total FROM reached r "
            "JOIN essential e ON e.concept_id = r.concept_id WHERE r.best = 1 "
            "ORDER BY r.text_rank DESC, share DESC FETCH FIRST (:limit) ROWS WITH TIES) "
            "SELECT k.concept_id, k.skill_id, k.skill_label, k.text_rank, k.skills, k.total, "
            "spread.skills AS reached_skills, spread.exact "
            "FROM kept k CROSS JOIN spread "
            "JOIN careerwright.occupation_concepts o ON o.concept_id = k.concept_id "
            "ORDER BY k.text_rank DESC, k.share DESC, o.preferred_label, k.concept_id"
        ),
        {"q": _skill_words(query), "limit": limit},
    ).mappings()
    reached, total, skills, exact = [], 0, 0, False
    for row in rows:
        total, skills, exact = int(row["total"]), int(row["reached_skills"]), bool(row["exact"])
        reached.append(
            SkillReach(
                concept_id=row["concept_id"],
                skill_id=row["skill_id"],
                skill_label=row["skill_label"],
                text_rank=float(row["text_rank"]),
                skills=frozenset(row["skills"]),
            )
        )
    return reached, total, skills, exact


def essential_skill_reach_among(
    tx: Tx, query: str, concepts: Iterable[uuid.UUID]
) -> list[SkillReach]:
    """Of `concepts`, those the query reaches as `essential_skill_reach` does, each by its
    best-ranked such skill, with no cut: for a search too general to find work on its own,
    which only adds weight to occupations another search found."""
    rows = tx.execute(
        sa.text(
            "WITH q AS (SELECT plainto_tsquery('english', :q) AS query), "
            "matched AS (SELECT s.skill_id, s.preferred_label, "
            "ts_rank_cd(s.search_vector, q.query, 32) AS text_rank "
            "FROM careerwright.skills s, q WHERE s.search_vector @@ q.query), "
            "reached AS (SELECT r.concept_id, m.skill_id, m.preferred_label, m.text_rank, "
            "row_number() OVER (PARTITION BY r.concept_id ORDER BY m.text_rank DESC, "
            "m.preferred_label, m.skill_id) AS best, "
            "array_agg(m.skill_id) OVER (PARTITION BY r.concept_id) AS skills "
            "FROM matched m JOIN careerwright.occupation_skills r ON r.skill_id = m.skill_id "
            "AND r.relation = 'essential' AND r.concept_id = ANY(CAST(:concepts AS uuid[]))) "
            "SELECT concept_id, skill_id, preferred_label AS skill_label, text_rank, skills "
            "FROM reached WHERE best = 1 ORDER BY concept_id"
        ),
        {"q": _skill_words(query), "concepts": [str(c) for c in sorted(set(concepts))]},
    ).mappings()
    return [
        SkillReach(
            concept_id=row["concept_id"],
            skill_id=row["skill_id"],
            skill_label=row["skill_label"],
            text_rank=float(row["text_rank"]),
            skills=frozenset(row["skills"]),
        )
        for row in rows
    ]


def concept_keys(tx: Tx, texts: Iterable[str]) -> dict[str, str]:
    """Each text as a concept (`careerwright.concept_key`: case, punctuation, hyphens and
    simple plurals folded), by text."""
    rows = tx.execute(
        sa.text(
            "SELECT t AS text, careerwright.concept_key(t) AS key "
            "FROM unnest(CAST(:texts AS text[])) AS t"
        ),
        {"texts": sorted(set(texts))},
    )
    return {row.text: row.key for row in rows}


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
    return _title_matches(rows)


def partial_title_matches(tx: Tx, words: Sequence[str], limit: int) -> tuple[list[TitleMatch], int]:
    """For when no label holds every typed word: the occupations whose preferred or
    alternative labels hold the most of `words` (each beginning a word of the label), one
    per occupation by its best label, and how many there are. Best first: the label holding
    more of the words whole (so "nurse" finds the nurses before a "nursery" title), then the
    label whose words are rarer among ESCO's titles (a word's count is how many of these
    occupations hold it, so "bookkeeping" outranks "assistant"), then a preferred label, then
    the shorter label, then by label. None when no label holds any of them. Hidden labels
    are never offered."""
    rows = tx.execute(
        sa.text(
            "WITH typed AS (SELECT w, to_tsquery('simple', quote_literal(w) || ':*') AS q, "
            "to_tsquery('simple', quote_literal(w)) AS whole "
            "FROM unnest(CAST(:words AS text[])) AS w), "
            "labels AS (SELECT l.concept_id, l.label, l.kind, "
            "to_tsvector('simple', l.label) AS v FROM careerwright.occupation_labels l "
            "WHERE l.kind <> 'hidden' AND to_tsvector('simple', l.label) @@ "
            "to_tsquery('simple', :any)), "
            "held AS (SELECT b.concept_id, b.label, b.kind, t.w, b.v @@ t.whole AS whole "
            "FROM labels b JOIN typed t ON b.v @@ t.q), "
            "reach AS (SELECT w, count(DISTINCT concept_id) AS occupations FROM held "
            "GROUP BY w), "
            "scored AS (SELECT h.concept_id, h.label, h.kind, count(*) AS words, "
            "count(*) FILTER (WHERE h.whole) AS whole_words, "
            "sum(r.occupations) AS commonness FROM held h JOIN reach r ON r.w = h.w "
            "GROUP BY h.concept_id, h.label, h.kind), "
            "best AS (SELECT s.*, row_number() OVER (PARTITION BY s.concept_id ORDER BY "
            "s.words DESC, s.whole_words DESC, s.commonness, s.kind = 'preferred' DESC, "
            "char_length(s.label), s.label) AS n, max(s.words) OVER () AS most FROM scored s) "
            "SELECT b.concept_id, b.label, b.kind, o.preferred_label, o.isco_code, "
            "g.label AS isco_label, count(*) OVER () AS total "
            "FROM best b JOIN careerwright.occupation_concepts o ON o.concept_id = b.concept_id "
            "JOIN careerwright.isco_groups g ON g.code = o.isco_code "
            "WHERE b.n = 1 AND b.words = b.most "
            "ORDER BY b.whole_words DESC, b.commonness, b.kind = 'preferred' DESC, "
            "char_length(b.label), b.label, b.concept_id LIMIT :limit"
        ),
        {
            "words": list(words),
            "any": " | ".join(f"'{word}':*" for word in words),
            "limit": limit,
        },
    ).mappings()
    return _title_matches(rows)


def _title_matches(rows: Iterable[sa.RowMapping]) -> tuple[list[TitleMatch], int]:
    matches, total = [], 0
    for row in rows:
        total = int(row["total"])
        matches.append(TitleMatch(**{k: v for k, v in row.items() if k != "total"}))
    return matches, total


def skill_neighbours(
    tx: Tx, anchors: Iterable[uuid.UUID], minimum: int
) -> tuple[int, list[SkillNeighbour]]:
    """How many distinct essential skills the anchor occupations have together, and every
    other occupation sharing at least `minimum` of them, with the skills it shares and its
    own count."""
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
            "shared AS (SELECT r.concept_id, count(*) AS shared, array_agg(r.skill_id) AS skills "
            "FROM careerwright.occupation_skills r JOIN mine m ON m.skill_id = r.skill_id "
            "WHERE r.relation = 'essential' AND r.concept_id <> ALL(CAST(:ids AS uuid[])) "
            "GROUP BY r.concept_id HAVING count(*) >= :minimum) "
            "SELECT s.concept_id, s.shared, s.skills, count(*) AS essential FROM shared s "
            "JOIN careerwright.occupation_skills e ON e.concept_id = s.concept_id "
            "AND e.relation = 'essential' GROUP BY s.concept_id, s.shared, s.skills"
        ),
        {"ids": ids, "minimum": minimum},
    )
    return mine, [
        SkillNeighbour(r.concept_id, int(r.shared), int(r.essential), frozenset(r.skills))
        for r in rows
    ]


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
