"""Pinned reference data: ASHE pay, the UK SOC 2020 coding index and the AI evidence (Task 7
slice B; ADR 0010; TAX1-02..07, AIR1-11).

- `reference_releases` is the import manifest of every pinned dataset other than ESCO: one
  release of each dataset at a time, with its URL, hash, size, licence, attribution, native
  code version, transformation version, import time and counts (TAX1-04). A sample is a
  labelled synthetic or reduced copy for tests only.
- Each dataset keeps its own native codes in its own table, never joined into one score
  (AIR1-03, AIR1-11): ASHE estimates by UK SOC 2020 unit group and ONS work region (never a
  city; TAX1-06); the coding index's title-level SOC 2020 and ISCO-08 links, every one kept
  (TAX1-02); ILO exposure by ISCO-08 unit group; O*NET tasks and their observed share of
  Claude conversations; the ESCO to O*NET crosswalk with its match types (TAX1-07).
- A withheld ASHE value is null with ONS's marker beside it, never zero.
- Public reference data, like ESCO (0004): every row readable by the API role, written only
  by setup.

Forward-only (see `docs/runbook.md`).

Revision ID: 0027
"""

from nessa.migrations.sql import run_script

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE nessa.reference_releases (
    dataset text PRIMARY KEY CHECK (dataset IN ('ashe', 'soc_index', 'ilo_exposure',
                                                'onet_tasks', 'task_usage', 'crosswalk')),
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
    record_count integer NOT NULL CHECK (record_count > 0),
    counts jsonb NOT NULL DEFAULT '{}',
    imported_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
COMMENT ON TABLE nessa.reference_releases IS
    'The import manifest of the pinned reference datasets other than ESCO (TAX1-04).';

CREATE TABLE nessa.ashe_estimates (
    soc_code text NOT NULL CHECK (soc_code ~ '^[0-9]{4}$'),
    region_code text NOT NULL CHECK (region_code ~ '^[EWS][0-9]{8}$'),
    period text NOT NULL CHECK (period IN ('year', 'week', 'hour')),
    population text NOT NULL CHECK (population = 'full_time'),
    soc_title text NOT NULL,
    region_name text NOT NULL,
    jobs_thousands numeric CHECK (jobs_thousands >= 0),
    figures jsonb NOT NULL,
    markers jsonb NOT NULL,
    median_cv numeric CHECK (median_cv >= 0),
    PRIMARY KEY (soc_code, region_code, period, population)
);
COMMENT ON TABLE nessa.ashe_estimates IS
    'ONS ASHE estimates (pence) by UK SOC 2020 unit group and work region: a region, never '
    'a city. A withheld statistic is null in figures, with ONS''s marker in markers.';

CREATE TABLE nessa.soc2020_unit_groups (
    code text PRIMARY KEY CHECK (code ~ '^[0-9]{4}$'),
    title text NOT NULL
);

CREATE TABLE nessa.soc2020_index_entries (
    entry_id integer PRIMARY KEY,
    soc_code text NOT NULL REFERENCES nessa.soc2020_unit_groups (code),
    isco_code text NOT NULL CHECK (isco_code ~ '^[0-9]{4}$'),
    title text NOT NULL,
    normalised text NOT NULL
);
CREATE INDEX soc2020_index_entries_isco ON nessa.soc2020_index_entries (isco_code);
CREATE INDEX soc2020_index_entries_title ON nessa.soc2020_index_entries (normalised);

CREATE TABLE nessa.ilo_genai_exposure (
    isco_code text PRIMARY KEY CHECK (isco_code ~ '^[0-9]{4}$'),
    title text NOT NULL,
    tasks integer NOT NULL CHECK (tasks > 0),
    mean_score numeric NOT NULL CHECK (mean_score BETWEEN 0 AND 1),
    sd_score numeric NOT NULL CHECK (sd_score BETWEEN 0 AND 1),
    gradient text NOT NULL CHECK (gradient IN ('Exposed: Gradient 4', 'Exposed: Gradient 3',
                                              'Exposed: Gradient 2', 'Exposed: Gradient 1',
                                              'Minimal Exposure', 'Not Exposed'))
);

CREATE TABLE nessa.onet_tasks (
    onet_code text NOT NULL CHECK (onet_code ~ '^[0-9]{2}-[0-9]{4}\\.[0-9]{2}$'),
    task_id integer NOT NULL,
    occupation_title text NOT NULL,
    task text NOT NULL,
    task_type text,
    normalised_task text NOT NULL,
    PRIMARY KEY (onet_code, task_id)
);
CREATE INDEX onet_tasks_task ON nessa.onet_tasks (normalised_task);

CREATE TABLE nessa.observed_task_use (
    task_name text PRIMARY KEY,
    share_pct numeric NOT NULL CHECK (share_pct BETWEEN 0 AND 100)
);
COMMENT ON TABLE nessa.observed_task_use IS
    'Each O*NET task''s share (percent) of the Claude conversations the Anthropic Economic '
    'Index mapped to tasks: observed use, never replacement. A task absent here was not '
    'observed in the release: never zero use, never protection.';

CREATE TABLE nessa.esco_onet_crosswalk (
    onet_code text NOT NULL CHECK (onet_code ~ '^[0-9]{2}-[0-9]{4}\\.[0-9]{2}$'),
    onet_title text NOT NULL,
    esco_uri text,
    isco_code text CHECK (isco_code ~ '^[0-9]{1,4}$'),
    target_title text NOT NULL,
    match_type text NOT NULL CHECK (match_type IN ('exactMatch', 'closeMatch', 'broadMatch',
                                                  'narrowMatch', 'exactISCO')),
    CONSTRAINT one_target CHECK ((esco_uri IS NULL) <> (isco_code IS NULL)),
    CONSTRAINT isco_rows_are_exact_isco CHECK ((isco_code IS NULL) = (match_type <> 'exactISCO'))
);
CREATE UNIQUE INDEX esco_onet_crosswalk_pair
    ON nessa.esco_onet_crosswalk (onet_code, coalesce(esco_uri, isco_code));
CREATE INDEX esco_onet_crosswalk_esco ON nessa.esco_onet_crosswalk (esco_uri);

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['reference_releases', 'ashe_estimates', 'soc2020_unit_groups',
                             'soc2020_index_entries', 'ilo_genai_exposure', 'onet_tasks',
                             'observed_task_use', 'esco_onet_crosswalk'] LOOP
        EXECUTE format('ALTER TABLE nessa.%I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('CREATE POLICY public_read ON nessa.%I FOR SELECT TO nessa_api '
                       'USING (true)', t);
        EXECUTE format('GRANT SELECT ON nessa.%I TO nessa_api', t);
    END LOOP;
END
$$;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
