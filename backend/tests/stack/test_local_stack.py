"""The Compose stack as `make demo` runs it: healthy, loopback-only, offline, restartable.

These tests drive real containers through their published ports, the way a browser would.
"""

import json
import socket
import subprocess
import threading
import time
import uuid
from collections.abc import Iterator
from typing import Any

import httpx2 as httpx
import psycopg
import pytest

from nessa.profile.document import FIELD_NAMES
from nessa.seed import FIXTURE_WORKSPACE_ID
from tools.localenv import REPO_ROOT as REPO
from tools.localenv import add_master_key_version
from tools.stack import CORE_SERVICES, Stack, reseal, rotate_master_key

pytestmark = pytest.mark.stack

PROFILE_FIELDS = FIELD_NAMES


def sign_in(stack: Stack, handle: str) -> str:
    response = httpx.post(
        f"{stack.auth_url}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
        params={"key": "emulator"},
        json={
            "email": f"{handle}@nessa.test",
            "password": f"nessa-demo-{handle}",
            "returnSecureToken": True,
        },
        timeout=10,
    )
    response.raise_for_status()
    return str(response.json()["idToken"])


def call(stack: Stack, method: str, path: str, token: str, body: Any = None) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"}
    if method != "GET":
        headers |= {"Origin": stack.web_origin, "Idempotency-Key": str(uuid.uuid4())}
    return httpx.request(method, f"{stack.api_url}{path}", json=body, headers=headers, timeout=20)


def profile(cities: list[str]) -> dict[str, Any]:
    fields: dict[str, Any] = {name: {"state": "unasked"} for name in PROFILE_FIELDS}
    fields["cities"] = {"state": "provided", "value": cities}
    return fields


@pytest.mark.req("BND1-13")
def test_only_the_edge_publishes_ports_and_only_on_loopback(demo_stack: Stack) -> None:
    bindings: dict[str, list[str]] = {}
    for service in CORE_SERVICES:
        inspected = subprocess.run(  # noqa: S603
            ["docker", "inspect", demo_stack.container_id(service)],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        ports = json.loads(inspected.stdout)[0]["NetworkSettings"]["Ports"] or {}
        bindings[service] = [
            binding["HostIp"] for published in ports.values() if published for binding in published
        ]

    assert {service for service, ips in bindings.items() if ips} == {"edge"}
    assert set(bindings["edge"]) == {"127.0.0.1"}
    assert httpx.get(f"{demo_stack.api_url}/readyz", timeout=10).json() == {"status": "ready"}


@pytest.fixture
def host_listener() -> Iterator[tuple[int, list[bool]]]:
    """A TCP listener on the host's loopback: the 'outside world' for the egress probe."""
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen()
    server.settimeout(0.5)
    accepted: list[bool] = []
    stop = threading.Event()

    def accept() -> None:
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except TimeoutError:
                continue
            accepted.append(True)
            conn.close()

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    yield server.getsockname()[1], accepted
    stop.set()
    thread.join(timeout=5)
    server.close()


# RFC 5737 documentation address: never routed anywhere, so a probe never contacts the
# internet. Only a container with no route at all fails it at once ("unreachable").
TEST_NET = "192.0.2.1"

PYTHON_PROBE = """
import json, socket
result = {}
for name, target in TARGETS:
    try:
        socket.create_connection(target, timeout=4).close()
        result[name] = "connected"
    except OSError as error:
        result[name] = type(error).__name__
if OUTSIDE:
    try:
        socket.getaddrinfo("example.com", 443)
        result["dns"] = "resolved"
    except OSError as error:
        result["dns"] = type(error).__name__
print(json.dumps(result))
"""

NODE_PROBE = (
    "const net=require('net'),dns=require('dns');const t=(h,p)=>new Promise(r=>{const s="
    "net.connect({host:h,port:p,timeout:4000});s.on('connect',()=>{s.destroy();r('connected')});"
    "s.on('error',"
    "e=>r(e.code));s.on('timeout',()=>{s.destroy();r('timeout')})});const d=new Promise(r=>dns."
    "lookup('example.com',e=>r(e?e.code:'resolved')));Promise.all([t('TEST_NET',443),"
    "t('host.docker.internal',PORT),d]).then(([a,b,c])=>console.log(JSON.stringify({outside:a,"
    "host:b,dns:c})))"
)

BASH_PROBE = (
    "for t in TEST_NET/443 host.docker.internal/PORT; do "
    'if timeout 4 bash -c "exec 3<>/dev/tcp/$t" 2>/dev/null; then echo "$t connected"; '
    'else echo "$t blocked"; fi; done'
)


def probe(stack: Stack, service: str, port: int, *, outside: bool = True) -> str:
    """Connect to the host listener and, when `outside`, to TEST_NET and resolve a public
    name through the container's resolver. The host listener is the egress evidence; the
    edge control and the live-mode worker have a real route, so they probe the host only."""
    if service in ("api", "edge", "worker"):
        targets = [("host", ("host.docker.internal", port))]
        if outside:
            targets.append(("outside", (TEST_NET, 443)))
        script = PYTHON_PROBE.replace("TARGETS", repr(targets)).replace("OUTSIDE", str(outside))
        command = ["python", "-c", script]
    elif service in ("auth", "web"):
        command = [
            "node",
            "-e",
            NODE_PROBE.replace("PORT", str(port)).replace("TEST_NET", TEST_NET),
        ]
    else:
        command = [
            "bash",
            "-c",
            BASH_PROBE.replace("PORT", str(port)).replace("TEST_NET", TEST_NET),
        ]
    return stack.exec(service, *command, timeout=60).stdout.strip()


@pytest.mark.req("BND1-11")
def test_demo_mode_services_have_no_route_out_and_the_probe_can_see_one(
    demo_stack: Stack, host_listener: tuple[int, list[bool]]
) -> None:
    port, accepted = host_listener

    # Positive control: the same probe from the edge, the one container on a normal bridge,
    # reaches the host listener. So a "blocked" result below is not a broken probe.
    control = json.loads(probe(demo_stack, "edge", port, outside=False))
    assert control["host"] == "connected"
    assert accepted

    accepted.clear()
    services = ("api", "worker", "auth", "web", "postgres")
    results = {service: probe(demo_stack, service, port) for service in services}

    assert "connected" not in results["postgres"], results
    for service in ("api", "worker", "auth", "web"):
        outcome = json.loads(results[service])
        assert outcome["outside"] != "connected", (service, outcome)
        assert outcome["host"] != "connected", (service, outcome)
    for service in ("api", "worker", "auth", "web"):
        assert json.loads(results[service])["dns"] != "resolved", service
    assert accepted == []  # nothing reached the host from inside the internal network


@pytest.mark.req("BND1-11")
def test_live_mode_gives_the_worker_and_only_the_worker_a_route_out(
    demo_stack: Stack, host_listener: tuple[int, list[bool]]
) -> None:
    port, accepted = host_listener
    live = Stack(
        project=demo_stack.project, home=demo_stack.home, ports=demo_stack.ports, live=True
    )
    live.up(*CORE_SERVICES)
    try:
        worker = json.loads(probe(live, "worker", port, outside=False))
        assert worker["host"] == "connected"
        assert accepted
        accepted.clear()
        api = json.loads(probe(live, "api", port, outside=False))
        web = json.loads(probe(live, "web", port))
        assert api["host"] != "connected"
        assert web["host"] != "connected"
        assert web["outside"] != "connected"
        assert web["dns"] != "resolved"
        assert accepted == []
    finally:
        demo_stack.up(*CORE_SERVICES)  # back to demo for the remaining tests
    assert json.loads(probe(demo_stack, "worker", port, outside=False))["host"] != "connected"


@pytest.mark.req("ARC1-08")
def test_the_containerised_worker_runs_dbos_as_the_non_owner_runtime_role(
    demo_stack: Stack,
) -> None:
    logs = demo_stack.logs("worker")

    password = (demo_stack.home / "secrets" / "pg_dbos_runtime").read_text().strip()

    assert '"msg": "worker ready"' in logs
    assert "nessa_dbos_runtime:[redacted]@postgres:5432/nessa_dbos" in logs
    assert password not in logs
    assert demo_stack.exec("worker", "python", "-m", "nessa.worker", "--check").returncode == 0


@pytest.mark.req("BND1-14", "STATE-07")
def test_a_profile_edit_survives_a_full_stop_and_start(demo_stack: Stack) -> None:
    ada = sign_in(demo_stack, "ada")
    created = call(
        demo_stack,
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Survives restart", "data_mode": "live_assisted", "synthetic": True},
    )
    workspace_id = created.json()["workspace_id"]
    saved = call(
        demo_stack,
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        ada,
        {"expected_version": 0, "profile": profile(["Leeds", "York"])},
    )
    assert saved.status_code == 201

    started = time.monotonic()
    outcome = demo_stack.stop()
    stopped_in = time.monotonic() - started
    demo_stack.up(*CORE_SERVICES)

    reopened = call(
        demo_stack, "GET", f"/v1/workspaces/{workspace_id}/profile", sign_in(demo_stack, "ada")
    )
    assert (reopened.json()["version"], reopened.json()["document"]["cities"]["value"]) == (
        1,
        ["Leeds", "York"],
    )
    assert outcome == "stopped"
    assert stopped_in < 60


@pytest.mark.req("TAX1-04", "DIV1-01")
def test_setup_imports_the_full_pinned_esco_release_into_the_stack(demo_stack: Stack) -> None:
    ada = sign_in(demo_stack, "ada")

    release = call(demo_stack, "GET", "/v1/taxonomy", ada).json()
    found = call(demo_stack, "GET", "/v1/taxonomy/occupations?q=plumber", ada).json()

    assert (release["dataset_id"], release["sample"], release["occupation_count"]) == (
        "esco-v1.2.1-en-csv",
        False,
        3_039,
    )
    assert release["sha256"] == "f9761b0b52be1828b38a3e5e0ae59a93a7b0ce358bc800f52f57a8b002adeb3e"
    # "plumber" is an occupation and an alternative label of another (pipe welder): both.
    assert {m["preferred_label"] for m in found["label_matches"]} == {"plumber", "pipe welder"}


@pytest.mark.req("BND1-11", "TEST1-10")
def test_a_demo_workspace_interviews_through_the_offline_worker(demo_stack: Stack) -> None:
    ada = sign_in(demo_stack, "ada")
    workspace = call(
        demo_stack,
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Offline interview", "data_mode": "demo", "synthetic": True},
    ).json()["workspace_id"]

    submitted = call(
        demo_stack,
        "POST",
        f"/v1/workspaces/{workspace}/interview/turns",
        ada,
        {"expected_profile_version": 0, "message": "I could work in York, 4 hours a week."},
    )
    assert submitted.status_code == 202, submitted.text
    path = f"/v1/workspaces/{workspace}/interview/turns/{submitted.json()['turn_id']}"
    deadline = time.monotonic() + 60
    turn = call(demo_stack, "GET", path, ada).json()
    while turn["run"]["status"] in ("queued", "running") and time.monotonic() < deadline:
        time.sleep(0.5)
        turn = call(demo_stack, "GET", path, ada).json()

    assert (turn["run"]["status"], turn["run"]["model_mode"]) == ("complete", "fixture")
    assert turn["proposal"]["origin"] == "fixture"
    assert {c["field"] for c in turn["proposal"]["changes"]} == {"cities", "weekly_study_hours"}


def superuser_query(stack: Stack, statement: str) -> list[tuple[Any, ...]]:
    password = (stack.home / "secrets" / "pg_superuser").read_text().strip()
    url = f"postgresql://postgres:{password}@127.0.0.1:{stack.ports.postgres}/nessa_app"
    with psycopg.connect(url) as conn:
        return conn.execute(statement.encode()).fetchall()


def networks_of(stack: Stack, service: str) -> set[str]:
    inspected = subprocess.run(  # noqa: S603
        ["docker", "inspect", stack.container_id(service)],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return set(json.loads(inspected.stdout)[0]["NetworkSettings"]["Networks"])


NETWORKS_SEEN_BY = (
    "import json; from nessa.localnet import {name}, ROUTE_TABLE; "
    "print(json.dumps([str(n) for n in {call}]))"
)


@pytest.mark.req("BND1-13")
def test_the_edge_relays_only_into_the_internal_network_and_refuses_an_absent_target(
    demo_stack: Stack,
) -> None:
    inspected = subprocess.run(  # noqa: S603
        ["docker", "network", "inspect", f"{demo_stack.project}_internal"],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    subnets = [c["Subnet"] for c in json.loads(inspected.stdout)[0]["IPAM"]["Config"]]
    edge_view = demo_stack.exec(
        "edge",
        "python",
        "-c",
        NETWORKS_SEEN_BY.format(
            name="internal_networks", call="internal_networks(ROUTE_TABLE.read_text())"
        ),
    )
    # What the running API's own configuration makes it serve (N4: opted in by compose).
    api_view = demo_stack.exec(
        "api",
        "python",
        "-c",
        "import json; from nessa.config import ApiSettings; "
        "from nessa.localnet import client_networks; print(json.dumps([str(n) for n in "
        "client_networks(internal=ApiSettings().internal_network_clients)]))",
    )

    # With the web service running, the edge relays its port into the internal network.
    served = httpx.get(f"{demo_stack.web_origin}/sign-in", timeout=20)
    # Stopped, its name is absent: Docker's DNS would forward that name upstream, and the edge
    # must refuse it, not follow the answer.
    demo_stack.compose("stop", "web", timeout=60)
    try:
        with socket.create_connection(("127.0.0.1", demo_stack.ports.web), timeout=5) as conn:
            conn.settimeout(15)
            conn.sendall(b"POST /v1/credentials HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
            try:
                answer = conn.recv(1)
            except ConnectionResetError:
                answer = b""
    finally:
        demo_stack.up("web")

    assert served.status_code == 200
    assert json.loads(edge_view.stdout) == subnets
    assert json.loads(api_view.stdout) == ["127.0.0.0/8", "::1/128", *subnets]
    assert answer == b""
    assert "edge refused web:3000: unresolved or outside the internal network" in (
        demo_stack.logs("edge")
    )


COMMITTED_OPENAPI = REPO / "apps" / "web" / "src" / "generated" / "openapi.json"


@pytest.mark.req("BND1-13", "ARC1-10")
def test_the_web_origin_serves_the_app_and_forwards_only_the_api_with_its_checks(
    demo_stack: Stack,
) -> None:
    web = demo_stack.web_origin
    page = httpx.get(f"{web}/sign-in", timeout=20)
    rebound = httpx.get(f"{web}/sign-in", headers={"Host": "rebound.example"}, timeout=20)
    unauthenticated = httpx.get(f"{web}/api/v1/me", timeout=20)
    not_forwarded = httpx.get(f"{web}/api/openapi.json", timeout=20)
    ada = sign_in(demo_stack, "ada")
    foreign = httpx.put(
        f"{web}/api/v1/workspaces/{FIXTURE_WORKSPACE_ID}/profile",
        headers={
            "Authorization": f"Bearer {ada}",
            "Origin": "http://127.0.0.1:1",
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"expected_version": 1, "profile": {}},
        timeout=20,
    )
    served_schema = httpx.get(f"{demo_stack.api_url}/openapi.json", timeout=20).json()

    assert page.status_code == 200
    assert "connect-src 'self' " + demo_stack.auth_url in page.headers["content-security-policy"]
    assert rebound.status_code == 400
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "UNAUTHENTICATED"
    assert unauthenticated.headers["x-correlation-id"]
    assert not_forwarded.status_code == 404
    assert foreign.status_code == 403
    assert foreign.json()["error"]["code"] == "ORIGIN_NOT_ALLOWED"
    # The client was generated from exactly what the running API serves.
    assert served_schema == json.loads(COMMITTED_OPENAPI.read_text(encoding="utf-8"))


@pytest.mark.req("MODEL-05")
def test_master_key_rotation_reloads_the_running_api_reseals_and_keeps_demo_offline(
    demo_stack: Stack,
) -> None:
    ada = sign_in(demo_stack, "ada")
    workspace_id = call(
        demo_stack,
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Rotation", "data_mode": "live_assisted", "synthetic": True},
    ).json()["workspace_id"]
    base = f"/v1/workspaces/{workspace_id}/credentials"
    first = call(
        demo_stack,
        "POST",
        base,
        ada,
        {"api_key": "a" * 40, "consent_to_encrypted_storage": True},
    ).json()
    assert {
        row[0] for row in superuser_query(demo_stack, "SELECT key_version FROM nessa.credentials")
    } == {1}

    created = rotate_master_key(demo_stack)

    assert created == "keys/v2.key"
    assert {
        row[0] for row in superuser_query(demo_stack, "SELECT key_version FROM nessa.credentials")
    } == {2}
    # The restarted API seals with the new version: a rotated user key lands on v2 too.
    rotated = call(
        demo_stack,
        "POST",
        f"{base}/{first['credential_id']}/rotate",
        sign_in(demo_stack, "ada"),
        {"api_key": "b" * 40, "consent_to_encrypted_storage": True},
    )
    assert rotated.status_code == 201
    new_id = uuid.UUID(rotated.json()["credential_id"])  # parsed, so safe to embed
    versions = superuser_query(
        demo_stack,
        f"SELECT key_version FROM nessa.credentials WHERE credential_id = '{new_id}'",  # noqa: S608
    )
    assert versions == [(2,)]
    # `restart` kept the demo configuration: the worker still has no route out.
    assert networks_of(demo_stack, "worker") == {f"{demo_stack.project}_internal"}


def key_versions(stack: Stack) -> set[int]:
    return {row[0] for row in superuser_query(stack, "SELECT key_version FROM nessa.credentials")}


@pytest.mark.req("MODEL-05")
def test_reseal_after_an_interrupted_rotation_reloads_the_running_api_first(
    demo_stack: Stack,
) -> None:
    """N3: a rotation that added its key but stopped before the restart, then `make reseal`.
    Records move to the new version, so the running API must hold it too: it seals a key
    stored afterwards with that version (and could open every resealed record)."""
    ada = sign_in(demo_stack, "ada")
    workspace_id = call(
        demo_stack,
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Interrupted rotation", "data_mode": "live_assisted", "synthetic": True},
    ).json()["workspace_id"]
    created = add_master_key_version(demo_stack.home)  # the interrupted rotation's first step
    newest = int(created.removeprefix("keys/v").removesuffix(".key"))

    reseal(demo_stack)

    assert key_versions(demo_stack) == {newest}
    stored = call(
        demo_stack,
        "POST",
        f"/v1/workspaces/{workspace_id}/credentials",
        sign_in(demo_stack, "ada"),
        {"api_key": "c" * 40, "consent_to_encrypted_storage": True},
    )
    assert stored.status_code == 201
    assert key_versions(demo_stack) == {newest}
    assert networks_of(demo_stack, "worker") == {f"{demo_stack.project}_internal"}


@pytest.mark.req("BND1-14")
def test_reset_demo_restores_the_fixture_and_touches_nothing_else(demo_stack: Stack) -> None:
    ada = sign_in(demo_stack, "ada")
    fixture = f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}"
    call(
        demo_stack,
        "PUT",
        f"{fixture}/profile",
        ada,
        {"expected_version": 1, "profile": profile(["York"])},
    )
    other_id = call(
        demo_stack,
        "POST",
        "/v1/workspaces",
        ada,
        {"name": "Not the fixture", "data_mode": "demo", "synthetic": True},
    ).json()["workspace_id"]
    call(
        demo_stack,
        "PUT",
        f"/v1/workspaces/{other_id}/profile",
        ada,
        {"expected_version": 0, "profile": profile(["Bath"])},
    )
    events_before = call(demo_stack, "GET", f"{fixture}/events", ada).json()["last_seq"]

    demo_stack.run("migrate", "python", "-m", "nessa.cli", "reset-demo")

    restored = call(demo_stack, "GET", f"{fixture}/profile", ada).json()
    assert (restored["version"], restored["document"]["cities"]["value"]) == (1, ["Manchester"])
    kept = call(demo_stack, "GET", f"/v1/workspaces/{other_id}/profile", ada).json()
    assert kept["document"]["cities"]["value"] == ["Bath"]
    events = call(
        demo_stack,
        "GET",
        f"{fixture}/events",
        ada,
    ).json()["items"]
    assert events[0]["seq"] > events_before  # numbering continues; a resuming client sees it
    assert events[0]["kind"] == "workspace.reset"


@pytest.mark.req("SEC-03")
@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("NESSA_ENVIRONMENT", "production"),
        ("NESSA_FIREBASE_PROJECT_ID", "nessa-real-project"),
        ("NESSA_ALLOWED_HOSTS", "0.0.0.0:8000"),
        ("FIREBASE_AUTH_EMULATOR_HOST", "auth.example.com:9099"),
    ],
)
def test_the_api_refuses_to_start_with_unsafe_configuration(
    demo_stack: Stack, variable: str, value: str
) -> None:
    result = demo_stack.compose(
        "run",
        "--rm",
        "--no-deps",
        "-e",
        f"{variable}={value}",
        "api",
        "python",
        "-c",
        "from nessa.api.main import build_app; build_app()",
        timeout=120,
        check=False,
    )

    assert result.returncode != 0
    assert "ValidationError" in result.stderr + result.stdout
