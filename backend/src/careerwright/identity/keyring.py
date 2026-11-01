"""AES-256-GCM sealing of private records, bound to their record identity (spec section 16).

The record kind, workspace and record ID are authenticated data, so a ciphertext copied to
another workspace or record does not open. Each seal draws a fresh 96-bit nonce. Master keys
are versioned for rotation and live in a directory outside the repository and the database
(`make setup` creates it); a key file readable by anyone but its owner is refused.
"""

import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_BYTES = 32
NONCE_BYTES = 12
_KEY_FILE = re.compile(r"^v([1-9][0-9]*)\.key$")
_OTHERS = stat.S_IRWXG | stat.S_IRWXO


class MasterKeyError(RuntimeError):
    """The master key directory is missing, malformed or too permissive. Names paths only."""


@dataclass(frozen=True)
class RecordContext:
    kind: str
    workspace_id: str
    record_id: str

    def associated_data(self) -> bytes:
        return f"careerwright:{self.kind}:{self.workspace_id}:{self.record_id}".encode()


@dataclass(frozen=True)
class SealedValue:
    key_version: int
    nonce: bytes
    ciphertext: bytes


class Keyring:
    def __init__(self, keys: Mapping[int, bytes], *, current_version: int) -> None:
        if any(len(key) != KEY_BYTES for key in keys.values()):
            raise MasterKeyError(f"master keys must be {KEY_BYTES} bytes")
        if current_version not in keys:
            raise MasterKeyError("the current key version is not in the keyring")
        self._keys = dict(keys)
        self.current_version = current_version

    def __repr__(self) -> str:
        return f"Keyring(versions={self.versions}, current_version={self.current_version})"

    @property
    def versions(self) -> tuple[int, ...]:
        return tuple(sorted(self._keys))

    def seal(self, plaintext: bytes, context: RecordContext) -> SealedValue:
        nonce = os.urandom(NONCE_BYTES)
        key = self._keys[self.current_version]
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, context.associated_data())
        return SealedValue(self.current_version, nonce, ciphertext)

    def open(self, sealed: SealedValue, context: RecordContext) -> bytes:
        key = self._keys.get(sealed.key_version)
        if key is None:
            raise MasterKeyError(f"master key version {sealed.key_version} is not loaded")
        return AESGCM(key).decrypt(sealed.nonce, sealed.ciphertext, context.associated_data())


def _owner_only(path: Path) -> None:
    if path.stat().st_mode & _OTHERS:
        raise MasterKeyError(f"{path} must be owner-only (chmod 700 for the directory, 600 keys)")


def load_keyring(directory: Path) -> Keyring:
    """Load `v<N>.key` files; the highest version seals, every version opens."""
    if not directory.is_dir():
        raise MasterKeyError(f"master key directory {directory} not found; run `make setup`")
    _owner_only(directory)
    keys: dict[int, bytes] = {}
    for path in directory.iterdir():
        match = _KEY_FILE.match(path.name)
        if match is None:
            continue
        _owner_only(path)
        keys[int(match.group(1))] = path.read_bytes()
    if not keys:
        raise MasterKeyError(f"no master key in {directory}; run `make setup`")
    return Keyring(keys, current_version=max(keys))
