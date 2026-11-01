"""A body whose JSON links hide a third party's detail is not kept (Task 7A fix round 5,
re-review 5 A R5-2; ADR 0009 decision 4).

- `source_attempts.body_not_kept` gains `link_detail`: a link in the page's JSON (`url`,
  `sameAs`, `image` and the like) is kept as written, so it is looked at with its HTML
  entities and percent-encoding decoded; a detail found there (a JSON-LD
  `"url": "mailto:..."`) means only the hash and excerpts are kept.
- `attribute_detail` now also covers an attribute whose percent-encoding hides a detail
  (`mailto:jane%40recruit.example`); its value is unchanged.

Forward-only (see `docs/runbook.md`).

Revision ID: 0026
"""

from careerwright.migrations.sql import run_script

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.source_attempts DROP CONSTRAINT source_attempts_body_not_kept_check;
ALTER TABLE careerwright.source_attempts ADD CONSTRAINT source_attempts_body_not_kept_check
    CHECK (body_not_kept IN ('contact_unlocated', 'block_unredactable', 'visible_text_detail',
                             'attribute_detail', 'link_detail'));
COMMENT ON COLUMN careerwright.source_attempts.body_not_kept IS
    'Why a body its class may keep was not kept: a script holding a detail was not found '
    '(contact_unlocated), a script that is not JSON held one (block_unredactable), the '
    'normalised visible text still showed one (visible_text_detail), an attribute''s '
    'decoded value held one (attribute_detail), or a link in the page''s JSON, decoded, '
    'held one (link_detail). Any script, not only JSON-LD.';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
