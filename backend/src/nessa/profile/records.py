"""Records of the profile module."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from nessa.profile.document import ProfileDocument


class SourceKind(StrEnum):
    DIRECT_ENTRY = "direct_entry"
    FIXTURE = "fixture"
    CONVERSATION = "conversation"  # a proposal from the interview, confirmed by the person


class Basis(StrEnum):
    """How an answer relates to what the person said (spec section 3: factual confirmations
    and inferences are styled differently)."""

    STATED = "stated"
    INFERRED = "inferred"


@dataclass(frozen=True)
class SourceReference:
    """Where a profile answer came from. A fixture source is pinned by path and SHA-256; a
    conversation source names the interview turn (run) that proposed it, the person's
    messages it cites and its basis, and `recorded_by` is the person who confirmed it."""

    source_ref_id: uuid.UUID
    workspace_id: uuid.UUID
    kind: SourceKind
    label: str
    locator: str | None
    content_sha256: str | None
    recorded_by: uuid.UUID | None
    observed_at: datetime
    created_at: datetime
    run_id: uuid.UUID | None = None
    message_ids: tuple[uuid.UUID, ...] = field(default_factory=tuple)
    basis: Basis | None = None


@dataclass(frozen=True)
class ProfileVersion:
    workspace_id: uuid.UUID
    version: int
    document: ProfileDocument
    created_by: uuid.UUID | None
    created_at: datetime


@dataclass(frozen=True)
class InterviewTurn:
    """One message from the person, written against `profile_version`; its run (same ID)
    produces the proposal."""

    turn_id: uuid.UUID
    workspace_id: uuid.UUID
    message_id: uuid.UUID
    message: str
    profile_version: int
    created_by: uuid.UUID
    created_at: datetime


@dataclass(frozen=True)
class TurnDecision:
    turn_id: uuid.UUID
    decided_by: uuid.UUID
    decided_at: datetime
    accepted_change_ids: tuple[str, ...]
    rejected_change_ids: tuple[str, ...]
    confirmed_hard_constraints: tuple[str, ...]
    profile_version: int | None  # the version the decision created; None: nothing changed
