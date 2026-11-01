"""Status events: commit-ordered sequence numbers and a stream that resumes from Last-Event-ID."""

import json
import time
import uuid
from typing import Any

import pytest

from careerwright.api import routes_events
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra, create_emulator_user, revoke_tokens, sign_in

pytestmark = pytest.mark.integration


def read_events(
    api: ApiClient, token: str, path: str, count: int, **headers: str
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with api.http.stream(
        "GET", path, headers={"Authorization": f"Bearer {token}", **headers}
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        frame: dict[str, str] = {}
        for line in response.iter_lines():
            if line == "":
                if "data" in frame:
                    events.append({"id": frame.get("id"), **json.loads(frame["data"])})
                    if len(events) == count:
                        break
                frame = {}
                continue
            name, _, value = line.partition(": ")
            frame[name] = value
    return events


@pytest.mark.req("DUR-03")
def test_stream_delivers_events_with_ids_and_resumes_after_last_event_id(
    api: ApiClient, ada: str
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    for version, city in enumerate(("Leeds", "York", "Hull")):
        api.write(
            "PUT",
            f"/v1/workspaces/{workspace_id}/profile",
            ada,
            {"expected_version": version, "profile": profile_with(cities=[city])},
        )
    stream = f"/v1/workspaces/{workspace_id}/events/stream"

    first = read_events(api, ada, stream, 4)
    resumed = read_events(api, ada, stream, 2, **{"Last-Event-ID": first[1]["id"]})

    assert [e["seq"] for e in first] == [1, 2, 3, 4]
    assert [e["id"] for e in first] == ["1", "2", "3", "4"]
    assert [e["kind"] for e in first] == ["workspace.created"] + ["profile.version_created"] * 3
    assert [e["seq"] for e in resumed] == [3, 4]
    assert first[3]["detail"] == {"version": 3, "changed_fields": "cities"}


@pytest.mark.req("DUR-03", "STATE-07")
def test_a_workspace_reports_its_last_event_so_a_reopened_page_resumes_there(
    api: ApiClient, ada: str
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        ada,
        {"expected_version": 0, "profile": profile_with(cities=["Leeds"])},
    )
    loaded = api.get(f"/v1/workspaces/{workspace_id}", ada).json()
    page = api.get(f"/v1/workspaces/{workspace_id}/events", ada).json()
    stream = f"/v1/workspaces/{workspace_id}/events/stream"
    api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        ada,
        {"expected_version": 1, "profile": profile_with(cities=["York"])},
    )

    resumed = read_events(api, ada, stream, 1, **{"Last-Event-ID": str(loaded["last_event_seq"])})

    assert loaded["last_event_seq"] == page["last_seq"] == 2
    assert [e["seq"] for e in resumed] == [3]  # only what happened after the page loaded


@pytest.mark.req("SEC-01")
def test_the_stream_ends_once_the_firebase_token_is_revoked(
    api: ApiClient, infra: Infra, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(routes_events, "REVERIFY_S", 0.3)
    monkeypatch.setattr(routes_events, "HEARTBEAT_S", 0.2)  # lines keep coming, so no hang
    uid = f"stream-{uuid.uuid4().hex[:8]}"
    email = f"{uid}@careerwright.test"
    create_emulator_user(uid, email, "password-123456")
    token = sign_in(email, "password-123456")
    infra.query(
        "INSERT INTO careerwright.actors (actor_id, email, display_name, access) "
        "VALUES (%s, %s, 'Streams until revoked', 'active')",
        (uuid.uuid4(), email),
    )
    workspace_id = api.create_workspace(token)["workspace_id"]
    deadline = time.monotonic() + 20
    lines: list[str] = []

    with api.http.stream(
        "GET",
        f"/v1/workspaces/{workspace_id}/events/stream",
        headers={"Authorization": f"Bearer {token}"},
    ) as response:
        for line in response.iter_lines():
            lines.append(line)
            if line.startswith("id: "):  # the workspace.created event: the stream is live
                revoke_tokens(uid)
            if lines[-2:-1] == ["event: stream_ended"] or time.monotonic() > deadline:
                break

    assert lines[-2:] == ["event: stream_ended", 'data: {"code": "UNAUTHENTICATED"}']


def test_event_page_and_bad_last_event_id(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]

    page = api.get(f"/v1/workspaces/{workspace_id}/events", ada, after=0).json()
    later = api.get(f"/v1/workspaces/{workspace_id}/events", ada, after=page["last_seq"]).json()
    bad = api.http.get(
        f"/v1/workspaces/{workspace_id}/events/stream",
        headers={"Authorization": f"Bearer {ada}", "Last-Event-ID": "abc"},
    )

    assert [e["kind"] for e in page["items"]] == ["workspace.created"]
    assert later == {"items": [], "last_seq": page["last_seq"]}
    assert (bad.status_code, bad.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
