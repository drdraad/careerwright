"""What a session package tells the product owner to open or type works (R14; Task 3b): every
file it names exists and opens, every folder it points to holds what it names, and every
`make` command it gives exists. In `make check` and `make acceptance` (`owner_commands`)."""

import json
import re
import struct
import subprocess
from pathlib import Path

import pytest

from tools.localenv import REPO_ROOT

pytestmark = pytest.mark.owner_commands

REVIEWS = REPO_ROOT / "docs" / "reviews"
PACKAGES = sorted(REVIEWS.glob("session-*.md"))
QUOTED = re.compile(r"`([^`\n]+)`")
FILE_NAME = re.compile(r"^[\w./-]+\.(png|md|json|html|pdf|csv)$")
MAKE = re.compile(r"^make ([a-z][a-z-]*)$")
PRIVATE = ("var/",)  # gitignored private evidence: never in the repository, so not checked
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Files a held session's package names that were retired after it (its package is a record,
# never rewritten): the route preview's design reference went in Task W2A (d989d15).
RETIRED = {
    "session-2.md": {"docs/design/screenshots/route-comparison--default--1440x900.png"},
}


def _named(package: Path) -> list[str]:
    return QUOTED.findall(package.read_text(encoding="utf-8"))


def _folders(package: Path) -> list[Path]:
    """The folders a package points to, where its bare file names are found."""
    found = [REVIEWS, package.with_suffix("")]
    for quoted in _named(package):
        if quoted.endswith("/") and not quoted.startswith(PRIVATE):
            found.append(REPO_ROOT / quoted)
    return found


def _opens(path: Path) -> None:
    """The file opens as what it is: a PNG with its header and size, a JSON document that
    parses, or text."""
    data = path.read_bytes()
    match path.suffix:
        case ".png":
            assert data.startswith(PNG_SIGNATURE), path
            width, height = struct.unpack(">II", data[16:24])
            assert min(width, height) > 0, path
        case ".json":
            json.loads(data)
        case _:
            assert data.decode("utf-8").strip(), path


def _resolved(package: Path, name: str) -> Path | None:
    if "/" in name:  # a repository path, a folder's included
        candidate = REPO_ROOT / name
        return candidate if candidate.exists() else None
    for folder in _folders(package):
        if (folder / name).exists():
            return folder / name
    hits = [p for p in REPO_ROOT.glob(f"backend/src/**/{name}") if p.is_file()]
    return hits[0] if hits else None


def test_there_are_session_packages_to_check() -> None:
    assert {p.name for p in PACKAGES} >= {"session-1.md", "session-2.md", "session-w1.md"}


@pytest.mark.req("TEST1-10")
@pytest.mark.parametrize("package", PACKAGES, ids=lambda p: p.name)
def test_every_file_a_session_package_names_exists_and_opens(package: Path) -> None:
    missing, checked = [], 0
    retired = RETIRED.get(package.name, set())
    for name in _named(package):
        if name.startswith(PRIVATE) or not (FILE_NAME.match(name) or name.endswith("/")):
            continue
        if name in retired:
            assert _resolved(package, name) is None, f"{name} is back: remove it from RETIRED"
            continue
        path = _resolved(package, name)
        if path is None:
            missing.append(name)
        elif path.is_file():
            _opens(path)
            checked += 1
        else:
            assert any(path.iterdir()), f"{name} is an empty folder"
    assert missing == [], f"{package.name} names files that aren't there: {missing}"
    folder = package.with_suffix("")
    if folder.is_dir():  # the package's own pictures, such as session W1's
        for picture in folder.iterdir():
            _opens(picture)


@pytest.mark.parametrize("package", PACKAGES, ids=lambda p: p.name)
def test_every_make_command_a_session_package_gives_exists(package: Path) -> None:
    for quoted in _named(package):
        command = MAKE.match(quoted.strip())
        if command is None:
            continue
        dry_run = subprocess.run(  # noqa: S603 - a fixed make dry run, nothing executes
            ["make", "-n", command.group(1)],  # noqa: S607
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert dry_run.returncode == 0, f"{package.name}: `{quoted}`: {dry_run.stderr}"
