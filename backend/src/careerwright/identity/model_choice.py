"""Which Meta model a run uses, and the rule that keeps personal data off Contributor models.

Non-synthetic workspaces always use the Standard production model. A synthetic workspace
uses the configured role: by default the cheaper test model (ruling R5). The Contributor
test model lets Meta train on traffic, so it is refused for any workspace not labelled
synthetic, at submission and again inside the activity (ADR 0003; carried-forward ruling).
Demo workspaces never reach a Meta model: their interview turns, discoveries and slate
explanations use the deterministic fixture models (`fixture_model`), which no configuration
can make a test or production model.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity.model_registry import (
    FIXTURE_DISCOVERY_MODEL_ID,
    FIXTURE_EXPLAINER_MODEL_ID,
    FIXTURE_MODEL_ID,
    ModelEntry,
    ModelMode,
    UnknownModelError,
    model_entry,
)
from careerwright.identity.records import RunKind

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


# The deterministic demo stand-in for each kind of run a demo workspace may make.
FIXTURE_MODELS: Mapping[RunKind, str] = {
    RunKind.INTERVIEW_TURN: FIXTURE_MODEL_ID,
    RunKind.DISCOVERY: FIXTURE_DISCOVERY_MODEL_ID,
    RunKind.SLATE_EXPLANATION: FIXTURE_EXPLAINER_MODEL_ID,
}


def fixture_model(kind: RunKind) -> ModelEntry | None:
    """The demo stand-in for this kind of run, if it has one (None: a demo workspace never
    makes this kind of run)."""
    model_id = FIXTURE_MODELS.get(kind)
    return None if model_id is None else model_entry(model_id)


def assert_model_permitted(model: ModelEntry, *, synthetic: bool) -> None:
    if model.mode is ModelMode.CONTRIBUTOR and not synthetic:
        raise CareerwrightError(
            ErrorCode.MODEL_UNAVAILABLE,
            "The test model may only see synthetic data, and this workspace is not synthetic.",
            stage=ErrorStage.EXECUTION,
        )
