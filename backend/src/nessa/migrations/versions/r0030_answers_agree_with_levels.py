"""An answer agrees with the level given with it (Task 9 fix round 1, review I2; ADR 0012
decision 5).

`skill_evidence` refuses what the domain refuses: "I have not learned this" and "I understand
it but have not tried" are no performance yet, so their level is 0 or none; "I did it with
help" is at most level 1, since levels 2 to 4 are defined by independence (spec section 8's
anchors).

The constraints are `NOT VALID`: before this rule the API accepted such answers, and a
database that ran 0029 may hold one. It is kept as written, never rewritten or dropped;
every new row is checked. (0029 has only ever run on this branch's test databases.)

Forward-only (see `docs/runbook.md`).

Revision ID: 0030
"""

from nessa.migrations.sql import run_script

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.skill_evidence ADD CONSTRAINT not_yet_done_is_level_zero CHECK (
    answer NOT IN ('not_learned', 'understand_not_tried') OR coalesce(self_assessed_level, 0) = 0
) NOT VALID;
ALTER TABLE nessa.skill_evidence ADD CONSTRAINT with_help_is_at_most_level_one CHECK (
    answer <> 'done_with_help' OR coalesce(self_assessed_level, 0) <= 1
) NOT VALID;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
