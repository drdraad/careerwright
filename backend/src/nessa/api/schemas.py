"""The API contract. The TypeScript client is generated from the OpenAPI schema built from
these models, so enums and money appear here once (Global Constraint 10)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from nessa.identity.access import Actor
from nessa.identity.records import EventKind, Workspace, WorkspaceEvent
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
