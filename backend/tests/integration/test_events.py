"""Status events: commit-ordered sequence numbers and a stream that resumes from Last-Event-ID."""

import json
from typing import Any

import pytest

from tests.support.client import ApiClient, profile_with

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
