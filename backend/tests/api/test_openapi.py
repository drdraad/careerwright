"""The OpenAPI contract the web app's TypeScript client is generated from (ARC1-10, GC10).

The client is generated offline from `tools.openapi`, so the offline document must be exactly
what the running API serves, and the committed copy beside the client must be current.
"""

import json
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from careerwright.api.app import create_app, openapi_document
from careerwright.api.deps import ApiDependencies
from careerwright.config import ApiSettings
from careerwright.identity.keyring import KEY_BYTES, Keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.profile.document import FIELD_SPECS, FieldKind
from tests.api.test_guard_and_envelope import ENV, HOST, RefusingVerifier
from tools.openapi import render

COMMITTED = (
    Path(__file__).resolve().parents[3] / "apps" / "web" / "src" / "generated" / "openapi.json"
)


@pytest.mark.req("ARC1-10")
def test_the_served_schema_is_the_offline_document(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    app = create_app(
        ApiDependencies(
            settings=ApiSettings(_env_file=None),
            engine=sa.create_engine("postgresql+psycopg://nobody@127.0.0.1:1/none"),
            verifier=RefusingVerifier(),
            keyring=Keyring({1: os.urandom(KEY_BYTES)}, current_version=1),
            models=ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test"),
        )
    )
    with TestClient(app, base_url=f"http://{HOST}", client=("127.0.0.1", 50001)) as client:
        served = client.get("/openapi.json").json()

    assert served == openapi_document()


@pytest.mark.req("ARC1-10")
def test_the_committed_client_document_is_current() -> None:
    assert COMMITTED.read_text(encoding="utf-8") == render(), (
        "apps/web/src/generated/openapi.json is stale: run `pnpm run generate` in apps/web"
    )


@pytest.mark.req("ARC1-10")
def test_every_operation_has_a_named_unique_id() -> None:
    ids = [
        operation["operationId"]
        for path in openapi_document()["paths"].values()
        for operation in path.values()
    ]

    assert len(ids) == len(set(ids))
    assert all("_v1_" not in operation for operation in ids), ids  # names, not generated paths
    assert json.loads(render())["info"]["title"] == "Careerwright local API"


@pytest.mark.req("ARC1-10")
def test_the_profile_input_publishes_every_list_bound_the_server_checks() -> None:
    schemas = openapi_document()["components"]["schemas"]

    published = {}
    for name, prop in schemas["ProfileInput"]["properties"].items():
        field = schemas[prop["$ref"].rsplit("/", 1)[-1]]
        arrays = [s for s in field["properties"]["value"]["anyOf"] if s.get("type") == "array"]
        if arrays:
            published[name] = arrays[0].get("maxItems")

    # The web reads these from the generated client instead of restating them.
    assert published == {
        name: spec.max_items
        for name, spec in FIELD_SPECS.items()
        if spec.kind in (FieldKind.LIST, FieldKind.QUALIFICATIONS)  # Task 6f: a list too
    }


@pytest.mark.req("PROF-09")
def test_a_workspace_s_name_is_answered_with_the_support_panel_beside_it() -> None:
    # Task 6d slice C fix round 1: the name is typed, so it is screened as What we know's
    # entries are; the panel comes with the saved workspace and with a refusal.
    document = openapi_document()
    schemas = document["components"]["schemas"]
    for path, method in (("/v1/workspaces", "post"), ("/v1/workspaces/{workspace_id}", "patch")):
        responses = document["paths"][path][method]["responses"]
        saved = next(r for code, r in responses.items() if code in {"200", "201"})
        refused = responses["4XX"]
        for answer in (saved, refused):
            name = answer["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[-1]
            assert "support_note" in schemas[name]["properties"], (path, name)
