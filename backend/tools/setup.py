"""`make setup`: check prerequisites, create the local configuration, fetch and verify the
pinned datasets (ESCO), build the images.

Run from `backend/` after `uv sync --locked`: `uv run --locked python -m tools.setup`.
Network access is allowed here (downloads, image builds); nothing after setup needs it in
demo mode.
"""

import re
import shutil
import subprocess
import sys

from tools import datasets
from tools.localenv import ensure_local_home, nessa_home
from tools.stack import Stack

PNPM_VERSION = "10.33.2"
NODE_MAJOR = 24


def _version(*command: str) -> str:
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)  # noqa: S603
    if result.returncode != 0:
        raise SystemExit(f"`{' '.join(command)}` failed; is it installed?")
    return result.stdout.strip()


def check_prerequisites() -> list[str]:
    problems = []
    for tool in ("docker", "uv", "pnpm", "node"):
        if shutil.which(tool) is None:
            problems.append(f"{tool} is not on PATH")
    if problems:
        return problems
    if not re.search(r"v2\.", _version("docker", "compose", "version")):
        problems.append("Docker Compose v2 is required")
    daemon = subprocess.run(["docker", "info"], capture_output=True, timeout=30, check=False)  # noqa: S607
    if daemon.returncode != 0:
        problems.append("the Docker daemon is not running")
    if _version("pnpm", "--version") != PNPM_VERSION:
        problems.append(f"pnpm {PNPM_VERSION} is required (corepack prepare pnpm@{PNPM_VERSION})")
    node = re.match(r"v(\d+)\.", _version("node", "--version"))
    if node is None or int(node.group(1)) != NODE_MAJOR:
        problems.append(f"Node.js {NODE_MAJOR} LTS is required")
    return problems


def main() -> None:
    problems = check_prerequisites()
    if problems:
        print("setup cannot continue:\n  - " + "\n  - ".join(problems), file=sys.stderr)
        raise SystemExit(1)
    created = ensure_local_home(nessa_home())
    print(f"local configuration in {nessa_home()}: {', '.join(created) or 'already complete'}")
    datasets.main([])  # exits non-zero, with the manual step, if a pinned file cannot be had
    print("building images (locked dependencies)...", flush=True)
    Stack().build()
    print("setup complete. Next: `make dev` (live) or `make demo` (offline).")


if __name__ == "__main__":
    main()
