"""The API contract. The TypeScript client is generated from the OpenAPI schema built from
these models, so enums and money appear here once (Global Constraint 10)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from nessa.identity.access import Actor
from nessa.identity.connection_check import ConnectionCheckResult
from nessa.identity.failures import FailureClass
from nessa.identity.model_registry import ModelMode
from nessa.identity.records import (
    Attempt,
    Credential,
    EventKind,
    Run,
    RunKind,
    Workspace,
    WorkspaceEvent,
)
from nessa.identity.spend import SpendState
from nessa.identity.spend_limits import SpendSummary
from nessa.identity.workspaces import WorkspaceName
from nessa.profile.commands import ProfileView
from nessa.profile.document import ProfileDocument, ProfileInput
from nessa.profile.records import SourceKind, SourceReference
from nessa.vocabulary import DataMode, WorkState


class _Out(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ActorOut(_Out):
    actor_id: uuid.UUID
    email: str
    display_name: str

    @classmethod
    def of(cls, actor: Actor) -> "ActorOut":
        return cls(actor_id=actor.actor_id, email=actor.email, display_name=actor.display_name)


class WorkspaceOut(_Out):
    workspace_id: uuid.UUID
    name: str
    data_mode: DataMode
    synthetic: bool = Field(description="Persistent synthetic-data label; never changes.")
    fixture: bool = Field(description="The named fixture workspace that `make reset-demo` resets.")
    version: int
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
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )


class WorkspacePage(_Out):
    items: list[WorkspaceOut]
    next_cursor: str | None


class RenameWorkspaceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    name: WorkspaceName


class ProfileOut(_Out):
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


class ProfileWriteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=0)
    profile: ProfileInput


class ProfileVersionPage(_Out):
    items: list[ProfileOut]
    next_cursor: str | None


class SourceOut(_Out):
    source_ref_id: uuid.UUID
    kind: SourceKind
    label: str
    locator: str | None
    content_sha256: str | None
    recorded_by: uuid.UUID | None
    observed_at: datetime
    created_at: datetime

    @classmethod
    def of(cls, source: SourceReference) -> "SourceOut":
        return cls(
            source_ref_id=source.source_ref_id,
            kind=source.kind,
            label=source.label,
            locator=source.locator,
            content_sha256=source.content_sha256,
            recorded_by=source.recorded_by,
            observed_at=source.observed_at,
            created_at=source.created_at,
        )


class SourcePage(_Out):
    items: list[SourceOut]
    next_cursor: str | None


class EventOut(_Out):
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


class EventPage(_Out):
    items: list[EventOut]
    last_seq: int = Field(description="Pass as `after` (or Last-Event-ID) to continue.")


class Health(_Out):
    status: str


class CredentialOut(_Out):
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


class CredentialList(_Out):
    items: list[CredentialOut]


class SpendOut(_Out):
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


class AttemptOut(_Out):
    attempt_id: int
    model_id: str
    started_at: datetime
    finished_at: datetime | None
    outcome: str | None
    spend_state: SpendState
    reserved_nano_usd: int
    cost_nano_usd: int | None = Field(description="null: unknown, never zero.")
    input_tokens: int | None
    output_tokens: int | None

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
        )


class RunOut(_Out):
    """The authoritative run state. A failed or unavailable run never carries an output."""

    run_id: uuid.UUID
    kind: RunKind
    status: WorkState
    failure_class: FailureClass | None
    data_mode: DataMode
    synthetic: bool
    model_id: str
    model_mode: ModelMode
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    attempts: list[AttemptOut]
    output: ConnectionCheckResult | None

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
            model_mode=ModelMode(run.model_mode),
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
            attempts=[AttemptOut.of(a) for a in attempts],
            output=output,
        )


class RunPage(_Out):
    items: list[RunOut]
    next_cursor: str | None
