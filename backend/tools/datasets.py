"""`make setup`: fetch the pinned third-party datasets and verify them (ruling R7).

Large datasets are not committed. Each one is pinned by URL, size and SHA-256 (ESCO,
`careerwright.catalogue.esco.ESCO_RELEASE`; the reference datasets,
`careerwright.catalogue.reference.DATASETS`: ONS ASHE and the SOC 2020 coding index, the ILO
exposure index, the Anthropic Economic Index and the ESCO to O*NET crosswalk) and downloaded once
into the gitignored `var/datasets/`, which the setup container mounts read-only and imports from. A
download is written to a temporary file and moved into place only after its size and hash match, so
a partial or altered file never has the pinned name. A file already present is re-verified,
never trusted by name. Network access is needed here only. A redirect is followed only to
https on the pinned URL's own host (Hugging Face serves its files that way); the hash check
still decides.

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
from urllib.parse import urlsplit

import httpx2

from careerwright.catalogue.esco import ESCO_RELEASE
from careerwright.catalogue.reference import DATASETS
from careerwright.catalogue.releases import MAX_RELEASE_BYTES, ReleasePin, read_verified
from tools.localenv import REPO_ROOT

DATASETS_DIR = REPO_ROOT / "var" / "datasets"
DOWNLOAD_TIMEOUT_S = 300.0
MAX_REDIRECTS = 5
PINNED: tuple[ReleasePin, ...] = (ESCO_RELEASE, *(dataset.pin for dataset in DATASETS))


class DownloadError(RuntimeError):
    pass


def _next_hop(pin: ReleasePin, current: httpx2.URL, response: httpx2.Response) -> httpx2.URL:
    following = current.join(response.headers.get("location", ""))
    if following.scheme != "https" or following.host != urlsplit(pin.url).hostname:
        raise DownloadError(f"{pin.url} redirects off its host")
    return following


def download(pin: ReleasePin, target: Path, client: httpx2.Client) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    url = httpx2.URL(pin.url)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".partial-", delete=False) as tmp:
        partial = Path(tmp.name)
        try:
            for _ in range(MAX_REDIRECTS + 1):
                with client.stream("GET", url) as response:
                    if response.is_redirect:
                        url = _next_hop(pin, url, response)
                        continue
                    if response.status_code != 200:
                        raise DownloadError(f"{pin.url} answered HTTP {response.status_code}")
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > min(pin.size_bytes, MAX_RELEASE_BYTES):
                            raise DownloadError(f"{pin.dataset_id} is larger than pinned")
                        digest.update(chunk)
                        tmp.write(chunk)
                    break
            else:
                raise DownloadError(f"{pin.url} redirects more than {MAX_REDIRECTS} times")
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
    failed = False
    with httpx2.Client(timeout=DOWNLOAD_TIMEOUT_S, follow_redirects=False) as client:
        for pin in PINNED:
            try:
                outcome = ensure(pin, args.dir, client)
            except (DownloadError, ValueError, httpx2.HTTPError) as error:
                failed = True
                print(
                    f"{pin.dataset_id} could not be fetched: {error}\n"
                    f"Manual step: download {pin.url}\n"
                    f"to {args.dir / pin.file_name} and run `make setup` again "
                    "(docs/runbook.md).",
                    file=sys.stderr,
                )
                continue
            print(f"{pin.dataset_id} ({pin.version}): {outcome}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
