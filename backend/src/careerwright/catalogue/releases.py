"""Pinned third-party releases (ruling R7, TAX1-04): where each comes from and the exact bytes
it must be.

Large datasets are not committed. `make setup` fetches each pinned file into the gitignored
`var/datasets/` and keeps it only at its pinned size and SHA-256 (`tools.datasets`); an
import reads it only after checking both again (`read_verified`).
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

# The largest pinned file is ONS's ASHE Table 15 package (about 67 MB).
MAX_RELEASE_BYTES = 128 * 1024 * 1024


@dataclass(frozen=True)
class ReleasePin:
    """One exact published file: where it comes from and the bytes it must be."""

    dataset_id: str
    version: str
    language: str
    url: str
    file_name: str
    sha256: str
    size_bytes: int
    native_code_version: str
    sample: bool = False


class ReleaseIntegrityError(ValueError):
    """The file is not the pinned release, or its contents do not have its documented
    structure."""


def read_verified(path: Path, pin: ReleasePin) -> bytes:
    """The release's bytes, only if they are exactly the pinned file."""
    if not path.is_file():
        raise ReleaseIntegrityError(f"{pin.dataset_id} is not at {path}; run `make setup`")
    size = path.stat().st_size
    if size != pin.size_bytes or size > MAX_RELEASE_BYTES:
        raise ReleaseIntegrityError(f"{path.name} is {size} bytes, not {pin.size_bytes}")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != pin.sha256:
        raise ReleaseIntegrityError(f"{path.name} has SHA-256 {digest}, not {pin.sha256}")
    return data
