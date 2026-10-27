"""Meta model configuration for the spike (ruling R5: model choice is configuration).

The key is read from the repository's gitignored `.env` (or the environment) into a
`SecretStr`; it is never accepted as a command argument and never printed.
"""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRIBUTOR_SUFFIX = "-contributor"


class MetaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    api_key: SecretStr = Field(validation_alias="META_API_KEY")
    # Test model: cheapest Meta model with the needed capabilities. Contributor mode lets Meta
    # train on prompts, so it is only for synthetic or public test inputs (ADR 0003).
    test_model: str = Field(
        default="muse-spark-1.3-contributor", validation_alias="NESSA_META_TEST_MODEL"
    )
    production_model: str = Field(
        default="muse-spark-1.3", validation_alias="NESSA_META_PRODUCTION_MODEL"
    )

    def is_production_model(self, model_id: str) -> bool:
        """Whether a call on `model_id` counts against the production-call cap."""
        return model_id == self.production_model

    @field_validator("production_model")
    @classmethod
    def _production_model_is_standard_mode(cls, value: str) -> str:
        # Spec section 16: personal data uses Standard mode; never select Contributor silently.
        if value.endswith(CONTRIBUTOR_SUFFIX):
            raise ValueError("the production model must be a Standard-mode model ID")
        return value
