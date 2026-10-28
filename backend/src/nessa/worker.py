"""The worker process entry point (composition root): the run tasks of every module, the
model each run's pinned ID names, and the DBOS worker loop (`nessa.identity.worker`).

Configuration comes from the environment and files only. A Meta model is built with the
key the activity opened just in time; the fixture interviewer (demo workspaces only)
needs no key and makes no network call.

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
from nessa.identity.model_registry import ModelMode, model_entry
from nessa.identity.records import RunKind
from nessa.logs import configure_logging
from nessa.profile.interview_agent import INTERVIEW_TURN_TASK, fixture_interviewer_model

TASKS: Mapping[RunKind, RunTask] = {
    RunKind.CONNECTION_CHECK: CONNECTION_CHECK_TASK,
    RunKind.INTERVIEW_TURN: INTERVIEW_TURN_TASK,
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
    """The fixture interviewer for its model ID, else `provider` (Meta; a fake in tests)."""

    def build(model_id: str, api_key: SecretStr | None) -> Model:
        if model_entry(model_id).mode is ModelMode.FIXTURE:
            return fixture_interviewer_model()
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
