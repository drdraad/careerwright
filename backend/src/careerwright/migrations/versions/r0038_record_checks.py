"""The title records' CHECKs repeat the role space's rules (Task 6d slice B fix round 1; the app
review's M-4; ADR 0015 decision 3).

- `an_ons_title_has_its_codes`: a title the UK job-title index lists (`kind = 'ons'`) is stored
  with at least one SOC 2020 unit group and one ISCO-08 group, as the index codes it. Without
  them it would silently never ask "Which of these is closest?". 0034's
  `only_an_ons_title_has_ons_codes` holds the other direction.
- `none_of_these_is_the_person_s_own`: "None of these is my job" is the person's own decision,
  so it is stored only with who recorded it (`recorded_by`), and only on a title in their words:
  an ONS title (the closest question) or their own words (the type-ahead's partial list, ESCO's
  closest titles), never on an ESCO title chosen as such.

Every record stored before meets both: `resolve_target` and migration 0036 store an ONS title
with the index's codes, and "None of these is my job" was recorded only by the person's own
command. Forward-only (see `docs/runbook.md`).

Revision ID: 0038
"""

from careerwright.migrations.sql import run_script

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.target_records ADD CONSTRAINT an_ons_title_has_its_codes CHECK (
    kind <> 'ons' OR (cardinality(soc_codes) > 0 AND cardinality(isco_codes) > 0)
);
ALTER TABLE careerwright.target_records ADD CONSTRAINT none_of_these_is_the_person_s_own CHECK (
    link <> 'none_of_these' OR (kind IN ('ons', 'own_words') AND recorded_by IS NOT NULL)
);
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
