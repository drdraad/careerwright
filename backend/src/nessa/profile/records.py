"""Records of the profile module."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from nessa.profile.document import ProfileDocument


class SourceKind(StrEnum):
    DIRECT_ENTRY = "direct_entry"
    FIXTURE = "fixture"


@dataclass(frozen=True)
class SourceReference:
    """Where a profile answer came from. A fixture source is pinned by path and SHA-256."""

    source_ref_id: uuid.UUID
    workspace_id: uuid.UUID
    kind: SourceKind
    label: str
    locator: str | None
    content_sha256: str | None
    recorded_by: uuid.UUID | None
    observed_at: datetime
    created_at: datetime


@dataclass(frozen=True)
class ProfileVersion:
    workspace_id: uuid.UUID
    version: int
    document: ProfileDocument
    created_by: uuid.UUID | None
    created_at: datetime
