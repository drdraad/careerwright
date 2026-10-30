"""The world's first moments end to end against real PostgreSQL 16, DBOS and the labelled ESCO
sample (plan section 4; Sprint W SW.5; ADR 0007 decision 13; ADR 0014 decision 3): the first
question's type-ahead, the first answer saved through the profile, the origin's usual skills
and first destinations joined by shared essential skills, "I've used this", and the
overlooked strength, proposed once per turn that added answers, verified, and recorded only
when the person confirms it. No model is called except the fake provider and the fixtures."""

import dataclasses
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from careerwright.api.app import create_app
from careerwright.api.deps import ApiDependencies
from careerwright.config import RuntimeMode
from tests.integration.durable import Scenario, make_scenario
from tests.support.client import ApiClient, profile_with
from tests.support.infra import API_BASE, Infra

pytestmark = pytest.mark.integration


def titles(api: ApiClient, token: str, typed: str, **params: Any) -> Any:
    return api.get("/v1/taxonomy/titles", token, q=typed, **params)


def occupation(api: ApiClient, token: str, title: str) -> str:
    [match] = [m for m in titles(api, token, title).json()["matches"] if m["title"] == title]
    return str(match["concept_id"])


def choose_role(api: ApiClient, token: str, workspace: str, concept: str, version: int) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace}/origin/role",
        token,
        {"expected_version": version, "concept_id": concept},
    )


def origin(api: ApiClient, token: str, workspace: str) -> dict[str, Any]:
    found = api.get(f"/v1/workspaces/{workspace}/origin", token)
    assert found.status_code == 200, found.text
    body: dict[str, Any] = found.json()
    return body


@pytest.mark.req("TAX1-01", "DIV1-03")
def test_the_type_ahead_offers_esco_titles_as_typed_and_never_invents_one(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    typed = titles(api, ada, "IT supp").json()
    bus = titles(api, ada, "bus").json()
    nothing = titles(api, ada, "zqxj").json()
    no_word = titles(api, ada, "!!")

    [help_desk] = typed["matches"]
    assert (help_desk["title"], help_desk["matched_label"], help_desk["label_kind"]) == (
        "ICT help desk agent",
        "IT support technician",
        "alternative",
    )
    assert help_desk["concept_kind"] == "esco"
    assert typed["release"]["sample"] is True
    # Titles that begin with what was typed first; one entry per occupation, each by a label
    # with a word beginning "bus" (the data analyst is also a "business data analyst").
    shown = [m["title"] for m in bus["matches"]]
    assert shown[:2] == ["bus driver", "trolley bus driver"]
    assert len(shown) == len(set(shown)) == bus["total"]
    assert all(
        any(word.startswith("bus") for word in m["matched_label"].casefold().split())
        for m in bus["matches"]
    )
    assert (nothing["matches"], nothing["total"]) == ([], 0)  # an honest empty answer
    assert (no_word.status_code, no_word.json()["error"]["details"]["reason"]) == (
        422,
        "no_search_terms",
    )
    [hidden] = infra.query(
        "SELECT label FROM careerwright.occupation_labels WHERE kind = 'hidden' "
        "ORDER BY label LIMIT 1"
    )
    offered = titles(api, ada, str(hidden["label"])).json()["matches"]
    assert str(hidden["label"]) not in [m["matched_label"] for m in offered]


@pytest.mark.req("PROF-07", "PROF-01")
def test_the_first_answer_is_saved_through_the_profile_with_its_esco_occupation(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace = api.create_workspace(ada, "First answer (synthetic)")["workspace_id"]
    bookkeeper = occupation(api, ada, "bookkeeper")

    before = origin(api, ada, workspace)
    chosen = choose_role(api, ada, workspace, bookkeeper, 0)
    again = choose_role(api, ada, workspace, bookkeeper, 1)
    stale = choose_role(api, ada, workspace, bookkeeper, 0)

    assert before["role"]["state"] == "not_answered"
    assert (before["usual_skills"], before["destinations"]) == ([], [])
    assert chosen.status_code == 201, chosen.text
    role = chosen.json()["document"]["current_role"]
    assert (role["state"], role["value"]) == ("provided", "bookkeeper")
    [source] = infra.query(
        "SELECT kind, locator FROM careerwright.source_references WHERE source_ref_id = %s",
        (role["source_ref_id"],),
    )
    assert source["kind"] == "occupation_choice"
    assert str(source["locator"]).startswith("http://data.europa.eu/esco/occupation/")
    assert (again.status_code, again.json()["version"]) == (200, 1)  # already the role
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"


@pytest.mark.req("ASSESS-01", "DIV1-10", "DIV1-12")
def test_the_origin_shows_usual_skills_and_destinations_joined_by_shared_skills(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Origin (synthetic)")["workspace_id"]
    choose_role(api, ada, workspace, occupation(api, ada, "bookkeeper"), 0)

    shown = origin(api, ada, workspace)

    assert (shown["role"]["state"], shown["role"]["chosen"]) == ("esco", True)
    assert shown["role"]["occupation"]["title"] == "bookkeeper"
    usual = shown["usual_skills"]
    assert len(usual) == 6  # the sample keeps six essential skills per occupation
    assert {s["state"] for s in usual} == {"usual_in_role"}
    assert all(s["subject"] == f"esco:{s['skill_id']}" for s in usual)
    # The sample's accounting assistant shares five of the bookkeeper's essential skills; the
    # role itself is the origin, never a destination.
    titles_shown = [d["title"] for d in shown["destinations"]]
    assert titles_shown == ["accounting assistant"]
    [assistant] = shown["destinations"]
    assert assistant["channels"] == ["shared_skills"]
    assert assistant["direction"] == "close_to_current"  # the same kind of work
    assert "5 of the same essential skills" in assistant["why_it_could_suit"][0]
    assert shown["connection"] is None  # nothing outside the bookkeeper's kind of work
    assert shown["release"]["sample"] is True

    used = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/capability/evidence",
        ada,
        {"expected_version": 0, "subject": usual[0]["subject"], "answer": "used"},
    )
    levelled = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/capability/evidence",
        ada,
        {
            "expected_version": 1,
            "subject": usual[1]["subject"],
            "answer": "used",
            "self_assessed_level": 2,
        },
    )
    elsewhere = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/capability/evidence",
        ada,
        {
            "expected_version": 1,
            "subject": "esco:00000000-0000-4000-8000-000000000000",
            "answer": "used",
        },
    )

    assert used.status_code == 201, used.text
    assert levelled.json()["error"]["details"]["reason"] == "level_without_rubric"
    assert elsewhere.json()["error"]["details"]["reason"] == "not_a_skill"
    after = origin(api, ada, workspace)
    states = {s["subject"]: (s["state"], s["answer"]) for s in after["usual_skills"]}
    assert states[usual[0]["subject"]] == ("self_reported", "used")
    assert states[usual[1]["subject"]] == ("usual_in_role", None)
    assert after["capability_version"] == 1


@pytest.mark.req("DIV1-03", "DIV1-04")
def test_a_role_esco_does_not_hold_joins_nothing_and_a_shared_title_asks_which(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Unmatched role (synthetic)")["workspace_id"]

    def role(text: str, version: int) -> dict[str, Any]:
        put = api.write(
            "PUT",
            f"/v1/workspaces/{workspace}/profile",
            ada,
            {"expected_version": version, "profile": profile_with(current_role=text)},
        )
        assert put.status_code == 201, put.text
        return origin(api, ada, workspace)

    unmatched = role("Warehouse shift supervisor", 0)
    shared = role("bus operator", 1)  # an alternative label of two occupations

    assert unmatched["role"]["state"] == "not_in_esco"
    assert (unmatched["usual_skills"], unmatched["destinations"]) == ([], [])
    assert shared["role"]["state"] == "ambiguous"
    assert sorted(c["title"] for c in shared["role"]["choices"]) == [
        "bus driver",
        "trolley bus driver",
    ]
    assert (shared["usual_skills"], shared["destinations"]) == ([], [])  # nothing guessed


@pytest.fixture
def demo_api(api_deps: ApiDependencies) -> Iterator[ApiClient]:
    settings = api_deps.settings.model_copy(update={"runtime_mode": RuntimeMode.DEMO})
    with TestClient(
        create_app(dataclasses.replace(api_deps, settings=settings)),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57004),
    ) as client:
        yield ApiClient(client)


def decided_turn(
    api: ApiClient, token: str, workspace: str, scenario: Scenario, message: str, version: int
) -> str:
    """A turn, run by a worker, whose proposals are all accepted (limits confirmed)."""
    submitted = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns",
        token,
        {"expected_profile_version": version, "message": message},
    )
    assert submitted.status_code == 202, submitted.text
    turn_id = str(submitted.json()["turn_id"])
    worker = scenario.worker(f"turn-{version}")
    scenario.wait_terminal(turn_id)
    assert worker.stop() == 0
    proposal = api.get(f"/v1/workspaces/{workspace}/interview/turns/{turn_id}", token).json()[
        "proposal"
    ]
    changes = proposal["changes"]
    decided = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/decision",
        token,
        {
            "expected_version": version,
            "accept": [c["change_id"] for c in changes],
            "confirm_hard_constraints": [c["field"] for c in changes if c["hard_constraint"]],
        },
    )
    assert decided.status_code == 201, decided.text
    return turn_id


def ask_strength(api: ApiClient, token: str, workspace: str, turn_id: str, version: int) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/strength",
        token,
        {"expected_profile_version": version},
    )


def strength(api: ApiClient, token: str, workspace: str, turn_id: str) -> dict[str, Any]:
    found = api.get(f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/strength", token)
    assert found.status_code == 200, found.text
    body: dict[str, Any] = found.json()
    return body


@pytest.mark.req("BND1-11", "TEST1-10", "ASSESS-01")
def test_a_demo_workspace_shows_one_scripted_labelled_strength_and_calls_no_provider(
    infra: Infra, api: ApiClient, demo_api: ApiClient, ada: str, tmp_path: Path
) -> None:
    workspace = demo_api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Demo strength", "data_mode": "demo", "synthetic": True},
    ).json()["workspace_id"]
    choose_role(demo_api, ada, workspace, occupation(api, ada, "bookkeeper"), 0)
    scenario = make_scenario(infra, api, ada, tmp_path)
    turn_id = decided_turn(
        demo_api, ada, workspace, scenario, "I enjoy reconciling accounting entries", 1
    )

    asked = ask_strength(demo_api, ada, workspace, turn_id, 2)
    assert asked.status_code == 202, asked.text
    run = asked.json()["run"]
    assert (run["kind"], run["model_id"], run["model_mode"]) == (
        "strength_proposal",
        "careerwright-fixture-strength-1",
        "fixture",
    )
    assert "proposal" not in asked.json()  # a receipt never holds the proposal
    worker = scenario.worker("strength")
    scenario.wait_terminal(run["run_id"])
    assert worker.stop() == 0

    found = strength(api, ada, workspace, turn_id)
    assert found["found"] is True
    proposed = found["proposal"]
    assert proposed["label"] == "Demo example (synthetic)"
    assert proposed["quotation"] == "reconciling accounting entries"
    assert proposed["answer_field"] == "enjoyed_tasks"
    assert proposed["destination"]["title"] == "accounting assistant"
    assert proposed["destination"]["kind"] == "horizon"
    record = api.get(
        f"/v1/taxonomy/occupations/{proposed['destination']['concept_id']}", ada
    ).json()
    essential = {s["skill_id"] for s in record["skills"] if s["relation"] == "essential"}
    assert proposed["skill_id"] in essential  # essential to that destination in ESCO
    [attempt] = scenario.attempts(run["run_id"])
    assert (attempt["spend_state"], attempt["cost_nano_usd"]) == ("none", 0)

    confirmed = demo_api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/strength/decision",
        ada,
        {"expected_version": 0, "confirm": True},
    )
    assert confirmed.status_code == 201, confirmed.text
    decision = confirmed.json()["decision"]
    assert (decision["decision"], confirmed.json()["capability_version"]) == ("confirmed", 1)
    [claim] = infra.query(
        "SELECT subject, answer, self_assessed_level, example, method "
        "FROM careerwright.skill_evidence WHERE evidence_id = %s",
        (decision["evidence_id"],),
    )
    assert claim == {
        "subject": proposed["subject"],
        "answer": "used",  # the person's own claim: self-reported, never evidence
        "self_assessed_level": None,
        "example": "reconciling accounting entries",
        "method": "self_report",
    }


@pytest.fixture
def live(infra: Infra, api: ApiClient, ada: str, tmp_path: Path) -> Iterator[Scenario]:
    started = make_scenario(infra, api, ada, tmp_path)
    chosen = choose_role(api, ada, started.workspace_id, occupation(api, ada, "bookkeeper"), 1)
    assert chosen.status_code == 201, chosen.text
    yield started
    for worker in started.workers:
        worker.kill_if_running()


@pytest.mark.req("MODEL-02", "ASSESS-01")
def test_a_strength_is_asked_once_per_turn_verified_and_declining_records_nothing(
    live: Scenario,
) -> None:
    api, token, workspace = live.api, live.token, live.workspace_id
    undecided = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns",
        token,
        {"expected_profile_version": 2, "message": "I could work in Leeds."},
    ).json()["turn_id"]
    turn_id = decided_turn(api, token, workspace, live, "I enjoy reconciling ledgers", 2)

    no_answers = ask_strength(api, token, workspace, undecided, 3)
    asked = ask_strength(api, token, workspace, turn_id, 3)
    again = ask_strength(api, token, workspace, turn_id, 3)
    assert (no_answers.status_code, no_answers.json()["error"]["details"]["reason"]) == (
        422,
        "no_new_answers",
    )
    assert asked.status_code == 202, asked.text
    assert (again.status_code, again.json()["strength_id"]) == (200, asked.json()["strength_id"])
    run = asked.json()["run"]
    assert (run["kind"], run["model_mode"], run["profile_version"]) == (
        "strength_proposal",
        "contributor",  # a synthetic workspace: the test model, with the person's key
        3,
    )
    worker = live.worker("strength")
    live.wait_terminal(run["run_id"])
    assert worker.stop() == 0

    found = strength(api, token, workspace, turn_id)
    assert found["run"]["status"] == "complete"
    assert found["proposal"]["quotation"] == "reconciling ledgers"
    assert found["proposal"]["label"] is None
    declined = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/strength/decision",
        token,
        {"expected_version": 0, "confirm": False},
    )
    twice = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/strength/decision",
        token,
        {"expected_version": 0, "confirm": True},
    )
    assert declined.status_code == 201, declined.text
    assert declined.json() == {
        "decision": {**declined.json()["decision"], "decision": "declined", "evidence_id": None},
        "capability_version": 0,
    }
    assert twice.json()["error"]["code"] == "ALREADY_DECIDED"
    assert (
        live.infra.query(
            "SELECT * FROM careerwright.skill_evidence WHERE workspace_id = %s", (workspace,)
        )
        == []
    )  # declining records nothing about the skill
    assert live.leaks() == []


@pytest.mark.req("PROF-09")
def test_a_turn_the_support_screen_answered_never_looks_for_a_strength(
    live: Scenario,
) -> None:
    api, token, workspace = live.api, live.token, live.workspace_id
    turn_id = decided_turn(
        api, token, workspace, live, "I enjoy reconciling ledgers but I want to die", 2
    )

    held = ask_strength(api, token, workspace, turn_id, 3)

    assert (held.status_code, held.json()["error"]["details"]["reason"]) == (422, "held_back")
    assert (
        live.infra.query(
            "SELECT * FROM careerwright.strength_proposals WHERE workspace_id = %s", (workspace,)
        )
        == []
    )  # refused before any run exists, and nothing about the screen is stored
