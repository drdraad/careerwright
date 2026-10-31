"""Your title, recognised (Task 6d slice B; S2.8; ADR 0015 decisions 1 to 3; ADR 0007 decision
13 as amended), end to end against real PostgreSQL 16, the labelled ESCO sample and the
synthetic sample of the UK job-title index (`tests/support/reference_data.py`): the first
question's type-ahead over ESCO and the index, the first answer in the person's own words,
"Which of these is closest?" with "None of these is my job", a title idea the index lists, and
each title's stored record. No model is called."""

import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from careerwright.db import system_transaction
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra, migrator_engine
from tools.evaluation import Case, CaseKind, observe_discovery_offline

pytestmark = pytest.mark.integration


def titles(api: ApiClient, token: str, typed: str, **params: Any) -> dict[str, Any]:
    found = api.get("/v1/taxonomy/titles", token, q=typed, **params)
    assert found.status_code == 200, found.text
    body: dict[str, Any] = found.json()
    return body


def offered(body: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (m["source"], m["matched_label"] if m["source"] == "esco" else m["title"])
        for m in body["matches"]
    ]


def name_role(api: ApiClient, token: str, workspace: str, title: str, version: int) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace}/origin/role/title",
        token,
        {"expected_version": version, "title": title},
    )


def closest(api: ApiClient, token: str, workspace: str, concept: str | None, version: int) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace}/origin/role/closest",
        token,
        {"expected_version": version, "concept_id": concept},
    )


def origin(api: ApiClient, token: str, workspace: str) -> dict[str, Any]:
    found = api.get(f"/v1/workspaces/{workspace}/origin", token)
    assert found.status_code == 200, found.text
    body: dict[str, Any] = found.json()
    return body


def record(infra: Infra, workspace: str, title: str) -> dict[str, Any]:
    engine = migrator_engine(infra)
    try:
        with system_transaction(engine) as tx:
            row = (
                tx.execute(
                    sa.text(
                        "SELECT kind, link, occupation_uri, soc_codes, isco_codes, coverage, "
                        "source_ref_id FROM careerwright.target_records WHERE workspace_id = :ws "
                        "AND title_key = careerwright.concept_key(:title)"
                    ),
                    {"ws": workspace, "title": title},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()
    return dict(row)


@pytest.mark.req("DIV1-13", "TAX1-01")
def test_the_type_ahead_offers_uk_job_titles_marked_with_every_group_esco_first_on_ties(
    api: ApiClient, ada: str
) -> None:
    nurse = titles(api, ada, "Registered nurse")
    doula = titles(api, ada, "Doula")
    prompt = titles(api, ada, "prompt eng")
    help_desk = titles(api, ada, "IT support")
    data = titles(api, ada, "data")

    # A title only the index lists is offered as a UK job title, once however many entries
    # the index gives it, with every group ONS codes it to, none picked.
    [uk_nurse] = nurse["matches"]
    assert (uk_nurse["source"], uk_nurse["title"]) == ("uk_title_index", "Registered nurse")
    assert uk_nurse["soc_codes"] == ["2235", "2237"]
    assert [g["code"] for g in uk_nurse["isco_groups"]] == ["2221"]
    assert (nurse["partial"], nurse["uk_total"]) == (False, 1)
    assert offered(doula) == [("uk_title_index", "Doula")]
    assert offered(prompt) == [("uk_title_index", "Prompt engineer")]
    # A title ESCO offers is ESCO's alone, never offered again as the index's.
    assert offered(help_desk) == [("esco", "IT support technician")]
    # ESCO first on ties: every ESCO title beginning with "data" comes before the index's
    # "Data quality analyst", which comes before any title that only holds the word later.
    shown = offered(data)
    at = shown.index(("uk_title_index", "Data quality analyst"))
    assert shown[:at]
    assert all(
        source == "esco" and label.casefold().startswith("data") for source, label in shown[:at]
    )
    assert not any(
        source == "esco" and label.casefold().startswith("data") for source, label in shown[at:]
    )


@pytest.mark.req("DIV1-13", "DIV1-03")
def test_a_title_neither_list_holds_asks_about_esco_s_closest_titles_and_refuses_nothing(
    api: ApiClient, ada: str
) -> None:
    found = titles(api, ada, "Bookkeeping assistant")

    assert found["partial"] is True
    assert {m["source"] for m in found["matches"]} == {"esco"}
    assert found["matches"][0]["title"] == "bookkeeper"
    # "Use my own words" keeps anything typed: the title nobody lists is the role, as typed.
    workspace = api.create_workspace(ada, "Own words (synthetic)")["workspace_id"]
    kept = name_role(api, ada, workspace, "Bookkeeping assistant", 0)
    again = name_role(api, ada, workspace, "Bookkeeping assistant", 1)
    shown = origin(api, ada, workspace)["role"]

    assert kept.status_code == 201, kept.text
    assert kept.json()["document"]["current_role"]["value"] == "Bookkeeping assistant"
    assert (again.status_code, again.json()["version"]) == (200, 1)  # already the role
    assert (shown["text"], shown["state"], shown["kind"]) == (
        "Bookkeeping assistant",
        "not_in_esco",
        "own_words",
    )
    # No list codes it to a group, so nothing asks the person to pick another job.
    assert (shown["closest"], shown["uk_groups"], shown["choices"]) == (None, [], [])
    refused = closest(api, ada, workspace, None, 1)
    assert (refused.status_code, refused.json()["error"]["details"]["reason"]) == (
        422,
        "not_offered",
    )


@pytest.mark.req("DIV1-13", "DIV1-14", "PROF-10")
def test_a_uk_title_keeps_the_person_s_words_and_asks_which_esco_occupation_is_closest(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace = api.create_workspace(ada, "UK title (synthetic)")["workspace_id"]
    named = name_role(api, ada, workspace, "Registered nurse", 0)
    asked = origin(api, ada, workspace)["role"]

    assert named.status_code == 201, named.text
    assert (asked["text"], asked["state"], asked["kind"]) == (
        "Registered nurse",
        "not_in_esco",
        "ons",
    )
    assert [g["code"] for g in asked["uk_groups"]] == ["2221"]
    assert asked["closest"]["decision"] == "not_yet"
    [group] = asked["closest"]["groups"]
    assert group["group"]["code"] == "2221"
    assert [o["title"] for o in group["occupations"]] == [
        "nurse responsible for general care",
        "specialist nurse",
    ]
    # Its record: an ONS title with ONS's codes. It is the pack's "Registered nurse" too, so it
    # links to the crosswalk's occupation for Skills alone; ESCO itself names none for it.
    stored = record(infra, workspace, "Registered nurse")
    assert (stored["kind"], stored["link"], stored["soc_codes"], stored["isco_codes"]) == (
        "ons",
        "pack_crosswalk",
        ["2235", "2237"],
        ["2221"],
    )

    # The closest occupation becomes the role's ESCO occupation; the words stay the person's.
    specialist = next(o["concept_id"] for o in group["occupations"] if "specialist" in o["title"])
    chosen = closest(api, ada, workspace, specialist, 1)
    seeded = origin(api, ada, workspace)

    assert chosen.status_code == 201, chosen.text
    assert chosen.json()["document"]["current_role"]["value"] == "Registered nurse"
    role = seeded["role"]
    assert (role["text"], role["state"], role["chosen"], role["kind"]) == (
        "Registered nurse",
        "esco",
        True,
        "ons",
    )
    assert role["occupation"]["title"] == "specialist nurse"
    assert (role["closest"]["decision"], role["closest"]["chosen"]) == ("chosen", specialist)
    assert seeded["usual_skills"]  # the chosen occupation's, usual in the role
    stored = record(infra, workspace, "Registered nurse")
    assert (stored["kind"], stored["link"], stored["source_ref_id"] is not None) == (
        "ons",
        "occupation_choice",
        True,
    )

    # "None of these is my job": the role names no ESCO occupation, and nothing asks for one.
    none = closest(api, ada, workspace, None, 2)
    kept = origin(api, ada, workspace)
    same = closest(api, ada, workspace, None, 3)

    assert none.status_code == 201, none.text
    assert none.json()["document"]["current_role"]["value"] == "Registered nurse"
    assert (kept["role"]["state"], kept["role"]["occupation"], kept["role"]["chosen"]) == (
        "not_in_esco",
        None,
        False,
    )
    assert kept["role"]["closest"]["decision"] == "none_of_these"
    assert (kept["usual_skills"], kept["destinations"]) == ([], [])
    assert (same.status_code, same.json()["version"]) == (200, 3)
    assert record(infra, workspace, "Registered nurse")["link"] == "none_of_these"
    outside = closest(api, ada, workspace, str(uuid.uuid4()), 3)
    assert (outside.status_code, outside.json()["error"]["details"]["reason"]) == (
        422,
        "not_offered",
    )


@pytest.mark.req("DIV1-14")
def test_a_title_coded_to_several_groups_shows_every_group_none_picked(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Several groups (synthetic)")["workspace_id"]
    assert name_role(api, ada, workspace, "Doula", 0).status_code == 201
    doula = origin(api, ada, workspace)["role"]
    assert name_role(api, ada, workspace, "Data quality analyst", 1).status_code == 201
    analyst = origin(api, ada, workspace)["role"]

    assert name_role(api, ada, workspace, "Nurse", 2).status_code == 201
    nurse = origin(api, ada, workspace)["role"]

    assert [g["group"]["code"] for g in doula["closest"]["groups"]] == ["5322"]
    # A group the held release has no occupation in is still shown, honestly empty.
    [empty] = analyst["closest"]["groups"]
    assert (empty["group"]["code"], empty["occupations"]) == ("2421", [])
    assert analyst["closest"]["decision"] == "not_yet"
    # Coded to two groups: both are shown, with their occupations, and none is picked.
    assert [g["group"]["code"] for g in nurse["closest"]["groups"]] == ["2221", "5322"]
    assert (nurse["closest"]["decision"], nurse["closest"]["chosen"]) == ("not_yet", None)
    assert (nurse["state"], nurse["occupation"]) == ("not_in_esco", None)

    # "IT support technician" is an ESCO title too (the help desk agent's), so ESCO names it:
    # the index's group is kept, and no closest question is asked.
    typed = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        ada,
        {"expected_version": 3, "profile": profile_with(current_role="IT support technician")},
    )
    assert typed.status_code == 201, typed.text
    role = origin(api, ada, workspace)["role"]
    assert (role["state"], role["kind"], role["closest"]) == ("esco", "ons", None)
    assert [g["code"] for g in role["uk_groups"]] == ["3512"]


@pytest.mark.req("DIV1-04", "TEST1-15", "REC1-06")
def test_a_title_idea_the_uk_index_lists_is_a_suggestion_beside_the_slate_never_in_it(
    infra: Infra,
) -> None:
    case = Case(
        id="ad hoc",
        kind=CaseKind.DISCOVERY,
        title="ad hoc",
        requirements=[],
        synthetic=True,
        profile={"enjoyed_tasks": ["writing prompts for AI tools", "analysing data"]},
        discovery_output={
            "queries": [
                {"text": "analyse data", "channel": "tasks", "based_on": ["analysing data"]}
            ],
            "hypotheses": [
                {"title": "data analyst", "based_on": ["analysing data"]},
                {"title": "Prompt engineer", "based_on": ["writing prompts for AI tools"]},
                {"title": "orbital gardener", "based_on": ["writing prompts for AI tools"]},
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

    ideas = {i["title"]: (i["reason"], i["outcome"]) for i in observed["title_ideas"]}
    assert ideas == {
        "data analyst": ("in_esco", "matched"),
        "Prompt engineer": ("in_uk_title_index", "not_matched"),
        "orbital gardener": ("not_yet_found", "not_matched"),
    }
    [prompt] = [i for i in observed["title_ideas"] if i["title"] == "Prompt engineer"]
    assert prompt["based_on"] == [
        {"field": "enjoyed_tasks", "text": "writing prompts for AI tools"}
    ]
    shown = {s["title"] for s in observed["suggestions"]}
    assert "data analyst" in shown
    assert not {"Prompt engineer", "orbital gardener"} & shown  # never in the slate's pool


@pytest.mark.req("PROF-10", "MAP1-05", "DIV1-13")
def test_a_target_the_uk_index_lists_is_an_ons_title_and_another_nursing_field_is_not_covered(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Targets (synthetic)")["workspace_id"]
    targets = ["Prompt engineer", "Registered nurse (mental health)", "Registered nurse (adult)"]
    put = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        ada,
        {"expected_version": 0, "profile": profile_with(target_titles=targets)},
    )
    assert put.status_code == 201, put.text
    stored = api.get(f"/v1/workspaces/{workspace}/targets", ada).json()["targets"]
    found = {t["title"]: (t["kind"], t["coverage"], t["pack_target_id"]) for t in stored}

    assert found == {
        "Prompt engineer": ("ons", "not_covered", None),
        "Registered nurse (mental health)": ("own_words", "not_covered", None),
        "Registered nurse (adult)": ("own_words", "pack_target", "registered-nurse-manchester"),
    }
    sketch = api.get(f"/v1/workspaces/{workspace}/sketch", ada).json()
    resolutions = {t["title"]: t["resolution"] for t in sketch["targets"]}
    assert resolutions == {
        "Prompt engineer": "uk_title",
        "Registered nurse (mental health)": "not_found",
        "Registered nurse (adult)": "not_found",
    }
