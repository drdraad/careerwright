"""The capability API against real PostgreSQL 16 (S4.1-S4.6; ADR 0012): matrices, the
question graph and readiness read from the option pack, the ESCO sample and the person's
evidence; every write takes an expected version and an Idempotency-Key; another person sees
nothing; history is append-only."""

import uuid
from pathlib import Path
from typing import Any

import psycopg
import pytest

from nessa.capability.commands import committed_data
from nessa.catalogue.esco import ESCO_RELEASE, concept_id, parse_release
from nessa.catalogue.releases import read_verified
from nessa.seed import INVITED_ACTORS
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra
from tools.datasets import DATASETS_DIR

pytestmark = pytest.mark.integration

ADA_ID, BEN_ID = (str(actor.actor_id) for actor in INVITED_ACTORS)
NURSE = "Registered nurse"
DATA = "Data quality analyst"
NMC = "pack:registered-nurse-manchester:nmc-registration"
VALIDATION = "pack:data-quality-analyst-manchester:data-validation"
NURSE_URI = "http://data.europa.eu/esco/occupation/8d3e8aaa-791b-4c75-a465-f3f827028f50"
BOOKKEEPER_URI = "http://data.europa.eu/esco/occupation/c3aae59e-1441-4b3e-bdd1-6da50dc7cf42"


def workspace_with_targets(api: ApiClient, token: str, *targets: str) -> str:
    workspace_id = str(api.create_workspace(token)["workspace_id"])
    response = api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        token,
        {
            "expected_version": 0,
            "profile": profile_with(cities=["Manchester"], target_titles=list(targets)),
        },
    )
    assert response.status_code == 201, response.text
    return workspace_id


def base(workspace_id: str) -> str:
    return f"/v1/workspaces/{workspace_id}/capability"


def matrices(api: ApiClient, token: str, workspace_id: str) -> dict[str, Any]:
    response = api.get(f"{base(workspace_id)}/matrices", token)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def matrix(body: dict[str, Any], title: str) -> dict[str, Any]:
    return next(m for m in body["matrices"] if m["target_title"] == title)


def row(found: dict[str, Any], row_id: str) -> dict[str, Any]:
    return next(r for r in found["rows"] if r["row_id"] == row_id)


@pytest.mark.req("MAP1-01", "MAP1-05", "OPTN-08")
def test_matrices_are_served_for_each_target_with_the_pack_s_date_and_review_states(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, NURSE, DATA)

    body = matrices(api, ada, workspace_id)

    assert body["version"] == 0
    assert body["profile_version"] == 1
    assert body["pack"]["pack_version"] == "0.1.0"
    assert body["pack"]["dated"] == "2026-10-29"
    assert body["pack"]["records_reviewed"] == 0
    assert body["pack"]["records_proposed"] > 0
    assert body["reference"]["review_state"] == "proposed"
    # A synthetic workspace's results say so (M8).
    assert (body["synthetic"], body["data_mode"]) == (True, "live_assisted")
    nurse = matrix(body, NURSE)
    assert nurse["synthetic"] is True
    assert nurse["sources"]["pack_target"]["basis"] == "title"
    assert nurse["status"] == "provisional_no_specialist_review"
    assert nurse["sources"]["occupation"]["label"] == "nurse responsible for general care"
    assert nurse["sources"]["occupation"]["basis"] == "pack_crosswalk"
    assert nurse["sources"]["esco_release"].endswith("-sample")
    gate = row(nurse, NMC)
    assert gate["gate"]["protected"] is True
    assert gate["required"] is True
    assert all(c["review_state"] == "proposed" for c in gate["citations"])
    assert {c["as_of"] for c in gate["citations"]} == {"2026-10-29"}
    # The ESCO sample's relations seed rows of unknown importance for this target.
    assert any(r["esco"] and r["importance"] == "unknown" for r in nurse["rows"])


def test_a_workspace_without_targets_has_no_matrices(api: ApiClient, ada: str) -> None:
    workspace_id = str(api.create_workspace(ada)["workspace_id"])

    body = matrices(api, ada, workspace_id)

    assert (body["matrices"], body["profile_version"]) == ([], 0)


@pytest.mark.req("MAP1-01")
def test_the_person_s_own_examples_are_counted_for_their_target_and_never_as_postings(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA, NURSE)
    pasted = api.write(
        "POST",
        f"/v1/workspaces/{workspace_id}/research/pasted",
        ada,
        {
            "target": "data quality ANALYST",
            "title": "Data Quality Analyst",
            "text": "We need a data quality analyst who can write SQL and fix duplicates.",
        },
    )

    body = matrices(api, ada, workspace_id)

    assert pasted.status_code == 201, pasted.text
    data = matrix(body, DATA)
    assert data["coverage"]["exemplars"] == 1
    assert data["coverage"]["exemplar_rows_read"] is False
    assert data["coverage"]["posting_copies"] == 4  # the pack's, unchanged by the example
    assert matrix(body, NURSE)["coverage"]["exemplars"] == 0


@pytest.mark.req("RDY1-04", "READINESS-04", "MAP1-05")
def test_the_registration_gate_cannot_be_demoted_through_the_api(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, NURSE)
    nurse = matrix(matrices(api, ada, workspace_id), NURSE)

    refused = api.write(
        "POST",
        f"{base(workspace_id)}/edits",
        ada,
        {
            "expected_version": 0,
            "target": NURSE,
            "matrix_version": nurse["matrix_version"],
            "row_id": NMC,
            "action": "set_importance",
            "importance": "preferred",
            "reason": "I would rather not need it",
            "warning_acknowledged": True,
        },
    )

    assert refused.status_code == 409
    assert refused.json()["error"]["code"] == "PROTECTED_GATE"
    assert infra.query(
        "SELECT count(*) AS n FROM nessa.matrix_edits WHERE workspace_id = %s", (workspace_id,)
    ) == [{"n": 0}]
    after = matrix(matrices(api, ada, workspace_id), NURSE)
    assert after["definition_version"] == nurse["definition_version"]


@pytest.mark.req("MAP1-05")
def test_a_gate_s_source_can_be_challenged_and_the_gate_stays(api: ApiClient, ada: str) -> None:
    workspace_id = workspace_with_targets(api, ada, NURSE)
    nurse = matrix(matrices(api, ada, workspace_id), NURSE)

    challenged = api.write(
        "POST",
        f"{base(workspace_id)}/edits",
        ada,
        {
            "expected_version": 0,
            "target": NURSE,
            "matrix_version": nurse["matrix_version"],
            "row_id": NMC,
            "action": "challenge",
            "reason": "I registered abroad; my route may differ",
        },
    )
    after = matrix(matrices(api, ada, workspace_id), NURSE)

    assert challenged.status_code == 201, challenged.text
    gate = row(after, NMC)
    assert gate["required"] is True
    assert gate["gate"]["protected"] is True
    assert [c["reason"] for c in gate["challenges"]] == ["I registered abroad; my route may differ"]
    assert after["definition_version"] == nurse["definition_version"]


@pytest.mark.req("MAP1-01", "MAP1-07")
def test_every_crosswalk_names_an_esco_concept_of_the_full_pinned_release() -> None:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    catalogue = parse_release(read_verified(release, ESCO_RELEASE), ESCO_RELEASE)
    occupations = {o.uri: o for o in catalogue.occupations}
    skills = {s.uri: s for s in catalogue.skills}
    relations = {(r.concept_id, r.skill_id): r.relation.value for r in catalogue.occupation_skills}
    reference = committed_data().reference

    for crosswalk in reference.targets:
        occupation = occupations[crosswalk.esco_occupation]
        assert occupation.preferred_label == crosswalk.esco_label
        for rubric in reference.rubrics:
            if not rubric.skill_id.startswith(f"pack:{crosswalk.target_id}:"):
                continue
            assert rubric.esco_skill is not None
            skill = skills[rubric.esco_skill]
            assert next(lbl.text for lbl in skill.labels if lbl.kind.value == "preferred") == (
                rubric.esco_label
            )
            # Each crosswalked skill is an essential relation of its target's occupation.
            assert relations[(occupation.concept_id, skill.skill_id)] == "essential"
    assert reference.esco_release == ESCO_RELEASE.dataset_id


@pytest.mark.req("RDY1-04", "BND1-08")
def test_a_stated_gate_shows_a_pathway_outside_the_model_never_ineligibility(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, NURSE)

    stated = api.write(
        "POST",
        f"{base(workspace_id)}/statements",
        ada,
        {
            "expected_version": 0,
            "subject": "gate:nmc-registration",
            "holding": "not_held",
            "verified": False,
        },
    )
    readiness = api.get(f"{base(workspace_id)}/readiness", ada).json()

    assert stated.status_code == 201, stated.text
    assert stated.json()["version"] == 1
    [assessment] = readiness["assessments"]
    assert assessment["state"] == "not_ready"
    assert {b["kind"] for b in assessment["blockers"]} == {"not_held", "pathway_outside_model"}
    action = next(a for a in assessment["actions"] if NMC in a["rows"])
    assert (action["state"], action["code"]) == ("outside_planning_model", "MODEL_SCOPE_EXCEEDED")
    assert "ineligible" not in str(readiness)
    assert assessment["evidence_version"] == 1


@pytest.mark.req("ASSESS-01", "ASSESS-05", "RDY1-05")
def test_evidence_is_recorded_with_an_expected_version_and_changes_only_its_own_gap(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    found = matrix(matrices(api, ada, workspace_id), DATA)
    validation = row(found, VALIDATION)
    before = api.get(f"{base(workspace_id)}/readiness", ada).json()["assessments"][0]
    body = {
        "expected_version": 0,
        "subject": validation["subject"],
        "rubric_version": validation["rubric"]["version_id"],
        "answer": "done_independently",
        "self_assessed_level": 2,
        "example": "Traced duplicated patient records to a bad import and fixed the job",
        "last_done": "2026-08",
        "context": "paid_work",
        "independence": "independent",
    }
    key = uuid.uuid4()

    recorded = api.write("POST", f"{base(workspace_id)}/evidence", ada, body, key=key)
    replayed = api.write("POST", f"{base(workspace_id)}/evidence", ada, body, key=key)
    stale = api.write("POST", f"{base(workspace_id)}/evidence", ada, body)
    after = api.get(f"{base(workspace_id)}/readiness", ada).json()["assessments"][0]

    assert recorded.status_code == 201, recorded.text
    assert (replayed.status_code, replayed.json()) == (201, recorded.json())
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert after["evidence_version"] == 1
    assert (after["matrix_version"], after["definition_version"]) == (
        found["matrix_version"],
        found["definition_version"],
    )
    gaps_before = {g["row_id"]: g for g in before["gaps"]}
    gaps_after = {g["row_id"]: g for g in after["gaps"]}
    assert VALIDATION in gaps_before
    assert VALIDATION not in gaps_after
    assert {k: v for k, v in gaps_before.items() if k != VALIDATION} == gaps_after
    evidence_row = next(r for r in after["rows"] if r["row_id"] == VALIDATION)
    assert evidence_row["evidence"]["confidence"] == "provisional"
    assert evidence_row["evidence"]["self_assessed_level"] == 2
    assert evidence_row["evidence"]["demonstrated_level"] is None


def test_evidence_for_a_subject_no_matrix_holds_is_refused_and_nothing_is_saved(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)

    refused = api.write(
        "POST",
        f"{base(workspace_id)}/evidence",
        ada,
        {
            "expected_version": 0,
            "subject": "esco:not-a-skill",
            "rubric_version": None,
            "answer": "unsure",
            "self_assessed_level": None,
        },
    )
    inconsistent = api.write(
        "POST",
        f"{base(workspace_id)}/evidence",
        ada,
        {
            "expected_version": 0,
            "subject": row(matrix(matrices(api, ada, workspace_id), DATA), VALIDATION)["subject"],
            "rubric_version": None,
            "answer": "unsure",
            "self_assessed_level": 2,
        },
    )
    validation = row(matrix(matrices(api, ada, workspace_id), DATA), VALIDATION)
    contradictory = api.write(
        "POST",
        f"{base(workspace_id)}/evidence",
        ada,
        {
            "expected_version": 0,
            "subject": validation["subject"],
            "rubric_version": validation["rubric"]["version_id"],
            "answer": "not_learned",
            "self_assessed_level": 3,
            "example": "an example",
            "last_done": "2026-09",
        },
    )

    assert refused.status_code == 422
    assert refused.json()["error"]["code"] == "VALIDATION_FAILED"
    assert inconsistent.status_code == 422
    assert contradictory.status_code == 422
    assert contradictory.json()["error"]["details"]["reason"] == "inconsistent_evidence"
    assert infra.query(
        "SELECT count(*) AS n FROM nessa.skill_evidence WHERE workspace_id = %s", (workspace_id,)
    ) == [{"n": 0}]


@pytest.mark.req("MAP1-04", "MAP1-06", "VERSIONS-04")
def test_relaxing_an_essential_row_needs_the_warning_and_makes_a_new_definition(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    found = matrix(matrices(api, ada, workspace_id), DATA)
    edit = {
        "expected_version": 0,
        "target": DATA,
        "matrix_version": found["matrix_version"],
        "row_id": VALIDATION,
        "action": "set_importance",
        "importance": "preferred",
        "reason": "None of my target employers asks for it",
    }

    unwarned = api.write("POST", f"{base(workspace_id)}/edits", ada, edit)
    accepted = api.write(
        "POST", f"{base(workspace_id)}/edits", ada, {**edit, "warning_acknowledged": True}
    )
    stale_matrix = api.write(
        "POST",
        f"{base(workspace_id)}/edits",
        ada,
        {**edit, "expected_version": 1, "importance": "essential"},
    )
    after = matrix(matrices(api, ada, workspace_id), DATA)

    assert unwarned.status_code == 409
    assert unwarned.json()["error"]["code"] == "CONFIRMATION_REQUIRED"
    assert accepted.status_code == 201, accepted.text
    assert stale_matrix.status_code == 409
    assert stale_matrix.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert after["definition_version"] != found["definition_version"]
    assert accepted.json()["definition_version"] == after["definition_version"]
    [applied] = after["edits"]
    assert applied["from_definition_version"] == found["definition_version"]
    assert applied["to_definition_version"] == after["definition_version"]
    assert applied["reason"] == "None of my target employers asks for it"
    assert row(after, VALIDATION)["source_importance"] == "essential"
    [stored] = infra.query(
        "SELECT from_matrix_version, to_matrix_version, recorded_by FROM nessa.matrix_edits "
        "WHERE workspace_id = %s",
        (workspace_id,),
    )
    assert stored["from_matrix_version"] == found["matrix_version"]
    assert stored["to_matrix_version"] == after["matrix_version"]


@pytest.mark.req("ASSESS-03")
def test_questions_ask_gates_first_and_can_be_stopped_and_resumed(api: ApiClient, ada: str) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA, NURSE)

    asking = api.get(f"{base(workspace_id)}/questions", ada).json()
    stopped = api.write(
        "PUT",
        f"{base(workspace_id)}/questions/state",
        ada,
        {"expected_version": 0, "stopped": True},
    )
    paused = api.get(f"{base(workspace_id)}/questions", ada).json()

    assert asking["graph"]["state"] == "asking"
    assert asking["graph"]["prompts"][0]["subject"] == "gate:nmc-registration"
    assert len(asking["graph"]["initial"]) <= 12
    assert stopped.status_code == 200, stopped.text
    assert stopped.json() == {
        "version": 1,
        "questions_stopped": True,
        "recorded_id": None,
        "matrix_version": None,
        "definition_version": None,
    }
    assert paused["graph"]["state"] == "stopped"
    assert paused["graph"]["prompts"] == asking["graph"]["prompts"]


def choose(api: ApiClient, token: str, workspace_id: str, version: int, concept: str) -> None:
    """Choose a target the way the product does: an ESCO occupation, stored by its label."""
    chosen = api.write(
        "POST",
        f"/v1/workspaces/{workspace_id}/targets",
        token,
        {"expected_version": version, "concept_id": concept},
    )
    assert chosen.status_code == 201, chosen.text


@pytest.mark.req("MAP1-05", "RDY1-04", "READINESS-04")
def test_a_nursing_occupation_chosen_in_the_product_keeps_the_registration_gate(
    api: ApiClient, ada: str
) -> None:
    workspace_id = str(api.create_workspace(ada)["workspace_id"])
    choose(api, ada, workspace_id, 0, str(concept_id(NURSE_URI)))

    [found] = matrices(api, ada, workspace_id)["matrices"]
    [assessment] = api.get(f"{base(workspace_id)}/readiness", ada).json()["assessments"]
    graph = api.get(f"{base(workspace_id)}/questions", ada).json()["graph"]

    assert found["target_title"] == "nurse responsible for general care"
    assert found["sources"]["pack_target"]["target_id"] == "registered-nurse-manchester"
    assert found["sources"]["pack_target"]["basis"] == "esco_crosswalk"
    assert row(found, NMC)["gate"]["kind"] == "legal_practice"
    assert assessment["state"] == "not_yet_assessed"
    assert {"row_id": NMC, "kind": "unresolved"} in assessment["blockers"]
    assert graph["prompts"][0]["subject"] == "gate:nmc-registration"


@pytest.mark.req("RDY1-03", "READINESS-03")
def test_a_bookkeeper_chosen_in_the_product_reaches_p05_s_pack_target_despite_a_shared_label(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # In ESCO "bookkeeper" is also an alternative label of "accountant"; the sample lacks
    # accountant, so another occupation is given the label for this test (C1(b), round 2).
    bookkeeper = str(concept_id(BOOKKEEPER_URI))
    [other] = infra.query(
        "SELECT concept_id FROM nessa.occupation_concepts WHERE preferred_label = %s",
        ("accounting assistant",),
    )
    infra.query(
        "INSERT INTO nessa.occupation_labels (concept_id, label, normalised, kind) "
        "VALUES (%s, 'bookkeeper', 'bookkeeper', 'alternative')",
        (other["concept_id"],),
    )
    try:
        chosen = str(api.create_workspace(ada)["workspace_id"])
        choose(api, ada, chosen, 0, bookkeeper)
        typed = workspace_with_targets(api, ada, "bookkeeper")
        found = {
            name: matrices(api, ada, workspace)["matrices"][0]
            for name, workspace in (("chosen", chosen), ("typed", typed))
        }
    finally:
        infra.query(
            "DELETE FROM nessa.occupation_labels WHERE concept_id = %s AND normalised = %s",
            (other["concept_id"], "bookkeeper"),
        )

    # The choice is read from its own source; a typed title prefers ESCO's preferred label.
    assert found["chosen"]["sources"]["occupation"]["basis"] == "occupation_choice"
    assert found["typed"]["sources"]["occupation"]["basis"] == "esco_label"
    for matrix_out in found.values():
        assert matrix_out["sources"]["occupation"]["concept_id"] == bookkeeper
        assert matrix_out["sources"]["pack_target"]["target_id"] == "bookkeeping-assistant-leeds"
        assert matrix_out["sources"]["pack_target"]["basis"] == "esco_crosswalk"
        assert row(matrix_out, "gate:uk-right-to-work")["gate"]["kind"] == "eligibility"


@pytest.mark.req("RDY1-01", "MAP1-05")
def test_an_unmodelled_target_or_a_regulated_one_without_a_typed_gate_is_never_ready_now(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, "Marine biologist")
    [doctor] = infra.query(
        "SELECT concept_id FROM nessa.occupation_concepts WHERE preferred_label = %s AND regulated",
        ("general practitioner",),
    )
    choose(api, ada, workspace_id, 1, str(doctor["concept_id"]))

    body = matrices(api, ada, workspace_id)
    assessments = api.get(f"{base(workspace_id)}/readiness", ada).json()["assessments"]
    graph = api.get(f"{base(workspace_id)}/questions", ada).json()["graph"]

    assert [m["target_title"] for m in body["matrices"]] == [
        "Marine biologist",
        "general practitioner",
    ]
    assert matrix(body, "Marine biologist")["sources"]["occupation_note"] == "no_exact_esco_label"
    regulation = row(matrix(body, "general practitioner"), "gate:occupation-regulation")
    assert regulation["gate"]["modelled"] is False
    assert [a["state"] for a in assessments] == ["insufficient_coverage"] * 2
    assert "review_current_postings_and_apply" not in [a["primary_action"] for a in assessments]
    assert {"row_id": "gate:occupation-regulation", "kind": "unresolved"} in assessments[1][
        "blockers"
    ]
    assert graph["state"] == "insufficient_coverage"


@pytest.mark.req("OPTN-08", "BND1-12")
def test_questions_and_readiness_carry_the_pack_labels_and_the_workspace_s_synthetic_label(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    validation = row(matrix(matrices(api, ada, workspace_id), DATA), VALIDATION)
    assert (
        api.write(
            "POST",
            f"{base(workspace_id)}/evidence",
            ada,
            {
                "expected_version": 0,
                "subject": validation["subject"],
                "rubric_version": validation["rubric"]["version_id"],
                "answer": "done_with_help",
                "self_assessed_level": 1,
                "example": "Found duplicates with a colleague's help",
                "last_done": "2026-07",
            },
        ).status_code
        == 201
    )
    real = str(api.create_workspace(ada, "Not synthetic", synthetic=False)["workspace_id"])
    assert (
        api.write(
            "PUT",
            f"/v1/workspaces/{real}/profile",
            ada,
            {"expected_version": 0, "profile": profile_with(target_titles=[DATA])},
        ).status_code
        == 201
    )

    questions = api.get(f"{base(workspace_id)}/questions", ada).json()
    readiness = api.get(f"{base(workspace_id)}/readiness", ada).json()
    unlabelled = api.get(f"{base(real)}/readiness", ada).json()

    assert questions["pack"]["dated"] == "2026-10-29"
    assert questions["reference"]["review_state"] == "proposed"
    prompt_rows = [r for p in questions["graph"]["prompts"] for r in p["rows"]]
    assert prompt_rows
    assert {r["review_state"] for r in prompt_rows} == {"proposed"}
    [assessment] = readiness["assessments"]
    assert {r["review_state"] for r in assessment["rows"]} == {"proposed"}
    assert {g["review_state"] for g in assessment["gaps"]} == {"proposed"}
    candidates = [c for a in assessment["actions"] for c in a["candidates"]]
    assert {c["option_id"] for c in candidates} == {"option:C01", "option:C04"}
    assert {c["as_of"] for c in candidates} == {"2026-10-29"}
    labels = (questions["synthetic"], questions["graph"]["synthetic"])
    assert labels == (True, True)
    assert (readiness["synthetic"], assessment["synthetic"]) == (True, True)
    assert (unlabelled["synthetic"], unlabelled["assessments"][0]["synthetic"]) == (False, False)
    assert unlabelled["data_mode"] == "live_assisted"


@pytest.mark.req("SEC-01", "SEC-02")
def test_another_person_sees_and_writes_none_of_it(
    api: ApiClient, ada: str, ben: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    found = row(matrix(matrices(api, ada, workspace_id), DATA), VALIDATION)
    assert (
        api.write(
            "POST",
            f"{base(workspace_id)}/evidence",
            ada,
            {
                "expected_version": 0,
                "subject": found["subject"],
                "rubric_version": found["rubric"]["version_id"],
                "answer": "done_with_help",
                "self_assessed_level": 1,
            },
        ).status_code
        == 201
    )

    for path in ("matrices", "questions", "readiness"):
        response = api.get(f"{base(workspace_id)}/{path}", ben)
        assert (response.status_code, response.json()["error"]["code"]) == (404, "NOT_FOUND")
    written = api.write(
        "PUT",
        f"{base(workspace_id)}/questions/state",
        ben,
        {"expected_version": 1, "stopped": True},
    )
    assert written.status_code == 404
    for table in ("capability_states", "skill_evidence"):
        statement = f"SELECT count(*) AS n FROM nessa.{table} WHERE workspace_id = %s"  # noqa: S608
        as_owner = infra.as_role("pg_api", statement, (workspace_id,), actor=ADA_ID)
        as_other = infra.as_role("pg_api", statement, (workspace_id,), actor=BEN_ID)
        assert int(str(as_owner[0]["n"])) == 1
        assert as_other[0]["n"] == 0
    for table in ("requirement_statements", "matrix_edits"):
        statement = f"SELECT count(*) AS n FROM nessa.{table} WHERE workspace_id = %s"  # noqa: S608
        assert infra.as_role("pg_api", statement, (workspace_id,), actor=BEN_ID)[0]["n"] == 0
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        infra.as_role(
            "pg_api",
            "INSERT INTO nessa.requirement_statements (statement_id, workspace_id, state_version, "
            "subject, holding, verified, recorded_by) VALUES (%s, %s, 9, 'gate:x', 'held', "
            "false, %s)",
            (uuid.uuid4(), workspace_id, BEN_ID),
            actor=BEN_ID,
        )


@pytest.mark.req("ASSESS-02")
def test_the_database_refuses_an_answer_that_contradicts_its_level(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)
    for answer, level in (("not_learned", 2), ("understand_not_tried", 1), ("done_with_help", 3)):
        with pytest.raises(psycopg.errors.CheckViolation):
            infra.as_role(
                "pg_api",
                "INSERT INTO nessa.skill_evidence (evidence_id, workspace_id, state_version, "
                "subject, answer, self_assessed_level, method, recorded_by) VALUES "
                "(%s, %s, 1, 'esco:x', %s, %s, 'self_report', %s)",
                (uuid.uuid4(), workspace_id, answer, level, ADA_ID),
                actor=ADA_ID,
            )


@pytest.mark.req("SEC-02")
def test_capability_history_is_append_only_for_the_api_role(infra: Infra) -> None:
    for statement in (
        "UPDATE nessa.skill_evidence SET self_assessed_level = 4",
        "DELETE FROM nessa.skill_evidence",
        "UPDATE nessa.requirement_statements SET verified = true",
        "DELETE FROM nessa.requirement_statements",
        "UPDATE nessa.matrix_edits SET reason = 'x'",
        "DELETE FROM nessa.matrix_edits",
        "DELETE FROM nessa.capability_states",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            infra.as_role("pg_api", statement, actor=ADA_ID)
