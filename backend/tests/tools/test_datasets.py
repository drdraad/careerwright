"""`make setup`'s dataset fetch: only the pinned bytes ever get the pinned name (R7, TAX1-04).
Offline: the publisher is a mock transport serving the committed sample."""

import dataclasses
from pathlib import Path

import httpx2
import pytest

from tests.support.esco import SAMPLE_PATH, SAMPLE_RELEASE
from tools.datasets import DownloadError, ensure

PIN = dataclasses.replace(SAMPLE_RELEASE, url="https://publisher.test/esco.zip")


def client(body: bytes, requests: list[str], status: int = 200) -> httpx2.Client:
    def handle(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        return httpx2.Response(status, content=body)

    return httpx2.Client(transport=httpx2.MockTransport(handle))


@pytest.mark.req("TAX1-04")
def test_a_download_is_kept_only_when_its_size_and_hash_match(tmp_path: Path) -> None:
    requests: list[str] = []

    outcome = ensure(PIN, tmp_path, client(SAMPLE_PATH.read_bytes(), requests))

    assert outcome == "downloaded, verified"
    assert (tmp_path / PIN.file_name).read_bytes() == SAMPLE_PATH.read_bytes()
    assert requests == [PIN.url]
    assert ensure(PIN, tmp_path, client(b"", requests)) == "already present, verified"
    assert requests == [PIN.url]  # a verified file is not fetched again


@pytest.mark.req("TAX1-04")
def test_altered_bytes_are_refused_and_never_left_under_the_pinned_name(tmp_path: Path) -> None:
    good = SAMPLE_PATH.read_bytes()
    altered = good[:-1] + bytes([good[-1] ^ 1])

    with pytest.raises(DownloadError, match="SHA-256"):
        ensure(PIN, tmp_path, client(altered, []))
    with pytest.raises(DownloadError, match="larger"):
        ensure(PIN, tmp_path, client(good + b"x", []))
    with pytest.raises(DownloadError, match="HTTP 404"):
        ensure(PIN, tmp_path, client(b"", [], status=404))

    assert list(tmp_path.iterdir()) == []  # no partial or altered file remains


def test_a_damaged_local_copy_is_replaced_by_the_pinned_bytes(tmp_path: Path) -> None:
    (tmp_path / PIN.file_name).write_bytes(b"damaged")
    requests: list[str] = []

    assert ensure(PIN, tmp_path, client(SAMPLE_PATH.read_bytes(), requests)) == (
        "downloaded, verified"
    )
    assert requests == [PIN.url]
