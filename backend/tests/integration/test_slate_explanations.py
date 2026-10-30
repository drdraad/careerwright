"""The written "Why this could suit you" end to end against real PostgreSQL 16, DBOS and the
labelled ESCO sample, with real worker processes and a fake provider (S2.7; REC1-11).

One bounded run per slate whatever view is shown; every quotation is a span of the answers
the discovery pinned or of ESCO's record; a failure is shown as unavailable while the
deterministic provenance stays; the export cites the provenance, never the written text."""

import dataclasses
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from careerwright.api.app import create_app
from careerwright.api.deps import ApiDependencies
from careerwright.config import RuntimeMode
from tests.integration.durable import Scenario, make_scenario
from tests.integration.test_discovery import ANSWERS, base, discover, slate
from tests.support.client import ApiClient, profile_with
from tests.support.infra import API_BASE, Infra

pytestmark = pytest.mark.integration


@pytest.fixture
def explaining(infra: Infra, api: ApiClient, ada: str, tmp_path: Path) -> Iterator[Scenario]:
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


def ask(scenario: Scenario, discovery_id: str, version: int = 2, *, retry: bool = False) -> Any:
    body: dict[str, Any] = {"expected_profile_version": version}
    if retry:
        body["retry_failed"] = True  # the person's explicit Try again
    return scenario.api.write(
        "POST", f"{base(scenario)}/discoveries/{discovery_id}/explanation", scenario.token, body
    )


def run_limit(scenario: Scenario, nano_usd: int) -> None:
    spend = scenario.api.get(f"{base(scenario)}/spend", scenario.token).json()
    put = scenario.api.write(
        "PUT",
        f"{base(scenario)}/spend/limits",
        scenario.token,
        {
            "expected_version": spend["version"],
            "run_limit_nano_usd": nano_usd,
            "period_limit_nano_usd": 1_000_000_000,
        },
    )
    assert put.status_code == 200, put.text


def refused_before_any_request(scenario: Scenario, discovery_id: str) -> dict[str, Any]:
    """The slate's note, queued, then refused inside the activity for its budget (lowered
    after submission): a failed run whose attempt sent nothing."""
    asked = ask(scenario, discovery_id)
    assert asked.status_code == 202, asked.text
    run_limit(scenario, 0)
    worker = scenario.worker("refusing")
    scenario.wait_terminal(asked.json()["explanation_id"])
    assert worker.stop() == 0
    found: dict[str, Any] = discovery(scenario, discovery_id)["explanation"]
    return found


def explain(scenario: Scenario, discovery_id: str, **worker_settings: str) -> dict[str, Any]:
    asked = ask(scenario, discovery_id)
    assert asked.status_code == 202, asked.text
    body: dict[str, Any] = asked.json()
    worker = scenario.worker("explainer", **worker_settings)
    scenario.wait_terminal(body["explanation_id"])
    assert worker.stop() == 0
    return body


def discovery(scenario: Scenario, discovery_id: str) -> dict[str, Any]:
    found = scenario.api.get(f"{base(scenario)}/discoveries/{discovery_id}", scenario.token)
    assert found.status_code == 200, found.text
    body: dict[str, Any] = found.json()
    return body


def record_texts(scenario: Scenario, concept_id: str) -> list[str]:
    """ESCO's record of an occupation as the taxonomy API serves it: an independent source."""
    detail = scenario.api.get(f"/v1/taxonomy/occupations/{concept_id}", scenario.token).json()
    skills = [s["preferred_label"] for s in detail["skills"] if s["relation"] == "essential"]
    return [detail["preferred_label"], detail["description"], *skills]


ANSWER_PAIRS = {
    ("current_role", "Warehouse shift supervisor"),
    ("enjoyed_tasks", "repairing bicycles"),
    ("enjoyed_tasks", "restoring old furniture"),
    ("confident_tasks", "looking after gardens"),
    ("work_style", "working outdoors"),
}  # `ANSWERS`, the answers that describe work
ANSWER_TEXTS = [text for _, text in ANSWER_PAIRS]


@pytest.mark.req("REC1-11", "REC1-06")
def test_a_slate_has_one_written_explanation_whose_every_quotation_is_a_span_of_its_source(
    explaining: Scenario,
) -> None:
    discovery_id = discover(explaining)["discovery_id"]
    before = slate(explaining, discovery_id)

    asked = explain(explaining, discovery_id)
    again = ask(explaining, discovery_id)  # a new request, another idempotency key
    other_view = slate(explaining, discovery_id, emphasis="unfamiliar")
    from_other_view = ask(explaining, discovery_id)

    assert asked["run"]["kind"] == "slate_explanation"
    assert asked["run"]["profile_version"] == 2  # the discovery's pinned version
    for repeated in (again, from_other_view):  # a view is never a new slate
        assert repeated.status_code == 200, repeated.text
        assert repeated.json()["explanation_id"] == asked["explanation_id"]
        assert repeated.json()["run"]["status"] == "complete"
        assert "written" not in repeated.json()  # a receipt never holds model output
    found = discovery(explaining, discovery_id)["explanation"]
    assert found["run"]["status"] == "complete"
    written = found["written"]
    assert written["origin"] == "model"
    assert [s["concept_id"] for s in written["suggestions"]] == [
        s["concept_id"] for s in before["suggestions"]
    ]  # the first view, in its order
    for suggestion in written["suggestions"]:
        record = record_texts(explaining, suggestion["concept_id"])
        for claim in suggestion["claims"]:
            sources = {q["source"] for q in claim["quotations"]}
            assert sources == {"answer", "esco"}
            for quotation in claim["quotations"]:
                pool = ANSWER_TEXTS if quotation["source"] == "answer" else record
                assert any(quotation["text"] in text for text in pool), quotation
    after = slate(explaining, discovery_id)
    assert after["suggestions"] == before["suggestions"]  # the written text changes nothing
    assert other_view["suggestions"]  # every view still shows its deterministic words
    [attempt] = explaining.attempts(asked["explanation_id"])
    assert (attempt["outcome"], attempt["spend_state"], attempt["requests_sent"]) == (
        "succeeded",
        "reconciled",
        1,
    )
    kinds = [
        r["kind"]
        for r in explaining.api.get(f"{base(explaining)}/runs", explaining.token).json()["items"]
    ]
    assert sorted(kinds) == ["discovery", "slate_explanation"]  # one call per slate
    assert explaining.profile()["version"] == 2
    assert (
        explaining.assert_identifier_only_journal(asked["explanation_id"])["status"] == "complete"
    )
    assert explaining.leaks() == []


@pytest.mark.req("REC1-11", "MODEL-03")
@pytest.mark.parametrize(
    ("failure", "failure_class", "requests"),
    [("invalid_always", "invalid_model_output", 2), ("truncated", "output_truncated", 1)],
)
def test_a_failed_explanation_is_unavailable_with_its_failure_and_the_provenance_stays(
    explaining: Scenario, failure: str, failure_class: str, requests: int
) -> None:
    discovery_id = discover(explaining)["discovery_id"]

    asked = explain(explaining, discovery_id, fake_failure=failure)

    found = discovery(explaining, discovery_id)["explanation"]
    assert (found["run"]["status"], found["run"]["failure_class"]) == ("failed", failure_class)
    assert found["written"] is None  # nothing stored as checked
    assert explaining.outputs(asked["explanation_id"]) == []
    [attempt] = explaining.attempts(asked["explanation_id"])
    assert attempt["requests_sent"] == requests  # one repair at most, none for a cut-off
    shown = slate(explaining, discovery_id)
    assert all(s["why_it_could_suit"] and s["linked_evidence"] for s in shown["suggestions"])
    assert found["can_retry"] is False  # a request was sent: the slate had its one call
    again = ask(explaining, discovery_id)
    assert (again.status_code, again.json()["run"]["status"]) == (200, "failed")  # no 2nd call
    tried = ask(explaining, discovery_id, retry=True)
    assert (tried.status_code, tried.json()["error"]["code"]) == (409, "SLATE_ALREADY_EXPLAINED")
    runs = explaining.api.get(f"{base(explaining)}/runs", explaining.token).json()["items"]
    assert sorted(r["kind"] for r in runs) == ["discovery", "slate_explanation"]
    assert explaining.profile()["version"] == 2
    assert explaining.leaks() == []


@pytest.mark.req("REC1-11", "MODEL-08")
def test_a_note_refused_before_any_request_can_be_tried_again_and_the_new_run_replaces_it(
    explaining: Scenario,
) -> None:
    discovery_id = discover(explaining)["discovery_id"]
    failed = refused_before_any_request(explaining, discovery_id)
    [refusal] = explaining.attempts(failed["explanation_id"])
    run_limit(explaining, 150_000_000)

    plain = ask(explaining, discovery_id)  # not a Try again: the same failed run
    retried = ask(explaining, discovery_id, retry=True)
    worker = explaining.worker("explainer")
    explaining.wait_terminal(retried.json()["explanation_id"])
    assert worker.stop() == 0

    assert (failed["run"]["status"], failed["run"]["failure_class"]) == (
        "failed",
        "budget_exceeded",
    )
    assert (refusal["spend_state"], refusal["requests_sent"]) == ("none", None)
    assert failed["can_retry"] is True
    assert (plain.status_code, plain.json()["explanation_id"]) == (200, failed["explanation_id"])
    assert retried.status_code == 202, retried.text
    assert retried.json()["explanation_id"] != failed["explanation_id"]
    current = discovery(explaining, discovery_id)["explanation"]
    assert current["explanation_id"] == retried.json()["explanation_id"]  # replaces the link
    assert current["written"] is not None
    assert current["can_retry"] is False
    # The failed run is kept, with its refusal, beside the one that wrote the note.
    runs = explaining.api.get(f"{base(explaining)}/runs", explaining.token).json()["items"]
    notes = {r["run_id"]: r["status"] for r in runs if r["kind"] == "slate_explanation"}
    assert notes == {failed["explanation_id"]: "failed", current["explanation_id"]: "complete"}
    assert explaining.leaks() == []


@pytest.mark.req("REC1-11")
def test_concurrent_tries_again_start_one_run(explaining: Scenario) -> None:
    discovery_id = discover(explaining)["discovery_id"]
    failed = refused_before_any_request(explaining, discovery_id)
    run_limit(explaining, 150_000_000)
    results: list[Any] = []

    def try_again() -> None:
        results.append(ask(explaining, discovery_id, retry=True))

    threads = [threading.Thread(target=try_again) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(r.status_code for r in results) == [200, 200, 200, 202]
    started = {r.json()["explanation_id"] for r in results}
    assert len(started) == 1
    assert started != {failed["explanation_id"]}
    runs = explaining.api.get(f"{base(explaining)}/runs", explaining.token).json()["items"]
    assert sum(r["kind"] == "slate_explanation" for r in runs) == 2  # the failed one and one new


@pytest.mark.req("REC1-11", "PROF-05")
def test_an_explanation_is_refused_before_any_run_for_a_failed_discovery_or_changed_answers(
    explaining: Scenario,
) -> None:
    failed = discover(explaining, fake_failure="invalid_always")["discovery_id"]
    no_searches = ask(explaining, failed)
    good = discover(explaining)["discovery_id"]
    changed = explaining.api.write(
        "PUT",
        f"{base(explaining)}/profile",
        explaining.token,
        {"expected_version": 2, "profile": {**ANSWERS, "work_style": {"state": "skipped"}}},
    )
    assert changed.status_code == 201, changed.text

    stale_view = ask(explaining, good, version=2)
    stale_answers = ask(explaining, good, version=3)
    # Fix round 1: answers too short to quote (no content word) would make a doomed call.
    short = explaining.api.write(
        "PUT",
        f"{base(explaining)}/profile",
        explaining.token,
        {"expected_version": 3, "profile": profile_with(enjoyed_tasks=["art"])},
    )
    assert short.status_code == 201, short.text
    unquotable = ask(explaining, discover(explaining, version=4)["discovery_id"], version=4)

    assert (unquotable.status_code, unquotable.json()["error"]["code"]) == (
        422,
        "INSUFFICIENT_EVIDENCE",
    )
    assert unquotable.json()["error"]["details"]["reason"] == "no_quotable_answer"
    assert (no_searches.status_code, no_searches.json()["error"]["code"]) == (
        409,
        "PROPOSAL_NOT_AVAILABLE",
    )
    for refused in (stale_view, stale_answers):
        assert (refused.status_code, refused.json()["error"]["code"]) == (
            409,
            "STALE_INPUT_VERSION",
        )
    assert discovery(explaining, good)["explanation"] is None
    runs = explaining.api.get(f"{base(explaining)}/runs", explaining.token).json()["items"]
    assert {r["kind"] for r in runs} == {"discovery"}  # every refusal came before any run


@pytest.mark.req("REC1-11")
@pytest.mark.parametrize(
    "answer",
    ["'odd jobs'", "\N{LEFT SINGLE QUOTATION MARK}odd jobs\N{RIGHT SINGLE QUOTATION MARK}"],
    ids=["straight quotes", "curly quotes"],
)
def test_an_answer_the_check_cannot_quote_whole_is_refused_before_any_run(
    explaining: Scenario, answer: str
) -> None:
    # Task 6b re-review 3, Minor 1: 'odd jobs' holds a content word, but its closing quote
    # after an "s" reads as a plural possessive, so the answer quoted whole never verifies.
    # The pre-check reads answers as the check does, so this costs no paid repair.
    only = explaining.api.write(
        "PUT",
        f"{base(explaining)}/profile",
        explaining.token,
        {"expected_version": 2, "profile": profile_with(enjoyed_tasks=[answer])},
    )
    assert only.status_code == 201, only.text

    refused = ask(explaining, discover(explaining, version=3)["discovery_id"], version=3)

    assert (refused.status_code, refused.json()["error"]["code"]) == (
        422,
        "INSUFFICIENT_EVIDENCE",
    )
    assert refused.json()["error"]["details"]["reason"] == "no_quotable_answer"
    runs = explaining.api.get(f"{base(explaining)}/runs", explaining.token).json()["items"]
    assert {r["kind"] for r in runs} == {"discovery"}  # refused before any run


@pytest.mark.req("REC1-11")
def test_the_export_cites_the_deterministic_provenance_never_the_written_text(
    explaining: Scenario,
) -> None:
    discovery_id = discover(explaining)["discovery_id"]
    explain(explaining, discovery_id)
    chosen = slate(explaining, discovery_id)["suggestions"][0]
    made = explaining.api.write(
        "POST",
        f"{base(explaining)}/targets",
        explaining.token,
        {"expected_version": 2, "concept_id": chosen["concept_id"], "discovery_id": discovery_id},
    )
    assert made.status_code == 201, made.text

    export = explaining.api.get(f"{base(explaining)}/export", explaining.token).json()

    assert export["format_version"] == 4
    [exported] = export["discoveries"]
    written = exported["explanation"]["written"]
    assert written["suggestions"][0]["claims"]  # kept, labelled as written by the model
    claims = {c["text"] for s in written["suggestions"] for c in s["claims"]}
    target = export["profile_versions"][-1]["document"]["target_titles"]
    [source] = [s for s in export["sources"] if s["source_ref_id"] == target["source_ref_id"]]
    assert (source["kind"], source["discovery_id"], source["locator"]) == (
        "occupation_choice",
        discovery_id,
        chosen["sources"][0]["uri"],
    )  # the ESCO record and the discovery that found it
    assert source["discovery_id"] != exported["explanation"]["explanation_id"]
    assert not any(text in str(export["sources"]) for text in claims)
    queries = exported["proposal"]["queries"]
    assert queries
    assert {(e["field"], e["text"]) for q in queries for e in q["based_on"]} <= ANSWER_PAIRS


@pytest.mark.req("REC1-11", "BND1-11", "TEST1-10")
def test_a_demo_workspace_s_slate_is_explained_offline_by_the_labelled_fixture_explainer(
    infra: Infra, api: ApiClient, api_deps: ApiDependencies, ada: str, tmp_path: Path
) -> None:
    settings = api_deps.settings.model_copy(update={"runtime_mode": RuntimeMode.DEMO})
    deps = dataclasses.replace(api_deps, settings=settings)
    with TestClient(
        create_app(deps),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57004),
    ) as client:
        demo = ApiClient(client)
        workspace = demo.write(
            "POST",
            "/v1/workspaces",
            ada,
            {"name": "Demo explanation", "data_mode": "demo", "synthetic": True},
        ).json()["workspace_id"]
        demo.write(
            "PUT",
            f"/v1/workspaces/{workspace}/profile",
            ada,
            {"expected_version": 0, "profile": ANSWERS},
        )
        found = demo.write(
            "POST", f"/v1/workspaces/{workspace}/discoveries", ada, {"expected_profile_version": 1}
        ).json()
        scenario = make_scenario(infra, api, ada, tmp_path)
        worker = scenario.worker("worker")
        scenario.wait_terminal(found["discovery_id"])
        asked = demo.write(
            "POST",
            f"/v1/workspaces/{workspace}/discoveries/{found['discovery_id']}/explanation",
            ada,
            {"expected_profile_version": 1},
        )
        assert asked.status_code == 202, asked.text
        run = asked.json()["run"]
        scenario.wait_terminal(run["run_id"])
        assert worker.stop() == 0

    assert (run["model_id"], run["model_mode"]) == ("careerwright-fixture-explainer-1", "fixture")
    shown = api.get(f"/v1/workspaces/{workspace}/discoveries/{found['discovery_id']}", ada).json()
    written = shown["explanation"]["written"]
    assert written["origin"] == "fixture"
    assert all(
        c["text"].startswith("Demo explainer (synthetic)")
        for s in written["suggestions"]
        for c in s["claims"]
    )
    [attempt] = scenario.attempts(run["run_id"])
    assert (attempt["spend_state"], attempt["cost_nano_usd"]) == ("none", 0)  # no provider
