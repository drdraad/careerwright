"""The early requirement sketch (spec section 3, "Early value and progressive refinement";
S2.5; STATE-05).

Once the person has a target, the sketch shows what that occupation usually asks for, from
ESCO's essential skills, and the generic steps between here and a plan, each explicitly
unresolved. It is always labelled an early sketch, never a feasible or Pareto-optimal
route; it names no provider, price or date. A target ESCO does not hold gets no requirement
list, only its research status. It says which of the minimum inputs (a target and four
practical answers: current work, weekly hours, budget and work area) are not asked yet,
because the later chapters need them; Unknown, Skipped and Prefer not to say are answers.
"""

import uuid
from dataclasses import dataclass
from enum import StrEnum

from nessa.catalogue import taxonomy_store
from nessa.catalogue.esco import normalise_label
from nessa.catalogue.records import IscoGroupRef
from nessa.catalogue.taxonomy import held_release, search_occupations
from nessa.db import Tx
from nessa.errors import NessaError
from nessa.identity.workspaces import visible_workspace
from nessa.profile import store
from nessa.profile.commands import current_profile
from nessa.profile.document import FieldState
from nessa.profile.interview import ProfileField

SKETCH_LABEL = "Early sketch, not a checked route"
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
    ESCO = "esco"  # exactly one ESCO occupation holds the title
    AMBIGUOUS = "ambiguous"  # several do: the person chooses, nothing is guessed
    PROVISIONAL = "provisional"  # a title the person confirmed that ESCO does not list
    NOT_FOUND = "not_found"  # neither: no requirement list until it is resolved


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
    close_matches: list[OccupationRef]  # for a title ESCO does not hold
    requirements: list[str]  # ESCO's essential skills, the first few (esco only)
    requirement_count: int | None  # None: no requirement list (not resolved to ESCO)
    regulated: bool | None
    research_status: str


@dataclass(frozen=True)
class Step:
    name: str
    chapter: str
    detail: str
    state: str = "unresolved"  # every step is, until later chapters resolve it


@dataclass(frozen=True)
class Sketch:
    label: str
    profile_version: int
    inputs: dict[ProfileField, FieldState]
    not_asked: list[ProfileField]
    targets: list[TargetSketch]
    steps: list[Step]


def _ref(tx: Tx, concept_id: uuid.UUID) -> OccupationRef | None:
    detail = taxonomy_store.occupation(tx, concept_id)
    if detail is None:
        return None
    unit = detail.isco_groups[-1]
    return OccupationRef(detail.concept_id, detail.preferred_label, unit)


def _chosen(tx: Tx, workspace_id: uuid.UUID) -> dict[str, OccupationRef]:
    """The occupations the person chose as targets, by their title (casefolded); a later
    choice of the same title wins. A choice from another release is simply absent."""
    uris = store.chosen_occupation_uris(tx, workspace_id)
    concepts = taxonomy_store.concepts_by_uri(tx, uris)
    chosen: dict[str, OccupationRef] = {}
    for uri in uris:
        ref = _ref(tx, concepts[uri]) if uri in concepts else None
        if ref is not None:
            chosen[ref.title.casefold()] = ref
    return chosen


def _esco(tx: Tx, title: str, ref: OccupationRef) -> TargetSketch:
    facts = taxonomy_store.occupation_facts(tx, [ref.concept_id], skills_shown=REQUIREMENTS_SHOWN)[
        ref.concept_id
    ]
    return TargetSketch(
        title,
        Resolution.ESCO,
        [ref],
        [],
        list(facts.essential_skills),
        facts.essential_skill_count,
        facts.regulated,
        "Requirements from ESCO; not yet compared with your experience.",
    )


def _target(
    tx: Tx, workspace_id: uuid.UUID, title: str, chosen: dict[str, OccupationRef]
) -> TargetSketch:
    """The occupation the person chose for this title, else the one ESCO occupation that
    holds it as a label; several is ambiguous, and nothing is guessed."""
    if title.casefold() in chosen:
        return _esco(tx, title, chosen[title.casefold()])
    matched = sorted({m.concept_id for m in taxonomy_store.concept_key_matches(tx, title)})
    refs = [ref for ref in (_ref(tx, concept_id) for concept_id in matched) if ref is not None]
    if len(refs) == 1:
        return _esco(tx, title, refs[0])
    if refs:
        return TargetSketch(
            title,
            Resolution.AMBIGUOUS,
            refs,
            [],
            [],
            None,
            None,
            "Several ESCO occupations have this title. Choose the one you mean.",
        )
    provisional = taxonomy_store.provisional_by_title(tx, workspace_id, normalise_label(title))
    close: list[OccupationRef] = []
    try:
        found = search_occupations(tx, title, CLOSE_MATCHES, any_word=False)
        close = [
            ref
            for ref in (_ref(tx, hit.concept_id) for hit in found.full_text[:CLOSE_MATCHES])
            if ref is not None
        ]
    except NessaError as error:
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
        "No ESCO record, so no requirement list yet. Not researched.",
    )


def _steps(inputs: dict[ProfileField, FieldState]) -> list[Step]:
    def known(field: ProfileField) -> bool:
        return inputs[field] is FieldState.PROVIDED

    timing = (
        "Uses your weekly hours."
        if known(ProfileField.WEEKLY_STUDY_HOURS)
        else "Your weekly hours aren't known, so timing can't be checked yet."
    )
    budget = (
        "Uses your spending limit."
        if known(ProfileField.DIRECT_SPEND_CAP)
        else "Your spending limit isn't known, so costs can't be checked yet."
    )
    return [
        Step(
            "Compare these requirements with what you have done",
            "skills",
            "Not compared yet: nothing is marked missing or met.",
        ),
        Step(
            "Find courses, work routes or funding for any gaps",
            "options",
            "Not researched yet: no providers, prices or dates.",
        ),
        Step(
            "Check the time and cost against your week and budget", "routes", f"{timing} {budget}"
        ),
    ]


def requirement_sketch(tx: Tx, workspace_id: uuid.UUID) -> Sketch:
    visible_workspace(tx, workspace_id)  # someone else's workspace is not found, never empty
    profile = current_profile(tx, workspace_id)
    held_release(tx)
    document = profile.document
    inputs = {field: getattr(document, field.value).state for field in MINIMUM_INPUTS}
    targets_field = document.target_titles
    titles = (
        [str(t) for t in targets_field.value]
        if targets_field.state is FieldState.PROVIDED and targets_field.value
        else []
    )
    chosen = _chosen(tx, workspace_id) if titles else {}
    return Sketch(
        label=SKETCH_LABEL,
        profile_version=profile.version,
        inputs=inputs,
        not_asked=[field for field, state in inputs.items() if state is FieldState.UNASKED],
        targets=[_target(tx, workspace_id, title, chosen) for title in titles],
        steps=_steps(inputs) if titles else [],
    )
