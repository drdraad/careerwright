"""Progress corrections retain older activity records and require an exact step."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from careerwright.planning.plan_records import PlanActivity, ProgressUpdate


def test_older_activity_without_a_saved_step_title_remains_readable() -> None:
    old = PlanActivity.model_validate(
        {
            "kind": "step_completed",
            "variant_id": "course:old",
            "until": None,
            "recorded_at": datetime(2027, 1, 1, tzinfo=UTC).isoformat(),
        }
    )
    assert old.step_title is None


def test_retraction_names_a_step_and_cannot_carry_a_review_date() -> None:
    valid = ProgressUpdate(expected_version=2, kind="step_retracted", variant_id="course:old")
    assert valid.variant_id == "course:old"
    with pytest.raises(ValidationError):
        ProgressUpdate.model_validate({"expected_version": 2, "kind": "step_retracted"})
    with pytest.raises(ValidationError):
        ProgressUpdate.model_validate(
            {
                "expected_version": 2,
                "kind": "step_retracted",
                "variant_id": "course:old",
                "until": "2027-02-01",
            }
        )


def test_commitment_retraction_names_a_step_and_cannot_carry_a_review_date() -> None:
    valid = ProgressUpdate(expected_version=2, kind="commitment_retracted", variant_id="course:old")
    assert valid.variant_id == "course:old"
    with pytest.raises(ValidationError):
        ProgressUpdate.model_validate({"expected_version": 2, "kind": "commitment_retracted"})
    with pytest.raises(ValidationError):
        ProgressUpdate.model_validate(
            {
                "expected_version": 2,
                "kind": "commitment_retracted",
                "variant_id": "course:old",
                "until": "2027-02-01",
            }
        )
