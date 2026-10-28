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
    RUN_PARTIAL_UPDATED = "run.partial_updated"  # detail: the partial's sequence number only
    PROVISIONAL_CONCEPT_CREATED = "concept.provisional_created"
    INTERVIEW_TURN_DECIDED = "interview.turn_decided"


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
    INTERVIEW_TURN = "interview_turn"


class PartialCompleteness(StrEnum):
    """How complete a run's streamed reply is (spec section 18: partial results carry
    completeness and freshness). Streamed text is never validated and never a result."""

    NONE = "none"  # no reply text has arrived
    STREAMING = "streaming"  # the reply so far; more may follow
    INCOMPLETE = "incomplete"  # it stopped and will not complete (that attempt or run failed)
    SUPERSEDED = "superseded"  # the run completed: its validated output is authoritative


@dataclass(frozen=True)
class PartialReply:
    seq: int | None  # the partial's write sequence, as its status events carry it
    completeness: PartialCompleteness
    text: str | None
    updated_at: datetime | None


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
    # The profile version a run read, pinned at submission (ADR 0004 decision 7); None for
    # a run that reads no workspace input (the connection check).
    profile_version: int | None = None


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
    requests_sent: int | None = None  # provider requests in the attempt (a repair adds one)
