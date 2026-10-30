"""A body whose attribute values hide a third party's detail is not kept (Task 7A fix round
4, item 1; ADR 0009 decision 4).

- `source_attempts.body_not_kept` gains `attribute_detail`: after a body is redacted, each
  attribute's value is decoded (its entities) and normalised, and looked at again; a detail
  found there (an obfuscated `mailto:` link with no visible address) means only the hash and
  excerpts are kept.
- `visible_text_detail` now also covers an email that inline markup split (`jane<span>@</span>
  recruit.example`, re-review 4 A R4-1); its value is unchanged.

Forward-only (see `docs/runbook.md`).

Revision ID: 0025
"""

from careerwright.migrations.sql import run_script

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.source_attempts DROP CONSTRAINT source_attempts_body_not_kept_check;
ALTER TABLE careerwright.source_attempts ADD CONSTRAINT source_attempts_body_not_kept_check
    CHECK (body_not_kept IN ('contact_unlocated', 'block_unredactable', 'visible_text_detail',
                             'attribute_detail'));
COMMENT ON COLUMN careerwright.source_attempts.body_not_kept IS
    'Why a body its class may keep was not kept: a script holding a detail was not found '
    '(contact_unlocated), a script that is not JSON held one (block_unredactable), the '
    'normalised visible text still showed one (visible_text_detail), or an attribute''s '
    'decoded value held one (attribute_detail). Any script, not only JSON-LD.';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
