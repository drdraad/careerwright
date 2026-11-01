"""The Skills chapter's facts and the person's chosen advert spans, end to end against real
PostgreSQL 16, the option pack and the labelled ESCO sample (Task 10, backend half; MAP1-01,
ASSESS-03, RDY1-03, PROF-13, STATE-11; ADR 0012 as amended). No model is called."""

import uuid
from typing import Any

import psycopg
import pytest

from careerwright.seed import INVITED_ACTORS
from tests.integration.test_capability import DATA, NMC, NURSE, base, workspace_with_targets
from tests.integration.test_origin import choose_role, occupation
from tests.integration.test_title_details import put_details
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra

pytestmark = pytest.mark.integration

ADA_ID, BEN_ID = (str(actor.actor_id) for actor in INVITED_ACTORS)
IT = "IT support technician"
TICKETING = "pack:it-support-technician-bristol:service-desk-ticketing"
ADVERT = (
    "Data Quality Analyst, Manchester.\n"
    "You will write SQL to find duplicate records.\n"
    "Experience with Power BI is a plus.\n"
)


def skills(api: ApiClient, token: str, workspace_id: str) -> dict[str, Any]:
    response = api.get(f"{base(workspace_id)}/skills", token)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def target(body: dict[str, Any], title: str) -> dict[str, Any]:
    return next(t for t in body["targets"] if t["target_title"] == title)


def paste(api: ApiClient, token: str, workspace_id: str, for_target: str) -> str:
    pasted = api.write(
        "POST",
        f"/v1/workspaces/{workspace_id}/research/pasted",
        token,
        {"target": for_target, "title": "Data Quality Analyst", "text": ADVERT},
    )
    assert pasted.status_code == 201, pasted.text
    return str(pasted.json()["job"]["job_id"])  # the paste answers with the job's detail


def select(
    api: ApiClient,
    token: str,
    workspace_id: str,
    version: int,
    job_id: str,
    spans: list[tuple[int, int]],
    title: str = DATA,
) -> Any:
    return api.write(
        "POST",
        f"{base(workspace_id)}/advert-spans",
        token,
        {
            "expected_version": version,
            "target": title,
            "job_id": job_id,
            "spans": [{"start": s, "end": e} for s, e in spans],
        },
    )


def span_of(words: str) -> tuple[int, int]:
    start = ADVERT.index(words)
    return start, start + len(words)


@pytest.mark.req("RDY1-03", "MAP1-09", "OPTN-08")
def test_a_target_outside_the_pack_is_not_assessed_yet_and_shows_what_it_asks(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, "Doula", DATA)

    body = skills(api, ada, workspace_id)

    outside = target(body, "Doula")
    assert outside["assessment_state"] == "not_assessed"
    assert outside["not_assessed_reason"] == "no_rubric"
    assert outside["readiness"] is None
    assert outside["seed"] == "no_occupation"
    assert (outside["esco_listed"], outside["requirements"], outside["examples"]) == ([], [], [])
    # A pack target: what it asks, each row with its review state and its records' date (R9).
    data = target(body, DATA)
    assert data["assessment_state"] == "not_assessed"
    assert data["not_assessed_reason"] == "rubrics_not_reviewed"
    assert data["readiness"] is None
    assert data["requirements"]
    assert {r["review_state"] for r in data["requirements"]} == {"proposed"}
    assert {r["as_of"] for r in data["requirements"]} == {"2026-10-29"}
    assert data["matrix_version"]
    assert data["definition_version"]
    assert (body["pack"]["pack_version"], body["pack"]["dated"]) == ("0.2.0", "2026-10-30")
    assert body["reference"]["review_state"] == "proposed"
    assert (body["synthetic"], body["data_mode"]) == (True, "live_assisted")
    # The evidence questions, shared across targets, come with it.
    assert body["questions"]["targets"]


@pytest.mark.req("STATE-11", "PROF-13")
def test_no_role_means_no_usual_in_your_role_panel_never_an_empty_one(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    no_role = skills(api, ada, workspace_id)
    choose_role(api, ada, workspace_id, occupation(api, ada, "bookkeeper"), 1)

    with_role = skills(api, ada, workspace_id)

    assert no_role["usual_in_role"] is None
    panel = with_role["usual_in_role"]
    assert panel is not None
    assert panel["occupation_label"] == "bookkeeper"
    assert panel["skills"]
    assert {s["state"] for s in panel["skills"]} == {"usual_in_role"}


@pytest.mark.req("PROF-13", "RDY1-04", "READINESS-04")
def test_qualifications_are_entry_facts_beside_the_requirements_that_name_them(
    api: ApiClient, ada: str
) -> None:
    workspace_id = str(api.create_workspace(ada)["workspace_id"])
    put = api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        ada,
        {
            "expected_version": 0,
            "profile": profile_with(
                cities=["Manchester"],
                target_titles=[IT, NURSE],
                qualifications=[
                    {"name": "ITIL Practitioner", "status": "expected"},
                    {"name": "NMC registration", "status": "achieved"},
                ],
            ),
        },
    )
    assert put.status_code == 201, put.text

    body = skills(api, ada, workspace_id)

    ticketing = next(r for r in target(body, IT)["requirements"] if r["row_id"] == TICKETING)
    assert ticketing["entry_facts"] == [
        {
            "qualification": "ITIL Practitioner",
            "status": "expected",
            "standing": "expected_not_met",
        }
    ]
    gate = next(r for r in target(body, NURSE)["requirements"] if r["row_id"] == NMC)
    assert gate["gate"]["protected"] is True
    assert [f["standing"] for f in gate["entry_facts"]] == ["achieved_unverified"]
    assert [q["status"] for q in body["qualifications"]] == ["expected", "achieved"]
    # An entry fact never settles the gate: the readiness endpoint still has it unresolved.
    readiness = api.get(f"{base(workspace_id)}/readiness", ada).json()
    nurse = next(a for a in readiness["assessments"] if a["target_title"] == NURSE)
    assert next(r for r in nurse["rows"] if r["row_id"] == NMC)["status"] == "unresolved"


@pytest.mark.req("MAP1-09", "ASSESS-02")
def test_a_skill_marked_not_part_of_my_job_is_shown_as_such_and_changes_nothing_computed(
    api: ApiClient, ada: str
) -> None:
    title = "nurse responsible for general care"
    workspace_id = workspace_with_targets(api, ada, title)
    before = skills(api, ada, workspace_id)
    listed = target(before, title)
    assert listed["seed"] == "esco_occupation"
    skill = next(s for s in listed["esco_listed"] if s["relation"] == "essential")

    marked = put_details(
        api, ada, workspace_id, "target", title, 0, not_part_of_job=[skill["skill_id"]]
    )
    after = skills(api, ada, workspace_id)

    assert marked.status_code == 201, marked.text
    shown = target(after, title)
    assert next(s for s in shown["esco_listed"] if s["skill_id"] == skill["skill_id"])[
        "not_part_of_job"
    ]
    assert shown["details_version"] == 1
    for unchanged in ("requirements", "readiness", "matrix_version", "definition_version"):
        assert shown[unchanged] == listed[unchanged]
    assert after["questions"] == before["questions"]
    assert after["version"] == before["version"]  # never evidence: no capability write


@pytest.mark.req("MAP1-01", "SEC-09")
def test_the_person_chooses_spans_in_their_own_example_with_a_version_and_a_key(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA, NURSE)
    job_id = paste(api, ada, workspace_id, DATA)
    shown = target(skills(api, ada, workspace_id), DATA)["examples"]

    chosen = select(api, ada, workspace_id, 0, job_id, [span_of("write SQL to find duplicate")])
    stale = select(api, ada, workspace_id, 0, job_id, [span_of("Power BI")])
    outside = select(api, ada, workspace_id, 1, job_id, [(0, len(ADVERT) + 5)])
    wrong_target = select(api, ada, workspace_id, 1, job_id, [span_of("SQL")], title=NURSE)
    not_an_example = select(api, ada, workspace_id, 1, str(uuid.uuid4()), [span_of("SQL")])
    after = target(skills(api, ada, workspace_id), DATA)["examples"]
    cleared = select(api, ada, workspace_id, 1, job_id, [])

    assert [(e["job_id"], e["text"], e["spans"]) for e in shown] == [(job_id, ADVERT, [])]
    assert chosen.status_code == 201, chosen.text
    assert chosen.json()["version"] == 1
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert (outside.status_code, outside.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert outside.json()["error"]["details"]["reason"] == "span_outside_text"
    assert wrong_target.status_code == 404
    assert not_an_example.status_code == 404
    [example] = after
    assert [s["excerpt"] for s in example["spans"]] == ["write SQL to find duplicate"]
    assert cleared.status_code == 201, cleared.text
    assert target(skills(api, ada, workspace_id), DATA)["examples"][0]["spans"] == []


@pytest.mark.req("SEC-01", "SEC-02")
def test_another_person_sees_and_chooses_none_of_it_and_the_choices_are_append_only(
    api: ApiClient, ada: str, ben: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    job_id = paste(api, ada, workspace_id, DATA)
    assert select(api, ada, workspace_id, 0, job_id, [span_of("SQL")]).status_code == 201

    seen = api.get(f"{base(workspace_id)}/skills", ben)
    written = select(api, ben, workspace_id, 1, job_id, [span_of("Power BI")])

    assert (seen.status_code, seen.json()["error"]["code"]) == (404, "NOT_FOUND")
    assert written.status_code == 404
    statement = (
        "SELECT count(*) AS n FROM careerwright.advert_span_selections WHERE workspace_id = %s"
    )
    assert infra.as_role("pg_api", statement, (workspace_id,), actor=ADA_ID)[0]["n"] == 1
    assert infra.as_role("pg_api", statement, (workspace_id,), actor=BEN_ID)[0]["n"] == 0
    for change in (
        "UPDATE careerwright.advert_span_selections SET spans = '[]'",
        "DELETE FROM careerwright.advert_span_selections",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            infra.as_role("pg_api", change, actor=ADA_ID)


@pytest.mark.req("SEC-02", "ACQ-01")
def test_the_api_opens_only_a_pasted_body_and_only_in_its_owner_s_workspace(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    paste(api, ada, workspace_id, DATA)
    [attempt] = infra.as_role(
        "pg_api",
        "SELECT attempt_id FROM careerwright.source_attempts WHERE workspace_id = %s",
        (workspace_id,),
        actor=ADA_ID,
    )
    opened = "SELECT count(*) AS n FROM careerwright.pasted_example_document(%s)"

    assert infra.as_role("pg_api", opened, (attempt["attempt_id"],), actor=ADA_ID)[0]["n"] == 1
    assert infra.as_role("pg_api", opened, (attempt["attempt_id"],), actor=BEN_ID)[0]["n"] == 0
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        infra.as_role(
            "pg_api", "SELECT ciphertext FROM careerwright.source_documents", actor=ADA_ID
        )


@pytest.mark.req("MAP1-01")
def test_the_database_refuses_a_selection_whose_spans_break_the_rules(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    for spans in ('{"start": 0}', '[{"start": 4, "end": 4}]', '[{"start": -1, "end": 2}]'):
        with pytest.raises(psycopg.errors.CheckViolation):
            infra.as_role(
                "pg_api",
                "INSERT INTO careerwright.advert_span_selections (selection_id, workspace_id, "
                "state_version, target_key, job_id, content_sha256, spans, recorded_by) VALUES "
                "(%s, %s, 1, 'data quality analyst', %s, %s, %s, %s)",
                (uuid.uuid4(), workspace_id, uuid.uuid4(), "0" * 64, spans, ADA_ID),
                actor=ADA_ID,
            )
