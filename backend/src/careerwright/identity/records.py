"""Records of the identity and execution module, as returned by its store."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from careerwright.vocabulary import DataMode, WorkState


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
    RUN_CANCEL_REQUESTED = "run.cancel_requested"
    # An acquisition run finished one of its targets; detail: the target's position only.
    RESEARCH_UPDATED = "research.updated"
    PROVISIONAL_CONCEPT_CREATED = "concept.provisional_created"
    INTERVIEW_TURN_DECIDED = "interview.turn_decided"
    INTERVIEW_PREFERENCES_UPDATED = "interview.preferences_updated"
    # Skill evidence, a requirement statement, a matrix edit or the questions' state changed;
    # detail: the capability version only.
    CAPABILITY_UPDATED = "capability.updated"


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
    DISCOVERY = "discovery"  # search queries for career suggestions, from the confirmed profile
    SLATE_EXPLANATION = "slate_explanation"  # the written "Why this could suit you" of a slate
    # Fetch permitted pages or query Adzuna through the restricted acquisition worker. Calls
    # no model, so it names none and needs no key.
    ACQUISITION = "acquisition"
    SOURCE_SEARCH = "source_search"  # Meta search proposes candidate pages for a target
    # A model reads one fetched page's visible text for its job advert; started by the
    # acquisition that fetched it, never by the API (`careerwright.evidence.extraction_runs`).
    PAGE_EXTRACTION = "page_extraction"


KEYLESS_KINDS = frozenset({RunKind.ACQUISITION})


class PartialCompleteness(StrEnum):
    """How complete a run's streamed reply is (spec section 18: partial results carry
    completeness and freshness). Streamed text is never validated and never a result."""

    NONE = "none"  # no reply text has arrived
    STREAMING = "streaming"  # the reply so far; more may follow
    # This attempt's reply stopped, but the run goes on: another attempt may stream a new
    # reply, and a validated output may still supersede it. Not final.
    STOPPED = "stopped"
    INCOMPLETE = "incomplete"  # final: the run ended without a validated output
    SUPERSEDED = "superseded"  # a validated output is stored: it is authoritative


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
    model_id: str | None  # None only for a keyless kind (`KEYLESS_KINDS`)
    model_mode: str | None
    status: WorkState
    failure_class: str | None
    output_id: uuid.UUID | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    # The profile version a run read, pinned at submission (ADR 0004 decision 7); None for
    # a run that reads no workspace input (the connection check).
    profile_version: int | None = None
    cancel_requested_at: datetime | None = None  # DUR-05: the person asked to cancel it


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
