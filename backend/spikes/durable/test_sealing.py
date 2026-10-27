import os

import pytest
from cryptography.exceptions import InvalidTag

from spikes.durable.sealing import Keyring, RecordContext, SealedValue

CONTEXT = RecordContext(kind="credential", workspace_id="ws-1", record_id="cred-1")


def keyring() -> Keyring:
    return Keyring({1: os.urandom(32)}, current_version=1)


def test_open_returns_the_sealed_plaintext() -> None:
    ring = keyring()

    assert ring.open(ring.seal(b"secret", CONTEXT), CONTEXT) == b"secret"


def test_ciphertext_does_not_contain_the_plaintext() -> None:
    sealed = keyring().seal(b"plainly-visible-secret", CONTEXT)

    assert b"plainly-visible-secret" not in sealed.ciphertext


def test_value_sealed_for_one_record_cannot_be_opened_as_another() -> None:
    ring = keyring()
    sealed = ring.seal(b"secret", CONTEXT)
    other_workspace = RecordContext(kind="credential", workspace_id="ws-2", record_id="cred-1")

    with pytest.raises(InvalidTag):
        ring.open(sealed, other_workspace)


def test_tampered_ciphertext_is_rejected() -> None:
    ring = keyring()
    sealed = ring.seal(b"secret", CONTEXT)
    flipped = bytes([sealed.ciphertext[0] ^ 1]) + sealed.ciphertext[1:]

    with pytest.raises(InvalidTag):
        ring.open(SealedValue(sealed.key_version, sealed.nonce, flipped), CONTEXT)


def test_each_seal_uses_a_fresh_nonce() -> None:
    ring = keyring()

    nonces = {ring.seal(b"secret", CONTEXT).nonce for _ in range(100)}

    assert len(nonces) == 100


def test_old_key_versions_still_open_after_rotation() -> None:
    old_key, new_key = os.urandom(32), os.urandom(32)
    sealed = Keyring({1: old_key}, current_version=1).seal(b"secret", CONTEXT)

    rotated = Keyring({1: old_key, 2: new_key}, current_version=2)

    assert rotated.open(sealed, CONTEXT) == b"secret"
    assert rotated.seal(b"secret", CONTEXT).key_version == 2


def test_unknown_key_version_is_rejected() -> None:
    sealed = keyring().seal(b"secret", CONTEXT)

    with pytest.raises(KeyError):
        Keyring({2: os.urandom(32)}, current_version=2).open(sealed, CONTEXT)


def test_keys_must_be_256_bit() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        Keyring({1: os.urandom(16)}, current_version=1)
