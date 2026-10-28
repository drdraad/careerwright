"""The pinned ESCO taxonomy, its full-text index and provisional occupation concepts.

- ESCO is shared public reference data (spec section 19 keeps it apart from private data):
  its row-level policy makes every row readable, the API role may only read it, and only
  setup (the migration owner) writes it, when it imports the pinned release. One release is
  held at a time; its manifest row records dataset, version, URL, hash, licence and
  attribution, native code version and transformation version (TAX1-04).
- Occupations are identified by an internal concept ID (UUIDv5 of the ESCO URI) and keep
  their URI and ISCO-08 group; ISCO is the grouping pivot, never the identity (TAX1-01).
- `search_vector` is English full-text search over preferred labels (A), alternative labels
  (B), hidden labels and essential skills (C), and the description and ISCO group (D). Alias
  lookup is exact on normalised labels; a label several occupations share returns them all.
- A provisional concept is a title a user verified that ESCO does not hold: private to its
  workspace, citing the user's confirmation, and never an ESCO record (DIV1-03). A trigger
  refuses one whose title is an ESCO label.

Forward-only (see `docs/runbook.md`).

Revision ID: 0004
"""

from nessa.migrations.sql import run_script

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE nessa.taxonomy_releases (
    release_id uuid PRIMARY KEY,
    taxonomy text NOT NULL CHECK (taxonomy = 'esco'),
    dataset_id text NOT NULL UNIQUE,
    version text NOT NULL,
    language text NOT NULL,
    source_url text NOT NULL,
    sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    size_bytes bigint NOT NULL CHECK (size_bytes > 0),
    native_code_version text NOT NULL,
    transformation_version text NOT NULL,
    licence text NOT NULL,
    attribution text NOT NULL,
    sample boolean NOT NULL,
    isco_group_count integer NOT NULL CHECK (isco_group_count > 0),
    occupation_count integer NOT NULL CHECK (occupation_count > 0),
    skill_count integer NOT NULL CHECK (skill_count > 0),
    repeated_rows_collapsed integer NOT NULL CHECK (repeated_rows_collapsed >= 0),
    imported_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE UNIQUE INDEX taxonomy_releases_one_per_taxonomy ON nessa.taxonomy_releases (taxonomy);
COMMENT ON TABLE nessa.taxonomy_releases IS
    'The import manifest (TAX1-04). A sample release is a reduced copy for tests only.';

CREATE TABLE nessa.isco_groups (
    code text PRIMARY KEY CHECK (code ~ '^[0-9]{1,4}$'),
    release_id uuid NOT NULL REFERENCES nessa.taxonomy_releases,
    uri text NOT NULL UNIQUE,
    label text NOT NULL,
    broader_code text REFERENCES nessa.isco_groups (code),
    CONSTRAINT broader_is_the_code_prefix CHECK (
        (char_length(code) = 1) = (broader_code IS NULL)
        AND (broader_code IS NULL OR code LIKE broader_code || '_')
    )
);

CREATE TABLE nessa.occupation_concepts (
    concept_id uuid PRIMARY KEY,
    release_id uuid NOT NULL REFERENCES nessa.taxonomy_releases,
    esco_uri text NOT NULL UNIQUE,
    isco_code text NOT NULL REFERENCES nessa.isco_groups (code)
        CHECK (char_length(isco_code) = 4),
    esco_code text NOT NULL,
    preferred_label text NOT NULL,
    description text NOT NULL,
    regulated boolean,
    search_vector tsvector
);
CREATE INDEX occupation_concepts_search ON nessa.occupation_concepts USING gin (search_vector);
CREATE INDEX occupation_concepts_isco ON nessa.occupation_concepts (isco_code);

CREATE TABLE nessa.occupation_labels (
    concept_id uuid NOT NULL REFERENCES nessa.occupation_concepts,
    label text NOT NULL,
    kind text NOT NULL CHECK (kind IN ('preferred', 'alternative', 'hidden')),
    normalised text NOT NULL,
    PRIMARY KEY (concept_id, normalised)
);
CREATE INDEX occupation_labels_lookup ON nessa.occupation_labels (normalised);
CREATE UNIQUE INDEX occupation_labels_one_preferred
    ON nessa.occupation_labels (concept_id) WHERE kind = 'preferred';

CREATE TABLE nessa.occupation_broader (
    concept_id uuid PRIMARY KEY REFERENCES nessa.occupation_concepts,
    broader_concept_id uuid REFERENCES nessa.occupation_concepts,
    broader_isco_code text REFERENCES nessa.isco_groups (code),
    CONSTRAINT one_parent CHECK ((broader_concept_id IS NULL) <> (broader_isco_code IS NULL))
);

CREATE TABLE nessa.skills (
    skill_id uuid PRIMARY KEY,
    release_id uuid NOT NULL REFERENCES nessa.taxonomy_releases,
    esco_uri text NOT NULL UNIQUE,
    skill_type text CHECK (skill_type IN ('skill/competence', 'knowledge')),
    reuse_level text,
    preferred_label text NOT NULL,
    description text NOT NULL
);

CREATE TABLE nessa.skill_labels (
    skill_id uuid NOT NULL REFERENCES nessa.skills,
    label text NOT NULL,
    kind text NOT NULL CHECK (kind IN ('preferred', 'alternative', 'hidden')),
    normalised text NOT NULL,
    PRIMARY KEY (skill_id, normalised)
);
CREATE INDEX skill_labels_lookup ON nessa.skill_labels (normalised);

CREATE TABLE nessa.occupation_skills (
    concept_id uuid NOT NULL REFERENCES nessa.occupation_concepts,
    skill_id uuid NOT NULL REFERENCES nessa.skills,
    relation text NOT NULL CHECK (relation IN ('essential', 'optional')),
    PRIMARY KEY (concept_id, skill_id)
);
CREATE INDEX occupation_skills_skill ON nessa.occupation_skills (skill_id);

CREATE TABLE nessa.skill_relations (
    skill_id uuid NOT NULL REFERENCES nessa.skills,
    related_skill_id uuid NOT NULL REFERENCES nessa.skills,
    relation text NOT NULL CHECK (relation IN ('essential', 'optional')),
    PRIMARY KEY (skill_id, related_skill_id)
);

-- Every application table has row-level security; for public reference data the policy
-- states that every row is readable (and the grants keep it read-only).
DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['taxonomy_releases', 'isco_groups', 'occupation_concepts',
                             'occupation_labels', 'occupation_broader', 'skills',
                             'skill_labels', 'occupation_skills', 'skill_relations'] LOOP
        EXECUTE format('ALTER TABLE nessa.%I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('CREATE POLICY public_read ON nessa.%I FOR SELECT TO nessa_api '
                       'USING (true)', t);
        EXECUTE format('GRANT SELECT ON nessa.%I TO nessa_api', t);
    END LOOP;
END
$$;

CREATE TABLE nessa.provisional_concepts (
    concept_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES nessa.workspaces ON DELETE CASCADE,
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120),
    normalised_title text NOT NULL,
    source_ref_id uuid NOT NULL,
    created_by uuid NOT NULL REFERENCES nessa.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (workspace_id, normalised_title),
    FOREIGN KEY (workspace_id, source_ref_id)
        REFERENCES nessa.source_references (workspace_id, source_ref_id) ON DELETE CASCADE
);
COMMENT ON TABLE nessa.provisional_concepts IS
    'A user-verified title outside ESCO (DIV1-03): private to its workspace, never an ESCO '
    'record, citing the confirmation that established it.';

CREATE FUNCTION nessa.provisional_title_is_not_in_esco() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, pg_temp
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM nessa.occupation_labels l WHERE l.normalised = NEW.normalised_title)
    THEN
        RAISE EXCEPTION 'an ESCO occupation already has this title'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER provisional_title_is_not_in_esco BEFORE INSERT ON nessa.provisional_concepts
    FOR EACH ROW EXECUTE FUNCTION nessa.provisional_title_is_not_in_esco();

ALTER TABLE nessa.provisional_concepts ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON nessa.provisional_concepts TO nessa_api
    USING (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w));
GRANT SELECT, INSERT ON nessa.provisional_concepts TO nessa_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
