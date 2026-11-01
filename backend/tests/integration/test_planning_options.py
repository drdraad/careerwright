"""The planning catalogue over the API against real PostgreSQL 16 (S5.1, S5.2; ADR 0013): each
target's options from the option pack, concepts apart from dated offerings, every field
cited or unknown with its reason, every record labelled with its review state and the pack's
date; another person sees nothing."""

from typing import Any

import pytest

from tests.support.client import ApiClient, profile_with

pytestmark = pytest.mark.integration

DATA = "Data quality analyst"
UNMATCHED = "Lighthouse keeper"


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


def options(api: ApiClient, token: str, workspace_id: str) -> dict[str, Any]:
    response = api.get(f"/v1/workspaces/{workspace_id}/planning/options", token)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


@pytest.mark.req("OPTN-01", "OPTN-08", "OPTN-09")
def test_each_target_s_pack_options_are_served_with_their_labels(api: ApiClient, ada: str) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA, UNMATCHED)

    body = options(api, ada, workspace_id)

    assert (body["synthetic"], body["data_mode"]) == (True, "live_assisted")
    assert body["pack"]["pack_version"] == "0.4.0"  # the reviewed school-leaver pack (Task 12b)
    assert body["pack"]["dated"] == "2026-11-01"
    data, unmatched = body["targets"]
    assert data["target_title"] == DATA
    assert data["pack_target_id"] == "data-quality-analyst-manchester"
    catalogue = data["catalogue"]
    assert catalogue["label"] == {
        "name": "nessa-england-option-pack 0.4.0",
        "dated": "2026-11-01",
        "synthetic": False,
    }
    assert sorted(c["concept_id"] for c in catalogue["concepts"]) == ["option:C01", "option:C04"]
    assert {o["review_state"] for o in catalogue["offerings"]} == {"proposed"}
    c04 = next(o for o in catalogue["offerings"] if o["offering_id"] == "offering:C04")
    fee = next(f for f in c04["facts"] if f["field"] == "fee_total")
    assert fee["value"] == {"currency": "GBP", "minor_units": 299500}
    assert fee["cited"]["claim_id"] == "C04.fee_total"
    [whole] = c04["payment_plans"][0]["payments"]
    assert whole["amount"] == {"currency": "GBP", "minor_units": 299500}  # Money, never bare
    assert c04["start"] is None  # unknown, never a default
    assert c04["unknown"]["start"] == "not stated on the page"
    # A target the pack does not cover has no options, and says so rather than empty success.
    assert unmatched == {
        "target_title": UNMATCHED,
        "pack_target_id": None,
        "catalogue": None,
        "note": "no_pack_target",
    }


def test_another_person_sees_none_of_it(api: ApiClient, ada: str, ben: str) -> None:
    workspace_id = workspace_with_targets(api, ada, DATA)

    response = api.get(f"/v1/workspaces/{workspace_id}/planning/options", ben)

    assert (response.status_code, response.json()["error"]["code"]) == (404, "NOT_FOUND")
