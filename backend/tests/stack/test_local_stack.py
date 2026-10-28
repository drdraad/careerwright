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
import pytest

from nessa.seed import FIXTURE_WORKSPACE_ID
from tools.stack import CORE_SERVICES, Stack

pytestmark = pytest.mark.stack

PROFILE_FIELDS = (
    "preferred_name",
    "current_role",
    "cities",
    "target_titles",
    "weekly_study_hours",
    "direct_spend_cap",
    "monthly_payment_cap",
)


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


PYTHON_PROBE = """
import json, socket
result = {}
for name, target in (("public_ip", ("1.1.1.1", 443)), ("host", ("host.docker.internal", PORT))):
    try:
        socket.create_connection(target, timeout=4).close()
        result[name] = "connected"
    except OSError as error:
        result[name] = type(error).__name__
try:
    socket.getaddrinfo("example.com", 443)
    result["dns"] = "resolved"
except OSError as error:
    result["dns"] = type(error).__name__
print(json.dumps(result))
"""

NODE_PROBE = (
    "const net=require('net');const t=(h,p)=>new Promise(r=>{const s=net.connect({host:h,port:p,"
    "timeout:4000});s.on('connect',()=>{s.destroy();r('connected')});s.on('error',e=>r(e.code));"
    "s.on('timeout',()=>{s.destroy();r('timeout')})});Promise.all([t('1.1.1.1',443),"
    "t('host.docker.internal',PORT)]).then(([a,b])=>console.log(JSON.stringify({public_ip:a,host:b})))"
)

BASH_PROBE = (
    "for t in 1.1.1.1/443 host.docker.internal/PORT; do "
    'if timeout 4 bash -c "exec 3<>/dev/tcp/$t" 2>/dev/null; then echo "$t connected"; '
    'else echo "$t blocked"; fi; done'
)


def probe(stack: Stack, service: str, port: int) -> str:
    if service in ("api", "edge"):
        command = ["python", "-c", PYTHON_PROBE.replace("PORT", str(port))]
    elif service == "auth":
        command = ["node", "-e", NODE_PROBE.replace("PORT", str(port))]
    else:
        command = ["bash", "-c", BASH_PROBE.replace("PORT", str(port))]
    return stack.exec(service, *command, timeout=60).stdout.strip()


@pytest.mark.req("BND1-11")
def test_demo_mode_services_have_no_route_out_and_the_probe_can_see_one(
    demo_stack: Stack, host_listener: tuple[int, list[bool]]
) -> None:
    port, accepted = host_listener

    # Positive control: the same probe from the edge, the one container on a normal bridge,
    # reaches the host listener. So a "blocked" result below is not a broken probe.
    control = json.loads(probe(demo_stack, "edge", port))
    assert control["host"] == "connected"
    assert accepted

    accepted.clear()
    results = {service: probe(demo_stack, service, port) for service in ("api", "auth", "postgres")}

    assert "connected" not in results["postgres"], results
    for service in ("api", "auth"):
        outcome = json.loads(results[service])
        assert outcome["public_ip"] != "connected", (service, outcome)
        assert outcome["host"] != "connected", (service, outcome)
    assert json.loads(results["api"])["dns"] != "resolved"
    assert accepted == []  # nothing reached the host from inside the internal network


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


@pytest.mark.req("BND1-14")
def test_reset_demo_restores_the_fixture_and_touches_nothing_else(demo_stack: Stack) -> None:
    ada = sign_in(demo_stack, "ada")
    fixture = f"/v1/workspaces/{FIXTURE_WORKSPACE_ID}"
    call(
        demo_stack,
        "PUT",
        f"{fixture}/profile",
        ada,
        {"expected_version": 1, "profile": profile(["Edited"])},
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
        {"expected_version": 0, "profile": profile(["Kept"])},
    )
    events_before = call(demo_stack, "GET", f"{fixture}/events", ada).json()["last_seq"]

    demo_stack.run("migrate", "python", "-m", "nessa.cli", "reset-demo")

    restored = call(demo_stack, "GET", f"{fixture}/profile", ada).json()
    assert (restored["version"], restored["document"]["cities"]["value"]) == (1, ["Manchester"])
    kept = call(demo_stack, "GET", f"/v1/workspaces/{other_id}/profile", ada).json()
    assert kept["document"]["cities"]["value"] == ["Kept"]
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
