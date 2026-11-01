"""The product owner's own command in the acceptance run (R14; Task 3b): `make demo`, exactly
as they type it, on its own Compose project, ports and CAREERWRIGHT_HOME, so the real stack is
never touched. It starts every service and the app answers at the address it prints; after the
live tools write their private evidence into CAREERWRIGHT_HOME it still starts (ledger 569: a
file one wrote readable by others made `make demo` refuse)."""

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import httpx2
import pytest

from tools.live_eval import Plan, write_results
from tools.localenv import REPO_ROOT
from tools.stack import CORE_SERVICES, Ports, Stack

pytestmark = pytest.mark.stack
PROJECT = "careerwright-l0-democheck"
PORTS = Ports(api=57200, auth=57299, postgres=57632, web=57500)


@pytest.fixture
def home(tmp_path: Path, demo_stack: Stack) -> Iterator[Path]:
    """A fresh CAREERWRIGHT_HOME; `demo_stack` has built this checkout's images first."""
    home = tmp_path / "careerwright-home"
    try:
        yield home
    finally:
        Stack(project=PROJECT, home=home, ports=PORTS, live=False).down()


def _make_demo(home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "demo"],  # noqa: S607 - the product owner's own command, no shell
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "CAREERWRIGHT_PROJECT": PROJECT,
            "CAREERWRIGHT_HOME": str(home),
            "CAREERWRIGHT_API_PORT": str(PORTS.api),
            "CAREERWRIGHT_AUTH_PORT": str(PORTS.auth),
            "CAREERWRIGHT_PG_PORT": str(PORTS.postgres),
            "CAREERWRIGHT_WEB_PORT": str(PORTS.web),
        },
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )


@pytest.mark.req("BND1-14")
def test_make_demo_as_the_product_owner_types_it_starts_the_app(home: Path, tmp_path: Path) -> None:
    first = _make_demo(home)

    assert first.returncode == 0, first.stderr[-2000:]
    web = f"http://127.0.0.1:{PORTS.web}"
    assert f"Careerwright:         {web}" in first.stdout
    assert "Demo mode: no Careerwright service has a route out of this machine." in first.stdout
    stack = Stack(project=PROJECT, home=home, ports=PORTS, live=False)
    assert set(CORE_SERVICES) <= stack.running()
    assert httpx2.get(f"{web}/healthz", timeout=10).status_code == 200

    # A live tool's private evidence, as `make live-eval` writes it into CAREERWRIGHT_HOME.
    plan = Plan("muse-spark-1.3-contributor", [], calls=0, worst_case_nano_usd=0)
    observations = home / "evidence" / "live-eval.jsonl"
    write_results(tmp_path / "results.md", observations, plan, [], {}, [], "democheck")
    again = _make_demo(home)

    assert again.returncode == 0, again.stderr[-2000:]
