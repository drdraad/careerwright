"""API contract for interview turns: the person's message, the run, the validated proposals
and the decision on them."""

import uuid
from datetime import datetime

from pydantic import Field

from careerwright.api.envelope import ErrorEnvelope
from careerwright.api.schemas import ProfileOut, ResponseModel, RunOut
from careerwright.identity.records import PartialCompleteness, PartialReply
from careerwright.money import Money
from careerwright.profile import safety
from careerwright.profile.conversation import TurnView
from careerwright.profile.document import SalaryFloor
from careerwright.profile.fixture_interviewer import asked_field
from careerwright.profile.interview import (
    AnsweredState,
    InterviewProposal,
    ProfileField,
    ProposalOrigin,
    ProposedChange,
)
from careerwright.profile.records import (
    Basis,
    ConversationMode,
    EntryMode,
    InterviewPreferences,
    TurnDecision,
)


class ProposedChangeOut(ResponseModel):
    change_id: str
    field: ProfileField
    state: AnsweredState
    value: SalaryFloor | Money | list[str] | float | str | None = Field(
        description=(
            "The proposed answer, typed as the field's input; null unless provided. A list is "
            "the complete list after the change: accepting it replaces the field's list."
        )
    )
    basis: Basis = Field(
        description=(
            "stated: the value appears in the cited messages (checked by the server); "
            "inferred: implied, or not found in them."
        )
    )
    message_ids: list[uuid.UUID] = Field(description="The person's messages it rests on.")
    reason: str
    hard_constraint: bool = Field(
        description="A limit or target: applied only if named in confirm_hard_constraints."
    )

    @classmethod
    def of(cls, change: ProposedChange) -> "ProposedChangeOut":
        return cls(
            change_id=change.change_id,
            field=change.field,
            state=change.state,
            value=change.value,
            basis=change.basis,
            message_ids=list(change.message_ids),
            reason=change.reason,
            hard_constraint=change.hard_constraint,
        )


class PartialReplyOut(ResponseModel):
    """The turn's reply as it streams: unvalidated text, never a proposal. The turn's run
    state and, once complete, its proposal are authoritative."""

    turn_id: uuid.UUID
    completeness: PartialCompleteness = Field(
        description=(
            "none: no text yet; streaming: the reply so far; stopped: this attempt's reply "
            "stopped, but the run goes on and may stream again or still be superseded (not "
            "final); incomplete: final, the run ended without a validated output; "
            "superseded: a validated output is stored, so read the proposal's reply once "
            "the run is complete."
        )
    )
    seq: int | None = Field(description="Matches the run.partial_updated event that announced it.")
    text: str | None = Field(description="The reply so far; null when none or superseded.")
    updated_at: datetime | None = Field(description="When the text was last written (freshness).")

    @classmethod
    def of(cls, turn_id: uuid.UUID, partial: PartialReply) -> "PartialReplyOut":
        return cls(
            turn_id=turn_id,
            completeness=partial.completeness,
            seq=partial.seq,
            text=partial.text,
            updated_at=partial.updated_at,
        )


class ProposalOut(ResponseModel):
    """A complete, validated interview output. Nothing in it is saved until decided."""

    origin: ProposalOrigin = Field(
        description="fixture: the deterministic demo interviewer (synthetic), never a live model."
    )
    prompt_version: str
    profile_version: int = Field(description="The profile version the proposals were made for.")
    reply: str
    changes: list[ProposedChangeOut]
    next_question: str | None
    asks_about: ProfileField | None = Field(
        description="The field the demo interviewer's next question asks about, so the web can "
        "offer its one-tap example replies; null for a model's question, which is never "
        "classified, and when there is no question."
    )
    missing_critical_fields: list[ProfileField]
    ready_for_review: bool

    @classmethod
    def of(cls, proposal: InterviewProposal) -> "ProposalOut":
        fixture = proposal.origin is ProposalOrigin.FIXTURE
        return cls(
            origin=proposal.origin,
            prompt_version=proposal.prompt_version,
            profile_version=proposal.profile_version,
            reply=proposal.reply,
            changes=[ProposedChangeOut.of(c) for c in proposal.changes],
            next_question=proposal.next_question,
            asks_about=asked_field(proposal.next_question) if fixture else None,
            missing_critical_fields=proposal.missing_critical_fields,
            ready_for_review=proposal.ready_for_review,
        )


class DecisionOut(ResponseModel):
    decided_by: uuid.UUID
    decided_at: datetime
    accepted_change_ids: list[str]
    rejected_change_ids: list[str]
    confirmed_hard_constraints: list[ProfileField]
    profile_version: int | None = Field(
        description="The profile version the decision created; null when it changed nothing."
    )

    @classmethod
    def of(cls, decision: TurnDecision) -> "DecisionOut":
        return cls(
            decided_by=decision.decided_by,
            decided_at=decision.decided_at,
            accepted_change_ids=list(decision.accepted_change_ids),
            rejected_change_ids=list(decision.rejected_change_ids),
            confirmed_hard_constraints=[
                ProfileField(f) for f in decision.confirmed_hard_constraints
            ],
            profile_version=decision.profile_version,
        )


class TurnOut(ResponseModel):
    """One interview turn. `run` is authoritative for its state: `proposal` exists only when
    the run is complete, and a failed run's failure class says why there is none."""

    turn_id: uuid.UUID
    message_id: uuid.UUID
    message: str
    profile_version: int = Field(description="The profile version the message was sent with.")
    created_at: datetime
    run: RunOut
    proposal: ProposalOut | None
    decision: DecisionOut | None

    @classmethod
    def of(cls, view: TurnView, run: RunOut) -> "TurnOut":
        return cls(
            turn_id=view.turn.turn_id,
            message_id=view.turn.message_id,
            message=view.turn.message,
            profile_version=view.turn.profile_version,
            created_at=view.turn.created_at,
            run=run,
            proposal=ProposalOut.of(view.proposal) if view.proposal else None,
            decision=DecisionOut.of(view.decision) if view.decision else None,
        )


class SupportResourceOut(ResponseModel):
    name: str
    contact: str
    when: str
    source_url: str
    checked_on: str = Field(description="When the service's own page was last checked.")


class SupportNoteOut(ResponseModel):
    """The support panel, shown beside a message that triggers the support screen
    (`careerwright.profile.safety`), whether the send was accepted or refused, and beside the
    first question's title field when what is typed there triggers it. Kept apart from career
    suitability. Derived from the request on every response, a replay included; never
    stored, not even in the idempotency receipt."""

    policy_version: str
    review_status: str = Field(description="How far the policy is reviewed (gate H-12).")
    message: str = Field(
        description="Says whether the message was sent, or that a title was not kept as the role."
    )
    resources: list[SupportResourceOut]

    @classmethod
    def current(cls, *, sent: bool) -> "SupportNoteOut":
        return cls._saying(safety.SUPPORT_NOTE if sent else safety.SUPPORT_NOTE_NOT_SENT)

    @classmethod
    def beside_a_title(cls) -> "SupportNoteOut":
        """Beside the first question's title field: the title is not kept as the role."""
        return cls._saying(safety.SUPPORT_NOTE_TITLE)

    @classmethod
    def _saying(cls, message: str) -> "SupportNoteOut":
        return cls(
            policy_version=safety.POLICY_VERSION,
            review_status=safety.REVIEW_STATUS,
            message=message,
            resources=[
                SupportResourceOut(
                    name=r.name,
                    contact=r.contact,
                    when=r.when,
                    source_url=r.source_url,
                    checked_on=r.checked_on,
                )
                for r in safety.SUPPORT_RESOURCES
            ],
        )


class TurnSubmittedOut(TurnOut):
    """A new turn, with the support panel when its message holds a risk stem."""

    support_note: SupportNoteOut | None

    @classmethod
    def sent(cls, turn: TurnOut, *, support: bool) -> "TurnSubmittedOut":
        note = SupportNoteOut.current(sent=True) if support else None
        return cls(**turn.model_dump(), support_note=note)


class TurnRefusedOut(ErrorEnvelope):
    """A refused send. When its message triggers the support screen, the panel comes with
    the refusal, since the message was screened before anything could refuse it."""

    support_note: SupportNoteOut | None = None


class PreferencesOut(ResponseModel):
    """How the person chose to start and to be interviewed, and whether it is paused. Null:
    not chosen yet (the interviewer then keeps to the practical mode)."""

    version: int = Field(description="0 while nothing has been saved.")
    entry_mode: EntryMode | None
    conversation_mode: ConversationMode | None
    paused: bool
    updated_at: datetime | None

    @classmethod
    def of(cls, preferences: InterviewPreferences) -> "PreferencesOut":
        return cls(
            version=preferences.version,
            entry_mode=preferences.entry_mode,
            conversation_mode=preferences.conversation_mode,
            paused=preferences.paused,
            updated_at=preferences.updated_at,
        )


class TurnPage(ResponseModel):
    items: list[TurnOut] = Field(description="Newest first.")
    next_cursor: str | None


class DecisionResult(ResponseModel):
    """The decision and the resulting profile. The proposals are read from the turn: this
    response is stored as the command's receipt, and model output is kept sealed."""

    turn_id: uuid.UUID
    decision: DecisionOut
    profile: ProfileOut
