"""Interview turns: the person's message becomes a durable model run whose validated
proposals the person then accepts, confirms or rejects (spec section 4, S2.2).

Submitting a turn names the profile version the person was looking at; a stale one is
refused. The turn's run pins that version and seals the minimum context the model needs.
Deciding on a turn applies only proposals from a complete, validated output, only against
the version they were made for, and only through the same command as a direct edit. Hard
constraints need the person's explicit confirmation, field by field. Every refusal leaves
the profile exactly as it was.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from careerwright.config import RuntimeMode
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import run_store
from careerwright.identity import store as identity_store
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.records import EventKind, Run, RunKind
from careerwright.identity.runs import RunRequest, open_output, submit_run
from careerwright.identity.spend import SpendLimits
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import interview, interview_store
from careerwright.profile.commands import (
    DIRECT_ENTRY_LABEL,
    FieldUpdate,
    NewSource,
    ProfileView,
    commit_profile_version,
    current_profile,
)
from careerwright.profile.document import FieldInput, checked_input, input_type
from careerwright.profile.interview import (
    HISTORY_MESSAGES,
    MAX_MESSAGE,
    MAX_PROMPT_BYTES,
    ContextMessage,
    InterviewProposal,
    ProfileField,
    TurnInput,
)
from careerwright.profile.preferences import current_preferences, prompt_modes
from careerwright.profile.records import (
    Basis,
    InterviewPreferences,
    InterviewTurn,
    SourceKind,
    TurnDecision,
)
from careerwright.profile.store import stale_version
from careerwright.vocabulary import WorkState

STATED_LABEL = "Your message, confirmed in review"
INFERRED_LABEL = "Inferred from your message, confirmed in review"

Message = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE)
]


class SubmitTurn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_profile_version: int = Field(ge=0)
    message: Message


class DecideTurn(BaseModel):
    """Which proposals to apply. A hard-constraint field is applied only if it is also named
    in `confirm_hard_constraints`; proposals not accepted are recorded as rejected."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0)
    accept: list[str] = Field(default_factory=list, max_length=len(ProfileField))
    confirm_hard_constraints: list[ProfileField] = Field(
        default_factory=list, max_length=len(ProfileField)
    )
    edits: list["FieldEdit"] = Field(
        default_factory=list,
        max_length=len(ProfileField),
        description=(
            "The person's own answers for fields this turn proposed, saved instead of those "
            "proposals (as direct entries) in the same version as the accepted ones."
        ),
    )


class FieldEdit(BaseModel):
    """The person's own answer for a field a proposal named. Typing it is their explicit
    choice, as in a direct edit, so a limit edited here needs no separate confirmation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: ProfileField
    answer: FieldInput


DecideTurn.model_rebuild()


@dataclass(frozen=True)
class TurnView:
    turn: InterviewTurn
    run: Run
    proposal: InterviewProposal | None  # only once the run is complete
    decision: TurnDecision | None


def proposal_of(tx: Tx, keyring: Keyring, run: Run) -> InterviewProposal | None:
    if run.kind is not RunKind.INTERVIEW_TURN or run.status is not WorkState.COMPLETE:
        return None
    plaintext = open_output(tx, keyring, run)
    return None if plaintext is None else InterviewProposal.model_validate_json(plaintext)


def turn_view(tx: Tx, keyring: Keyring, turn: InterviewTurn) -> TurnView:
    run = run_store.run(tx, turn.turn_id)
    if run is None:  # the run and its turn are written together; never show half a turn
        raise CareerwrightError(
            ErrorCode.INTERNAL_ERROR, "The turn has no run.", stage=ErrorStage.PROFILE
        )
    return TurnView(
        turn, run, proposal_of(tx, keyring, run), interview_store.decision(tx, turn.turn_id)
    )


def visible_turn(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, turn_id: uuid.UUID) -> TurnView:
    visible_workspace(tx, workspace_id)
    found = interview_store.turn(tx, workspace_id, turn_id)
    if found is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such interview turn.", stage=ErrorStage.PROFILE
        )
    return turn_view(tx, keyring, found)


def _context(
    tx: Tx,
    keyring: Keyring,
    profile: ProfileView,
    message_id: uuid.UUID,
    text: str,
    now: datetime,
    preferences: InterviewPreferences,
) -> TurnInput:
    """The current message and as many earlier ones (with Careerwright's replies) as fit the
    prompt budget, newest kept first."""
    earlier = list(
        reversed(
            interview_store.turns(tx, profile.workspace_id, before=None, limit=HISTORY_MESSAGES - 1)
        )
    )
    replies: dict[uuid.UUID, str] = {}
    for past in earlier:
        run = run_store.run(tx, past.turn_id)
        proposal = None if run is None else proposal_of(tx, keyring, run)
        if proposal is not None:
            replies[past.message_id] = proposal.reply
    subset = interview.context_profile(profile.document)
    entry_mode, conversation_mode = prompt_modes(preferences)
    current = (message_id, text, now)
    for start in range(len(earlier) + 1):
        kept = [(t.message_id, t.message, t.created_at) for t in earlier[start:]] + [current]
        messages = [
            ContextMessage(ref=f"m{i}", message_id=mid, text=body, sent_at=at)
            for i, (mid, body, at) in enumerate(kept, start=1)
        ]
        context = TurnInput(
            profile_version=profile.version,
            profile=subset,
            messages=messages,
            replies={m.ref: replies[m.message_id] for m in messages if m.message_id in replies},
            entry_mode=entry_mode,
            conversation_mode=conversation_mode,
        )
        if interview.prompt_bytes(context) <= MAX_PROMPT_BYTES:
            return context
    raise CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        "That message is too long to send. Shorten it and try again.",
        stage=ErrorStage.PROFILE,
        details={"field": "message", "reason": "too_long"},
    )


def submit_turn(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: SubmitTurn,
    *,
    models: ModelChoice,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
) -> TurnView:
    """A new turn and its run. Every message is sent, one with a risk stem included: the
    support flow (`careerwright.profile.safety`) is derived from the message where it is needed,
    by the API for the panel and by the interviewer's instructions, and never stored."""
    visible_workspace(tx, workspace_id, lock=True)
    profile = current_profile(tx, workspace_id)
    if command.expected_profile_version != profile.version:
        raise stale_version(profile.version)
    message_id = uuid.uuid4()
    context = _context(
        tx,
        keyring,
        profile,
        message_id,
        command.message,
        now,
        current_preferences(tx, workspace_id),
    )
    run = submit_run(
        tx,
        actor,
        workspace_id,
        RunRequest(
            RunKind.INTERVIEW_TURN,
            interview.worst_case_nano_usd,
            profile_version=profile.version,
            input=context.model_dump_json().encode(),
        ),
        models=models,
        keyring=keyring,
        runtime_mode=runtime_mode,
        defaults=defaults,
        now=now,
    )
    turn = InterviewTurn(
        turn_id=run.run_id,
        workspace_id=workspace_id,
        message_id=message_id,
        message=command.message,
        profile_version=profile.version,
        created_by=actor.actor_id,
        created_at=now,
    )
    interview_store.insert_turn(tx, turn)
    return TurnView(turn, run, None, None)


def _refusal(code: ErrorCode, message: str, **details: str | int | list[str]) -> CareerwrightError:
    return CareerwrightError(code, message, stage=ErrorStage.PROFILE, details=details)


def _checked_edits(
    edits: list[FieldEdit], proposed: set[ProfileField], accepted: set[ProfileField]
) -> dict[ProfileField, FieldInput]:
    """Each edit's answer, checked as a direct edit of its field would be. An edit replaces
    a proposal of this turn, so it names a proposed field, once, and one not also accepted."""
    checked: dict[ProfileField, FieldInput] = {}
    for edit in edits:
        name = edit.field.value
        reason = (
            "not_proposed"
            if edit.field not in proposed
            else "accepted_and_edited"
            if edit.field in accepted
            else "edited_twice"
            if edit.field in checked
            else None
        )
        if reason is not None:
            raise _refusal(
                ErrorCode.VALIDATION_FAILED,
                "Edit only a field this message proposed, once, instead of accepting it.",
                field=name,
                reason=reason,
            )
        try:
            answer = input_type(name).model_validate(edit.answer.model_dump())
        except ValidationError:
            raise _refusal(
                ErrorCode.VALIDATION_FAILED,
                "That answer doesn't fit this field.",
                field=name,
                reason="invalid_answer",
            ) from None
        checked[edit.field] = checked_input(name, answer)
    return checked


def decide_turn(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    turn_id: uuid.UUID,
    command: DecideTurn,
    *,
    keyring: Keyring,
    now: datetime,
) -> tuple[TurnDecision, ProfileView]:
    """Apply the accepted proposals (as one new profile version, if any changes anything)
    and record the decision. Returns the decision and the resulting profile."""
    visible_workspace(tx, workspace_id, lock=True)
    view = visible_turn(tx, keyring, workspace_id, turn_id)
    if view.decision is not None:
        raise _refusal(ErrorCode.ALREADY_DECIDED, "This turn's proposals were already decided.")
    if view.proposal is None:
        raise _refusal(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "This turn has no validated proposals to apply.",
            run_status=view.run.status.value,
            failure_class=view.run.failure_class or "",
        )
    profile = current_profile(tx, workspace_id)
    if command.expected_version != profile.version:
        raise stale_version(profile.version)
    if view.turn.profile_version != profile.version:
        # The proposals were validated against an older profile: never applied to a newer one.
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "The profile changed after this message was sent. Review the latest version and "
            "send the message again.",
            stage=ErrorStage.PROFILE,
            details={
                "current_version": profile.version,
                "proposal_version": view.turn.profile_version,
            },
        )
    changes = {change.change_id: change for change in view.proposal.changes}
    accepted = list(dict.fromkeys(command.accept))
    confirmed = list(dict.fromkeys(command.confirm_hard_constraints))
    unknown = [change_id for change_id in accepted if change_id not in changes]
    if unknown:
        raise _refusal(
            ErrorCode.VALIDATION_FAILED,
            "Accept only proposals this turn made.",
            field="accept",
            reason="unknown_change",
            change_ids=unknown,
        )
    accepted_fields = {changes[c].field for c in accepted}
    unconfirmed = sorted(
        changes[c].field.value
        for c in accepted
        if changes[c].hard_constraint and changes[c].field not in confirmed
    )
    if unconfirmed:
        raise _refusal(
            ErrorCode.CONFIRMATION_REQUIRED,
            "Confirm each limit or target explicitly before it is saved.",
            fields=unconfirmed,
        )
    stray = sorted(field.value for field in confirmed if field not in accepted_fields)
    if stray:
        raise _refusal(
            ErrorCode.VALIDATION_FAILED,
            "Confirm only proposals you accept.",
            field="confirm_hard_constraints",
            reason="not_accepted",
            fields=stray,
        )
    edited = _checked_edits(command.edits, {c.field for c in changes.values()}, accepted_fields)
    cited = {m for c in accepted for m in changes[c].message_ids}
    sent_at = interview_store.message_times(tx, workspace_id, cited)
    if set(sent_at) != cited:  # a proposal's messages are this workspace's, by construction
        raise CareerwrightError(
            ErrorCode.INTERNAL_ERROR,
            "A proposal cites an unknown message.",
            stage=ErrorStage.PROFILE,
        )
    updates = {}
    for change_id in accepted:
        change = changes[change_id]
        updates[change.field.value] = FieldUpdate(
            change.field_input(),
            NewSource(
                source_ref_id=uuid.uuid4(),
                kind=SourceKind.CONVERSATION,
                label=STATED_LABEL if change.basis is Basis.STATED else INFERRED_LABEL,
                observed_at=max(sent_at[m] for m in change.message_ids),
                recorded_by=actor.actor_id,
                run_id=view.run.run_id,
                message_ids=tuple(change.message_ids),
                basis=change.basis,
            ),
        )
    entry = NewSource(
        source_ref_id=uuid.uuid4(),
        kind=SourceKind.DIRECT_ENTRY,
        label=DIRECT_ENTRY_LABEL,
        observed_at=now,
        recorded_by=actor.actor_id,
    )
    for field, answer in edited.items():
        updates[field.value] = FieldUpdate(answer, entry)
    result, changed = commit_profile_version(
        tx, actor, workspace_id, command.expected_version, updates
    )
    decided = TurnDecision(
        turn_id=turn_id,
        decided_by=actor.actor_id,
        decided_at=now,
        accepted_change_ids=tuple(accepted),
        rejected_change_ids=tuple(c for c in changes if c not in accepted),
        confirmed_hard_constraints=tuple(field.value for field in confirmed),
        profile_version=result.version if changed else None,
    )
    if not interview_store.insert_decision(tx, workspace_id, decided):
        raise _refusal(ErrorCode.ALREADY_DECIDED, "This turn's proposals were already decided.")
    identity_store.append_event(
        tx,
        workspace_id,
        EventKind.INTERVIEW_TURN_DECIDED,
        str(turn_id),
        detail={"accepted": len(accepted), "version": result.version},
    )
    return decided, result
