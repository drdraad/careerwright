"""The first answer on the full pinned ESCO release (plan section 4, "The first ten seconds";
Sprint W SW.5): the type-ahead, the answer saved, and the world's response (the role's usual
skills, the first destinations joined by shared essential skills),
each through the real API against real PostgreSQL 16, with no model call, timed against the
one-second budget, for "data analyst" and the heaviest roles ESCO holds; and the type-ahead
for titles ESCO does not list. The timings are printed with the run (`-s`); the database
runs in the test stack's container on this machine."""

import re
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from careerwright.api.app import create_app
from careerwright.api.deps import ApiDependencies
from careerwright.catalogue.esco import ESCO_RELEASE
from careerwright.catalogue.reference import DATASETS
from careerwright.cli import import_reference_data, import_taxonomy, migrate_app, seed
from careerwright.db import create_engine
from careerwright.identity.firebase import FirebaseTokenVerifier
from careerwright.identity.keyring import load_keyring
from careerwright.identity.model_choice import ModelChoice
from tests.support.client import ApiClient
from tests.support.infra import API_BASE, Infra, migrator_engine
from tools.datasets import DATASETS_DIR

pytestmark = pytest.mark.integration

BUDGET_S = 1.0  # plan section 4: the first answer changes the world within one second
UK_INDEX = next(dataset for dataset in DATASETS if dataset.name == "soc_index")


@pytest.fixture(scope="module")
def full_api(infra: Infra) -> Iterator[ApiClient]:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    database = f"careerwright_first_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    migrate_app(owner)
    assert import_taxonomy(owner, release) == "imported"
    # The pinned UK job-title index (ONS's SOC 2020 coding index), then the seed, as setup
    # does: the type-ahead offers its titles, and every title's record says whether it lists
    # it.
    index = Path(DATASETS_DIR) / UK_INDEX.pin.file_name
    assert import_reference_data(owner, [(UK_INDEX, index)]) == {"soc_index": "imported"}
    seed(owner, infra.ops_settings(database))
    settings = infra.api_settings(database)
    engine = create_engine(settings.app_database, application_name="test-first-answer")
    deps = ApiDependencies(
        settings=settings,
        engine=engine,
        verifier=FirebaseTokenVerifier(settings.firebase_project_id),
        keyring=load_keyring(settings.master_key_dir),
        models=ModelChoice.configure(
            settings.meta_test_model, settings.meta_production_model, settings.synthetic_model_role
        ),
    )
    with TestClient(
        create_app(deps),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57005),
    ) as client:
        yield ApiClient(client)
    engine.dispose()
    owner.dispose()


def timed(call: Any) -> tuple[Any, float]:
    started = time.perf_counter()
    response = call()
    return response, time.perf_counter() - started


@pytest.mark.req("DIV1-01", "DIV1-10")
def test_the_first_answer_changes_the_world_within_one_second_on_the_pinned_release(
    full_api: ApiClient, ada: str
) -> None:
    workspace = full_api.create_workspace(ada, "First answer (synthetic)")["workspace_id"]
    base = f"/v1/workspaces/{workspace}"

    typing = [
        timed(lambda prefix=prefix: full_api.get("/v1/taxonomy/titles", ada, q=prefix))
        for prefix in ("a", "s", "c", "d", "da", "data", "data an", "data analyst")
    ]
    typed, _ = typing[-1]
    [analyst] = [m for m in typed.json()["matches"] if m["title"] == "data analyst"]
    chosen, choose_s = timed(
        lambda: full_api.write(
            "POST",
            f"{base}/origin/role",
            ada,
            {"expected_version": 0, "concept_id": analyst["concept_id"]},
        )
    )
    shown, origin_s = timed(lambda: full_api.get(f"{base}/origin", ada))
    _, again_s = timed(lambda: full_api.get(f"{base}/origin", ada))

    typing_s = [round(seconds, 3) for _, seconds in typing]
    print(
        f"first answer on {typed.json()['release']['dataset_id']}: type-ahead {typing_s} s, "
        f"choose {choose_s:.3f} s, origin {origin_s:.3f} s (again {again_s:.3f} s)"
    )
    assert all(response.status_code == 200 for response, _ in typing)
    assert typed.json()["release"]["sample"] is False  # the full pinned release
    assert chosen.status_code == 201, chosen.text
    assert shown.status_code == 200, shown.text
    assert max(seconds for _, seconds in typing) < BUDGET_S
    assert choose_s + origin_s < BUDGET_S  # the answer saved and the world's response

    body = shown.json()
    print(
        "destinations:",
        [(d["title"], d["family"]["code"], d["direction"]) for d in body["destinations"]],
    )
    assert len(body["usual_skills"]) == 36  # ESCO v1.2.1 lists 36 for the data analyst
    assert {s["state"] for s in body["usual_skills"]} == {"usual_in_role"}
    assert len(body["destinations"]) >= 4
    assert "data analyst" not in [d["title"] for d in body["destinations"]]  # the origin
    assert all(d["reasons"][0]["reason"] == "joined_by_shared_skills" for d in body["destinations"])
    # The product owner's answer (1 November 2026, "Always a plain line"): each destination
    # states the skills it shares as a plain fact; none is singled out as a connection.
    assert "connection" not in body


# The heaviest first answers on ESCO v1.2.1: the occupation with the most essential skills,
# and the one sharing three or more with the most other occupations (review M1).
HEAVIEST = {"clinical psychologist": 99, "spa manager": 46}


@pytest.mark.req("DIV1-01", "DIV1-10")
def test_the_heaviest_first_answers_change_the_world_within_one_second(
    full_api: ApiClient, ada: str
) -> None:
    for title, essential in HEAVIEST.items():
        workspace = full_api.create_workspace(ada, f"{title} (synthetic)")["workspace_id"]
        base = f"/v1/workspaces/{workspace}"
        [match] = [
            m
            for m in full_api.get("/v1/taxonomy/titles", ada, q=title).json()["matches"]
            if m["title"] == title
        ]
        chosen, choose_s = timed(
            lambda base=base, match=match: full_api.write(
                "POST",
                f"{base}/origin/role",
                ada,
                {"expected_version": 0, "concept_id": match["concept_id"]},
            )
        )
        shown, origin_s = timed(lambda base=base: full_api.get(f"{base}/origin", ada))

        body = shown.json()
        print(
            f"{title}: {len(body['usual_skills'])} usual skills, "
            f"{len(body['destinations'])} destinations, choose {choose_s:.3f} s, "
            f"origin {origin_s:.3f} s"
        )
        assert chosen.status_code == 201, chosen.text
        assert shown.status_code == 200, shown.text
        assert len(body["usual_skills"]) == essential
        assert choose_s + origin_s < BUDGET_S


@pytest.mark.req("DIV1-03", "DIV1-04")
def test_a_title_esco_does_not_list_offers_the_titles_holding_most_of_its_words(
    full_api: ApiClient, ada: str
) -> None:
    # P01's, P04's and P05's own titles are not ESCO titles (review I5): the type-ahead
    # offers the occupations whose titles hold the most of their words, whole words then
    # rarer words first, for the person to choose from. Nothing is chosen or joined for them.
    def offered(typed: str) -> tuple[bool, list[str]]:
        found = full_api.get("/v1/taxonomy/titles", ada, q=typed, limit=20)
        assert found.status_code == 200, found.text
        body = found.json()
        assert len(body["matches"]) <= body["total"] + body["uk_total"]
        return body["partial"], [m["title"] for m in body["matches"]]

    p05 = offered("Bookkeeping assistant")
    # Neither list holds "NHS" in any title, so only "nurse" is counted, as P04's "Registered
    # nurse" was before the UK job-title index (Task 6d slice B) listed it.
    nhs = offered("Registered nurse (NHS)")
    whole, nothing = offered("data analyst"), offered("zqxj wvuy")
    # The widest fallback: nearly every label holds one of these words, none holds them all.
    widest, widest_s = timed(lambda: offered("a b c d e f g h"))
    longer = offered("a b c d e f g h i")  # more words than any fallback compares

    print(f"type-ahead with no title holding every word: widest {widest_s:.3f} s")
    print(f"P05 {p05}\nRegistered nurse (NHS) {nhs}")
    assert widest_s < BUDGET_S
    assert widest[0] is True
    assert longer == (False, [])
    # Task 6d slice B: P01's and P04's own titles are UK job titles the index lists, so they
    # are offered as such (`test_the_acceptance_titles_are_uk_job_titles_...`); only a title
    # neither list holds asks about ESCO's closest titles.
    assert (p05[0], nhs[0]) == (True, True)
    # Task W2B fix round 2 (re-review M-B): "registered" says a role's standing, not its work,
    # so it isn't counted, and a title holding "nurse" whole comes before one that only
    # begins with it ("nursery"): the five nurses first, never a registered sales assistant.
    nurses = {
        "nurse assistant",
        "specialist nurse",
        "veterinary nurse",
        "advanced nurse practitioner",
        "nurse responsible for general care",
    }
    assert set(nhs[1][:5]) == nurses
    assert "sales support assistant" not in nhs[1]
    labels = full_api.get("/v1/taxonomy/titles", ada, q="Registered nurse (NHS)", limit=20).json()
    held = [bool(re.search(r"\bnurse\b", m["matched_label"])) for m in labels["matches"]]
    assert held == sorted(held, reverse=True)  # every whole "nurse" before any "nursery"
    assert not all(held)
    assert p05[1][0] == "bookkeeper"  # "bookkeeping" is a rarer word than "assistant"
    assert (whole[0], whole[1][0]) == (False, "data analyst")  # every word: not partial
    assert nothing == (False, [])  # no word of any title: an honest empty answer


# The role-space appendix's offline test (Task 6d slice B, acceptance 1 and 2): each title is
# in the pinned UK job-title index and no ESCO title, with the ISCO-08 groups ONS codes it to.
UK_TITLES = {
    "Registered nurse": ["2221"],
    "Data quality analyst": ["2421"],
    "Prompt engineer": ["2512"],
    "Doula": ["5321"],
}


@pytest.mark.req("DIV1-13", "DIV1-14")
def test_the_acceptance_titles_are_uk_job_titles_and_the_world_answers_within_a_second(
    full_api: ApiClient, ada: str
) -> None:
    for title, groups in UK_TITLES.items():
        typed, typed_s = timed(
            lambda title=title: full_api.get("/v1/taxonomy/titles", ada, q=title)
        )
        assert typed.status_code == 200, typed.text
        matches = typed.json()["matches"]
        # What was typed comes first ("Registered children's nurse" holds the words too).
        assert (matches[0]["source"], matches[0]["title"]) == ("uk_title_index", title)
        assert [g["code"] for g in matches[0]["isco_groups"]] == groups

        workspace = full_api.create_workspace(ada, f"{title} (synthetic)")["workspace_id"]
        named, name_s = timed(
            lambda workspace=workspace, title=title: full_api.write(
                "POST",
                f"/v1/workspaces/{workspace}/origin/role/title",
                ada,
                {"expected_version": 0, "title": title},
            )
        )
        shown, origin_s = timed(
            lambda workspace=workspace: full_api.get(f"/v1/workspaces/{workspace}/origin", ada)
        )
        print(f"{title}: type-ahead {typed_s:.3f} s, saved {name_s:.3f} s, origin {origin_s:.3f} s")
        assert named.status_code == 201, named.text
        assert shown.status_code == 200, shown.text
        role = shown.json()["role"]
        assert (role["text"], role["kind"], role["state"]) == (title, "ons", "not_in_esco")
        closest = role["closest"]
        assert closest["decision"] == "not_yet"
        assert [g["group"]["code"] for g in closest["groups"]] == groups
        assert all(g["occupations"] and g["group"]["label"] for g in closest["groups"])
        assert typed_s < BUDGET_S
        assert name_s + origin_s < BUDGET_S

    # Acceptance 3: a title neither list holds is kept in the person's own words.
    workspace = full_api.create_workspace(ada, "Own words (synthetic)")["workspace_id"]
    own = full_api.write(
        "POST",
        f"/v1/workspaces/{workspace}/origin/role/title",
        ada,
        {"expected_version": 0, "title": "Bookkeeping assistant"},
    )
    role = full_api.get(f"/v1/workspaces/{workspace}/origin", ada).json()["role"]
    assert own.status_code == 201, own.text
    assert (role["text"], role["kind"], role["closest"]) == (
        "Bookkeeping assistant",
        "own_words",
        None,
    )
