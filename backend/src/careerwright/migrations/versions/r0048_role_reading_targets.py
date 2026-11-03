"""A role research reading tries up to 40 pages and reads at most 20 (Task W2F slice D, round 2;
the product owner's live try of 3 November 2026: Muse passed on two of the search's pages and
both had expired, so the research read nothing).

- `acquisition_targets.position` holds 0 to 39 (was 0 to 19): a reading's targets are Muse's
  picks and then every other page the search returned (`search.ROLE_CANDIDATES`).
- `acquisition_targets.status` gains `not_needed`: a role target the reading never fetched,
  because it had read its 20 pages (`acquisition.MAX_ROLE_PAGES`) before reaching it. It is no
  page of the reading: never read, never unread.

Every existing row already holds; nothing is rewritten.

Forward-only (see `docs/runbook.md`).

Revision ID: 0048
"""

from careerwright.migrations.sql import run_script

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.acquisition_targets
    DROP CONSTRAINT acquisition_targets_position_check,
    ADD CONSTRAINT acquisition_targets_position_check CHECK (position BETWEEN 0 AND 39),
    DROP CONSTRAINT acquisition_targets_status_check,
    ADD CONSTRAINT acquisition_targets_status_check
        CHECK (status IN ('queued', 'succeeded', 'blocked', 'failed', 'cancelled', 'not_needed')),
    ADD CONSTRAINT only_a_role_target_is_not_needed
        CHECK (status <> 'not_needed' OR role_title IS NOT NULL);
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
