"""The guarded fetcher's proxy mode (ADR 0009, 2026-11-01 amendment; ACQ-01, ACQ-02, ACQ-06),
for the controller's tools only, against a local fake proxy and the controlled server. Every
request goes through CONNECT with no name looked up here; every other guard still runs (the
URL checks, robots.txt through the same mode, every redirect checked, the size limit, TLS
verified against the named bundle); and the product can never select it. No request leaves
loopback: the fake proxy tunnels only to the test's own servers."""

import ast
import ipaddress
import ssl
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from pydantic import ValidationError

from careerwright import acquisition
from careerwright.acquisition import AcquisitionSettings
from careerwright.evidence.addresses import IPAddress
from careerwright.evidence.fetcher import (
    DEFAULT_LIMITS,
    HTML_TYPES,
    Fetched,
    Fetcher,
    FetchFailure,
    FetchLimits,
    FetchProxy,
    ProxyConfigError,
    fetch_proxy,
)
from careerwright.evidence.records import AttemptStatus
from tests.support.certificates import make_ca, make_leaf
from tests.support.fake_proxy import FakeProxy, fake_proxy
from tests.support.source_server import Scripted, SourceServer, html, source_server

PAGE = html("<h1>Data quality analyst</h1>")
ROBOTS = Scripted(
    body=b"User-agent: *\nDisallow: /private\n", headers=(("Content-Type", "text/plain"),)
)
HOST = "page.test.example"
SRC = Path(__file__).resolve().parents[2] / "src" / "careerwright"


def _no_lookup(host: str, port: int) -> list[IPAddress]:
    raise AssertionError("proxy mode never looks a name up")


@pytest.fixture
def ca_file(tmp_path: Path) -> Path:
    return make_ca().bundle(tmp_path / "bundle.pem")


def proxied(
    server_port: int, proxy: FakeProxy, ca: Path, limits: FetchLimits = DEFAULT_LIMITS
) -> Fetcher:
    return Fetcher(
        resolve=_no_lookup,
        limits=limits,
        user_agent="CareerwrightL0/test",
        extra_allowed=frozenset({("127.0.0.1", server_port)}),  # the port only: no lookup
        proxy=fetch_proxy(proxy.url, ca),
    )


def failure(result: Fetched | FetchFailure) -> FetchFailure:
    assert isinstance(result, FetchFailure), result
    return result


@contextmanager
def through_proxy(routes: dict[str, Scripted]) -> Iterator[tuple[SourceServer, FakeProxy]]:
    with source_server(routes) as server, fake_proxy() as proxy:
        proxy.routes[f"{HOST}:{server.port}"] = server.port
        yield server, proxy


@pytest.mark.req("ACQ-01", "ACQ-06")
def test_a_page_and_its_robots_txt_go_through_connect_with_no_name_looked_up(
    ca_file: Path,
) -> None:
    with through_proxy({"/robots.txt": ROBOTS, "/jobs/1": Scripted(body=PAGE)}) as (server, proxy):
        f = proxied(server.port, proxy, ca_file)
        result = f.fetch_page(f"http://{HOST}:{server.port}/jobs/1")

    assert isinstance(result, Fetched)
    assert result.body == PAGE
    assert result.address is None  # Careerwright never learnt the proxy's address
    assert result.requests == 2
    assert f.via_proxy is True
    assert proxy.connects() == [f"{HOST}:{server.port}"] * 2  # robots.txt, then the page
    assert all(line.startswith("CONNECT ") for line in proxy.lines)
    assert server.paths() == ["/robots.txt", "/jobs/1"]
    assert server.seen[1].host == f"{HOST}:{server.port}"  # the origin's name, unchanged


@pytest.mark.req("ACQ-06")
def test_robots_txt_still_refuses_a_page_in_proxy_mode(ca_file: Path) -> None:
    with through_proxy({"/robots.txt": ROBOTS, "/private/1": Scripted(body=PAGE)}) as (
        server,
        proxy,
    ):
        result = failure(
            proxied(server.port, proxy, ca_file).fetch_page(
                f"http://{HOST}:{server.port}/private/1"
            )
        )

    assert (result.outcome, result.reason) == (AttemptStatus.BLOCKED, "robots_disallowed")
    assert server.paths() == ["/robots.txt"]


@pytest.mark.req("ACQ-01")
@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/",
        "http://intranet/",
        "http://10.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://2130706433/",
        "http://printer.local/",
        "https://user:pass@jobs.example.com/",
        "ftp://jobs.example.com/",
        "https://jobs.example.com:8443/",
    ],
)
def test_a_refused_url_is_refused_in_proxy_mode_before_any_connect(url: str, ca_file: Path) -> None:
    with fake_proxy() as proxy:
        f = Fetcher(
            user_agent="CareerwrightL0/test",
            resolve=_no_lookup,
            proxy=fetch_proxy(proxy.url, ca_file),
        )
        result = failure(f.fetch_page(url))

    assert result.outcome is AttemptStatus.BLOCKED
    assert proxy.lines == []


@pytest.mark.req("ACQ-01")
@pytest.mark.parametrize(
    "location", ["http://10.0.0.1/", "http://localhost/", "http://[::1]/", "file:///etc/passwd"]
)
def test_a_redirect_is_checked_in_proxy_mode_and_a_refused_one_never_tunnelled(
    location: str, ca_file: Path
) -> None:
    routes = {"/go": Scripted(302, headers=(("Location", location),))}
    with through_proxy(routes) as (server, proxy):
        result = failure(
            proxied(server.port, proxy, ca_file).fetch(
                f"http://{HOST}:{server.port}/go", accept=HTML_TYPES
            )
        )

    assert result.outcome is AttemptStatus.BLOCKED
    assert result.redirects == ()
    assert proxy.connects() == [f"{HOST}:{server.port}"]


@pytest.mark.req("ACQ-02")
def test_the_size_limit_holds_in_proxy_mode(ca_file: Path) -> None:
    with through_proxy({"/big": Scripted(body=b"x" * 5_000)}) as (server, proxy):
        f = proxied(server.port, proxy, ca_file, FetchLimits(max_bytes=1_000))
        result = failure(f.fetch(f"http://{HOST}:{server.port}/big", accept=None))

    assert result.reason == "too_large"


@pytest.mark.req("ACQ-02")
def test_a_proxy_s_refusal_is_a_connection_failure_that_is_not_retried(ca_file: Path) -> None:
    with through_proxy({"/jobs/1": Scripted(body=PAGE)}) as (server, proxy):
        proxy.routes[f"{HOST}:{server.port}"] = "403 Forbidden"
        f = proxied(server.port, proxy, ca_file)
        fetched = failure(f.fetch(f"http://{HOST}:{server.port}/jobs/1", accept=HTML_TYPES))
        page = failure(f.fetch_page(f"http://{HOST}:{server.port}/jobs/1"))

    assert (fetched.outcome, fetched.reason, fetched.transient) == (
        AttemptStatus.FAILED,
        "connection_failed",
        False,
    )
    assert fetched.http_status is None  # the proxy's status is never taken for the site's
    # A refused robots.txt is unreachable, never a 4xx that would allow everything.
    assert (page.reason, page.transient) == ("robots_unreachable", False)
    assert server.paths() == []


@pytest.mark.req("ACQ-02")
def test_an_unreachable_proxy_is_a_transient_connection_failure(ca_file: Path) -> None:
    with fake_proxy() as proxy:
        url = proxy.url
    f = Fetcher(
        user_agent="CareerwrightL0/test", resolve=_no_lookup, proxy=fetch_proxy(url, ca_file)
    )

    result = failure(f.fetch("https://jobs.example.com/", accept=HTML_TYPES))

    assert (result.reason, result.transient) == ("connection_failed", True)


# TLS through the proxy: a test CA and a certificate for the page's name.


@contextmanager
def tls_server(cert: Path, key: Path) -> Iterator[int]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            body = b"User-agent: *\nAllow: /\n" if self.path == "/robots.txt" else PAGE
            kind = "text/plain" if self.path == "/robots.txt" else "text/html"
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, args=(0.02,), daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.req("ACQ-01")
def test_https_through_the_proxy_is_verified_against_the_named_bundle(tmp_path: Path) -> None:
    ca = make_ca()
    trusted = ca.bundle(tmp_path / "trusted.pem")
    other = make_ca().bundle(tmp_path / "other.pem")  # a CA that did not sign the page's
    cert, key = make_leaf(ca, "secure.test.example", tmp_path)

    with tls_server(cert, key) as port, fake_proxy() as proxy:
        proxy.routes[f"secure.test.example:{port}"] = port
        url = f"https://secure.test.example:{port}/jobs/1"

        def fetcher(bundle: Path) -> Fetcher:
            return Fetcher(
                resolve=_no_lookup,
                user_agent="CareerwrightL0/test",
                extra_allowed=frozenset({("127.0.0.1", port)}),
                proxy=fetch_proxy(proxy.url, bundle),
            )

        verified = fetcher(trusted).fetch_page(url)
        unverified = failure(fetcher(other).fetch(url, accept=HTML_TYPES))

    assert isinstance(verified, Fetched)
    assert verified.body == PAGE
    assert (unverified.reason, unverified.outcome) == ("tls_failed", AttemptStatus.FAILED)


# The settings: explicit and checked.


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:3128",  # the proxy is spoken to in plain HTTP, CONNECT only
        "socks5://127.0.0.1:1080",
        "http://127.0.0.1",  # no port
        "http://user:secret@127.0.0.1:3128",
        "http://127.0.0.1:3128/path",
        "http://127.0.0.1:3128?q=1",
        "http://:3128",
        "http://127.0.0.1:notaport",
    ],
)
def test_a_proxy_url_proxy_mode_cannot_use_is_refused_without_repeating_it(
    url: str, ca_file: Path
) -> None:
    with pytest.raises(ProxyConfigError) as refused:
        fetch_proxy(url, ca_file)

    assert url not in str(refused.value)
    assert "secret" not in str(refused.value)


def test_proxy_mode_needs_its_ca_bundle(tmp_path: Path) -> None:
    with pytest.raises(ProxyConfigError, match="CA bundle"):
        fetch_proxy("http://127.0.0.1:3128", tmp_path / "missing.pem")
    with pytest.raises(ProxyConfigError, match="CA bundle"):
        fetch_proxy("http://127.0.0.1:3128", tmp_path)


def test_a_proxy_url_s_parts_are_kept(ca_file: Path) -> None:
    assert fetch_proxy("http://127.0.0.1:42367", ca_file) == FetchProxy("127.0.0.1", 42367, ca_file)


# The product never selects it.


@pytest.mark.req("ACQ-01")
def test_the_default_fetcher_ignores_a_proxy_in_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with (
        source_server({"/robots.txt": ROBOTS, "/jobs/1": Scripted(body=PAGE)}) as server,
        fake_proxy() as proxy,
    ):
        proxy.routes[f"{HOST}:{server.port}"] = server.port
        for name in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "ALL_PROXY"):
            monkeypatch.setenv(name, proxy.url)
        f = Fetcher(
            resolve=lambda host, port: [ipaddress.ip_address("127.0.0.1")],
            user_agent="CareerwrightL0/test",
            extra_allowed=frozenset({("127.0.0.1", server.port)}),
        )
        result = f.fetch_page(f"http://{HOST}:{server.port}/jobs/1")

    assert isinstance(result, Fetched)
    assert result.address == "127.0.0.1"  # direct, to the checked address
    assert f.via_proxy is False
    assert proxy.lines == []


@pytest.mark.req("ACQ-01", "SEC-05")
def test_the_restricted_worker_s_settings_refuse_proxy_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CAREERWRIGHT_ENVIRONMENT", "local")
    assert AcquisitionSettings().fetch_proxy is None

    monkeypatch.setenv("CAREERWRIGHT_FETCH_PROXY", "http://127.0.0.1:3128")
    with pytest.raises(ValidationError):
        AcquisitionSettings()


@pytest.mark.req("ACQ-01", "SEC-05")
def test_the_restricted_worker_builds_its_fetcher_without_a_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CAREERWRIGHT_ENVIRONMENT", "local")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:3128")
    monkeypatch.setattr(sys, "argv", ["careerwright.acquisition"])
    monkeypatch.setattr(acquisition, "configure_logging", lambda name: None)
    built: list[acquisition.AcquisitionService] = []

    class Stopped:
        def serve_forever(self, poll_interval: float) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            return

    def make_server(service: acquisition.AcquisitionService, host: str, port: int) -> Stopped:
        built.append(service)
        return Stopped()

    monkeypatch.setattr(acquisition, "make_server", make_server)
    acquisition.main()

    [service] = built
    assert service._fetcher.via_proxy is False


def test_no_product_module_can_reach_proxy_mode() -> None:
    """Only the fetcher itself names proxy mode: no product module imports `FetchProxy` or
    `fetch_proxy`, or passes `proxy=` to anything."""
    found: list[str] = []
    for path in SRC.rglob("*.py"):
        if path == SRC / "evidence" / "fetcher.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(
                a.name in {"FetchProxy", "fetch_proxy"} for a in node.names
            ):
                found.append(f"{path.name}: imports {[a.name for a in node.names]}")
            if isinstance(node, ast.Call) and any(k.arg == "proxy" for k in node.keywords):
                found.append(f"{path.name}:{node.lineno}: proxy=")
            if isinstance(node, ast.Attribute) and node.attr in {"FetchProxy", "fetch_proxy"}:
                found.append(f"{path.name}:{node.lineno}: {node.attr}")

    assert found == []
