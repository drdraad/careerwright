"""The first answer on the full pinned ESCO release (plan section 4, "The first ten seconds";
Sprint W SW.5): the type-ahead, the answer saved, and the world's response (the role's usual
skills, the first destinations joined by shared essential skills, the unexpected connection),
each through the real API against real PostgreSQL 16, with no model call, timed against the
one-second budget, for "data analyst" and the heaviest roles ESCO holds; and the type-ahead
for titles ESCO does not list. The timings are printed with the run (`-s`); the database
runs in the test stack's container on this machine."""

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
from careerwright.cli import import_taxonomy, migrate_app, seed
from careerwright.db import create_engine
from careerwright.identity.firebase import FirebaseTokenVerifier
from careerwright.identity.keyring import load_keyring
from careerwright.identity.model_choice import ModelChoice
from tests.support.client import ApiClient
from tests.support.infra import API_BASE, Infra, migrator_engine
from tools.datasets import DATASETS_DIR

pytestmark = pytest.mark.integration

BUDGET_S = 1.0  # plan section 4: the first answer changes the world within one second


@pytest.fixture(scope="module")
def full_api(infra: Infra) -> Iterator[ApiClient]:
    release = Path(DATASETS_DIR) / ESCO_RELEASE.file_name
    assert release.is_file(), f"run `make setup` first: {release} is missing"
    database = f"careerwright_first_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    owner = migrator_engine(infra, database)
    migrate_app(owner)
    seed(owner, infra.ops_settings(database))
    assert import_taxonomy(owner, release) == "imported"
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
    print("connection:", body["connection"]["sentence"] if body["connection"] else None)
    assert len(body["usual_skills"]) == 36  # ESCO v1.2.1 lists 36 for the data analyst
    assert {s["state"] for s in body["usual_skills"]} == {"usual_in_role"}
    assert len(body["destinations"]) >= 4
    assert "data analyst" not in [d["title"] for d in body["destinations"]]  # the origin
    assert all(
        "of the same essential skills" in d["why_it_could_suit"][0] for d in body["destinations"]
    )
    connection = body["connection"]
    assert connection is not None
    assert connection["sentence"].startswith("A data analyst and ")
    assert connection["shared_skill_count"] >= 3


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
    # offers the occupations whose titles hold the most of their words, rarer words first,
    # for the person to choose from. Nothing is chosen or joined for them.
    def offered(typed: str) -> tuple[bool, list[str]]:
        found = full_api.get("/v1/taxonomy/titles", ada, q=typed, limit=20)
        assert found.status_code == 200, found.text
        body = found.json()
        assert len(body["matches"]) <= body["total"]
        return body["partial"], [m["title"] for m in body["matches"]]

    p01 = offered("Data quality analyst")
    p04 = offered("Registered nurse")
    p05 = offered("Bookkeeping assistant")
    whole, nothing = offered("data analyst"), offered("zqxj wvuy")
    # The widest fallback: nearly every label holds one of these words, none holds them all.
    widest, widest_s = timed(lambda: offered("a b c d e f g h"))
    longer = offered("a b c d e f g h i")  # more words than any fallback compares

    print(f"type-ahead with no title holding every word: widest {widest_s:.3f} s")
    print(f"P01 {p01}\nP04 {p04}\nP05 {p05}")
    assert widest_s < BUDGET_S
    assert widest[0] is True
    assert longer == (False, [])
    assert (p01[0], p04[0], p05[0]) == (True, True, True)
    assert {"data quality specialist", "data analyst"} <= set(p01[1])
    assert {"specialist nurse", "nurse responsible for general care"} <= set(p04[1])
    assert p05[1][0] == "bookkeeper"  # "bookkeeping" is a rarer word than "assistant"
    assert (whole[0], whole[1][0]) == (False, "data analyst")  # every word: not partial
    assert nothing == (False, [])  # no word of any title: an honest empty answer
