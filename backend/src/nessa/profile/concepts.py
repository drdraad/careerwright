"""Provisional occupation concepts: titles a person verified that ESCO does not hold
(spec section 4, DIV-1: "Verified user-supplied titles absent from ESCO remain provisional
internal concepts, not fabricated ESCO records"; DIV1-03).

The person's explicit confirmation is the verification, recorded as a direct-entry source.
A title that is an ESCO label (preferred, alternative or hidden) as a concept, with case,
punctuation, hyphens and simple plurals folded (`nessa.concept_key`), is refused with the
matching occupations; the database trigger applies the same rule to the title itself. A
title that only resembles an ESCO label ("senior data analyst") is not refused: offering
the person the full-text matches first is discovery's work (DIV1-05, T6). Model-suggested
titles are not accepted here: they stay search hypotheses until corroborated by
independent evidence (DIV1-04, Sprint 2 discovery).
"""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from nessa.catalogue import taxonomy_store
from nessa.catalogue.esco import normalise_label
from nessa.catalogue.records import ProvisionalConcept
from nessa.catalogue.taxonomy import held_release
from nessa.db import Tx
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity import store as identity_store
from nessa.identity.access import Actor
from nessa.identity.records import EventKind
from nessa.identity.workspaces import visible_workspace
from nessa.profile import store
from nessa.profile.records import SourceKind

SOURCE_LABEL = "A title you confirmed that ESCO does not list"

ConceptTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]


class RegisterProvisionalConcept(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: ConceptTitle


def register_provisional_concept(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: RegisterProvisionalConcept,
    now: datetime,
) -> tuple[ProvisionalConcept, bool]:
    """Returns the concept and whether it was created; the same title again returns the
    first one (compared case- and space-insensitively)."""
    visible_workspace(tx, workspace_id, lock=True)
    held_release(tx)  # without the taxonomy, "not in ESCO" cannot be established
    normalised = normalise_label(command.title)
    in_esco = taxonomy_store.concept_key_matches(tx, command.title)
    if in_esco:
        raise NessaError(
            ErrorCode.VALIDATION_FAILED,
            "ESCO already lists this title: choose its occupation instead.",
            stage=ErrorStage.CATALOGUE,
            details={
                "field": "title",
                "reason": "in_taxonomy",
                "concept_ids": sorted({str(m.concept_id) for m in in_esco}),
            },
        )
    existing = taxonomy_store.provisional_by_title(tx, workspace_id, normalised)
    if existing is not None:
        return existing, False
    source_id = uuid.uuid4()
    store.insert_source(
        tx,
        source_ref_id=source_id,
        workspace_id=workspace_id,
        kind=SourceKind.DIRECT_ENTRY,
        label=SOURCE_LABEL,
        recorded_by=actor.actor_id,
        observed_at=now,
    )
    created = taxonomy_store.insert_provisional(
        tx,
        concept_id=uuid.uuid4(),
        workspace_id=workspace_id,
        title=command.title,
        normalised_title=normalised,
        source_ref_id=source_id,
        created_by=actor.actor_id,
    )
    if created is None:  # cannot happen under the workspace lock; never report a phantom
        raise NessaError(
            ErrorCode.INTERNAL_ERROR, "The concept was not recorded.", stage=ErrorStage.CATALOGUE
        )
    identity_store.append_event(
        tx, workspace_id, EventKind.PROVISIONAL_CONCEPT_CREATED, str(created.concept_id)
    )
    return created, True
