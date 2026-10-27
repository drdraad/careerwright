"""AES-256-GCM sealing of private records, bound to their record identity.

The record kind, workspace and record ID are authenticated data, so a ciphertext copied to
another workspace or record does not open. Keys are versioned for rotation; the runtime
master key lives outside the repository and the database.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_BYTES = 32
NONCE_BYTES = 12


@dataclass(frozen=True)
class RecordContext:
    kind: str
    workspace_id: str
    record_id: str

    def associated_data(self) -> bytes:
        return f"nessa:{self.kind}:{self.workspace_id}:{self.record_id}".encode()


@dataclass(frozen=True)
class SealedValue:
    key_version: int
    nonce: bytes
    ciphertext: bytes


class Keyring:
    def __init__(self, keys: Mapping[int, bytes], *, current_version: int) -> None:
        if any(len(key) != KEY_BYTES for key in keys.values()):
            raise ValueError(f"master keys must be {KEY_BYTES} bytes")
        if current_version not in keys:
            raise ValueError("current key version is not in the keyring")
        self._keys = dict(keys)
        self._current_version = current_version

    def seal(self, plaintext: bytes, context: RecordContext) -> SealedValue:
        nonce = os.urandom(NONCE_BYTES)
        key = self._keys[self._current_version]
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, context.associated_data())
        return SealedValue(self._current_version, nonce, ciphertext)

    def open(self, sealed: SealedValue, context: RecordContext) -> bytes:
        key = self._keys[sealed.key_version]
        return AESGCM(key).decrypt(sealed.nonce, sealed.ciphertext, context.associated_data())
