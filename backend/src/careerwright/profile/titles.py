"""The person's own titles as ESCO occupations (plan section 4, Sprint W SW.5; ADR 0007
decision 13): their current or last role and their target titles.

A role names the occupation the person chose for it from ESCO (an `occupation_choice`
source, by its ESCO URI); otherwise every occupation of the held release that holds it as a
label (`careerwright.concept_key`); otherwise none, and it is not an ESCO title. A target is
what its stored record names (`careerwright.profile.targets`, decided once by the same rules):
its occupation in ESCO itself, or else every occupation holding its title as a label. Nothing
is guessed from the title's words: work joins a title only through the essential skills its
occupations list (`careerwright.profile.slate.skill_join_hits`).
"""

import uuid
from dataclasses import dataclass

from careerwright.catalogue import taxonomy_store
from careerwright.db import Tx
from careerwright.profile import store
from careerwright.profile.document import FieldState, ProfileDocument
from careerwright.profile.interview import ProfileField
from careerwright.profile.records import SourceKind, TargetLink, TargetRecord


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


def targets(tx: Tx, records: list[TargetRecord]) -> list[ResolvedTitle]:
    """Each target (`careerwright.profile.targets.stored_targets`, one per title as a
    concept), as its record names it in ESCO: its occupation (chosen, or the one holding its
    title as a label), else every occupation holding its title as a label. The pack's
    crosswalk is Skills' alone. An occupation the held release lacks is simply absent."""
    uris = {u for r in records for u in (r.esco_occupation, *r.label_matches) if u is not None}
    held = taxonomy_store.concepts_by_uri(tx, uris)
    resolved: list[ResolvedTitle] = []
    for record in records:
        named = (record.esco_occupation,) if record.esco_occupation else record.label_matches
        occupations = tuple(sorted(held[uri] for uri in named if uri in held))
        chosen = record.link is TargetLink.OCCUPATION_CHOICE
        resolved.append(
            ResolvedTitle(record.title, ProfileField.TARGET_TITLES, occupations, chosen)
        )
    return resolved
