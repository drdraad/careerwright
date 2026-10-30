"""Records of the profile module."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from careerwright.profile.document import ProfileDocument


class SourceKind(StrEnum):
    DIRECT_ENTRY = "direct_entry"
    FIXTURE = "fixture"
    CONVERSATION = "conversation"  # a proposal from the interview, confirmed by the person
    # An occupation the person chose from the taxonomy as a target: a suggestion, or the
    # ESCO occupation an ambiguous title meant. Its locator is the ESCO URI.
    OCCUPATION_CHOICE = "occupation_choice"


class EntryMode(StrEnum):
    """How the person chose to start (spec section 3, the You chapter)."""

    SURE = "sure"  # "I know my direction": confirm the target, skip optional exploration
    UNSURE = "unsure"  # "Help me explore": explore tasks first, then a varied slate


class ConversationMode(StrEnum):
    """The tone the person chose (spec section 4, "Uncertainty and emotional comfort")."""

    PRACTICAL = "practical"  # "Keep this practical"
    GENTLE = "gentle"  # "Help me explore gently"
    CHALLENGE = "challenge"  # "Challenge my assumptions"


@dataclass(frozen=True)
class InterviewPreferences:
    """The person's interview preferences. Version 0: never saved (nothing chosen, not
    paused). They are preferences: never profile facts and never planning limits."""

    workspace_id: uuid.UUID
    version: int
    entry_mode: EntryMode | None
    conversation_mode: ConversationMode | None
    paused: bool
    updated_by: uuid.UUID | None
    updated_at: datetime | None


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
class ExplanationRequest:
    """The one written explanation a discovery's slate may have; its run (same ID) writes it."""

    explanation_id: uuid.UUID
    workspace_id: uuid.UUID
    discovery_id: uuid.UUID
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
