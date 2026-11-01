"""Optional seniority and industry beside a role or a target title, and the skills ESCO lists
for a role that the person marks "not part of my job" (Task 6d slice C; ADR 0015 decisions 3
and 4; ADR 0012 as amended): kept per title as a concept, never a default, ignored by
matching, never evidence. End to end against real PostgreSQL 16 and the labelled ESCO sample.
No model is called."""

import uuid
from typing import Any

import pytest

from careerwright.profile import safety
from tests.integration.test_interview_choices import DISTRESS
from tests.integration.test_origin import choose_role, occupation, origin
from tests.integration.test_role_space import closest, name_role
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra

pytestmark = pytest.mark.integration


def details(api: ApiClient, token: str, workspace: str) -> dict[str, Any]:
    found = api.get(f"/v1/workspaces/{workspace}/profile/titles", token)
    assert found.status_code == 200, found.text
    body: dict[str, Any] = found.json()
    return body


def put_details(
    api: ApiClient,
    token: str,
    workspace: str,
    title_use: str,
    title: str,
    version: int,
    **more: Any,
) -> Any:
    return api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile/titles",
        token,
        {
            "expected_version": version,
            "title_use": title_use,
            "title": title,
            "seniority": None,
            "industry": None,
            "not_part_of_job": [],
            **more,
        },
    )


def edit(api: ApiClient, token: str, workspace: str, version: int, **answers: Any) -> None:
    put = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile",
        token,
        {"expected_version": version, "profile": profile_with(**answers)},
    )
    assert put.status_code == 201, put.text


def shown(body: dict[str, Any]) -> list[tuple[str, str, str | None, str | None, int]]:
    return [
        (t["title_use"], t["title"], t["seniority"], t["industry"], t["version"])
        for t in body["titles"]
    ]


@pytest.mark.req("PROF-11", "PROF-08", "VERSIONS-01")
def test_seniority_and_industry_are_kept_beside_each_title_and_matching_ignores_them(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Seniority and industry (synthetic)")["workspace_id"]
    empty = details(api, ada, workspace)
    choose_role(api, ada, workspace, occupation(api, ada, "bookkeeper"), 0)
    edit(api, ada, workspace, 1, current_role="bookkeeper", target_titles=["Doula"])
    before = origin(api, ada, workspace)
    unknown = details(api, ada, workspace)

    saved = put_details(api, ada, workspace, "role", "Bookkeeper", 0, seniority="Senior")
    again = put_details(api, ada, workspace, "role", "bookkeeper", 1, seniority="Senior")
    stale = put_details(api, ada, workspace, "role", "bookkeeper", 0, industry="Retail")
    target = put_details(api, ada, workspace, "target", "doula", 0, industry="Maternity care")
    after = origin(api, ada, workspace)

    # Nothing before a title is given; then each title is shown with nothing known: shadow,
    # never a default.
    assert empty["titles"] == []
    assert shown(unknown) == [
        ("role", "bookkeeper", None, None, 0),
        ("target", "Doula", None, None, 0),
    ]
    assert saved.status_code == 201, saved.text
    assert (saved.json()["seniority"], saved.json()["industry"], saved.json()["version"]) == (
        "Senior",
        None,
        1,
    )
    assert saved.json()["support_note"] is None
    assert (again.status_code, again.json()["version"]) == (200, 1)  # nothing changed
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_INPUT_VERSION")
    assert target.status_code == 201, target.text
    # Kept in the person's words, each beside its own title, in the profile's spelling.
    assert shown(details(api, ada, workspace)) == [
        ("role", "bookkeeper", "Senior", None, 1),
        ("target", "Doula", None, "Maternity care", 1),
    ]
    # Matching ignores them: the role names the same occupation and joins the same work.
    assert after["role"] == before["role"]
    assert after["destinations"] == before["destinations"]


@pytest.mark.req("PROF-11")
def test_a_title_s_details_are_kept_per_title_and_only_for_the_person_s_own_titles(
    api: ApiClient, ada: str
) -> None:
    workspace = api.create_workspace(ada, "Kept per title (synthetic)")["workspace_id"]
    edit(api, ada, workspace, 0, current_role="Bookkeeper")
    put_details(api, ada, workspace, "role", "Bookkeeper", 0, seniority="Trainee")
    edit(api, ada, workspace, 1, current_role="Doula")
    away = details(api, ada, workspace)
    edit(api, ada, workspace, 2, current_role="bookkeepers")
    back = details(api, ada, workspace)

    not_mine = put_details(api, ada, workspace, "role", "Doula", 0, seniority="Senior")
    not_a_target = put_details(api, ada, workspace, "target", "bookkeeper", 0, seniority="Senior")

    assert shown(away) == [("role", "Doula", None, None, 0)]
    # The same title as a concept, so its details are back with it.
    assert shown(back) == [("role", "bookkeepers", "Trainee", None, 1)]
    for refused in (not_mine, not_a_target):
        assert refused.status_code == 422, refused.text
        assert refused.json()["error"]["details"]["reason"] == "not_your_title"


@pytest.mark.req("PROF-11")
def test_a_title_of_punctuation_alone_takes_no_details_and_a_save_for_it_is_refused(
    api: ApiClient, ada: str
) -> None:
    # Fix round 1: no letters or digits gives no concept key; this save was a 500 before.
    workspace = api.create_workspace(ada, "Punctuation title (synthetic)")["workspace_id"]
    edit(api, ada, workspace, 0, current_role="-", target_titles=["Doula"])

    listed = details(api, ada, workspace)
    refused = put_details(api, ada, workspace, "role", "-", 0, seniority="Senior")

    assert shown(listed) == [("target", "Doula", None, None, 0)]
    assert refused.status_code == 422, refused.text
    assert refused.json()["error"]["code"] == "VALIDATION_FAILED"
    assert refused.json()["error"]["details"]["reason"] == "not_your_title"


@pytest.mark.req("PROF-11", "ASSESS-01")
def test_a_skill_marked_not_part_of_my_job_is_a_display_state_never_evidence(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace = api.create_workspace(ada, "Not part of my job (synthetic)")["workspace_id"]
    choose_role(api, ada, workspace, occupation(api, ada, "bookkeeper"), 0)
    first = origin(api, ada, workspace)
    skill = first["usual_skills"][0]["skill_id"]
    other = str(uuid.uuid4())  # no skill ESCO lists for this kind of work

    marked = put_details(api, ada, workspace, "role", "bookkeeper", 0, not_part_of_job=[skill])
    shown_after = origin(api, ada, workspace)
    unlisted = put_details(api, ada, workspace, "role", "bookkeeper", 1, not_part_of_job=[other])
    unmarked = put_details(api, ada, workspace, "role", "bookkeeper", 1, not_part_of_job=[])

    assert marked.status_code == 201, marked.text
    assert marked.json()["not_part_of_job"] == [skill]
    flags = {u["skill_id"]: (u["state"], u["not_part_of_job"]) for u in shown_after["usual_skills"]}
    # Still ESCO's list, now marked: a display state, never the person's claim or evidence.
    assert flags[skill] == ("usual_in_role", True)
    assert all(not marked for s, (_, marked) in flags.items() if s != skill)
    assert shown_after["destinations"] == first["destinations"]
    assert infra.query(
        "SELECT count(*) AS n FROM careerwright.skill_evidence WHERE workspace_id = %s",
        (workspace,),
    ) == [{"n": 0}]
    assert shown_after["capability_version"] == first["capability_version"]
    assert unlisted.status_code == 422, unlisted.text
    assert unlisted.json()["error"]["details"]["reason"] == "not_listed"
    assert unmarked.status_code == 201, unmarked.text
    assert all(not u["not_part_of_job"] for u in origin(api, ada, workspace)["usual_skills"])


@pytest.mark.req("PROF-11", "MAP1-09")
def test_a_mark_kept_from_an_earlier_closest_choice_never_blocks_a_later_save(
    api: ApiClient, ada: str
) -> None:
    # Self-review: a role whose closest occupation the person later let go ("None of these is
    # my job") lists no skills; the marks made before are kept, and saving its seniority must
    # still work. Only a newly marked skill is checked against what ESCO lists.
    workspace = api.create_workspace(ada, "Marks kept (synthetic)")["workspace_id"]
    assert name_role(api, ada, workspace, "Registered nurse", 0).status_code == 201
    [group] = origin(api, ada, workspace)["role"]["closest"]["groups"]
    specialist = next(o["concept_id"] for o in group["occupations"] if "specialist" in o["title"])
    assert closest(api, ada, workspace, specialist, 1).status_code == 201
    skill = origin(api, ada, workspace)["usual_skills"][0]["skill_id"]
    marked = put_details(
        api, ada, workspace, "role", "Registered nurse", 0, not_part_of_job=[skill]
    )
    assert marked.status_code == 201, marked.text
    assert closest(api, ada, workspace, None, 2).status_code == 201

    later = put_details(
        api,
        ada,
        workspace,
        "role",
        "Registered nurse",
        1,
        seniority="Band 6",
        not_part_of_job=[skill],
    )
    added = put_details(
        api,
        ada,
        workspace,
        "role",
        "Registered nurse",
        2,
        seniority="Band 6",
        not_part_of_job=[skill, str(uuid.uuid4())],
    )

    assert later.status_code == 201, later.text
    assert (later.json()["seniority"], later.json()["not_part_of_job"]) == ("Band 6", [skill])
    assert added.status_code == 422, added.text
    assert added.json()["error"]["details"]["reason"] == "not_listed"


@pytest.mark.req("PROF-09", "PROF-11")
def test_seniority_and_industry_go_through_the_support_screen_and_nothing_of_it_is_kept(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # The product owner's "every place a person types" (31 October 2026). The input is the
    # existing risk-word fixture.
    workspace = api.create_workspace(ada, "Screened details (synthetic)")["workspace_id"]
    edit(api, ada, workspace, 0, current_role="Doula")

    saved = put_details(api, ada, workspace, "role", "Doula", 0, industry=DISTRESS)
    replay_key = uuid.uuid4()
    first = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile/titles",
        ada,
        {
            "expected_version": 1,
            "title_use": "role",
            "title": "Doula",
            "seniority": "Senior",
            "industry": DISTRESS,
            "not_part_of_job": [],
        },
        key=replay_key,
    )
    replay = api.write(
        "PUT",
        f"/v1/workspaces/{workspace}/profile/titles",
        ada,
        {
            "expected_version": 1,
            "title_use": "role",
            "title": "Doula",
            "seniority": "Senior",
            "industry": DISTRESS,
            "not_part_of_job": [],
        },
        key=replay_key,
    )
    stale = put_details(api, ada, workspace, "role", "Doula", 0, seniority=DISTRESS)

    # Saved as usual, as the person typed it, with the calm panel beside the answer.
    assert saved.status_code == 201, saved.text
    assert saved.json()["industry"] == DISTRESS
    assert saved.json()["support_note"]["message"] == safety.SUPPORT_NOTE_ENTRY
    # Words saved before don't bring the panel back; a replay derives the same answer again.
    assert first.status_code == 201, first.text
    assert first.json()["support_note"] is None
    assert (replay.status_code, replay.json()) == (201, first.json())
    # A refusal of a screened entry carries the panel too.
    assert stale.status_code == 409, stale.text
    assert stale.json()["support_note"]["message"] == safety.SUPPORT_NOTE_ENTRY_NOT_SAVED
    receipts = infra.query(
        "SELECT response FROM careerwright.command_receipts WHERE workspace_id = %s",
        (workspace,),
    )
    assert receipts
    assert all("support" not in str(r["response"]) for r in receipts)
