"""Records of the profile module."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Literal

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


class TargetKind(StrEnum):
    """What a title's words are (`careerwright.profile.targets`)."""

    ESCO = "esco"  # an ESCO occupation's title, chosen as such
    ONS = "ons"  # a title the UK job-title index lists (ONS's SOC 2020 coding index)
    OWN_WORDS = "own_words"  # the person's own words


class TargetLink(StrEnum):
    """The source of the link between a title and its ESCO occupation."""

    # The person chose the occupation: as their target, or as the closest to their title.
    OCCUPATION_CHOICE = "occupation_choice"
    EXACT_LABEL = "exact_label"  # the one occupation holding the title as a label
    PACK_CROSSWALK = "pack_crosswalk"  # the option pack's crosswalk for its target
    NONE = "none"  # none yet
    # The person said none of the ESCO occupations offered as closest is their job: none, and
    # Careerwright doesn't ask again (ADR 0015 decision 3).
    NONE_OF_THESE = "none_of_these"


# The links that are matches in ESCO itself: the slate, the sketch and the strength join work
# only to these (ADR 0007 decision 13). The pack's crosswalk seeds Skills alone.
ESCO_LINKS = frozenset({TargetLink.OCCUPATION_CHOICE, TargetLink.EXACT_LABEL})


class TargetCoverage(StrEnum):
    """How far Careerwright can cover a target: one of the option pack's targets, or not."""

    PACK_TARGET = "pack_target"
    NOT_COVERED = "not_covered"
    # Several pack targets' crosswalks name its occupation: never guessed between.
    SEVERAL_PACK_TARGETS = "several_pack_targets"


PackTargetBasis = Literal["title", "esco_crosswalk"]


@dataclass(frozen=True)
class TargetRecord:
    """A title, stored once with what it names (`careerwright.profile.targets`): a target's,
    or the person's current or last role's."""

    title: str
    key: str  # the title as a concept (`careerwright.concept_key`)
    kind: TargetKind
    occupation_uri: str | None
    link: TargetLink
    label_matches: tuple[str, ...]  # every occupation holding the title as a label, by URI
    coverage: TargetCoverage
    pack_target_id: str | None
    pack_target_basis: PackTargetBasis | None
    pack_version: str
    source_ref_id: uuid.UUID | None = None  # the choice's source
    # An ONS title's SOC 2020 unit groups and ISCO-08 groups, as the index codes it; empty
    # for any other kind.
    soc_codes: tuple[str, ...] = ()
    isco_codes: tuple[str, ...] = ()

    @property
    def esco_occupation(self) -> str | None:
        """The occupation the target names in ESCO itself (chosen, or its one label)."""
        return self.occupation_uri if self.link in ESCO_LINKS else None


class TitleUse(StrEnum):
    """Which of the person's titles details sit beside."""

    ROLE = "role"  # their current or last role
    TARGET = "target"


@dataclass(frozen=True)
class TitleDetails:
    """The person's own details beside a title, by the title as a concept: never a default
    (None: not given), ignored by matching; the marks are a display state, never evidence.
    Version 0: nothing saved yet."""

    title_use: TitleUse
    title_key: str
    version: int
    seniority: str | None = None
    industry: str | None = None
    not_part_of_job: tuple[uuid.UUID, ...] = ()  # ESCO skill IDs, in the person's order
    recorded_by: uuid.UUID | None = None
    recorded_at: datetime | None = None
