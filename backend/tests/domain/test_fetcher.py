"""The guarded fetcher against a controlled server (spec section 6; ACQ-01, ACQ-02, ACQ-06,
ACQ-07). The production address check applies throughout; the one exception is the
controlled server's own loopback origin, named explicitly, so the permitted path can be
exercised without the network. Names resolve through a scripted resolver, so DNS answers
(private, mixed, rebinding) are under the test's control."""

import gzip
import ipaddress
import socket
import time
import zlib
from collections.abc import Callable, Iterator

import pytest

from nessa.evidence.addresses import IPAddress
from nessa.evidence.fetcher import (
    DEFAULT_LIMITS,
    HTML_TYPES,
    Fetched,
    Fetcher,
    FetchFailure,
    FetchLimits,
    HostNotFoundError,
)
from nessa.evidence.records import AttemptStatus
from tests.support.source_server import Scripted, SourceServer, html, source_server

LOOPBACK = ipaddress.ip_address("127.0.0.1")
PUBLIC = ipaddress.ip_address("93.184.215.14")
PAGE = html("<h1>Data quality analyst</h1>")


def resolver(names: dict[str, list[IPAddress]]) -> Callable[[str, int], list[IPAddress]]:
    """A scripted DNS: IP literals resolve to themselves, listed names to their answers."""

    def resolve(host: str, port: int) -> list[IPAddress]:
        try:
            return [ipaddress.ip_address(host)]
        except ValueError:
            pass
        if host not in names:
            raise HostNotFoundError
        return names[host]

    return resolve


def fetcher(
    server: SourceServer,
    names: dict[str, list[IPAddress]] | None = None,
    limits: FetchLimits = DEFAULT_LIMITS,
) -> Fetcher:
    return Fetcher(
        resolve=resolver({"page.test.example": [LOOPBACK], **(names or {})}),
        limits=limits,
        user_agent="NessaL0/test",
        extra_allowed=frozenset({("127.0.0.1", server.port)}),
    )


def url(server: SourceServer, path: str, host: str = "page.test.example") -> str:
    return f"http://{host}:{server.port}{path}"


def failure(result: Fetched | FetchFailure) -> FetchFailure:
    assert isinstance(result, FetchFailure), result
    return result


@pytest.mark.req("ACQ-01", "ACQ-02")
def test_a_permitted_page_is_fetched_from_the_checked_address_under_its_own_name() -> None:
    with source_server({"/job": Scripted(body=PAGE)}) as server:
        result = fetcher(server).fetch(url(server, "/job"), accept=HTML_TYPES)

    assert isinstance(result, Fetched)
    assert result.status == 200
    assert result.body == PAGE
    assert result.content_type == "text/html"
    assert result.address == "127.0.0.1"
    assert result.final_url == url(server, "/job")
    assert server.seen[0].host == f"page.test.example:{server.port}"
    assert server.seen[0].user_agent == "NessaL0/test"


@pytest.mark.req("ACQ-01")
@pytest.mark.parametrize(
    "location",
    [
        "http://10.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://2130706433/",
        "http://0x7f.0.0.1/",
        "http://%31%32%37.0.0.1/",
        "http://localhost/",
        "file:///etc/passwd",
    ],
)
def test_a_redirect_to_a_private_or_encoded_address_is_blocked_before_it_is_followed(
    location: str,
) -> None:
    routes = {"/go": Scripted(302, headers=(("Location", location),))}
    with source_server(routes) as server:
        result = failure(fetcher(server).fetch(url(server, "/go"), accept=HTML_TYPES))

    assert result.outcome is AttemptStatus.BLOCKED
    assert result.reason in {
        "address_not_allowed",
        "host_not_allowed",
        "scheme_not_allowed",
    }
    assert result.redirects == (location,)
    assert server.paths() == ["/go"]


@pytest.mark.req("ACQ-01")
def test_a_name_that_resolves_to_a_private_address_is_blocked_at_connect_time() -> None:
    names = {"internal.test.example": [ipaddress.ip_address("10.1.2.3")]}
    with source_server() as server:
        result = failure(
            fetcher(server, names).fetch(
                url(server, "/", "internal.test.example"), accept=HTML_TYPES
            )
        )

    assert (result.outcome, result.reason) == (AttemptStatus.BLOCKED, "address_not_allowed")
    assert server.seen == []


@pytest.mark.req("ACQ-01")
def test_a_name_with_one_private_answer_among_public_ones_is_blocked() -> None:
    names = {"mixed.test.example": [PUBLIC, ipaddress.ip_address("192.168.0.10")]}
    with source_server() as server:
        result = failure(
            fetcher(server, names).fetch(url(server, "/", "mixed.test.example"), accept=HTML_TYPES)
        )

    assert (result.outcome, result.reason) == (AttemptStatus.BLOCKED, "address_not_allowed")


@pytest.mark.req("ACQ-01")
def test_a_redirect_to_a_name_whose_answer_is_private_is_blocked_at_connect_time() -> None:
    # The first hop is the allowed origin; the redirect names a host on the same (allowed)
    # port whose DNS answer is private: the URL passes, the connect-time check refuses it.
    names = {"rebind.test.example": [ipaddress.ip_address("10.0.0.7")]}
    with source_server() as server:
        server.routes["/go"] = Scripted(
            302, headers=(("Location", f"http://rebind.test.example:{server.port}/admin"),)
        )
        result = failure(fetcher(server, names).fetch(url(server, "/go"), accept=HTML_TYPES))

    assert (result.outcome, result.reason) == (AttemptStatus.BLOCKED, "address_not_allowed")
    assert server.paths() == ["/go"]


@pytest.mark.req("ACQ-01")
def test_a_redirect_to_another_port_is_refused() -> None:
    with source_server() as other, source_server() as server:
        server.routes["/go"] = Scripted(
            302, headers=(("Location", f"http://page.test.example:{other.port}/admin"),)
        )
        result = failure(fetcher(server).fetch(url(server, "/go"), accept=HTML_TYPES))

    assert (result.outcome, result.reason) == (AttemptStatus.BLOCKED, "port_not_allowed")
    assert other.seen == []


@pytest.mark.req("ACQ-01")
def test_every_hop_is_recorded_and_redirects_are_bounded() -> None:
    routes = {f"/r{n}": Scripted(302, headers=(("Location", f"/r{n + 1}"),)) for n in range(10)}
    with source_server(routes) as server:
        result = failure(
            fetcher(server, limits=FetchLimits(max_redirects=3)).fetch(
                url(server, "/r0"), accept=HTML_TYPES
            )
        )

    assert (result.outcome, result.reason) == (AttemptStatus.FAILED, "too_many_redirects")
    assert len(result.redirects) == 4
    assert server.paths() == ["/r0", "/r1", "/r2", "/r3"]


@pytest.mark.req("ACQ-01")
def test_a_followed_redirect_ends_at_its_final_url() -> None:
    routes = {
        "/old": Scripted(301, headers=(("Location", "/new"),)),
        "/new": Scripted(body=PAGE),
    }
    with source_server(routes) as server:
        result = fetcher(server).fetch(url(server, "/old"), accept=HTML_TYPES)

    assert isinstance(result, Fetched)
    assert result.final_url == url(server, "/new")
    assert result.redirects == (url(server, "/new"),)


def _endless() -> Iterator[bytes]:
    while True:
        yield b"x" * 65_536


@pytest.mark.req("ACQ-02")
def test_a_body_past_the_size_limit_is_cut_off_and_fails() -> None:
    routes = {"/big": Scripted(body=_endless)}
    with source_server(routes) as server:
        result = failure(
            fetcher(server, limits=FetchLimits(max_bytes=200_000)).fetch(
                url(server, "/big"), accept=HTML_TYPES
            )
        )

    assert (result.outcome, result.reason) == (AttemptStatus.FAILED, "too_large")
    assert not result.transient


@pytest.mark.req("ACQ-02")
def test_a_declared_length_past_the_limit_fails_before_reading() -> None:
    routes = {
        "/big": Scripted(
            headers=(("Content-Type", "text/html"), ("Content-Length", "50000000")), body=b""
        )
    }
    with source_server(routes) as server:
        result = failure(
            fetcher(server, limits=FetchLimits(max_bytes=200_000)).fetch(
                url(server, "/big"), accept=HTML_TYPES
            )
        )

    assert result.reason == "too_large"


@pytest.mark.req("ACQ-02")
def test_a_compressed_body_is_bounded_by_its_decompressed_size() -> None:
    bomb = gzip.compress(b"\0" * 5_000_000)
    small = gzip.compress(PAGE)
    routes = {
        "/bomb": Scripted(
            headers=(("Content-Type", "text/html"), ("Content-Encoding", "gzip")), body=bomb
        ),
        "/small": Scripted(
            headers=(("Content-Type", "text/html"), ("Content-Encoding", "gzip")), body=small
        ),
        "/deflate": Scripted(
            headers=(("Content-Type", "text/html"), ("Content-Encoding", "deflate")),
            body=zlib.compress(PAGE),
        ),
        "/br": Scripted(
            headers=(("Content-Type", "text/html"), ("Content-Encoding", "br")), body=b"x"
        ),
    }
    with source_server(routes) as server:
        f = fetcher(server, limits=FetchLimits(max_bytes=1_000_000))
        bombed = failure(f.fetch(url(server, "/bomb"), accept=HTML_TYPES))
        fine = f.fetch(url(server, "/small"), accept=HTML_TYPES)
        deflated = f.fetch(url(server, "/deflate"), accept=HTML_TYPES)
        brotli = failure(f.fetch(url(server, "/br"), accept=HTML_TYPES))

    assert bombed.reason == "too_large"
    assert isinstance(fine, Fetched)
    assert fine.body == PAGE
    assert isinstance(deflated, Fetched)
    assert deflated.body == PAGE
    assert brotli.reason == "unsupported_content_encoding"


def _slow() -> Iterator[bytes]:
    for _ in range(20):
        time.sleep(0.3)
        yield b"<p>"


@pytest.mark.req("ACQ-02")
def test_a_page_slower_than_the_time_limit_fails_as_a_timeout() -> None:
    routes = {"/slow": Scripted(body=_slow)}
    with source_server(routes) as server:
        started = time.monotonic()
        result = failure(
            fetcher(server, limits=FetchLimits(total_s=1.0, read_s=1.0)).fetch(
                url(server, "/slow"), accept=HTML_TYPES
            )
        )

    assert (result.outcome, result.reason) == (AttemptStatus.FAILED, "timeout")
    assert result.transient
    assert time.monotonic() - started < 3.0


@pytest.mark.req("ACQ-02", "ACQ-07")
@pytest.mark.parametrize("content_type", ["application/pdf", "image/png", "application/json", ""])
def test_an_unsupported_content_type_is_an_explicit_limitation(content_type: str) -> None:
    headers = (("Content-Type", content_type),) if content_type else ()
    routes = {"/doc": Scripted(headers=headers, body=b"%PDF-1.7")}
    with source_server(routes) as server:
        result = failure(fetcher(server).fetch(url(server, "/doc"), accept=HTML_TYPES))

    assert (result.outcome, result.reason) == (AttemptStatus.FAILED, "unsupported_content_type")
    assert not result.transient


@pytest.mark.req("ACQ-02")
@pytest.mark.parametrize(
    ("status", "transient"), [(404, False), (410, False), (403, False), (429, True), (503, True)]
)
def test_http_errors_are_failures_classified_by_status(status: int, transient: bool) -> None:
    with source_server({"/x": Scripted(status, body=b"gone")}) as server:
        result = failure(fetcher(server).fetch(url(server, "/x"), accept=HTML_TYPES))

    assert result.outcome is AttemptStatus.FAILED
    assert result.reason == f"http_{status}"
    assert result.http_status == status
    assert result.transient is transient


def _closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.mark.req("ACQ-02")
def test_connection_failures_and_unknown_hosts_are_typed_failures() -> None:
    port = _closed_port()
    f = Fetcher(
        resolve=resolver({"down.test.example": [LOOPBACK]}),
        limits=FetchLimits(),
        user_agent="NessaL0/test",
        extra_allowed=frozenset({("127.0.0.1", port)}),
    )

    refused = failure(f.fetch(f"http://down.test.example:{port}/", accept=HTML_TYPES))
    unknown = failure(f.fetch("http://nowhere.test.example/", accept=HTML_TYPES))

    assert (refused.reason, refused.transient) == ("connection_failed", True)
    assert (unknown.reason, unknown.transient) == ("host_not_found", False)


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    ("robots", "outcome", "reason"),
    [
        (
            Scripted(
                body=b"User-agent: *\nDisallow: /private\n",
                headers=(("Content-Type", "text/plain"),),
            ),
            AttemptStatus.BLOCKED,
            "robots_disallowed",
        ),
        (
            Scripted(
                body=b"User-agent: NessaL0\nDisallow: /\n",
                headers=(("Content-Type", "text/plain"),),
            ),
            AttemptStatus.BLOCKED,
            "robots_disallowed",
        ),
        (Scripted(503, body=b"down"), AttemptStatus.BLOCKED, "robots_unreachable"),
    ],
    ids=["path disallowed for every agent", "disallowed for Nessa", "robots unreachable"],
)
def test_robots_txt_is_read_first_and_a_refusal_means_no_request_for_the_page(
    robots: Scripted, outcome: AttemptStatus, reason: str
) -> None:
    routes = {"/robots.txt": robots, "/private/job": Scripted(body=PAGE)}
    with source_server(routes) as server:
        result = failure(fetcher(server).fetch_page(url(server, "/private/job")))

    assert (result.outcome, result.reason) == (outcome, reason)
    assert server.paths() == ["/robots.txt"]


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    "robots",
    [
        Scripted(404, body=b"none"),
        Scripted(
            body=b"User-agent: *\nDisallow: /admin\n", headers=(("Content-Type", "text/plain"),)
        ),
    ],
    ids=["no robots.txt", "another path disallowed"],
)
def test_a_page_robots_txt_allows_is_fetched(robots: Scripted) -> None:
    routes = {"/robots.txt": robots, "/jobs/1": Scripted(body=PAGE)}
    with source_server(routes) as server:
        result = fetcher(server).fetch_page(url(server, "/jobs/1"))

    assert isinstance(result, Fetched), result
    assert server.paths() == ["/robots.txt", "/jobs/1"]


@pytest.mark.req("ACQ-01")
def test_a_url_refused_before_lookup_makes_no_request_at_all() -> None:
    with source_server() as server:
        result = failure(fetcher(server).fetch_page("http://192.168.1.1/admin"))

    assert (result.outcome, result.reason) == (AttemptStatus.BLOCKED, "address_not_allowed")
    assert result.redirects == ()
    assert server.seen == []
