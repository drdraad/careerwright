"""Career discovery end to end against real PostgreSQL 16, DBOS and the labelled ESCO sample,
with real worker processes and a fake provider (S2.4-S2.5; REC-1, DIV-1, STATE-05).

The chain is checked link by link: confirmed answers, the model's validated queries citing
them, ESCO hits, the deterministic slate and, only by the person's choice, a target."""

import dataclasses
import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from nessa.api.app import create_app
from nessa.api.deps import ApiDependencies
from nessa.config import RuntimeMode
from tests.integration.durable import Scenario, make_scenario
from tests.support.client import ApiClient, profile_with
from tests.support.esco import SAMPLE_RELEASE
from tests.support.infra import API_BASE, Infra

pytestmark = pytest.mark.integration

ANSWERS = profile_with(
    current_role="Warehouse shift supervisor",
    enjoyed_tasks=["repairing bicycles", "restoring old furniture"],
    confident_tasks=["looking after gardens"],
    work_style=["working outdoors"],
    cities=["Leeds"],
)


@pytest.fixture
def scenario(infra: Infra, api: ApiClient, ada: str, tmp_path: Path) -> Iterator[Scenario]:
    started = make_scenario(infra, api, ada, tmp_path)
    put = api.write(
        "PUT",
        f"/v1/workspaces/{started.workspace_id}/profile",
        ada,
        {"expected_version": 1, "profile": ANSWERS},
    )
    assert put.status_code == 201, put.text
    yield started
    for worker in started.workers:
        worker.kill_if_running()


def base(scenario: Scenario) -> str:
    return f"/v1/workspaces/{scenario.workspace_id}"


def discover(scenario: Scenario, version: int = 2) -> dict[str, Any]:
    submitted = scenario.api.write(
        "POST",
        f"{base(scenario)}/discoveries",
        scenario.token,
        {"expected_profile_version": version},
    )
    assert submitted.status_code == 202, submitted.text
    body: dict[str, Any] = submitted.json()
    worker = scenario.worker("worker")
    scenario.wait_terminal(body["discovery_id"])
    assert worker.stop() == 0
    return body


def slate(scenario: Scenario, discovery_id: str, **query: str) -> dict[str, Any]:
    response = scenario.api.get(
        f"{base(scenario)}/discoveries/{discovery_id}/slate", scenario.token, **query
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


@pytest.mark.req("DIV1-02", "DIV1-04", "REC1-05", "REC1-06", "DIV1-10", "MODEL-02")
def test_a_discovery_runs_durably_and_its_slate_is_grounded_in_esco_and_the_answers(
    scenario: Scenario,
) -> None:
    submitted = discover(scenario)
    discovery_id = submitted["discovery_id"]

    shown = scenario.api.get(f"{base(scenario)}/discoveries/{discovery_id}", scenario.token).json()
    assert (shown["run"]["kind"], shown["run"]["status"], shown["profile_version"]) == (
        "discovery",
        "complete",
        2,
    )
    assert shown["proposal"]["origin"] == "model"
    answers = {
        ("enjoyed_tasks", "repairing bicycles"),
        ("enjoyed_tasks", "restoring old furniture"),
        ("confident_tasks", "looking after gardens"),
        ("work_style", "working outdoors"),
        ("current_role", "Warehouse shift supervisor"),
    }
    for query in shown["proposal"]["queries"]:
        assert {(e["field"], e["text"]) for e in query["based_on"]} <= answers

    result = slate(scenario, discovery_id)

    assert 1 <= len(result["suggestions"]) <= 6
    assert result["release"]["sample"] is True  # the labelled test subset, never real
    assert "ESCO" in result["release"]["attribution"]
    for suggestion in result["suggestions"]:
        assert suggestion["concept_kind"] == "esco"
        detail = scenario.api.get(
            f"/v1/taxonomy/occupations/{suggestion['concept_id']}", scenario.token
        )
        assert detail.status_code == 200  # grounded: an occupation of the pinned release
        assert suggestion["sources"] == [
            {"kind": "esco", "uri": detail.json()["esco_uri"], "release": SAMPLE_RELEASE.dataset_id}
        ]
        assert {(e["field"], e["text"]) for e in suggestion["linked_evidence"]} <= answers
        assert suggestion["why_it_could_suit"]
        assert suggestion["try_it"]
    # The model's invented title is a hypothesis ESCO does not hold: never a suggestion.
    [unsupported] = result["unsupported_hypotheses"]
    assert unsupported.endswith("orbital gardener")
    assert unsupported not in {s["title"] for s in result["suggestions"]}
    assert not re.search(r"\d\s?%|per ?cent", json.dumps(result))  # no match percentage
    families = [s["family"]["code"] for s in result["suggestions"]]
    assert max(families.count(f) for f in families) <= result["family_limit"]
    assert result["pool_size"] >= len(result["suggestions"])
    assert len(result["not_included"]) == result["pool_size"] - len(result["suggestions"]) + sum(
        1 for n in result["not_included"] if n["reason"] == "duplicate"
    )
    [attempt] = scenario.attempts(discovery_id)
    assert (attempt["outcome"], attempt["spend_state"], attempt["requests_sent"]) == (
        "succeeded",
        "reconciled",
        1,
    )
    assert scenario.assert_identifier_only_journal(discovery_id)["status"] == "complete"
    assert scenario.leaks() == []


@pytest.mark.req("REC1-08", "DIV1-07")
def test_the_slate_controls_change_the_view_only_and_count_their_effect(
    scenario: Scenario,
) -> None:
    discovery_id = discover(scenario)["discovery_id"]
    first = slate(scenario, discovery_id)
    title = first["suggestions"][0]
    family = title["family"]["code"]

    without_title = slate(scenario, discovery_id, exclude_concept=title["concept_id"])
    without_family = slate(scenario, discovery_id, exclude_family=family)

    assert title["concept_id"] not in {s["concept_id"] for s in without_title["suggestions"]}
    assert without_title["excluded"] == {"occupations": 1, "families": 0}
    assert without_family["excluded"]["families"] >= 1
    assert family not in {s["family"]["code"] for s in without_family["suggestions"]}
    reasons = {n["concept_id"]: n["reason"] for n in without_title["not_included"]}
    assert reasons[title["concept_id"]] == "excluded_occupation"  # "show why"
    deeper = slate(scenario, discovery_id, emphasis="deeper")
    assert (deeper["emphasis"], deeper["family_limit"]) == ("deeper", 4)
    assert deeper["notes"]
    assert scenario.profile()["version"] == 2  # a view never changes the profile


@pytest.mark.req("REC1-07", "PROF-04", "PROF-07")
def test_a_suggestion_becomes_a_target_only_by_the_person_s_choice(scenario: Scenario) -> None:
    discovery_id = discover(scenario)["discovery_id"]
    chosen = slate(scenario, discovery_id)["suggestions"][0]
    assert scenario.profile()["document"]["target_titles"]["state"] == "unasked"

    def choose(version: int, **extra: Any) -> Any:
        body = {"expected_version": version, "concept_id": chosen["concept_id"], **extra}
        return scenario.api.write("POST", f"{base(scenario)}/targets", scenario.token, body)

    made = choose(2, discovery_id=discovery_id)
    again = choose(3, discovery_id=discovery_id)
    stale = choose(2)

    assert made.status_code == 201, made.text
    document = made.json()["document"]
    assert document["target_titles"]["value"] == [chosen["title"]]
    sources = scenario.api.get(f"{base(scenario)}/sources", scenario.token).json()["items"]
    [source] = [
        s for s in sources if s["source_ref_id"] == document["target_titles"]["source_ref_id"]
    ]
    assert (source["kind"], source["discovery_id"], source["turn_id"]) == (
        "occupation_choice",
        discovery_id,
        None,
    )
    assert source["locator"] == chosen["sources"][0]["uri"]
    assert again.status_code == 200  # already a target: nothing changed
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    not_a_target = choose(3, replaces="astronaut")
    assert not_a_target.json()["error"]["details"]["reason"] == "not_a_target"
    assert scenario.profile()["version"] == 3


@pytest.mark.req("DIV1-06")
def test_a_discovery_needs_an_answer_that_describes_work_and_the_current_version(
    infra: Infra, api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Empty (synthetic)")["workspace_id"]

    empty = api.write(
        "POST", f"/v1/workspaces/{workspace}/discoveries", ada, {"expected_profile_version": 0}
    )
    stale = api.write(
        "POST", f"/v1/workspaces/{workspace}/discoveries", ada, {"expected_profile_version": 4}
    )

    assert (empty.status_code, empty.json()["error"]["code"]) == (422, "INSUFFICIENT_EVIDENCE")
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    listed = api.get(f"/v1/workspaces/{workspace}/discoveries", ada).json()
    assert listed["items"] == []  # refused before any run exists


@pytest.mark.req("BND1-11", "TEST1-10")
def test_a_demo_workspace_discovers_offline_with_the_labelled_fixture_proposer(
    infra: Infra, api: ApiClient, api_deps: ApiDependencies, ada: str, tmp_path: Path
) -> None:
    settings = api_deps.settings.model_copy(update={"runtime_mode": RuntimeMode.DEMO})
    deps = dataclasses.replace(api_deps, settings=settings)
    with TestClient(
        create_app(deps),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57003),
    ) as client:
        demo = ApiClient(client)
        workspace = demo.write(
            "POST",
            "/v1/workspaces",
            ada,
            {"name": "Demo discovery", "data_mode": "demo", "synthetic": True},
        ).json()["workspace_id"]
        demo.write(
            "PUT",
            f"/v1/workspaces/{workspace}/profile",
            ada,
            {"expected_version": 0, "profile": ANSWERS},
        )
        submitted = demo.write(
            "POST", f"/v1/workspaces/{workspace}/discoveries", ada, {"expected_profile_version": 1}
        )
    assert submitted.status_code == 202, submitted.text
    run = submitted.json()["run"]
    assert (run["model_id"], run["model_mode"]) == ("nessa-fixture-discovery-1", "fixture")
    scenario = make_scenario(infra, api, ada, tmp_path)
    worker = scenario.worker("worker")
    scenario.wait_terminal(run["run_id"])
    assert worker.stop() == 0

    found = api.get(f"/v1/workspaces/{workspace}/discoveries/{run['run_id']}", ada).json()
    assert found["proposal"]["origin"] == "fixture"
    assert found["proposal"]["hypotheses"] == []  # the fixture never invents a title
    result = api.get(f"/v1/workspaces/{workspace}/discoveries/{run['run_id']}/slate", ada).json()
    assert result["suggestions"]
    [attempt] = scenario.attempts(run["run_id"])
    assert (attempt["spend_state"], attempt["cost_nano_usd"]) == ("none", 0)


@pytest.mark.req("STATE-05")
def test_the_sketch_lists_esco_requirements_for_a_target_and_every_step_stays_unresolved(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Sketch (synthetic)")["workspace_id"]
    before = api.get(f"/v1/workspaces/{workspace}/sketch", ada).json()
    api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        ada,
        {
            "expected_version": 0,
            "profile": {
                **profile_with(target_titles=["Bicycle mechanic", "Tidal lagoon whisperer"]),
                "direct_spend_cap": {"state": "prefer_not_to_say"},
            },
        },
    )

    sketch = api.get(f"/v1/workspaces/{workspace}/sketch", ada).json()

    assert (before["targets"], before["steps"]) == ([], [])  # no sketch without a target
    assert sketch["label"] == "Early sketch, not a checked route"
    mechanic, invented = sketch["targets"]
    assert mechanic["resolution"] == "esco"
    assert mechanic["requirements"]
    assert mechanic["requirement_count"] >= len(mechanic["requirements"])
    assert invented["resolution"] == "not_found"
    assert (invented["requirements"], invented["requirement_count"]) == ([], None)
    assert {step["state"] for step in sketch["steps"]} == {"unresolved"}
    assert "spending limit isn't known" in sketch["steps"][-1]["detail"]
    assert set(sketch["not_asked"]) == {"current_role", "weekly_study_hours", "cities"}
    assert sketch["inputs"]["direct_spend_cap"] == "prefer_not_to_say"  # an answer, not zero
    assert not re.search(r"feasible|optimal|£\s?\d", json.dumps(sketch), re.IGNORECASE)


@pytest.mark.req("SEC-02", "API-01")
def test_another_account_or_a_missing_workspace_is_not_found_never_an_empty_result(
    api: ApiClient, ada: str, ben: str, scenario: Scenario
) -> None:
    discovery_id = discover(scenario)["discovery_id"]
    missing = "00000000-0000-4000-8000-00000000dead"
    mine = base(scenario)
    reads = [
        f"{mine}/sketch",
        f"{mine}/discoveries",
        f"{mine}/discoveries/{discovery_id}",
        f"{mine}/discoveries/{discovery_id}/slate",
        f"{mine}/interview/preferences",
    ]

    for path in reads:
        refused = api.get(path, ben)
        assert (refused.status_code, refused.json()["error"]["code"]) == (404, "NOT_FOUND"), path
        absent = api.get(path.replace(scenario.workspace_id, missing), ada)
        assert absent.status_code == 404, path
    writes = [
        ("POST", f"{mine}/discoveries", {"expected_profile_version": 2}),
        ("POST", f"{mine}/targets", {"expected_version": 2, "concept_id": missing}),
        (
            "PUT",
            f"{mine}/interview/preferences",
            {
                "expected_version": 0,
                "entry_mode": "sure",
                "conversation_mode": None,
                "paused": False,
            },
        ),
    ]
    for method, path, body in writes:
        assert api.write(method, path, ben, body).status_code == 404, path
    assert scenario.profile()["version"] == 2  # nothing changed
