"""Create the local runtime configuration outside the repository, safely (plan: `make setup`).

`NESSA_HOME` (default `~/.nessa/l0`) holds generated database passwords and the versioned
master keys. Both directories are owner-only (0700) and every file 0600. Existing files are
never overwritten: replacing a master key would make every stored credential unreadable, and
replacing a password would no longer match the database volume. Nothing here is printed.

Run: `uv run python -m tools.localenv [--rotate-master-key]`.
"""

import argparse
import os
import secrets
import stat
import sys
from pathlib import Path

from nessa.identity.keyring import KEY_BYTES

DEFAULT_HOME = Path.home() / ".nessa" / "l0"
PASSWORD_NAMES = (
    "pg_superuser",
    "pg_migrator",
    "pg_api",
    "pg_worker",
    "pg_dbos_owner",
    "pg_dbos_runtime",
)
REPO_ROOT = Path(__file__).resolve().parents[2]


def nessa_home() -> Path:
    return Path(os.environ.get("NESSA_HOME", DEFAULT_HOME)).expanduser().resolve()


def _private_dir(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)


def _write_new(path: Path, content: bytes) -> bool:
    """Create `path` 0600 with `content` unless it exists. Returns whether it was created."""
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "wb") as handle:
        handle.write(content)
    return True


def _key_versions(keys: Path) -> list[int]:
    return sorted(int(p.stem[1:]) for p in keys.glob("v*.key") if p.stem[1:].isdigit())


def ensure_local_home(home: Path) -> list[str]:
    """Create whatever is missing; return the names of files created (never their contents)."""
    if home.is_relative_to(REPO_ROOT):
        raise SystemExit(f"NESSA_HOME must be outside the repository ({REPO_ROOT})")
    created: list[str] = []
    for directory in (home, home / "secrets", home / "keys"):
        _private_dir(directory)
    for name in PASSWORD_NAMES:
        if _write_new(home / "secrets" / name, secrets.token_urlsafe(32).encode()):
            created.append(f"secrets/{name}")
    if not _key_versions(home / "keys") and _write_new(
        home / "keys" / "v1.key", secrets.token_bytes(KEY_BYTES)
    ):
        created.append("keys/v1.key")
    check_permissions(home)
    return created


def add_master_key_version(home: Path) -> str:
    """Rotation step 1: a new current master key. `make rotate-master-key` runs it, reloads
    the API and worker, and reseals; `make reseal` alone finishes an interrupted rotation."""
    keys = home / "keys"
    version = max(_key_versions(keys), default=0) + 1
    if not _write_new(keys / f"v{version}.key", secrets.token_bytes(KEY_BYTES)):
        raise SystemExit(f"keys/v{version}.key already exists")
    return f"keys/v{version}.key"


def check_permissions(home: Path) -> None:
    others = stat.S_IRWXG | stat.S_IRWXO
    for path in (home, home / "secrets", home / "keys", *home.glob("*/*")):
        if path.stat().st_mode & others:
            raise SystemExit(f"{path} is readable by other users; chmod it owner-only")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rotate-master-key", action="store_true")
    args = parser.parse_args(argv)
    home = nessa_home()
    created = ensure_local_home(home)
    if args.rotate_master_key:
        created.append(add_master_key_version(home))
    print(f"local configuration: {home} ({', '.join(created) or 'already complete'})")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
