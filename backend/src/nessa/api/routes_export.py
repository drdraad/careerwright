"""Workspace data export (portability). Credentials appear as metadata only, never key
material; the export is built from the same row-level-secured reads as every other view, in
one transaction, and pages through every row (an export is never silently truncated)."""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import Field

from nessa.api.catalogue_schemas import ProvisionalConceptOut
from nessa.api.deps import CallerDep, Deps
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.interview_schemas import TurnOut
from nessa.api.routes_interview import turn_out
from nessa.api.routes_runs import run_out
from nessa.api.schemas import (
    CredentialOut,
    EventOut,
    ProfileOut,
    ResponseModel,
    RunOut,
    SourceOut,
    SpendOut,
    WorkspaceOut,
)
from nessa.catalogue import taxonomy_store
from nessa.catalogue.records import ProvisionalConcept
from nessa.db import Tx, actor_transaction
from nessa.identity import credential_store, run_store
from nessa.identity import store as identity_store
from nessa.identity.keyring import Keyring
from nessa.identity.records import Run, WorkspaceEvent
from nessa.identity.spend_limits import spend_summary
from nessa.identity.workspaces import visible_workspace
from nessa.profile import interview_store
from nessa.profile import store as profile_store
from nessa.profile.conversation import turn_view
from nessa.profile.records import InterviewTurn, ProfileVersion, SourceReference

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["export"]
)
PAGE = 500


class WorkspaceExport(ResponseModel):
    format: Literal["nessa.workspace-export"] = "nessa.workspace-export"
    format_version: Literal[2] = 2
    exported_at: datetime
    synthetic: bool
    workspace: WorkspaceOut
    profile_versions: list[ProfileOut]
    sources: list[SourceOut]
    events: list[EventOut]
    credentials: list[CredentialOut]
    runs: list[RunOut]
    interview_turns: list[TurnOut] = Field(description="Oldest first.")
    provisional_concepts: list[ProvisionalConceptOut]
    spend: SpendOut


def _all_runs(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID) -> list[RunOut]:
    runs: list[Run] = []
    while page := run_store.runs(
        tx,
        workspace_id,
        before=(runs[-1].created_at, runs[-1].run_id) if runs else None,
        limit=PAGE,
    ):
        runs.extend(page)
    return [run_out(tx, keyring, run) for run in reversed(runs)]


def _all_versions(tx: Tx, workspace_id: uuid.UUID) -> list[ProfileVersion]:
    versions: list[ProfileVersion] = []
    while page := profile_store.list_profile_versions(
        tx, workspace_id, before=versions[-1].version if versions else None, limit=PAGE
    ):
        versions.extend(page)
    return list(reversed(versions))


def _all_sources(tx: Tx, workspace_id: uuid.UUID) -> list[SourceReference]:
    sources: list[SourceReference] = []
    while page := profile_store.list_sources(
        tx,
        workspace_id,
        after=(sources[-1].created_at, sources[-1].source_ref_id) if sources else None,
        limit=PAGE,
    ):
        sources.extend(page)
    return sources


def _all_turns(tx: Tx, keyring: Keyring, workspace_id: uuid.UUID) -> list[TurnOut]:
    turns: list[InterviewTurn] = []
    while page := interview_store.turns(
        tx,
        workspace_id,
        before=(turns[-1].created_at, turns[-1].turn_id) if turns else None,
        limit=PAGE,
    ):
        turns.extend(page)
    return [turn_out(tx, keyring, turn_view(tx, keyring, t)) for t in reversed(turns)]


def _all_concepts(tx: Tx, workspace_id: uuid.UUID) -> list[ProvisionalConcept]:
    concepts: list[ProvisionalConcept] = []
    while page := taxonomy_store.provisional_concepts(
        tx,
        workspace_id,
        after=(concepts[-1].created_at, concepts[-1].concept_id) if concepts else None,
        limit=PAGE,
    ):
        concepts.extend(page)
    return concepts


def _all_events(tx: Tx, workspace_id: uuid.UUID) -> list[WorkspaceEvent]:
    events: list[WorkspaceEvent] = []
    while page := identity_store.events_after(
        tx, workspace_id, events[-1].seq if events else 0, PAGE
    ):
        events.extend(page)
    return events


@router.get("/export", response_model=WorkspaceExport)
def export_workspace(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> WorkspaceExport:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        workspace = visible_workspace(tx, workspace_id)
        versions = _all_versions(tx, workspace_id)
        sources = _all_sources(tx, workspace_id)
        events = _all_events(tx, workspace_id)
        credentials = credential_store.credentials(tx, workspace_id)
        runs = _all_runs(tx, deps.keyring, workspace_id)
        turns = _all_turns(tx, deps.keyring, workspace_id)
        concepts = _all_concepts(tx, workspace_id)
        spend = spend_summary(tx, workspace_id, deps.clock(), deps.spend_defaults)
    return WorkspaceExport(
        exported_at=deps.clock(),
        synthetic=workspace.synthetic,
        workspace=WorkspaceOut.of(workspace),
        profile_versions=[ProfileOut.of_version(v) for v in versions],
        sources=[SourceOut.of(s) for s in sources],
        events=[EventOut.of(e) for e in events],
        credentials=[CredentialOut.of(c) for c in credentials],
        runs=runs,
        interview_turns=turns,
        provisional_concepts=[ProvisionalConceptOut.of(c) for c in concepts],
        spend=SpendOut.of(spend),
    )
