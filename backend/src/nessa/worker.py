"""The worker process entry point (composition root): the run tasks of every module, the
model each run's pinned ID names, and the DBOS worker loop (`nessa.identity.worker`).

Configuration comes from the environment and files only. A Meta model is built with the
key the activity opened just in time; the fixture interviewer, query proposer and explainer
(demo workspaces only) need no key and make no network call.

Run: `python -m nessa.worker`; health check: `python -m nessa.worker --check`.
"""

import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from pydantic import SecretStr
from pydantic_ai.models import Model

from nessa.config import WorkerSettings
from nessa.db import create_engine, url_with_password
from nessa.identity import connection_check, worker
from nessa.identity.activity import CONNECTION_CHECK_TASK, ActivityRuntime, ModelBuilder, RunTask
from nessa.identity.keyring import load_keyring
from nessa.identity.meta import meta_model
from nessa.identity.model_choice import ModelChoice
from nessa.identity.model_registry import (
    FIXTURE_DISCOVERY_MODEL_ID,
    FIXTURE_EXPLAINER_MODEL_ID,
    FIXTURE_MODEL_ID,
    ModelMode,
    model_entry,
)
from nessa.identity.records import RunKind
from nessa.logs import configure_logging
from nessa.profile.discovery_agent import DISCOVERY_TASK, fixture_discovery_model
from nessa.profile.interview_agent import INTERVIEW_TURN_TASK, fixture_interviewer_model
from nessa.profile.slate_explanation_agent import SLATE_EXPLANATION_TASK, fixture_explainer_model

TASKS: Mapping[RunKind, RunTask] = {
    RunKind.CONNECTION_CHECK: CONNECTION_CHECK_TASK,
    RunKind.INTERVIEW_TURN: INTERVIEW_TURN_TASK,
    RunKind.DISCOVERY: DISCOVERY_TASK,
    RunKind.SLATE_EXPLANATION: SLATE_EXPLANATION_TASK,
}
# The deterministic stand-ins for demo workspaces, by model ID.
FIXTURE_MODELS: Mapping[str, Callable[[], Model]] = {
    FIXTURE_MODEL_ID: fixture_interviewer_model,
    FIXTURE_DISCOVERY_MODEL_ID: fixture_discovery_model,
    FIXTURE_EXPLAINER_MODEL_ID: fixture_explainer_model,
}


class MissingKeyError(RuntimeError):
    """A Meta model was requested without a key (the activity always opens one first)."""


# A provider model for a model ID and the key the activity opened.
ProviderBuilder = Callable[[str, SecretStr], Model]


def _meta(model_id: str, api_key: SecretStr) -> Model:
    # Each task sets its own output bound per run; this is the default ceiling.
    return meta_model(
        model_id,
        api_key,
        max_output_tokens=connection_check.LIMITS.max_output_tokens,
        effort="minimal",
    )


def model_builder(provider: ProviderBuilder = _meta) -> ModelBuilder:
    """The fixture model for its model ID, else `provider` (Meta; a fake in tests)."""

    def build(model_id: str, api_key: SecretStr | None) -> Model:
        if model_entry(model_id).mode is ModelMode.FIXTURE:
            return FIXTURE_MODELS[model_id]()
        if api_key is None:
            raise MissingKeyError(model_id)
        return provider(model_id, api_key)

    return build


def _utc_now() -> datetime:
    return datetime.now(UTC)


def main() -> None:
    if sys.argv[1:] == ["--check"]:
        sys.exit(worker.check())
    configure_logging("worker")
    settings = WorkerSettings()
    # Fail closed on an unusable model configuration before any work is accepted.
    ModelChoice.configure(
        settings.meta_test_model, settings.meta_production_model, settings.synthetic_model_role
    )
    engine = create_engine(settings.app_database, application_name="nessa-worker")
    runtime = ActivityRuntime(
        engine=engine,
        keyring=load_keyring(settings.master_key_dir),
        build_model=model_builder(),
        clock=_utc_now,
        tasks=TASKS,
    )
    worker.run(engine, runtime, url_with_password(settings.dbos_database))


if __name__ == "__main__":
    main()
