"""Migrations against real PostgreSQL 16: a fresh database reaches head; a populated database
at every earlier revision upgrades to head without losing data (plan Sprint 1 acceptance)."""

import dataclasses
import json
import uuid
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient

from careerwright.api.app import create_app
from careerwright.api.deps import ApiDependencies
from careerwright.capability.commands import committed_data, pack_targets
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.taxonomy import search_essential_skills
from careerwright.cli import import_taxonomy, migrate_app, seed, seed_fixture
from careerwright.db import create_engine, system_transaction
from careerwright.identity import store as identity_store
from careerwright.identity.keyring import Keyring
from careerwright.identity.model_registry import FIXTURE_DISCOVERY_MODEL_ID
from careerwright.identity.records import EventKind
from careerwright.identity.runs import output_context
from careerwright.profile import store as profile_store
from careerwright.profile.discovery import PROMPT_VERSION, DiscoveryProposal
from careerwright.profile.document import (
    FieldState,
    ProfileInput,
    TargetListInput,
    apply_profile_input,
    apply_updates,
    empty_profile,
)
from careerwright.profile.records import SourceKind, TargetCoverage, TargetLink
from careerwright.profile.targets import resolve_target, stored_targets
from careerwright.seed import FIXTURE_WORKSPACE_ID, INVITED_ACTORS
from careerwright.vocabulary import DataMode
from tests.support.client import ApiClient
from tests.support.esco import SAMPLE_PATH, SAMPLE_RELEASE
from tests.support.infra import API_BASE, Infra, migrator_engine

pytestmark = pytest.mark.integration


def head() -> str:
    config = Config()
    config.set_main_option("script_location", "careerwright:migrations")
    revision = ScriptDirectory.from_config(config).get_current_head()
    assert revision is not None
    return revision


@pytest.mark.req("BND1-14")
def test_a_fresh_database_migrates_to_head_and_seeds(infra: Infra) -> None:
    database = f"careerwright_fresh_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine)
        seed(engine, infra.ops_settings(database))
        seed(engine, infra.ops_settings(database))  # seeding twice changes nothing
    finally:
        engine.dispose()

    [version] = infra.query("SELECT version_num FROM alembic_version", database=database)
    assert version["version_num"] == head()
    counts = infra.query(
        "SELECT (SELECT count(*) FROM careerwright.actors) AS actors, "
        "(SELECT count(*) FROM careerwright.workspaces) AS workspaces, "
        "(SELECT count(*) FROM careerwright.profile_versions) AS versions",
        database=database,
    )
    assert counts == [{"actors": 2, "workspaces": 1, "versions": 1}]


TABLES_0001 = (
    "actors",
    "workspaces",
    "source_references",
    "profile_versions",
    "profile_version_sources",
    "workspace_events",
)
RECEIPT_COLUMNS_0001 = "actor_id, idempotency_key, command, request_sha256, status_code, response"


# Columns later revisions add to 0001 tables (0005: a source's turn, messages and basis).
ADDED_SINCE_0001 = {"source_references": ["run_id", "message_ids", "basis"]}


def snapshot(infra: Infra, database: str) -> dict[str, list[dict[str, object]]]:
    """Every 0001 row with its 0001 columns, exactly."""
    return {
        table: infra.query(
            f"SELECT (to_jsonb(t) - %s::text[])::text AS row FROM careerwright.{table} t "  # noqa: S608
            "ORDER BY 1",
            (ADDED_SINCE_0001.get(table, []),),
            database=database,
        )
        for table in TABLES_0001
    }


def add_receipts(tx: sa.Connection, workspace_id: uuid.UUID) -> None:
    """One receipt whose response names its workspace, and one retry cache that does not."""
    owner = INVITED_ACTORS[0].actor_id
    for key, response in (
        (ATTRIBUTABLE, {"workspace_id": str(workspace_id), "version": 2}),
        (UNATTRIBUTABLE, {"credential_id": str(uuid.uuid4())}),
    ):
        tx.exec_driver_sql(
            "INSERT INTO careerwright.command_receipts (actor_id, idempotency_key, command, "
            "request_sha256, status_code, response) VALUES (%(actor)s, %(key)s, 'cmd', "
            "repeat('a', 64), 200, %(response)s::jsonb)",
            {"actor": owner, "key": key, "response": json.dumps(response)},
        )


ATTRIBUTABLE = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
UNATTRIBUTABLE = uuid.UUID("00000000-0000-4000-8000-0000000000a2")


@pytest.mark.req("BND1-14")
def test_a_populated_database_upgrades_to_head_without_losing_data(infra: Infra) -> None:
    database = f"careerwright_upgrade_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0001")
        seed_fixture(engine, infra.ops_settings(database))  # the fixture workspace, profile
        with engine.begin() as tx:
            edited = add_edited_workspace(tx)
            add_receipts(tx, edited)
        before = snapshot(infra, database)
        receipt_before = infra.query(
            f"SELECT {RECEIPT_COLUMNS_0001} FROM careerwright.command_receipts "  # noqa: S608
            "WHERE idempotency_key = %s",
            (ATTRIBUTABLE,),
            database=database,
        )

        migrate_app(engine)
    finally:
        engine.dispose()

    assert snapshot(infra, database) == before
    # 0005's source columns are empty for every upgraded source: nothing is invented.
    assert infra.query(
        "SELECT count(*) AS n FROM careerwright.source_references "
        "WHERE run_id IS NOT NULL OR message_ids IS NOT NULL OR basis IS NOT NULL",
        database=database,
    ) == [{"n": 0}]
    # 0003: a receipt is kept and attributed to the workspace its response names; a retry
    # cache that names none is dropped (documented in the migration).
    receipts = infra.query(
        f"SELECT {RECEIPT_COLUMNS_0001}, workspace_id FROM careerwright.command_receipts",  # noqa: S608
        database=database,
    )
    assert receipts == [{**receipt_before[0], "workspace_id": edited}]
    [version] = infra.query("SELECT version_num FROM alembic_version", database=database)
    assert version["version_num"] == head()
    # The upgraded data is still reachable through row-level security, and only by its owner.
    count = "SELECT count(*) AS n FROM careerwright.profile_versions"
    owner = infra.as_role("pg_api", count, actor=str(INVITED_ACTORS[0].actor_id), database=database)
    other = infra.as_role("pg_api", count, actor=str(INVITED_ACTORS[1].actor_id), database=database)
    assert (owner, other) == ([{"n": 3}], [{"n": 0}])


def add_edited_workspace(tx: sa.Connection) -> uuid.UUID:
    """A second workspace with two profile versions, written through the 0001-era stores."""
    owner = INVITED_ACTORS[0].actor_id
    workspace = identity_store.insert_workspace(
        tx,
        workspace_id=uuid.uuid4(),
        owner_actor_id=owner,
        name="Edited before the upgrade",
        data_mode=DataMode.LIVE_ASSISTED,
        synthetic=True,
    )
    now = datetime.now(UTC)
    document = empty_profile()
    for version, city in enumerate(("Leeds", "York"), start=1):
        source = uuid.uuid4()
        profile_store.insert_source(
            tx,
            source_ref_id=source,
            workspace_id=workspace.workspace_id,
            kind=SourceKind.DIRECT_ENTRY,
            label="Direct entry",
            recorded_by=owner,
            observed_at=now,
        )
        new = ProfileInput.model_validate(
            {
                **{name: {"state": "unasked"} for name in ProfileInput.model_fields},
                "cities": {"state": "provided", "value": [city]},
            }
        )
        document = apply_profile_input(document, new, source)
        profile_store.insert_profile_version(tx, workspace.workspace_id, version, document, owner)
        profile_store.link_sources(tx, workspace.workspace_id, version, [source])
        identity_store.append_event(
            tx, workspace.workspace_id, EventKind.PROFILE_VERSION_CREATED, str(version)
        )
    return workspace.workspace_id


@pytest.mark.req("MODEL-08", "MODEL-04")
def test_an_untouched_old_default_run_limit_upgrades_to_the_new_default(infra: Infra) -> None:
    database = f"careerwright_limits_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0008")
        seed_fixture(engine, infra.ops_settings(database))
        with engine.begin() as tx:
            rows = {
                "untouched": (100_000_000, 1),  # the old built-in default, never edited
                "chosen": (100_000_000, 2),  # the person set $0.10 themselves
                "lower": (50_000_000, 1),  # created under another configured default
            }
            workspaces = {name: add_edited_workspace(tx) for name in rows}
            for name, (run_limit, version) in rows.items():
                tx.exec_driver_sql(
                    "INSERT INTO careerwright.spend_limits (workspace_id, run_limit_nano_usd, "
                    "period_limit_nano_usd, version) VALUES (%(ws)s, %(run)s, 1000000000, %(v)s)",
                    {"ws": workspaces[name], "run": run_limit, "v": version},
                )

        migrate_app(engine)
    finally:
        engine.dispose()

    limits = {
        name: infra.query(
            "SELECT run_limit_nano_usd AS run, period_limit_nano_usd AS period, version "
            "FROM careerwright.spend_limits WHERE workspace_id = %s",
            (workspace,),
            database=database,
        )[0]
        for name, workspace in workspaces.items()
    }
    assert limits == {
        "untouched": {"run": 150_000_000, "period": 1_000_000_000, "version": 1},
        "chosen": {"run": 100_000_000, "period": 1_000_000_000, "version": 2},
        "lower": {"run": 50_000_000, "period": 1_000_000_000, "version": 1},
    }


@pytest.mark.req("MODEL-08")
def test_attempts_that_made_no_call_upgrade_to_a_known_zero_cost(infra: Infra) -> None:
    database = f"careerwright_zero_cost_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0005")
        seed_fixture(engine, infra.ops_settings(database))
        with engine.begin() as tx:
            workspace = add_edited_workspace(tx)
            for state, cost in (("none", None), ("reconciled", 40_000), ("unknown", None)):
                run = uuid.uuid4()
                tx.exec_driver_sql(
                    "INSERT INTO careerwright.runs (run_id, workspace_id, data_mode, synthetic, "
                    "kind, "
                    "requested_by, model_id, model_mode, status) SELECT %(run)s, workspace_id, "
                    "data_mode, synthetic, 'connection_check', owner_actor_id, "
                    "'muse-spark-1.3-contributor', 'contributor', 'queued' "
                    "FROM careerwright.workspaces WHERE workspace_id = %(ws)s",
                    {"run": run, "ws": workspace},
                )
                tx.exec_driver_sql(
                    "INSERT INTO careerwright.model_attempts (run_id, workspace_id, model_id, "
                    "period_start, spend_state, cost_nano_usd, finished_at, outcome) VALUES "
                    "(%(run)s, %(ws)s, 'muse-spark-1.3-contributor', date '2026-10-01', "
                    "%(state)s, %(cost)s, clock_timestamp(), 'x')",
                    {"run": run, "ws": workspace, "state": state, "cost": cost},
                )

        migrate_app(engine)
    finally:
        engine.dispose()

    rows = infra.query(
        "SELECT spend_state, cost_nano_usd FROM careerwright.model_attempts ORDER BY spend_state",
        database=database,
    )
    # No call was made, so the cost is known: zero. Unknown stays unknown.
    assert rows == [
        {"spend_state": "none", "cost_nano_usd": 0},
        {"spend_state": "reconciled", "cost_nano_usd": 40_000},
        {"spend_state": "unknown", "cost_nano_usd": None},
    ]


@pytest.mark.req("DIV1-01", "BND1-14")
def test_0032_fills_the_essential_skill_search_for_the_release_already_held(
    infra: Infra,
) -> None:
    # Task W2B fix round 1: a release imported before 0032 is searched through its essential
    # skills' labels once migrated, with no new import.
    database = f"careerwright_skill_search_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0031")
        assert import_taxonomy(engine, SAMPLE_PATH, SAMPLE_RELEASE) == "imported"
        migrate_app(engine)
        with system_transaction(engine) as tx:
            found = search_essential_skills(tx, "accounting entries", 10)
            titles = taxonomy_store.occupation_facts(
                tx, [r.concept_id for r in found.reached], skills_shown=0
            )
    finally:
        engine.dispose()

    [counts] = infra.query(
        "SELECT count(*) AS skills, count(*) FILTER (WHERE search_vector = "
        "to_tsvector('english', preferred_label)) AS filled FROM careerwright.skills",
        database=database,
    )
    assert counts["skills"] > 0
    assert counts["filled"] == counts["skills"]
    reached = {titles[r.concept_id].preferred_label: r.skill_label for r in found.reached}
    assert reached == {
        "accounting assistant": "accounting entries",
        "bookkeeper": "accounting entries",
    }


@pytest.mark.req("PROF-10", "BND1-14")
def test_0034_gives_each_stored_target_its_record_and_folds_ampersands_and_accents(
    infra: Infra,
) -> None:
    # Task 6d slice A: existing profiles migrate forward, each target title gets its record by
    # the same rules as `resolve_target`; and the concept key, defined only by migrations, is
    # changed by this one: "&" against "and", and accented titles against their plain
    # spelling (real ESCO titles of the sample: "distribution & logistics manager", "sauté
    # cook").
    database = f"careerwright_targets_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    pairs = [("distribution & logistics manager", "distribution and logistics manager"),
             ("sauté cook", "saute cook")]  # fmt: skip
    titles = ["Registered nurse", "Bicycle-mechanics.", "Saute cooks"]  # at most three
    try:
        migrate_app(engine, "0033")
        assert import_taxonomy(engine, SAMPLE_PATH, SAMPLE_RELEASE) == "imported"
        seed_fixture(engine, infra.ops_settings(database))  # as seeded before 0034
        with system_transaction(engine) as tx:
            before = [
                taxonomy_store.concept_keys(tx, pair) for pair in pairs
            ]  # the key before 0034
            workspace = add_targets(tx, titles)
        migrate_app(engine)
        with system_transaction(engine) as tx:
            after = [taxonomy_store.concept_keys(tx, pair) for pair in pairs]
            latest = profile_store.current_profile(tx, workspace)
            assert latest is not None
            stored = stored_targets(tx, workspace, latest.document)
            pack = pack_targets(committed_data())
            decided = [resolve_target(tx, workspace, title, pack) for title in titles]
            fixture = profile_store.current_profile(tx, FIXTURE_WORKSPACE_ID)
            assert fixture is not None
            seeded = stored_targets(tx, FIXTURE_WORKSPACE_ID, fixture.document)
    finally:
        engine.dispose()

    assert [len(set(keys.values())) for keys in before] == [2, 2]  # the defect: two keys
    assert [len(set(keys.values())) for keys in after] == [1, 1]
    # The backfill and the resolver agree, title for title.
    assert stored == decided
    assert [(r.link, r.coverage) for r in stored] == [
        (TargetLink.PACK_CROSSWALK, TargetCoverage.PACK_TARGET),
        (TargetLink.OCCUPATION_CHOICE, TargetCoverage.NOT_COVERED),
        (TargetLink.EXACT_LABEL, TargetCoverage.NOT_COVERED),
    ]
    # The fixture workspace seeded before 0034 has its target's record too.
    assert [(r.title, r.link, r.pack_target_id) for r in seeded] == [
        ("Data quality analyst", TargetLink.PACK_CROSSWALK, "data-quality-analyst-manchester")
    ]


MECHANIC_URI = "http://data.europa.eu/esco/occupation/336cf331-8082-4a0c-bf5f-e7c54706211c"


def add_targets(tx: sa.Connection, targets: list[str]) -> uuid.UUID:
    """A workspace whose current profile names these targets, written through the stores
    before 0034, with the bicycle mechanic chosen from ESCO."""
    owner = INVITED_ACTORS[0].actor_id
    workspace = identity_store.insert_workspace(
        tx,
        workspace_id=uuid.uuid4(),
        owner_actor_id=owner,
        name="Targets before 0034",
        data_mode=DataMode.LIVE_ASSISTED,
        synthetic=True,
    )
    now = datetime.now(UTC)
    choice = uuid.uuid4()
    profile_store.insert_source(
        tx,
        source_ref_id=choice,
        workspace_id=workspace.workspace_id,
        kind=SourceKind.OCCUPATION_CHOICE,
        label="Chosen from the ESCO occupations",
        recorded_by=owner,
        observed_at=now,
        locator=MECHANIC_URI,
    )
    new = ProfileInput.model_validate(
        {
            **{name: {"state": "unasked"} for name in ProfileInput.model_fields},
            "target_titles": {"state": "provided", "value": targets},
        }
    )
    document = apply_profile_input(empty_profile(), new, choice)
    profile_store.insert_profile_version(tx, workspace.workspace_id, 1, document, owner)
    profile_store.link_sources(tx, workspace.workspace_id, 1, [choice])
    return workspace.workspace_id


OLDER_TARGETS = ["Saute cooks", "IT support technician [2nd line]", "Registered nurse (adult)"]
NEWER_TARGETS = ["bicycle mechanic", "Registered nurse (adult)"]


@pytest.mark.req("PROF-10", "BND1-14")
def test_0035_gives_every_version_s_targets_a_record_so_an_older_discovery_still_opens(
    infra: Infra, api_deps: ApiDependencies, ada: str
) -> None:
    # Task 6d slice A fix round 1 (the target records' review, Important 1): 0034 gave a record
    # only to each workspace's newest targets. A discovery is read from the version it pinned,
    # so one made before a target was replaced failed to open its slate and its note
    # (INTERNAL_ERROR). Before 0034: version 1 holds three targets and a discovery pinned to
    # it; version 2, the bicycle mechanic chosen from that discovery's slate, keeps one of
    # them, so the discovery is still current.
    database = f"careerwright_every_version_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    settings = infra.api_settings(database)
    app_engine = create_engine(settings.app_database, application_name="test-0035")
    deps = dataclasses.replace(api_deps, settings=settings, engine=app_engine)
    try:
        migrate_app(engine, "0033")
        assert import_taxonomy(engine, SAMPLE_PATH, SAMPLE_RELEASE) == "imported"
        seed_fixture(engine, infra.ops_settings(database))
        with system_transaction(engine) as tx:
            workspace, discovery = add_discovery_then_a_choice(tx, deps.keyring)
        base = f"/v1/workspaces/{workspace}/discoveries/{discovery}"
        with TestClient(
            create_app(deps),
            base_url=API_BASE,
            raise_server_exceptions=False,
            client=("127.0.0.1", 57016),
        ) as client:
            api = ApiClient(client)
            migrate_app(engine, "0034")
            with system_transaction(engine) as tx:
                after_0034 = {
                    tuple(row)
                    for row in tx.execute(
                        sa.text(
                            "SELECT title, link, coverage FROM careerwright.target_records "
                            "WHERE workspace_id = :ws"
                        ),
                        {"ws": workspace},
                    )
                }
            # A title with no record is not resolved, never an error.
            gap = api.get(f"{base}/slate", ada)

            migrate_app(engine)
            with system_transaction(engine) as tx:
                pack = pack_targets(committed_data())
                documents = [profile_store.profile_version(tx, workspace, v) for v in (1, 2)]
                stored = [
                    record
                    for document in documents
                    if document is not None
                    for record in stored_targets(tx, workspace, document.document)
                ]
                decided = [resolve_target(tx, workspace, r.title, pack) for r in stored]
            opened = api.get(f"{base}/slate", ada)
            note = api.write("POST", f"{base}/explanation", ada, {"expected_profile_version": 2})
    finally:
        engine.dispose()
        app_engine.dispose()

    # 0034's gap: the two targets only version 1 holds have no record.
    assert after_0034 == {
        ("bicycle mechanic", "occupation_choice", "not_covered"),
        ("Registered nurse (adult)", "none", "not_covered"),
    }
    assert gap.status_code == 200, gap.text
    assert gap.json()["unmatched_titles"] == OLDER_TARGETS
    # After 0035 every title of every version has its record, decided as `resolve_target`
    # decides it, the bracketed qualifiers left out to reach a pack target by its title.
    assert stored == decided
    assert [(r.title, r.link, r.coverage, r.pack_target_id) for r in stored] == [
        ("Saute cooks", TargetLink.EXACT_LABEL, TargetCoverage.NOT_COVERED, None),
        (
            "IT support technician [2nd line]",
            TargetLink.PACK_CROSSWALK,
            TargetCoverage.PACK_TARGET,
            "it-support-technician-bristol",
        ),
        (
            "Registered nurse (adult)",
            TargetLink.PACK_CROSSWALK,
            TargetCoverage.PACK_TARGET,
            "registered-nurse-manchester",
        ),
        ("bicycle mechanic", TargetLink.OCCUPATION_CHOICE, TargetCoverage.NOT_COVERED, None),
        (
            "Registered nurse (adult)",
            TargetLink.PACK_CROSSWALK,
            TargetCoverage.PACK_TARGET,
            "registered-nurse-manchester",
        ),
    ]
    # The older discovery opens its slate, the sauté cook joined to its title, and its note.
    assert opened.status_code == 200, opened.text
    assert opened.json()["unmatched_titles"] == OLDER_TARGETS[1:]
    assert note.status_code == 202, note.text


def add_discovery_then_a_choice(tx: sa.Connection, keyring: Keyring) -> tuple[uuid.UUID, uuid.UUID]:
    """Ada's demo workspace (its note runs offline) before 0034: version 1 with an answer and
    three targets, a discovery pinned to it, and version 2, the bicycle mechanic chosen from
    that discovery's slate in place of two of them."""
    owner = INVITED_ACTORS[0].actor_id
    workspace = identity_store.insert_workspace(
        tx,
        workspace_id=uuid.uuid4(),
        owner_actor_id=owner,
        name="An older discovery (synthetic)",
        data_mode=DataMode.DEMO,
        synthetic=True,
    ).workspace_id
    now = datetime.now(UTC)
    typed, choice, discovery, output = (uuid.uuid4() for _ in range(4))
    profile_store.insert_source(
        tx,
        source_ref_id=typed,
        workspace_id=workspace,
        kind=SourceKind.DIRECT_ENTRY,
        label="Typed in (synthetic)",
        recorded_by=owner,
        observed_at=now,
    )
    first = ProfileInput.model_validate(
        {
            **{name: {"state": "unasked"} for name in ProfileInput.model_fields},
            "enjoyed_tasks": {"state": "provided", "value": ["tuning bicycles"]},
            "target_titles": {"state": "provided", "value": OLDER_TARGETS},
        }
    )
    older = apply_profile_input(empty_profile(), first, typed)
    profile_store.insert_profile_version(tx, workspace, 1, older, owner)
    profile_store.link_sources(tx, workspace, 1, [typed])
    proposal = DiscoveryProposal.model_validate(
        {
            "origin": "fixture",
            "prompt_version": PROMPT_VERSION,
            "profile_version": 1,
            "queries": [
                {
                    "query_id": "q1",
                    "text": "tune bicycles",
                    "channel": "tasks",
                    "based_on": [{"field": "enjoyed_tasks", "text": "tuning bicycles"}],
                }
            ],
            "hypotheses": [],
            "release": SAMPLE_RELEASE.dataset_id,
        }
    )
    sealed = keyring.seal(proposal.model_dump_json().encode(), output_context(workspace, output))
    tx.exec_driver_sql(
        "INSERT INTO careerwright.runs (run_id, workspace_id, data_mode, synthetic, kind, "
        "requested_by, model_id, model_mode, status, output_id, started_at, finished_at, "
        "profile_version) VALUES (%(run)s, %(ws)s, 'demo', true, 'discovery', %(owner)s, "
        "%(model)s, 'fixture', 'complete', %(out)s, clock_timestamp(), clock_timestamp(), 1)",
        {
            "run": discovery,
            "ws": workspace,
            "owner": owner,
            "model": FIXTURE_DISCOVERY_MODEL_ID,
            "out": output,
        },
    )
    tx.exec_driver_sql(
        "INSERT INTO careerwright.run_outputs (output_id, run_id, workspace_id, key_version, "
        "nonce, ciphertext, content_sha256) VALUES (%(out)s, %(run)s, %(ws)s, %(v)s, %(n)s, "
        "%(c)s, repeat('0', 64))",
        {
            "out": output,
            "run": discovery,
            "ws": workspace,
            "v": sealed.key_version,
            "n": sealed.nonce,
            "c": sealed.ciphertext,
        },
    )
    profile_store.insert_source(
        tx,
        source_ref_id=choice,
        workspace_id=workspace,
        kind=SourceKind.OCCUPATION_CHOICE,
        label="Chosen from Careerwright's suggestions",
        recorded_by=owner,
        observed_at=now,
        locator=MECHANIC_URI,
        run_id=discovery,
    )
    chosen = TargetListInput(state=FieldState.PROVIDED, value=NEWER_TARGETS)
    newer, _ = apply_updates(older, {"target_titles": (chosen, choice)})
    profile_store.insert_profile_version(tx, workspace, 2, newer, owner)
    profile_store.link_sources(tx, workspace, 2, [choice])
    return workspace, discovery


@pytest.mark.req("ACQ-01")
def test_0014_leaves_only_http_urls_in_url_fields(infra: Infra) -> None:
    database = f"careerwright_urls_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    unsafe = "javascript:alert(1)"
    try:
        migrate_app(engine, "0013")
        seed_fixture(engine, infra.ops_settings(database))
        with engine.begin() as tx:
            workspace = add_edited_workspace(tx)
            run, attempt = uuid.uuid4(), uuid.uuid4()
            tx.exec_driver_sql(
                "INSERT INTO careerwright.runs (run_id, workspace_id, data_mode, synthetic, kind, "
                "requested_by, status, failure_class, finished_at) SELECT %(run)s, workspace_id, "
                "data_mode, synthetic, 'acquisition', owner_actor_id, 'failed', 'source_blocked', "
                "clock_timestamp() FROM careerwright.workspaces WHERE workspace_id = %(ws)s",
                {"run": run, "ws": workspace},
            )
            tx.exec_driver_sql(
                "INSERT INTO careerwright.acquisition_targets (run_id, workspace_id, position, "
                "route, "
                "url, status) VALUES (%(run)s, %(ws)s, 0, 'fetch', %(url)s, 'blocked')",
                {"run": run, "ws": workspace, "url": unsafe},
            )
            tx.exec_driver_sql(
                "INSERT INTO careerwright.source_attempts (attempt_id, workspace_id, run_id, "
                "position, "
                "route, provider, requested_url, redirects, status, reason, finished_at) VALUES "
                "(%(id)s, %(ws)s, %(run)s, 0, 'fetch', 'unknown', %(url)s, %(redirects)s::jsonb, "
                "'blocked', 'scheme_not_allowed', clock_timestamp())",
                {
                    "id": attempt,
                    "ws": workspace,
                    "run": run,
                    "url": unsafe,
                    "redirects": json.dumps(["https://ok.example/a", "file:///etc/passwd"]),
                },
            )

        migrate_app(engine)
    finally:
        engine.dispose()

    [target] = infra.query(
        "SELECT url, refusal FROM careerwright.acquisition_targets", database=database
    )
    [kept] = infra.query(
        "SELECT requested_url, redirects, status, reason FROM careerwright.source_attempts",
        database=database,
    )
    assert target == {"url": None, "refusal": "scheme_not_allowed"}
    assert kept == {
        "requested_url": None,
        "redirects": ["https://ok.example/a"],
        "status": "blocked",
        "reason": "scheme_not_allowed",
    }
