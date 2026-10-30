"""The person's own titles as ESCO occupations (plan section 4, Sprint W SW.5; ADR 0007
decision 13): their current or last role and their target titles.

A title names the occupation the person chose for it from ESCO (an `occupation_choice`
source, by its ESCO URI); otherwise every occupation of the held release that holds it as a
label (`careerwright.concept_key`); otherwise none, and it is not an ESCO title. Nothing is
guessed from the title's words: work joins a title only through the essential skills its
occupations list (`careerwright.profile.slate.skill_join_hits`).
"""

import uuid
from dataclasses import dataclass

from careerwright.catalogue import taxonomy_store
from careerwright.db import Tx
from careerwright.profile import store
from careerwright.profile.document import FieldState, ProfileDocument
from careerwright.profile.interview import ProfileField
from careerwright.profile.records import SourceKind


@dataclass(frozen=True)
class ResolvedTitle:
    text: str  # the person's words
    field: ProfileField
    # The occupation chosen for it; else every occupation holding it as a label (several
    # is ambiguous: each is kept, none is picked); empty when it is not an ESCO title.
    occupations: tuple[uuid.UUID, ...]
    chosen: bool


def _labelled(tx: Tx, text: str) -> tuple[uuid.UUID, ...]:
    return tuple(sorted({m.concept_id for m in taxonomy_store.concept_key_matches(tx, text)}))


def current_role(
    tx: Tx, workspace_id: uuid.UUID, document: ProfileDocument
) -> ResolvedTitle | None:
    """The role the person gave, or None when they have not given one."""
    field = document.current_role
    if field.state is not FieldState.PROVIDED or field.value is None:
        return None
    found = store.source(tx, workspace_id, field.source_ref_id) if field.source_ref_id else None
    if found is not None and found.kind is SourceKind.OCCUPATION_CHOICE and found.locator:
        concept = taxonomy_store.concepts_by_uri(tx, [found.locator]).get(found.locator)
        if concept is not None:
            return ResolvedTitle(field.value, ProfileField.CURRENT_ROLE, (concept,), chosen=True)
    return ResolvedTitle(
        field.value, ProfileField.CURRENT_ROLE, _labelled(tx, field.value), chosen=False
    )


def targets(tx: Tx, workspace_id: uuid.UUID, document: ProfileDocument) -> list[ResolvedTitle]:
    """Each target title, by the occupation chosen for it (its preferred label is the
    title) or else by label. A choice from another release is simply absent."""
    field = document.target_titles
    if field.state is not FieldState.PROVIDED or not field.value:
        return []
    uris = store.chosen_occupation_uris(tx, workspace_id)
    concepts = taxonomy_store.concepts_by_uri(tx, uris)
    facts = taxonomy_store.occupation_facts(tx, concepts.values(), skills_shown=0)
    chosen = {fact.preferred_label.casefold(): concept for concept, fact in facts.items()}
    resolved: list[ResolvedTitle] = []
    for title in field.value:
        concept = chosen.get(title.casefold())
        if concept is not None:
            resolved.append(ResolvedTitle(title, ProfileField.TARGET_TITLES, (concept,), True))
        else:
            resolved.append(
                ResolvedTitle(title, ProfileField.TARGET_TITLES, _labelled(tx, title), False)
            )
    return resolved
