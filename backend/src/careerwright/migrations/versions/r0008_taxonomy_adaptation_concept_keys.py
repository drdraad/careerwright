"""The import manifest marks the catalogue as adapted, and the "not in ESCO" guard folds
near-duplicates.

- `taxonomy_releases.adaptation`: ESCO's second reuse condition (mark an adapted version as
  such). The product import is itself reduced and transformed, so its manifest says how;
  existing rows (transformation `careerwright-esco-import-1`) get that statement.
- `careerwright.concept_key(text)`: a title compared as a concept: lower case, every run of
  characters other than letters and digits (hyphens, punctuation) a single space, and a
  simple English plural folded per word ("analysts" -> "analyst", "duties" -> "duty"; words
  ending -ss, -us or -is, and words of three letters or fewer, are kept). It is a
  deliberately small heuristic, indexed over every occupation label.
- The trigger on `provisional_concepts` derives the key from `NEW.title` itself, so the
  database guard no longer trusts the caller's normalised form, and refuses a title whose
  key equals any ESCO label's key ("ICT help-desk agent", "Data analyst.", "data analysts").

Forward-only (see `docs/runbook.md`).

Revision ID: 0008
"""

from careerwright.migrations.sql import run_script

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.taxonomy_releases ADD COLUMN adaptation text;
UPDATE careerwright.taxonomy_releases SET adaptation =
    'Adapted from ESCO: Careerwright imports occupations, skills, their relations and ISCO-08 '
    'groups only (not skill groups, the skill hierarchy, collections, the dictionary or '
    'green-share data), with labels trimmed and de-duplicated and repeated rows merged '
    '(transformation careerwright-esco-import-1). It is not the official ESCO release.'
    WHERE transformation_version = 'careerwright-esco-import-1';
ALTER TABLE careerwright.taxonomy_releases ALTER COLUMN adaptation SET NOT NULL;

CREATE FUNCTION careerwright.concept_key(title text) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    RETURN (
        SELECT coalesce(string_agg(
            CASE
                WHEN w ~ '[^aeiou]ies$' AND length(w) > 4 THEN left(w, -3) || 'y'
                WHEN length(w) <= 3 OR w ~ '(ss|us|is)$' THEN w
                WHEN w ~ 's$' THEN left(w, -1)
                ELSE w
            END, ' ' ORDER BY n), '')
        FROM regexp_split_to_table(lower(title), '[^[:alnum:]]+') WITH ORDINALITY AS t(w, n)
        WHERE w <> ''
    );
COMMENT ON FUNCTION careerwright.concept_key(text) IS
    'A title compared as a concept: case, punctuation, hyphens and simple plurals folded.';
CREATE INDEX occupation_labels_concept_key ON careerwright.occupation_labels
    (careerwright.concept_key(label));

CREATE OR REPLACE FUNCTION careerwright.provisional_title_is_not_in_esco() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, pg_temp
    AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM careerwright.occupation_labels l
        WHERE careerwright.concept_key(l.label) = careerwright.concept_key(NEW.title)
    )
    THEN
        RAISE EXCEPTION 'an ESCO occupation already has this title'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END
$$;
GRANT EXECUTE ON FUNCTION careerwright.concept_key(text) TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
