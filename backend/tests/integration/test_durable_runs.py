"""Durability and journal privacy of model runs against real PostgreSQL 16 and DBOS
(ADR 0002; ARC1-05/06/07, DUR-01/02, MODEL-05/08). Workers are real processes; "kill" is
SIGKILL. Every scenario ends with a leak scan of both databases and every worker log."""

import secrets
import signal
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import SecretStr

from nessa.identity.workflow import ACTIVITY_MAX_ATTEMPTS
from tests.integration.durable import Scenario, make_scenario
from tests.support.client import ApiClient
from tests.support.fake_models import FakeFailure, key_fingerprint
from tests.support.infra import Infra
from tests.support.workers import wait_for

pytestmark = pytest.mark.integration


@pytest.fixture
def scenario(infra: Infra, api: ApiClient, ada: str, tmp_path: Path) -> Iterator[Scenario]:
    started = make_scenario(infra, api, ada, tmp_path)
    yield started
    # A failed assertion must not leave a worker running against the session database.
    for worker in started.workers:
        worker.kill_if_running()


@pytest.mark.req("ARC1-05", "ARC1-06", "DUR-03")
def test_a_run_completes_with_a_sealed_output_and_an_identifier_only_journal(
    scenario: Scenario,
) -> None:
    run_id = scenario.submit()
    queued = scenario.api_run(run_id)
    worker = scenario.worker("worker")
    run = scenario.wait_terminal(run_id)
    assert worker.stop() == 0

    assert queued["status"] == "queued"
    assert (run["status"], run["failure_class"]) == ("complete", None)
    shown = scenario.api_run(run_id)
    assert shown["output"]["suggested_title"].endswith(scenario.output_sentinel)
    assert shown["output"]["reason"] == f"key fingerprint {key_fingerprint_of(scenario)}"
    assert scenario.assert_identifier_only_journal(run_id) == {
        "status": "complete",
        "output_id": str(run["output_id"]),
    }
    [attempt] = scenario.attempts(run_id)
    assert (attempt["outcome"], attempt["spend_state"]) == ("succeeded", "reconciled")
    assert attempt["cost_nano_usd"] > 0
    assert attempt["reserved_nano_usd"] >= attempt["cost_nano_usd"]
    states = [
        (e["kind"], e["state"])
        for e in scenario.api.get(
            f"/v1/workspaces/{scenario.workspace_id}/events", scenario.token
        ).json()["items"]
        if e["subject_id"] == run_id
    ]
    assert states == [("run.state_changed", s) for s in ("queued", "running", "complete")]
    assert scenario.leaks() == []


def key_fingerprint_of(scenario: Scenario) -> str:
    return key_fingerprint(SecretStr(scenario.api_key))


@pytest.mark.req("ARC1-05", "DUR-02")
def test_worker_killed_mid_call_recovers_to_one_output_and_keeps_the_ambiguous_charge(
    scenario: Scenario,
) -> None:
    run_id = scenario.submit()
    first = scenario.worker("first", fake_delay_s="30")
    wait_for(lambda: len(scenario.attempts(run_id)) == 1, timeout_s=30, what="attempt")
    # The outbox entry is already marked, so only DBOS recovery can finish this run.
    wait_for(
        lambda: (
            scenario.infra.query(
                "SELECT dispatched_at FROM nessa.outbox WHERE run_id = %s", (run_id,)
            )[0]["dispatched_at"]
            is not None
        ),
        timeout_s=10,
        what="dispatch mark",
    )
    first.kill()
    assert scenario.run(run_id)["status"] == "running"

    second = scenario.worker("second")
    run = scenario.wait_terminal(run_id)
    assert second.stop() == 0

    assert run["status"] == "complete"
    assert len(scenario.outputs(run_id)) == 1
    attempts = scenario.attempts(run_id)
    assert [(a["outcome"], a["spend_state"]) for a in attempts] == [
        ("interrupted", "unknown"),  # may have been billed: its reservation stays committed
        ("succeeded", "reconciled"),
    ]
    assert scenario.journal(run_id)["status"][0]["status"] == "SUCCESS"
    assert scenario.leaks() == []


@pytest.mark.req("DUR-02")
def test_a_crash_after_acceptance_never_calls_the_model_again_and_keeps_the_usage(
    scenario: Scenario,
) -> None:
    """Carry-forward M4: the accepted output is found before anything else, and the first
    call's usage was committed with it."""
    run_id = scenario.submit()
    first = scenario.worker("first", crash_at="after_settle")
    assert first.wait_exit(60) == -signal.SIGKILL
    [accepted] = scenario.outputs(run_id)
    [paid] = scenario.attempts(run_id)

    second = scenario.worker("second")
    run = scenario.wait_terminal(run_id)
    second.stop()

    assert scenario.outputs(run_id) == [accepted]  # same row, untouched
    assert run["output_id"] == accepted["output_id"]
    first_attempt, reused = scenario.attempts(run_id)
    assert first_attempt == paid
    assert (paid["outcome"], paid["spend_state"]) == ("succeeded", "reconciled")
    assert paid["input_tokens"] is not None
    assert paid["cost_nano_usd"] is not None
    assert (reused["outcome"], reused["spend_state"], reused["input_tokens"]) == (
        "reused_accepted",
        "none",
        None,
    )
    assert scenario.leaks() == []


@pytest.mark.req("DUR-02")
def test_a_crash_after_a_recorded_failure_returns_it_without_a_second_call(
    scenario: Scenario,
) -> None:
    """B-M4: a terminal failure is committed (and may have been billed), the DBOS step is
    not. Re-execution must publish that failure, not reserve and call the model again."""
    run_id = scenario.submit()
    first = scenario.worker(
        "first", crash_at="after_settle", fake_failure=FakeFailure.AUTH_ECHO.value
    )
    assert first.wait_exit(60) == -signal.SIGKILL
    [failed] = scenario.attempts(run_id)

    second = scenario.worker("second", fake_failure=FakeFailure.AUTH_ECHO.value)
    run = scenario.wait_terminal(run_id)
    second.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "provider_authentication")
    first_attempt, reused = scenario.attempts(run_id)
    assert first_attempt == failed
    assert (failed["outcome"], failed["spend_state"]) == ("provider_authentication", "unknown")
    assert (reused["outcome"], reused["spend_state"], reused["reserved_nano_usd"]) == (
        "reused_failure",
        "none",
        0,
    )
    assert scenario.leaks() == []


@pytest.mark.req("ARC1-07")
def test_inconsistent_provider_usage_fails_typed_with_an_unknown_cost(
    scenario: Scenario,
) -> None:
    """B-M3: usage the registry rejects (more cached than input tokens) must not escape the
    activity as an untyped step error that leaves the run running."""
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.INCONSISTENT_USAGE.value)
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"], run["output_id"]) == (
        "failed",
        "unknown_failure",
        None,
    )
    [attempt] = scenario.attempts(run_id)
    assert (attempt["outcome"], attempt["spend_state"], attempt["cost_nano_usd"]) == (
        "unknown_failure:ValueError",
        "unknown",
        None,
    )
    assert scenario.journal(run_id)["status"][0]["status"] == "SUCCESS"
    assert scenario.leaks() == []


@pytest.mark.req("DUR-08")
def test_the_reconciler_publishes_an_errored_workflow_s_accepted_output(
    scenario: Scenario,
) -> None:
    """B-M1: a workflow left in DBOS ERROR after its call was accepted (its publication
    outlived the retries) is reconciled to `complete` with that output, never to a failure.
    The ERROR state is simulated: an outage longer than the publish retries takes 34 min."""
    run_id = scenario.submit()
    first = scenario.worker("first")
    done = scenario.wait_terminal(run_id)
    first.stop()
    scenario.infra.query(
        "UPDATE nessa.runs SET status = 'running', output_id = NULL, finished_at = NULL "
        "WHERE run_id = %s",
        (run_id,),
    )
    scenario.infra.query(
        "UPDATE dbos.workflow_status SET status = 'ERROR' WHERE workflow_uuid = %s",
        (f"nessa-run-{run_id}",),
        database="nessa_dbos",
    )

    second = scenario.worker("second")  # reconciles on its first pass
    run = scenario.wait_terminal(run_id, timeout_s=30)
    second.stop()

    assert (run["status"], run["output_id"], run["failure_class"]) == (
        "complete",
        done["output_id"],
        None,
    )
    assert len(scenario.attempts(run_id)) == 1  # reconciliation never calls the model
    assert scenario.leaks() == []


@pytest.mark.req("ARC1-05", "DUR-01")
def test_outbox_replay_after_a_dispatch_crash_starts_one_workflow(scenario: Scenario) -> None:
    run_id = scenario.submit()
    first = scenario.worker("first", crash_at="after_dispatch_before_mark", fake_delay_s="1")
    assert first.wait_exit(60) == -signal.SIGKILL
    outbox = scenario.infra.query("SELECT * FROM nessa.outbox WHERE run_id = %s", (run_id,))
    assert outbox[0]["dispatched_at"] is None  # the crash lost the dispatch mark

    second = scenario.worker("second")
    run = scenario.wait_terminal(run_id)
    wait_for(
        lambda: (
            scenario.infra.query(
                "SELECT dispatched_at FROM nessa.outbox WHERE run_id = %s", (run_id,)
            )[0]["dispatched_at"]
            is not None
        ),
        timeout_s=10,
        what="outbox replay",
    )
    second.stop()

    assert run["status"] == "complete"
    assert len(scenario.journal(run_id)["status"]) == 1
    assert len(scenario.outputs(run_id)) == 1
    assert [a["outcome"] for a in scenario.attempts(run_id)].count("succeeded") == 1
    assert scenario.leaks() == []


@pytest.mark.req("DUR-01")
def test_replaying_a_completed_outbox_entry_has_no_effect(scenario: Scenario) -> None:
    run_id = scenario.submit()
    first = scenario.worker("first")
    scenario.wait_terminal(run_id)
    first.stop()
    before = scenario.attempts(run_id)
    scenario.infra.query(
        "UPDATE nessa.outbox SET dispatched_at = NULL WHERE run_id = %s", (run_id,)
    )

    second = scenario.worker("second")
    wait_for(
        lambda: (
            scenario.infra.query(
                "SELECT dispatched_at FROM nessa.outbox WHERE run_id = %s", (run_id,)
            )[0]["dispatched_at"]
            is not None
        ),
        timeout_s=10,
        what="redelivered entry",
    )
    second.stop()

    assert scenario.attempts(run_id) == before
    assert len(scenario.outputs(run_id)) == 1
    assert scenario.leaks() == []


@pytest.mark.req("ARC1-07")
def test_a_transient_provider_error_is_retried_by_the_dbos_step_only(scenario: Scenario) -> None:
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.RATE_LIMIT_ONCE.value)
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert run["status"] == "complete"
    assert [a["outcome"] for a in scenario.attempts(run_id)] == ["transient_429", "succeeded"]
    # The provider body echoed 20 characters of the key; none of it may be persisted or logged.
    assert scenario.leaks() == []


@pytest.mark.req("ARC1-07", "API-03")
def test_exhausted_retries_end_provider_unavailable_never_an_empty_success(
    scenario: Scenario,
) -> None:
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.ALWAYS_UNAVAILABLE.value)
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"], run["output_id"]) == (
        "provider_unavailable",
        "provider_unavailable",
        None,
    )
    assert len(scenario.attempts(run_id)) == ACTIVITY_MAX_ATTEMPTS
    assert scenario.outputs(run_id) == []
    assert scenario.api_run(run_id)["output"] is None
    assert scenario.assert_identifier_only_journal(run_id) == {
        "status": "provider_unavailable",
        "failure_class": "provider_unavailable",
    }
    assert scenario.leaks() == []


@pytest.mark.req("ARC1-06", "MODEL-06")
def test_a_provider_error_echoing_the_key_is_classified_and_never_journalled(
    scenario: Scenario,
) -> None:
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.AUTH_ECHO.value)
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "provider_authentication")
    [attempt] = scenario.attempts(run_id)
    # No usage reported: the charge is unknown and its reservation stays committed.
    assert (attempt["outcome"], attempt["spend_state"]) == ("provider_authentication", "unknown")
    scenario.assert_identifier_only_journal(run_id)
    assert scenario.leaks() == []


def test_connection_errors_are_retried_then_fail_visibly(scenario: Scenario) -> None:
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.CONNECTION_ERROR.value)
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("provider_unavailable", "provider_unavailable")
    assert [a["outcome"] for a in scenario.attempts(run_id)] == ["transient_connection"] * 3
    assert scenario.leaks() == []


@pytest.mark.req("ARC1-06")
def test_an_unexpected_error_fails_typed_without_its_message(scenario: Scenario) -> None:
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.UNEXPECTED_ERROR.value)
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "unknown_failure")
    [attempt] = scenario.attempts(run_id)
    assert attempt["outcome"] == "unknown_failure:RuntimeError"
    journal = scenario.journal(run_id)
    assert journal["status"][0]["status"] == "SUCCESS"
    assert [step["error"] for step in journal["steps"]] == [None, None]
    # The RuntimeError quoted the key and the output sentinel; only its class name persists.
    assert scenario.leaks() == []


@pytest.mark.req("MODEL-05")
def test_revoking_the_key_stops_a_queued_run_before_any_call(scenario: Scenario) -> None:
    run_id = scenario.submit()
    [credential] = scenario.api.get(
        f"/v1/workspaces/{scenario.workspace_id}/credentials", scenario.token
    ).json()["items"]
    scenario.api.write(
        "POST",
        f"/v1/workspaces/{scenario.workspace_id}/credentials/{credential['credential_id']}/revoke",
        scenario.token,
    )

    worker = scenario.worker("worker")
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "credential_unavailable")
    [attempt] = scenario.attempts(run_id)
    assert (attempt["spend_state"], attempt["input_tokens"]) == ("none", None)
    assert scenario.leaks() == []


@pytest.mark.req("MODEL-05")
def test_rotating_the_key_while_a_run_is_queued_uses_the_new_key(scenario: Scenario) -> None:
    run_id = scenario.submit()
    [credential] = scenario.api.get(
        f"/v1/workspaces/{scenario.workspace_id}/credentials", scenario.token
    ).json()["items"]
    new_key = secrets.token_urlsafe(32)
    scenario.api.write(
        "POST",
        f"/v1/workspaces/{scenario.workspace_id}/credentials/{credential['credential_id']}/rotate",
        scenario.token,
        {"api_key": new_key, "consent_to_encrypted_storage": True},
    )

    worker = scenario.worker("worker")
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert run["status"] == "complete"
    shown = scenario.api_run(run_id)
    assert shown["output"]["reason"] == f"key fingerprint {key_fingerprint(SecretStr(new_key))}"
    scenario.retired_keys.append(scenario.api_key)
    scenario.api_key = new_key
    assert scenario.leaks() == []  # neither the replaced key nor its successor anywhere


def cancel(scenario: Scenario, run_id: str) -> dict[str, object]:
    response = scenario.api.write(
        "POST", f"/v1/workspaces/{scenario.workspace_id}/runs/{run_id}/cancel", scenario.token
    )
    assert response.status_code == 202, response.text
    body: dict[str, object] = response.json()
    return body


@pytest.mark.req("DUR-05", "MODEL-08")
def test_a_run_cancelled_while_queued_never_calls_the_model_or_reserves_spend(
    scenario: Scenario,
) -> None:
    run_id = scenario.submit()
    requested = cancel(scenario, run_id)  # no worker yet: the run is still queued

    worker = scenario.worker("worker")
    run = scenario.wait_terminal(run_id)
    worker.stop()

    assert requested["status"] == "queued"
    assert requested["cancel_requested_at"] is not None
    assert (run["status"], run["failure_class"], run["output_id"]) == ("cancelled", None, None)
    assert scenario.attempts(run_id) == []  # no call, no reservation
    assert scenario.journal(run_id)["status"] == []  # its workflow was never started
    assert scenario.leaks() == []


@pytest.mark.req("DUR-05", "MODEL-08")
def test_a_run_cancelled_mid_call_settles_that_call_and_makes_no_other(
    scenario: Scenario,
) -> None:
    run_id = scenario.submit()
    worker = scenario.worker("worker", fake_delay_s="4")
    wait_for(lambda: len(scenario.attempts(run_id)) == 1, timeout_s=30, what="the call")

    cancel(scenario, run_id)
    run = scenario.wait_terminal(run_id, timeout_s=10)  # before the call itself ends
    wait_for(
        lambda: scenario.attempts(run_id)[0]["finished_at"] is not None,
        timeout_s=30,
        what="the call to settle",
    )
    worker.stop()
    [attempt] = scenario.attempts(run_id)
    journal = scenario.journal(run_id)

    assert (run["status"], run["failure_class"]) == ("cancelled", None)
    assert attempt["spend_state"] == "reconciled"  # the sent call is booked at its cost
    assert scenario.run(run_id)["status"] == "cancelled"  # its result never revives the run
    assert journal["status"][0]["status"] == "CANCELLED"
    assert "nessa.publish_outcome" not in {s["function_name"] for s in journal["steps"]}
    assert scenario.leaks() == []
