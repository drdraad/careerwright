"""The saved answers' schema version 5 (Task W2F; ADR 0006, amendment line of 2026-11-02): one
optional answer, the tasks the person doesn't enjoy (`disliked_tasks`, spec section 4's
"disliked tasks"). It informs the conversation and is never a search, a filter or a ranking
input.

Every stored profile version is rewritten as version 5 with it not yet asked (and any older
version's later answers too: versions 1 to 3 lacked some of them). Nothing else in a document
changes: every answer keeps its state, value and source, so a version still reads exactly as
it did. A schema migration may add not-yet-asked answers in place, and nothing else (ADR 0006,
amendment of 2026-11-01). `ProfileDocument` also reads an older document this way.

Forward-only (see `docs/runbook.md`).

Revision ID: 0046
"""

from careerwright.migrations.sql import run_script

revision = "0046"
down_revision = "0045"
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
    "disliked_tasks",
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
        'qualifications', '{"state": "unasked"}'::jsonb,
        'disliked_tasks', '{"state": "unasked"}'::jsonb
    ) || document || jsonb_build_object('schema_version', '5'),
    schema_version = '5'
WHERE schema_version <> '5' OR document->>'schema_version' <> '5';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
