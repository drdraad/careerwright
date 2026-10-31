"""Your title, recognised (Task 6d slice B; S2.8; ADR 0015 decisions 1 to 3; ADR 0007 decision
13 as amended), end to end against real PostgreSQL 16, the labelled ESCO sample and the
synthetic sample of the UK job-title index (`tests/support/reference_data.py`): the first
question's type-ahead over ESCO and the index, the first answer in the person's own words,
"Which of these is closest?" with "None of these is my job", a title idea the index lists, and
each title's stored record. No model is called."""

import uuid
from typing import Any

import psycopg
import pytest
import sqlalchemy as sa

from careerwright.db import system_transaction
from careerwright.profile import safety
from tests.integration.test_interview_choices import DISTRESS, SERVICES
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


def name_role(
    api: ApiClient, token: str, workspace: str, title: str, version: int, **more: Any
) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace}/origin/role/title",
        token,
        {"expected_version": version, "title": title, **more},
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


def edit(api: ApiClient, token: str, workspace: str, version: int, **answers: Any) -> None:
    """A direct edit in What we know: the whole profile, these answers given."""
    put = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        token,
        {"expected_version": version, "profile": profile_with(**answers)},
    )
    assert put.status_code == 201, put.text


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


@pytest.mark.req("PROF-09", "DIV1-13")
def test_the_first_question_goes_through_the_support_screen_and_keeps_nothing_of_it(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # Design review I-3: a risk phrase typed as the title was offered back as "Use my own
    # words", saved as the role and echoed as "your role", with no support panel. The title
    # field now goes through the same screen as a message (`careerwright.profile.safety`).
    workspace = api.create_workspace(ada, "Support at the start (synthetic)")["workspace_id"]
    typed = api.get("/v1/taxonomy/titles", ada, q=DISTRESS)
    named = name_role(api, ada, workspace, DISTRESS, 0)
    stale = name_role(api, ada, workspace, DISTRESS, 4)
    declined = name_role(api, ada, workspace, DISTRESS, 0, none_of_these=True)
    ordinary = titles(api, ada, "Registered nurse")

    # The type-ahead matches nothing on those words and brings the calm panel instead.
    assert typed.status_code == 200, typed.text
    body = typed.json()
    assert (body["matches"], body["partial"], body["total"], body["uk_total"]) == ([], False, 0, 0)
    panel = body["support_note"]
    assert panel["message"] == safety.SUPPORT_NOTE_TITLE
    assert panel["policy_version"] == safety.POLICY_VERSION
    assert {r["name"] for r in panel["resources"]} == SERVICES
    assert ordinary["support_note"] is None
    # Never kept as the role: refused, with the panel beside the refusal, whatever else the
    # refusal is (a stale version too), so the person can type again or skip.
    for refused in (named, declined):
        assert refused.status_code == 422, refused.text
        assert refused.json()["error"]["details"] == {"field": "title", "reason": "support_screen"}
        assert refused.json()["support_note"] == panel
    assert (stale.status_code, stale.json()["support_note"]) == (409, panel)
    # Nothing about it is stored: no profile version, source, record or receipt.
    assert api.get(f"/v1/workspaces/{workspace}/profile", ada).json()["version"] == 0
    stored = infra.query(
        "SELECT (SELECT count(*) FROM careerwright.profile_versions WHERE workspace_id = %s) "
        "AS versions, (SELECT count(*) FROM careerwright.source_references WHERE "
        "workspace_id = %s) AS sources, (SELECT count(*) FROM careerwright.target_records "
        "WHERE workspace_id = %s) AS records, (SELECT count(*) FROM "
        "careerwright.command_receipts WHERE workspace_id = %s AND command = 'name_role') "
        "AS receipts",
        (workspace,) * 4,
    )
    assert stored == [{"versions": 0, "sources": 0, "records": 0, "receipts": 0}]


@pytest.mark.req("DIV1-13", "DIV1-03", "VERSIONS-01")
def test_none_of_these_in_the_type_ahead_is_the_person_s_refusal_recorded_by_a_versioned_command(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # Design review I-2: the partial list's "None of these is my job" recorded nothing, so the
    # slate later asked for "the ESCO occupation closest to it". It is now the person's
    # refusal, recorded like every consequential write: expected version and Idempotency-Key.
    workspace = api.create_workspace(ada, "None of these, typed (synthetic)")["workspace_id"]
    stale = name_role(api, ada, workspace, "Bookkeeping assistant", 1, none_of_these=True)
    declined = name_role(api, ada, workspace, "Bookkeeping assistant", 0, none_of_these=True)
    again = name_role(api, ada, workspace, "Bookkeeping assistant", 1, none_of_these=True)
    role = origin(api, ada, workspace)["role"]

    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert (declined.status_code, declined.json()["version"]) == (201, 1)
    assert declined.json()["document"]["current_role"]["value"] == "Bookkeeping assistant"
    assert (again.status_code, again.json()["version"]) == (200, 1)  # already recorded
    assert (role["state"], role["kind"], role["occupation"], role["closest"]) == (
        "not_in_esco",
        "own_words",
        None,
        None,
    )
    stored = record(infra, workspace, "Bookkeeping assistant")
    assert (stored["kind"], stored["link"], stored["occupation_uri"]) == (
        "own_words",
        "none_of_these",
        None,
    )

    # The same words kept without the refusal ("Use my own words", or Enter) record none (the
    # title is the option pack's target, so it links to the pack's crosswalk, for Skills
    # alone); the refusal given later for the role's own words is a new version.
    other = api.create_workspace(ada, "Own words, typed (synthetic)")["workspace_id"]
    assert name_role(api, ada, other, "Bookkeeping assistant", 0).status_code == 201
    assert record(infra, other, "Bookkeeping assistant")["link"] == "pack_crosswalk"
    later = name_role(api, ada, other, "Bookkeeping assistant", 1, none_of_these=True)
    assert (later.status_code, later.json()["version"]) == (201, 2)
    assert record(infra, other, "Bookkeeping assistant")["link"] == "none_of_these"


@pytest.mark.req("DIV1-14", "VERSIONS-01")
def test_none_of_these_at_the_closest_question_is_a_new_version_so_a_stale_tab_conflicts(
    api: ApiClient, ada: str
) -> None:
    # App review M-5: "None of these is my job" from not_yet made no profile version, so a
    # stale tab sending the same expected version could override it without a conflict.
    workspace = api.create_workspace(ada, "None of these, closest (synthetic)")["workspace_id"]
    assert name_role(api, ada, workspace, "Registered nurse", 0).status_code == 201
    [group] = origin(api, ada, workspace)["role"]["closest"]["groups"]
    specialist = next(o["concept_id"] for o in group["occupations"] if "specialist" in o["title"])

    none = closest(api, ada, workspace, None, 1)
    stale = closest(api, ada, workspace, specialist, 1)
    role = origin(api, ada, workspace)["role"]

    assert (none.status_code, none.json()["version"]) == (201, 2)
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert (role["closest"]["decision"], role["occupation"]) == ("none_of_these", None)


@pytest.mark.req("DIV1-13", "DIV1-03")
def test_own_words_of_only_punctuation_are_kept_as_given(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # App review M-8: nothing typed is refused, not even a title with no letter or digit (the
    # type-ahead searches nothing for it; the person's own words are still theirs to keep).
    workspace = api.create_workspace(ada, "Punctuation (synthetic)")["workspace_id"]
    searched = api.get("/v1/taxonomy/titles", ada, q="--")
    kept = name_role(api, ada, workspace, "--", 0)
    role = origin(api, ada, workspace)["role"]

    assert searched.json()["error"]["details"]["reason"] == "no_search_terms"
    assert kept.status_code == 201, kept.text
    assert kept.json()["document"]["current_role"]["value"] == "--"
    assert (role["text"], role["state"], role["kind"], role["closest"]) == (
        "--",
        "not_in_esco",
        "own_words",
        None,
    )
    stored = record(infra, workspace, "--")  # its concept key is empty, which no CHECK forbids
    assert (stored["kind"], stored["link"], stored["occupation_uri"]) == ("own_words", "none", None)


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


@pytest.mark.req("DIV1-14", "PROF-10", "MAP1-09")
def test_the_role_s_record_is_its_one_truth_so_an_edit_of_its_words_keeps_the_closest_choice(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # App review I-1: the closest choice was kept on the role's source and in its record, and
    # an edit of the words (even their capitals) lost the first while the second still said
    # "chosen". The record is now the role's one truth, as it is each target's.
    workspace = api.create_workspace(ada, "One record (synthetic)")["workspace_id"]
    assert name_role(api, ada, workspace, "Registered nurse", 0).status_code == 201
    [group] = origin(api, ada, workspace)["role"]["closest"]["groups"]
    specialist = next(o["concept_id"] for o in group["occupations"] if "specialist" in o["title"])
    assert closest(api, ada, workspace, specialist, 1).status_code == 201

    def seeded(text: str) -> None:
        shown = origin(api, ada, workspace)
        role = shown["role"]
        assert (role["text"], role["state"], role["chosen"], role["kind"]) == (
            text,
            "esco",
            True,
            "ons",
        )
        assert role["occupation"]["concept_id"] == specialist
        assert (role["closest"]["decision"], role["closest"]["chosen"]) == ("chosen", specialist)
        assert shown["usual_skills"]  # the chosen occupation's skills still seed the role

    # The same title as a concept, in What we know: capitals, then away and back.
    edit(api, ada, workspace, 2, current_role="Registered Nurse")
    seeded("Registered Nurse")
    edit(api, ada, workspace, 3, current_role="Doula")
    away = origin(api, ada, workspace)["role"]
    assert (away["state"], away["occupation"], away["closest"]["decision"]) == (
        "not_in_esco",
        None,
        "not_yet",
    )
    edit(api, ada, workspace, 4, current_role="Registered nurse")
    seeded("Registered nurse")
    stored = record(infra, workspace, "Registered nurse")
    assert (stored["kind"], stored["link"]) == ("ons", "occupation_choice")

    # App review M-8: a target with the role's title reads the same record, so it names the
    # occupation the person chose as closest for their role (ruling 1's consequence).
    edit(
        api,
        ada,
        workspace,
        5,
        current_role="Registered nurse",
        target_titles=["Registered nurse"],
    )
    [target] = api.get(f"/v1/workspaces/{workspace}/targets", ada).json()["targets"]
    assert (target["title"], target["link"], target["concept_id"]) == (
        "Registered nurse",
        "occupation_choice",
        specialist,
    )
    seeded("Registered nurse")


@pytest.mark.req("PROF-10", "MAP1-09")
def test_a_role_chosen_by_one_of_esco_s_other_titles_is_stored_as_an_esco_title(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # App review M-1: "IT support technician" is one of the ICT help desk agent's other titles
    # in ESCO (and a UK job title too); chosen from ESCO, the role's record says it is ESCO's.
    [match] = titles(api, ada, "IT support")["matches"]
    workspace = api.create_workspace(ada, "Other ESCO title (synthetic)")["workspace_id"]
    chosen = api.write(
        "POST",
        f"/v1/workspaces/{workspace}/origin/role",
        ada,
        {
            "expected_version": 0,
            "concept_id": match["concept_id"],
            "label": match["matched_label"],
        },
    )
    role = origin(api, ada, workspace)["role"]

    assert chosen.status_code == 201, chosen.text
    assert (role["text"], role["state"], role["chosen"], role["kind"]) == (
        "IT support technician",
        "esco",
        True,
        "esco",
    )
    assert role["occupation"]["concept_id"] == match["concept_id"]
    stored = record(infra, workspace, "IT support technician")
    assert (stored["kind"], stored["link"], stored["source_ref_id"] is not None) == (
        "esco",
        "occupation_choice",
        True,
    )


@pytest.mark.req("PROF-10", "DIV1-14")
def test_the_record_checks_repeat_the_role_space_rules(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # App review M-4 (migration 0038): kept in code only, an ONS record with no codes would
    # silently never ask the closest question, and "None of these" could be anyone's.
    workspace = api.create_workspace(ada, "Record checks (synthetic)")["workspace_id"]
    assert name_role(api, ada, workspace, "Registered nurse", 0).status_code == 201
    assert closest(api, ada, workspace, None, 1).status_code == 201
    row = "WHERE workspace_id = %s AND title_key = 'registered nurse'"
    refused = [
        ("an_ons_title_has_its_codes", "soc_codes = '{}'"),
        ("an_ons_title_has_its_codes", "isco_codes = '{}'"),
        ("none_of_these_is_the_person_s_own", "recorded_by = NULL"),
        # An ESCO title has no ONS codes (0034), so only the new rule refuses this one.
        ("none_of_these_is_the_person_s_own", "kind = 'esco', soc_codes = '{}', isco_codes = '{}'"),
    ]
    for constraint, change in refused:
        with pytest.raises(psycopg.errors.CheckViolation, match=constraint):
            infra.query(f"UPDATE careerwright.target_records SET {change} {row}", (workspace,))  # noqa: S608
    # The type-ahead's refusal is on the person's own words, which the rule allows.
    assert (
        name_role(api, ada, workspace, "Orbital gardener", 2, none_of_these=True).status_code == 201
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
    nothing_offered = closest(api, ada, workspace, None, 2)

    assert name_role(api, ada, workspace, "Nurse", 2).status_code == 201
    nurse = origin(api, ada, workspace)["role"]

    assert [g["group"]["code"] for g in doula["closest"]["groups"]] == ["5322"]
    # Design review M-5: a title whose groups hold no ESCO occupation in the held release is
    # never asked "Which of these is closest?" with nothing to pick; its group is kept.
    assert (analyst["closest"], analyst["kind"], analyst["state"]) == (None, "ons", "not_in_esco")
    assert [g["code"] for g in analyst["uk_groups"]] == ["2421"]
    assert (nothing_offered.status_code, nothing_offered.json()["error"]["details"]["reason"]) == (
        422,
        "not_offered",
    )
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
