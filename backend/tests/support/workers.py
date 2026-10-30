"""Worker processes for integration tests (ported from the Sprint 0 spike harness).

`stop()` sends SIGTERM and waits; a worker that does not exit in time is killed, never left
running, and the test fails, because shutdown must be bounded.
"""

import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

from tests.support.infra import Infra
from tools.localenv import REPO_ROOT

BACKEND = REPO_ROOT / "backend"


class WorkerShutdownTimeoutError(RuntimeError):
    """A worker did not exit after SIGTERM within the allowed time (it has been killed)."""


@dataclass
class Worker:
    process: subprocess.Popen[bytes]
    log_path: Path
    _log: IO[bytes] = field(repr=False)

    def kill(self) -> None:
        self.process.kill()
        self.process.wait(timeout=10)
        self._log.close()

    def stop(self, timeout_s: float = 20.0) -> int:
        self.process.terminate()
        try:
            code = self.process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            self.kill()
            raise WorkerShutdownTimeoutError(
                f"worker ignored SIGTERM for {timeout_s}s and was killed; see {self.log_path}"
            ) from None
        self._log.close()
        return code

    def kill_if_running(self) -> None:
        if self.process.poll() is None:
            self.kill()

    def wait_exit(self, timeout_s: float) -> int:
        code = self.process.wait(timeout=timeout_s)
        self._log.close()
        return code


def start_worker(
    infra: Infra, log_path: Path, *, acquisition_url: str | None = None, **settings: str
) -> Worker:
    """`acquisition_url`: a test-started acquisition worker for the DBOS worker to call."""
    env = {
        **infra.worker_env(),
        "CAREERWRIGHT_WORKER_HEARTBEAT": str(log_path.with_suffix(".heartbeat")),
        "PYDANTIC_AI_NO_BANNER": "1",
        **({"CAREERWRIGHT_ACQUISITION_URL": acquisition_url} if acquisition_url else {}),
        **{f"CAREERWRIGHT_TEST_{name.upper()}": value for name, value in settings.items()},
    }
    log = log_path.open("ab")
    process = subprocess.Popen(
        [sys.executable, "-m", "tests.support.worker_entry"],
        cwd=BACKEND,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    return Worker(process, log_path, log)


def wait_for(predicate: Callable[[], bool], *, timeout_s: float, what: str) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise TimeoutError(f"timed out after {timeout_s}s waiting for {what}")
