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

    # The export includes each saved profile version and a place for chosen plan versions.
    assert (export["format"], export["format_version"], export["synthetic"]) == (
        "careerwright.workspace-export",
        6,
        True,
    )
    assert [v["version"] for v in export["profile_versions"]] == [1, 2]
    assert len(export["sources"]) == 2
    assert [e["seq"] for e in export["events"]] == [1, 2, 3]
    assert (export["interview_turns"], export["provisional_concepts"]) == ([], [])
    assert export["discoveries"] == []
    assert export["interview_preferences"]["version"] == 0  # never chosen, not paused
    assert export["interview_preferences"]["paused"] is False
    assert export["plans"] == []
