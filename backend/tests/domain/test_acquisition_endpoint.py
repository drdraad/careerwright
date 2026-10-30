"""The restricted acquisition worker's own HTTP endpoint refuses a malformed request before
reading it (review A M8): a Content-Length that is not a non-negative integer is a 400, so
it can neither block a thread reading to the end of a kept-alive connection nor escape the
handler."""

import json
import socket
import threading
from collections.abc import Iterator

import pytest

from careerwright.acquisition import AcquisitionService, make_server
from careerwright.evidence.acquire import AcquisitionResult, Pacer
from careerwright.evidence.addresses import IPAddress
from careerwright.evidence.fetcher import Fetcher
from careerwright.evidence.records import AttemptReason, AttemptStatus


@pytest.fixture
def endpoint() -> Iterator[int]:
    service = AcquisitionService(
        Fetcher(user_agent="CareerwrightL0/test"),
        credentials=None,
        pacer=Pacer(sleep=lambda s: None),
    )
    server = make_server(service, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, args=(0.05,), daemon=True)
    thread.start()
    try:
        yield int(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()


def _post(port: int, length: str, body: bytes = b"") -> bytes:
    request = (
        f"POST /v1/fetch HTTP/1.1\r\nHost: acquisition:8100\r\nContent-Type: application/json"
        f"\r\nContent-Length: {length}\r\n\r\n"
    ).encode() + body
    with socket.create_connection(("127.0.0.1", port), timeout=5) as conn:
        conn.sendall(request)
        answer = b""
        while chunk := conn.recv(4096):  # a 5 s timeout: a server that hangs fails the test
            answer += chunk
            head, found, rest = answer.partition(b"\r\n\r\n")
            declared = head.lower().partition(b"content-length: ")[2].partition(b"\r\n")[0]
            if found and declared.isdigit() and len(rest) >= int(declared):
                break
        return answer


@pytest.mark.req("ACQ-05")
@pytest.mark.parametrize("length", ["-5", "abc", "1e3", "+4", "٣"])
def test_a_content_length_that_is_not_a_non_negative_integer_is_refused(
    endpoint: int, length: str
) -> None:
    answer = _post(endpoint, length)

    assert answer.startswith(b"HTTP/1.1 400 ")
    assert b"invalid_content_length" in answer


@pytest.mark.req("ACQ-05")
def test_a_well_formed_request_is_answered(endpoint: int) -> None:
    body = b'{"url": "http://10.0.0.1/admin"}'

    answer = _post(endpoint, str(len(body)), body)

    assert answer.startswith(b"HTTP/1.1 200 ")
    assert b"address_not_allowed" in answer


def _defective_resolve(host: str, port: int) -> list[IPAddress]:
    raise RuntimeError("a defect, not the source's fault")


@pytest.mark.req("ACQ-05", "ACQ-02")
def test_a_defect_while_acquiring_is_a_failed_attempt_never_a_malformed_request() -> None:
    # Re-review A M-7: an internal error used to be answered 422, which the client takes for
    # the worker being unavailable (a transient retry).
    service = AcquisitionService(
        Fetcher(user_agent="CareerwrightL0/test", resolve=_defective_resolve),
        credentials=None,
        pacer=Pacer(sleep=lambda s: None),
    )

    status, payload = service.handle(
        "/v1/fetch", json.dumps({"url": "https://jobs.example.org/job/1"}).encode()
    )
    malformed, _ = service.handle("/v1/fetch", b'{"no": "url"}')

    result = AcquisitionResult.model_validate(payload)
    assert status == 200
    assert (result.status, result.reason, result.transient) == (
        AttemptStatus.FAILED,
        AttemptReason.INTERNAL_ERROR,
        False,
    )
    assert result.requested_url == "https://jobs.example.org/job/1"
    assert malformed == 422  # only a request that does not parse is one
