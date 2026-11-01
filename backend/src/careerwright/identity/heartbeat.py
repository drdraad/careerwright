"""The DBOS worker's heartbeat: the worker touches a file after each good pass, and the
container's health check reads its age.

Standard library only, so the health check (`python -m careerwright.identity.heartbeat`,
compose.yaml) starts within its few-second timeout. Importing the worker itself (DBOS,
Pydantic AI, every run kind) took longer than that on a slower Linux Docker host, so Docker
marked a working worker unhealthy and the stack never came up.
"""

import os
import sys
import time
from pathlib import Path

HEARTBEAT_FILE = Path(
    os.environ.get("CAREERWRIGHT_WORKER_HEARTBEAT", "/tmp/careerwright-worker-heartbeat")  # noqa: S108
)
HEARTBEAT_STALE_S = 15.0


def beat(path: Path = HEARTBEAT_FILE) -> None:
    path.touch()


def check(path: Path = HEARTBEAT_FILE, *, now: float | None = None) -> int:
    """0 when the worker's last good pass is recent, else 1 (a missing file included)."""
    try:
        age = (time.time() if now is None else now) - path.stat().st_mtime
    except OSError:
        return 1
    return 0 if age < HEARTBEAT_STALE_S else 1


if __name__ == "__main__":
    sys.exit(check())
