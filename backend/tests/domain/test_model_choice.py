"""Which model a run may use (ADR 0003; MODEL-02; the Contributor ruling carried into Task 3)."""

import uuid
from datetime import UTC, datetime

import pytest

from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.identity.activity import model_refusal
from careerwright.identity.failures import FailureClass
from careerwright.identity.model_choice import (
    ModelChoice,
    ModelConfigurationError,
    assert_model_permitted,
)
from careerwright.identity.model_registry import ModelMode, model_entry
from careerwright.identity.records import Run, RunKind
from careerwright.vocabulary import DataMode, WorkState

CONTRIBUTOR = "muse-spark-1.3-contributor"
STANDARD = "muse-spark-1.3"


def choice(test: str = CONTRIBUTOR, production: str = STANDARD, role: str = "test") -> ModelChoice:
    return ModelChoice.configure(test, production, role)  # type: ignore[arg-type]


@pytest.mark.req("MODEL-02")
def test_a_contributor_production_model_is_refused_at_startup() -> None:
    with pytest.raises(ModelConfigurationError, match="Standard"):
        choice(production=CONTRIBUTOR)


def test_an_unpriced_model_is_refused_because_its_spend_cannot_be_reserved() -> None:
    with pytest.raises(ModelConfigurationError, match="price"):
        choice(test="muse-spark-9.9")


@pytest.mark.req("MODEL-02")
def test_non_synthetic_workspaces_always_get_the_standard_production_model() -> None:
    for role in ("test", "production"):
        model = choice(role=role).for_workspace(synthetic=False)
        assert (model.model_id, model.mode) == (STANDARD, ModelMode.STANDARD)


def test_synthetic_workspaces_use_the_configured_role() -> None:
    assert choice(role="test").for_workspace(synthetic=True).model_id == CONTRIBUTOR
    assert choice(role="production").for_workspace(synthetic=True).model_id == STANDARD


@pytest.mark.req("MODEL-02")
def test_the_contributor_model_is_refused_for_a_non_synthetic_workspace() -> None:
    with pytest.raises(CareerwrightError) as raised:
        assert_model_permitted(model_entry(CONTRIBUTOR), synthetic=False)

    assert raised.value.code is ErrorCode.MODEL_UNAVAILABLE
    assert_model_permitted(model_entry(CONTRIBUTOR), synthetic=True)
    assert_model_permitted(model_entry(STANDARD), synthetic=False)


def run_in(data_mode: DataMode, *, synthetic: bool) -> Run:
    now = datetime.now(UTC)
    return Run(
        run_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        kind=RunKind.INTERVIEW_TURN,
        data_mode=data_mode,
        synthetic=synthetic,
        requested_by=uuid.uuid4(),
        model_id="any",
        model_mode="any",
        status=WorkState.QUEUED,
        failure_class=None,
        output_id=None,
        created_at=now,
        started_at=None,
        finished_at=None,
        profile_version=0,
    )


@pytest.mark.req("MODEL-02", "BND1-11")
@pytest.mark.parametrize(
    ("data_mode", "synthetic", "mode", "refused"),
    [
        (DataMode.LIVE_ASSISTED, False, ModelMode.CONTRIBUTOR, True),
        (DataMode.LIVE_ASSISTED, True, ModelMode.CONTRIBUTOR, False),
        (DataMode.LIVE_ASSISTED, False, ModelMode.STANDARD, False),
        (DataMode.DEMO, True, ModelMode.CONTRIBUTOR, True),  # demo: the fixture only
        (DataMode.DEMO, True, ModelMode.FIXTURE, False),
        (DataMode.LIVE_ASSISTED, True, ModelMode.FIXTURE, True),  # the fixture: demo only
    ],
)
def test_the_activity_re_checks_which_model_a_run_may_call(
    data_mode: DataMode, synthetic: bool, mode: ModelMode, refused: bool
) -> None:
    # Defence in depth behind the submission rule and the database CHECKs.
    refusal = model_refusal(run_in(data_mode, synthetic=synthetic), mode)

    assert refusal is (FailureClass.MODEL_NOT_PERMITTED if refused else None)
