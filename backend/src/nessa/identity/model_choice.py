"""Which Meta model a run uses, and the rule that keeps personal data off Contributor models.

Non-synthetic workspaces always use the Standard production model. A synthetic workspace
uses the configured role: by default the cheaper test model (ruling R5). The Contributor
test model lets Meta train on traffic, so it is refused for any workspace not labelled
synthetic, at submission and again inside the activity (ADR 0003; carried-forward ruling).
Demo workspaces never reach a Meta model: their interview turns use the fixture
interviewer (`fixture_model`), which no configuration can make a test or production model.
"""

from dataclasses import dataclass
from typing import Literal

from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity.model_registry import (
    FIXTURE_MODEL_ID,
    ModelEntry,
    ModelMode,
    UnknownModelError,
    model_entry,
)

ModelRole = Literal["test", "production"]


class ModelConfigurationError(ValueError):
    """The configured models cannot be used (unknown price, or a Contributor production model)."""


@dataclass(frozen=True)
class ModelChoice:
    test: ModelEntry
    production: ModelEntry
    synthetic_role: ModelRole

    @classmethod
    def configure(
        cls, test_model: str, production_model: str, synthetic_role: ModelRole
    ) -> "ModelChoice":
        try:
            test, production = model_entry(test_model), model_entry(production_model)
        except UnknownModelError as error:
            raise ModelConfigurationError(
                f"no recorded price or mode for model {error.args[0]!r}"
            ) from None
        if production.mode is not ModelMode.STANDARD:
            # Spec section 16: personal data uses Standard mode; never select Contributor.
            raise ModelConfigurationError("the production model must be a Standard-mode model")
        if test.mode is ModelMode.FIXTURE:
            # The fixture interviewer answers demo workspaces only; it is never a Meta model.
            raise ModelConfigurationError("the test model must be a Meta model")
        return cls(test=test, production=production, synthetic_role=synthetic_role)

    def for_workspace(self, *, synthetic: bool) -> ModelEntry:
        if synthetic and self.synthetic_role == "test":
            return self.test
        return self.production

    def is_production(self, model_id: str) -> bool:
        return model_id == self.production.model_id


def fixture_model() -> ModelEntry:
    return model_entry(FIXTURE_MODEL_ID)


def assert_model_permitted(model: ModelEntry, *, synthetic: bool) -> None:
    if model.mode is ModelMode.CONTRIBUTOR and not synthetic:
        raise NessaError(
            ErrorCode.MODEL_UNAVAILABLE,
            "The test model may only see synthetic data, and this workspace is not synthetic.",
            stage=ErrorStage.EXECUTION,
        )
