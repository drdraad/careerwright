"""Role research's copies of one advert, by every passage around the title (Task 6e fix round
1; ADR 0015, Task 6e fix round line; ADR 0009 decision 6).

- `role_page_checks.passages`: the fingerprints of the passages around each of the title's
  places on the page (at most 16 places, two passages each:
  `careerwright.evidence.corroboration.passages`), in place of `passage_sha256`, which held the
  title's first place only. A page's `<title>`, navigation or footer name the title first, so
  two copies of one advert differed there and counted as two sources.

The CHECKs repeat the rule: a verified title keeps its span, its excerpt and at least one
passage, and an unverified one none; each passage is a SHA-256 in hex. A check recorded
before this keeps its one passage.

Forward-only (see `docs/runbook.md`).

Revision ID: 0043
"""

from careerwright.migrations.sql import run_script

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.role_page_checks
    ADD COLUMN passages text[] NOT NULL DEFAULT '{}';
UPDATE careerwright.role_page_checks SET passages = ARRAY[passage_sha256]
    WHERE passage_sha256 IS NOT NULL;
ALTER TABLE careerwright.role_page_checks
    DROP CONSTRAINT a_verified_title_has_its_span_excerpt_and_passage,
    DROP COLUMN passage_sha256,
    ADD CONSTRAINT a_verified_title_has_its_span_excerpt_and_passages CHECK (
        (span_start IS NULL) = (span_end IS NULL)
        AND (span_start IS NULL) = (excerpt IS NULL)
        AND (span_start IS NULL) = (cardinality(passages) = 0)
    ),
    ADD CONSTRAINT passages_are_bounded_fingerprints CHECK (
        cardinality(passages) <= 32
        AND array_ndims(passages) IS NOT DISTINCT FROM CASE
            WHEN cardinality(passages) = 0 THEN NULL ELSE 1 END
        AND (cardinality(passages) = 0
             OR array_to_string(passages, ',', '?') ~ '^[0-9a-f]{64}(,[0-9a-f]{64})*$')
    );
COMMENT ON COLUMN careerwright.role_page_checks.passages IS
    'Fingerprints of the passages around each of the title''s places on the page (the title '
    'with the words after it, and the words before it with the title), so copies of one '
    'advert fold whatever the page puts around them. Never the words themselves.';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
