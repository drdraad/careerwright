"""An Advanced Learner Loan paid straight to the provider, beside the tuition fee loan (Task
12c's follow-up; the product owner's provisional yes of 2026-11-01; ADR 0013, Task 12c's
amendment).

- `planning_input_versions.document`: an option's `tuition_fee_loan` may now say which loan it
  is (`kind`): a tuition fee loan or an Advanced Learner Loan. Left out, it is a tuition fee
  loan, so every stored document keeps its meaning.

The CHECK repeats the domain rule (`careerwright.planning.catalogue.FeeLoanKind`): a fee loan
is one of the two kinds. Every other loan, a maintenance loan included, is still refused as a
support by migration 0033's CHECK.

Forward-only (see `docs/runbook.md`).

Revision ID: 0044
"""

from careerwright.migrations.sql import run_script

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.planning_input_versions
    ADD CONSTRAINT a_fee_loan_is_one_of_the_two_kinds CHECK (
        NOT jsonb_path_exists(
            document,
            'lax $.variants[*].tuition_fee_loan'
            ' ? (@.kind != "tuition_fee_loan" && @.kind != "advanced_learner_loan")'
        )
    );
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
