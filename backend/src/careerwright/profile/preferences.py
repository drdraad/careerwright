"""Interview preferences: how the person chose to start, the conversation mode and pause
(spec sections 3-4, S2.3; PROF-08, PROF-09).

They shape what the interviewer asks and how, and nothing else: they are never profile
facts, never planning limits and never a judgement about the person. "Not chosen" stays
distinct from any choice. Pausing keeps everything saved; while paused the web app asks
nothing and offers no way to send a message until the person resumes. The API itself does
not refuse a message while paused (ADR 0007 decision 1): pause is the person's own setting,
not a lock. Writes take an expected version, like every consequential write.
"""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import store as identity_store
from careerwright.identity.access import Actor
from careerwright.identity.records import EventKind
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import interview_store
from careerwright.profile.records import ConversationMode, EntryMode, InterviewPreferences


class SetPreferences(BaseModel):
    """The whole set of preferences; null means not chosen."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0, description="0 while nothing has been saved.")
    entry_mode: EntryMode | None
    conversation_mode: ConversationMode | None
    paused: bool


def current_preferences(tx: Tx, workspace_id: uuid.UUID) -> InterviewPreferences:
    visible_workspace(tx, workspace_id)
    stored = interview_store.preferences(tx, workspace_id)
    if stored is None:
        return InterviewPreferences(workspace_id, 0, None, None, False, None, None)
    return stored


def set_preferences(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: SetPreferences
) -> InterviewPreferences:
    visible_workspace(tx, workspace_id, lock=True)
    current = current_preferences(tx, workspace_id)
    if command.expected_version != current.version or not interview_store.write_preferences(
        tx,
        workspace_id,
        command.expected_version,
        entry_mode=command.entry_mode,
        conversation_mode=command.conversation_mode,
        paused=command.paused,
        updated_by=actor.actor_id,
    ):
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "Your interview preferences changed since you loaded them. Reload, then try again.",
            stage=ErrorStage.PROFILE,
            details={"current_version": current.version},
        )
    identity_store.append_event(
        tx,
        workspace_id,
        EventKind.INTERVIEW_PREFERENCES_UPDATED,
        str(workspace_id),
        detail={"version": command.expected_version + 1},
    )
    return current_preferences(tx, workspace_id)


def prompt_modes(preferences: InterviewPreferences) -> tuple[EntryMode | None, ConversationMode]:
    """What the interviewer is told: the entry as chosen (or not), and the mode, which is
    practical until the person chooses another."""
    return preferences.entry_mode, preferences.conversation_mode or ConversationMode.PRACTICAL
