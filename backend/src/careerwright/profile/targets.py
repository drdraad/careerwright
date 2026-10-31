"""Each target is stored once (Task 6d slice A; ADR 0015 decision 3; ADR 0012 and ADR 0007 as
amended on 2026-10-31; the audit's code appendix, finding F5).

When a target is chosen or saved, `resolve_target` decides once what it names, by one set of
rules, and the record is stored with it (`target_records`, migration 0034). The slate, the
sketch, the strength, Skills and the world read that record instead of resolving the title
again, so they can't disagree about the same target.

The rules, in order. A title is compared as a concept (`careerwright.concept_key`: "&" read as
"and", accents, case, punctuation, hyphens and simple plurals folded), and nothing is guessed:
1. the occupation the person chose for it (an `occupation_choice` source, by its ESCO URI),
   or an earlier choice of the workspace whose ESCO title is the title as a concept;
2. otherwise the one occupation holding the title as a label (hidden labels included);
   several stay several, each kept, none picked: the person chooses which they mean;
3. otherwise, for a title that is one of the option pack's targets, the occupation its
   crosswalk names;
4. otherwise none yet.
Its coverage is the option pack's target with the same title, or else the one pack target
whose crosswalk names its occupation; several such targets are never guessed between.
"""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from careerwright.catalogue import taxonomy_store
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import store
from careerwright.profile.document import FieldState, ProfileDocument
from careerwright.profile.records import (
    PackTargetBasis,
    TargetCoverage,
    TargetKind,
    TargetLink,
    TargetRecord,
)


@dataclass(frozen=True)
class PackTarget:
    target_id: str
    title: str
    esco_uri: str | None  # the occupation its crosswalk names


@dataclass(frozen=True)
class PackTargets:
    """The option pack's targets as the capability model loads them."""

    version: str
    targets: tuple[PackTarget, ...]


@dataclass(frozen=True)
class Choice:
    """An occupation the person chose for a title, by its ESCO URI and the source citing it."""

    esco_uri: str
    source_ref_id: uuid.UUID


def decide(
    title: str,
    key: str,
    *,
    choice: Choice | None,
    labelled: Sequence[str],
    pack: PackTargets,
    pack_keys: Mapping[str, str],
) -> TargetRecord:
    """The record for a title (as a concept, `key`), from what matching it found: the
    person's choice, the occupations holding it as a label, and the pack's targets (each
    target's title as a concept, by target ID)."""
    matches = tuple(sorted(set(labelled)))
    titled = next((t for t in pack.targets if pack_keys.get(t.target_id) == key), None)
    link, occupation = TargetLink.NONE, None
    if choice is not None:
        link, occupation = TargetLink.OCCUPATION_CHOICE, choice.esco_uri
    elif len(matches) == 1:
        link, occupation = TargetLink.EXACT_LABEL, matches[0]
    elif titled is not None and titled.esco_uri is not None:
        link, occupation = TargetLink.PACK_CROSSWALK, titled.esco_uri
    coverage, covered = TargetCoverage.NOT_COVERED, None
    basis: PackTargetBasis | None = None
    crosswalked = [t for t in pack.targets if occupation and t.esco_uri == occupation]
    if titled is not None:
        coverage, covered, basis = TargetCoverage.PACK_TARGET, titled.target_id, "title"
    elif len(crosswalked) == 1:
        coverage, covered = TargetCoverage.PACK_TARGET, crosswalked[0].target_id
        basis = "esco_crosswalk"
    elif crosswalked:
        coverage = TargetCoverage.SEVERAL_PACK_TARGETS
    return TargetRecord(
        title=title,
        key=key,
        kind=TargetKind.ESCO if choice is not None else TargetKind.OWN_WORDS,
        occupation_uri=occupation,
        link=link,
        label_matches=matches,
        coverage=coverage,
        pack_target_id=covered,
        pack_target_basis=basis,
        pack_version=pack.version,
        source_ref_id=choice.source_ref_id if choice is not None else None,
    )


def resolve_target(
    tx: Tx, workspace_id: uuid.UUID, title: str, pack: PackTargets, choice: Choice | None = None
) -> TargetRecord:
    """What a target title names, by the module's rules. Without `choice`, an earlier choice
    of the workspace whose ESCO title is the title as a concept is the person's choice (the
    latest such)."""
    keys = taxonomy_store.concept_keys(tx, [title, *(t.title for t in pack.targets)])
    key = keys[title]
    if choice is None:
        choices = store.occupation_choices(tx, workspace_id)
        preferred = taxonomy_store.preferred_keys(tx, [uri for uri, _ in choices])
        earlier = [Choice(uri, source) for uri, source in choices if preferred.get(uri) == key]
        choice = earlier[-1] if earlier else None
    return decide(
        title,
        key,
        choice=choice,
        labelled=taxonomy_store.label_match_uris(tx, title),
        pack=pack,
        pack_keys={t.target_id: keys[t.title] for t in pack.targets},
    )


def target_titles(document: ProfileDocument) -> list[str]:
    field = document.target_titles
    if field.state is not FieldState.PROVIDED or not field.value:
        return []
    return [str(title) for title in field.value]


def record_targets(
    tx: Tx,
    recorded_by: uuid.UUID | None,
    workspace_id: uuid.UUID,
    document: ProfileDocument,
    pack: PackTargets,
    choice: tuple[str, Choice] | None = None,
) -> None:
    """Store a record for each of the document's targets that has none yet, and for the title
    the person just chose an occupation for (`choice`), which replaces any earlier record of
    that title. `recorded_by`: the actor, or None for the seeded fixture workspace."""
    titles = target_titles(document)
    if not titles:
        return
    keys = taxonomy_store.concept_keys(tx, titles)
    held = store.target_records(tx, workspace_id, keys.values())
    for title in titles:
        chosen = choice[1] if choice is not None and choice[0] == title else None
        if keys[title] in held and chosen is None:
            continue
        record = resolve_target(tx, workspace_id, title, pack, chosen)
        store.upsert_target_record(tx, workspace_id, record, recorded_by)
        held[record.key] = record


def current_targets(tx: Tx, workspace_id: uuid.UUID) -> tuple[int, list[TargetRecord]]:
    """The current profile's version and its targets' records (`stored_targets`)."""
    visible_workspace(tx, workspace_id)  # someone else's workspace is not found, never empty
    latest = store.current_profile(tx, workspace_id)
    if latest is None:
        return 0, []
    return latest.version, stored_targets(tx, workspace_id, latest.document)


def stored_targets(
    tx: Tx, workspace_id: uuid.UUID, document: ProfileDocument
) -> list[TargetRecord]:
    """The records of the document's targets, in its order, one per title as a concept. A
    target saved without one is an internal error, never a target that names nothing."""
    titles = target_titles(document)
    if not titles:
        return []
    keys = taxonomy_store.concept_keys(tx, titles)
    held = store.target_records(tx, workspace_id, keys.values())
    records: dict[str, TargetRecord] = {}
    for title in titles:
        record = held.get(keys[title])
        if record is None:
            raise CareerwrightError(
                ErrorCode.INTERNAL_ERROR,
                "A target has no stored record.",
                stage=ErrorStage.PROFILE,
            )
        # The person's words as the profile holds them; the first of one concept stands.
        records.setdefault(record.key, replace(record, title=title))
    return list(records.values())
