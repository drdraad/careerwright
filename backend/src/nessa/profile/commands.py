"""Profile commands: an expected-version write creates the next immutable profile version.

A workspace starts at version 0, the empty profile, with nothing stored. Each accepted write
whose content differs inserts `expected_version + 1`, records a direct-entry source for the
changed answers and appends a status event, all in the caller's transaction. A write against
an older version is rejected as stale, never merged silently (VERSIONS-01).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from nessa.db import Tx
from nessa.identity import store as identity_store
from nessa.identity.access import Actor
from nessa.identity.records import EventKind
from nessa.identity.workspaces import visible_workspace
from nessa.profile import store
from nessa.profile.document import (
    FIELD_NAMES,
    ProfileDocument,
    ProfileInput,
    apply_profile_input,
    changed_fields,
    empty_profile,
)
from nessa.profile.records import SourceKind
from nessa.profile.store import stale_version

DIRECT_ENTRY_LABEL = "Direct entry"


@dataclass(frozen=True)
class ProfileView:
    """The current profile: version 0 (never saved) has no author or timestamp."""

    workspace_id: uuid.UUID
    version: int
    document: ProfileDocument
    created_by: uuid.UUID | None
    created_at: datetime | None


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


def write_profile(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    expected_version: int,
    new: ProfileInput,
    now: datetime,
) -> tuple[ProfileView, bool]:
    """Returns the resulting profile and whether a new version was created."""
    visible_workspace(tx, workspace_id, lock=True)
    current = current_profile(tx, workspace_id)
    if expected_version != current.version:
        raise stale_version(current.version)
    changed = changed_fields(current.document, new)
    if not changed:
        return current, False
    source_id = uuid.uuid4()
    store.insert_source(
        tx,
        source_ref_id=source_id,
        workspace_id=workspace_id,
        kind=SourceKind.DIRECT_ENTRY,
        label=DIRECT_ENTRY_LABEL,
        recorded_by=actor.actor_id,
        observed_at=now,
    )
    document = apply_profile_input(current.document, new, source_id)
    created = store.insert_profile_version(
        tx, workspace_id, expected_version + 1, document, actor.actor_id
    )
    store.link_sources(tx, workspace_id, created.version, cited_sources(document))
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
    return view, True
