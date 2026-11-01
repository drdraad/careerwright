"""A tuition fee loan paid straight to the provider, in the person's planning inputs (Task
12c; spec section 22, the product owner's decision of 2026-11-01; ADR 0013, Task 12c's
amendment).

- `planning_input_versions.document`: each option's answers may now hold
  `tuition_fee_loan`, its amount (null: not known, never £0) and its funding statuses. The
  document's existing CHECKs already keep its money in GBP and never negative, and still refuse
  a loan, a maintenance loan included, stated as a support.

The CHECKs repeat the domain rules (`careerwright.planning.inputs.TuitionFeeLoanInput`): a
tuition fee loan takes one of the four eligibility statuses and one of the four application
states, and an approved one needs confirmed eligibility. Existing documents hold no loan, so
every one passes.

Forward-only (see `docs/runbook.md`).

Revision ID: 0041
"""

from careerwright.migrations.sql import run_script

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.planning_input_versions
    ADD CONSTRAINT a_tuition_fee_loan_states_its_statuses CHECK (
        NOT jsonb_path_exists(
            document,
            'lax $.variants[*].tuition_fee_loan ? ('
            '(@.eligibility != "confirmed" && @.eligibility != "potentially_eligible"'
            ' && @.eligibility != "ineligible" && @.eligibility != "insufficient_information")'
            ' || (@.application != "not_applied" && @.application != "applied"'
            ' && @.application != "approved" && @.application != "refused"))'
        )
    ),
    ADD CONSTRAINT a_tuition_fee_loan_is_approved_only_if_eligible CHECK (
        NOT jsonb_path_exists(
            document,
            'lax $.variants[*].tuition_fee_loan'
            ' ? (@.application == "approved" && @.eligibility != "confirmed")'
        )
    );
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
