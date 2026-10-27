import pytest
from pydantic import ValidationError

from spikes.meta.settings import MetaSettings


def settings(**values: str) -> MetaSettings:
    # model_validate skips the settings sources, so the real key in .env is never read.
    return MetaSettings.model_validate({"META_API_KEY": "unit-test-key", **values})


def test_unit_settings_never_read_the_real_key() -> None:
    assert settings().api_key.get_secret_value() == "unit-test-key"


def test_test_model_calls_do_not_count_as_production_by_default() -> None:
    configured = settings()

    assert not configured.is_production_model(configured.test_model)
    assert configured.is_production_model("muse-spark-1.3")


def test_test_model_set_to_the_production_model_counts_as_production() -> None:
    # ADR 0003 fallback: NESSA_META_TEST_MODEL=muse-spark-1.3 must not bypass the cap.
    configured = settings(NESSA_META_TEST_MODEL="muse-spark-1.3")

    assert configured.is_production_model(configured.test_model)


def test_contributor_production_model_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Standard-mode"):
        settings(NESSA_META_PRODUCTION_MODEL="muse-spark-1.3-contributor")
