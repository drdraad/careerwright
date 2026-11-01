"""Model extraction runs: started by the acquisition that fetched a page, and what an
accepted extraction records (Task 7A fix round 2, rulings 9-12; ADR 0009 decision 15).

Started in the transaction that records the page's attempt, for each retrieved, permitted
page whose structured data gave no posting (`records.MODEL_READABLE`), at most
`MAX_EXTRACTIONS_PER_ACQUISITION` per acquisition (the database holds the same cap). Each is
an ordinary model run, with its own outbox entry, workflow, reservation and repair bound, on
the workspace's own model and key, requested by the acquisition's requester; the restricted
acquisition worker never holds a key (GC8). A page not handed over (the cap, the spend
limits, no key, the test model with data not synthetic, a demo workspace, no visible text,
a cancelled acquisition) keeps its `extraction_not_run` reason and stays
`no_posting_readable`, never "none found". The reservation itself is the activity's: these
checks only avoid starting a run the activity would refuse. Each run records its
acquisition as `started_by_run`, so cancelling the acquisition cancels the runs it started
that have not settled (fix round 3, item 4; `identity.runs.cancel_run`).

Recorded in the transaction that accepts the run's output (`RunTask.record`): the postings,
as copies of the page's own attempt, through the shared recording path under the
workspace's recording lock, and what the run found (`page_extractions.outcome`).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from careerwright.db import Tx
from careerwright.evidence import extraction, store
from careerwright.evidence.acquire import AcquisitionResult
from careerwright.evidence.extraction import ExtractionInput, ExtractionProposal
from careerwright.evidence.recording import record_copies
from careerwright.evidence.records import MODEL_READABLE, AttemptStatus, ExtractionNotRun
from careerwright.identity import credential_store, run_store
from careerwright.identity import store as identity_store
from careerwright.identity.activity import run_worst_case_nano_usd
from careerwright.identity.keyring import Keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.model_registry import ModelEntry, ModelMode
from careerwright.identity.records import EventKind, Run, RunKind
from careerwright.identity.runs import input_context
from careerwright.identity.spend import period_start, refused_scope
from careerwright.vocabulary import DataMode, WorkState

MAX_EXTRACTIONS_PER_ACQUISITION = 5


@dataclass(frozen=True)
class ModelSpendEstimate:
    """The most an acquisition may spend on the person's key, shown before it starts
    (MODEL-08: "display estimated incremental cost before deep research"; fix round 3, item
    5), as two maxima, never an expected cost:
    - without a worker crash (fix round 4, item 4): at most `model_runs` extraction runs,
      each spending at most `per_run_nano_usd`, every attempt its retry owner (the DBOS
      step) may make at the reservation the activity takes for each;
    - the hard maximum, a crash included (fix round 5, re-review 2-C N1): DBOS gives a step
      interrupted by a crash fresh attempts, but the activity never reserves past the
      workspace's per-run spend limit, so `model_runs` times that limit."""

    model_id: str
    model_runs: int
    per_run_nano_usd: int
    worst_case_nano_usd: int
    hard_maximum_nano_usd: int


def acquisition_model_spend(
    models: ModelChoice, *, synthetic: bool, data_mode: DataMode, run_limit_nano_usd: int
) -> ModelSpendEstimate | None:
    """Deterministic: the cap times one extraction run's ceiling for the model the
    workspace's runs pin, from the functions the reservation uses
    (`activity.run_worst_case_nano_usd` over the task's `extraction.worst_case_nano_usd`), so
    the two cannot drift; and the cap times the workspace's run limit. None for a demo
    workspace, which never extracts."""
    if data_mode is DataMode.DEMO:
        return None
    model = models.for_workspace(synthetic=synthetic)
    per_run = run_worst_case_nano_usd(extraction.worst_case_nano_usd, model.model_id)
    return ModelSpendEstimate(
        model_id=model.model_id,
        model_runs=MAX_EXTRACTIONS_PER_ACQUISITION,
        per_run_nano_usd=per_run,
        worst_case_nano_usd=MAX_EXTRACTIONS_PER_ACQUISITION * per_run,
        hard_maximum_nano_usd=MAX_EXTRACTIONS_PER_ACQUISITION * run_limit_nano_usd,
    )


def _not_run(
    tx: Tx, run: Run, model: ModelEntry, text: str | None, now: datetime
) -> ExtractionNotRun | None:
    if run.data_mode is DataMode.DEMO:
        return ExtractionNotRun.DEMO_WORKSPACE
    if not text:
        return ExtractionNotRun.NO_VISIBLE_TEXT
    started = store.extractions_started(tx, run.run_id)
    if started >= MAX_EXTRACTIONS_PER_ACQUISITION:
        return ExtractionNotRun.CAP_REACHED
    permitted = model.mode is ModelMode.STANDARD or (
        model.mode is ModelMode.CONTRIBUTOR and run.synthetic
    )
    if not permitted:
        return ExtractionNotRun.MODEL_NOT_PERMITTED
    if credential_store.sealed_active_credential(tx, run.workspace_id) is None:
        return ExtractionNotRun.NO_MODEL_KEY
    limits = credential_store.spend_limits(tx, run.workspace_id)
    worst_case = extraction.worst_case_nano_usd(model.model_id)
    committed, _ = run_store.committed_spend(tx, run.workspace_id, run.run_id, period_start(now))
    # The committed spend holds every reservation made; this acquisition's started runs that
    # have made none yet will, so they count as if (only they: review C M3).
    unreserved = store.extractions_unreserved(tx, run.run_id)
    if limits is None or refused_scope(
        limits[0],
        period_committed=committed + unreserved * worst_case,
        run_committed=0,
        worst_case=worst_case,
    ):
        return ExtractionNotRun.BUDGET_EXCEEDED
    return None


def model_readable(result: AcquisitionResult) -> bool:
    """Whether a recorded page goes to model extraction (or records why it does not): it was
    retrieved and its structured data gave no posting."""
    return result.status is AttemptStatus.SUCCEEDED and result.extraction in MODEL_READABLE


def start_extraction(
    tx: Tx,
    keyring: Keyring,
    models: ModelChoice,
    run: Run,
    attempt_id: uuid.UUID,
    result: AcquisitionResult,
    now: datetime,
) -> None:
    """Worker, in the acquisition's recording transaction: for a page model extraction may
    read, its extraction run, or the reason none is started. That transaction holds the
    acquisition's cancellation lock, taken as its first lock (`run_store.lock_started_runs`;
    `acquisition.acquire_target`), so a cancel either sees this run once it is started, or
    is seen here (fix round 3, item 4; review C-1 N1)."""
    if not model_readable(result):
        return
    current = run_store.run(tx, run.run_id)
    model = models.for_workspace(synthetic=run.synthetic)
    if current is None or current.cancel_requested_at is not None:
        reason: ExtractionNotRun | None = ExtractionNotRun.ACQUISITION_CANCELLED
    else:
        reason = _not_run(tx, run, model, result.extraction_text, now)
    if reason is not None or result.extraction_text is None:
        store.insert_extraction_not_run(
            tx,
            attempt_id=attempt_id,
            workspace_id=run.workspace_id,
            acquisition_run_id=run.run_id,
            reason=reason or ExtractionNotRun.NO_VISIBLE_TEXT,
        )
        return
    context = ExtractionInput(text=result.extraction_text)
    extraction_run = uuid.uuid4()
    store.submit_extraction(
        tx,
        attempt_id=attempt_id,
        run_id=extraction_run,
        model_id=model.model_id,
        model_mode=model.mode.value,
        sealed=keyring.seal(
            context.model_dump_json().encode(), input_context(run.workspace_id, extraction_run)
        ),
        text_sha256=context.sha256,
    )
    identity_store.append_event(
        tx,
        run.workspace_id,
        EventKind.RUN_STATE_CHANGED,
        str(extraction_run),
        state=WorkState.QUEUED,
        detail={"kind": RunKind.PAGE_EXTRACTION.value},
    )


def record_extraction(tx: Tx, _keyring: Keyring, run: Run, output: BaseModel) -> None:
    """Worker, in the transaction that accepts the extraction's output (`RunTask.record`):
    its postings as copies of the page's attempt, and what it found. Raises when the page
    is not on record, so nothing is accepted."""
    if not isinstance(output, ExtractionProposal):
        raise TypeError("a page extraction's output is its checked proposal")
    link = store.extraction_of_run(tx, run.run_id)
    page = None if link is None else store.attempt(tx, link.attempt_id)
    if link is None or page is None:
        raise LookupError("the extraction's page is not on record")
    store.lock_workspace_records(tx, run.workspace_id)
    record_copies(
        tx,
        workspace_id=run.workspace_id,
        attempt_id=page.attempt_id,
        provider=page.provider,
        copies=output.postings,
        at=page.finished_at or page.started_at,
    )
    store.set_extraction_outcome(tx, run.run_id, output.outcome)
    identity_store.append_event(
        tx,
        run.workspace_id,
        EventKind.RESEARCH_UPDATED,
        str(link.acquisition_run_id),
        detail={} if page.position is None else {"position": page.position},
    )
