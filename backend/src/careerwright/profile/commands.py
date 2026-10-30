"""Profile commands: one expected-version write path for direct edits and confirmed chat
proposals (spec section 4: "Direct editing and chat use the same application commands").

A workspace starts at version 0, the empty profile, with nothing stored. An accepted write
that changes a field inserts `expected_version + 1`, records a source for each changed
answer and appends a status event, all in the caller's transaction. A write against an
older version is rejected as stale, never merged silently (VERSIONS-01), so the previous
version survives every refused or failed write.
"""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import store as identity_store
from careerwright.identity.access import Actor
from careerwright.identity.records import EventKind
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import store
from careerwright.profile.document import (
    FIELD_NAMES,
    FieldInput,
    ProfileDocument,
    ProfileInput,
    apply_updates,
    empty_profile,
    input_type,
)
from careerwright.profile.records import Basis, SourceKind
from careerwright.profile.store import stale_version

DIRECT_ENTRY_LABEL = "Direct entry"


@dataclass(frozen=True)
class ProfileView:
    """The current profile: version 0 (never saved) has no author or timestamp."""

    workspace_id: uuid.UUID
    version: int
    document: ProfileDocument
    created_by: uuid.UUID | None
    created_at: datetime | None


@dataclass(frozen=True)
class NewSource:
    """A source reference to record if an update citing it changes the profile."""

    source_ref_id: uuid.UUID
    kind: SourceKind
    label: str
    observed_at: datetime
    recorded_by: uuid.UUID
    run_id: uuid.UUID | None = None
    message_ids: tuple[uuid.UUID, ...] = ()
    basis: Basis | None = None
    locator: str | None = None  # an occupation choice's ESCO URI


@dataclass(frozen=True)
class ExistingSource:
    """A source this workspace already recorded, cited again by a restored answer; None
    only for an answer that was not asked."""

    source_ref_id: uuid.UUID | None


@dataclass(frozen=True)
class FieldUpdate:
    value: FieldInput
    source: NewSource | ExistingSource


class RevertProfile(BaseModel):
    """Restore an earlier version's answers, each with its own source, as a new version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0)
    to_version: int = Field(ge=0, description="An earlier version; 0 is the empty profile.")


def current_profile(tx: Tx, workspace_id: uuid.UUID) -> ProfileView:
    visible_workspace(tx, workspace_id)
    stored = store.current_profile(tx, workspace_id)
    if stored is None:
        return ProfileView(workspace_id, 0, empty_profile(), None, None)
    return ProfileView(
        workspace_id, stored.version, stored.document, stored.created_by, stored.created_at
    )


def cited_sources(document: ProfileDocument) -> set[uuid.UUID]:
    return {
        source
        for name in FIELD_NAMES
        if (source := getattr(document, name).source_ref_id) is not None
    }


def commit_profile_version(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    expected_version: int,
    updates: Mapping[str, FieldUpdate],
) -> tuple[ProfileView, list[str]]:
    """The one write path. Returns the resulting profile and the fields it changed (none:
    no new version)."""
    visible_workspace(tx, workspace_id, lock=True)
    current = current_profile(tx, workspace_id)
    if expected_version != current.version:
        raise stale_version(current.version)
    document, changed = apply_updates(
        current.document,
        {name: (u.value, u.source.source_ref_id) for name, u in updates.items()},
    )
    if not changed:
        return current, []
    cited = cited_sources(document)
    recorded: set[uuid.UUID] = set()
    for name in changed:
        source = updates[name].source
        if not isinstance(source, NewSource):
            continue  # already recorded in this workspace
        if source.source_ref_id in cited and source.source_ref_id not in recorded:
            recorded.add(source.source_ref_id)
            store.insert_source(
                tx,
                source_ref_id=source.source_ref_id,
                workspace_id=workspace_id,
                kind=source.kind,
                label=source.label,
                recorded_by=source.recorded_by,
                observed_at=source.observed_at,
                run_id=source.run_id,
                message_ids=source.message_ids,
                basis=source.basis,
                locator=source.locator,
            )
    created = store.insert_profile_version(
        tx, workspace_id, expected_version + 1, document, actor.actor_id
    )
    store.link_sources(tx, workspace_id, created.version, cited)
    identity_store.append_event(
        tx,
        workspace_id,
        EventKind.PROFILE_VERSION_CREATED,
        str(created.version),
        detail={"version": created.version, "changed_fields": ",".join(changed)},
    )
    view = ProfileView(
        workspace_id, created.version, created.document, created.created_by, created.created_at
    )
    return view, changed


def write_profile(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    expected_version: int,
    new: ProfileInput,
    now: datetime,
) -> tuple[ProfileView, bool]:
    """A direct edit of the whole profile. Returns the profile and whether a version was
    created; changed answers cite one new direct-entry source."""
    source = NewSource(
        source_ref_id=uuid.uuid4(),
        kind=SourceKind.DIRECT_ENTRY,
        label=DIRECT_ENTRY_LABEL,
        observed_at=now,
        recorded_by=actor.actor_id,
    )
    updates = {name: FieldUpdate(getattr(new, name), source) for name in FIELD_NAMES}
    view, changed = commit_profile_version(tx, actor, workspace_id, expected_version, updates)
    return view, bool(changed)


def revert_profile(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: RevertProfile
) -> tuple[ProfileView, bool]:
    """Undo: an earlier version's answers become the newest version, each citing the source
    it had then (a fixture stays a fixture, a confirmed reading keeps its basis and turn),
    never re-recorded as a direct entry. Returns the profile and whether it changed."""
    visible_workspace(tx, workspace_id, lock=True)
    current = current_profile(tx, workspace_id)
    if command.expected_version != current.version:
        raise stale_version(current.version)
    if command.to_version >= current.version:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Restore an earlier version than the current one.",
            stage=ErrorStage.PROFILE,
            details={"field": "to_version", "reason": "not_earlier"},
        )
    earlier = store.profile_version(tx, workspace_id, command.to_version)
    document = empty_profile() if earlier is None else earlier.document
    view, changed = commit_profile_version(
        tx, actor, workspace_id, command.expected_version, restored_answers(document)
    )
    return view, bool(changed)


def restored_answers(document: ProfileDocument) -> dict[str, FieldUpdate]:
    """A stored version's answers as updates citing their own sources. An answer stored before
    a newer input rule (a £0 salary floor) is refused in words, never saved again."""
    updates: dict[str, FieldUpdate] = {}
    for name in FIELD_NAMES:
        field = getattr(document, name)
        try:
            answer = input_type(name).model_validate({"state": field.state, "value": field.value})
        except ValidationError:
            raise CareerwrightError(
                ErrorCode.VALIDATION_FAILED,
                "An answer in that version can't be saved any more; edit it directly instead.",
                stage=ErrorStage.PROFILE,
                details={"field": name, "reason": "no_longer_valid"},
            ) from None
        updates[name] = FieldUpdate(answer, ExistingSource(field.source_ref_id))
    return updates
