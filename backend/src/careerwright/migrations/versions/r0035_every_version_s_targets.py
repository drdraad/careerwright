"""Every target title of every profile version gets its record, and a qualifier in brackets
reaches a pack target by its title again (Task 6d slice A, fix round 1; ADR 0015 and ADR 0012,
amendment lines of 2026-10-31).

- 0034 gave a record only to the targets of each workspace's newest profile version. A
  discovery is read from the version it pinned, so one made from an older version could not
  open when a target it held had been removed or replaced since. This fills in a record for
  every target title of every version that has none: one per workspace and title as a
  concept, spelled as the latest version holding it spells it, by the same rules as
  `careerwright.profile.targets.resolve_target`. A record already stored is kept, except as
  the next point says.
- `resolve_target` again leaves out a qualifier in brackets to reach an option pack target by
  its title ("Registered nurse (adult)" is the pack's "Registered nurse"), as Skills did before
  0034. A record decided without that rule, by 0034 or since, is decided again where the rule
  now reaches a pack target by title: it becomes that target's, and a record that named no
  occupation now names the one its crosswalk names. A choice or a label match it holds stays.

The pinned option pack's targets and crosswalks (pack 0.1.0, capability reference 0.1.0) and
the qualifier pattern are this module's own copies; `test_targets.py` keeps them equal to
0034's and to `resolve_target`'s.

Forward-only (see `docs/runbook.md`).

Revision ID: 0035
"""

from careerwright.migrations.sql import run_script

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None

QUALIFIER = r"\([^)]*\)|\[[^\]]*\]"

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


def _pack_keys() -> str:
    values = ", ".join(f"('{target}', '{title}', '{uri}')" for target, title, uri in PACK_TARGETS)
    return f"""pack (target_id, title, esco_uri) AS (VALUES {values}),
pack_keys AS (
    SELECT target_id, careerwright.concept_key(title) AS key, esco_uri FROM pack
)"""  # noqa: S608


def _unqualified(column: str) -> str:
    return f"careerwright.concept_key(regexp_replace({column}, '{QUALIFIER}', ' ', 'g'))"


# Built from this module's own constants only, never from input.
FILL_IN = f"""
WITH {_pack_keys()},
lists AS MATERIALIZED (
    SELECT workspace_id, version, document -> 'target_titles' -> 'value' AS titles
    FROM careerwright.profile_versions
    WHERE document -> 'target_titles' ->> 'state' = 'provided'
        AND jsonb_typeof(document -> 'target_titles' -> 'value') = 'array'
),
spelled AS (
    SELECT DISTINCT ON (l.workspace_id, careerwright.concept_key(t.title))
        l.workspace_id, t.title, careerwright.concept_key(t.title) AS key,
        {_unqualified("t.title")} AS unqualified
    FROM lists l, jsonb_array_elements_text(l.titles) WITH ORDINALITY AS t(title, n)
    ORDER BY l.workspace_id, careerwright.concept_key(t.title), l.version DESC, t.n
),
titled AS (
    SELECT s.*, coalesce(w.target_id, u.target_id) AS titled,
        CASE WHEN w.target_id IS NOT NULL THEN w.esco_uri ELSE u.esco_uri END AS crosswalk
    FROM spelled s
    LEFT JOIN pack_keys w ON w.key = s.key
    LEFT JOIN pack_keys u ON u.key = s.unqualified
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
    SELECT s.workspace_id, s.key,
        array_agg(DISTINCT o.esco_uri ORDER BY o.esco_uri) AS uris
    FROM spelled s
    JOIN careerwright.occupation_labels l ON careerwright.concept_key(l.label) = s.key
    JOIN careerwright.occupation_concepts o ON o.concept_id = l.concept_id
    GROUP BY s.workspace_id, s.key
),
linked AS (
    SELECT t.workspace_id, t.title, t.key, t.titled, c.source_ref_id,
        coalesce(b.uris, '{{}}') AS label_matches,
        CASE
            WHEN c.esco_uri IS NOT NULL THEN 'occupation_choice'
            WHEN cardinality(b.uris) = 1 THEN 'exact_label'
            WHEN t.crosswalk IS NOT NULL THEN 'pack_crosswalk'
            ELSE 'none'
        END AS link,
        CASE
            WHEN c.esco_uri IS NOT NULL THEN c.esco_uri
            WHEN cardinality(b.uris) = 1 THEN b.uris[1]
            ELSE t.crosswalk
        END AS occupation_uri
    FROM titled t
    LEFT JOIN chosen c ON c.workspace_id = t.workspace_id AND c.key = t.key
    LEFT JOIN labelled b ON b.workspace_id = t.workspace_id AND b.key = t.key
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
FROM covered
ON CONFLICT (workspace_id, title_key) DO NOTHING;
"""  # noqa: S608

# Built from this module's own constants only, never from input.
QUALIFIED = f"""
WITH {_pack_keys()}
UPDATE careerwright.target_records r SET
    coverage = 'pack_target',
    pack_target_id = p.target_id,
    pack_target_basis = 'title',
    link = CASE WHEN r.link = 'none' AND p.esco_uri IS NOT NULL THEN 'pack_crosswalk'
        ELSE r.link END,
    occupation_uri = CASE WHEN r.link = 'none' THEN p.esco_uri ELSE r.occupation_uri END
FROM pack_keys p
WHERE p.key = {_unqualified("r.title")}
    AND r.pack_target_basis IS DISTINCT FROM 'title';
"""  # noqa: S608


def upgrade() -> None:
    run_script(FILL_IN + QUALIFIED)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
