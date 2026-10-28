"""The person's interview choices and the support flow, against real PostgreSQL 16 (S2.3,
S2.6; PROF-04, PROF-08, PROF-09, STATE-08): entry and mode reach the interviewer sealed in
the turn's input; a message with a risk stem is sent as usual, with the support panel and a
smaller-step turn, and nothing of the flow is stored; the salary floor is a hard limit set
only by confirmation."""

import json
import logging
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from nessa.identity.keyring import SealedValue, load_keyring
from nessa.identity.receipts import fingerprint
from nessa.identity.runs import input_context
from nessa.profile import safety
from tests.integration.durable import Scenario, make_scenario
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra
from tools.leak_scan import Needle, scan

pytestmark = pytest.mark.integration

DISTRESS = "Some days I just want to die, and I don't know why I'm even looking for jobs."
SERVICES = {"Emergency services", "NHS 111", "Samaritans", "Shout"}


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
        "interview-turn-4",
    )
    worker = scenario.worker("worker")  # leave no queued run behind
    scenario.wait_terminal(turn["turn_id"])
    assert worker.stop() == 0


@pytest.mark.req("PROF-09")
def test_a_message_with_a_risk_stem_is_sent_with_the_support_panel_and_none_of_it_is_stored(
    scenario: Scenario, caplog: pytest.LogCaptureFixture
) -> None:
    # Controller ruling, fix round 4: one screen; the message proceeds; the panel and the
    # smaller-step turn are derived from the message each time and never stored.
    turns = f"/v1/workspaces/{scenario.workspace_id}/interview/turns"
    plain = "I could work in Leeds."
    key = uuid.uuid4()

    with caplog.at_level(logging.DEBUG):
        flagged = scenario.api.write(
            "POST",
            turns,
            scenario.token,
            {"expected_profile_version": 1, "message": DISTRESS},
            key=key,
        )
        ordinary = scenario.api.write(
            "POST", turns, scenario.token, {"expected_profile_version": 1, "message": plain}
        )
        replayed = scenario.api.write(
            "POST",
            turns,
            scenario.token,
            {"expected_profile_version": 1, "message": DISTRESS},
            key=key,
        )
        worker = scenario.worker("worker")
        for body in (flagged.json(), ordinary.json()):
            scenario.wait_terminal(body["turn_id"])
        assert worker.stop() == 0
        listed = scenario.api.get(turns, scenario.token).json()["items"]
        exported = scenario.api.get(
            f"/v1/workspaces/{scenario.workspace_id}/export", scenario.token
        ).text

    assert flagged.status_code == 202, flagged.text  # sent: no hold, no extra step
    panel = flagged.json()["support_note"]
    assert panel["policy_version"] == safety.POLICY_VERSION == "support-policy-4"
    assert "provisional" in panel["review_status"]
    assert {r["name"] for r in panel["resources"]} == SERVICES
    assert "sent to Nessa as usual" in panel["message"]
    assert (ordinary.status_code, ordinary.json()["support_note"]) == (202, None)
    assert replayed.json()["turn_id"] == flagged.json()["turn_id"]  # the same turn, replayed
    assert replayed.json()["support_note"] == panel  # recomputed from the request
    # Only that turn had the smaller step: the interviewer asked no question in it.
    by_message = {t["message"]: t for t in listed}
    assert by_message.keys() == {DISTRESS, plain}
    assert by_message[DISTRESS]["proposal"]["next_question"] is None
    assert by_message[plain]["proposal"]["next_question"] is not None
    assert all("support_note" not in t for t in listed)
    # Nothing of the flow is stored or logged: no receipt, turn, run, event, journal, export
    # or log holds the panel's words, its services, the policy or the turn's instruction.
    logs = [(log.name, log.read_text(encoding="utf-8")) for log in scenario.logs if log.exists()]
    cells = [
        *scenario.infra.database_cells("nessa_app"),
        *scenario.infra.database_cells("nessa_dbos"),
        *logs,
        ("api log", caplog.text),
        ("export", exported),
    ]
    needles = [
        Needle("panel", safety.SUPPORT_NOTE),
        Needle("services", "116 123"),
        Needle("policy", safety.POLICY_VERSION),
        Needle("instruction", safety.SUPPORT_TURN_INSTRUCTION),
    ]
    assert scan(cells, needles) == []
    receipts = scenario.infra.query(
        "SELECT response::text AS response FROM nessa.command_receipts WHERE workspace_id = %s",
        (scenario.workspace_id,),
    )
    assert receipts
    assert not [r for r in receipts if "support" in r["response"]]


@pytest.mark.req("PROF-09")
def test_a_turn_receipt_stored_before_the_redesign_is_refused_never_a_500(
    scenario: Scenario,
) -> None:
    # Re-review 3, M-b: a round-2 receipt holds the support note beside the turn, and its
    # request carried `send_after_support`. That field is gone, so the request a client sends
    # now is a different request: refused with the key-reuse error. An old client still
    # sending the field is refused as invalid. Neither is a 500.
    turns = f"/v1/workspaces/{scenario.workspace_id}/interview/turns"
    message = "I volunteer on a suicide prevention helpline and want paid work like it."
    turn = scenario.submit_turn(message)
    [owner] = scenario.infra.query(
        "SELECT owner_actor_id FROM nessa.workspaces WHERE workspace_id = %s",
        (scenario.workspace_id,),
    )
    old_request = {
        "workspace_id": scenario.workspace_id,
        "expected_profile_version": 1,
        "message": message,
        "send_after_support": False,
    }
    old_note = {"policy": "risk_mention", "policy_version": "support-policy-2", "resources": []}
    old_response = {**turn, "support_note": old_note}
    key = uuid.uuid4()
    scenario.infra.query(
        "INSERT INTO nessa.command_receipts (actor_id, idempotency_key, command, "
        "request_sha256, status_code, response, workspace_id) "
        "VALUES (%s, %s, 'submit_turn', %s, 202, %s::jsonb, %s)",
        (
            owner["owner_actor_id"],
            key,
            fingerprint("submit_turn", old_request),
            json.dumps(old_response),
            scenario.workspace_id,
        ),
    )
    try:
        replayed = scenario.api.write(
            "POST",
            turns,
            scenario.token,
            {"expected_profile_version": 1, "message": message},
            key=key,
        )
        old_client = scenario.api.write(
            "POST",
            turns,
            scenario.token,
            {"expected_profile_version": 1, "message": message, "send_after_support": False},
            key=key,
        )
    finally:
        scenario.infra.query(
            "DELETE FROM nessa.command_receipts WHERE idempotency_key = %s", (key,)
        )

    assert (replayed.status_code, replayed.json()["error"]["code"]) == (
        422,
        "IDEMPOTENCY_KEY_REUSED",
    )
    assert (old_client.status_code, old_client.json()["error"]["code"]) == (
        422,
        "VALIDATION_FAILED",
    )
    worker = scenario.worker("worker")
    scenario.wait_terminal(turn["turn_id"])
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
