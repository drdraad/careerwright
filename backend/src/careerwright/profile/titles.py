"""The person's own titles as ESCO occupations (plan section 4, Sprint W SW.5; ADR 0007
decision 13): their current or last role and their target titles.

Each is what its stored record names (`careerwright.profile.targets`, decided once by one set of
rules, one record per title as a concept, so a role and a target with the same title name the
same): its occupation in ESCO itself (the person's choice, as the title itself or as the closest
to it, or the one occupation holding it as a label), else every occupation holding its title as
a label (several is ambiguous: each is kept, none is picked), else none, and it is not an ESCO
title. Nothing is guessed from the title's words: work joins a title only through the essential
skills its occupations list (`careerwright.profile.slate.skill_join_hits`).
"""

import uuid
from dataclasses import dataclass

from careerwright.catalogue import taxonomy_store
from careerwright.db import Tx
from careerwright.profile.document import ProfileDocument
from careerwright.profile.interview import ProfileField
from careerwright.profile.records import TargetLink, TargetRecord
from careerwright.profile.targets import PackTargets, role_record


@dataclass(frozen=True)
class ResolvedTitle:
    text: str  # the person's words
    field: ProfileField
    # The occupation chosen for it; else every occupation holding it as a label (several
    # is ambiguous: each is kept, none is picked); empty when it is not an ESCO title.
    occupations: tuple[uuid.UUID, ...]
    chosen: bool
    # The person said none of the ESCO occupations offered as closest is their job (its
    # record's `none_of_these`): it names none, and nothing asks them to pick another.
    declined: bool = False


def _resolved(tx: Tx, records: list[TargetRecord], field: ProfileField) -> list[ResolvedTitle]:
    uris = {u for r in records for u in (r.esco_occupation, *r.label_matches) if u is not None}
    held = taxonomy_store.concepts_by_uri(tx, uris)
    resolved: list[ResolvedTitle] = []
    for record in records:
        named = (record.esco_occupation,) if record.esco_occupation else record.label_matches
        occupations = tuple(sorted(held[uri] for uri in named if uri in held))
        chosen = record.link is TargetLink.OCCUPATION_CHOICE
        declined = record.link is TargetLink.NONE_OF_THESE
        resolved.append(
            ResolvedTitle(record.title, field, () if declined else occupations, chosen, declined)
        )
    return resolved


def role(tx: Tx, record: TargetRecord) -> ResolvedTitle:
    """The role, as its record (`careerwright.profile.targets.role_record`) names it in ESCO."""
    [resolved] = _resolved(tx, [record], ProfileField.CURRENT_ROLE)
    return resolved


def current_role(
    tx: Tx, workspace_id: uuid.UUID, document: ProfileDocument, pack: PackTargets
) -> ResolvedTitle | None:
    """The role the person gave, or None when they have not given one."""
    record = role_record(tx, workspace_id, document, pack)
    return None if record is None else role(tx, record)


def targets(tx: Tx, records: list[TargetRecord]) -> list[ResolvedTitle]:
    """Each target (`careerwright.profile.targets.stored_targets`, one per title as a
    concept), as its record names it in ESCO. The pack's crosswalk is Skills' alone. An
    occupation the held release lacks is simply absent."""
    return _resolved(tx, records, ProfileField.TARGET_TITLES)
