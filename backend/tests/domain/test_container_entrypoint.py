"""A backend container starts as root only long enough to copy the files Compose gave it into
its private tmpfs, owned by the service user, then drops to that user and runs the service
(ADR 0004, amendment 2026-11-01: the stack on a Linux Docker host)."""

import os
import pwd
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from careerwright import entrypoint
from careerwright.identity.keyring import load_keyring


def owner_only_tree(root: Path) -> dict[str, Path]:
    """What `make setup` makes: 0700 directories holding 0600 files."""
    secrets, keys = root / "secrets", root / "keys"
    root.mkdir(mode=0o700)
    for directory in (secrets, keys):
        directory.mkdir(mode=0o700)
    for path, content in (
        (secrets / "pg_worker", b"worker-password-not-real"),
        (secrets / "pg_dbos_runtime", b"dbos-password-not-real"),
        (keys / "v1.key", bytes(range(32))),
        (keys / "v2.key", bytes(range(32, 64))),
    ):
        path.write_bytes(content)
        path.chmod(0o600)
    return {"secrets": secrets, "keys": keys}


def private_dir(tmp_path: Path) -> Path:
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    return private


@pytest.mark.req("MODEL-05", "ACQ-05")
def test_each_given_file_is_copied_read_only_for_the_service_user_alone(tmp_path: Path) -> None:
    given = owner_only_tree(tmp_path / "host")
    private = private_dir(tmp_path)
    absent = tmp_path / "host" / "adzuna"  # not given to this container
    uid, gid = os.getuid(), os.getgid()

    copied = entrypoint.copy_given(
        (("secrets", given["secrets"]), ("keys", given["keys"]), ("adzuna", absent)),
        private,
        uid,
        gid,
    )

    assert copied == ["keys/v1.key", "keys/v2.key", "secrets/pg_dbos_runtime", "secrets/pg_worker"]
    assert sorted(p.name for p in private.iterdir()) == ["keys", "secrets"]  # nothing invented
    for name in copied:
        copy = private / name
        assert copy.read_bytes() == (given[copy.parent.name] / copy.name).read_bytes()
        assert stat.S_IMODE(copy.stat().st_mode) == 0o400
        assert (copy.stat().st_uid, copy.stat().st_gid) == (uid, gid)
    for directory in (private, private / "keys", private / "secrets"):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o500
        assert directory.stat().st_uid == uid
    # The service's own owner-only check accepts the copies (ADR 0004 decision 3).
    assert load_keyring(private / "keys").versions == (1, 2)


@pytest.mark.req("MODEL-05")
def test_a_restart_copies_afresh_so_a_removed_key_is_gone(tmp_path: Path) -> None:
    given = owner_only_tree(tmp_path / "host")
    private = private_dir(tmp_path)
    locations = (("keys", given["keys"]),)
    entrypoint.copy_given(locations, private, os.getuid(), os.getgid())

    (given["keys"] / "v1.key").unlink()
    copied = entrypoint.copy_given(locations, private, os.getuid(), os.getgid())

    assert copied == ["keys/v2.key"]
    assert sorted(p.name for p in (private / "keys").iterdir()) == ["v2.key"]


class Exec(Exception):  # noqa: N818 - stands in for os.execvp, which never returns
    pass


def started(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, euid: int = 0, mounted: bool = True
) -> list[tuple[str, object]]:
    """Run `main` with the process calls recorded instead of made."""
    given = owner_only_tree(tmp_path / "host")
    private = private_dir(tmp_path)
    calls: list[tuple[str, object]] = []
    user = SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid(), pw_dir="/home/careerwright")

    def getpwnam(name: str) -> SimpleNamespace:
        calls.append(("user", name))
        return user

    def execvp(file: str, args: list[str]) -> None:
        calls.append(("exec", (file, args, os.environ["HOME"])))
        raise Exec

    monkeypatch.setattr(entrypoint, "GIVEN", (("secrets", given["secrets"]),))
    monkeypatch.setattr(entrypoint, "PRIVATE", private)
    monkeypatch.setattr(pwd, "getpwnam", getpwnam)
    monkeypatch.setattr(os, "geteuid", lambda: euid)
    monkeypatch.setattr(os.path, "ismount", lambda path: mounted and path == private)
    monkeypatch.setattr(os, "setgroups", lambda groups: calls.append(("groups", groups)))
    monkeypatch.setattr(os, "setgid", lambda gid: calls.append(("gid", gid)))
    monkeypatch.setattr(os, "setuid", lambda uid: calls.append(("uid", uid)))
    monkeypatch.setattr(os, "execvp", execvp)
    monkeypatch.setenv("HOME", "/root")
    return calls


@pytest.mark.req("ACQ-05")
def test_it_drops_every_privilege_before_the_service_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = started(monkeypatch, tmp_path)

    with pytest.raises(Exec):
        entrypoint.main(["python", "-m", "careerwright.worker"])

    assert calls == [
        ("user", "careerwright"),
        ("groups", []),
        ("gid", os.getgid()),
        ("uid", os.getuid()),
        ("exec", ("python", ["python", "-m", "careerwright.worker"], "/home/careerwright")),
    ]
    assert (tmp_path / "private" / "secrets" / "pg_worker").is_file()


@pytest.mark.parametrize(
    ("euid", "mounted", "argv", "reason"),
    [
        (10001, True, ["python"], "must start as root"),
        (0, False, ["python"], "is not a tmpfs mount"),
        (0, True, [], "usage"),
    ],
)
@pytest.mark.req("ACQ-05")
def test_it_refuses_to_start_rather_than_run_without_its_files_or_as_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    euid: int,
    mounted: bool,
    argv: list[str],
    reason: str,
) -> None:
    calls = started(monkeypatch, tmp_path, euid=euid, mounted=mounted)

    with pytest.raises(SystemExit, match=reason):
        entrypoint.main(argv)

    assert [c for c in calls if c[0] in ("uid", "exec")] == []
    assert list((tmp_path / "private").iterdir()) == []
