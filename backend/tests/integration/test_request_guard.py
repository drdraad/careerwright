"""Loopback only (BND1-13): a non-local Host, or an unauthorised local Origin, cannot reach
the API or trigger authenticated changes, even with a valid token."""

import uuid

import pytest

from careerwright.seed import FIXTURE_WORKSPACE_ID
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra

pytestmark = pytest.mark.integration


@pytest.mark.req("BND1-13")
@pytest.mark.parametrize("host", ["evil.example:57000", "192.168.1.20:57000", "localhost:9999", ""])
def test_a_request_for_another_host_name_is_refused(api: ApiClient, ada: str, host: str) -> None:
    response = api.http.get("/v1/me", headers={"Host": host, "Authorization": f"Bearer {ada}"})

    assert (response.status_code, response.json()["error"]["code"]) == (400, "HOST_NOT_ALLOWED")
    assert response.headers["x-correlation-id"] == response.json()["error"]["correlation_id"]


@pytest.mark.req("BND1-13")
@pytest.mark.parametrize(
    "origin", ["http://127.0.0.1:8081", "http://localhost:3000", "https://evil.example", "null"]
)
def test_an_unauthorised_local_origin_cannot_change_anything(
    api: ApiClient, ada: str, infra: Infra, origin: str
) -> None:
    before = infra.query(
        "SELECT count(*) AS n FROM careerwright.profile_versions WHERE workspace_id = %s",
        (FIXTURE_WORKSPACE_ID,),
    )
    response = api.write(
        "PUT",
        f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}/profile",
        ada,
        {"expected_version": 1, "profile": profile_with(cities=["Origin attack"])},
        origin=origin,
    )

    assert (response.status_code, response.json()["error"]["code"]) == (403, "ORIGIN_NOT_ALLOWED")
    assert (
        infra.query(
            "SELECT count(*) AS n FROM careerwright.profile_versions WHERE workspace_id = %s",
            (FIXTURE_WORKSPACE_ID,),
        )
        == before
    )


@pytest.mark.req("BND1-13")
def test_a_state_changing_request_without_an_origin_is_refused(api: ApiClient, ada: str) -> None:
    response = api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "no origin", "data_mode": "live_assisted", "synthetic": True},
        origin=None,
    )

    assert (response.status_code, response.json()["error"]["code"]) == (403, "ORIGIN_NOT_ALLOWED")


def test_reads_from_a_foreign_origin_are_refused_too(api: ApiClient, ada: str) -> None:
    response = api.http.get(
        "/v1/workspaces",
        headers={"Authorization": f"Bearer {ada}", "Origin": "http://127.0.0.1:8081"},
    )

    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


def test_the_web_origin_is_accepted(api: ApiClient, ada: str) -> None:
    response = api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "ok", "data_mode": "live_assisted", "synthetic": True},
    )

    assert response.status_code == 201


@pytest.mark.req("SEC-04", "MODEL-06")
def test_validation_errors_never_echo_request_input(api: ApiClient, ada: str) -> None:
    secret_like = f"sk-should-never-echo-{uuid.uuid4().hex}"

    response = api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": secret_like * 10, "data_mode": "nope", "synthetic": 3},
    )

    body = response.json()
    assert (response.status_code, body["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert secret_like not in response.text
    assert "body.name: string_too_long" in body["error"]["details"]["errors"]


@pytest.mark.req("SEC-04", "MODEL-06")
def test_validation_errors_never_echo_client_supplied_field_names(api: ApiClient, ada: str) -> None:
    secret_like = f"sk-pasted-as-a-key-{uuid.uuid4().hex}"

    response = api.write(
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "ok", "data_mode": "live_assisted", "synthetic": True, secret_like: "x"},
    )

    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert secret_like not in response.text
    assert (
        "body.<unexpected field>: extra_forbidden" in response.json()["error"]["details"]["errors"]
    )
