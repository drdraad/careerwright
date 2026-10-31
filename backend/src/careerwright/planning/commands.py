"""Planning input commands (Task 12a; ADR 0013 decision 11 and its amendment): read the
person's stored planning inputs with what a solve still needs, and replace them with an
expected version.

A workspace starts at version 0, nothing stated. An accepted write that changes anything
inserts `expected_version + 1` and appends a status event, in the caller's transaction; a
write against an older version is refused as stale, never merged. Every input is the person's
direct entry: no run kind and no model writes here. An answer about an option, a place held
or an outcome decision is checked against the workspace's own options when it is new or
changed; one kept unchanged from the current version stays, even if its option has gone, so
a stored answer never blocks the next write.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from careerwright.capability.commands import CapabilityData, capability_view
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import store as identity_store
from careerwright.identity.access import Actor
from careerwright.identity.records import EventKind
from careerwright.identity.workspaces import visible_workspace
from careerwright.money import Money
from careerwright.planning import store
from careerwright.planning.catalogue import Catalogue
from careerwright.planning.inputs import (
    Need,
    PlanningInputsDocument,
    PlanningInputsIn,
    SpendingCaps,
    VariantInputs,
    as_submitted,
    needs,
    refused_decision,
    stamped,
)
from careerwright.planning.pack import target_options
from careerwright.profile.commands import current_profile
from careerwright.profile.document import FieldState, MoneyField
from careerwright.vocabulary import DataMode


class WriteInputs(BaseModel):
    """Replace the whole document: every input left out is not stated."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0)
    inputs: PlanningInputsIn


@dataclass(frozen=True)
class InputsView:
    """The current inputs: version 0 (nothing stated) has no author or timestamp."""

    version: int
    document: PlanningInputsDocument
    created_by: uuid.UUID | None
    created_at: datetime | None
    profile_version: int
    caps: SpendingCaps
    needs: list[Need]
    synthetic: bool
    data_mode: DataMode


def _cap(field: MoneyField) -> Money | None:
    return field.value if field.state is FieldState.PROVIDED else None


def current_inputs(tx: Tx, workspace_id: uuid.UUID) -> InputsView:
    workspace = visible_workspace(tx, workspace_id)
    profile = current_profile(tx, workspace_id)
    caps = SpendingCaps(
        direct_spend_cap=_cap(profile.document.direct_spend_cap),
        monthly_payment_cap=_cap(profile.document.monthly_payment_cap),
    )
    stored = store.current_inputs(tx, workspace_id)
    document = stored.document if stored is not None else PlanningInputsDocument()
    return InputsView(
        version=stored.version if stored is not None else 0,
        document=document,
        created_by=stored.created_by if stored is not None else None,
        created_at=stored.created_at if stored is not None else None,
        profile_version=profile.version,
        caps=caps,
        needs=needs(document, caps),
        synthetic=workspace.synthetic,
        data_mode=workspace.data_mode,
    )


def write_inputs(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: WriteInputs,
    *,
    data: CapabilityData,
    now: datetime,
) -> tuple[InputsView, bool]:
    """The one write path. Returns the inputs and whether a version was created."""
    visible_workspace(tx, workspace_id, lock=True)
    current = current_inputs(tx, workspace_id)
    if command.expected_version != current.version:
        raise store.stale_version(current.version)
    if command.inputs == as_submitted(current.document):
        return current, False
    document = stamped(command.inputs, previous=current.document, by=actor.actor_id, at=now)
    _check_against_options(tx, workspace_id, current.document, document, data)
    created = store.insert_inputs(
        tx, workspace_id, command.expected_version + 1, document, actor.actor_id
    )
    identity_store.append_event(
        tx,
        workspace_id,
        EventKind.PLANNING_INPUTS_UPDATED,
        str(workspace_id),
        detail={"version": created.version},
    )
    return current_inputs(tx, workspace_id), True


def _invalid(field: str, reason: str) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        "That answer does not fit this workspace's options.",
        stage=ErrorStage.PLANNING,
        details={"field": field, "reason": reason},
    )


def _check_against_options(
    tx: Tx,
    workspace_id: uuid.UUID,
    previous: PlanningInputsDocument,
    document: PlanningInputsDocument,
    data: CapabilityData,
) -> None:
    """Each new or changed answer names one of the workspace's options and fits it."""
    kept = {v.variant_id: v for v in previous.variants}
    variants = [v for v in document.variants if kept.get(v.variant_id) != v]
    admissions = [a for a in document.admissions if a not in previous.admissions]
    before = {d.outcome_id: d for d in previous.outcome_decisions}
    decisions = [d for d in document.outcome_decisions if before.get(d.outcome_id) != d]
    if decisions:
        reason = refused_decision(data.outcomes, decisions)
        if reason is not None:
            raise _invalid("outcome_decisions", reason)
    if not variants and not admissions:
        return
    catalogues = [
        found.catalogue
        for matrix in capability_view(tx, workspace_id, data).matrices
        if (found := target_options(matrix, data.pack)).catalogue is not None
    ]
    for answer in variants:
        _check_variant(answer, catalogues)
    offerings = {o.offering_id: o for c in catalogues for o in c.offerings}
    for offering_id in admissions:
        offering = offerings.get(offering_id)
        if offering is None:
            raise _invalid("admissions", "not_an_option")
        if offering.application_gate is None and offering.offer_gate is None:
            raise _invalid("admissions", "nothing_to_admit")


def _check_variant(answer: VariantInputs, catalogues: list[Catalogue]) -> None:
    catalogue = next(
        (c for c in catalogues if any(v.variant_id == answer.variant_id for v in c.variants)),
        None,
    )
    if catalogue is None:
        raise _invalid("variants", "not_an_option")
    variant = next(v for v in catalogue.variants if v.variant_id == answer.variant_id)
    offering = next(o for o in catalogue.offerings if o.offering_id == variant.offering_id)
    conditions = {c.field for c in offering.eligibility_conditions}
    if set(answer.condition_statuses) - conditions:
        raise _invalid("condition_statuses", "not_a_condition")
    kinds = {i.instrument_id: i.kind for i in catalogue.instruments}
    # A scheme the catalogue names keeps its own kind: a loan never passes as a grant.
    if any(kinds.get(s.instrument_id, s.kind) is not s.kind for s in answer.supports):
        raise _invalid("supports", "not_its_kind")
