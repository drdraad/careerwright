import os
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

from nessa.identity.keyring import (
    KEY_BYTES,
    Keyring,
    MasterKeyError,
    RecordContext,
    SealedValue,
    load_keyring,
)

CONTEXT = RecordContext(kind="credential", workspace_id="ws-1", record_id="cred-1")


def keyring() -> Keyring:
    return Keyring({1: os.urandom(KEY_BYTES)}, current_version=1)


def write_key(directory: Path, version: int, *, mode: int = 0o600, size: int = KEY_BYTES) -> None:
    path = directory / f"v{version}.key"
    path.write_bytes(os.urandom(size))
    path.chmod(mode)


@pytest.fixture
def key_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "keys"
    directory.mkdir(mode=0o700)
    return directory


def test_open_returns_the_sealed_plaintext() -> None:
    ring = keyring()

    assert ring.open(ring.seal(b"secret", CONTEXT), CONTEXT) == b"secret"


def test_ciphertext_does_not_contain_the_plaintext() -> None:
    sealed = keyring().seal(b"plainly-visible-secret", CONTEXT)

    assert b"plainly-visible-secret" not in sealed.ciphertext


@pytest.mark.req("MODEL-05")
def test_value_sealed_for_one_workspace_cannot_be_opened_as_another() -> None:
    ring = keyring()
    sealed = ring.seal(b"secret", CONTEXT)

    with pytest.raises(InvalidTag):
        ring.open(sealed, RecordContext("credential", "ws-2", "cred-1"))
    with pytest.raises(InvalidTag):
        ring.open(sealed, RecordContext("credential", "ws-1", "cred-2"))
    with pytest.raises(InvalidTag):
        ring.open(sealed, RecordContext("run_output", "ws-1", "cred-1"))


def test_tampered_ciphertext_is_rejected() -> None:
    ring = keyring()
    sealed = ring.seal(b"secret", CONTEXT)
    flipped = bytes([sealed.ciphertext[0] ^ 1]) + sealed.ciphertext[1:]

    with pytest.raises(InvalidTag):
        ring.open(SealedValue(sealed.key_version, sealed.nonce, flipped), CONTEXT)


@pytest.mark.req("MODEL-05")
def test_each_seal_uses_a_fresh_nonce() -> None:
    ring = keyring()

    nonces = {ring.seal(b"secret", CONTEXT).nonce for _ in range(200)}

    assert len(nonces) == 200


@pytest.mark.req("MODEL-05")
def test_old_key_versions_still_open_after_rotation() -> None:
    old_key, new_key = os.urandom(KEY_BYTES), os.urandom(KEY_BYTES)
    sealed = Keyring({1: old_key}, current_version=1).seal(b"secret", CONTEXT)

    rotated = Keyring({1: old_key, 2: new_key}, current_version=2)

    assert rotated.open(sealed, CONTEXT) == b"secret"
    assert rotated.seal(b"secret", CONTEXT).key_version == 2


def test_unknown_key_version_is_refused_without_revealing_keys() -> None:
    sealed = keyring().seal(b"secret", CONTEXT)

    with pytest.raises(MasterKeyError, match="version 1"):
        Keyring({2: os.urandom(KEY_BYTES)}, current_version=2).open(sealed, CONTEXT)


def test_keys_must_be_256_bit() -> None:
    with pytest.raises(MasterKeyError, match="32 bytes"):
        Keyring({1: os.urandom(16)}, current_version=1)


def test_load_keyring_uses_the_highest_version_as_current(key_dir: Path) -> None:
    write_key(key_dir, 1)
    write_key(key_dir, 2)

    ring = load_keyring(key_dir)

    assert ring.current_version == 2
    assert ring.versions == (1, 2)


@pytest.mark.req("MODEL-05")
@pytest.mark.parametrize("mode", [0o640, 0o604, 0o644])
def test_load_keyring_refuses_a_key_readable_by_others(key_dir: Path, mode: int) -> None:
    write_key(key_dir, 1, mode=mode)

    with pytest.raises(MasterKeyError, match="owner-only"):
        load_keyring(key_dir)


def test_load_keyring_refuses_a_directory_open_to_others(key_dir: Path) -> None:
    write_key(key_dir, 1)
    key_dir.chmod(0o755)

    with pytest.raises(MasterKeyError, match="owner-only"):
        load_keyring(key_dir)


def test_load_keyring_refuses_an_empty_or_missing_directory(tmp_path: Path, key_dir: Path) -> None:
    with pytest.raises(MasterKeyError, match="no master key"):
        load_keyring(key_dir)
    with pytest.raises(MasterKeyError, match="not found"):
        load_keyring(tmp_path / "absent")


def test_load_keyring_refuses_a_wrong_sized_key(key_dir: Path) -> None:
    write_key(key_dir, 1, size=31)

    with pytest.raises(MasterKeyError, match="32 bytes"):
        load_keyring(key_dir)


def test_keyring_repr_never_shows_key_material() -> None:
    key = os.urandom(KEY_BYTES)

    assert key.hex() not in repr(Keyring({1: key}, current_version=1))
