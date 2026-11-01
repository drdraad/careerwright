"""Create the local runtime configuration outside the repository, safely (plan: `make setup`).

`CAREERWRIGHT_HOME` (default `~/.careerwright/l0`) holds generated database passwords and the
versioned master keys. Both directories are owner-only (0700) and every file 0600. Existing files
are never overwritten: replacing a master key would make every stored credential unreadable, and
replacing a password would no longer match the database volume. Nothing here is printed.

Run: `uv run python -m tools.localenv`. Master-key rotation is `make rotate-master-key` only.
"""

import argparse
import os
import re
import secrets
import stat
import sys
from pathlib import Path

from careerwright.identity.keyring import KEY_BYTES

DEFAULT_HOME = Path.home() / ".careerwright" / "l0"
PASSWORD_NAMES = (
    "pg_superuser",
    "pg_migrator",
    "pg_api",
    "pg_worker",
    "pg_dbos_owner",
    "pg_dbos_runtime",
)
REPO_ROOT = Path(__file__).resolve().parents[2]


def careerwright_home() -> Path:
    return Path(os.environ.get("CAREERWRIGHT_HOME", DEFAULT_HOME)).expanduser().resolve()


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


ADZUNA_DIR = "adzuna"
# The Adzuna credentials' names in the repository `.env`, as the product owner wrote them
# (ruling R4; controller ruling, fix round 5), and the files the acquisition worker reads
# them from (`careerwright.acquisition`;
# `test_the_acquisition_worker_reads_the_files_setup_places`).
ADZUNA_ENV = {
    "ADZUNA_APPLICATION_ID": "adzuna_application_id",
    "ADZUNA_API_KEY": "adzuna_api_key",
}
ENV_FILE = REPO_ROOT / ".env"


def ensure_local_home(home: Path) -> list[str]:
    """Create whatever is missing; return the names of files created (never their contents)."""
    if home.is_relative_to(REPO_ROOT):
        raise SystemExit(f"CAREERWRIGHT_HOME must be outside the repository ({REPO_ROOT})")
    created: list[str] = []
    for directory in (home, home / "secrets", home / "keys", home / ADZUNA_DIR):
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


def _env_values(env_file: Path, names: tuple[str, ...]) -> dict[str, str]:
    """`NAME=value` lines of a dotenv file, for the names asked for only. Read in code: the
    values are never printed or passed on a command line."""
    if not env_file.is_file():
        return {}
    found: dict[str, str] = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and name.strip() in names:
            found[name.strip()] = value.strip().strip("'\"")
    return {name: value for name, value in found.items() if value}


_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def env_names_containing(env_file: Path, fragment: str) -> list[str]:
    """The names, never the values, of the variables a dotenv file sets whose name holds
    `fragment` (case aside), sorted. A line counts only when what stands before its `=` is a
    variable name, so neither a comment nor any part of a value is taken for one. Read in
    code: nothing of the file but these names leaves this function."""
    if not env_file.is_file():
        return []
    names: set[str] = set()
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, sep, _ = line.strip().removeprefix("export ").partition("=")
        name = name.strip()
        if sep and _ENV_NAME.fullmatch(name) and fragment.lower() in name.lower():
            names.add(name)
    return sorted(names)


def place_adzuna_credentials(home: Path, env_file: Path = ENV_FILE) -> str:
    """Copy the Adzuna credentials from `.env` into CAREERWRIGHT_HOME (owner-only), where only the
    acquisition worker's container reads them. Returns what happened, never a value: both
    are needed, and a name that is absent is reported as such, never guessed."""
    values = _env_values(env_file, tuple(ADZUNA_ENV))
    missing = sorted(set(ADZUNA_ENV) - set(values))
    if missing:
        return f"blocked: Adzuna credentials not found ({', '.join(missing)} absent from .env)"
    directory = home / ADZUNA_DIR
    _private_dir(directory)
    for name, file_name in ADZUNA_ENV.items():
        path = directory / file_name
        if path.exists() and path.read_text(encoding="utf-8").strip() == values[name]:
            continue
        path.unlink(missing_ok=True)
        _write_new(path, values[name].encode())
    check_permissions(home)
    return "placed in CAREERWRIGHT_HOME/adzuna"


def adzuna_configured(home: Path) -> bool:
    """Both credential files are in place (their values are not read here)."""
    return all(
        (home / ADZUNA_DIR / name).is_file() and (home / ADZUNA_DIR / name).stat().st_size > 0
        for name in ADZUNA_ENV.values()
    )


def add_master_key_version(home: Path) -> str:
    """A new current master key: the first step of `make rotate-master-key`, which then
    reseals (`tools.stack.reseal`); `make reseal` alone finishes an interrupted rotation."""
    keys = home / "keys"
    version = max(_key_versions(keys), default=0) + 1
    if not _write_new(keys / f"v{version}.key", secrets.token_bytes(KEY_BYTES)):
        raise SystemExit(f"keys/v{version}.key already exists")
    return f"keys/v{version}.key"


def check_permissions(home: Path) -> None:
    others = stat.S_IRWXG | stat.S_IRWXO
    directories = [
        home / name for name in ("secrets", "keys", ADZUNA_DIR) if (home / name).exists()
    ]
    for path in (home, *directories, *home.glob("*/*")):
        if path.stat().st_mode & others:
            raise SystemExit(f"{path} is readable by other users; chmod it owner-only")


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    home = careerwright_home()
    created = ensure_local_home(home)
    print(f"local configuration: {home} ({', '.join(created) or 'already complete'})")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
