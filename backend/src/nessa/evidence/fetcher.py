"""Guarded HTTP retrieval for the restricted acquisition worker (adapter: httpcore2; spec
section 6, "Retrieval pipeline and security boundary"; ADR 0009).

Scrapling's own HTTP fetcher cannot be used: in the pinned releases it imports Playwright,
Patchright and browserforge at import time, and the backend excludes browser automation
(spec section 6, GC2). This client does the HTTP retrieval instead, on the HTTP core already
in the lock, and Scrapling parses (`nessa.evidence.pages`).

Every hop is checked before it is requested: the URL (`addresses.check_url`), then, at
connect time, every address the host resolves to (`addresses.address_refusal`); the
connection goes to an address that passed, so no later DNS answer can change it. A redirect
is a new hop with the same checks; https never redirects down to http. The response is
bounded in redirects, total time, size (decompressed size too) and content type. A page
fetch reads robots.txt first (RFC 9309). Failures are labels, classified from types and
statuses only; no exception message or response body is kept.
"""

import ipaddress
import re
import socket
import ssl
import time
import zlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from urllib.parse import urljoin, urlsplit

import certifi
import httpcore2

from nessa.evidence.addresses import (
    ALLOWED_PORTS,
    DEFAULT_PORTS,
    CheckedUrl,
    IPAddress,
    UrlRefusal,
    address_refusal,
    check_url,
)
from nessa.evidence.records import AttemptStatus

HTML_TYPES = frozenset({"text/html", "application/xhtml+xml"})
JSON_TYPES = frozenset({"application/json"})
TRANSIENT_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
ROBOTS_TOKEN = "NessaL0"  # noqa: S105 - the robots.txt user-agent token, not a secret
ROBOTS_MAX_BYTES = 512_000  # RFC 9309: parse at least 500 KiB
ROBOTS_CACHE_S = 600.0

Resolve = Callable[[str, int], list[IPAddress]]


@dataclass(frozen=True)
class FetchLimits:
    max_bytes: int = 2_000_000
    total_s: float = 20.0
    connect_s: float = 5.0
    read_s: float = 10.0
    max_redirects: int = 5


DEFAULT_LIMITS = FetchLimits()


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
    redirects: tuple[str, ...] = ()
    final_url: str | None = None
    http_status: int | None = None
    transient: bool = False
    address: str | None = None


class HostNotFoundError(Exception):
    """The name does not exist (not a temporary lookup failure)."""


class _AddressRefusedError(Exception):
    pass


class _TooLargeError(Exception):
    pass


class _DeadlineError(Exception):
    pass


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
    to an address that passed."""

    def __init__(self, resolve: Resolve, allowed: Callable[[IPAddress, int], bool]) -> None:
        self._resolve = resolve
        self._allowed = allowed
        self._inner = httpcore2.SyncBackend()
        self.address: str | None = None

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[httpcore2.SOCKET_OPTION] | None = None,
    ) -> httpcore2.NetworkStream:
        addresses = self._resolve(host, port)
        if not addresses or not all(self._allowed(a, port) for a in addresses):
            raise _AddressRefusedError
        last: Exception = httpcore2.ConnectError()
        for address in addresses:
            try:
                stream = self._inner.connect_tcp(
                    str(address),
                    port,
                    timeout=timeout,
                    local_address=local_address,
                    socket_options=socket_options,
                )
            except (httpcore2.ConnectError, httpcore2.ConnectTimeout) as error:
                last = error
                continue
            self.address = str(address)
            return stream
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
    through: only the controlled test server's, never set in production (`nessa.acquisition`
    constructs this with none)."""

    def __init__(
        self,
        *,
        resolve: Resolve = system_resolve,
        limits: FetchLimits = DEFAULT_LIMITS,
        user_agent: str,
        extra_allowed: frozenset[tuple[str, int]] = frozenset(),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._resolve = resolve
        self.limits = limits
        self._user_agent = user_agent
        self._extra_allowed = extra_allowed
        self._ports = ALLOWED_PORTS | {port for _, port in extra_allowed}
        self._clock = clock
        self._ssl = ssl.create_default_context(cafile=certifi.where())
        self._robots: dict[str, tuple[float, RobotsRules]] = {}

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
        """One bounded GET, following checked redirects. `accept`: the content types taken
        (None takes any, for robots.txt)."""
        deadline = self._clock() + self.limits.total_s
        limit = max_bytes or self.limits.max_bytes
        redirects: list[str] = []
        current, previous_scheme = url, None
        backend = _GuardedBackend(self._resolve, self._address_allowed)
        with httpcore2.ConnectionPool(
            ssl_context=self._ssl,
            network_backend=backend,
            retries=0,
            max_connections=1,
            http1=True,
            http2=False,
        ) as pool:
            for _hop in range(self.limits.max_redirects + 1):
                checked = check_url(current, allowed_ports=self._ports)
                if isinstance(checked, UrlRefusal):
                    return self._blocked(url, checked.value, redirects)
                if previous_scheme == "https" and checked.scheme == "http":
                    return self._blocked(url, "redirect_downgrade", redirects)
                if (checked.ip_literal is not None) and not self._address_allowed(
                    checked.ip_literal, checked.port
                ):
                    return self._blocked(url, UrlRefusal.ADDRESS_NOT_ALLOWED.value, redirects)
                result = self._get(pool, backend, checked, accept, limit, deadline)
                if isinstance(result, _Redirect):
                    current, previous_scheme = urljoin(checked.url, result.location), checked.scheme
                    redirects.append(current)
                    continue
                if isinstance(result, FetchFailure):
                    return FetchFailure(
                        url,
                        result.outcome,
                        result.reason,
                        tuple(redirects),
                        checked.url,
                        result.http_status,
                        result.transient,
                        backend.address,
                    )
                return Fetched(
                    url,
                    checked.url,
                    tuple(redirects),
                    result.status,
                    result.content_type,
                    result.charset,
                    result.body,
                    backend.address,
                )
        return FetchFailure(
            url, AttemptStatus.FAILED, "too_many_redirects", tuple(redirects), current
        )

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
                    return (
                        _Redirect(location) if location else failed(f"http_{status}", status=status)
                    )
                if status >= 400:
                    return failed(
                        f"http_{status}", status=status, transient=status in TRANSIENT_STATUSES
                    )
                if not 200 <= status < 300 or status == 204:
                    return failed(f"http_{status}", status=status)
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
                    if self._clock() > deadline:
                        raise _DeadlineError
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
        except (
            _DeadlineError,
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

    def robots_refusal(self, checked: CheckedUrl) -> FetchFailure | None:
        """None when robots.txt allows the page; otherwise why not (RFC 9309 section 2.3.1:
        a 4xx robots.txt allows everything; one that cannot be reached disallows, as a
        transient failure that is not remembered, so the next try reads it again)."""
        netloc = (
            checked.host
            if checked.ip_literal is None or checked.ip_literal.version == 4
            else f"[{checked.host}]"
        )
        if checked.port != DEFAULT_PORTS[checked.scheme]:
            netloc = f"{netloc}:{checked.port}"
        origin = f"{checked.scheme}://{netloc}"
        cached = self._robots.get(origin)
        if cached is None or self._clock() - cached[0] > ROBOTS_CACHE_S:
            result = self.fetch(f"{origin}/robots.txt", accept=None, max_bytes=ROBOTS_MAX_BYTES)
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

    def fetch_page(self, url: str) -> Fetched | FetchFailure:
        """A page: its URL checked, then robots.txt, then the page itself (HTML only)."""
        checked = check_url(url, allowed_ports=self._ports)
        if isinstance(checked, UrlRefusal):
            return self._blocked(url, checked.value, [])
        if checked.ip_literal is not None and not self._address_allowed(
            checked.ip_literal, checked.port
        ):
            return self._blocked(url, UrlRefusal.ADDRESS_NOT_ALLOWED.value, [])
        refusal = self.robots_refusal(checked)
        if refusal is not None:
            return replace(refusal, requested_url=url)
        return self.fetch(checked.url, accept=HTML_TYPES)
