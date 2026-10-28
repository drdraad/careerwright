"""Interview turns end to end against real PostgreSQL 16 and DBOS, with real worker
processes and a fake provider (S2.2; PROF-01..07, MODEL-02/03/04, DUR-04).

Every failure path ends typed, with nothing to apply and the previous profile intact; a
proposal is applied only from a complete validated output, against the version it was made
for, through the same command as a direct edit, with hard constraints confirmed one by one.
"""

import dataclasses
import secrets
import signal
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from psycopg import errors

from nessa.api.app import create_app
from nessa.api.deps import ApiDependencies
from nessa.config import RuntimeMode
from tests.integration.durable import Scenario, fresh_actor, make_scenario
from tests.support.client import ApiClient, profile_with
from tests.support.fake_models import interview_answer
from tests.support.infra import API_BASE, Infra
from tests.support.workers import wait_for

pytestmark = pytest.mark.integration


@pytest.fixture
def scenario(infra: Infra, api: ApiClient, ada: str, tmp_path: Path) -> Iterator[Scenario]:
    started = make_scenario(infra, api, ada, tmp_path)
    yield started
    for worker in started.workers:
        worker.kill_if_running()


def message_sentinel() -> str:
    return f"PRIVATE-MESSAGE-{secrets.token_hex(6)}"


def run_turn(scenario: Scenario, message: str, **worker: str) -> dict[str, Any]:
    turn = scenario.submit_turn(f"I could work in Leeds and spend about £1,500. {message}")
    started = scenario.worker("worker", **worker)
    scenario.wait_terminal(turn["turn_id"])
    assert started.stop() == 0
    return scenario.turn(turn["turn_id"])


def accept_all(turn: dict[str, Any], version: int = 1, **overrides: Any) -> dict[str, Any]:
    changes = turn["proposal"]["changes"]
    return {
        "expected_version": version,
        "accept": [c["change_id"] for c in changes],
        "confirm_hard_constraints": [c["field"] for c in changes if c["hard_constraint"]],
        **overrides,
    }


@pytest.mark.req("PROF-05", "PROF-01", "DUR-03")
def test_a_turn_runs_durably_and_its_proposals_cite_the_message(scenario: Scenario) -> None:
    secret = message_sentinel()

    turn = run_turn(scenario, secret)

    run = turn["run"]
    assert (run["kind"], run["status"], run["profile_version"]) == ("interview_turn", "complete", 1)
    assert (turn["profile_version"], turn["decision"]) == (1, None)
    proposal = turn["proposal"]
    assert (proposal["origin"], proposal["profile_version"]) == ("model", 1)
    assert proposal["reply"].startswith(scenario.output_sentinel)
    changes = {c["field"]: c for c in proposal["changes"]}
    assert changes["cities"]["value"] == ["Leeds"]
    assert changes["cities"]["basis"] == "stated"
    assert changes["direct_spend_cap"]["value"] == {"minor_units": 150_000, "currency": "GBP"}
    assert changes["direct_spend_cap"]["basis"] == "inferred"
    assert all(c["hard_constraint"] for c in changes.values())
    assert all(c["message_ids"] == [turn["message_id"]] for c in changes.values())
    [attempt] = scenario.attempts(turn["turn_id"])
    assert (attempt["outcome"], attempt["spend_state"], attempt["requests_sent"]) == (
        "succeeded",
        "reconciled",
        1,
    )
    assert scenario.profile()["version"] == 1  # a proposal changes nothing by itself
    assert scenario.assert_identifier_only_journal(turn["turn_id"])["status"] == "complete"
    assert scenario.leaks(secret) == []


@pytest.mark.req("PROF-04", "PROF-07", "PROF-01")
def test_hard_constraints_apply_only_when_each_is_confirmed(scenario: Scenario) -> None:
    turn = run_turn(scenario, "")
    changes = {c["field"]: c["change_id"] for c in turn["proposal"]["changes"]}

    unconfirmed = scenario.decide(turn["turn_id"], accept_all(turn, confirm_hard_constraints=[]))
    partly = scenario.decide(turn["turn_id"], accept_all(turn, confirm_hard_constraints=["cities"]))

    for refused in (unconfirmed, partly):
        assert refused.status_code == 409
        assert refused.json()["error"]["code"] == "CONFIRMATION_REQUIRED"
    assert partly.json()["error"]["details"]["fields"] == ["direct_spend_cap"]
    assert scenario.profile()["version"] == 1  # nothing was saved
    key = uuid.uuid4()
    body = {
        "expected_version": 1,
        "accept": [changes["cities"]],
        "confirm_hard_constraints": ["cities"],
    }
    decided = scenario.decide(turn["turn_id"], body, key=key)
    assert decided.status_code == 201, decided.text
    result = decided.json()
    assert result["decision"]["accepted_change_ids"] == [changes["cities"]]
    assert result["decision"]["rejected_change_ids"] == [changes["direct_spend_cap"]]
    assert result["decision"]["profile_version"] == 2
    document = result["profile"]["document"]
    assert (result["profile"]["version"], document["cities"]["value"]) == (2, ["Leeds"])
    assert document["direct_spend_cap"]["state"] == "unasked"  # the rejected one is not saved
    sources = scenario.api.get(
        f"/v1/workspaces/{scenario.workspace_id}/sources", scenario.token
    ).json()["items"]
    [source] = [s for s in sources if s["source_ref_id"] == document["cities"]["source_ref_id"]]
    assert source["kind"] == "conversation"
    assert (source["turn_id"], source["message_ids"], source["basis"]) == (
        turn["turn_id"],
        [turn["message_id"]],
        "stated",
    )
    assert source["recorded_by"] == scenario.api.get("/v1/me", scenario.token).json()["actor_id"]
    retried = scenario.decide(turn["turn_id"], body, key=key)
    assert (retried.status_code, retried.json()) == (201, result)  # the receipt, not twice
    again = scenario.decide(turn["turn_id"], body)
    assert (again.status_code, again.json()["error"]["code"]) == (409, "ALREADY_DECIDED")
    shown = scenario.turn(turn["turn_id"])
    assert shown["decision"]["confirmed_hard_constraints"] == ["cities"]
    kinds = [
        e["kind"]
        for e in scenario.api.get(
            f"/v1/workspaces/{scenario.workspace_id}/events", scenario.token
        ).json()["items"]
    ]
    assert "interview.turn_decided" in kinds


@pytest.mark.req("DUR-04", "PROF-05")
def test_a_proposal_is_never_applied_to_a_newer_profile(scenario: Scenario) -> None:
    turn = run_turn(scenario, "")
    edited = scenario.api.write(
        "PUT",
        f"/v1/workspaces/{scenario.workspace_id}/profile",
        scenario.token,
        {"expected_version": 1, "profile": profile_with(cities=["York"])},
    )
    assert edited.status_code == 201
    before = scenario.profile()

    stale = scenario.decide(turn["turn_id"], accept_all(turn, version=2))
    older = scenario.decide(turn["turn_id"], accept_all(turn, version=1))

    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert stale.json()["error"]["details"] == {"current_version": 2, "proposal_version": 1}
    assert (older.status_code, older.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert scenario.profile() == before  # the newer profile survives, untouched
    assert scenario.turn(turn["turn_id"])["decision"] is None


def test_a_message_written_against_an_old_version_is_refused_before_any_run(
    scenario: Scenario,
) -> None:
    response = scenario.api.write(
        "POST",
        f"/v1/workspaces/{scenario.workspace_id}/interview/turns",
        scenario.token,
        {"expected_profile_version": 0, "message": "Hello"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["details"] == {"current_version": 1}
    assert scenario.infra.query(
        "SELECT count(*) AS n FROM nessa.runs WHERE workspace_id = %s", (scenario.workspace_id,)
    ) == [{"n": 0}]


@pytest.mark.req("PROF-05", "MODEL-03")
def test_an_output_invalid_after_its_repair_fails_typed_and_leaves_nothing_to_apply(
    scenario: Scenario,
) -> None:
    turn = run_turn(scenario, "", fake_failure="invalid_always")

    assert (turn["run"]["status"], turn["run"]["failure_class"]) == (
        "failed",
        "invalid_model_output",
    )
    assert turn["proposal"] is None
    [attempt] = scenario.attempts(turn["turn_id"])
    assert attempt["requests_sent"] == 2  # the first request and one repair, never more
    assert scenario.outputs(turn["turn_id"]) == []
    refused = scenario.decide(turn["turn_id"], {"expected_version": 1, "accept": ["c1"]})
    assert (refused.status_code, refused.json()["error"]["code"]) == (409, "PROPOSAL_NOT_AVAILABLE")
    assert scenario.profile()["version"] == 1
    assert scenario.leaks() == []


@pytest.mark.req("PROF-05")
def test_an_output_invalid_once_is_repaired_by_one_more_request(scenario: Scenario) -> None:
    turn = run_turn(scenario, "", fake_failure="invalid_once")

    assert turn["run"]["status"] == "complete"
    [attempt] = scenario.attempts(turn["turn_id"])
    assert (attempt["requests_sent"], attempt["spend_state"]) == (2, "reconciled")


def reply_path(scenario: Scenario, turn_id: str) -> str:
    return f"/v1/workspaces/{scenario.workspace_id}/interview/turns/{turn_id}/reply"


def partial_events(scenario: Scenario, turn_id: str) -> list[dict[str, Any]]:
    events = scenario.api.get(f"/v1/workspaces/{scenario.workspace_id}/events", scenario.token)
    return [
        e
        for e in events.json()["items"]
        if e["kind"] == "run.partial_updated" and e["subject_id"] == turn_id
    ]


@pytest.mark.req("MODEL-03", "DUR-03", "SEC-01")
def test_a_turn_streams_its_reply_to_its_owner_and_the_validated_output_supersedes_it(
    scenario: Scenario, ben: str
) -> None:
    secret = message_sentinel()
    turn_id = scenario.submit_turn(f"I could work in Leeds and spend about £1,500. {secret}")[
        "turn_id"
    ]
    crashed = scenario.worker("crashes", crash_at="after_first_partial")
    assert crashed.wait_exit(60) == -signal.SIGKILL  # mid-call, after the first piece

    streaming = scenario.api.get(reply_path(scenario, turn_id), scenario.token).json()
    assert (streaming["completeness"], streaming["seq"]) == ("streaming", 1)
    assert streaming["text"]
    assert streaming["updated_at"]
    assert scenario.turn(turn_id)["proposal"] is None  # the reply so far is never a proposal
    # The status event names the run and the sequence, nothing else.
    assert [(e["state"], e["detail"]) for e in partial_events(scenario, turn_id)] == [
        (None, {"seq": 1})
    ]
    assert scenario.api.get(reply_path(scenario, turn_id), ben).status_code == 404
    ben_id = scenario.api.get("/v1/me", ben).json()["actor_id"]
    count = "SELECT count(*) AS n FROM nessa.run_partials"
    assert scenario.infra.as_role("pg_api", count, actor=ben_id) == [{"n": 0}]

    recovered = scenario.worker("recovers")
    scenario.wait_terminal(turn_id)
    assert recovered.stop() == 0

    shown = scenario.turn(turn_id)
    assert shown["run"]["status"] == "complete"
    assert shown["proposal"]["reply"].startswith(streaming["text"])
    done = scenario.api.get(reply_path(scenario, turn_id), scenario.token).json()
    assert (done["completeness"], done["text"], done["seq"]) == ("superseded", None, None)
    assert scenario.infra.query(
        "SELECT count(*) AS n FROM nessa.run_partials WHERE run_id = %s", (turn_id,)
    ) == [{"n": 0}]  # deleted with the validated output's arrival
    assert scenario.leaks(secret) == []  # the streamed text is sealed, like the output


@pytest.mark.req("MODEL-03", "PROF-03")
def test_a_reply_cut_off_mid_stream_ends_observably_with_the_partial_marked_incomplete(
    scenario: Scenario,
) -> None:
    before = scenario.profile()

    turn = run_turn(scenario, "", fake_failure="cut_mid_stream")

    assert (turn["run"]["status"], turn["run"]["failure_class"]) == (
        "provider_unavailable",
        "provider_unavailable",
    )
    assert turn["proposal"] is None
    partial = scenario.api.get(reply_path(scenario, turn["turn_id"]), scenario.token).json()
    assert partial["completeness"] == "incomplete"
    full = interview_answer({"current_message": "m1"}, scenario.output_sentinel, valid=True)
    assert partial["text"]
    assert str(full["reply"]).startswith(partial["text"])
    assert partial["text"] != full["reply"]  # only the part that arrived
    seqs = [e["detail"]["seq"] for e in partial_events(scenario, turn["turn_id"])]
    assert partial["seq"] == max(seqs)  # the last event announced the incomplete state
    assert scenario.outputs(turn["turn_id"]) == []
    refused = scenario.decide(turn["turn_id"], {"expected_version": 1, "accept": ["c1"]})
    assert (refused.status_code, refused.json()["error"]["code"]) == (409, "PROPOSAL_NOT_AVAILABLE")
    assert scenario.profile() == before  # nothing partial ever commits
    # A call cut off part-way may have been billed in full: never reconciled at the usage
    # counted so far, but unknown, with the whole reservation kept.
    attempts = scenario.attempts(turn["turn_id"])
    assert [(a["spend_state"], a["cost_nano_usd"]) for a in attempts] == [("unknown", None)] * 3
    assert all(a["reserved_nano_usd"] == 3_500_000 for a in attempts)
    # The stored partial holds the output sentinel (the fake's reply starts with it), and the
    # scan finds nothing: it is sealed. Stored unsealed, the same scan finds it.
    assert scenario.output_sentinel in partial["text"]
    assert scenario.leaks() == []
    [row] = scenario.infra.query(
        "SELECT ciphertext FROM nessa.run_partials WHERE run_id = %s", (turn["turn_id"],)
    )
    unsealed = "UPDATE nessa.run_partials SET ciphertext = %s WHERE run_id = %s"
    scenario.infra.query(unsealed, (partial["text"].encode(), turn["turn_id"]))
    try:
        assert ("nessa.run_partials", "model output") in {
            (f.location, f.needle_label) for f in scenario.leaks()
        }
    finally:
        scenario.infra.query(unsealed, (row["ciphertext"], turn["turn_id"]))


@pytest.mark.req("MODEL-03")
def test_the_whole_reply_is_stored_as_soon_as_it_ends_while_the_proposals_are_still_coming(
    scenario: Scenario,
) -> None:
    turn_id = scenario.submit_turn("Leeds")["turn_id"]
    full = interview_answer({"current_message": "m1"}, scenario.output_sentinel, valid=True)
    worker = scenario.worker("worker", fake_failure="pause_after_reply")

    def whole_reply_stored() -> bool:
        partial = scenario.api.get(reply_path(scenario, turn_id), scenario.token).json()
        return bool(partial["text"] == full["reply"])

    # The reply streams in pieces quickly, then the fake pauses before the proposals: the
    # stored partial must already be the whole reply, not the first piece of it.
    wait_for(whole_reply_stored, timeout_s=10, what="the whole reply in the partial store")
    assert scenario.run(turn_id)["status"] == "running"
    assert scenario.outputs(turn_id) == []  # the proposals have not finished
    assert scenario.leaks() == []  # the partial holds the sentinel, sealed
    scenario.wait_terminal(turn_id)
    assert worker.stop() == 0
    done = scenario.api.get(reply_path(scenario, turn_id), scenario.token).json()
    assert done["completeness"] == "superseded"


@pytest.mark.req("MODEL-03")
def test_between_attempts_a_stopped_reply_is_not_called_final_and_a_stored_output_supersedes(
    scenario: Scenario,
) -> None:
    turn_id = scenario.submit_turn("Leeds")["turn_id"]
    # The first attempt's stream is cut; the worker dies right after settling it, so the
    # run is still running and the DBOS step will try again.
    crashed = scenario.worker("crashes", crash_at="after_settle", fake_failure="cut_mid_stream")
    assert crashed.wait_exit(60) == -signal.SIGKILL

    between = scenario.api.get(reply_path(scenario, turn_id), scenario.token).json()

    assert scenario.run(turn_id)["status"] == "running"
    assert between["completeness"] == "stopped"  # may still be superseded: not final
    assert between["text"]
    succeeding = scenario.worker("succeeds", crash_at="after_settle")
    assert succeeding.wait_exit(60) == -signal.SIGKILL
    # The output is stored, the run is not yet published as complete: the reply is already
    # superseded, never "none".
    assert scenario.run(turn_id)["status"] == "running"
    assert scenario.outputs(turn_id) != []
    stored = scenario.api.get(reply_path(scenario, turn_id), scenario.token).json()
    assert (stored["completeness"], stored["text"]) == ("superseded", None)
    finisher = scenario.worker("finishes")
    assert scenario.wait_terminal(turn_id)["status"] == "complete"
    assert finisher.stop() == 0


@pytest.mark.req("MODEL-03", "SEC-01")
def test_access_revoked_mid_call_still_settles_the_attempt_and_ends_typed(
    infra: Infra, api: ApiClient, tmp_path: Path
) -> None:
    email, token = fresh_actor(api, infra)
    revoked = make_scenario(infra, api, token, tmp_path)
    turn_id = revoked.submit_turn("Leeds")["turn_id"]
    worker = revoked.worker("worker", fake_failure="cut_mid_stream", fake_delay_s="3")
    wait_for(lambda: revoked.attempts(turn_id) != [], timeout_s=30, what="the first attempt")

    # Revoked while the call is in flight: the partial cannot be written, nor marked.
    infra.query("UPDATE nessa.actors SET access = 'revoked' WHERE email = %s", (email,))
    run = revoked.wait_terminal(turn_id)
    assert worker.stop() == 0

    # The attempt's settlement is not lost to the partial store: it is recorded with its
    # own outcome, and the retry is refused for the real reason.
    assert (run["status"], run["failure_class"]) == ("failed", "access_revoked")
    first, second = revoked.attempts(turn_id)
    assert (first["outcome"], first["spend_state"]) == ("transient_connection", "unknown")
    assert (second["outcome"], second["spend_state"]) == ("access_revoked", "none")


@pytest.mark.req("MODEL-03", "PROF-03")
@pytest.mark.parametrize(
    ("failure", "failure_class"),
    [("refusal", "model_refused"), ("truncated", "output_truncated")],
)
def test_a_refusal_or_a_truncated_output_ends_typed_with_the_profile_intact(
    scenario: Scenario, failure: str, failure_class: str
) -> None:
    before = scenario.profile()

    turn = run_turn(scenario, "", fake_failure=failure)

    assert (turn["run"]["status"], turn["run"]["failure_class"]) == ("failed", failure_class)
    assert turn["proposal"] is None
    [attempt] = scenario.attempts(turn["turn_id"])
    # Neither is sent back for repair; the cut-off response's reported usage is booked.
    assert (attempt["requests_sent"], attempt["spend_state"]) == (1, "reconciled")
    assert scenario.outputs(turn["turn_id"]) == []  # partial output is never stored
    assert scenario.profile() == before
    # The refusal text and the cut-off output carry the output sentinel: discarded.
    assert scenario.leaks() == []


@pytest.mark.req("MODEL-04", "MODEL-03")
def test_an_unavailable_model_ends_provider_unavailable_with_the_profile_intact(
    scenario: Scenario,
) -> None:
    turn = run_turn(scenario, "", fake_failure="always_unavailable")

    assert (turn["run"]["status"], turn["run"]["failure_class"]) == (
        "provider_unavailable",
        "provider_unavailable",
    )
    assert len(scenario.attempts(turn["turn_id"])) == 3  # the DBOS step's budget, not more
    assert turn["proposal"] is None
    assert scenario.profile()["version"] == 1


@pytest.mark.req("MODEL-04", "MODEL-08")
def test_a_standard_model_outage_ends_provider_unavailable_within_the_default_limits(
    infra: Infra, api: ApiClient, ada: str, tmp_path: Path
) -> None:
    personal = make_scenario(infra, api, ada, tmp_path, synthetic=False)

    turn = run_turn(personal, "", fake_failure="always_unavailable")

    assert turn["run"]["model_id"] == "muse-spark-1.3"
    assert (turn["run"]["status"], turn["run"]["failure_class"]) == (
        "provider_unavailable",
        "provider_unavailable",
    )  # the outage, never "over budget": every retry fits the default run limit
    attempts = personal.attempts(turn["turn_id"])
    assert [a["spend_state"] for a in attempts] == ["unknown"] * 3
    assert all(a["reserved_nano_usd"] == 49_000_000 for a in attempts)


@pytest.mark.req("MODEL-08")
def test_a_repair_request_that_fails_without_usage_keeps_the_whole_reservation(
    scenario: Scenario,
) -> None:
    turn = run_turn(scenario, "", fake_failure="invalid_then_unavailable")

    assert turn["run"]["status"] == "provider_unavailable"
    attempts = scenario.attempts(turn["turn_id"])
    assert len(attempts) == 3
    for attempt in attempts:
        # The first request reported usage; the repair may have been billed but reported
        # nothing, so the attempt's cost is unknown and its full reservation stays committed.
        assert attempt["requests_sent"] == 2
        assert (attempt["spend_state"], attempt["cost_nano_usd"]) == ("unknown", None)
        assert attempt["reserved_nano_usd"] == 3_500_000
    spend = scenario.api.get(f"/v1/workspaces/{scenario.workspace_id}/spend", scenario.token)
    assert spend.json()["period_committed_nano_usd"] == 3 * 3_500_000


def set_limits(scenario: Scenario, run_limit: int) -> None:
    base = f"/v1/workspaces/{scenario.workspace_id}/spend"
    current = scenario.api.get(base, scenario.token).json()["version"]
    response = scenario.api.write(
        "PUT",
        f"{base}/limits",
        scenario.token,
        {
            "expected_version": current,
            "run_limit_nano_usd": run_limit,
            "period_limit_nano_usd": 1_000_000_000,
        },
    )
    assert response.status_code == 200, response.text


@pytest.mark.req("MODEL-04", "MODEL-08")
def test_budget_exhaustion_refuses_a_turn_before_and_after_it_is_queued(
    scenario: Scenario,
) -> None:
    set_limits(scenario, 1_000_000)  # below one attempt's $0.0035
    refused = scenario.api.write(
        "POST",
        f"/v1/workspaces/{scenario.workspace_id}/interview/turns",
        scenario.token,
        {"expected_profile_version": 1, "message": "Leeds"},
    )
    assert (refused.status_code, refused.json()["error"]["code"]) == (402, "BUDGET_EXCEEDED")
    assert scenario.infra.query(
        "SELECT count(*) AS n FROM nessa.interview_turns WHERE workspace_id = %s",
        (scenario.workspace_id,),
    ) == [{"n": 0}]
    set_limits(scenario, 100_000_000)
    turn = scenario.submit_turn("Leeds")
    set_limits(scenario, 1_000_000)  # lowered while it is queued

    worker = scenario.worker("worker")
    scenario.wait_terminal(turn["turn_id"])
    assert worker.stop() == 0

    shown = scenario.turn(turn["turn_id"])
    assert (shown["run"]["status"], shown["run"]["failure_class"]) == ("failed", "budget_exceeded")
    [attempt] = scenario.attempts(turn["turn_id"])
    # Refused before any call: a known zero, not an unknown cost.
    assert (attempt["spend_state"], attempt["cost_nano_usd"]) == ("none", 0)
    assert scenario.profile()["version"] == 1


@pytest.mark.req("MODEL-02")
def test_a_non_synthetic_workspace_s_turns_use_the_standard_model_only(
    infra: Infra, api: ApiClient, ada: str, tmp_path: Path
) -> None:
    workspace = api.create_workspace(ada, "Personal data", synthetic=False)["workspace_id"]
    stored = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/credentials",
        ada,
        {"api_key": secrets.token_urlsafe(32), "consent_to_encrypted_storage": True},
    )
    assert stored.status_code == 201

    submitted = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns",
        ada,
        {"expected_profile_version": 0, "message": "I work in Leeds."},
    )

    assert submitted.status_code == 202, submitted.text
    run = submitted.json()["run"]
    assert (run["model_id"], run["model_mode"], run["synthetic"]) == (
        "muse-spark-1.3",
        "standard",
        False,
    )
    with pytest.raises(errors.CheckViolation):
        infra.query(
            "INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, "
            "requested_by, model_id, model_mode, status, profile_version) SELECT "
            "gen_random_uuid(), workspace_id, data_mode, synthetic, 'interview_turn', "
            "owner_actor_id, 'muse-spark-1.3-contributor', 'contributor', 'queued', 0 "
            "FROM nessa.workspaces WHERE workspace_id = %s",
            (workspace,),
        )
    scenario = make_scenario(infra, api, ada, tmp_path)  # a worker to finish the queued run
    worker = scenario.worker("worker")
    scenario.wait_terminal(run["run_id"])
    assert worker.stop() == 0
    [attempt] = scenario.attempts(run["run_id"])
    assert attempt["model_id"] == "muse-spark-1.3"  # the activity called Standard, too


@pytest.fixture
def demo_runtime_api(api_deps: ApiDependencies) -> Iterator[ApiClient]:
    settings = api_deps.settings.model_copy(update={"runtime_mode": RuntimeMode.DEMO})
    deps = dataclasses.replace(api_deps, settings=settings)
    with TestClient(
        create_app(deps),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57002),
    ) as client:
        yield ApiClient(client)


@pytest.mark.req("BND1-11", "TEST1-10")
def test_a_demo_workspace_interviews_offline_with_the_labelled_fixture_interviewer(
    infra: Infra, api: ApiClient, demo_runtime_api: ApiClient, ada: str, tmp_path: Path
) -> None:
    created = api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Demo interview", "data_mode": "demo", "synthetic": True},
    )
    workspace = created.json()["workspace_id"]
    connection = demo_runtime_api.write(
        "POST", f"/v1/workspaces/{workspace}/runs", ada, {"kind": "connection_check"}
    )
    assert connection.json()["error"]["code"] == "MODEL_UNAVAILABLE"  # no provider offline

    submitted = demo_runtime_api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns",
        ada,
        {"expected_profile_version": 0, "message": "I could work in Bristol, 5 hours a week."},
    )
    assert submitted.status_code == 202, submitted.text
    turn_id = submitted.json()["turn_id"]
    run = submitted.json()["run"]
    assert (run["model_id"], run["model_mode"], run["data_mode"]) == (
        "nessa-fixture-interviewer-1",
        "fixture",
        "demo",
    )
    scenario = make_scenario(infra, api, ada, tmp_path)
    worker = scenario.worker("worker")
    scenario.wait_terminal(turn_id)
    assert worker.stop() == 0

    turn = api.get(f"/v1/workspaces/{workspace}/interview/turns/{turn_id}", ada).json()
    assert turn["run"]["status"] == "complete", turn["run"]
    proposal = turn["proposal"]
    assert proposal["origin"] == "fixture"
    assert proposal["reply"].startswith("Demo interviewer (synthetic):")
    assert {c["field"]: c["value"] for c in proposal["changes"]} == {
        "cities": ["Bristol"],
        "weekly_study_hours": 5.0,
    }
    # The fixture streams its reply like a provider; the validated proposal supersedes it.
    events = api.get(f"/v1/workspaces/{workspace}/events", ada).json()["items"]
    assert any(e["kind"] == "run.partial_updated" for e in events)
    reply = api.get(f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/reply", ada).json()
    assert (reply["completeness"], reply["text"]) == ("superseded", None)
    [attempt] = scenario.attempts(turn_id)
    assert (attempt["spend_state"], attempt["cost_nano_usd"], attempt["reserved_nano_usd"]) == (
        "none",
        0,
        0,
    )  # no provider, no key: a known zero charge
    decided = demo_runtime_api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/decision",
        ada,
        {
            "expected_version": 0,
            "accept": [c["change_id"] for c in proposal["changes"]],
            "confirm_hard_constraints": ["cities", "weekly_study_hours"],
        },
    )
    assert decided.status_code == 201, decided.text
    assert decided.json()["profile"]["document"]["weekly_study_hours"]["value"] == 5.0


@pytest.mark.req("BND1-11")
@pytest.mark.parametrize(
    ("kind", "model_id", "model_mode", "constraint"),
    [
        # A demo workspace never reaches a provider model...
        (
            "interview_turn",
            "muse-spark-1.3-contributor",
            "contributor",
            "demo_workspaces_use_only_the_fixture_model",
        ),
        # ...and the fixture interviewer answers interview turns only.
        (
            "connection_check",
            "nessa-fixture-interviewer-1",
            "fixture",
            "the_fixture_model_only_interviews",
        ),
    ],
)
def test_the_database_keeps_the_fixture_interviewer_and_demo_workspaces_together(
    infra: Infra,
    api: ApiClient,
    ada: str,
    kind: str,
    model_id: str,
    model_mode: str,
    constraint: str,
) -> None:
    created = api.write(
        "POST", "/v1/workspaces", ada, {"name": "Demo", "data_mode": "demo", "synthetic": True}
    )
    assert created.status_code == 201, created.text

    with pytest.raises(errors.CheckViolation, match=constraint):
        infra.query(
            "INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, "
            "requested_by, model_id, model_mode, status, profile_version) SELECT "
            "gen_random_uuid(), workspace_id, data_mode, synthetic, %s, owner_actor_id, %s, %s, "
            "'queued', CASE WHEN %s = 'interview_turn' THEN 0 END "
            "FROM nessa.workspaces WHERE workspace_id = %s",
            (kind, model_id, model_mode, kind, created.json()["workspace_id"]),
        )


def test_the_worker_never_reads_profile_or_conversation_tables_and_the_api_never_reads_inputs(
    scenario: Scenario, infra: Infra, api: ApiClient, ada: str, tmp_path: Path
) -> None:
    turn = run_turn(scenario, "")
    run_id = turn["turn_id"]
    second = scenario.submit_turn("York, too.")["turn_id"]  # queued, never run
    other = make_scenario(infra, api, ada, tmp_path)
    elsewhere = other.submit_turn("Bristol.")["turn_id"]

    for table in ("interview_turns", "interview_decisions", "profile_versions"):
        with pytest.raises(errors.InsufficientPrivilege):
            scenario.infra.as_role("pg_worker", f"SELECT * FROM nessa.{table}", run=run_id)  # noqa: S608
    with pytest.raises(errors.InsufficientPrivilege):
        scenario.infra.as_role(
            "pg_api", "SELECT ciphertext FROM nessa.run_inputs", actor=str(uuid.uuid4())
        )
    visible = scenario.infra.as_role(
        "pg_worker", "SELECT run_id::text AS run_id FROM nessa.run_inputs", run=run_id
    )
    # Scoped like run outputs and keys: the run's workspace (while its requester may act),
    # so the worker sees that workspace's sealed inputs and no other workspace's.
    assert {row["run_id"] for row in visible} == {run_id, second}
    assert elsewhere not in {row["run_id"] for row in visible}
    finisher = scenario.worker("finisher")  # leave no queued run for a later test's worker
    scenario.wait_terminal(second)
    scenario.wait_terminal(elsewhere)
    assert finisher.stop() == 0


def test_the_export_carries_the_conversation_and_its_decisions(scenario: Scenario) -> None:
    turn = run_turn(scenario, "")
    scenario.decide(turn["turn_id"], {"expected_version": 1, "accept": []})

    exported = scenario.api.get(
        f"/v1/workspaces/{scenario.workspace_id}/export", scenario.token
    ).json()

    assert exported["format_version"] == 2
    [shown] = exported["interview_turns"]
    assert shown["turn_id"] == turn["turn_id"]
    assert shown["proposal"]["changes"]
    assert shown["decision"]["accepted_change_ids"] == []
