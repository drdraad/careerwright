"""A thin test client: the real FastAPI app over TestClient, with Nessa's request headers."""

import uuid
from typing import Any

import httpx2 as httpx
from fastapi.testclient import TestClient

from tests.support.infra import WEB_ORIGIN


class ApiClient:
    def __init__(self, client: TestClient) -> None:
        self.http = client

    def _headers(
        self, token: str | None, *, key: uuid.UUID | None, origin: str | None
    ) -> dict[str, str]:
        headers: dict[str, str] = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if key is not None:
            headers["Idempotency-Key"] = str(key)
        if origin is not None:
            headers["Origin"] = origin
        return headers

    def get(self, path: str, token: str | None, **params: Any) -> httpx.Response:
        return self.http.get(
            path, headers=self._headers(token, key=None, origin=None), params=params
        )

    def write(
        self,
        method: str,
        path: str,
        token: str | None,
        body: Any = None,
        *,
        key: uuid.UUID | None = None,
        origin: str | None = WEB_ORIGIN,
    ) -> httpx.Response:
        return self.http.request(
            method,
            path,
            json=body,
            headers=self._headers(token, key=key or uuid.uuid4(), origin=origin),
        )

    def create_workspace(
        self, token: str, name: str = "Test workspace", *, synthetic: bool = True
    ) -> dict[str, Any]:
        response = self.write(
            "POST",
            "/v1/workspaces",
            token,
            {"name": name, "data_mode": "live_assisted", "synthetic": synthetic},
        )
        assert response.status_code == 201, response.text
        body: dict[str, Any] = response.json()
        return body


def unasked_profile() -> dict[str, dict[str, Any]]:
    return {
        name: {"state": "unasked"}
        for name in (
            "preferred_name",
            "current_role",
            "cities",
            "target_titles",
            "weekly_study_hours",
            "direct_spend_cap",
            "monthly_payment_cap",
            "enjoyed_tasks",
            "confident_tasks",
            "evidenced_tasks",
            "work_style",
            "minimum_salary",
        )
    }


def profile_with(**fields: Any) -> dict[str, dict[str, Any]]:
    profile = unasked_profile()
    for name, value in fields.items():
        profile[name] = {"state": "provided", "value": value}
    return profile
