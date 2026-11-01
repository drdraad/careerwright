"""Career discovery end to end against real PostgreSQL 16, DBOS and the labelled ESCO sample,
with real worker processes and a fake provider (S2.4-S2.5; REC-1, DIV-1, STATE-05).

The chain is checked link by link: confirmed answers, the model's validated queries citing
them, ESCO hits, the deterministic slate and, only by the person's choice, a target."""

import dataclasses
import json
import re
import uuid
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
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
from tools.evaluation import Case, CaseKind, load_cases, observe_discovery_offline

pytestmark = pytest.mark.integration

# Each task reaches the labelled sample's work through an essential skill holding all its
# words ("tune bicycles", "apply restoration techniques", "maintain plants' growth"): since
# Task W2B fix round 2 one shared word is never enough, and how someone likes to work is not
# searched.
ANSWERS = profile_with(
    current_role="Warehouse shift supervisor",
    enjoyed_tasks=["tuning bicycles", "applying restoration techniques"],
    confident_tasks=["maintaining plant growth"],
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
        ("enjoyed_tasks", "tuning bicycles"),
        ("enjoyed_tasks", "applying restoration techniques"),
        ("confident_tasks", "maintaining plant growth"),
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
        assert suggestion["reasons"]
        assert all(r["outcome"] in {"found_work", "matched"} for r in suggestion["reasons"])
    # The model's invented title is a hypothesis ESCO does not hold: never a suggestion.
    [unsupported] = [i for i in result["title_ideas"] if i["outcome"] == "not_matched"]
    assert unsupported["title"].endswith("orbital gardener")
    assert unsupported["occupations"] == 0
    assert unsupported["title"] not in {s["title"] for s in result["suggestions"]}
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
    # The relaxation is stated in its own fact (Task W2B re-review 2, N-M3: the slate has
    # other notes too, so any note at all proved nothing).
    assert {"reason": "more_depth", "family_limit": 4} in deeper["notes"]
    assert not any(note["reason"] == "more_depth" for note in first["notes"])
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
    assert floor["left_out"] + floor["meets"] + floor["kept_pay_unknown"] >= 1  # they add up
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
    assert "summary" not in shown  # facts only: the web words a filter that is not at Any
    # A minimum leaves every unscored role in: unknown is never read as 0.
    assert [s["concept_id"] for s in any_minimum["suggestions"]] == [
        s["concept_id"] for s in default["suggestions"]
    ]
    assert any_minimum["ai_resilience_filter"]["below_minimum"] == 0
    # Only switching unscored roles off removes them, and it says how many.
    assert hidden["suggestions"] == []
    assert hidden["ai_resilience_filter"]["unscored_excluded"] == shown["unscored"]
    assert hidden["ai_resilience_filter"]["include_unscored"] is False
    assert {n["reason"] for n in hidden["not_included"]} >= {"ai_resilience_unscored_excluded"}
    # The role is kept in the person's words: nothing offers it a closest occupation after the
    # start, so its fact never asks for one (Task 6d slice B fix round 1, design review I-2).
    assert hidden["fewer_reasons"] == [
        {"reason": "few_matched", "count": 0},
        {
            "reason": "role_not_matched",
            "outcome": "not_matched",
            "title": "Warehouse shift supervisor",
        },
    ]
    assert default["salary_floor"] is None  # the person set no floor


@pytest.mark.req("DIV1-03", "DIV1-13", "DIV1-10")
def test_after_none_of_these_the_slate_keeps_the_role_in_the_person_s_words_and_says_less(
    scenario: Scenario,
) -> None:
    # Design review I-2 and M-2: after the type-ahead's "None of these is my job" the slate
    # asked for "the ESCO occupation closest to it" and headed its less familiar directions
    # "Something different", though nothing knew the person's kind of work.
    declined = scenario.api.write(
        "POST",
        f"{base(scenario)}/origin/role/title",
        scenario.token,
        {"expected_version": 2, "title": "Warehouse shift supervisor", "none_of_these": True},
    )
    assert declined.status_code == 201, declined.text

    discovery_id = discover(scenario, version=3)["discovery_id"]
    default = slate(scenario, discovery_id)
    hidden = slate(scenario, discovery_id, min_ai_resilience="3", include_unscored="false")

    assert hidden["fewer_reasons"] == [
        {"reason": "few_matched", "count": 0},
        {
            "reason": "title_kept_as_own",
            "outcome": "not_matched",
            "title": "Warehouse shift supervisor",
        },
    ]
    assert default["familiarity_known"] is False
    assert not any(s["different_kind_of_work"] for s in default["suggestions"])


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
    assert kept["minimum"] == 5  # the web says the range is a synthetic fixture's
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


@pytest.mark.req("STATE-10")
def test_a_target_chosen_from_the_slate_leaves_it_current_and_any_other_change_does_not(
    scenario: Scenario,
) -> None:
    discovery_id = discover(scenario)["discovery_id"]
    first, second = slate(scenario, discovery_id)["suggestions"][:2]

    def current() -> bool:
        found = scenario.api.get(f"{base(scenario)}/discoveries/{discovery_id}", scenario.token)
        assert found.status_code == 200, found.text
        return bool(found.json()["current"])

    def choose(version: int, chosen: dict[str, Any]) -> None:
        body = {
            "expected_version": version,
            "concept_id": chosen["concept_id"],
            "discovery_id": discovery_id,
        }
        made = scenario.api.write("POST", f"{base(scenario)}/targets", scenario.token, body)
        assert made.status_code == 201, made.text

    assert current()
    choose(2, first)
    choose(3, second)
    assert current()  # two choices from this slate: still made from the current answers
    # Its one written note can still be asked for: it quotes the answers it pinned.
    note = scenario.api.write(
        "POST",
        f"{base(scenario)}/discoveries/{discovery_id}/explanation",
        scenario.token,
        {"expected_profile_version": 4},
    )
    assert note.status_code == 202, note.text
    targets = scenario.profile()["document"]["target_titles"]["value"]
    edited = {
        **ANSWERS,
        "target_titles": {"state": "provided", "value": targets},
        "cities": {"state": "provided", "value": ["York"]},
    }
    put = scenario.api.write(
        "PUT",
        f"{base(scenario)}/profile",
        scenario.token,
        {"expected_version": 4, "profile": edited},
    )
    assert put.status_code == 201, put.text
    assert not current()  # another answer changed: based on earlier answers


@pytest.mark.req("DIV1-06", "DIV1-03")
def test_a_role_esco_does_not_list_is_reported_never_searched_by_its_words(
    scenario: Scenario,
) -> None:
    # Task 6 review A-M6 said a role with no searchable word is never a search that found
    # nothing. Since Sprint W no title is searched by its words at all: a role ESCO does not
    # list joins nothing and is listed, whatever its words.
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

    assert result["unmatched_titles"] == ["Of the"]
    assert "Of the" not in [q["text"] for q in result["queries"]]
    assert "connection" not in result  # no suggestion is singled out (the plain line)


@pytest.mark.req("DIV1-10", "DIV1-12")
def test_a_role_esco_lists_joins_other_work_by_shared_essential_skills_only(
    scenario: Scenario,
) -> None:
    put = scenario.api.write(
        "PUT",
        f"{base(scenario)}/profile",
        scenario.token,
        {
            "expected_version": 2,
            "profile": {**ANSWERS, "current_role": {"state": "provided", "value": "bus driver"}},
        },
    )
    assert put.status_code == 201, put.text

    result = slate(scenario, discover(scenario, version=3)["discovery_id"])

    joined = next(q for q in result["queries"] if q["channel"] == "shared_skills")
    assert (joined["text"], joined["hits"]) == ("bus driver", 1)
    [trolley] = [s for s in result["suggestions"] if s["title"] == "trolley bus driver"]
    assert "shared_skills" in trolley["channels"]
    assert {
        "reason": "joined_by_shared_skills",
        "outcome": "found_work",
        "field": "current_role",
        "answer": "bus driver",
        "shared": 4,
    } in trolley["reasons"]
    # The four are named, by label (Task W2E, the audit's F4): never only counted.
    named = [skill["label"] for skill in trolley["shared_skills"]]
    assert len(named) == 4
    assert named == sorted(named)
    engine = migrator_engine(scenario.infra)
    try:
        with system_transaction(engine) as tx:
            [bus] = tx.execute(
                sa.text(
                    "SELECT concept_id FROM careerwright.occupation_concepts "
                    "WHERE preferred_label = 'bus driver'"
                )
            ).scalars()
            # Read from the release itself, beside the API's own answer.
            both = tx.execute(
                sa.text(
                    "SELECT DISTINCT s.preferred_label FROM careerwright.occupation_skills r "
                    "JOIN careerwright.skills s ON s.skill_id = r.skill_id "
                    "WHERE r.concept_id = :other AND r.relation = 'essential' AND r.skill_id IN "
                    "(SELECT a.skill_id FROM careerwright.occupation_skills a "
                    "WHERE a.concept_id = :bus AND a.relation = 'essential') "
                    "ORDER BY s.preferred_label"
                ),
                {"other": uuid.UUID(trolley["concept_id"]), "bus": bus},
            ).scalars()
            shared = list(both)
    finally:
        engine.dispose()
    assert named == shared
    # Work found by a search, not joined by skills, names none.
    assert all(
        s["shared_skills"] == []
        for s in result["suggestions"]
        if "shared_skills" not in s["channels"]
    )
    assert result["unmatched_titles"] == []
    assert result["familiarity_known"] is True  # the role names an ESCO occupation


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
    assert "label" not in sketch  # facts only: the web labels it an early sketch
    mechanic, invented = sketch["targets"]
    assert mechanic["resolution"] == "esco"
    assert mechanic["requirements"]
    assert mechanic["requirement_count"] >= len(mechanic["requirements"])
    assert invented["resolution"] == "not_found"
    assert (invented["requirements"], invented["requirement_count"]) == ([], None)
    assert sketch["steps"] == [
        {"step": "compare", "state": "unresolved"},
        {"step": "find_options", "state": "unresolved"},
        {"step": "check_time_and_cost", "state": "unresolved"},
    ]
    # The last step's words say the spending limit isn't known, from this input's state.
    assert sketch["inputs"]["direct_spend_cap"] != "provided"
    assert (mechanic["coverage"], invented["coverage"]) == ("not_covered", "not_covered")
    assert set(sketch["not_asked"]) == {"current_role", "weekly_study_hours", "cities"}
    assert sketch["inputs"]["direct_spend_cap"] == "prefer_not_to_say"  # an answer, not zero
    assert not re.search(r"feasible|optimal|£\s?\d", json.dumps(sketch), re.IGNORECASE)


@pytest.mark.req("STATE-05", "DIV1-03")
def test_the_sketch_says_what_matching_each_title_did_never_what_esco_holds(
    api: ApiClient, ada: str
) -> None:
    # Task W2B re-review 5: "Several ESCO occupations have this title" was untrue where only a
    # hidden label is shared, and "No ESCO record" where ESCO writes the title another way
    # ("façade cleaner"): titles are matched with case, punctuation and plurals folded.
    workspace = api.create_workspace(ada, "Sketch words (synthetic)")["workspace_id"]
    api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        ada,
        {
            "expected_version": 0,
            "profile": profile_with(target_titles=["bus operator", "Tidal lagoon whisperer"]),
        },
    )

    shared, invented = api.get(f"/v1/workspaces/{workspace}/sketch", ada).json()["targets"]

    # The web words each resolution (`RESEARCH_STATUS`, with a test of each sentence).
    assert shared["resolution"] == "ambiguous"
    assert len(shared["occupations"]) == 2
    assert invented["resolution"] == "not_found"
    assert "research_status" not in shared


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

    assert not [note for note in same["notes"] if note["reason"] == "release_changed"]
    [note] = [note for note in other["notes"] if note["reason"] == "release_changed"]
    assert note == {"reason": "release_changed", "searched": "esco-v1.1.1-en-csv", "held": held}


@pytest.mark.req("DIV1-04")
def test_a_title_idea_that_was_never_searched_has_no_count_of_matching_occupations(
    infra: Infra,
) -> None:
    # Task 6d slice A fix round 1 (review M-2): unknown is never zero. An idea resting only on
    # a one-word answer about how someone likes to work is not searched, so how many
    # occupations match it isn't known; an idea that was searched has its count, 0 included.
    case = Case(
        id="ad hoc",
        kind=CaseKind.DISCOVERY,
        title="ad hoc",
        requirements=[],
        synthetic=True,
        profile={"enjoyed_tasks": ["tuning bicycles"], "work_style": ["practical"]},
        discovery_output={
            "queries": [
                {"text": "tune bicycles", "channel": "tasks", "based_on": ["tuning bicycles"]}
            ],
            "hypotheses": [
                {"title": "workshop technician", "based_on": ["practical"]},
                {"title": "orbital gardener", "based_on": ["tuning bicycles"]},
            ],
        },
        expect=[],
    )
    engine = migrator_engine(infra)
    try:
        with system_transaction(engine) as tx:
            observed = observe_discovery_offline(tx, case)
    finally:
        engine.dispose()

    assert [(i["title"], i["outcome"], i["occupations"]) for i in observed["title_ideas"]] == [
        ("workshop technician", "not_searched", None),
        ("orbital gardener", "not_matched", 0),
    ]


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
