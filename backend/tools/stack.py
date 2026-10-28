"""Drive the Docker Compose stack: the make targets and the acceptance tests use this module.

Every docker call runs with a timeout, so no command can hang (`make stop` included: a
service that ignores SIGTERM is killed, and DBOS recovers its in-flight work on the next
start). Secrets travel only as files under NESSA_HOME; compose output never contains them.

Run from `backend/`: `uv run python -m tools.stack {dev,demo,stop,reset-demo,status}`.
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from nessa.seed import FIXTURE_WORKSPACE_ID
from tools.localenv import REPO_ROOT, ensure_local_home, nessa_home

COMPOSE_FILE = REPO_ROOT / "compose.yaml"
LIVE_OVERRIDE = REPO_ROOT / "compose.live.yaml"
DEFAULT_PROJECT = "nessa-l0"
CORE_SERVICES = ("postgres", "auth", "edge", "api", "worker")
STOP_TIMEOUT_S = 10
COMMAND_TIMEOUT_S = 600.0


@dataclass(frozen=True)
class Ports:
    api: int = 58000
    auth: int = 59099
    postgres: int = 56432
    web: int = 53000


@dataclass(frozen=True)
class Stack:
    project: str = DEFAULT_PROJECT
    home: Path = field(default_factory=nessa_home)
    ports: Ports = Ports()
    live: bool = True
    overrides: tuple[tuple[str, str], ...] = ()  # extra compose variables, e.g. the model role

    @property
    def api_url(self) -> str:
        return f"http://127.0.0.1:{self.ports.api}"

    @property
    def auth_url(self) -> str:
        return f"http://127.0.0.1:{self.ports.auth}"

    @property
    def web_origin(self) -> str:
        return f"http://127.0.0.1:{self.ports.web}"

    def env(self) -> dict[str, str]:
        return {
            **os.environ,
            "NESSA_HOME": str(self.home),
            "NESSA_RUNTIME_MODE": "live" if self.live else "demo",
            "NESSA_API_PORT": str(self.ports.api),
            "NESSA_AUTH_PORT": str(self.ports.auth),
            "NESSA_PG_PORT": str(self.ports.postgres),
            "NESSA_WEB_PORT": str(self.ports.web),
            **dict(self.overrides),
        }

    def _files(self) -> list[str]:
        files = ["-f", str(COMPOSE_FILE)]
        if self.live:
            files += ["-f", str(LIVE_OVERRIDE)]
        return files

    def compose(
        self, *args: str, timeout: float = COMMAND_TIMEOUT_S, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(  # noqa: S603 - fixed docker compose invocation, no shell
            ["docker", "compose", "-p", self.project, *self._files(), *args],  # noqa: S607
            env=self.env(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if check and result.returncode != 0:
            raise RuntimeError(
                f"docker compose {' '.join(args)} failed ({result.returncode}): "
                f"{result.stderr.strip()[-2000:]}"
            )
        return result

    def up(self, *services: str, timeout: float = COMMAND_TIMEOUT_S) -> None:
        self.compose("up", "--detach", "--wait", "--no-build", *services, timeout=timeout)

    def build(self) -> None:
        self.compose("build", "--quiet", timeout=1800)

    def stop(self, services: tuple[str, ...] = ()) -> str:
        """Stop without deleting volumes, bounded: SIGTERM, SIGKILL after the grace period,
        and `kill` if even that does not return in time."""
        try:
            self.compose("stop", "--timeout", str(STOP_TIMEOUT_S), *services, timeout=90)
        except subprocess.TimeoutExpired:
            self.compose("kill", *services, timeout=30, check=False)
            return "killed after the stop deadline"
        return "stopped"

    def down(self) -> None:
        """Tests only: remove containers, networks and this project's volumes."""
        self.compose("down", "--volumes", "--remove-orphans", "--timeout", "5", timeout=120)

    def run(
        self, service: str, *command: str, timeout: float = 300
    ) -> subprocess.CompletedProcess[str]:
        return self.compose("run", "--rm", "--no-deps", service, *command, timeout=timeout)

    def exec(
        self, service: str, *command: str, timeout: float = 60
    ) -> subprocess.CompletedProcess[str]:
        return self.compose("exec", "-T", service, *command, timeout=timeout, check=False)

    def logs(self, *services: str) -> str:
        return self.compose("logs", "--no-color", "--no-log-prefix", *services, timeout=60).stdout

    def container_id(self, service: str) -> str:
        return self.compose("ps", "--all", "--quiet", service, timeout=30).stdout.strip()


def _start(stack: Stack, mode: str) -> None:
    ensure_local_home(stack.home)
    print(f"starting Nessa ({mode} mode, project {stack.project})...", flush=True)
    stack.up(*CORE_SERVICES)
    print(f"API:           {stack.api_url}  (OpenAPI at {stack.api_url}/openapi.json)")
    print(f"Auth emulator: {stack.auth_url}  (project demo-nessa)")
    print(f"Web:           {stack.web_origin}  (the Next.js app arrives in Task 4)")
    print("Sign in as ada@nessa.test or ben@nessa.test (password: nessa-demo-<name>).")
    print(f"Fixture workspace (owned by Ada): {stack.api_url}/v1/workspaces/{FIXTURE_WORKSPACE_ID}")
    if mode == "demo":
        print("Demo mode: no Nessa service has a route out of this machine.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("dev", "demo", "stop", "reset-demo", "status", "build"))
    args = parser.parse_args(argv)
    match args.command:
        case "dev":
            _start(Stack(live=True), "live")
        case "demo":
            _start(Stack(live=False), "demo")
        case "stop":
            print(f"Nessa {Stack().stop()}; volumes and data are kept.")
        case "reset-demo":
            Stack().run("migrate", "python", "-m", "nessa.cli", "reset-demo")
            print("fixture workspace reset; other workspaces untouched.")
        case "status":
            print(Stack().compose("ps", "--all").stdout)
        case "build":
            Stack().build()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
