"""A title is recognised in the UK job-title index, and a qualifier naming another nursing field
never reaches the pack's adult nurse (Task 6d slice B; ADR 0015 decisions 1 to 3, ADR 0012
and ADR 0007 as amended on 2026-10-31).

- `resolve_target` now records a title that the pinned ONS SOC 2020 coding index lists
  (exactly, on the index's normalised title: case folded, spaces single) as an ONS title,
  with every SOC 2020 unit group and ISCO-08 group ONS codes it to, none picked. A stored
  record in the person's own words whose title the index lists is decided again so: it
  becomes an ONS title with its codes. What it names in ESCO and its coverage don't change.
  On a database that hasn't imported the index yet nothing is listed here, and nothing is
  stored before setup imports it (`resolve_target` refuses to decide without it).
- A qualifier in brackets that names another field of nursing ("(mental health)",
  "(children's)", "(learning disabilities)") is another registered role, so the bracket rule
  never takes it to the pack's "Registered nurse", whose evidence is adult nursing
  (`careerwright.profile.targets.OTHER_FIELDS`). A record 0035 or the code since gave that
  target by the bracket rule is decided again: it is no pack target's by its title, a
  crosswalk link it held by that title goes, and its coverage follows the occupation it still
  names (one pack target's crosswalk occupation, or not covered).
- The person's current or last role, named at the first question, is recorded in the same
  table by the same rules, one record per title as a concept: the closest occupation they
  chose, or "None of these is my job". The table's comment says so. Its CHECKs need no change:
  a choice still cites its source (the closest choice too), an ONS title's codes are in its
  row, and "None of these is my job" names no occupation and is the person's own decision,
  recorded with `recorded_by` and `recorded_at`.
- The type-ahead reads the index's titles word by word, so they get the same kind of word
  index ESCO's titles have (migration 0031).

The pinned option pack's targets and crosswalks (pack 0.1.0, capability reference 0.1.0), the
qualifier pattern and the other fields are this module's own copies; `test_targets.py` keeps
them equal to 0035's and to `resolve_target`'s.

Forward-only (see `docs/runbook.md`).

Revision ID: 0036
"""

from careerwright.migrations.sql import run_script

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None

QUALIFIER = r"\([^)]*\)|\[[^\]]*\]"
NURSE_TARGET = "registered-nurse-manchester"
NURSE_KEY = "registered nurse"
OTHER_FIELDS = ("mental health", "children s", "children", "learning disability")

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


def _values(rows: tuple[tuple[str, ...], ...]) -> str:
    return ", ".join("(" + ", ".join(f"'{cell}'" for cell in row) + ")" for row in rows)


def _quoted(texts: tuple[str, ...]) -> str:
    return ", ".join(f"'{text}'" for text in texts)


WORD_INDEX = """
CREATE INDEX soc2020_index_entries_words ON careerwright.soc2020_index_entries
    USING gin (to_tsvector('simple', title));
"""

# The index's normalised title is Python's `" ".join(title.casefold().split())`.
UK_TITLES = """
WITH listed AS (
    SELECT normalised,
        array_agg(DISTINCT soc_code ORDER BY soc_code) AS soc_codes,
        array_agg(DISTINCT isco_code ORDER BY isco_code) AS isco_codes
    FROM careerwright.soc2020_index_entries GROUP BY normalised
)
UPDATE careerwright.target_records r SET
    kind = 'ons', soc_codes = l.soc_codes, isco_codes = l.isco_codes
FROM listed l
WHERE r.kind = 'own_words'
    AND l.normalised = regexp_replace(btrim(lower(r.title)), '\\s+', ' ', 'g');
"""

# Built from this module's own constants only, never from input.
OTHER_FIELD = f"""
WITH pack (target_id, title, esco_uri) AS (VALUES {_values(PACK_TARGETS)}),
reached AS (
    SELECT r.workspace_id, r.title_key,
        CASE WHEN r.link = 'pack_crosswalk' THEN 'none' ELSE r.link END AS link,
        CASE WHEN r.link = 'pack_crosswalk' THEN NULL ELSE r.occupation_uri END AS occupation_uri
    FROM careerwright.target_records r
    WHERE r.pack_target_id = '{NURSE_TARGET}' AND r.pack_target_basis = 'title'
        AND careerwright.concept_key(r.title) <> '{NURSE_KEY}'
        AND EXISTS (
            SELECT 1 FROM regexp_matches(r.title, '{QUALIFIER}', 'g') AS m(found)
            WHERE careerwright.concept_key(substr(m.found[1], 2, char_length(m.found[1]) - 2))
                IN ({_quoted(OTHER_FIELDS)})
        )
),
decided AS (
    SELECT d.*,
        (SELECT array_agg(p.target_id ORDER BY p.target_id) FROM pack p
            WHERE p.esco_uri = d.occupation_uri) AS crosswalked
    FROM reached d
)
UPDATE careerwright.target_records r SET
    link = d.link,
    occupation_uri = d.occupation_uri,
    coverage = CASE
        WHEN cardinality(d.crosswalked) = 1 THEN 'pack_target'
        WHEN cardinality(d.crosswalked) > 1 THEN 'several_pack_targets'
        ELSE 'not_covered'
    END,
    pack_target_id = CASE WHEN cardinality(d.crosswalked) = 1 THEN d.crosswalked[1] END,
    pack_target_basis = CASE WHEN cardinality(d.crosswalked) = 1 THEN 'esco_crosswalk' END
FROM decided d
WHERE r.workspace_id = d.workspace_id AND r.title_key = d.title_key;
"""  # noqa: S608

COMMENT = """
COMMENT ON TABLE careerwright.target_records IS
    'Each title once, by its concept key: a target''s, or the current or last role''s named at '
    'the first question. Its words (an ESCO title, a title the UK job-title index lists, with '
    'every group ONS codes it to, or the person''s own), the ESCO occupation it names (or none, '
    'or none of the closest, as the person said), the source of that link, every occupation '
    'holding the title as a label, and whether it is one of the option pack''s targets. Written '
    'when a title is chosen or saved; every module reads it instead of resolving the title '
    'again.';
"""


def upgrade() -> None:
    run_script(WORD_INDEX + UK_TITLES + OTHER_FIELD + COMMENT)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
