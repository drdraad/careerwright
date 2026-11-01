"""Start a backend service as its own unprivileged user, holding private copies of exactly
the files Compose gave its container (ADR 0004, amendment 2026-11-01).

On a Linux Docker host a Compose file secret or a bind-mounted directory keeps its host owner
and mode, and `make setup` makes them owner-only (0600 files in 0700 directories), so the
service user (uid 10001) cannot read them. Docker Desktop hides host ownership, which is why
a Mac never saw this. So the container starts as root (compose.yaml) and this step runs first:

1. Every regular file of each location given to this container (`/run/secrets`,
   `/run/careerwright/keys`, `/run/careerwright/adzuna`, whichever exist) is copied into the
   container's private tmpfs, `/run/careerwright/private/<name>/`, owned by the service user:
   files 0400, directories 0500. Content goes from file to file, never through an argument,
   the environment or a log, and never onto disk or into an image layer.
2. The process drops to the service user (supplementary groups cleared, then the group, then
   the user) and replaces itself with the service's command.

A container is given only its own secrets and mounts, so it copies only those. Standard
library only: the acquisition worker's container runs this too (ACQ-05).

Run: `python -m careerwright.entrypoint <command> [args...]` (compose.yaml's `entrypoint`).
"""

import os
import pwd
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

SERVICE_USER = "careerwright"
PRIVATE = Path("/run/careerwright/private")
MOUNTS = Path("/proc/mounts")
GIVEN: tuple[tuple[str, Path], ...] = (
    ("secrets", Path("/run/secrets")),
    ("keys", Path("/run/careerwright/keys")),
    ("adzuna", Path("/run/careerwright/adzuna")),
)


def copy_given(given: Sequence[tuple[str, Path]], private: Path, uid: int, gid: int) -> list[str]:
    """Copy each existing location's regular files to `private/<name>/`, read-only for
    `uid:gid` alone, replacing an earlier copy. Returns the copies' names, sorted."""
    copied: list[str] = []
    private.chmod(0o700)
    for name, source in given:
        if not source.is_dir():
            continue
        target = private / name
        if target.exists():
            target.chmod(0o700)
            shutil.rmtree(target)
        target.mkdir(mode=0o700)
        os.chown(target, uid, gid)
        for path in sorted(source.iterdir()):
            if not path.is_file():
                continue
            fd = os.open(target / path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
            os.fchown(fd, uid, gid)
            with os.fdopen(fd, "wb") as handle:
                handle.write(path.read_bytes())
            copied.append(f"{name}/{path.name}")
        target.chmod(0o500)
    os.chown(private, uid, gid)
    private.chmod(0o500)
    return sorted(copied)


def is_tmpfs(path: Path, mounts: Path) -> bool:
    """Whether `path` is itself a tmpfs mount point, as the kernel lists it: the last mount
    there is the one in use. Any other mount (a disk volume, a bind mount) is not memory."""
    found = None
    for line in mounts.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[1] == str(path):
            found = fields[2]
    return found == "tmpfs"


def main(argv: Sequence[str] | None = None) -> NoReturn:
    command = list(sys.argv[1:] if argv is None else argv)
    if not command:
        raise SystemExit("usage: python -m careerwright.entrypoint <command> [args...]")
    if os.geteuid() != 0:
        raise SystemExit(
            "careerwright.entrypoint must start as root to give the service its files "
            "(compose.yaml sets `user: root`)"
        )
    if not is_tmpfs(PRIVATE, MOUNTS):
        raise SystemExit(f"{PRIVATE} is not a tmpfs mount; the copies must stay in memory")
    user = pwd.getpwnam(SERVICE_USER)
    copy_given(GIVEN, PRIVATE, user.pw_uid, user.pw_gid)
    os.setgroups([])
    os.setgid(user.pw_gid)
    os.setuid(user.pw_uid)
    os.environ["HOME"] = user.pw_dir  # what Docker sets when the image's user starts it
    os.execvp(command[0], command)  # noqa: S606 - compose.yaml's command, no shell


if __name__ == "__main__":
    main()
