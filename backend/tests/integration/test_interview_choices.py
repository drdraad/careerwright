"""The person's interview choices and the support response, against real PostgreSQL 16
(S2.3, S2.6; PROF-04, PROF-08, PROF-09, STATE-08): entry and mode reach the interviewer
sealed in the turn's input; explicit acute distress is answered before any model call and
nothing is stored; the salary floor is a hard limit set only by confirmation."""

import json
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from nessa.identity.keyring import SealedValue, load_keyring
from nessa.identity.runs import input_context
from tests.integration.durable import Scenario, make_scenario
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra

pytestmark = pytest.mark.integration

DISTRESS = "Some days I just want to die, and I don't know why I'm even looking for jobs."


@pytest.fixture
def scenario(infra: Infra, api: ApiClient, ada: str, tmp_path: Path) -> Iterator[Scenario]:
    started = make_scenario(infra, api, ada, tmp_path)
    yield started
    for worker in started.workers:
        worker.kill_if_running()


def preferences(scenario: Scenario, version: int, **choices: Any) -> Any:
    body = {
        "expected_version": version,
        "entry_mode": None,
        "conversation_mode": None,
        "paused": False,
        **choices,
    }
    return scenario.api.write(
        "PUT",
        f"/v1/workspaces/{scenario.workspace_id}/interview/preferences",
        scenario.token,
        body,
    )


@pytest.mark.req("PROF-08", "PROF-09")
def test_the_entry_mode_and_pause_are_saved_with_versions_and_reach_the_interviewer(
    scenario: Scenario, infra: Infra, ben: str
) -> None:
    path = f"/v1/workspaces/{scenario.workspace_id}/interview/preferences"
    fresh = scenario.api.get(path, scenario.token).json()

    saved = preferences(scenario, 0, entry_mode="sure", conversation_mode="gentle")
    paused = preferences(scenario, 1, entry_mode="sure", conversation_mode="gentle", paused=True)
    stale = preferences(scenario, 1, entry_mode="unsure")

    assert (fresh["version"], fresh["entry_mode"], fresh["paused"]) == (0, None, False)
    assert saved.status_code == 200, saved.text
    assert (saved.json()["entry_mode"], saved.json()["conversation_mode"]) == ("sure", "gentle")
    assert (paused.json()["version"], paused.json()["paused"]) == (2, True)
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert scenario.api.get(path, ben).status_code == 404  # another account sees nothing
    resumed = preferences(scenario, 2, entry_mode="sure", conversation_mode="gentle")
    assert resumed.json()["paused"] is False

    turn = scenario.submit_turn("I want to be a data quality analyst.")
    [row] = infra.query(
        "SELECT key_version, nonce, ciphertext FROM nessa.run_inputs WHERE run_id = %s",
        (turn["turn_id"],),
    )
    keyring = load_keyring(infra.api_settings().master_key_dir)
    sealed = SealedValue(row["key_version"], bytes(row["nonce"]), bytes(row["ciphertext"]))
    opened = json.loads(
        keyring.open(
            sealed, input_context(uuid.UUID(scenario.workspace_id), uuid.UUID(turn["turn_id"]))
        )
    )
    assert (opened["entry_mode"], opened["conversation_mode"], opened["prompt_version"]) == (
        "sure",
        "gentle",
        "interview-turn-3",
    )
    worker = scenario.worker("worker")  # leave no queued run behind
    scenario.wait_terminal(turn["turn_id"])
    assert worker.stop() == 0


@pytest.mark.req("PROF-09")
def test_explicit_acute_distress_gets_support_before_any_model_call_and_nothing_is_stored(
    scenario: Scenario,
) -> None:
    turns = f"/v1/workspaces/{scenario.workspace_id}/interview/turns"
    events_before = scenario.api.get(
        f"/v1/workspaces/{scenario.workspace_id}/events", scenario.token
    ).json()["last_seq"]
    receipts = "SELECT count(*) FROM nessa.command_receipts WHERE workspace_id = %s"
    receipts_before = scenario.infra.query(receipts, (scenario.workspace_id,))

    response = scenario.api.write(
        "POST", turns, scenario.token, {"expected_profile_version": 1, "message": DISTRESS}
    )

    assert response.status_code == 200, response.text
    support = response.json()
    assert (support["policy"], support["sent_to_interviewer"]) == ("acute_distress", False)
    assert "provisional" in support["review_status"]
    assert {r["name"] for r in support["resources"]} == {
        "Emergency services",
        "NHS 111",
        "Samaritans",
        "Shout",
    }
    assert scenario.api.get(turns, scenario.token).json()["items"] == []
    assert (
        scenario.infra.query(
            "SELECT run_id FROM nessa.runs WHERE workspace_id = %s AND kind = 'interview_turn'",
            (scenario.workspace_id,),
        )
        == []
    )
    events = scenario.api.get(
        f"/v1/workspaces/{scenario.workspace_id}/events", scenario.token
    ).json()
    assert events["last_seq"] == events_before  # nothing happened
    # Not even an idempotency receipt (it would keep a fingerprint of the message, A-M8).
    assert scenario.infra.query(receipts, (scenario.workspace_id,)) == receipts_before
    assert scenario.leaks("don't know why I'm even looking") == []

    sent = scenario.api.write(
        "POST",
        turns,
        scenario.token,
        {"expected_profile_version": 1, "message": DISTRESS, "send_after_support": True},
    )
    assert sent.status_code == 202  # the person's choice, after seeing the support response
    worker = scenario.worker("worker")
    scenario.wait_terminal(sent.json()["turn_id"])
    assert worker.stop() == 0


@pytest.mark.req("PROF-09")
def test_any_other_risk_word_is_sent_as_usual_with_a_support_note(scenario: Scenario) -> None:
    # Tier 2 (controller ruling, fix round 2): never blocked, never silently dropped.
    turns = f"/v1/workspaces/{scenario.workspace_id}/interview/turns"
    mention = "I volunteer on a suicide prevention helpline and want paid work like it."
    plain = "I could work in Leeds."

    key = uuid.uuid4()
    noted = scenario.api.write(
        "POST", turns, scenario.token, {"expected_profile_version": 1, "message": mention}, key=key
    )
    ordinary = scenario.api.write(
        "POST", turns, scenario.token, {"expected_profile_version": 1, "message": plain}
    )

    assert noted.status_code == 202, noted.text  # sent to the interviewer as usual
    note = noted.json()["support_note"]
    assert (note["policy"], note["policy_version"]) == ("risk_mention", "support-policy-3")
    assert {r["name"] for r in note["resources"]} == {
        "Emergency services",
        "NHS 111",
        "Samaritans",
        "Shout",
    }
    assert "sent to Nessa as usual" in note["message"]
    assert ordinary.status_code == 202
    assert ordinary.json()["support_note"] is None
    listed = scenario.api.get(turns, scenario.token).json()["items"]
    assert {t["message"] for t in listed} == {mention, plain}
    assert all("support_note" not in t for t in listed)
    # Never stored (re-review 2, I-3): not even in the idempotency receipt; a replay of the
    # same request recomputes the note from the request.
    receipts = scenario.infra.query(
        "SELECT response::text AS response FROM nessa.command_receipts WHERE workspace_id = %s",
        (scenario.workspace_id,),
    )
    assert receipts
    assert not [
        r for r in receipts if "risk_mention" in r["response"] or "support" in r["response"]
    ]
    replayed = scenario.api.write(
        "POST", turns, scenario.token, {"expected_profile_version": 1, "message": mention}, key=key
    )
    assert replayed.json()["turn_id"] == noted.json()["turn_id"]  # the same turn, replayed
    assert replayed.json()["support_note"] == note
    worker = scenario.worker("worker")
    for body in (noted.json(), ordinary.json()):
        scenario.wait_terminal(body["turn_id"])
    assert worker.stop() == 0


@pytest.mark.req("PROF-04", "STATE-08", "PROF-05")
def test_a_salary_floor_is_saved_only_when_confirmed_and_unknown_is_never_zero(
    scenario: Scenario,
) -> None:
    turn = scenario.submit_turn("I could work in Leeds but need at least £26,000 a year.")
    worker = scenario.worker("worker")
    scenario.wait_terminal(turn["turn_id"])
    assert worker.stop() == 0
    shown = scenario.turn(turn["turn_id"])
    changes = {c["field"]: c for c in shown["proposal"]["changes"]}
    salary = changes["minimum_salary"]
    assert salary["hard_constraint"]
    assert salary["value"] == {
        "amount": {"minor_units": 2_600_000, "currency": "GBP"},
        "period": "year",
        "basis": "gross",
    }

    unconfirmed = scenario.decide(
        turn["turn_id"],
        {"expected_version": 1, "accept": [salary["change_id"]], "confirm_hard_constraints": []},
    )
    assert (unconfirmed.status_code, unconfirmed.json()["error"]["code"]) == (
        409,
        "CONFIRMATION_REQUIRED",
    )
    assert unconfirmed.json()["error"]["details"]["fields"] == ["minimum_salary"]
    assert scenario.profile()["document"]["minimum_salary"]["state"] == "unasked"
    confirmed = scenario.decide(
        turn["turn_id"],
        {
            "expected_version": 1,
            "accept": [salary["change_id"]],
            "confirm_hard_constraints": ["minimum_salary"],
        },
    )
    assert confirmed.status_code == 201, confirmed.text
    assert confirmed.json()["profile"]["document"]["minimum_salary"]["value"] == salary["value"]

    profile_path = f"/v1/workspaces/{scenario.workspace_id}/profile"
    stale = scenario.api.write(
        "PUT",
        profile_path,
        scenario.token,
        {
            "expected_version": 1,
            "profile": {**profile_with(), "minimum_salary": {"state": "unknown"}},
        },
    )
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert scenario.profile()["document"]["minimum_salary"]["value"] == salary["value"]
    unknown = scenario.api.write(
        "PUT",
        profile_path,
        scenario.token,
        {
            "expected_version": 2,
            "profile": {**profile_with(), "minimum_salary": {"state": "unknown"}},
        },
    )
    assert unknown.status_code == 201, unknown.text
    stored = unknown.json()["document"]["minimum_salary"]
    assert (stored["state"], stored.get("value")) == ("unknown", None)  # never £0
