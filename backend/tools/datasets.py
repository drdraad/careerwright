"""`make setup`: fetch the pinned third-party datasets and verify them (ruling R7).

Large datasets are not committed. Each one is pinned by URL, size and SHA-256
(`nessa.catalogue.esco.ESCO_RELEASE`) and downloaded once into the gitignored
`var/datasets/`, which the setup container mounts read-only and imports from. A download is
written to a temporary file and moved into place only after its size and hash match, so a
partial or altered file never has the pinned name. A file already present is re-verified,
never trusted by name. Network access is needed here only.

If the automated download fails (the publisher's site changed), the manual step is in
`docs/runbook.md`: download the same file by hand, put it at the path printed below, and
re-run `make setup`; the hash check still applies.

Run from `backend/`: `uv run --locked python -m tools.datasets`.
"""

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

import httpx2

from nessa.catalogue.esco import ESCO_RELEASE, MAX_RELEASE_BYTES, ReleasePin, read_verified
from tools.localenv import REPO_ROOT

DATASETS_DIR = REPO_ROOT / "var" / "datasets"
DOWNLOAD_TIMEOUT_S = 300.0


class DownloadError(RuntimeError):
    pass


def download(pin: ReleasePin, target: Path, client: httpx2.Client) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".partial-", delete=False) as tmp:
        partial = Path(tmp.name)
        try:
            with client.stream("GET", pin.url) as response:
                if response.status_code != 200:
                    raise DownloadError(f"{pin.url} answered HTTP {response.status_code}")
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > min(pin.size_bytes, MAX_RELEASE_BYTES):
                        raise DownloadError(f"{pin.dataset_id} is larger than pinned")
                    digest.update(chunk)
                    tmp.write(chunk)
            if size != pin.size_bytes or digest.hexdigest() != pin.sha256:
                raise DownloadError(
                    f"{pin.dataset_id}: got {size} bytes with SHA-256 {digest.hexdigest()}, "
                    f"pinned {pin.size_bytes} bytes with SHA-256 {pin.sha256}"
                )
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
    partial.chmod(0o644)  # public data; the setup container's user must read it
    partial.replace(target)


def ensure(pin: ReleasePin, directory: Path, client: httpx2.Client) -> str:
    """Make `directory/pin.file_name` the verified release; returns what was done."""
    target = directory / pin.file_name
    if target.exists():
        try:
            read_verified(target, pin)
            return "already present, verified"
        except ValueError:
            target.unlink()  # not the pinned bytes: fetch them again
    download(pin, target, client)
    read_verified(target, pin)
    return "downloaded, verified"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=DATASETS_DIR)
    args = parser.parse_args(argv)
    with httpx2.Client(timeout=DOWNLOAD_TIMEOUT_S, follow_redirects=False) as client:
        try:
            outcome = ensure(ESCO_RELEASE, args.dir, client)
        except (DownloadError, ValueError, httpx2.HTTPError) as error:
            print(
                f"{ESCO_RELEASE.dataset_id} could not be fetched: {error}\n"
                f"Manual step: download {ESCO_RELEASE.url}\n"
                f"to {args.dir / ESCO_RELEASE.file_name} and run `make setup` again "
                "(docs/runbook.md).",
                file=sys.stderr,
            )
            raise SystemExit(1) from None
    print(f"{ESCO_RELEASE.dataset_id} ({ESCO_RELEASE.version}): {outcome}")


if __name__ == "__main__":
    main()
