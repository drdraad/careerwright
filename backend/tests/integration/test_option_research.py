"""Option research preflight uses the migrated workspace tables and actor-scoped API."""

import pytest

from tests.support.client import ApiClient
from tests.support.infra import Infra

pytestmark = pytest.mark.integration


@pytest.mark.req("OPTN-12", "API-06")
def test_option_research_preflight_is_migrated_and_workspace_private(
    infra: Infra, api: ApiClient, ada: str, ben: str
) -> None:
    tables = infra.query(
        "SELECT to_regclass('careerwright.option_researches')::text AS researches, "
        "to_regclass('careerwright.researched_option_records')::text AS records"
    )[0]
    assert tables == {
        "researches": "careerwright.option_researches",
        "records": "careerwright.researched_option_records",
    }
    assert infra.query(
        "SELECT conname FROM pg_constraint WHERE conrelid = "
        "'careerwright.researched_option_records'::regclass AND contype = 'u' "
        "AND conname = 'researched_option_record_slot'"
    ) == [{"conname": "researched_option_record_slot"}]

    workspace = api.create_workspace(ada, "Option research preflight")["workspace_id"]
    path = f"/v1/workspaces/{workspace}/option-research"
    estimate = api.get(f"{path}/estimate", ada)
    assert estimate.status_code == 200, estimate.text
    cost = estimate.json()
    assert cost["search_maximum_nano_usd"] > 0
    assert cost["pages_maximum_nano_usd"] > 0
    assert cost["combined_maximum_nano_usd"] == (
        cost["search_maximum_nano_usd"] + cost["pages_maximum_nano_usd"]
    )
    assert api.get(path, ada).json() == []
    assert api.get(f"{path}/estimate", ben).status_code == 404
    assert api.get(f"{path}/estimate", None).status_code == 401
