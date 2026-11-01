"""Guarded HTTP retrieval for the restricted acquisition worker (adapter: httpcore2; spec
section 6, "Retrieval pipeline and security boundary"; ADR 0009).

Scrapling's own HTTP fetcher cannot be used: in the pinned releases it imports Playwright,
Patchright and browserforge at import time, and the backend excludes browser automation
(spec section 6, GC2). This client does the HTTP retrieval instead, on the HTTP core already
in the lock, and Scrapling parses (`careerwright.evidence.pages`).

Every hop is checked before it is requested: the URL (`addresses.check_url`), then, at
connect time, every address the host resolves to (`addresses.address_refusal`); the
connection goes to an address that passed, so no later DNS answer can change it. A redirect
target is checked before it is recorded or followed, and is a new hop with the same checks;
https never redirects down to http. For a page, each new host a page or its redirects reach
(robots.txt included) is admitted by the caller first (the source permission manifest and
the pacer, `acquire.acquire_page`), and every hop's URL is checked against its origin's
robots.txt (RFC 9309) before it is requested. One deadline bounds the whole page fetch, in
every phase: the name lookup, each connect (at most `MAX_ADDRESSES` tried), every read and
write, TLS and the response's status line and headers. The response is bounded in
redirects, size (decompressed size too) and content type. Failures are labels, classified
from types and statuses only; no exception message or response body is kept.

Proxy mode (`FetchProxy`; ADR 0009, 2026-11-01 amendment) is for the controller's tools
alone, in an environment whose only way out is an allowlisting HTTPS proxy: each connection
is a CONNECT tunnel through that proxy, and TLS is verified against the CA bundle it names.
The proxy, not Careerwright, then picks the address it connects to, so the resolved-address
check does not run (no name is looked up here); every other check stays. The product never
selects it: the restricted worker builds its fetcher without one and its settings refuse one.
"""

import ipaddress
import math
import re
import socket
import ssl
import threading
import time
import zlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import certifi
import httpcore2

from careerwright.evidence.addresses import (
    ALLOWED_PORTS,
    DEFAULT_PORTS,
    CheckedUrl,
    IPAddress,
    UrlRefusal,
    address_refusal,
    check_url,
)
from careerwright.evidence.records import AttemptStatus

HTML_TYPES = frozenset({"text/html", "application/xhtml+xml"})
JSON_TYPES = frozenset({"application/json"})
TRANSIENT_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
ROBOTS_TOKEN = "CareerwrightL0"  # noqa: S105 - the robots.txt user-agent token, not a secret
ROBOTS_MAX_BYTES = 512_000  # RFC 9309: parse at least 500 KiB
ROBOTS_CACHE_S = 600.0
HTTP_ERROR = "http_error"  # the status itself is the failure's `http_status`
MAX_ADDRESSES = 4  # tried in turn when a name resolves to several
MAX_PROXY_REPLY = 8_192  # a CONNECT reply's status line and headers

Resolve = Callable[[str, int], list[IPAddress]]
# Called before the first request to each host of a page fetch, with the seconds left of its
# time bound: None once the host is admitted (and paced), `PACING_TIMEOUT` when its pacing
# would outlast the bound (a transient failure), else the refusal label (blocked).
Admit = Callable[[CheckedUrl, float], str | None]
PACING_TIMEOUT = "timeout"


@dataclass(frozen=True)
class FetchLimits:
    max_bytes: int = 2_000_000
    total_s: float = 20.0
    connect_s: float = 5.0
    read_s: float = 10.0
    max_redirects: int = 5


DEFAULT_LIMITS = FetchLimits()


@dataclass(frozen=True)
class FetchProxy:
    """An explicit HTTPS proxy reached in plain HTTP and spoken to only with CONNECT, and the
    CA bundle that TLS through it is verified against. Built by `fetch_proxy`."""

    host: str
    port: int
    ca_file: Path


class ProxyConfigError(ValueError):
    """A proxy URL or CA bundle that proxy mode cannot use. Its message never repeats the
    URL, which may come from the environment."""


def fetch_proxy(url: str, ca_file: Path) -> FetchProxy:
    """Proxy mode's settings, checked: an `http://host:port` URL with no credentials, path,
    query or fragment, and a CA bundle that is a readable file. TLS verification is never
    turned off: the bundle is required."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        raise ProxyConfigError("the proxy URL does not parse") from None
    if parts.scheme != "http" or not parts.hostname or port is None:
        raise ProxyConfigError("the proxy URL must be http://host:port")
    if parts.username is not None or parts.password is not None:
        raise ProxyConfigError("the proxy URL may not hold credentials")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise ProxyConfigError("the proxy URL may hold only a host and a port")
    if not ca_file.is_file():
        raise ProxyConfigError("the proxy's CA bundle is not a file")
    return FetchProxy(parts.hostname, port, ca_file)


@dataclass(frozen=True)
class Fetched:
    requested_url: str
    final_url: str
    redirects: tuple[str, ...]
    status: int
    content_type: str
    charset: str | None
    body: bytes  # after any content encoding is undone
    address: str | None  # the address the last hop connected to
    requests: int = 0  # HTTP requests sent for it, robots.txt included

    @property
    def text(self) -> str:
        try:
            return self.body.decode(self.charset or "utf-8", errors="replace")
        except LookupError:  # a charset Python does not know
            return self.body.decode("utf-8", errors="replace")


@dataclass(frozen=True)
class FetchFailure:
    requested_url: str
    outcome: AttemptStatus  # BLOCKED by policy, or FAILED when tried
    reason: str
    redirects: tuple[str, ...] = ()  # checked URLs only: a refused target is never recorded
    final_url: str | None = None
    http_status: int | None = None
    transient: bool = False
    address: str | None = None
    requests: int = 0  # HTTP requests sent for it, robots.txt included


class HostNotFoundError(Exception):
    """The name does not exist (not a temporary lookup failure)."""


class _AddressRefusedError(Exception):
    pass


class _TooLargeError(Exception):
    pass


class _ProxyRefusedError(Exception):
    """The proxy answered CONNECT with a status other than 2xx (a policy denial, most
    often): not retried."""


def _resolve_within(resolve: Resolve, host: str, port: int, timeout: float) -> list[IPAddress]:
    """The lookup, given at most `timeout` seconds. The system resolver cannot be
    interrupted, so it runs on a daemon thread that is left to finish on its own."""
    outcome: list[list[IPAddress] | BaseException] = []

    def lookup() -> None:
        try:
            outcome.append(resolve(host, port))
        except BaseException as error:  # handed to the caller as it was
            outcome.append(error)

    thread = threading.Thread(target=lookup, name="careerwright-resolve", daemon=True)
    thread.start()
    thread.join(timeout)
    if not outcome:
        raise httpcore2.ConnectTimeout
    if isinstance(outcome[0], BaseException):
        raise outcome[0]
    return outcome[0]


class _BoundedStream(httpcore2.NetworkStream):
    """A connection whose every read, write and TLS start waits at most the per-operation
    timeout or what is left before the deadline, whichever is less, so a server trickling
    its status line or sending 1xx responses without end cannot outlast the bound."""

    def __init__(
        self, inner: httpcore2.NetworkStream, deadline: float, clock: Callable[[], float]
    ) -> None:
        self._inner = inner
        self._deadline = deadline
        self._clock = clock

    def _within(self, timeout: float | None, expired: type[Exception]) -> float:
        remaining = self._deadline - self._clock()
        if remaining <= 0:
            raise expired
        return remaining if timeout is None else min(timeout, remaining)

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        return self._inner.read(max_bytes, self._within(timeout, httpcore2.ReadTimeout))

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        self._inner.write(buffer, self._within(timeout, httpcore2.WriteTimeout))

    def close(self) -> None:
        self._inner.close()

    def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str | None = None,
        timeout: float | None = None,
    ) -> httpcore2.NetworkStream:
        inner = self._inner.start_tls(
            ssl_context, server_hostname, self._within(timeout, httpcore2.ConnectTimeout)
        )
        return _BoundedStream(inner, self._deadline, self._clock)

    def get_extra_info(self, info: str) -> Any:
        return self._inner.get_extra_info(info)


def system_resolve(host: str, port: int) -> list[IPAddress]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        if error.errno == socket.EAI_AGAIN:
            raise httpcore2.ConnectError() from None  # temporary: transient
        raise HostNotFoundError from None
    found: list[IPAddress] = []
    for info in infos:
        try:
            found.append(ipaddress.ip_address(info[4][0]))
        except ValueError:  # a scoped (link-local) address: never allowed
            raise _AddressRefusedError from None
    return found


class _GuardedBackend(httpcore2.NetworkBackend):
    """Resolves at connect time, refuses the host if any answer is not allowed, and connects
    to an address that passed; all within the deadline. In proxy mode it looks nothing up:
    it opens a CONNECT tunnel to the host's name through the proxy, and `address` stays
    None, since Careerwright never learns or checks the address the proxy chose."""

    def __init__(
        self,
        resolve: Resolve,
        allowed: Callable[[IPAddress, int], bool],
        deadline: float,
        clock: Callable[[], float],
        proxy: FetchProxy | None = None,
    ) -> None:
        self._resolve = resolve
        self._allowed = allowed
        self._deadline = deadline
        self._clock = clock
        self._proxy = proxy
        self._inner = httpcore2.SyncBackend()
        self.address: str | None = None

    def _tunnel(
        self,
        proxy: FetchProxy,
        host: str,
        port: int,
        timeout: float | None,
        socket_options: Iterable[httpcore2.SOCKET_OPTION] | None,
    ) -> httpcore2.NetworkStream:
        """A CONNECT tunnel to `host:port` through the proxy, once it answers 2xx with
        nothing after its headers."""
        stream = _BoundedStream(
            self._inner.connect_tcp(
                proxy.host, proxy.port, timeout=self._within(timeout), socket_options=socket_options
            ),
            self._deadline,
            self._clock,
        )
        try:
            authority = f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
            stream.write(
                f"CONNECT {authority} HTTP/1.1\r\nHost: {authority}\r\n\r\n".encode("ascii"),
                timeout,
            )
            reply = b""
            while b"\r\n\r\n" not in reply:
                if len(reply) > MAX_PROXY_REPLY:
                    raise httpcore2.RemoteProtocolError
                chunk = stream.read(MAX_PROXY_REPLY, timeout)
                if not chunk:
                    raise httpcore2.ConnectError
                reply += chunk
            head, _, rest = reply.partition(b"\r\n\r\n")
            version, _, status = head.split(b"\r\n", 1)[0].partition(b" ")
            code = status[:3]
            if rest or not version.startswith(b"HTTP/1.") or not code.isdigit():
                raise httpcore2.RemoteProtocolError
            if not 200 <= int(code) < 300:
                raise _ProxyRefusedError
        except BaseException:
            stream.close()
            raise
        return stream

    def _within(self, timeout: float | None) -> float:
        remaining = self._deadline - self._clock()
        if remaining <= 0:
            raise httpcore2.ConnectTimeout
        return remaining if timeout is None else min(timeout, remaining)

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[httpcore2.SOCKET_OPTION] | None = None,
    ) -> httpcore2.NetworkStream:
        if self._proxy is not None:
            return self._tunnel(self._proxy, host, port, timeout, socket_options)
        addresses = _resolve_within(self._resolve, host, port, self._within(timeout))
        if not addresses or not all(self._allowed(a, port) for a in addresses):
            raise _AddressRefusedError
        last: Exception = httpcore2.ConnectError()
        for address in addresses[:MAX_ADDRESSES]:
            try:
                stream = self._inner.connect_tcp(
                    str(address),
                    port,
                    timeout=self._within(timeout),
                    local_address=local_address,
                    socket_options=socket_options,
                )
            except (httpcore2.ConnectError, httpcore2.ConnectTimeout) as error:
                last = error
                continue
            self.address = str(address)
            return _BoundedStream(stream, self._deadline, self._clock)
        raise last

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Iterable[httpcore2.SOCKET_OPTION] | None = None,
    ) -> httpcore2.NetworkStream:
        raise _AddressRefusedError


@dataclass(frozen=True)
class _Redirect:
    location: str


@dataclass
class _Body:
    """Collects a body within the byte limit, undoing gzip or deflate as it arrives."""

    limit: int
    encoding: str
    parts: list[bytes] = field(default_factory=list)
    size: int = 0
    raw: int = 0

    def __post_init__(self) -> None:
        self._inflate = zlib.decompressobj(zlib.MAX_WBITS | 16) if self.encoding == "gzip" else None
        self._deflate_started = False

    def _keep(self, data: bytes) -> None:
        self.size += len(data)
        if self.size > self.limit:
            raise _TooLargeError
        self.parts.append(data)

    def feed(self, chunk: bytes) -> None:
        self.raw += len(chunk)
        if self.raw > self.limit:
            raise _TooLargeError
        if self.encoding == "identity":
            self._keep(chunk)
            return
        if self._inflate is None:  # deflate: zlib-wrapped, or raw as some servers send it
            wrapped = chunk[:1] == b"\x78"
            self._inflate = zlib.decompressobj(zlib.MAX_WBITS if wrapped else -zlib.MAX_WBITS)
        data = chunk
        while data:
            try:
                out = self._inflate.decompress(data, self.limit - self.size + 1)
            except zlib.error:
                raise _TooLargeError from None  # corrupt compression is never kept
            self._keep(out)
            data = self._inflate.unconsumed_tail

    def body(self) -> bytes:
        if self._inflate is not None:
            self._keep(self._inflate.flush())
        return b"".join(self.parts)


_UNRESERVED = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_HEX = frozenset(b"0123456789abcdefABCDEF")
_AGENT = re.compile(r"[A-Za-z0-9_-]+|\*")


def _normalise(value: str) -> str:
    """A path or rule as octets to compare (RFC 9309 section 2.2.2): octets outside printable
    US-ASCII percent-encoded, percent-encoded unreserved characters decoded, other
    percent-encodings in upper case."""
    data = value.encode("utf-8")
    out: list[str] = []
    i = 0
    while i < len(data):
        octet = data[i]
        if octet == 0x25 and i + 2 < len(data) and data[i + 1] in _HEX and data[i + 2] in _HEX:
            decoded = int(data[i + 1 : i + 3], 16)
            out.append(chr(decoded) if decoded in _UNRESERVED else f"%{decoded:02X}")
            i += 3
            continue
        out.append(chr(octet) if 0x20 < octet < 0x7F else f"%{octet:02X}")
        i += 1
    return "".join(out)


def _rule_matches(pattern: str, path: str) -> bool:
    """Whether a rule matches the path from its start: `*` is any run of characters and a
    final `$` the end of the path. Iterative, so a hostile pattern costs at most the product
    of the two lengths."""
    pattern = pattern[:-1] if pattern.endswith("$") else f"{pattern}*"
    p = t = 0
    star, mark = -1, 0
    while t < len(path):
        if p < len(pattern) and pattern[p] == "*":
            star, mark = p, t
            p += 1
        elif p < len(pattern) and pattern[p] == path[t]:
            p += 1
            t += 1
        elif star != -1:
            p, mark = star + 1, mark + 1
            t = mark
        else:
            return False
    return all(c == "*" for c in pattern[p:])


@dataclass(frozen=True)
class RobotsRules:
    """The allow and disallow rules that apply to one product token."""

    rules: tuple[tuple[bool, str], ...] = ()  # (allow, normalised path pattern)

    def allows(self, path: str) -> bool:
        """`path`: the URL's path with its query. The matching rule with the most octets
        decides, an allow rule winning a tie; no matching rule allows (RFC 9309 section
        2.2.2). `/robots.txt` itself is always allowed."""
        target = _normalise(path or "/")
        if target == "/robots.txt":
            return True
        best: tuple[int, bool] | None = None
        for allow, pattern in self.rules:
            if _rule_matches(pattern, target) and (best is None or (len(pattern), allow) > best):
                best = (len(pattern), allow)
        return best is None or best[1]


def parse_robots(text: str, token: str) -> RobotsRules:
    """The rules for `token` (RFC 9309 section 2.2.1): every group with a user-agent line
    naming it, without regard to case, combined; failing that every `*` group combined;
    failing that none. Consecutive user-agent lines open one group; other records (a
    sitemap, a crawl delay) are ignored without ending it; a rule before any group is
    ignored."""
    groups: list[tuple[set[str], list[tuple[bool, str]]]] = []
    in_rules = False
    for raw in text.removeprefix("﻿").splitlines():
        key, colon, value = raw.partition("#")[0].partition(":")
        if not colon:
            continue
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if not groups or in_rules:
                groups.append((set(), []))
                in_rules = False
            agent = _AGENT.match(value)
            if agent is not None:
                groups[-1][0].add(agent.group().lower())
        elif key in ("allow", "disallow") and groups:
            in_rules = True
            if value:
                groups[-1][1].append((key == "allow", _normalise(value)))
    wanted = token.lower()
    if not any(wanted in agents for agents, _ in groups):
        wanted = "*"
    return RobotsRules(
        tuple(rule for agents, rules in groups if wanted in agents for rule in rules)
    )


def redirect_target(
    current: CheckedUrl, location: str, allowed_ports: frozenset[int] = ALLOWED_PORTS
) -> CheckedUrl | str:
    """Where a redirect from `current` leads, checked, or the refusal label: a target that
    fails the URL checks, or http after https, is refused before it is recorded."""
    target = check_url(urljoin(current.url, location), allowed_ports=allowed_ports)
    if isinstance(target, UrlRefusal):
        return target.value
    if current.scheme == "https" and target.scheme == "http":
        return "redirect_downgrade"
    return target


def _header(headers: list[tuple[bytes, bytes]], name: bytes) -> str | None:
    for key, value in headers:
        if key.lower() == name:
            return value.decode("latin-1").strip()
    return None


def _content_type(value: str | None) -> tuple[str, str | None]:
    if not value:
        return "", None
    kind, _, params = value.partition(";")
    charset = None
    for param in params.split(";"):
        key, _, val = param.strip().partition("=")
        if key.lower() == "charset" and val:
            charset = val.strip().strip('"').lower()
    return kind.strip().lower(), charset


class Fetcher:
    """`extra_allowed` names (host, port) origins that the address and port checks let
    through: only the controlled test server's, never set in production (`careerwright.acquisition`
    constructs this with none). `proxy`: proxy mode, for the controller's tools only (the
    module's docstring); never set in production either."""

    def __init__(
        self,
        *,
        resolve: Resolve = system_resolve,
        limits: FetchLimits = DEFAULT_LIMITS,
        user_agent: str,
        extra_allowed: frozenset[tuple[str, int]] = frozenset(),
        clock: Callable[[], float] = time.monotonic,
        proxy: FetchProxy | None = None,
    ) -> None:
        self._resolve = resolve
        self.limits = limits
        self._user_agent = user_agent
        self._extra_allowed = extra_allowed
        self._ports = ALLOWED_PORTS | {port for _, port in extra_allowed}
        self._clock = clock
        self._proxy = proxy
        # Verification stays on in both modes; proxy mode trusts its own bundle instead.
        cafile = str(proxy.ca_file) if proxy is not None else certifi.where()
        self._ssl = ssl.create_default_context(cafile=cafile)
        self._robots: dict[str, tuple[float, RobotsRules]] = {}

    @property
    def via_proxy(self) -> bool:
        """Whether this fetcher is in proxy mode, where no resolved address is checked."""
        return self._proxy is not None

    def check(self, url: str) -> CheckedUrl | UrlRefusal:
        """`addresses.check_url` with this fetcher's ports."""
        return check_url(url, allowed_ports=self._ports)

    def _address_allowed(self, address: IPAddress, port: int) -> bool:
        return (str(address), port) in self._extra_allowed or address_refusal(address) is None

    def _blocked(self, requested: str, reason: str, redirects: list[str]) -> FetchFailure:
        return FetchFailure(requested, AttemptStatus.BLOCKED, reason, tuple(redirects))

    def fetch(
        self, url: str, *, accept: frozenset[str] | None, max_bytes: int | None = None
    ) -> Fetched | FetchFailure:
        """One bounded GET, following checked redirects, with no robots.txt and no host
        admission (an API request). `accept`: the content types taken (None takes any)."""
        checked = check_url(url, allowed_ports=self._ports)
        if isinstance(checked, UrlRefusal):
            return self._blocked(url, checked.value, [])
        visit = _Visit(self._clock() + self.limits.total_s, admit=None)
        return self._follow(
            checked, accept=accept, limit=max_bytes or self.limits.max_bytes, visit=visit
        )

    def _follow(
        self,
        checked: CheckedUrl,
        *,
        accept: frozenset[str] | None,
        limit: int,
        visit: "_Visit",
        robots: bool = False,
    ) -> Fetched | FetchFailure:
        """GETs from `checked`, following redirects. With `robots`, every hop's URL is
        checked against its origin's robots.txt first."""
        requested = checked.url
        redirects: list[str] = []
        backend = _GuardedBackend(
            self._resolve, self._address_allowed, visit.deadline, self._clock, self._proxy
        )
        with httpcore2.ConnectionPool(
            ssl_context=self._ssl,
            network_backend=backend,
            retries=0,
            max_connections=1,
            http1=True,
            http2=False,
        ) as pool:
            for _hop in range(self.limits.max_redirects + 1):
                refusal = self._before_request(checked, visit, robots=robots)
                if refusal is not None:
                    return replace(
                        refusal,
                        requested_url=requested,
                        redirects=tuple(redirects),
                        final_url=checked.url,
                        requests=visit.requests,
                    )
                visit.requests += 1
                result = self._get(pool, backend, checked, accept, limit, visit.deadline)
                if isinstance(result, _Redirect):
                    target = redirect_target(checked, result.location, self._ports)
                    if isinstance(target, str):
                        return replace(
                            self._blocked(requested, target, redirects), requests=visit.requests
                        )
                    redirects.append(target.url)
                    checked = target
                    continue
                if isinstance(result, FetchFailure):
                    return FetchFailure(
                        requested,
                        result.outcome,
                        result.reason,
                        tuple(redirects),
                        checked.url,
                        result.http_status,
                        result.transient,
                        backend.address,
                        visit.requests,
                    )
                return Fetched(
                    requested,
                    checked.url,
                    tuple(redirects),
                    result.status,
                    result.content_type,
                    result.charset,
                    result.body,
                    backend.address,
                    visit.requests,
                )
        return FetchFailure(
            requested,
            AttemptStatus.FAILED,
            "too_many_redirects",
            tuple(redirects),
            checked.url,
            requests=visit.requests,
        )

    def _before_request(
        self, checked: CheckedUrl, visit: "_Visit", *, robots: bool
    ) -> FetchFailure | None:
        """A hop's checks before its request: its address, its host's admission when the
        visit reaches the host for the first time, and its origin's robots.txt."""
        if checked.ip_literal is not None and not self._address_allowed(
            checked.ip_literal, checked.port
        ):
            return FetchFailure(
                checked.url, AttemptStatus.BLOCKED, UrlRefusal.ADDRESS_NOT_ALLOWED.value
            )
        if visit.admit is not None and checked.host not in visit.admitted:
            reason = visit.admit(checked, visit.deadline - self._clock())
            if reason == PACING_TIMEOUT:
                return FetchFailure(checked.url, AttemptStatus.FAILED, reason, transient=True)
            if reason is not None:
                return FetchFailure(checked.url, AttemptStatus.BLOCKED, reason)
            visit.admitted.add(checked.host)
        return self._robots_refusal(checked, visit) if robots else None

    def _get(
        self,
        pool: httpcore2.ConnectionPool,
        backend: _GuardedBackend,
        checked: CheckedUrl,
        accept: frozenset[str] | None,
        limit: int,
        deadline: float,
    ) -> Fetched | FetchFailure | _Redirect:
        def failed(
            reason: str, *, status: int | None = None, transient: bool = False
        ) -> FetchFailure:
            return FetchFailure(
                checked.url, AttemptStatus.FAILED, reason, http_status=status, transient=transient
            )

        remaining = deadline - self._clock()
        if remaining <= 0:
            return failed("timeout", transient=True)
        host = (
            checked.host
            if checked.ip_literal is None or checked.ip_literal.version == 4
            else f"[{checked.host}]"
        )
        if checked.port != DEFAULT_PORTS[checked.scheme]:
            host = f"{host}:{checked.port}"
        headers = [
            (b"Host", host.encode()),
            (b"User-Agent", self._user_agent.encode()),
            (b"Accept", b"text/html,application/xhtml+xml,application/json;q=0.9,text/plain;q=0.8"),
            (b"Accept-Encoding", b"gzip, deflate"),
        ]
        timeouts = {
            "connect": min(self.limits.connect_s, remaining),
            "read": min(self.limits.read_s, remaining),
            "write": min(self.limits.read_s, remaining),
            "pool": min(self.limits.connect_s, remaining),
        }
        try:
            with pool.stream(
                "GET", checked.url, headers=headers, extensions={"timeout": timeouts}
            ) as response:
                status = response.status
                if status in REDIRECT_STATUSES:
                    location = _header(response.headers, b"location")
                    return _Redirect(location) if location else failed(HTTP_ERROR, status=status)
                if status >= 400:
                    return failed(HTTP_ERROR, status=status, transient=status in TRANSIENT_STATUSES)
                if not 200 <= status < 300 or status == 204:
                    return failed(HTTP_ERROR, status=status)
                content_type, charset = _content_type(_header(response.headers, b"content-type"))
                if accept is not None and content_type not in accept:
                    return failed("unsupported_content_type", status=status)
                encoding = (_header(response.headers, b"content-encoding") or "identity").lower()
                if encoding not in ("identity", "gzip", "deflate"):
                    return failed("unsupported_content_encoding", status=status)
                declared = _header(response.headers, b"content-length")
                if declared is not None and declared.isdigit() and int(declared) > limit:
                    return failed("too_large", status=status)
                body = _Body(limit, encoding)
                for chunk in response.iter_stream():
                    body.feed(chunk)
                return Fetched(
                    checked.url, checked.url, (), status, content_type, charset, body.body(), None
                )
        except _AddressRefusedError:
            return FetchFailure(
                checked.url, AttemptStatus.BLOCKED, UrlRefusal.ADDRESS_NOT_ALLOWED.value
            )
        except _TooLargeError:
            return failed("too_large")
        except _ProxyRefusedError:
            return failed("connection_failed")  # the proxy's refusal: not retried
        except (
            httpcore2.ConnectTimeout,
            httpcore2.ReadTimeout,
            httpcore2.WriteTimeout,
            httpcore2.PoolTimeout,
        ):
            return failed("timeout", transient=True)
        except HostNotFoundError:
            return failed("host_not_found")
        except httpcore2.ConnectError as error:
            if isinstance(error.__context__, ssl.SSLError) or isinstance(
                error.__cause__, ssl.SSLError
            ):
                return failed("tls_failed")
            return failed("connection_failed", transient=True)
        except (httpcore2.NetworkError, httpcore2.ProtocolError):
            return failed("connection_failed", transient=True)

    def _robots_refusal(self, checked: CheckedUrl, visit: "_Visit") -> FetchFailure | None:
        """None when robots.txt allows the URL; otherwise why not (RFC 9309 section 2.3.1:
        a 4xx robots.txt allows everything; one that cannot be reached disallows, as a
        transient failure that is not remembered, so the next try reads it again). The
        robots.txt request is part of the visit: its time, its count and its redirects'
        admission."""
        root = urlsplit(checked.url)
        origin = f"{root.scheme}://{root.netloc}"
        cached = self._robots.get(origin)
        if cached is None or self._clock() - cached[0] > ROBOTS_CACHE_S:
            result = self._follow(
                replace(checked, url=f"{origin}/robots.txt"),
                accept=None,
                limit=ROBOTS_MAX_BYTES,
                visit=visit,
            )
            if isinstance(result, Fetched):
                rules = parse_robots(result.text, ROBOTS_TOKEN)
            elif result.http_status is not None and 400 <= result.http_status < 500:
                rules = RobotsRules()  # unavailable: no restrictions
            else:
                return FetchFailure(
                    checked.url,
                    AttemptStatus.FAILED,
                    "robots_unreachable",
                    transient=result.transient,
                )
            cached = (self._clock(), rules)
            self._robots[origin] = cached
        parts = urlsplit(checked.url)
        if not cached[1].allows(f"{parts.path or '/'}{'?' if parts.query else ''}{parts.query}"):
            return FetchFailure(checked.url, AttemptStatus.BLOCKED, "robots_disallowed")
        return None

    def fetch_page(self, url: str, admit: Admit | None = None) -> Fetched | FetchFailure:
        """A page (HTML only): its URL checked; then, for each hop, its host admitted the
        first time the visit reaches it (`admit`, first host included), its origin's
        robots.txt, and the request. The time bound starts once the first host is admitted,
        so the pacer's wait for it is not counted against the page."""
        checked = check_url(url, allowed_ports=self._ports)
        if isinstance(checked, UrlRefusal):
            return self._blocked(url, checked.value, [])
        visit = _Visit(0.0, admit=admit)
        if admit is not None:
            reason = admit(checked, math.inf)  # before the bound starts: the pacer may wait
            if reason is not None:
                return FetchFailure(checked.url, AttemptStatus.BLOCKED, reason)
            visit.admitted.add(checked.host)
        visit.deadline = self._clock() + self.limits.total_s
        return self._follow(
            checked, accept=HTML_TYPES, limit=self.limits.max_bytes, visit=visit, robots=True
        )


@dataclass
class _Visit:
    """One fetch's shared state across its hops and robots.txt requests."""

    deadline: float
    admit: Admit | None
    admitted: set[str] = field(default_factory=set)
    requests: int = 0
