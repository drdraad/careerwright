"""The person's own details beside a title (Task 6d slice C; ADR 0015 decisions 3 and 4; ADR
0012 as amended on 2026-10-31; spec section 4's target hypotheses and section 18's TargetRole).

Beside their current or last role, or a target, the person may give a seniority and an
industry, in their words, and may mark skills ESCO lists for its kind of work "not part of my
job". Everything here is optional and never a default: a detail not given is None, shown as
not known. Matching ignores it (the slate, the sketch, the records and Skills never read it),
display and search keep it. A mark is a display state: never evidence, never a level, never
used for suitability or readiness. Details are kept per title as a concept
(`careerwright.concept_key`), so a role named again later finds them again. Each save is the
next version of that title's details, with an expected version and an Idempotency-Key.
"""

import uuid
from dataclasses import dataclass
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from careerwright.catalogue import taxonomy_store
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import store as identity_store
from careerwright.identity.access import Actor
from careerwright.identity.records import EventKind
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import store, titles
from careerwright.profile.document import FieldState, ProfileDocument
from careerwright.profile.records import TargetRecord, TitleDetails, TitleUse
from careerwright.profile.targets import PackTargets, role_record, stored_targets, target_titles

DetailText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
# ESCO v1.2.1 lists at most 99 essential skills for one occupation.
MAX_MARKS = 100


class SetTitleDetails(BaseModel):
    """The whole of a title's details, as the person leaves them."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0, description="This title's details; 0 while none saved.")
    title_use: TitleUse
    title: str = Field(
        min_length=1,
        max_length=120,
        description="Your role, or one of your targets, as your answers hold it (as a concept).",
    )
    seniority: DetailText | None = Field(description="Optional, in your words; null: not given.")
    industry: DetailText | None = Field(description="Optional, in your words; null: not given.")
    not_part_of_job: list[uuid.UUID] = Field(
        default_factory=list,
        max_length=MAX_MARKS,
        description="Skills ESCO lists as essential for this kind of work that you marked not "
        "part of your job: a display state, never evidence.",
    )

    @model_validator(mode="after")
    def _each_mark_once(self) -> Self:
        if len(set(self.not_part_of_job)) != len(self.not_part_of_job):
            raise ValueError("each skill is marked at most once")
        return self


@dataclass(frozen=True)
class TitleDetailsView:
    title: str  # as the person's answers hold it
    details: TitleDetails


def _titles(document: ProfileDocument) -> list[tuple[TitleUse, str]]:
    role = document.current_role
    mine = [(TitleUse.ROLE, role.value)] if role.state is FieldState.PROVIDED and role.value else []
    return mine + [(TitleUse.TARGET, title) for title in target_titles(document)]


def _views(tx: Tx, workspace_id: uuid.UUID, document: ProfileDocument) -> list[TitleDetailsView]:
    """Each of the person's titles with its details (version 0 with none), the role first,
    then the targets in their order, one per title as a concept."""
    mine = _titles(document)
    if not mine:
        return []
    keys = taxonomy_store.concept_keys(tx, [title for _, title in mine])
    held = {
        use: store.title_details(tx, workspace_id, use, [keys[t] for u, t in mine if u is use])
        for use in TitleUse
    }
    views: dict[tuple[TitleUse, str], TitleDetailsView] = {}
    for use, title in mine:
        key = keys[title]
        details = held[use].get(key) or TitleDetails(use, key, 0)
        views.setdefault((use, key), TitleDetailsView(title, details))
    return list(views.values())


def current_title_details(tx: Tx, workspace_id: uuid.UUID) -> tuple[int, list[TitleDetailsView]]:
    """The current profile's version and the details beside each of its titles."""
    visible_workspace(tx, workspace_id)  # someone else's workspace is not found, never empty
    latest = store.current_profile(tx, workspace_id)
    if latest is None:
        return 0, []
    return latest.version, _views(tx, workspace_id, latest.document)


def role_marks(tx: Tx, workspace_id: uuid.UUID, document: ProfileDocument) -> frozenset[uuid.UUID]:
    """The skills ESCO lists for the role's kind of work that the person marked not part of
    their job (display only)."""
    for view in _views(tx, workspace_id, document):
        if view.details.title_use is TitleUse.ROLE:
            return frozenset(view.details.not_part_of_job)
    return frozenset()


def entered_words(tx: Tx, workspace_id: uuid.UUID, command: SetTitleDetails) -> list[str]:
    """What a save enters in words: a seniority or an industry the version it was made
    against doesn't hold. What the support screen reads (ADR 0007): a stored version never
    changes, so a replay reads the same words."""
    key = taxonomy_store.concept_keys(tx, [command.title])[command.title]
    base = store.title_details_at(
        tx, workspace_id, command.title_use, key, command.expected_version
    )
    held = (None, None) if base is None else (base.seniority, base.industry)
    given = (command.seniority, command.industry)
    return [words for words, was in zip(given, held, strict=True) if words and words != was]


def _invalid(field: str, reason: str, message: str) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        message,
        stage=ErrorStage.PROFILE,
        details={"field": field, "reason": reason},
    )


def _record(
    tx: Tx,
    workspace_id: uuid.UUID,
    document: ProfileDocument,
    use: TitleUse,
    key: str,
    pack: PackTargets,
) -> TargetRecord | None:
    if use is TitleUse.ROLE:
        return role_record(tx, workspace_id, document, pack)
    found = [r for r in stored_targets(tx, workspace_id, document, pack) if r.key == key]
    return found[0] if found else None


def listed_skills(tx: Tx, record: TargetRecord | None, use: TitleUse) -> frozenset[uuid.UUID]:
    """The essential skills ESCO lists for the one occupation a title names, or none."""
    if record is None:
        return frozenset()
    if use is TitleUse.ROLE:
        resolved = titles.role(tx, record)
    else:
        [resolved] = titles.targets(tx, [record])
    if len(resolved.occupations) != 1:
        return frozenset()
    occupation = taxonomy_store.occupation(tx, resolved.occupations[0])
    if occupation is None:  # an occupation the held release lacks lists nothing
        return frozenset()
    return frozenset(s.skill_id for s in occupation.skills if s.relation == "essential")


def set_title_details(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: SetTitleDetails, pack: PackTargets
) -> tuple[TitleDetailsView, bool]:
    """Save a title's details as its next version. Returns them and whether they changed."""
    visible_workspace(tx, workspace_id, lock=True)
    latest = store.current_profile(tx, workspace_id)
    key = taxonomy_store.concept_keys(tx, [command.title])[command.title]
    views = [] if latest is None else _views(tx, workspace_id, latest.document)
    mine = [
        v for v in views if v.details.title_use is command.title_use and v.details.title_key == key
    ]
    if latest is None or not mine:
        raise _invalid(
            "title", "not_your_title", "Details go beside your role or one of your targets."
        )
    [view] = mine
    current = view.details
    if command.expected_version != current.version:
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "These details changed since you loaded them. Reload, then try again.",
            stage=ErrorStage.PROFILE,
            details={"current_version": current.version},
        )
    # Only a newly marked skill is checked: a mark made before stays a display state even when
    # the title's occupation has changed since, so it never blocks a later save.
    added = [skill for skill in command.not_part_of_job if skill not in current.not_part_of_job]
    if added:
        record = _record(tx, workspace_id, latest.document, command.title_use, key, pack)
        listed = listed_skills(tx, record, command.title_use)
        if any(skill not in listed for skill in added):
            raise _invalid(
                "not_part_of_job",
                "not_listed",
                "Only a skill ESCO lists for this kind of work can be marked.",
            )
    marks = tuple(command.not_part_of_job)
    if (command.seniority, command.industry, marks) == (
        current.seniority,
        current.industry,
        current.not_part_of_job,
    ):
        return view, False
    saved = store.insert_title_details(
        tx,
        workspace_id,
        TitleDetails(
            command.title_use,
            key,
            current.version + 1,
            command.seniority,
            command.industry,
            marks,
        ),
        actor.actor_id,
    )
    identity_store.append_event(
        tx,
        workspace_id,
        EventKind.TITLE_DETAILS_UPDATED,
        str(workspace_id),
        detail={"version": saved.version},
    )
    return TitleDetailsView(view.title, saved), True
