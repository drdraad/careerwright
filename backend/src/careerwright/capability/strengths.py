"""Overlooked-strength use cases (plan section 4; ADR 0014 decision 3; Sprint W SW.5): ask for
a turn's one proposal, read it, and confirm or decline it.

A proposal is asked for once per conversation turn whose decision added answers, and reads
only the answers that decision added, words no earlier version held (so declining one stores
nothing, yet the same words are not offered again on a later turn, even moved to another
field or added back); never for a turn whose message the support screen
(`careerwright.profile.safety`) answered: that turn only acknowledges and offers a smaller
step. It runs as its own bounded run (`strength_proposal`, one `RunTask` on the one
activity, so the DBOS step sequence is unchanged): live only with
the person's key and within their spend limit, which the activity checks again before any
call; a demo workspace uses the deterministic, labelled fixture model and never a provider.

Its destinations are the person's world now: each target that names one ESCO occupation and
the first slate's destinations on their horizon (`careerwright.profile.exploration`). Each
carries only the essential skills ESCO lists for it that the person has not already claimed.

The strength shows only once the person confirms it, through a command with an expected
version and an idempotency key: it is then their own claim, recorded as a self-report
(`Answer.USED`) whose example is the verified quotation. Declining records nothing about the
skill. A command's answer is kept as its receipt, so it never holds the model's proposal.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from careerwright.capability import store, strength, usual
from careerwright.capability.commands import record_checked_evidence
from careerwright.capability.evidence import Answer, SkillEvidence
from careerwright.capability.strength import (
    DestinationKind,
    DestinationSkills,
    OverlookedStrength,
    StrengthChoice,
    StrengthDecision,
    StrengthRequest,
)
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.taxonomy import held_release
from careerwright.config import RuntimeMode
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import run_store
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.records import Run, RunKind
from careerwright.identity.runs import RunRequest, open_output, submit_run
from careerwright.identity.spend import SpendLimits
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import store as profile_store
from careerwright.profile import titles
from careerwright.profile.commands import current_profile
from careerwright.profile.conversation import visible_turn
from careerwright.profile.discovery import EvidenceItem, evidence_of
from careerwright.profile.exploration import HardFilterInput, first_slate
from careerwright.profile.safety import has_risk_stem
from careerwright.profile.store import stale_version
from careerwright.profile.targets import stored_targets
from careerwright.vocabulary import WorkState


class SubmitStrength(BaseModel):
    """Ask for the one strength proposal of a turn whose decision added answers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_profile_version: int = Field(ge=0)


class DecideStrength(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0, description="The capability version shown.")
    confirm: bool = Field(
        description="True: it is the person's own claim, recorded as self-reported. False: "
        "declined, and nothing about the skill is recorded."
    )


@dataclass(frozen=True)
class StrengthView:
    request: StrengthRequest
    run: Run
    proposal: OverlookedStrength | None  # only once the run is complete
    decision: StrengthDecision | None


def _refusal(code: ErrorCode, message: str, reason: str) -> CareerwrightError:
    return CareerwrightError(code, message, stage=ErrorStage.CAPABILITY, details={"reason": reason})


def _view(tx: Tx, keyring: Keyring, request: StrengthRequest) -> StrengthView:
    run = run_store.run(tx, request.strength_id)
    if run is None:  # the run and its link are written together; never show half of one
        raise CareerwrightError(
            ErrorCode.INTERNAL_ERROR, "The strength has no run.", stage=ErrorStage.CAPABILITY
        )
    proposal = None
    if run.kind is RunKind.STRENGTH_PROPOSAL and run.status is WorkState.COMPLETE:
        plaintext = open_output(tx, keyring, run)
        if plaintext is None:  # a complete run stored its output; "none found" is an output
            raise CareerwrightError(
                ErrorCode.INTERNAL_ERROR,
                "The strength's run is complete but its output is missing.",
                stage=ErrorStage.CAPABILITY,
            )
        proposal = OverlookedStrength.model_validate_json(plaintext)
    return StrengthView(request, run, proposal, store.strength_decision(tx, request.strength_id))


def turn_strength(
    tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, turn_id: uuid.UUID
) -> StrengthView:
    visible_workspace(tx, workspace_id)
    request = store.strength_for_turn(tx, workspace_id, turn_id)
    if request is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND,
            "No strength was asked for on this turn.",
            stage=ErrorStage.CAPABILITY,
        )
    return _view(tx, keyring, request)


def _words(text: str) -> str:
    return " ".join(text.casefold().split())


def _added_answers(tx: Tx, workspace_id: uuid.UUID, version: int) -> list[EvidenceItem]:
    """The answers about work (what the person enjoys, can do or has done) that the profile
    version a turn's decision created added: answers whose words no earlier version held in
    any of those fields (case and spacing aside). An answer kept or removed, moved between
    those fields, or removed and added back is not added, so a strength declined for it is
    not offered again."""
    after = profile_store.profile_version(tx, workspace_id, version)
    if after is None:
        return []
    earlier = {
        _words(item.text)
        for past in profile_store.list_profile_versions(
            tx, workspace_id, before=version, limit=version
        )
        for item in evidence_of(past.document)
        if item.field in strength.ANSWER_FIELDS
    }
    return [
        item
        for item in evidence_of(after.document)
        if item.field in strength.ANSWER_FIELDS and _words(item.text) not in earlier
    ]


def _destinations(
    tx: Tx, workspace_id: uuid.UUID, hard: HardFilterInput, claimed: set[str]
) -> list[DestinationSkills]:
    """The person's targets that name one ESCO occupation, then the first slate's
    destinations, each with its essential skills not yet claimed (ESCO's order)."""
    profile = current_profile(tx, workspace_id)
    found: dict[uuid.UUID, DestinationKind] = {}
    for target in titles.targets(tx, stored_targets(tx, workspace_id, profile.document)):
        if len(target.occupations) == 1:
            found.setdefault(target.occupations[0], DestinationKind.TARGET)
    for suggestion in first_slate(tx, workspace_id, hard).suggestions:
        found.setdefault(suggestion.candidate.occupation.concept_id, DestinationKind.HORIZON)
    destinations: list[DestinationSkills] = []
    for concept_id, kind in found.items():
        detail = taxonomy_store.occupation(tx, concept_id)
        if detail is None:
            continue
        skills = [
            s for s in usual.essential_skills(detail) if usual.subject_of(s.skill_id) not in claimed
        ]
        if skills:
            destinations.append(DestinationSkills(concept_id, detail.preferred_label, kind, skills))
    return destinations


def submit_strength(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    turn_id: uuid.UUID,
    command: SubmitStrength,
    *,
    models: ModelChoice,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
    hard: HardFilterInput,
) -> tuple[StrengthView, bool]:
    """The turn's one strength run, and whether this request started it: asking again
    answers with the run already asked for, in whatever state. The run reads only the
    answers the turn's decision added, so a strength declined on an earlier turn is not
    proposed again from the same words. Refused before any run exists when the turn's
    decision added no answers, when the support screen answered its message, when the
    answers it added are no longer the current ones, when none of them can be quoted, when
    the person has no destination with an unclaimed essential skill, and for the usual
    reasons any run is refused (no key, over budget)."""
    visible_workspace(tx, workspace_id, lock=True)
    existing = store.strength_for_turn(tx, workspace_id, turn_id)
    if existing is not None:
        return _view(tx, keyring, existing), False
    turn = visible_turn(tx, keyring, workspace_id, turn_id)
    created = turn.decision.profile_version if turn.decision else None
    added = [] if created is None else _added_answers(tx, workspace_id, created)
    if created is None or not added:
        raise _refusal(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "Only a turn that saved something you enjoy, can do or have done can show a strength.",
            "no_new_answers",
        )
    if has_risk_stem(turn.turn.message):  # recomputed from the message, never stored
        raise _refusal(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "Careerwright doesn't look for strengths on this turn.",
            "held_back",
        )
    profile = current_profile(tx, workspace_id)
    if command.expected_profile_version != profile.version:
        raise stale_version(profile.version)
    if created != profile.version:
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "Your answers changed after this turn. A later turn can show a strength.",
            stage=ErrorStage.CAPABILITY,
            details={"current_version": profile.version, "turn_version": created},
        )
    answers = strength.quotable_answers(added)
    if not answers:
        raise _refusal(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "What this turn saved has no words a strength could quote: a strength quotes your "
            "own words about your work.",
            "no_quotable_answer",
        )
    claimed = {e.subject for e in store.evidence(tx, workspace_id) if e.answer in usual.SAID_DONE}
    destinations = _destinations(tx, workspace_id, hard, claimed)
    if not destinations:
        raise _refusal(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "Choose a target or answer what you do now first: a strength is shown against a "
            "destination.",
            "no_destinations",
        )
    context = strength.build_input(
        turn_id=turn_id,
        profile_version=profile.version,
        release=held_release(tx).dataset_id,
        answers=answers,
        destinations=destinations,
    )
    run = submit_run(
        tx,
        actor,
        workspace_id,
        RunRequest(
            RunKind.STRENGTH_PROPOSAL,
            strength.worst_case_nano_usd,
            profile_version=profile.version,
            input=context.model_dump_json().encode(),
        ),
        models=models,
        keyring=keyring,
        runtime_mode=runtime_mode,
        defaults=defaults,
        now=now,
    )
    request = StrengthRequest(run.run_id, workspace_id, turn_id, actor.actor_id, now)
    store.insert_strength(tx, request)
    return StrengthView(request, run, None, None), True


def decide_strength(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    turn_id: uuid.UUID,
    command: DecideStrength,
    *,
    keyring: Keyring,
    now: datetime,
) -> tuple[StrengthDecision, int]:
    """Confirm or decline the turn's proposed strength, once. Confirmed, it is recorded as
    the person's own claim about the skill (self-reported, no level) with the verified
    quotation as its example, as the next capability version. Returns the decision and the
    capability version."""
    visible_workspace(tx, workspace_id, lock=True)
    view = turn_strength(tx, keyring, workspace_id, turn_id)
    if view.decision is not None:
        raise _refusal(ErrorCode.ALREADY_DECIDED, "This strength was already decided.", "decided")
    proposed = view.proposal.strength if view.proposal else None
    if proposed is None:
        raise CareerwrightError(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "There is no proposed strength to decide.",
            stage=ErrorStage.CAPABILITY,
            details={
                "run_status": view.run.status.value,
                "failure_class": view.run.failure_class or "",
            },
        )
    evidence_id: uuid.UUID | None = None
    if command.confirm:
        claim = SkillEvidence(
            evidence_id=uuid.uuid4(),
            subject=usual.subject_of(proposed.skill.skill_id),
            answer=Answer.USED,
            self_assessed_level=None,
            example=proposed.quotation.text,
            recorded_by=actor.actor_id,
            recorded_at=now,
        )
        version = record_checked_evidence(
            tx, actor, workspace_id, command.expected_version, claim
        ).version
        evidence_id = claim.evidence_id
    else:
        version = store.state(tx, workspace_id).version
        if command.expected_version != version:
            raise CareerwrightError(
                ErrorCode.STALE_INPUT_VERSION,
                "Your skills and evidence changed since you loaded them. Reload, then try again.",
                stage=ErrorStage.CAPABILITY,
                details={"current_version": version},
            )
    decided = StrengthDecision(
        strength_id=view.request.strength_id,
        workspace_id=workspace_id,
        decision=StrengthChoice.CONFIRMED if command.confirm else StrengthChoice.DECLINED,
        evidence_id=evidence_id,
        decided_by=actor.actor_id,
        decided_at=now,
    )
    if not store.insert_strength_decision(tx, decided):
        raise _refusal(ErrorCode.ALREADY_DECIDED, "This strength was already decided.", "decided")
    return decided, version
