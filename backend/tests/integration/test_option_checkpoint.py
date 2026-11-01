"""The Options chapter's review checkpoint over the API against real PostgreSQL 16 (Task 12b,
backend half; S5.3, S5.7): for each option the facts the route search lacks, named; the
person's own figures through the planning inputs' command (an expected version and an
Idempotency-Key), filling only what is missing; an option the person adds from pasted text,
round-tripping as their own `proposed` record with its source; a target outside the pack;
and another person sees none of it. The person and their figures are synthetic."""

from typing import Any

import pytest

from tests.support.client import ApiClient, profile_with

pytestmark = pytest.mark.integration

DATA = "Data quality analyst"
UNMATCHED = "Lighthouse keeper"
FULL_TIME = "offering:C01#full_time"
PAGE = "Evening data course 🎓 Bright College. Starts 4 January 2027, £450 in full."


def gbp(minor: int) -> dict[str, Any]:
    return {"minor_units": minor, "currency": "GBP"}


def workspace(api: ApiClient, token: str, *targets: str, **profile: Any) -> str:
    workspace_id = str(api.create_workspace(token)["workspace_id"])
    response = api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        token,
        {
            "expected_version": 0,
            "profile": profile_with(
                cities=["Manchester"], target_titles=list(targets or [DATA]), **profile
            ),
        },
    )
    assert response.status_code == 201, response.text
    return workspace_id


def base(workspace_id: str) -> str:
    return f"/v1/workspaces/{workspace_id}/planning"


def checkpoint(api: ApiClient, token: str, workspace_id: str) -> dict[str, Any]:
    response = api.get(f"{base(workspace_id)}/checkpoint", token)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def write(
    api: ApiClient, token: str, workspace_id: str, version: int, inputs: dict[str, Any]
) -> Any:
    return api.write(
        "PUT",
        f"{base(workspace_id)}/inputs",
        token,
        {"expected_version": version, "inputs": inputs},
    )


def option(body: dict[str, Any], title: str, variant_id: str) -> dict[str, Any]:
    target = next(t for t in body["targets"] if t["target_title"] == title)
    found: dict[str, Any] = next(o for o in target["options"] if o["variant_id"] == variant_id)
    return found


@pytest.mark.req("OPTN-13", "OPTN-11", "OPTN-15", "API-06")
def test_the_checkpoint_names_each_option_s_missing_facts_and_the_person_s_figures_fill_them(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace(
        api,
        ada,
        monthly_payment_cap=gbp(150000),
        work_status="in_education_or_training",
        qualifications=[{"name": "GCSE maths", "status": "expected"}],
    )

    before = checkpoint(api, ada, workspace_id)
    figures = {
        "offering_id": FULL_TIME,
        "start": {"on": "2027-01-04", "basis": "own_figure"},
        "weekly_hours": 9,
        "cost": gbp(0),
    }
    written = write(
        api,
        ada,
        workspace_id,
        0,
        {
            "continuation": {"hours_per_week": 0, "net_income": gbp(0)},
            "baseline": {"kind": "staying_in_education", "net_income": gbp(0)},
            "offering_figures": [figures],
        },
    )
    after = checkpoint(api, ada, workspace_id)

    assert before["inputs_version"] == 0
    assert (before["pack"]["pack_version"], before["pack"]["dated"]) == ("0.4.0", "2026-11-01")
    assert before["payment_cap_basis"] == "payments_and_debt_repayments"  # session 2, D15
    assert before["monthly_payment_cap"] == gbp(150000)
    assert before["work_status"] == "in_education_or_training"
    assert (before["continuation"], before["not_working"]) == (None, None)  # not stated
    assert option(before, DATA, FULL_TIME)["missing"] == ["start_date", "weekly_hours", "cost"]
    assert option(before, DATA, FULL_TIME)["supplied"] == []
    [target] = before["targets"]
    assert target["reviewed_options"] == 0  # C01 and C04 are proposed
    assert target["scope"]["code"] is None
    assert all(r["applied"] is False for s in target["schemes"] for r in s["age_rules"])
    assert written.status_code == 201, written.text
    assert after["inputs_version"] == 1
    assert after["not_working"] is True  # "not working: 0 hours, £0", the person's own figures
    assert after["baseline"]["kind"] == "staying_in_education"
    c01 = option(after, DATA, FULL_TIME)
    assert c01["supplied"] == ["start_date", "weekly_hours", "cost"]
    # The cost is known now, so its fee's eligibility conditions are what is left to confirm.
    assert c01["missing"] == ["eligibility_confirmation"]
    assert [c["status"] for c in c01["eligibility_conditions"]] == [None] * 4


@pytest.mark.req("OPTN-13")
def test_a_figure_for_a_fact_the_page_states_or_an_option_not_theirs_is_refused(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace(api, ada, "IT support technician")

    stated = write(
        api,
        ada,
        workspace_id,
        0,
        {
            "offering_figures": [
                {
                    "offering_id": "offering:C07",
                    "start": {"on": "2027-02-01", "basis": "own_figure"},
                }
            ]
        },
    )
    unknown = write(
        api,
        ada,
        workspace_id,
        0,
        {"offering_figures": [{"offering_id": "offering:C01#full_time", "weekly_hours": 3}]},
    )
    left_out = write(api, ada, workspace_id, 0, {"excluded_variants": ["offering:nowhere"]})

    for response, field, reason in (
        (stated, "offering_figures", "not_missing"),
        (unknown, "offering_figures", "not_an_option"),  # not one of this target's options
        (left_out, "excluded_variants", "not_an_option"),
    ):
        assert response.status_code == 422, response.text
        assert response.json()["error"]["details"] == {"field": field, "reason": reason}


@pytest.mark.req("OPTN-03", "OPTN-08", "OPTN-09", "BND1-07", "API-06")
def test_an_added_option_round_trips_as_the_person_s_proposed_record_with_its_source(
    api: ApiClient, ada: str, ben: str
) -> None:
    workspace_id = workspace(api, ada, DATA, UNMATCHED)
    pasted = api.write(
        "POST",
        f"{base(workspace_id)}/option-texts",
        ada,
        {"text": PAGE, "source_url": "https://college.example.ac.uk/evening-data"},
    )
    assert pasted.status_code == 201, pasted.text
    text_id = pasted.json()["text_id"]
    assert set(pasted.json()) == {"text_id", "sha256"}  # the words are read back, not echoed
    kept = api.get(f"{base(workspace_id)}/option-texts/{text_id}", ada).json()
    added = {
        "option_id": "evening-course",
        "target": UNMATCHED,
        "text_id": text_id,
        "title": {"span": {"start": 0, "end": 19}},
        "provider": {"span": {"start": 23, "end": 37}},
        "start": "2027-01-04",
        "finish": "2027-03-26",
        "weekly_hours": 6,
        "cost": gbp(45000),
        "cited": {"cost": {"start": 62, "end": 66}},
    }

    written = write(api, ada, workspace_id, 0, {"own_options": [added]})
    options = api.get(f"{base(workspace_id)}/options", ada).json()
    found = checkpoint(api, ada, workspace_id)
    stored = api.get(f"{base(workspace_id)}/inputs", ada).json()["inputs"]["own_options"]

    assert kept["text"] == PAGE
    assert kept["source_url"] == "https://college.example.ac.uk/evening-data"
    assert written.status_code == 201, written.text
    [own] = stored
    assert own["recorded_at"]
    assert own["recorded_by"]
    unmatched = next(t for t in options["targets"] if t["target_title"] == UNMATCHED)
    assert unmatched["note"] == "no_pack_target"  # still outside the pack
    catalogue = unmatched["catalogue"]
    assert catalogue["label"]["name"] == "own options"
    [concept] = catalogue["concepts"]
    assert (concept["title"], concept["provider"]) == ("Evening data course", "Bright College")
    assert concept["review_state"] == "proposed"
    assert concept["added_by_person"] is True
    assert concept["cited"]["source_id"] == text_id
    [offering] = catalogue["offerings"]
    assert offering["review_state"] == "proposed"
    assert offering["payment_plans"][0]["payments"][0]["cited"]["excerpt"] == "£450"
    mine = option(found, UNMATCHED, "own:evening-course")
    assert mine["added_by_person"] is True
    assert mine["missing"] == []
    assert mine["review_states"] == ["proposed", "proposed"]
    # Another person reads neither the text nor the checkpoint.
    assert api.get(f"{base(workspace_id)}/option-texts/{text_id}", ben).status_code == 404
    assert api.get(f"{base(workspace_id)}/checkpoint", ben).status_code == 404


@pytest.mark.req("OPTN-03")
def test_an_added_option_must_be_for_a_target_and_its_spans_in_its_text(
    api: ApiClient, ada: str
) -> None:
    workspace_id = workspace(api, ada)
    other = workspace(api, ada)
    text_id = api.write("POST", f"{base(workspace_id)}/option-texts", ada, {"text": PAGE}).json()[
        "text_id"
    ]
    elsewhere = api.write("POST", f"{base(other)}/option-texts", ada, {"text": PAGE}).json()[
        "text_id"
    ]

    def added(**changes: Any) -> dict[str, Any]:
        return {
            "option_id": "evening-course",
            "target": DATA,
            "text_id": text_id,
            "title": {"span": {"start": 0, "end": 19}},
            **changes,
        }

    for changes, reason in (
        ({"target": "Astronaut"}, "not_a_target"),
        ({"title": {"span": {"start": 0, "end": 21}}}, "span_splits_character"),
        ({"text_id": elsewhere}, "text_not_found"),  # another workspace's text
    ):
        refused = write(api, ada, workspace_id, 0, {"own_options": [added(**changes)]})
        assert refused.status_code == 422, refused.text
        assert refused.json()["error"]["details"] == {"field": "own_options", "reason": reason}
