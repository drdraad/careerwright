"""API contract for interview turns: the person's message, the run, the validated proposals
and the decision on them."""

import uuid
from datetime import datetime

from pydantic import Field

from nessa.api.schemas import ProfileOut, ResponseModel, RunOut
from nessa.money import Money
from nessa.profile.conversation import TurnView
from nessa.profile.interview import (
    AnsweredState,
    InterviewProposal,
    ProfileField,
    ProposalOrigin,
    ProposedChange,
)
from nessa.profile.records import Basis, TurnDecision


class ProposedChangeOut(ResponseModel):
    change_id: str
    field: ProfileField
    state: AnsweredState
    value: Money | list[str] | float | str | None = Field(
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
    missing_critical_fields: list[ProfileField]
    ready_for_review: bool

    @classmethod
    def of(cls, proposal: InterviewProposal) -> "ProposalOut":
        return cls(
            origin=proposal.origin,
            prompt_version=proposal.prompt_version,
            profile_version=proposal.profile_version,
            reply=proposal.reply,
            changes=[ProposedChangeOut.of(c) for c in proposal.changes],
            next_question=proposal.next_question,
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


class TurnPage(ResponseModel):
    items: list[TurnOut] = Field(description="Newest first.")
    next_cursor: str | None


class DecisionResult(ResponseModel):
    """The decision and the resulting profile. The proposals are read from the turn: this
    response is stored as the command's receipt, and model output is kept sealed."""

    turn_id: uuid.UUID
    decision: DecisionOut
    profile: ProfileOut
