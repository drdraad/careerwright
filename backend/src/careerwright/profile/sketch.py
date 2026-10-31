"""The early requirement sketch (spec section 3, "Early value and progressive refinement";
S2.5; STATE-05).

Once the person has a target, the sketch shows what that occupation usually asks for, from
ESCO's essential skills, and the generic steps between here and a plan, each explicitly
unresolved. The web labels it an early sketch, never a feasible or Pareto-optimal route; it
names no provider, price or date. A target ESCO does not name gets no requirement list,
only its resolution. Each target is read from its stored record
(`careerwright.profile.targets`), with its coverage. It says which of the minimum inputs (a
target and four practical answers: current work, weekly hours, budget and work area) are not
asked yet, because the later chapters need them; Unknown, Skipped and Prefer not to say are
answers. It carries facts only: the web words them (Task 6d slice A; ruling R11).
"""

import uuid
from dataclasses import dataclass
from enum import StrEnum

from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.esco import concept_id, normalise_label
from careerwright.catalogue.records import IscoGroupRef
from careerwright.catalogue.taxonomy import held_release, search_occupations
from careerwright.db import Tx
from careerwright.errors import CareerwrightError
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile.commands import current_profile
from careerwright.profile.document import FieldState
from careerwright.profile.interview import ProfileField
from careerwright.profile.records import TargetCoverage, TargetRecord
from careerwright.profile.targets import PackTargets, stored_targets

REQUIREMENTS_SHOWN = 6
CLOSE_MATCHES = 3
MINIMUM_INPUTS = (
    ProfileField.TARGET_TITLES,
    ProfileField.CURRENT_ROLE,
    ProfileField.WEEKLY_STUDY_HOURS,
    ProfileField.DIRECT_SPEND_CAP,
    ProfileField.CITIES,
)


class Resolution(StrEnum):
    # The title is matched with case, punctuation and plurals folded, hidden labels included.
    ESCO = "esco"  # matched to exactly one ESCO occupation
    AMBIGUOUS = "ambiguous"  # to several: the person chooses, nothing is guessed
    PROVISIONAL = "provisional"  # to none, and the person confirmed it as their own title
    NOT_FOUND = "not_found"  # to none: no requirement list until it is resolved


@dataclass(frozen=True)
class OccupationRef:
    concept_id: uuid.UUID
    title: str
    isco_group: IscoGroupRef


@dataclass(frozen=True)
class TargetSketch:
    title: str
    resolution: Resolution
    occupations: list[OccupationRef]  # the one (esco) or the several (ambiguous)
    close_matches: list[OccupationRef]  # for a title matched to none
    requirements: list[str]  # ESCO's essential skills, the first few (esco only)
    requirement_count: int | None  # None: no requirement list (not resolved to ESCO)
    regulated: bool | None
    coverage: TargetCoverage  # from its stored record


class Step(StrEnum):
    """The generic steps between here and a plan, each unresolved until a later chapter
    resolves it."""

    COMPARE = "compare"  # compare the requirements with what the person has done (Skills)
    FIND_OPTIONS = "find_options"  # courses, work routes or funding for any gaps (Options)
    CHECK_TIME_AND_COST = "check_time_and_cost"  # against their week and budget (Routes)


STEPS = (Step.COMPARE, Step.FIND_OPTIONS, Step.CHECK_TIME_AND_COST)


@dataclass(frozen=True)
class Sketch:
    profile_version: int
    inputs: dict[ProfileField, FieldState]
    not_asked: list[ProfileField]
    targets: list[TargetSketch]
    steps: list[Step]


def _ref(tx: Tx, concept: uuid.UUID) -> OccupationRef | None:
    detail = taxonomy_store.occupation(tx, concept)
    if detail is None:
        return None
    unit = detail.isco_groups[-1]
    return OccupationRef(detail.concept_id, detail.preferred_label, unit)


def _esco(tx: Tx, record: TargetRecord, ref: OccupationRef) -> TargetSketch:
    facts = taxonomy_store.occupation_facts(tx, [ref.concept_id], skills_shown=REQUIREMENTS_SHOWN)[
        ref.concept_id
    ]
    return TargetSketch(
        record.title,
        Resolution.ESCO,
        [ref],
        [],
        list(facts.essential_skills),
        facts.essential_skill_count,
        facts.regulated,
        record.coverage,
    )


def _target(tx: Tx, workspace_id: uuid.UUID, record: TargetRecord) -> TargetSketch:
    """What the target's record names in ESCO: its occupation (chosen, or the one holding its
    title as a label); several holding its title is ambiguous, and nothing is guessed. An
    occupation the held release lacks is simply absent."""
    named = (record.esco_occupation,) if record.esco_occupation else record.label_matches
    refs = [ref for ref in (_ref(tx, concept_id(uri)) for uri in named) if ref is not None]
    if record.esco_occupation is not None and refs:
        return _esco(tx, record, refs[0])
    title = record.title
    if len(refs) == 1:
        return _esco(tx, record, refs[0])
    if refs:
        refs.sort(key=lambda ref: ref.concept_id)
        return TargetSketch(title, Resolution.AMBIGUOUS, refs, [], [], None, None, record.coverage)
    provisional = taxonomy_store.provisional_by_title(tx, workspace_id, normalise_label(title))
    close: list[OccupationRef] = []
    try:
        found = search_occupations(tx, title, CLOSE_MATCHES, any_word=False)
        close = [
            ref
            for ref in (_ref(tx, hit.concept_id) for hit in found.full_text[:CLOSE_MATCHES])
            if ref is not None
        ]
    except CareerwrightError as error:
        if error.details.get("reason") != "no_search_terms":
            raise
        close = []  # a title with no searchable word has no close matches to offer
    return TargetSketch(
        title,
        Resolution.PROVISIONAL if provisional is not None else Resolution.NOT_FOUND,
        [],
        close,
        [],
        None,
        None,
        record.coverage,
    )


def requirement_sketch(tx: Tx, workspace_id: uuid.UUID, pack: PackTargets) -> Sketch:
    visible_workspace(tx, workspace_id)  # someone else's workspace is not found, never empty
    profile = current_profile(tx, workspace_id)
    held_release(tx)
    document = profile.document
    inputs = {field: getattr(document, field.value).state for field in MINIMUM_INPUTS}
    records = stored_targets(tx, workspace_id, document, pack)
    return Sketch(
        profile_version=profile.version,
        inputs=inputs,
        not_asked=[field for field, state in inputs.items() if state is FieldState.UNASKED],
        targets=[_target(tx, workspace_id, record) for record in records],
        steps=list(STEPS) if records else [],
    )
