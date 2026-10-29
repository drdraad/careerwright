"""A body whose visible text still shows a third party's detail is not kept (Task 7A fix
round 3, review C I1 with re-review 3 A R3-2; ADR 0009 decision 4).

- `source_attempts.body_not_kept` gains `visible_text_detail`: after a body is redacted, its
  visible text is normalised (entities decoded, whitespace collapsed, characters that do not
  print dropped) and looked at again; a detail found there means only the hash and excerpts
  are kept.
- Correction to migration 0020's description (re-review 3 A R3-1; 0020 is not edited):
  `contact_unlocated` and `block_unredactable` apply to any script, not only a JSON-LD
  block. `contact_unlocated` is a script holding a detail that could not be found in the
  page's text to be written again; `block_unredactable` is a script that is not JSON and
  holds a detail once its JSON or JavaScript escapes are decoded.

Forward-only (see `docs/runbook.md`).

Revision ID: 0022
"""

from nessa.migrations.sql import run_script

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.source_attempts DROP CONSTRAINT source_attempts_body_not_kept_check;
ALTER TABLE nessa.source_attempts ADD CONSTRAINT source_attempts_body_not_kept_check
    CHECK (body_not_kept IN ('contact_unlocated', 'block_unredactable', 'visible_text_detail'));
COMMENT ON COLUMN nessa.source_attempts.body_not_kept IS
    'Why a body its class may keep was not kept: a script holding a detail was not found '
    '(contact_unlocated), a script that is not JSON held one (block_unredactable), or the '
    'normalised visible text still showed one (visible_text_detail). Any script, not only '
    'JSON-LD.';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
