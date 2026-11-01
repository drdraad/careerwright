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


def choose_role(
    api: ApiClient, token: str, workspace: str, concept: str, version: int, **label: str
) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace}/origin/role",
        token,
        {"expected_version": version, "concept_id": concept, **label},
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
    [reason] = assistant["reasons"]
    assert (reason["reason"], reason["shared"]) == ("joined_by_shared_skills", 5)
    assert "connection" not in shown  # shared skills are a plain fact on each destination
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


@pytest.mark.req("DIV1-02", "DIV1-04")
def test_a_role_no_other_occupation_joins_says_what_careerwright_found(
    api: ApiClient, ada: str
) -> None:
    # Task W2B re-review 5: the empty join's words had no test. In the sample no occupation
    # shares 3 or more essential skills with the cook; the fact says what Careerwright found,
    # never what ESCO holds (the web words it; Task 6d slice A).
    workspace = api.create_workspace(ada, "Empty join (synthetic)")["workspace_id"]
    choose_role(api, ada, workspace, occupation(api, ada, "cook"), 0)

    shown = origin(api, ada, workspace)

    assert shown["destinations"] == []
    assert shown["fewer_reasons"] == [
        {
            "reason": "no_shared_occupation",
            "outcome": "found_none",
            "title": "cook",
            "min_shared": 3,
        }
    ]


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

    # The person chooses which they meant for the words they already typed: the words stay,
    # and the role now cites the chosen occupation (review M4: the `recite` path).
    driver = next(c["concept_id"] for c in shared["role"]["choices"] if c["title"] == "bus driver")
    chosen = choose_role(api, ada, workspace, driver, 2, label="bus operator")
    again = choose_role(api, ada, workspace, driver, 3, label="bus operator")
    resolved = origin(api, ada, workspace)

    assert chosen.status_code == 201, chosen.text
    assert chosen.json()["version"] == 3  # a new version: the same words, a new source
    assert (again.status_code, again.json()["version"]) == (200, 3)  # already the role
    assert (resolved["role"]["text"], resolved["role"]["state"], resolved["role"]["chosen"]) == (
        "bus operator",
        "esco",
        True,
    )
    assert resolved["role"]["occupation"]["title"] == "bus driver"
    assert resolved["usual_skills"]  # one occupation: its essential skills, usual in the role


@pytest.mark.req("PROF-07", "PROF-01")
def test_the_role_keeps_the_title_the_person_picked_and_resolves_by_its_occupation(
    api: ApiClient, ada: str
) -> None:
    # Review M5: picking "IT support technician" (ESCO's other title for the ICT help desk
    # agent) keeps the person's title; only a title ESCO lists for that occupation is taken.
    workspace = api.create_workspace(ada, "Picked title (synthetic)")["workspace_id"]
    [picked] = titles(api, ada, "IT supp").json()["matches"]

    foreign = choose_role(api, ada, workspace, picked["concept_id"], 0, label="bus operator")
    chosen = choose_role(
        api, ada, workspace, picked["concept_id"], 0, label=picked["matched_label"]
    )
    shown = origin(api, ada, workspace)

    assert (foreign.status_code, foreign.json()["error"]["details"]["reason"]) == (
        422,
        "not_its_title",
    )
    assert chosen.status_code == 201, chosen.text
    assert chosen.json()["document"]["current_role"]["value"] == "IT support technician"
    assert (shown["role"]["text"], shown["role"]["state"], shown["role"]["chosen"]) == (
        "IT support technician",
        "esco",
        True,
    )
    assert shown["role"]["occupation"]["title"] == "ICT help desk agent"


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


@pytest.mark.req("DIV1-14", "PROF-10", "MAP1-09")
def test_the_conversation_s_change_of_the_role_keeps_the_role_s_record(
    infra: Infra, api: ApiClient, demo_api: ApiClient, ada: str, tmp_path: Path
) -> None:
    # App re-review N-M2 (Task 6d slice B fix round 2): the role's record was tested through
    # What we know only. A decision on the conversation's proposal of the role goes through the
    # same write path, so the same title in other capitals keeps the person's closest choice.
    workspace = demo_api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Role by conversation", "data_mode": "demo", "synthetic": True},
    ).json()["workspace_id"]
    path = f"/v1/workspaces/{workspace}/origin/role"
    named = demo_api.write(
        "POST", f"{path}/title", ada, {"expected_version": 0, "title": "Registered nurse"}
    )
    assert named.status_code == 201, named.text
    [group] = origin(demo_api, ada, workspace)["role"]["closest"]["groups"]
    specialist = next(o["concept_id"] for o in group["occupations"] if "specialist" in o["title"])
    chosen = demo_api.write(
        "POST", f"{path}/closest", ada, {"expected_version": 1, "concept_id": specialist}
    )
    assert chosen.status_code == 201, chosen.text
    scenario = make_scenario(infra, api, ada, tmp_path)

    # The demo interviewer proposes the role in the message's words; the decision accepts it.
    decided_turn(demo_api, ada, workspace, scenario, "I am a Registered Nurse.", 2)

    profile = demo_api.get(f"/v1/workspaces/{workspace}/profile", ada).json()
    assert (profile["version"], profile["document"]["current_role"]["value"]) == (
        3,
        "Registered Nurse",
    )
    shown = origin(demo_api, ada, workspace)
    role = shown["role"]
    assert (role["text"], role["state"], role["chosen"], role["kind"]) == (
        "Registered Nurse",
        "esco",
        True,
        "ons",
    )
    assert role["occupation"]["concept_id"] == specialist
    assert (role["closest"]["decision"], role["closest"]["chosen"]) == ("chosen", specialist)
    assert shown["usual_skills"]  # the chosen occupation's skills still seed the role


def run_strength(
    api: ApiClient, token: str, workspace: str, scenario: Scenario, turn_id: str, version: int
) -> dict[str, Any]:
    """Ask for the turn's strength, run it with a worker and read it."""
    asked = ask_strength(api, token, workspace, turn_id, version)
    assert asked.status_code == 202, asked.text
    worker = scenario.worker(f"strength-{version}")
    scenario.wait_terminal(asked.json()["run"]["run_id"])
    assert worker.stop() == 0
    return strength(api, token, workspace, turn_id)


@pytest.mark.req("ASSESS-01", "BND1-11")
def test_a_strength_reads_only_the_turn_s_new_answers_so_a_declined_one_is_not_offered_again(
    infra: Infra, api: ApiClient, demo_api: ApiClient, ada: str, tmp_path: Path
) -> None:
    # Review I3: the run reads the answers the turn's decision added, never every answer.
    workspace = demo_api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Demo strength declined", "data_mode": "demo", "synthetic": True},
    ).json()["workspace_id"]
    choose_role(demo_api, ada, workspace, occupation(api, ada, "bookkeeper"), 0)
    scenario = make_scenario(infra, api, ada, tmp_path)
    first = decided_turn(
        demo_api, ada, workspace, scenario, "I enjoy reconciling accounting entries", 1
    )
    proposed = run_strength(demo_api, ada, workspace, scenario, first, 2)
    declined = demo_api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{first}/strength/decision",
        ada,
        {"expected_version": 0, "confirm": False},
    )
    later = decided_turn(demo_api, ada, workspace, scenario, "I enjoy planning budgets", 2)
    after = run_strength(demo_api, ada, workspace, scenario, later, 3)
    unquotable = decided_turn(demo_api, ada, workspace, scenario, "I enjoy it all", 3)
    refused = ask_strength(demo_api, ada, workspace, unquotable, 4)

    assert proposed["proposal"]["quotation"] == "reconciling accounting entries"
    assert declined.status_code == 201, declined.text
    profile = api.get(f"/v1/workspaces/{workspace}/profile", ada).json()
    assert profile["document"]["enjoyed_tasks"]["value"] == [
        "reconciling accounting entries",
        "planning budgets",
        "it all",
    ]  # the earlier answer is still there, but the later turn did not add it
    assert (after["run"]["status"], after["found"], after["proposal"]) == ("complete", False, None)
    assert (refused.status_code, refused.json()["error"]["details"]["reason"]) == (
        422,
        "no_quotable_answer",
    )  # "it all" says nothing to quote, and it is all that turn added


@pytest.mark.req("ASSESS-01", "BND1-11")
def test_an_answer_moved_or_added_back_is_not_new_so_a_declined_strength_stays_declined(
    infra: Infra, api: ApiClient, demo_api: ApiClient, ada: str, tmp_path: Path
) -> None:
    # Task W2B re-review M-E: an answer counts as new only if no earlier version held its
    # words in what the person enjoys, can do or has done, so moving a declined answer to
    # another of those fields, or removing it and adding it back, does not offer it again.
    workspace = demo_api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Demo strength moved", "data_mode": "demo", "synthetic": True},
    ).json()["workspace_id"]
    choose_role(demo_api, ada, workspace, occupation(api, ada, "bookkeeper"), 0)
    scenario = make_scenario(infra, api, ada, tmp_path)
    first = decided_turn(
        demo_api, ada, workspace, scenario, "I enjoy reconciling accounting entries", 1
    )
    proposed = run_strength(demo_api, ada, workspace, scenario, first, 2)
    declined = demo_api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{first}/strength/decision",
        ada,
        {"expected_version": 0, "confirm": False},
    )
    moved = demo_api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        ada,
        {
            "expected_version": 2,
            "profile": profile_with(
                current_role="bookkeeper", confident_tasks=["Reconciling accounting entries"]
            ),
        },
    )
    back = decided_turn(
        demo_api, ada, workspace, scenario, "I enjoy reconciling accounting entries", 3
    )
    again = ask_strength(demo_api, ada, workspace, back, 4)

    assert proposed["proposal"]["quotation"] == "reconciling accounting entries"
    assert (declined.status_code, moved.status_code) == (201, 201), moved.text
    document = api.get(f"/v1/workspaces/{workspace}/profile", ada).json()["document"]
    assert document["enjoyed_tasks"]["value"] == ["reconciling accounting entries"]  # back
    assert document["confident_tasks"]["value"] == ["Reconciling accounting entries"]  # moved
    assert again.status_code == 422, again.text  # no run: nothing new to offer
    assert again.json()["error"]["details"]["reason"] == "no_new_answers"


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


def decide(api: ApiClient, token: str, workspace: str, turn_id: str, version: int) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns/{turn_id}/strength/decision",
        token,
        {"expected_version": version, "confirm": True},
    )


@pytest.mark.req("MODEL-02", "ASSESS-01")
def test_a_strength_invalid_after_its_repair_fails_typed_and_has_nothing_to_decide(
    live: Scenario,
) -> None:
    # Review M4: the strength kind's own failure path, and a decision on a failed run.
    api, token, workspace = live.api, live.token, live.workspace_id
    turn_id = decided_turn(api, token, workspace, live, "I enjoy reconciling ledgers", 2)
    asked = ask_strength(api, token, workspace, turn_id, 3)
    run_id = asked.json()["run"]["run_id"]
    worker = live.worker("strength", fake_failure="invalid_always")
    live.wait_terminal(run_id)
    assert worker.stop() == 0

    found = strength(api, token, workspace, turn_id)
    decided = decide(api, token, workspace, turn_id, 0)

    assert (found["run"]["status"], found["run"]["failure_class"]) == (
        "failed",
        "invalid_model_output",
    )
    assert (found["found"], found["proposal"], found["decision"]) == (None, None, None)
    [attempt] = live.attempts(run_id)
    assert attempt["requests_sent"] == 2  # the first request and one repair, never more
    assert (decided.status_code, decided.json()["error"]["code"]) == (
        409,
        "PROPOSAL_NOT_AVAILABLE",
    )  # a failure is never an empty proposal
    assert (
        live.infra.query(
            "SELECT * FROM careerwright.skill_evidence WHERE workspace_id = %s", (workspace,)
        )
        == []
    )
    assert live.leaks() == []


@pytest.mark.req("MODEL-02", "ASSESS-01")
def test_a_strength_is_confirmed_against_the_versions_the_person_saw(live: Scenario) -> None:
    # Review M4: a confirmation against a stale capability version, and a strength asked
    # for after the turn's answers changed.
    api, token, workspace = live.api, live.token, live.workspace_id
    turn_id = decided_turn(api, token, workspace, live, "I enjoy reconciling ledgers", 2)
    assert run_strength(api, token, workspace, live, turn_id, 3)["found"] is True

    stale = decide(api, token, workspace, turn_id, 1)  # the capability is at version 0
    confirmed = decide(api, token, workspace, turn_id, 0)
    later = decided_turn(api, token, workspace, live, "I enjoy planning budgets", 3)
    assistant = occupation(api, token, "accounting assistant")
    assert choose_role(api, token, workspace, assistant, 4).status_code == 201
    too_late = ask_strength(api, token, workspace, later, 5)

    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert stale.json()["error"]["details"]["current_version"] == 0
    assert confirmed.status_code == 201, confirmed.text  # nothing was kept from the refusal
    assert confirmed.json()["capability_version"] == 1
    assert too_late.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert too_late.json()["error"]["details"] == {"current_version": 5, "turn_version": 4}
    assert (
        live.infra.query(
            "SELECT * FROM careerwright.strength_proposals WHERE turn_id = %s", (later,)
        )
        == []
    )  # refused before any run exists
