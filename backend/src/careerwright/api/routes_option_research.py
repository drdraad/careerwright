"""Find proposed course and funding records for one confirmed target."""

import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.api.option_schemas import (
    OptionResearchEstimateOut,
    OptionResearchOut,
    OptionResearchRecordOut,
)
from careerwright.api.routes_runs import run_out
from careerwright.db import Tx, actor_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import extraction, option_research, search
from careerwright.evidence.extraction_runs import acquisition_model_spend
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.identity.records import RunKind
from careerwright.identity.spend import BudgetScope, budget_exceeded
from careerwright.identity.spend_limits import run_estimate, spend_summary
from careerwright.identity.workspaces import visible_workspace

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}/option-research",
    responses=ERROR_RESPONSES,
    tags=["option-research"],
)


def _estimate(tx: Tx, workspace_id: uuid.UUID, deps: Deps) -> OptionResearchEstimateOut:
    now = deps.clock()
    search_estimate = run_estimate(
        tx,
        workspace_id,
        RunKind.SOURCE_SEARCH,
        search.worst_case_nano_usd,
        models=deps.models,
        now=now,
        defaults=deps.spend_defaults,
    )
    summary = spend_summary(tx, workspace_id, now, deps.spend_defaults)
    workspace = visible_workspace(tx, workspace_id)
    pages = acquisition_model_spend(
        deps.models,
        synthetic=workspace.synthetic,
        data_mode=workspace.data_mode,
        run_limit_nano_usd=summary.limits.run_limit_nano_usd,
    )
    if pages is None:
        raise CareerwrightError(
            ErrorCode.MODE_NOT_SUPPORTED,
            "Option research is unavailable in demo workspaces.",
            stage=ErrorStage.EXECUTION,
        )
    combined = search_estimate.per_run_nano_usd + pages.worst_case_nano_usd
    refused = search_estimate.refused_scope
    if (
        refused is None
        and extraction.worst_case_nano_usd(search_estimate.model.model_id)
        > summary.limits.run_limit_nano_usd
    ):
        refused = BudgetScope.RUN
    if (
        refused is None
        and summary.period_committed_nano_usd + combined > summary.limits.period_limit_nano_usd
    ):
        refused = BudgetScope.PERIOD
    return OptionResearchEstimateOut(
        model_id=search_estimate.model.model_id,
        model_mode=search_estimate.model.mode,
        search_maximum_nano_usd=search_estimate.per_run_nano_usd,
        pages_maximum_nano_usd=pages.worst_case_nano_usd,
        combined_maximum_nano_usd=combined,
        hard_maximum_nano_usd=search_estimate.hard_maximum_nano_usd + pages.hard_maximum_nano_usd,
        refused_scope=refused,
    )


@router.get(
    "/estimate", response_model=OptionResearchEstimateOut, operation_id="estimate_option_research"
)
def estimate_option_research(
    workspace_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> OptionResearchEstimateOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return _estimate(tx, workspace_id, deps)


def _out(tx: Tx, deps: Deps, workspace_id: uuid.UUID, research_id: uuid.UUID) -> OptionResearchOut:
    view = option_research.view(tx, deps.keyring, workspace_id, research_id)
    records = []
    now = deps.clock()
    for row in view.records:
        concept = row.catalogue.concepts[0] if row.catalogue.concepts else None
        offering = row.catalogue.offerings[0] if row.catalogue.offerings else None
        instrument = row.catalogue.instruments[0] if row.catalogue.instruments else None
        citations = {}
        if concept:
            if concept.cited:
                citations["title"] = concept.cited
            citations.update({fact.field: fact.cited for fact in concept.facts if fact.cited})
        if offering:
            citations.update({fact.field: fact.cited for fact in offering.facts if fact.cited})
        if instrument:
            citations.update(
                {
                    fact.field: fact.cited
                    for fact in [*instrument.rules, *instrument.facts]
                    if fact.cited
                }
            )
        records.append(
            OptionResearchRecordOut(
                record_id=row.record_id,
                kind=(
                    "funding"
                    if instrument
                    else "apprenticeship"
                    if concept and concept.kind.value == "apprenticeship"
                    else "course"
                ),
                title=concept.title
                if concept and concept.title
                else instrument.programme
                if instrument and instrument.programme
                else "Unnamed record",
                source_url=row.source_url,
                retrieved_on=row.retrieved_at,
                expires_on=row.expires_at,
                expired=row.expires_at <= now,
                citations=citations,
            )
        )
    return OptionResearchOut(
        research_id=research_id,
        target=view.research.target,
        city=view.research.city,
        status=view.status,
        coverage=view.coverage,
        search=run_out(tx, deps.keyring, view.search),
        reading=run_out(tx, deps.keyring, view.reading) if view.reading else None,
        candidates=view.candidates,
        empty_reason=view.empty_reason,
        pages_attempted=view.pages_attempted,
        pages_read=view.pages_read,
        pages_blocked=view.pages_blocked,
        pages_failed=view.pages_failed,
        failure_reason=view.failure_reason,
        records=records,
    )


def _receipt(research_id: uuid.UUID) -> dict[str, object]:
    return {"research_id": str(research_id)}


def _answer(
    workspace_id: uuid.UUID, caller: CallerDep, deps: Deps, status: int, receipt: dict[str, object]
) -> JSONResponse:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        out = _out(tx, deps, workspace_id, uuid.UUID(str(receipt["research_id"])))
    return JSONResponse(out.model_dump(mode="json"), status_code=status)


@router.post(
    "", status_code=202, response_model=OptionResearchOut, operation_id="start_option_research"
)
def start_option_research(
    workspace_id: uuid.UUID,
    body: option_research.StartOptionResearch,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        estimate = _estimate(tx, workspace_id, deps)
        if estimate.refused_scope is not None:
            raise budget_exceeded(estimate.refused_scope)
        research_id = option_research.start_research(
            tx,
            caller.actor,
            workspace_id,
            body,
            models=deps.models,
            keyring=deps.keyring,
            runtime_mode=deps.settings.runtime_mode,
            defaults=deps.spend_defaults,
            now=deps.clock(),
        )
        return CommandResult(202, _receipt(research_id), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, receipt = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "start_option_research",
        fingerprint("start_option_research", request),
        execute,
    )
    return _answer(workspace_id, caller, deps, status, receipt)


@router.get("", response_model=list[OptionResearchOut], operation_id="list_option_research")
def list_option_research(
    workspace_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> list[OptionResearchOut]:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return [
            _out(tx, deps, workspace_id, view.research.research_id)
            for view in option_research.views(tx, deps.keyring, workspace_id)
        ]


@router.get("/{research_id}", response_model=OptionResearchOut, operation_id="get_option_research")
def get_option_research(
    workspace_id: uuid.UUID, research_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> OptionResearchOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return _out(tx, deps, workspace_id, research_id)


@router.post(
    "/{research_id}/reading",
    status_code=202,
    response_model=OptionResearchOut,
    operation_id="read_option_pages",
)
def read_option_pages(
    workspace_id: uuid.UUID,
    research_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        started = option_research.start_reading(
            tx,
            caller.actor,
            workspace_id,
            research_id,
            keyring=deps.keyring,
            runtime_mode=deps.settings.runtime_mode,
            now=deps.clock(),
        )
        return CommandResult(202 if started else 200, _receipt(research_id), workspace_id)

    request = {"workspace_id": str(workspace_id), "research_id": str(research_id)}
    status, receipt = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "read_option_pages",
        fingerprint("read_option_pages", request),
        execute,
    )
    return _answer(workspace_id, caller, deps, status, receipt)
