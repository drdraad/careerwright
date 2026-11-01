"""Each target is stored once, and a title is a concept whatever its "&" or accents (Task 6d
slice A; ADR 0015 decision 3, ADR 0012 and ADR 0007 as amended on 2026-10-31; the audit's
code appendix, finding F5).

- `careerwright.concept_key(text)` also reads "&" as "and" and folds accents: every letter of
  Unicode's Latin-1 Supplement and Latin Extended-A blocks that decomposes to one ASCII
  letter and accents becomes that letter (NFKD), in either case, before the case is folded.
  So "distribution and logistics manager" is ESCO's "distribution & logistics manager", and
  "saute cook" its "sauté cook". The key is defined only here, so it changes only by a
  forward migration: the expression index over every occupation label is rebuilt, and no
  other stored value holds a key made before this one.
- `target_records`: one row per target title of a workspace, by the title as a concept. It
  holds the ESCO occupation the target names (or none), the source of that link (the
  person's choice of an occupation, the one occupation holding the title as a label, the
  option pack's crosswalk, or none yet), every occupation holding the title as a label
  (several: the person chooses, none is guessed), and whether the target is one of the
  option pack's targets. Every module reads it instead of resolving the title again.
  Slice B's kinds have room already: a UK title from the ONS coding index (`kind = 'ons'`,
  with its SOC 2020 and ISCO-08 codes) and "None of these is my job" (`none_of_these`).
- Existing profiles migrate forward: each target title of a workspace's current profile
  gets its record, by the same rules as `careerwright.profile.targets.resolve_target`, with
  the pinned option pack's targets and crosswalks below (pack 0.1.0, capability reference
  0.1.0; `test_targets.py` checks them against the committed files).

Forward-only (see `docs/runbook.md`).

Revision ID: 0034
"""

from careerwright.migrations.sql import run_script

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None

# Every letter of Latin-1 Supplement and Latin Extended-A that decomposes (NFKD) to one ASCII
# letter and accents, and that letter in lower case.
ACCENTED = (
    "ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüýÿĀāĂăĄąĆćĈĉĊċČčĎďĒēĔĕĖėĘęĚěĜĝĞğĠġĢģ"
    "ĤĥĨĩĪīĬĭĮįİĴĵĶķĹĺĻļĽľŃńŅņŇňŌōŎŏŐőŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽžſ"
)
PLAIN = (
    "aaaaaaceeeeiiiinooooouuuuyaaaaaaceeeeiiiinooooouuuuyyaaaaaaccccccccddeeeeeeeeeegggggggg"
    "hhiiiiiiiiijjkkllllllnnnnnnoooooorrrrrrssssssssttttuuuuuuuuuuuuwwyyyzzzzzzs"
)

# The pinned option pack's targets (0.1.0) and the ESCO occupations their crosswalks name
# (capability reference 0.1.0), as the capability model loads them.
PACK_VERSION = "0.1.0"
PACK_TARGETS = (
    (
        "data-quality-analyst-manchester",
        "Data quality analyst",
        "http://data.europa.eu/esco/occupation/7086d0ca-1e77-4690-89c9-7ed1a0478fa3",
    ),
    (
        "it-support-technician-bristol",
        "IT support technician",
        "http://data.europa.eu/esco/occupation/aaeec9a7-dc57-4485-890c-86b3eef735f9",
    ),
    (
        "registered-nurse-manchester",
        "Registered nurse",
        "http://data.europa.eu/esco/occupation/8d3e8aaa-791b-4c75-a465-f3f827028f50",
    ),
    (
        "bookkeeping-assistant-leeds",
        "Bookkeeping assistant",
        "http://data.europa.eu/esco/occupation/c3aae59e-1441-4b3e-bdd1-6da50dc7cf42",
    ),
)

# Built from this module's own constants only, never from input.
CONCEPT_KEY = f"""
CREATE OR REPLACE FUNCTION careerwright.concept_key(title text) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    RETURN (
        SELECT coalesce(string_agg(
            CASE
                WHEN w ~ '[^aeiou]ies$' AND length(w) > 4 THEN left(w, -3) || 'y'
                WHEN length(w) <= 3 OR w ~ '(ss|us|is)$' THEN w
                WHEN w ~ 's$' THEN left(w, -1)
                ELSE w
            END, ' ' ORDER BY n), '')
        FROM regexp_split_to_table(
            lower(translate(replace(title, '&', ' and '), '{ACCENTED}', '{PLAIN}')),
            '[^[:alnum:]]+'
        ) WITH ORDINALITY AS t(w, n)
        WHERE w <> ''
    );
COMMENT ON FUNCTION careerwright.concept_key(text) IS
    'A title compared as a concept: "&" read as "and", accents, case, punctuation, hyphens and '
    'simple plurals folded.';
REINDEX INDEX careerwright.occupation_labels_concept_key;
"""  # noqa: S608

SCHEMA = """
CREATE TABLE careerwright.target_records (
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    title_key text NOT NULL,
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120),
    kind text NOT NULL CHECK (kind IN ('esco', 'ons', 'own_words')),
    soc_codes text[] NOT NULL DEFAULT '{}',
    isco_codes text[] NOT NULL DEFAULT '{}',
    occupation_uri text CHECK (occupation_uri ~ '^http://data\\.europa\\.eu/esco/occupation/'),
    link text NOT NULL CHECK (link IN ('occupation_choice', 'exact_label', 'pack_crosswalk',
        'none', 'none_of_these')),
    label_matches text[] NOT NULL DEFAULT '{}',
    coverage text NOT NULL CHECK (coverage IN ('pack_target', 'not_covered',
        'several_pack_targets')),
    pack_target_id text,
    pack_target_basis text CHECK (pack_target_basis IN ('title', 'esco_crosswalk')),
    pack_version text NOT NULL,
    source_ref_id uuid,
    recorded_by uuid REFERENCES careerwright.actors (actor_id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, title_key),
    FOREIGN KEY (workspace_id, source_ref_id)
        REFERENCES careerwright.source_references (workspace_id, source_ref_id),
    CONSTRAINT a_link_names_its_occupation CHECK (
        (link IN ('none', 'none_of_these')) = (occupation_uri IS NULL)
    ),
    CONSTRAINT a_choice_cites_its_source CHECK (
        (link = 'occupation_choice') = (source_ref_id IS NOT NULL)
    ),
    CONSTRAINT an_exact_label_is_the_one_label_match CHECK (
        link <> 'exact_label' OR label_matches = ARRAY[occupation_uri]
    ),
    CONSTRAINT a_crosswalk_link_is_a_pack_target CHECK (
        link <> 'pack_crosswalk' OR coverage = 'pack_target'
    ),
    CONSTRAINT a_pack_target_names_itself CHECK (
        (coverage = 'pack_target') = (pack_target_id IS NOT NULL)
        AND (pack_target_id IS NULL) = (pack_target_basis IS NULL)
    ),
    CONSTRAINT only_an_ons_title_has_ons_codes CHECK (
        kind = 'ons' OR (soc_codes = '{}' AND isco_codes = '{}')
    )
);
COMMENT ON TABLE careerwright.target_records IS
    'Each target title once, by its concept key: the ESCO occupation it names (or none), the '
    'source of that link, every occupation holding the title as a label, and whether it is one '
    'of the option pack''s targets. Written when a target is chosen or saved; every module '
    'reads it instead of resolving the title again.';

ALTER TABLE careerwright.target_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.target_records TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT, UPDATE ON careerwright.target_records TO careerwright_api;
"""


def _pack_values() -> str:
    return ", ".join(f"('{target}', '{title}', '{uri}')" for target, title, uri in PACK_TARGETS)


# Built from this module's own constants only, never from input.
BACKFILL = f"""
WITH pack (target_id, title, esco_uri) AS (VALUES {_pack_values()}),
pack_keys AS (
    SELECT target_id, careerwright.concept_key(title) AS key, esco_uri FROM pack
),
latest AS (
    SELECT DISTINCT ON (workspace_id) workspace_id, document
    FROM careerwright.profile_versions ORDER BY workspace_id, version DESC
),
titles AS (
    SELECT l.workspace_id, t.title, careerwright.concept_key(t.title) AS key, t.n
    FROM latest l,
        jsonb_array_elements_text(l.document -> 'target_titles' -> 'value')
            WITH ORDINALITY AS t(title, n)
    WHERE l.document -> 'target_titles' ->> 'state' = 'provided'
),
firsts AS (
    SELECT DISTINCT ON (workspace_id, key) workspace_id, title, key
    FROM titles ORDER BY workspace_id, key, n
),
chosen AS (
    SELECT DISTINCT ON (s.workspace_id, careerwright.concept_key(o.preferred_label))
        s.workspace_id, careerwright.concept_key(o.preferred_label) AS key, o.esco_uri,
        s.source_ref_id
    FROM careerwright.source_references s
    JOIN careerwright.occupation_concepts o ON o.esco_uri = s.locator
    WHERE s.kind = 'occupation_choice'
    ORDER BY s.workspace_id, careerwright.concept_key(o.preferred_label), s.created_at DESC,
        s.source_ref_id DESC
),
labelled AS (
    SELECT f.workspace_id, f.key,
        array_agg(DISTINCT o.esco_uri ORDER BY o.esco_uri) AS uris
    FROM firsts f
    JOIN careerwright.occupation_labels l ON careerwright.concept_key(l.label) = f.key
    JOIN careerwright.occupation_concepts o ON o.concept_id = l.concept_id
    GROUP BY f.workspace_id, f.key
),
linked AS (
    SELECT f.workspace_id, f.title, f.key, c.source_ref_id,
        coalesce(b.uris, '{{}}') AS label_matches, p.target_id AS titled, p.esco_uri AS crosswalk,
        CASE
            WHEN c.esco_uri IS NOT NULL THEN 'occupation_choice'
            WHEN cardinality(b.uris) = 1 THEN 'exact_label'
            WHEN p.target_id IS NOT NULL THEN 'pack_crosswalk'
            ELSE 'none'
        END AS link,
        CASE
            WHEN c.esco_uri IS NOT NULL THEN c.esco_uri
            WHEN cardinality(b.uris) = 1 THEN b.uris[1]
            ELSE p.esco_uri
        END AS occupation_uri
    FROM firsts f
    LEFT JOIN chosen c ON c.workspace_id = f.workspace_id AND c.key = f.key
    LEFT JOIN labelled b ON b.workspace_id = f.workspace_id AND b.key = f.key
    LEFT JOIN pack_keys p ON p.key = f.key
),
covered AS (
    SELECT k.*,
        (SELECT array_agg(x.target_id ORDER BY x.target_id) FROM pack_keys x
            WHERE x.esco_uri = k.occupation_uri) AS crosswalked
    FROM linked k
)
INSERT INTO careerwright.target_records (workspace_id, title_key, title, kind, occupation_uri,
    link, label_matches, coverage, pack_target_id, pack_target_basis, pack_version,
    source_ref_id)
SELECT workspace_id, key, title,
    CASE WHEN link = 'occupation_choice' THEN 'esco' ELSE 'own_words' END,
    occupation_uri, link, label_matches,
    CASE
        WHEN titled IS NOT NULL OR cardinality(crosswalked) = 1 THEN 'pack_target'
        WHEN cardinality(crosswalked) > 1 THEN 'several_pack_targets'
        ELSE 'not_covered'
    END,
    CASE WHEN titled IS NOT NULL THEN titled
        WHEN cardinality(crosswalked) = 1 THEN crosswalked[1] END,
    CASE WHEN titled IS NOT NULL THEN 'title'
        WHEN cardinality(crosswalked) = 1 THEN 'esco_crosswalk' END,
    '{PACK_VERSION}',
    CASE WHEN link = 'occupation_choice' THEN source_ref_id END
FROM covered;
"""  # noqa: S608


def upgrade() -> None:
    run_script(CONCEPT_KEY + SCHEMA + BACKFILL)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
