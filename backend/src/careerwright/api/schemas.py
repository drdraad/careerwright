"""The API contract. The TypeScript client is generated from the OpenAPI schema built from
these models, so enums and money appear here once (Global Constraint 10)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from careerwright.identity.access import Actor
from careerwright.identity.connection_check import ConnectionCheckResult
from careerwright.identity.failures import FailureClass
from careerwright.identity.model_registry import ModelMode
from careerwright.identity.records import (
    Attempt,
    Credential,
    EventKind,
    Run,
    RunKind,
    Workspace,
    WorkspaceEvent,
)
from careerwright.identity.spend import BudgetScope, SpendState
from careerwright.identity.spend_limits import RunEstimate, SpendSummary
from careerwright.identity.workspaces import WorkspaceName
from careerwright.profile.commands import ProfileView
from careerwright.profile.document import ProfileDocument, ProfileInput
from careerwright.profile.records import Basis, ProfileVersion, SourceKind, SourceReference
from careerwright.vocabulary import DataMode, WorkState


class ResponseModel(BaseModel):
    """Base of every response body: closed and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ActorOut(ResponseModel):
    actor_id: uuid.UUID
    email: str
    display_name: str

    @classmethod
    def of(cls, actor: Actor) -> "ActorOut":
        return cls(actor_id=actor.actor_id, email=actor.email, display_name=actor.display_name)


class WorkspaceOut(ResponseModel):
    workspace_id: uuid.UUID
    name: str
    data_mode: DataMode
    synthetic: bool = Field(description="Persistent synthetic-data label; never changes.")
    fixture: bool = Field(description="The named fixture workspace that `make reset-demo` resets.")
    version: int
    last_event_seq: int = Field(
        description="The workspace's latest status-event sequence number when read: pass it "
        "as Last-Event-ID to receive only what happens after this read."
    )
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, workspace: Workspace) -> "WorkspaceOut":
        return cls(
            workspace_id=workspace.workspace_id,
            name=workspace.name,
            data_mode=workspace.data_mode,
            synthetic=workspace.synthetic,
            fixture=workspace.fixture_key is not None,
            version=workspace.version,
            last_event_seq=workspace.last_event_seq,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )


class WorkspacePage(ResponseModel):
    items: list[WorkspaceOut]
    next_cursor: str | None


class RenameWorkspaceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    name: WorkspaceName


class ProfileOut(ResponseModel):
    workspace_id: uuid.UUID
    version: int = Field(description="0 means nothing has been saved yet.")
    document: ProfileDocument
    created_by: uuid.UUID | None
    created_at: datetime | None

    @classmethod
    def of(cls, view: ProfileView) -> "ProfileOut":
        return cls(
            workspace_id=view.workspace_id,
            version=view.version,
            document=view.document,
            created_by=view.created_by,
            created_at=view.created_at,
        )

    @classmethod
    def of_version(cls, version: ProfileVersion) -> "ProfileOut":
        return cls(
            workspace_id=version.workspace_id,
            version=version.version,
            document=version.document,
            created_by=version.created_by,
            created_at=version.created_at,
        )


class ProfileWriteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=0)
    profile: ProfileInput


class ProfileVersionPage(ResponseModel):
    items: list[ProfileOut]
    next_cursor: str | None


class SourceOut(ResponseModel):
    """Where an answer came from. A conversation source also names the turn that proposed
    it, the person's messages it cites and its basis; `recorded_by` confirmed it."""

    source_ref_id: uuid.UUID
    kind: SourceKind
    label: str
    locator: str | None
    content_sha256: str | None
    recorded_by: uuid.UUID | None
    observed_at: datetime
    created_at: datetime
    turn_id: uuid.UUID | None = None
    message_ids: list[uuid.UUID] = Field(default_factory=list)
    basis: Basis | None = None
    discovery_id: uuid.UUID | None = Field(
        default=None, description="An occupation choice: the discovery that suggested it."
    )

    @classmethod
    def of(cls, source: SourceReference) -> "SourceOut":
        conversation = source.kind is SourceKind.CONVERSATION
        return cls(
            source_ref_id=source.source_ref_id,
            kind=source.kind,
            label=source.label,
            locator=source.locator,
            content_sha256=source.content_sha256,
            recorded_by=source.recorded_by,
            observed_at=source.observed_at,
            created_at=source.created_at,
            turn_id=source.run_id if conversation else None,
            message_ids=list(source.message_ids),
            basis=source.basis,
            discovery_id=None if conversation else source.run_id,
        )


class SourcePage(ResponseModel):
    items: list[SourceOut]
    next_cursor: str | None


class EventOut(ResponseModel):
    """One status event. The stream's SSE `id` is `seq`; reconnect with Last-Event-ID."""

    seq: int
    kind: EventKind
    subject_id: str
    state: WorkState | None
    detail: dict[str, str | int]
    created_at: datetime

    @classmethod
    def of(cls, event: WorkspaceEvent) -> "EventOut":
        return cls(
            seq=event.seq,
            kind=event.kind,
            subject_id=event.subject_id,
            state=event.state,
            detail=event.detail,
            created_at=event.created_at,
        )


class EventPage(ResponseModel):
    items: list[EventOut]
    last_seq: int = Field(description="Pass as `after` (or Last-Event-ID) to continue.")


class Health(ResponseModel):
    status: str


class CredentialOut(ResponseModel):
    """Metadata only. No endpoint ever returns key material, or any part of it."""

    credential_id: uuid.UUID
    provider: str
    active: bool
    consented_at: datetime
    created_by: uuid.UUID
    created_at: datetime
    revoked_at: datetime | None
    replaced_by: uuid.UUID | None

    @classmethod
    def of(cls, credential: Credential) -> "CredentialOut":
        return cls(
            credential_id=credential.credential_id,
            provider=credential.provider,
            active=credential.revoked_at is None,
            consented_at=credential.consented_at,
            created_by=credential.created_by,
            created_at=credential.created_at,
            revoked_at=credential.revoked_at,
            replaced_by=credential.replaced_by,
        )


class CredentialList(ResponseModel):
    items: list[CredentialOut]


class SpendOut(ResponseModel):
    """Provider spend in integer nano-USD (Meta bills in USD; never a float)."""

    run_limit_nano_usd: int
    period_limit_nano_usd: int
    version: int = Field(description="0 while the configured defaults apply.")
    period_start: date
    period_committed_nano_usd: int = Field(
        description="Known costs plus the full reservation of every call whose cost is unknown."
    )
    unknown_cost_attempts: int

    @classmethod
    def of(cls, summary: SpendSummary) -> "SpendOut":
        return cls(
            run_limit_nano_usd=summary.limits.run_limit_nano_usd,
            period_limit_nano_usd=summary.limits.period_limit_nano_usd,
            version=summary.version,
            period_start=summary.period_start,
            period_committed_nano_usd=summary.period_committed_nano_usd,
            unknown_cost_attempts=summary.unknown_cost_attempts,
        )


class RunEstimateOut(ResponseModel):
    """What one run of a kind may spend on the person's key, shown before it starts (spec
    section 16; MODEL-08): two maxima in integer nano-USD, never an expected cost."""

    kind: RunKind
    model_id: str = Field(description="The model this workspace's runs of this kind pin.")
    model_mode: ModelMode
    per_run_nano_usd: int = Field(
        description="The most the run spends without a worker crash: every attempt it may "
        "make, each at its reservation's bounds, never past the run limit (0 for a fixture)."
    )
    hard_maximum_nano_usd: int = Field(
        description="The most it can ever spend, a worker crash included: the workspace's "
        "per-run spend limit, past which a run never reserves (0 for a fixture)."
    )
    refused_scope: BudgetScope | None = Field(
        description="The spend limit that would refuse the run if it started now; null when "
        "it fits."
    )

    @classmethod
    def of(cls, estimate: RunEstimate) -> "RunEstimateOut":
        return cls(
            kind=estimate.kind,
            model_id=estimate.model.model_id,
            model_mode=estimate.model.mode,
            per_run_nano_usd=estimate.per_run_nano_usd,
            hard_maximum_nano_usd=estimate.hard_maximum_nano_usd,
            refused_scope=estimate.refused_scope,
        )


class AttemptOut(ResponseModel):
    attempt_id: int
    model_id: str
    started_at: datetime
    finished_at: datetime | None
    outcome: str | None
    spend_state: SpendState
    reserved_nano_usd: int
    cost_nano_usd: int | None = Field(
        description="0 when no provider call was made (spend_state none); null: unknown."
    )
    input_tokens: int | None
    output_tokens: int | None
    requests_sent: int | None = Field(
        default=None, description="Provider requests in the attempt; a validation repair adds one."
    )

    @classmethod
    def of(cls, attempt: Attempt) -> "AttemptOut":
        return cls(
            attempt_id=attempt.attempt_id,
            model_id=attempt.model_id,
            started_at=attempt.started_at,
            finished_at=attempt.finished_at,
            outcome=attempt.outcome,
            spend_state=SpendState(attempt.spend_state),
            reserved_nano_usd=attempt.reserved_nano_usd,
            cost_nano_usd=attempt.cost_nano_usd,
            input_tokens=attempt.input_tokens,
            output_tokens=attempt.output_tokens,
            requests_sent=attempt.requests_sent,
        )


class RunOut(ResponseModel):
    """The authoritative run state. A failed or unavailable run never carries an output."""

    run_id: uuid.UUID
    kind: RunKind
    status: WorkState
    failure_class: FailureClass | None
    data_mode: DataMode
    synthetic: bool
    model_id: str | None = Field(description="None for a run that calls no model (acquisition).")
    model_mode: ModelMode | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    cancel_requested_at: datetime | None = Field(
        default=None,
        description="When the person asked to cancel it; the run ends `cancelled` once the "
        "worker has stopped it.",
    )
    attempts: list[AttemptOut]
    output: ConnectionCheckResult | None = Field(
        description="A connection check's result. An interview turn's proposals are read "
        "through the turn (`GET .../interview/turns/{turn_id}`)."
    )
    profile_version: int | None = Field(
        default=None, description="The profile version the run read, pinned at submission."
    )

    @classmethod
    def of(
        cls, run: Run, attempts: list[Attempt], output: ConnectionCheckResult | None
    ) -> "RunOut":
        return cls(
            run_id=run.run_id,
            kind=run.kind,
            status=run.status,
            failure_class=FailureClass(run.failure_class) if run.failure_class else None,
            data_mode=run.data_mode,
            synthetic=run.synthetic,
            model_id=run.model_id,
            model_mode=ModelMode(run.model_mode) if run.model_mode else None,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
            cancel_requested_at=run.cancel_requested_at,
            attempts=[AttemptOut.of(a) for a in attempts],
            output=output,
            profile_version=run.profile_version,
        )


class RunCancelOut(RunOut):
    """A cancel's answer (DUR-05): the run as it stands, and the runs whose cancellation the
    request asked for (review C-1 N2)."""

    cancellation_requested: list[uuid.UUID] = Field(
        description="The runs whose cancellation this asked for: the run itself while it is "
        "queued or running, and every run it started that has not settled (an acquisition's "
        "extraction runs), or both. Each ends `cancelled` once the worker has stopped it."
    )


class RunPage(ResponseModel):
    items: list[RunOut]
    next_cursor: str | None
