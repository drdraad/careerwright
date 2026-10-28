"""Records of the identity and execution module, as returned by its store."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from nessa.vocabulary import DataMode, WorkState


@dataclass(frozen=True)
class Workspace:
    workspace_id: uuid.UUID
    owner_actor_id: uuid.UUID
    name: str
    data_mode: DataMode
    synthetic: bool
    fixture_key: str | None
    version: int
    last_event_seq: int
    created_at: datetime
    updated_at: datetime


class EventKind(StrEnum):
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_RESET = "workspace.reset"
    PROFILE_VERSION_CREATED = "profile.version_created"
    CREDENTIAL_STORED = "credential.stored"
    CREDENTIAL_ROTATED = "credential.rotated"
    CREDENTIAL_REVOKED = "credential.revoked"
    SPEND_LIMITS_UPDATED = "spend_limits.updated"
    RUN_STATE_CHANGED = "run.state_changed"


@dataclass(frozen=True)
class WorkspaceEvent:
    """A durable status event. `detail` holds identifiers and labels only."""

    workspace_id: uuid.UUID
    seq: int
    kind: EventKind
    subject_id: str
    state: WorkState | None
    created_at: datetime
    detail: dict[str, str | int] = field(default_factory=dict)


@dataclass(frozen=True)
class Receipt:
    """A command's recorded response. It is deleted with its workspace (it holds copies)."""

    command: str
    request_sha256: str
    status_code: int
    response: dict[str, object]
    workspace_id: uuid.UUID


@dataclass(frozen=True)
class Credential:
    """Credential metadata. Key material never leaves the sealed columns."""

    credential_id: uuid.UUID
    workspace_id: uuid.UUID
    provider: str
    key_version: int
    consented_at: datetime
    created_by: uuid.UUID
    created_at: datetime
    revoked_at: datetime | None
    replaced_by: uuid.UUID | None


class RunKind(StrEnum):
    CONNECTION_CHECK = "connection_check"


@dataclass(frozen=True)
class Run:
    run_id: uuid.UUID
    workspace_id: uuid.UUID
    kind: RunKind
    data_mode: DataMode
    synthetic: bool
    requested_by: uuid.UUID
    model_id: str
    model_mode: str
    status: WorkState
    failure_class: str | None
    output_id: uuid.UUID | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


@dataclass(frozen=True)
class Attempt:
    attempt_id: int
    model_id: str
    started_at: datetime
    finished_at: datetime | None
    outcome: str | None
    spend_state: str
    reserved_nano_usd: int
    cost_nano_usd: int | None
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    web_search_queries: int | None
    provider_response_id: str | None
