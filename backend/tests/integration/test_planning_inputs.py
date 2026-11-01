"""The person's planning inputs over the API against real PostgreSQL 16 (Task 12a; ADR 0013
decision 11 and its amendment): every input round-trips through its command with an expected
version and an Idempotency-Key; a stale version is refused; an answer must fit one of the
workspace's own options; work rights are never read from a city; another person sees nothing;
history is append-only; and the database repeats the domain rules."""

import json
import uuid
from typing import Any

import psycopg
import pytest

from careerwright.seed import INVITED_ACTORS
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra

pytestmark = pytest.mark.integration

ADA_ID, BEN_ID = (str(actor.actor_id) for actor in INVITED_ACTORS)
DATA = "Data quality analyst"


def gbp(minor: int) -> dict[str, Any]:
    return {"minor_units": minor, "currency": "GBP"}


def workspace(api: ApiClient, token: str, **profile: Any) -> str:
    workspace_id = str(api.create_workspace(token)["workspace_id"])
    response = api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        token,
        {
            "expected_version": 0,
            "profile": profile_with(cities=["Manchester"], target_titles=[DATA], **profile),
        },
    )
    assert response.status_code == 201, response.text
    return workspace_id


def path(workspace_id: str) -> str:
    return f"/v1/workspaces/{workspace_id}/planning/inputs"


def read(api: ApiClient, token: str, workspace_id: str) -> dict[str, Any]:
    response = api.get(path(workspace_id), token)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def everything() -> dict[str, Any]:
    """Every input stated, P01's figures and one answer about each kind of thing (synthetic)."""
    return {
        "objective_basis": "economic",
        "baseline": {"kind": "current_role", "net_income": gbp(200000)},
        "continuation": {"hours_per_week": 30, "net_income": gbp(200000)},
        "opening_cash": gbp(600000),
        "living_costs": gbp(100000),
        "reserve": gbp(50000),
        "monthly_deficit_cap": gbp(80000),
        "weekly_availability": 40,
        "commitments": [{"kind": "commute", "hours_per_week": 5}],
        "existing_debts": [
            {"monthly_repayment": gbp(5000), "balance": gbp(120000), "annual_interest_bps": 1990}
        ],
        "scenario_delay_months": 2,
        "work_rights": "held",
        "remote_work": {
            "works_remotely": True,
            "employment_country": "GB-ENG",
            "timezone": "Europe/London",
        },
        "admissions": [],
        "shared_schemes": ["funding:employer"],  # fix round 1: it may pay for several options
        "variants": [
            {
                "variant_id": "offering:C04~pay-in-full",
                "work_pattern": {
                    "kind": "retain_work",
                    "hours_per_week": 30,
                    "net_income": gbp(200000),
                },
                "wage": None,
                "supports": [
                    {
                        "instrument_id": "funding:employer",
                        "kind": "employer_support",
                        "covers_fees_in_full": False,
                        "amount": gbp(50000),
                        "paid_to": "provider",
                        "paid_month_offset": None,
                        "proven_before_outflows": False,
                        "eligibility": "confirmed",
                        "award": "approved",
                        "assumed": False,
                    }
                ],
                "stacking_confirmed": False,
                "entry_requirements_met": None,
                "condition_statuses": {},
            },
            {
                "variant_id": "offering:C01#full_time",
                "work_pattern": None,
                "wage": None,
                "supports": [],
                "stacking_confirmed": False,
                "entry_requirements_met": False,
                "condition_statuses": {"eligibility_age": "confirmed"},
            },
        ],
        "outcome_decisions": [
            {
                "outcome_id": "outcome:C01.1",
                "decision": "accept",
                "evidence_kind": None,
                "level_on_completion": None,
                "rubric_version": None,
                "reason": None,
            }
        ],
    }


@pytest.mark.req("PLN-11", "API-05", "VERSIONS-01")
def test_every_input_round_trips_through_its_command_and_a_stale_version_is_refused(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = workspace(api, ada, direct_spend_cap=gbp(150000))
    empty = read(api, ada, workspace_id)
    key = uuid.uuid4()

    written = api.write(
        "PUT", path(workspace_id), ada, {"expected_version": 0, "inputs": everything()}, key=key
    )
    stored = read(api, ada, workspace_id)
    replayed = api.write(
        "PUT", path(workspace_id), ada, {"expected_version": 0, "inputs": everything()}, key=key
    )
    stale = api.write(
        "PUT",
        path(workspace_id),
        ada,
        {"expected_version": 0, "inputs": {**everything(), "reserve": gbp(1)}},
    )
    unchanged = api.write(
        "PUT", path(workspace_id), ada, {"expected_version": 1, "inputs": everything()}
    )

    assert (empty["version"], empty["created_by"]) == (0, None)
    assert empty["inputs"]["opening_cash"] is None
    assert written.status_code == 201, written.text
    assert stored["version"] == 1
    assert stored["created_by"] == ADA_ID
    decisions = stored["inputs"].pop("outcome_decisions")
    expected = everything()
    assert [
        {k: v for k, v in d.items() if k not in ("recorded_by", "recorded_at")} for d in decisions
    ] == expected.pop("outcome_decisions")
    assert decisions[0]["recorded_by"] == ADA_ID
    assert stored["inputs"] == {**expected, "schema_version": "1"}
    # The caps are the profile's answers, beside the inputs; what a solve needs is named.
    assert (stored["direct_spend_cap"], stored["monthly_payment_cap"]) == (gbp(150000), None)
    assert stored["needs"] == [
        {"input": "monthly_payment_cap", "effect": "leaves_every_route_unresolved"}
    ]
    assert (replayed.status_code, replayed.json()) == (201, written.json())
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_INPUT_VERSION"
    assert stale.json()["error"]["details"] == {"current_version": 1}
    assert (unchanged.status_code, unchanged.json()["version"]) == (200, 1)  # nothing new
    assert read(api, ada, workspace_id)["inputs"]["reserve"] == gbp(50000)  # survived the refusal
    # One status event for the one new version, carrying its number only.
    events = infra.query(
        "SELECT detail FROM careerwright.workspace_events WHERE workspace_id = %s AND kind = %s",
        (workspace_id, "planning.inputs_updated"),
    )
    assert [e["detail"] for e in events] == [{"version": 1}]


@pytest.mark.req("PLN-11", "API-05")
def test_nothing_stated_names_what_a_solve_needs_and_unknown_money_is_null(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace(api, ada)

    body = read(api, ada, workspace_id)

    assert body["version"] == 0
    assert (body["synthetic"], body["data_mode"]) == (True, "live_assisted")
    assert all(
        body["inputs"][name] is None
        for name in ("opening_cash", "living_costs", "reserve", "existing_debts", "work_rights")
    )
    blocks = [n["input"] for n in body["needs"] if n["effect"] == "blocks_a_solve"]
    assert blocks == [
        "objective_basis",
        "continuation",
        "opening_cash",
        "living_costs",
        "commitments",
        "existing_debts",
        "scenario_delay_months",
    ]


@pytest.mark.req("BND1-04", "BND1-05")
def test_work_rights_and_remote_working_are_never_read_from_a_city(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace(api, ada)  # the profile names Manchester

    body = read(api, ada, workspace_id)

    assert body["inputs"]["work_rights"] is None
    assert body["inputs"]["remote_work"] is None
    assert {"input": "work_rights", "effect": "leaves_every_route_unresolved"} in body["needs"]


@pytest.mark.req("PLN-11", "OUT1-03", "FUNDING-04")
@pytest.mark.parametrize(
    ("changes", "field", "reason"),
    [
        ({"variants": [{"variant_id": "offering:elsewhere"}]}, "variants", "not_an_option"),
        (
            {
                "variants": [
                    {
                        "variant_id": "offering:C04~pay-in-full",
                        "condition_statuses": {"eligibility_age": "confirmed"},
                    }
                ]
            },
            "condition_statuses",
            "not_a_condition",
        ),
        (
            {
                "variants": [
                    {
                        "variant_id": "offering:C01#full_time",
                        "supports": [
                            {
                                "instrument_id": "funding:F01",
                                "kind": "grant",  # the pack names F01 a fee waiver
                                "amount": gbp(1000),
                                "paid_to": "provider",
                                "eligibility": "confirmed",
                                "award": "approved",
                            }
                        ],
                    }
                ]
            },
            "supports",
            "not_its_kind",
        ),
        ({"admissions": ["offering:C04"]}, "admissions", "nothing_to_admit"),
        (
            {
                "outcome_decisions": [
                    {
                        "outcome_id": "outcome:C01.1",
                        "decision": "override",
                        "evidence_kind": "topic_mention",
                        "level_on_completion": 2,
                        "rubric_version": "rubric:constructed",
                        "reason": "it teaches enough",
                    }
                ]
            },
            "outcome_decisions",
            "override_not_supported",
        ),
    ],
)
def test_an_answer_must_fit_one_of_the_workspace_s_own_options(
    api: ApiClient, ada: str, changes: dict[str, Any], field: str, reason: str
) -> None:
    workspace_id = workspace(api, ada)

    refused = api.write("PUT", path(workspace_id), ada, {"expected_version": 0, "inputs": changes})

    assert refused.status_code == 422, refused.text
    error = refused.json()["error"]
    assert (error["code"], error["details"]) == (
        "VALIDATION_FAILED",
        {"field": field, "reason": reason},
    )
    assert read(api, ada, workspace_id)["version"] == 0  # nothing was stored


@pytest.mark.req("PLN-11", "FUNDING-04")
def test_a_loan_is_refused_as_support_before_anything_is_stored(api: ApiClient, ada: str) -> None:
    workspace_id = workspace(api, ada)
    loan = {
        "instrument_id": "funding:F02",
        "kind": "loan",
        "amount": gbp(1000),
        "paid_to": "person",
        "paid_month_offset": 0,
        "eligibility": "confirmed",
        "award": "approved",
    }

    answer = {"variant_id": "offering:C04~pay-in-full", "supports": [loan]}
    refused = api.write(
        "PUT",
        path(workspace_id),
        ada,
        {"expected_version": 0, "inputs": {"variants": [answer]}},
    )

    assert (refused.status_code, refused.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert read(api, ada, workspace_id)["version"] == 0


@pytest.mark.req("SEC-02", "PLN-11")
def test_another_person_sees_none_of_it_and_history_is_append_only(
    api: ApiClient, ada: str, ben: str, infra: Infra
) -> None:
    workspace_id = workspace(api, ada)
    written = api.write(
        "PUT", path(workspace_id), ada, {"expected_version": 0, "inputs": everything()}
    )
    assert written.status_code == 201, written.text

    seen = api.get(path(workspace_id), ben)
    wrote = api.write(
        "PUT", path(workspace_id), ben, {"expected_version": 1, "inputs": everything()}
    )

    assert (seen.status_code, seen.json()["error"]["code"]) == (404, "NOT_FOUND")
    assert wrote.status_code == 404
    count = "SELECT count(*) AS n FROM careerwright.planning_input_versions WHERE workspace_id = %s"
    assert int(str(infra.as_role("pg_api", count, (workspace_id,), actor=ADA_ID)[0]["n"])) == 1
    assert infra.as_role("pg_api", count, (workspace_id,), actor=BEN_ID)[0]["n"] == 0
    for statement in (
        "UPDATE careerwright.planning_input_versions SET document = '{}'::jsonb",
        "DELETE FROM careerwright.planning_input_versions",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            infra.as_role("pg_api", statement, actor=ADA_ID)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        infra.as_role(
            "pg_api",
            "INSERT INTO careerwright.planning_input_versions (workspace_id, version, "
            "schema_version, document, created_by) VALUES (%s, 9, '1', %s::jsonb, %s)",
            (workspace_id, json.dumps({"schema_version": "1"}), BEN_ID),
            actor=BEN_ID,
        )


@pytest.mark.req("PLN-11", "FUNDING-04", "BND1-05")
@pytest.mark.parametrize(
    "document",
    [
        {"opening_cash": {"minor_units": -1, "currency": "GBP"}},  # money never below zero
        {"weekly_availability": 169},  # more hours than a week holds
        {"scenario_delay_months": 25},
        {"work_rights": "probably"},
        {"remote_work": {"works_remotely": True, "employment_country": "US", "timezone": "x"}},
        {"variants": [{"variant_id": "v", "supports": [{"kind": "loan", "award": "applied"}]}]},
        {  # an approval needs confirmed eligibility
            "variants": [
                {
                    "variant_id": "v",
                    "supports": [
                        {
                            "kind": "grant",
                            "award": "approved",
                            "eligibility": "potentially_eligible",
                        }
                    ],
                }
            ]
        },
        {"outcome_decisions": [{"outcome_id": "o", "decision": "maybe"}]},
    ],
)
def test_the_database_repeats_the_domain_rules(
    api: ApiClient, ada: str, infra: Infra, document: dict[str, Any]
) -> None:
    workspace_id = workspace(api, ada)

    with pytest.raises(psycopg.errors.CheckViolation):
        infra.as_role(
            "pg_api",
            "INSERT INTO careerwright.planning_input_versions (workspace_id, version, "
            "schema_version, document, created_by) VALUES (%s, 1, '1', %s::jsonb, %s)",
            (workspace_id, json.dumps({"schema_version": "1", **document}), ADA_ID),
            actor=ADA_ID,
        )
