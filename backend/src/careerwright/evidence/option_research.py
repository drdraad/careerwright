"""One bounded search and page reading for a confirmed target's options."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pydantic import Field

from careerwright.config import RuntimeMode
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import option_store, store
from careerwright.evidence.acquisition import MAX_OPTION_PAGES, RECORDABLE_PORTS
from careerwright.evidence.addresses import CheckedUrl, check_url
from careerwright.evidence.records import (
    AttemptStatus,
    ExtractionOutcome,
    InputRoute,
    RightsClass,
    StrictModel,
)
from careerwright.evidence.search import (
    OPTION_SEARCH,
    OptionSearchInput,
    SearchEmptyReason,
    SearchProposal,
    SearchPurpose,
    option_prompt_bytes,
    role_page_refusal,
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
from careerwright.profile.document import FieldState
from careerwright.profile.store import stale_version
from careerwright.vocabulary import WorkState

LIST_LIMIT = 20
SETTLED = frozenset(
    {
        WorkState.COMPLETE,
        WorkState.FAILED,
        WorkState.CANCELLED,
        WorkState.PROVIDER_UNAVAILABLE,
    }
)


class StartOptionResearch(StrictModel):
    expected_profile_version: int = Field(ge=0)
    target: str = Field(min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=120)


class ResearchStatus(StrEnum):
    SEARCHING = "searching"
    SEARCH_STOPPED = "search_stopped"
    NO_PAGES = "no_pages"
    READY_TO_READ = "ready_to_read"
    READING = "reading"
    COMPLETED = "completed"
    READING_STOPPED = "reading_stopped"


class OptionResearchCoverage(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    STOPPED = "stopped"
    NONE_READ = "none_read"


@dataclass(frozen=True)
class ResearchView:
    research: option_store.ResearchRow
    status: ResearchStatus
    coverage: OptionResearchCoverage
    search: Run
    reading: Run | None
    candidates: int
    empty_reason: SearchEmptyReason | None
    pages_attempted: int
    pages_read: int
    pages_blocked: int
    pages_failed: int
    failure_reason: str | None
    records: list[option_store.RecordRow]


def _confirmed(values: list[str] | None, wanted: str) -> str | None:
    return next((v for v in values or [] if v.casefold() == wanted.strip().casefold()), None)


def start_research(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: StartOptionResearch,
    *,
    models: ModelChoice,
    keyring: Keyring,
    runtime_mode: RuntimeMode,
    defaults: SpendLimits,
    now: datetime,
) -> uuid.UUID:
    profile = current_profile(tx, workspace_id)
    if command.expected_profile_version != profile.version:
        raise stale_version(profile.version)
    document = profile.document
    targets = (
        document.target_titles.value
        if document.target_titles.state is FieldState.PROVIDED
        else None
    )
    cities = document.cities.value if document.cities.state is FieldState.PROVIDED else None
    target = _confirmed(targets, command.target)
    city = _confirmed(cities, command.city)
    if target is None or city is None:
        raise CareerwrightError(
            ErrorCode.CONFIRMATION_REQUIRED,
            "Choose one of your target roles and one of your cities.",
            stage=ErrorStage.PROFILE,
            details={
                "fields": [
                    name
                    for name, value in (("target_titles", target), ("cities", city))
                    if value is None
                ]
            },
        )
    context = OptionSearchInput(profile_version=profile.version, target=target, city=city)
    if option_prompt_bytes(context) > OPTION_SEARCH.max_prompt_bytes:
        raise CareerwrightError(
            ErrorCode.LIMIT_EXCEEDED,
            "That role or city name is too long to search for.",
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
    option_store.insert_research(
        tx,
        research_id=research_id,
        workspace_id=workspace_id,
        target=target,
        city=city,
        search_run_id=run.run_id,
        now=now,
    )
    return research_id


def _visible(
    tx: Tx, workspace_id: uuid.UUID, research_id: uuid.UUID, *, lock: bool = False
) -> option_store.ResearchRow:
    visible_workspace(tx, workspace_id)
    row = option_store.research(tx, workspace_id, research_id, lock=lock)
    if row is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such option research.", stage=ErrorStage.EXECUTION
        )
    return row


def _proposal(tx: Tx, keyring: Keyring, run: Run) -> SearchProposal | None:
    if run.status is not WorkState.COMPLETE:
        return None
    raw = open_output(tx, keyring, run)
    if raw is None:
        return None
    proposal = SearchProposal.model_validate_json(raw)
    return proposal if proposal.purpose is SearchPurpose.OPTION_RESEARCH else None


def pages_to_read(proposal: SearchProposal) -> list[str]:
    urls: list[str] = []
    for candidate in proposal.candidates:
        checked = check_url(candidate.url, allowed_ports=RECORDABLE_PORTS)
        if (
            candidate.grounded
            and isinstance(checked, CheckedUrl)
            and role_page_refusal(checked.url, proposal.target) is None
            and checked.url not in urls
        ):
            urls.append(checked.url)
    return urls[:MAX_OPTION_PAGES]


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
    row = _visible(tx, workspace_id, research_id, lock=True)
    if row.reading_run_id is not None:
        return False
    search = visible_run(tx, workspace_id, row.search_run_id)
    proposal = _proposal(tx, keyring, search)
    if proposal is None:
        raise CareerwrightError(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "The search has not finished, so there are no pages to read yet.",
            stage=ErrorStage.EXECUTION,
        )
    urls = pages_to_read(proposal)
    if not urls:
        raise CareerwrightError(
            ErrorCode.PROPOSAL_NOT_AVAILABLE,
            "This search found no page Careerwright could read.",
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
            option_research_id=research_id,
        )
    option_store.set_reading(tx, research_id, run.run_id, now)
    return True


def research_view(
    tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, row: option_store.ResearchRow
) -> ResearchView:
    search = visible_run(tx, workspace_id, row.search_run_id)
    proposal = _proposal(tx, keyring, search)
    reading = visible_run(tx, workspace_id, row.reading_run_id) if row.reading_run_id else None
    targets = store.targets(tx, reading.run_id) if reading else []
    attempts = {a.position: a for a in store.attempts_of_run(tx, reading.run_id)} if reading else {}
    attempted = sum(1 for target in targets if target.position in attempts)
    extractions = store.extractions_of_attempts(tx, [a.attempt_id for a in attempts.values()])
    extraction_pending = any(
        e.run_id is not None and e.run_status not in SETTLED for e in extractions.values()
    )
    extraction_failed = any(
        e.run_status in (WorkState.FAILED, WorkState.CANCELLED, WorkState.PROVIDER_UNAVAILABLE)
        or e.outcome is ExtractionOutcome.OPTIONS_UNVERIFIED
        for e in extractions.values()
    )
    extraction_not_run = any(e.not_run is not None for e in extractions.values())
    read = sum(
        1
        for target in targets
        if (a := attempts.get(target.position)) is not None
        and a.status is AttemptStatus.SUCCEEDED
        and a.rights_class is not None
        and a.rights_class not in (RightsClass.OTHER.value, RightsClass.JOB_BOARD.value)
    )
    blocked = sum(
        1
        for a in attempts.values()
        if a.status is AttemptStatus.BLOCKED
        or a.rights_class in (RightsClass.OTHER.value, RightsClass.JOB_BOARD.value)
    )
    failed = sum(1 for a in attempts.values() if a.status is AttemptStatus.FAILED)
    if search.status not in SETTLED:
        status = ResearchStatus.SEARCHING
    elif proposal is None:
        status = ResearchStatus.SEARCH_STOPPED
    elif not pages_to_read(proposal):
        status = ResearchStatus.NO_PAGES
    elif reading is None:
        status = ResearchStatus.READY_TO_READ
    elif reading.status not in SETTLED or extraction_pending:
        status = ResearchStatus.READING
    elif reading.status is WorkState.COMPLETE:
        status = ResearchStatus.COMPLETED
    else:
        status = ResearchStatus.READING_STOPPED
    if status in (ResearchStatus.SEARCH_STOPPED, ResearchStatus.READING_STOPPED):
        coverage = OptionResearchCoverage.STOPPED
    elif status is ResearchStatus.NO_PAGES or (reading and reading.status in SETTLED and read == 0):
        coverage = OptionResearchCoverage.NONE_READ
    elif (
        status is ResearchStatus.COMPLETED
        and blocked == 0
        and failed == 0
        and not extraction_failed
        and not extraction_not_run
        and all(t.status != "not_needed" for t in targets)
    ):
        coverage = OptionResearchCoverage.COMPLETE
    else:
        coverage = OptionResearchCoverage.PARTIAL
    return ResearchView(
        research=row,
        status=status,
        coverage=coverage,
        search=search,
        reading=reading,
        candidates=len(proposal.candidates) if proposal else 0,
        empty_reason=proposal.empty_reason if proposal else None,
        pages_attempted=attempted,
        pages_read=read,
        pages_blocked=blocked,
        pages_failed=failed,
        failure_reason=(
            reading.failure_class
            if reading and reading.failure_class
            else next((e.failure_class for e in extractions.values() if e.failure_class), None)
            or search.failure_class
        ),
        records=option_store.records(tx, workspace_id, row.research_id),
    )


def view(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, research_id: uuid.UUID) -> ResearchView:
    return research_view(tx, keyring, workspace_id, _visible(tx, workspace_id, research_id))


def views(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID) -> list[ResearchView]:
    visible_workspace(tx, workspace_id)
    return [
        research_view(tx, keyring, workspace_id, row)
        for row in option_store.researches(tx, workspace_id, LIST_LIMIT)
    ]
