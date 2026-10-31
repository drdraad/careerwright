"""Each target is stored once (Task 6d slice A; ADR 0015 decision 3; ADR 0012 and ADR 0007 as
amended on 2026-10-31; the audit's code appendix, finding F5), and so is the person's current
or last role when they name it at the first question (Task 6d slice B).

When a target is chosen or saved, `resolve_target` decides once what it names, by one set of
rules, and the record is stored with it (`target_records`, migration 0034). The slate, the
sketch, the strength, Skills and the world read that record instead of resolving the title
again, so they can't disagree about the same target. One record serves a title as a concept,
whether it is a target or the role.

The rules, in order. A title is compared as a concept (`careerwright.concept_key`: "&" read as
"and", accents, case, punctuation, hyphens and simple plurals folded), and nothing is guessed:
1. the occupation the person chose for it (an `occupation_choice` source, by its ESCO URI):
   as the target itself, or as the closest to a title of their own (`closest`); or an
   earlier choice of the workspace whose ESCO title is the title as a concept;
2. otherwise, once the person said none of the closest occupations is their job, none;
3. otherwise the one occupation holding the title as a label (hidden labels included);
   several stay several, each kept, none picked: the person chooses which they mean;
4. otherwise, for a title that is one of the option pack's targets, the occupation its
   crosswalk names;
5. otherwise none yet.
Its words are an ESCO occupation's title (chosen as such), a title the UK job-title index
lists (exactly, `catalogue.uk_titles`: with every SOC 2020 and ISCO-08 group ONS codes it to),
or the person's own. Its coverage is the option pack's target with the same title, or else the
one pack target whose crosswalk names its occupation; several such targets are never guessed
between. A title is a pack target's when it is that title as a concept, or else when it is
without its qualifiers in brackets: "Registered nurse (adult)" is the pack's "Registered
nurse", as Skills matched pack titles before targets were stored once, unless a qualifier
names another field of the target's registered work (`OTHER_FIELDS`). Only the pack's titles
are matched so; ESCO's labels are matched by the whole title.
"""

import re
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from careerwright.catalogue import taxonomy_store, uk_titles
from careerwright.catalogue.records import UkTitle
from careerwright.db import Tx
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

# A qualifier in brackets, such as "(adult)" or "[2nd line]". Migration 0035 holds the same
# pattern, and a test keeps the two equal.
QUALIFIER = r"\([^)]*\)|\[[^\]]*\]"
_QUALIFIER = re.compile(QUALIFIER)

# Qualifiers, as concepts, that name another field of a pack target's registered work, by the
# target's title as a concept: such a title is another registered role, so the bracket rule
# never takes it to that target. The pack's "Registered nurse" rests on adult nursing evidence,
# and the Nursing and Midwifery Council registers nurses in four fields: adult, children's,
# learning disabilities and mental health. A neutral qualifier ("(adult)") still reaches it.
OTHER_FIELDS: Mapping[str, frozenset[str]] = {
    "registered nurse": frozenset(
        {"mental health", "children s", "children", "learning disability"}
    ),
}


def without_qualifiers(title: str) -> str:
    return _QUALIFIER.sub(" ", title)


def qualifiers(title: str) -> list[str]:
    """The words inside each pair of brackets in the title."""
    return [match[1:-1] for match in _QUALIFIER.findall(title)]


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
    unqualified: str,
    choice: Choice | None,
    labelled: Sequence[str],
    pack: PackTargets,
    pack_keys: Mapping[str, str],
    qualifiers: Sequence[str] = (),
    listed: UkTitle | None = None,
    closest: bool = False,
    none_of_these: bool = False,
) -> TargetRecord:
    """The record for a title (as a concept, `key`; without its qualifiers in brackets,
    `unqualified`; each qualifier as a concept, `qualifiers`), from what matching it found:
    the person's choice (`closest`: chosen as the closest to a title of their own, not as the
    title itself), whether they said none of the closest is their job, the occupations
    holding it as a label, the UK job-title index's entry for it, and the pack's targets
    (each target's title as a concept, by target ID)."""
    matches = tuple(sorted(set(labelled)))

    def reached(target: PackTarget, by_brackets: bool) -> bool:
        own = pack_keys.get(target.target_id)
        if not by_brackets:
            return own == key
        return own == unqualified and not OTHER_FIELDS.get(own, frozenset()) & set(qualifiers)

    titled = next(
        (t for by in (False, True) for t in pack.targets if reached(t, by)),
        None,
    )
    link, occupation = TargetLink.NONE, None
    if choice is not None:
        link, occupation = TargetLink.OCCUPATION_CHOICE, choice.esco_uri
    elif none_of_these:
        link = TargetLink.NONE_OF_THESE
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
    kind = (
        TargetKind.ESCO
        if choice is not None and not closest
        else TargetKind.ONS
        if listed is not None
        else TargetKind.OWN_WORDS
    )
    ons = listed if kind is TargetKind.ONS else None
    return TargetRecord(
        title=title,
        key=key,
        kind=kind,
        occupation_uri=occupation,
        link=link,
        label_matches=matches,
        coverage=coverage,
        pack_target_id=covered,
        pack_target_basis=basis,
        pack_version=pack.version,
        source_ref_id=choice.source_ref_id if choice is not None else None,
        soc_codes=ons.soc_codes if ons else (),
        isco_codes=tuple(g.code for g in ons.isco_groups) if ons else (),
    )


def resolve_target(
    tx: Tx,
    workspace_id: uuid.UUID,
    title: str,
    pack: PackTargets,
    choice: Choice | None = None,
    *,
    closest: bool = False,
    none_of_these: bool = False,
) -> TargetRecord:
    """What a title names, by the module's rules. Without `choice`, an earlier choice of the
    workspace whose ESCO title is the title as a concept is the person's choice (the latest
    such). `closest`: `choice` is the occupation the person chose as closest to their own
    title; `none_of_these`: they said none of those is their job."""
    unqualified = without_qualifiers(title)
    brackets = qualifiers(title)
    keys = taxonomy_store.concept_keys(
        tx, [title, unqualified, *brackets, *(t.title for t in pack.targets)]
    )
    key = keys[title]
    if choice is None and not none_of_these:
        choices = store.occupation_choices(tx, workspace_id)
        preferred = taxonomy_store.preferred_keys(tx, [uri for uri, _ in choices])
        earlier = [Choice(uri, source) for uri, source in choices if preferred.get(uri) == key]
        choice = earlier[-1] if earlier else None
    return decide(
        title,
        key,
        unqualified=keys[unqualified],
        qualifiers=[keys[b] for b in brackets],
        choice=choice,
        labelled=taxonomy_store.label_match_uris(tx, title),
        pack=pack,
        pack_keys={t.target_id: keys[t.title] for t in pack.targets},
        listed=uk_titles.listed(tx, [title]).get(title),
        closest=closest,
        none_of_these=none_of_these,
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


def title_record(tx: Tx, workspace_id: uuid.UUID, title: str, pack: PackTargets) -> TargetRecord:
    """The stored record of one title (the role's, named at the first question), in the
    person's spelling, or, with none stored, the record `resolve_target` would store; a read
    stores nothing."""
    key = taxonomy_store.concept_keys(tx, [title])[title]
    held = store.target_records(tx, workspace_id, [key]).get(key)
    return replace(held, title=title) if held else resolve_target(tx, workspace_id, title, pack)


def current_targets(
    tx: Tx, workspace_id: uuid.UUID, pack: PackTargets
) -> tuple[int, list[TargetRecord]]:
    """The current profile's version and its targets' records (`stored_targets`)."""
    visible_workspace(tx, workspace_id)  # someone else's workspace is not found, never empty
    latest = store.current_profile(tx, workspace_id)
    if latest is None:
        return 0, []
    return latest.version, stored_targets(tx, workspace_id, latest.document, pack)


def stored_targets(
    tx: Tx, workspace_id: uuid.UUID, document: ProfileDocument, pack: PackTargets
) -> list[TargetRecord]:
    """The records of the document's targets, in its order, one per title as a concept. Every
    write path stores its targets' records (`record_targets`; migration 0035 for the past). A
    title with none is decided here by `resolve_target`, as it would be stored, and nothing
    is stored on a read."""
    titles = target_titles(document)
    if not titles:
        return []
    keys = taxonomy_store.concept_keys(tx, titles)
    held = store.target_records(tx, workspace_id, keys.values())
    records: dict[str, TargetRecord] = {}
    for title in titles:
        record = held.get(keys[title]) or resolve_target(tx, workspace_id, title, pack)
        # The person's words as the profile holds them; the first of one concept stands.
        records.setdefault(record.key, replace(record, title=title))
    return list(records.values())
