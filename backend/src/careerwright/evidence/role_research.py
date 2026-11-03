"""Research this role (Task 6e, S2.9; ADR 0015 decisions 2, 3 and 6; ADR 0009 decision 12,
amendment): for a title no list holds, the person's own words or a title idea not yet found.

1. **The search** is a source search with its own purpose (`RoleSearchInput`): one bounded
   request on the one bounded activity, told only the title and "England" (SEC-05), its
   candidates checked by code against the fetch checks and the source manifest. Its estimated
   cost is the source search's (`GET .../spend/estimate?kind=source_search`).
2. **The reading** is an acquisition of up to `MAX_PAGES` of those candidates (only pages the
   search really returned, never a site's home page; with none, the search found no page
   Careerwright could read) through the restricted acquisition worker and the guarded
   fetcher; each page's class comes from the manifest. Each target carries the title, so the
   worker checks it as a span of the page's visible text and records that check, never a
   posting, and never hands the page to a model. It calls no model and costs nothing.
3. **Whether the role is found** is decided on read, by `corroboration.corroborate`, from the
   checks recorded: found on two independent sources or one official page; otherwise "not yet
   found in independent sources". A blocked, failed or unread page is never counted as a
   page without the title: a reading that ended without reading enough says it stopped.

The research is private to its workspace, `proposed` and dated (R9). Either run can be
cancelled (`POST .../runs/{id}/cancel`). Nothing here changes the profile: the person's own
title stays choosable without research, and making a found title a target is the person's
choice through the profile's own write path.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit

from pydantic import Field

from careerwright.catalogue import taxonomy_store, uk_titles
from careerwright.config import RuntimeMode
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import role_store, store
from careerwright.evidence.acquisition import RECORDABLE_PORTS
from careerwright.evidence.addresses import CheckedUrl, check_url
from careerwright.evidence.corroboration import (
    Corroboration,
    NotYetFoundReason,
    PageEvidence,
    RoleVerdict,
    corroborate,
)
from careerwright.evidence.records import (
    AttemptReason,
    AttemptStatus,
    InputRoute,
    RightsClass,
    StrictModel,
)
from careerwright.evidence.search import (
    ROLE_SEARCH,
    RoleSearchInput,
    SearchEmptyReason,
    SearchProposal,
    SearchPurpose,
    is_site_root,
    role_prompt_bytes,
    worst_case_nano_usd,
)
from careerwright.identity import run_store
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.records import Run, RunKind
from careerwright.identity.runs import (
    RunRequest,
    open_output,
    submit_keyless_run,
    submit_run,
    visible_run,
)
from careerwright.identity.spend import SpendLimits
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile.commands import current_profile
from careerwright.profile.store import stale_version
from careerwright.vocabulary import WorkState

# The candidate pages one reading fetches (ADR 0009 decision 12, amendments; the product owner,
# 3 November 2026: "Up to 20 pages"); `acquisition_targets.position` holds 0 to 19.
MAX_PAGES = 20
LIST_LIMIT = 20
_SETTLED = frozenset({WorkState.COMPLETE, WorkState.FAILED, WorkState.CANCELLED})


class StartRoleResearch(StrictModel):
    expected_profile_version: int = Field(ge=0)
    title: str = Field(
        min_length=1,
        max_length=120,
        description="A title no list holds: your own words, or a title idea not yet found.",
    )


def no_list_holds(tx: Tx, title: str) -> None:
    """Research is for a title no list holds: one ESCO holds as a label, or the UK job-title
    index lists, is already recognised without it."""
    if taxonomy_store.label_match_uris(tx, title) or uk_titles.listed(tx, [title]):
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "That title is already in a list Careerwright holds, so it needs no research.",
            stage=ErrorStage.REQUEST,
            details={"field": "title", "reason": "title_already_listed"},
        )


def start_research(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: StartRoleResearch,
    *,
    models: ModelChoice,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
) -> uuid.UUID:
    """The research's search run, pinned to the profile version the person saw, and its
    record. Only the title and England are sealed into the run."""
    profile = current_profile(tx, workspace_id)
    if command.expected_profile_version != profile.version:
        raise stale_version(profile.version)
    title = " ".join(command.title.split())
    if not title:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Give the title to research.",
            stage=ErrorStage.REQUEST,
            details={"field": "title", "reason": "empty"},
        )
    no_list_holds(tx, title)
    context = RoleSearchInput(title=title)
    if role_prompt_bytes(context) > ROLE_SEARCH.max_prompt_bytes:
        raise CareerwrightError(
            ErrorCode.LIMIT_EXCEEDED,
            "That title is too long to search for.",
            stage=ErrorStage.REQUEST,
            details={"reason": "search_too_long"},
        )
    run = submit_run(
        tx,
        actor,
        workspace_id,
        RunRequest(
            RunKind.SOURCE_SEARCH,
            worst_case_nano_usd,
            profile_version=profile.version,
            input=context.model_dump_json().encode(),
        ),
        models=models,
        keyring=keyring,
        runtime_mode=runtime_mode,
        defaults=defaults,
        now=now,
    )
    research_id = uuid.uuid4()
    role_store.insert_research(
        tx,
        research_id=research_id,
        workspace_id=workspace_id,
        title=title,
        title_key=taxonomy_store.concept_keys(tx, [title])[title],
        search_run_id=run.run_id,
        requested_by=actor.actor_id,
        now=now,
    )
    return research_id


def _visible(
    tx: Tx, workspace_id: uuid.UUID, research_id: uuid.UUID, *, lock: bool = False
) -> role_store.ResearchRow:
    visible_workspace(tx, workspace_id)
    row = role_store.research(tx, workspace_id, research_id, lock=lock)
    if row is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such research.", stage=ErrorStage.EXECUTION
        )
    return row


def _proposal(tx: Tx, keyring: Keyring, run: Run) -> SearchProposal | None:
    """A complete search's proposal only: a cancelled or failed one's output is never used."""
    if run.status is not WorkState.COMPLETE:
        return None
    raw = open_output(tx, keyring, run)
    if raw is None:
        return None
    proposal = SearchProposal.model_validate_json(raw)
    return proposal if proposal.purpose is SearchPurpose.ROLE_RESEARCH else None


def pages_to_read(proposal: SearchProposal) -> list[str]:
    """Up to `MAX_PAGES` candidates: only pages the search really returned, never a site's
    home page (held here too for proposals sealed before the search excluded them), each
    still passing the fetch checks but the port's. The port is left, as a job acquisition's
    targets leave it (`acquisition.RECORDABLE_PORTS`), to the restricted worker's own fetch
    check: it refuses a port other than 80 or 443 as a blocked attempt, on record, and it
    alone knows a controlled test server's port. The search already excludes other ports."""
    urls: list[str] = []
    for candidate in proposal.candidates:
        if not candidate.grounded:
            continue
        checked = check_url(candidate.url, allowed_ports=RECORDABLE_PORTS)
        if (
            isinstance(checked, CheckedUrl)
            and not is_site_root(checked.url)
            and checked.url not in urls
        ):
            urls.append(checked.url)
    return urls[:MAX_PAGES]


def start_reading(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    research_id: uuid.UUID,
    *,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    now: datetime,
) -> bool:
    """The acquisition that reads the search's pages; False when one was started already (the
    same reading is returned, never a second). Refused until the search is complete, and when
    it proposed no page."""
    row = _visible(tx, workspace_id, research_id, lock=True)
    if row.reading_run_id is not None:
        return False
    search = visible_run(tx, workspace_id, row.search_run_id)
    proposal = _proposal(tx, keyring, search)
    if proposal is None:
        raise CareerwrightError(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "The search hasn't finished, so there are no pages to read yet.",
            stage=ErrorStage.EXECUTION,
        )
    urls = pages_to_read(proposal)
    if not urls:
        raise CareerwrightError(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "The search found no page Careerwright could read.",
            stage=ErrorStage.EXECUTION,
            details={"reason": "no_pages"},
        )
    run = submit_keyless_run(
        tx,
        actor,
        workspace_id,
        RunKind.ACQUISITION,
        runtime_mode=runtime_mode,
        workflow_name=run_store.ACQUISITION_WORKFLOW,
        now=now,
    )
    for position, url in enumerate(urls):
        store.insert_target(
            tx,
            run_id=run.run_id,
            workspace_id=workspace_id,
            position=position,
            route=InputRoute.FETCH,
            url=url,
            query=None,
            role_title=row.title,
        )
    role_store.set_reading(tx, research_id, run.run_id, now)
    return True


# --- the view ------------------------------------------------------------------------------


class ResearchState(StrEnum):
    """Where a research is. Only `found` and `not_yet_found` are results; neither says a role
    does or doesn't exist, only what Careerwright checked."""

    SEARCHING = "searching"
    SEARCH_STOPPED = "search_stopped"  # the search failed or was cancelled: its run says why
    NO_PAGES = "no_pages"  # the search proposed no page to read (`empty_reason` says why)
    READY_TO_READ = "ready_to_read"  # the search is done and its pages aren't being read yet
    READING = "reading"
    READING_STOPPED = "reading_stopped"  # failed or cancelled before the rule could say found
    FOUND = "found"  # on two independent sources, or one official page
    # In independent sources: the reading ended, not enough (its reason says whether every
    # page was read).
    NOT_YET_FOUND = "not_yet_found"


@dataclass(frozen=True)
class PageView:
    position: int
    url: str | None
    host: str | None
    status: AttemptStatus | None  # None: not tried yet
    reason: AttemptReason | None
    rights_class: RightsClass | None
    retrieved_at: datetime | None
    title_verified: bool | None  # None: the page wasn't read
    quote: str | None  # the page's own words around the title, where verified
    source: int | None  # which independent source it counts in (1, 2, ...), where verified


@dataclass(frozen=True)
class ResearchView:
    research: role_store.ResearchRow
    state: ResearchState
    search: Run
    reading: Run | None
    candidates: int
    empty_reason: SearchEmptyReason | None
    pages: list[PageView] = field(default_factory=list)
    corroboration: Corroboration | None = None

    @property
    def not_yet_found_reason(self) -> NotYetFoundReason | None:
        if self.state is not ResearchState.NOT_YET_FOUND or self.corroboration is None:
            return None
        return self.corroboration.reason


def _host(url: str | None) -> str | None:
    if url is None:
        return None
    return urlsplit(url).hostname


def _pages(tx: Tx, reading: Run) -> tuple[list[PageView], Corroboration]:
    targets = store.targets(tx, reading.run_id)
    last = {a.position: a for a in store.attempts_of_run(tx, reading.run_id)}
    checks = role_store.page_checks(tx, [a.attempt_id for a in last.values()])
    evidence = [
        PageEvidence(
            ref=str(a.attempt_id),
            host=a.provider,
            rights_class=RightsClass(a.rights_class) if a.rights_class else None,
            check=checks[a.attempt_id],
        )
        for t in targets
        if (a := last.get(t.position)) is not None and a.attempt_id in checks
    ]
    # A target with no check recorded (blocked, failed or not tried yet) wasn't read: never a
    # page without the title (`NotYetFoundReason.PAGES_UNREAD`).
    result = corroborate(evidence, unread=len(targets) - len(evidence))
    group_of = {ref: n for n, group in enumerate(result.groups, start=1) for ref in group}
    pages: list[PageView] = []
    for target in targets:
        attempt = last.get(target.position)
        check = checks.get(attempt.attempt_id) if attempt is not None else None
        pages.append(
            PageView(
                position=target.position,
                url=target.url,
                host=_host(target.url),
                status=attempt.status if attempt is not None else None,
                reason=attempt.reason if attempt is not None else None,
                rights_class=RightsClass(attempt.rights_class)
                if attempt is not None and attempt.rights_class
                else None,
                retrieved_at=attempt.finished_at
                if attempt is not None and attempt.status is AttemptStatus.SUCCEEDED
                else None,
                title_verified=check.verified if check is not None else None,
                quote=check.excerpt if check is not None else None,
                source=group_of.get(str(attempt.attempt_id)) if attempt is not None else None,
            )
        )
    return pages, result


def research_view(
    tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, row: role_store.ResearchRow
) -> ResearchView:
    search = visible_run(tx, workspace_id, row.search_run_id)
    proposal = _proposal(tx, keyring, search)

    def made(
        state: ResearchState,
        reading: Run | None = None,
        pages: list[PageView] | None = None,
        result: Corroboration | None = None,
    ) -> ResearchView:
        return ResearchView(
            research=row,
            state=state,
            search=search,
            reading=reading,
            candidates=len(proposal.candidates) if proposal else 0,
            empty_reason=proposal.empty_reason if proposal else None,
            pages=pages or [],
            corroboration=result,
        )

    if search.status not in _SETTLED:
        return made(ResearchState.SEARCHING)
    if proposal is None:
        return made(ResearchState.SEARCH_STOPPED)
    if row.reading_run_id is None:
        return made(
            ResearchState.READY_TO_READ if pages_to_read(proposal) else ResearchState.NO_PAGES
        )
    reading = visible_run(tx, workspace_id, row.reading_run_id)
    pages, result = _pages(tx, reading)
    if reading.status not in _SETTLED:
        state = ResearchState.READING
    elif result.verdict is RoleVerdict.FOUND:
        state = ResearchState.FOUND  # verified spans are a fact, however the reading ended
    elif reading.status is WorkState.COMPLETE:
        state = ResearchState.NOT_YET_FOUND
    else:
        state = ResearchState.READING_STOPPED
    return made(state, reading, pages, result)


def view(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, research_id: uuid.UUID) -> ResearchView:
    return research_view(tx, keyring, workspace_id, _visible(tx, workspace_id, research_id))


def views(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID) -> list[ResearchView]:
    visible_workspace(tx, workspace_id)
    return [
        research_view(tx, keyring, workspace_id, row)
        for row in role_store.researches(tx, workspace_id, LIST_LIMIT)
    ]
