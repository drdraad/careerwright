"""Which model a run may use (ADR 0003; MODEL-02; the Contributor ruling carried into Task 3)."""

import pytest

from nessa.errors import ErrorCode, NessaError
from nessa.identity.model_choice import ModelChoice, ModelConfigurationError, assert_model_permitted
from nessa.identity.model_registry import ModelMode, model_entry

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
    with pytest.raises(NessaError) as raised:
        assert_model_permitted(model_entry(CONTRIBUTOR), synthetic=False)

    assert raised.value.code is ErrorCode.MODEL_UNAVAILABLE
    assert_model_permitted(model_entry(CONTRIBUTOR), synthetic=True)
    assert_model_permitted(model_entry(STANDARD), synthetic=False)
