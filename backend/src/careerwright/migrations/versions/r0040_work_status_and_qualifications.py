"""The saved answers' schema version 4 (Task 6f; ADR 0006, amendment line of 2026-11-01): two
optional answers, what the person is doing now (`work_status`) and their qualifications
(`qualifications`, each achieved or expected), and the current role's answer "I haven't had a
job yet" (`no_job_yet`, a field state that needs no column).

Every stored profile version is rewritten as version 4 with both new answers not yet asked
(and any older version's later answers too: versions 1 and 2 had no interest, capability or
work-style answers). Nothing else in a document changes: every answer keeps its state, value
and source, so a version still reads exactly as it did. `ProfileDocument` also reads an older
document this way (an export made before this migration, for example).

Forward-only (see `docs/runbook.md`).

Revision ID: 0040
"""

from careerwright.migrations.sql import run_script

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None

# This module's own copy of the fields added after version 1 (`document._ADDED_AFTER`).
ADDED_AFTER_VERSION_1 = (
    "enjoyed_tasks",
    "confident_tasks",
    "evidenced_tasks",
    "work_style",
    "minimum_salary",
    "work_status",
    "qualifications",
)

SCHEMA = """
UPDATE careerwright.profile_versions
SET document = jsonb_build_object(
        'enjoyed_tasks', '{"state": "unasked"}'::jsonb,
        'confident_tasks', '{"state": "unasked"}'::jsonb,
        'evidenced_tasks', '{"state": "unasked"}'::jsonb,
        'work_style', '{"state": "unasked"}'::jsonb,
        'minimum_salary', '{"state": "unasked"}'::jsonb,
        'work_status', '{"state": "unasked"}'::jsonb,
        'qualifications', '{"state": "unasked"}'::jsonb
    ) || document || jsonb_build_object('schema_version', '4'),
    schema_version = '4'
WHERE schema_version <> '4' OR document->>'schema_version' <> '4';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
