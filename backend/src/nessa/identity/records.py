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
    command: str
    request_sha256: str
    status_code: int
    response: dict[str, object]
