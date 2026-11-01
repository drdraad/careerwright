"""Route solves, worker side (Task 13b; ADR 0016's Task 13b amendment): one bounded activity per
execution, run by the route solve's DBOS step (`careerwright.planning.workflow`).

Solves run one at a time in the worker. The search is CPU-bound Python on a wall clock, so two
at once would share one interpreter and either could stop at its 30 seconds where it would
finish alone. An execution waits its turn before it marks its run running or records an
attempt, so its run stays queued meanwhile and its clocks start only when it runs; it stops
waiting once the person cancels.

Under the worker role and row-level security scoped to the run, the activity:
1. ends at once for a run the person cancelled, and returns the stored result of a run that
   stored one before a crash (it is never solved twice into two results);
2. marks every attempt a predecessor left unfinished `interrupted` (a crash, or a store that
   went away): never a truncated result. L0 keeps no checkpoint (spec section 22), so the
   solve starts again from the start under a new attempt ID; a run makes at most
   `SOLVE_MAX_ATTEMPTS`, then fails;
3. re-checks that the requester still owns the workspace and is invited, opens the sealed
   snapshot and records the attempt;
4. runs the search stage, records the rank stage's start (`stage`), runs the rank stage, and
   stores the ranked result sealed, its facts and the attempt's end in one transaction.

The search is pure and reads nothing else: no model, key, network or other table. A cancel
reaches it at its next check: the person's request is read every `CANCEL_POLL_S` on a thread
of its own (`cancel_watch`), never on the search's clock, and a cancelled search stores
nothing. The rank stage reaching its own limit fails the run
`rank_limit_reached`, never a result without its ranks. A store outage is transient: the DBOS
step re-runs the activity, which solves again (a solve costs nothing). Everything else fails
the run `unknown_failure`, named by class only.

However a run ends, its publication settles any attempt still unfinished in the same
transaction (`settle_attempts`), so no attempt reads as running once its run has ended.
"""

import hashlib
import logging
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from careerwright.db import StoreUnavailableError, Tx, run_transaction
from careerwright.identity import run_store
from careerwright.identity import store as identity_store
from careerwright.identity.activity import ActivityRuntime, Outcome, cancelled, failed, succeeded
from careerwright.identity.failures import STORE_LABEL, FailureClass, classify_failure
from careerwright.identity.keyring import SealedValue
from careerwright.identity.records import EventKind, Run, RunKind
from careerwright.identity.runs import input_context, output_context
from careerwright.planning import store
from careerwright.planning.search import (
    RankLimitReachedError,
    SearchCancelledError,
    SearchResult,
    rank_archive,
    search_archive,
)
from careerwright.planning.solve_records import AttemptOutcome, SolveSnapshot, SolveStage
from careerwright.vocabulary import WorkState

SOLVE_MAX_ATTEMPTS = 3  # executions of one solve, its restarts after a crash included
CANCEL_POLL_S = 0.2  # how often a running search reads whether the person cancelled
_log = logging.getLogger("careerwright.route_solve")
# This worker's one solve slot. L0 runs one worker process; a second would need a DBOS queue.
_ONE_AT_A_TIME = threading.Lock()


@dataclass(frozen=True)
class SolveRuntime:
    """Composition-root dependencies: the activity runtime's engine and keyring, and the clock
    the search's and the rank stage's limits read."""

    activity: ActivityRuntime
    clock: Callable[[], float] = time.monotonic


@dataclass(frozen=True)
class SolveEnd:
    label: str  # how the execution ended, for the log
    outcome: Outcome | None  # None: transient; the DBOS step runs it again


@dataclass(frozen=True)
class _Ready:
    run: Run
    attempt_id: int
    sealed: SealedValue


def _failed(failure: FailureClass, label: str | None = None) -> SolveEnd:
    return SolveEnd(label or failure.value, failed(failure))


def _prepare(rt: SolveRuntime, run_id: uuid.UUID) -> _Ready | SolveEnd:
    with run_transaction(rt.activity.engine, run_id) as tx:
        run = run_store.run(tx, run_id, lock=True)  # the transaction's first lock
        if run is None or run.kind is not RunKind.ROUTE_SOLVE:
            return _failed(FailureClass.UNKNOWN_FAILURE)
        if run.status is WorkState.CANCELLED or run.cancel_requested_at is not None:
            return SolveEnd("cancelled", cancelled())
        stored = run_store.accepted_output(tx, run_id)
        if stored is not None:  # stored, then a crash before it was published
            return SolveEnd("reused_result", succeeded(stored))
        if run_store.mark_running(tx, run_id):
            identity_store.append_event(
                tx,
                run.workspace_id,
                EventKind.RUN_STATE_CHANGED,
                str(run_id),
                state=WorkState.RUNNING,
            )
        store.end_unfinished_solve_attempts(tx, run_id, AttemptOutcome.INTERRUPTED)
        if len(store.solve_attempts(tx, run_id)) >= SOLVE_MAX_ATTEMPTS:
            return _failed(FailureClass.UNKNOWN_FAILURE, "attempts_exhausted")
        if run_store.authorised_workspace(tx) != run.workspace_id:
            return _failed(FailureClass.ACCESS_REVOKED)
        sealed = run_store.sealed_input(tx, run_id)
        if sealed is None:
            return _failed(FailureClass.UNKNOWN_FAILURE, "snapshot_missing")
        attempt_id = store.insert_solve_attempt(tx, run)
    return _Ready(run, attempt_id, sealed)


def _cancel_requested(rt: SolveRuntime, run_id: uuid.UUID) -> bool:
    """Whether the person asked to cancel the run (or it is gone), read from the store."""
    with run_transaction(rt.activity.engine, run_id) as tx:
        run = run_store.run(tx, run_id)
    return run is None or run.cancel_requested_at is not None


@contextmanager
def cancel_watch(read: Callable[[], bool]) -> Iterator[Callable[[], bool]]:
    """The search's cancel check, true for good once the person has cancelled. A daemon thread
    calls `read` every `CANCEL_POLL_S` and sets an event; the check reads only the event. So
    the search never waits on the store, and a slow store is never charged to its clock or the
    rank stage's. A failed read is never a cancel: it is logged by class, once per run of
    failures, and tried again at the next poll (the worker loop still publishes a cancelled
    run `cancelled`)."""
    requested = threading.Event()
    ended = threading.Event()

    def watch() -> None:
        failing = False
        while not ended.is_set():
            try:
                if read():
                    requested.set()
                    return
                failing = False
            except Exception as error:
                if not failing:
                    _log.warning(
                        "route solve cancel read failed",
                        extra={"error_class": type(error).__name__},
                    )
                failing = True
            ended.wait(CANCEL_POLL_S)

    threading.Thread(target=watch, name="route-solve-cancel-watch", daemon=True).start()
    try:
        yield requested.is_set
    finally:
        ended.set()


def settle_attempts(tx: Tx, run_id: uuid.UUID, status: WorkState) -> None:
    """Publication's part for a route solve (`ActivityRuntime.settle_attempts`), in the
    transaction that ends its run: an attempt still unfinished is settled, so none reads as
    running once the run has ended. On a cancelled run it is `cancelled` (its search stops at
    its next check, or its worker is gone); on any other, `interrupted`: it never finished
    (its store went away, its result could not be stored, or its worker stopped)."""
    outcome = (
        AttemptOutcome.CANCELLED if status is WorkState.CANCELLED else AttemptOutcome.INTERRUPTED
    )
    store.end_unfinished_solve_attempts(tx, run_id, outcome)


def _finish(rt: SolveRuntime, ready: _Ready, outcome: AttemptOutcome) -> None:
    with run_transaction(rt.activity.engine, ready.run.run_id) as tx:
        store.finish_solve_attempt(tx, ready.attempt_id, outcome)


def _ranking(rt: SolveRuntime, ready: _Ready) -> None:
    """The search stage has ended: the attempt is in its rank stage, for anyone reading it."""
    with run_transaction(rt.activity.engine, ready.run.run_id) as tx:
        store.set_solve_stage(tx, ready.attempt_id, SolveStage.RANKING)


def _store(rt: SolveRuntime, ready: _Ready, result: SearchResult) -> SolveEnd:
    run, keyring = ready.run, rt.activity.keyring
    body = result.model_dump_json().encode()
    with run_transaction(rt.activity.engine, run.run_id) as tx:
        if run_store.authorised_workspace(tx) != run.workspace_id:  # revoked while it ran
            store.finish_solve_attempt(tx, ready.attempt_id, AttemptOutcome.FAILED)
            return _failed(FailureClass.ACCESS_REVOKED)
        output_id = uuid.uuid4()
        accepted, newly = run_store.insert_output(
            tx,
            output_id=output_id,
            run=run,
            sealed=keyring.seal(body, output_context(run.workspace_id, output_id)),
            content_sha256=hashlib.sha256(body).hexdigest(),
        )
        if newly:
            store.insert_solve_result(tx, run, ready.attempt_id, accepted, result)
        store.finish_solve_attempt(tx, ready.attempt_id, AttemptOutcome.SUCCEEDED)
    return SolveEnd("succeeded" if newly else "reused_result", succeeded(accepted))


def _solve(rt: SolveRuntime, ready: _Ready, stop: Callable[[], bool]) -> SolveEnd:
    run = ready.run
    ended: AttemptOutcome | None = None
    label = ""
    try:
        context = input_context(run.workspace_id, run.run_id)
        snapshot = SolveSnapshot.model_validate_json(
            rt.activity.keyring.open(ready.sealed, context)
        )
        archive = search_archive(
            snapshot.monthly, limits=snapshot.limits, clock=rt.clock, cancelled=stop
        )
        _ranking(rt, ready)
        result = rank_archive(
            archive, clock=rt.clock, cancelled=stop, limit_seconds=snapshot.rank_seconds
        )
    except SearchCancelledError:
        ended = AttemptOutcome.CANCELLED
    except RankLimitReachedError:
        ended = AttemptOutcome.RANK_LIMIT_REACHED
    except StoreUnavailableError:
        raise  # transient: the attempt stays unfinished and the next execution interrupts it
    except Exception as error:
        # Classified inside the handler, acted on outside it: nothing rides along as context.
        label, ended = classify_failure(error).label, AttemptOutcome.FAILED
    if ended is None:
        return _store(rt, ready, result)
    _finish(rt, ready, ended)
    if ended is AttemptOutcome.CANCELLED:
        return SolveEnd("cancelled", cancelled())
    if ended is AttemptOutcome.RANK_LIMIT_REACHED:
        return _failed(FailureClass.RANK_LIMIT_REACHED)
    return _failed(FailureClass.UNKNOWN_FAILURE, label)


def _take_turn(stop: Callable[[], bool]) -> bool:
    """This worker's one solve slot, or False once the person cancels while it waits."""
    while not _ONE_AT_A_TIME.acquire(timeout=CANCEL_POLL_S):
        if stop():
            return False
    return True


def execute(rt: SolveRuntime, run_id: uuid.UUID) -> SolveEnd:
    """Never raises: every end is a label and, unless transient, an outcome to publish."""
    try:
        with cancel_watch(lambda: _cancel_requested(rt, run_id)) as stop:
            if not _take_turn(stop):
                end = SolveEnd("cancelled", cancelled())
            else:
                try:
                    prepared = _prepare(rt, run_id)
                    end = prepared if isinstance(prepared, SolveEnd) else _solve(rt, prepared, stop)
                finally:
                    _ONE_AT_A_TIME.release()
    except Exception as error:
        classified = classify_failure(error)
        if classified.label == STORE_LABEL:
            end = SolveEnd(STORE_LABEL, None)
        else:
            end = _failed(FailureClass.UNKNOWN_FAILURE, classified.label)
    _log.info("route solve attempt finished", extra={"run_id": str(run_id), "outcome": end.label})
    return end
