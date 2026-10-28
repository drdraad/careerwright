"""Workspace export: complete, labelled, and limited to the owner's own records."""

import pytest

from tests.support.client import ApiClient, profile_with

pytestmark = pytest.mark.integration


def test_export_holds_every_version_source_and_event_with_its_synthetic_label(
    api: ApiClient, ada: str
) -> None:
    workspace_id = api.create_workspace(ada, "Exported")["workspace_id"]
    for version, city in enumerate(("Leeds", "York")):
        api.write(
            "PUT",
            f"/v1/workspaces/{workspace_id}/profile",
            ada,
            {"expected_version": version, "profile": profile_with(cities=[city])},
        )

    export = api.get(f"/v1/workspaces/{workspace_id}/export", ada).json()

    # Format 2 (Task 5) adds the interview turns and provisional concepts; format 3 (Task 6)
    # the discoveries and the interview preferences.
    assert (export["format"], export["format_version"], export["synthetic"]) == (
        "nessa.workspace-export",
        3,
        True,
    )
    assert [v["version"] for v in export["profile_versions"]] == [1, 2]
    assert len(export["sources"]) == 2
    assert [e["seq"] for e in export["events"]] == [1, 2, 3]
    assert (export["interview_turns"], export["provisional_concepts"]) == ([], [])
    assert export["discoveries"] == []
    assert export["interview_preferences"]["version"] == 0  # never chosen, not paused
    assert export["interview_preferences"]["paused"] is False
