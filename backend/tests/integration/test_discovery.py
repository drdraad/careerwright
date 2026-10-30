"""Career discovery end to end against real PostgreSQL 16, DBOS and the labelled ESCO sample,
with real worker processes and a fake provider (S2.4-S2.5; REC-1, DIV-1, STATE-05).

The chain is checked link by link: confirmed answers, the model's validated queries citing
them, ESCO hits, the deterministic slate and, only by the person's choice, a target."""

import dataclasses
import json
import re
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from careerwright.api.app import create_app
from careerwright.api.deps import ApiDependencies
from careerwright.catalogue.esco import concept_id
from careerwright.catalogue.pay import MappingReview, MappingReviewPack
from careerwright.catalogue.taxonomy import held_release
from careerwright.config import RuntimeMode
from careerwright.db import system_transaction
from tests.integration.durable import Scenario, make_scenario
from tests.support import reference_data as samples
from tests.support.client import ApiClient, profile_with
from tests.support.esco import SAMPLE_RELEASE
from tests.support.infra import API_BASE, Infra, migrator_engine
from tools.evaluation import load_cases, observe_discovery_offline

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


def discover(scenario: Scenario, version: int = 2, **worker_settings: str) -> dict[str, Any]:
    submitted = scenario.api.write(
        "POST",
        f"{base(scenario)}/discoveries",
        scenario.token,
        {"expected_profile_version": version},
    )
    assert submitted.status_code == 202, submitted.text
    body: dict[str, Any] = submitted.json()
    worker = scenario.worker("worker", **worker_settings)
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
    assert not re.search(r"\d\s?(?:%|per ?cent)", json.dumps(result), re.IGNORECASE)  # none
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


BICYCLE_MECHANIC = str(concept_id(samples.BICYCLE_MECHANIC))
FLOOR = {"amount": {"minor_units": 2_600_000, "currency": "GBP"}, "period": "year"}


def with_floor(scenario: Scenario) -> str:
    """The answers again with a confirmed salary floor (a direct edit), then a discovery."""
    put = scenario.api.write(
        "PUT",
        f"{base(scenario)}/profile",
        scenario.token,
        {"expected_version": 2, "profile": {**ANSWERS, "minimum_salary": {
            "state": "provided", "value": FLOOR}}},
    )  # fmt: skip
    assert put.status_code == 201, put.text
    return str(discover(scenario, version=3)["discovery_id"])


@pytest.mark.req("DIV1-07", "PROF-04")
def test_the_salary_floor_leaves_out_only_what_reviewed_pay_puts_below_it_and_counts_it(
    scenario: Scenario, api_deps: ApiDependencies
) -> None:
    discovery_id = with_floor(scenario)
    unreviewed = slate(scenario, discovery_id)
    review = MappingReview(
        esco_uri=samples.BICYCLE_MECHANIC,
        soc_code="5231",
        reviewer="Synthetic reviewer (tests only)",
        reviewed_on=date(2026, 10, 29),
        reasons="Synthetic review for a test.",
    )
    reviews = MappingReviewPack(pack_version="test", dated=date(2026, 10, 29), reviews=[review])
    with TestClient(
        create_app(dataclasses.replace(api_deps, mapping_reviews=reviews)),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57012),
    ) as client:
        response = ApiClient(client).get(
            f"{base(scenario)}/discoveries/{discovery_id}/slate", scenario.token
        )
    assert response.status_code == 200, response.text
    reviewed = response.json()

    # No reviewed mapping: every pooled occupation's pay is unknown, so nothing is left out.
    floor = unreviewed["salary_floor"]
    assert (floor["amount"], floor["period"], floor["basis"]) == (
        FLOOR["amount"],
        "year",
        "gross",
    )
    assert floor["left_out"] == 0
    assert floor["kept_by_reason"] == [
        {"reason": "no_reviewed_mapping", "count": floor["kept_pay_unknown"]}
    ]
    assert floor["kept_pay_unknown"] >= 1
    assert "never treated as below it" in floor["summary"]
    assert BICYCLE_MECHANIC in {s["concept_id"] for s in unreviewed["suggestions"]}
    # A reviewed mapping whose regional 90th percentile (synthetic) is below the floor.
    assert reviewed["salary_floor"]["left_out"] == 1
    assert BICYCLE_MECHANIC not in {s["concept_id"] for s in reviewed["suggestions"]}
    reasons = {n["concept_id"]: n["reason"] for n in reviewed["not_included"]}
    assert reasons[BICYCLE_MECHANIC] == "below_salary_floor"
    assert reviewed["salary_floor"]["kept_pay_unknown"] == floor["kept_pay_unknown"] - 1
    no_floor = slate(scenario, discover(scenario, version=3)["discovery_id"])
    assert no_floor["salary_floor"]["left_out"] == 0  # the same answers, same unknowns


@pytest.mark.req("AIR1-05")
def test_the_ai_resilience_filter_keeps_unscored_roles_by_default_and_counts_its_effect(
    scenario: Scenario,
) -> None:
    discovery_id = discover(scenario)["discovery_id"]
    default = slate(scenario, discovery_id)
    any_minimum = slate(scenario, discovery_id, min_ai_resilience="7")
    hidden = slate(scenario, discovery_id, min_ai_resilience="3", include_unscored="false")

    shown = default["ai_resilience_filter"]
    assert (shown["basis"], shown["minimum"], shown["include_unscored"]) == (
        "lower_bound",
        None,
        True,
    )
    assert shown["scored"] == 0  # no reviewed record exists: every role is unscored
    assert shown["unscored"] >= len(default["suggestions"]) >= 1
    assert shown["summary"] is None
    # A minimum leaves every unscored role in: unknown is never read as 0.
    assert [s["concept_id"] for s in any_minimum["suggestions"]] == [
        s["concept_id"] for s in default["suggestions"]
    ]
    assert any_minimum["ai_resilience_filter"]["below_minimum"] == 0
    # Only switching unscored roles off removes them, and it says how many.
    assert hidden["suggestions"] == []
    assert hidden["ai_resilience_filter"]["unscored_excluded"] == shown["unscored"]
    assert "unscored left out" in hidden["ai_resilience_filter"]["summary"]
    assert {n["reason"] for n in hidden["not_included"]} >= {"ai_resilience_unscored_excluded"}
    assert hidden["fewer_reasons"]
    assert default["salary_floor"] is None  # the person set no floor


@pytest.mark.req("AIR1-05")
def test_a_published_range_is_filtered_on_its_lower_end_and_labelled_synthetic(
    scenario: Scenario, api_deps: ApiDependencies
) -> None:
    # Fix round 1, B-M7, B-M8: the labelled synthetic record (5-8) moved onto the bicycle
    # mechanic, whose slate this discovery makes.
    discovery_id = discover(scenario)["discovery_id"]
    packs = samples.packs_scoring(samples.BICYCLE_MECHANIC)
    with TestClient(
        create_app(dataclasses.replace(api_deps, assessment_packs=packs)),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57015),
    ) as client:
        scored_api = ApiClient(client)

        def view(minimum: str) -> dict[str, Any]:
            response = scored_api.get(
                f"{base(scenario)}/discoveries/{discovery_id}/slate",
                scenario.token,
                min_ai_resilience=minimum,
            )
            assert response.status_code == 200, response.text
            body: dict[str, Any] = response.json()
            return body

        at_five, at_six = view("5"), view("6")

    kept = at_five["ai_resilience_filter"]
    assert (kept["scored"], kept["below_minimum"], kept["synthetic"]) == (1, 0, True)
    assert BICYCLE_MECHANIC in {s["concept_id"] for s in at_five["suggestions"]}
    assert "synthetic fixture range" in kept["summary"]
    left = at_six["ai_resilience_filter"]
    assert (left["scored"], left["below_minimum"], left["synthetic"]) == (1, 1, True)
    assert BICYCLE_MECHANIC not in {s["concept_id"] for s in at_six["suggestions"]}
    reasons = {n["concept_id"]: n["reason"] for n in at_six["not_included"]}
    assert reasons[BICYCLE_MECHANIC] == "below_ai_resilience_minimum"
    unscored = slate(scenario, discovery_id, min_ai_resilience="6")["ai_resilience_filter"]
    assert (unscored["scored"], unscored["synthetic"]) == (0, False)  # the product pack


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
def test_a_current_role_with_no_searchable_word_is_reported_never_a_search_that_found_nothing(
    scenario: Scenario,
) -> None:
    # Task 6 review A-M6: like a model query, it is listed as unsearchable, not run.
    put = scenario.api.write(
        "PUT",
        f"{base(scenario)}/profile",
        scenario.token,
        {
            "expected_version": 2,
            "profile": {**ANSWERS, "current_role": {"state": "provided", "value": "Of the"}},
        },
    )
    assert put.status_code == 201, put.text

    result = slate(scenario, discover(scenario, version=3)["discovery_id"])

    assert "Of the" in result["unsearchable_queries"]
    assert "Of the" not in [q["text"] for q in result["queries"]]


@pytest.mark.req("PROF-05", "MODEL-02")
def test_a_discovery_invalid_after_its_repair_fails_typed_and_has_no_slate(
    scenario: Scenario,
) -> None:
    # Task 6 review A-M2: the discovery kind's own failure path, not only the interview's.
    discovery_id = discover(scenario, fake_failure="invalid_always")["discovery_id"]

    found = scenario.api.get(f"{base(scenario)}/discoveries/{discovery_id}", scenario.token)
    run = found.json()["run"]
    assert (run["status"], run["failure_class"]) == ("failed", "invalid_model_output")
    assert found.json()["proposal"] is None
    [attempt] = scenario.attempts(discovery_id)
    assert attempt["requests_sent"] == 2  # the first request and one repair, never more
    refused = scenario.api.get(f"{base(scenario)}/discoveries/{discovery_id}/slate", scenario.token)
    assert (refused.status_code, refused.json()["error"]["code"]) == (
        409,
        "PROPOSAL_NOT_AVAILABLE",
    )  # a failure is never an empty slate
    assert scenario.profile()["version"] == 2
    assert scenario.leaks() == []


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
    assert (run["model_id"], run["model_mode"]) == ("careerwright-fixture-discovery-1", "fixture")
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


@pytest.mark.req("STATE-05", "REC1-07")
def test_the_sketch_uses_the_occupation_the_person_chose_even_when_its_title_is_shared(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # In ESCO 260 preferred labels are also another occupation's label ("administrative
    # assistant"). The sample has none, so the test gives one to another occupation and
    # removes it after (Task 6 review A-I-3).
    def holder(title: str) -> str:
        found = api.get("/v1/taxonomy/occupations", ada, q=title).json()
        concept_id: str = found["label_matches"][0]["concept_id"]
        return concept_id

    mechanic, restorer = holder("bicycle mechanic"), holder("furniture restorer")
    workspace = api.create_workspace(ada, "Shared title (synthetic)")["workspace_id"]
    infra.query(
        "INSERT INTO careerwright.occupation_labels (concept_id, label, normalised, kind) "
        "VALUES (%s, 'bicycle mechanic', 'bicycle mechanic', 'alternative')",
        (restorer,),
    )
    try:
        chosen = api.write(
            "POST",
            f"/v1/workspaces/{workspace}/targets",
            ada,
            {"expected_version": 0, "concept_id": mechanic},
        )
        sketch = api.get(f"/v1/workspaces/{workspace}/sketch", ada).json()
    finally:
        infra.query(
            "DELETE FROM careerwright.occupation_labels WHERE concept_id = %s AND label = %s",
            (restorer, "bicycle mechanic"),
        )

    assert chosen.status_code == 201, chosen.text
    [target] = sketch["targets"]
    assert target["resolution"] == "esco"  # never "choose the one you mean" again
    assert [o["concept_id"] for o in target["occupations"]] == [mechanic]
    assert target["requirements"]


@pytest.mark.req("TAX1-01", "DIV1-04")
def test_a_slate_read_against_another_release_than_its_searches_says_so(infra: Infra) -> None:
    # Re-review N-M9: the note reaches a computed slate, not only the pure function.
    case = next(c for c in load_cases() if c.id == "DSC-01")
    engine = migrator_engine(infra)
    try:
        with system_transaction(engine) as tx:
            held = held_release(tx).dataset_id
            same = observe_discovery_offline(tx, case, release=held)
            other = observe_discovery_offline(tx, case, release="esco-v1.1.1-en-csv")
    finally:
        engine.dispose()

    assert not [note for note in same["notes"] if "were chosen when" in note]
    [note] = [note for note in other["notes"] if "were chosen when" in note]
    assert "esco-v1.1.1-en-csv" in note
    assert held in note


@pytest.mark.req("SEC-02", "API-01")
def test_another_account_or_a_missing_workspace_is_not_found_never_an_empty_result(
    api: ApiClient, ada: str, ben: str, scenario: Scenario
) -> None:
    discovery_id = discover(scenario)["discovery_id"]
    missing = "00000000-0000-4000-8000-00000000dead"
    mine = base(scenario)
    # A real occupation from this workspace's slate, so only the workspace check can refuse.
    real = slate(scenario, discovery_id)["suggestions"][0]["concept_id"]
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
        (
            "POST",
            f"{mine}/discoveries/{discovery_id}/explanation",
            {"expected_profile_version": 2},
        ),
        ("POST", f"{mine}/targets", {"expected_version": 2, "concept_id": real}),
        ("POST", f"{mine}/profile/revert", {"expected_version": 2, "to_version": 1}),  # N-M1
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
