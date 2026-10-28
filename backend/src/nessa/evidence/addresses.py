"""URL and address checks made before any retrieval (spec section 6, "Retrieval pipeline and
security boundary"; ACQ-01). Pure: no network.

A URL passes only with an `http` or `https` scheme, no credentials, port 80 or 443, and a
host that is either a public IP literal or a multi-label DNS name. Anything that could be an
encoded address (one decimal or hex number, octal or short dotted forms, percent-encoding,
Unicode digits) is refused rather than decoded, so no parser disagreement can turn it into
a private address. The fetcher applies `address_refusal` again to every address a name
resolves to, at connect time, and checks every redirect target with `check_url` again.
"""

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import quote, urlsplit, urlunsplit

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

MAX_URL_CHARS = 2_048
DEFAULT_PORTS = {"https": 443, "http": 80}
ALLOWED_PORTS = frozenset(DEFAULT_PORTS.values())
# Names that only ever resolve inside a machine or a local network.
LOCAL_NAMES = frozenset({"localhost"})
LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".arpa", ".lan", ".home", ".corp")
MAX_NAME_CHARS = 253
_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
_NUMERIC_LABEL = re.compile(r"^(0x[0-9a-f]*|[0-9]+)$")
_DECIMAL_OCTET = re.compile(r"^(0|[1-9][0-9]{0,2})$")
_NAT64 = ipaddress.ip_network("64:ff9b::/96")
_PATH_SAFE = "/%;:@&=+$,!~*'()-._"
_QUERY_SAFE = "/%;:@&=+$,!~*'()-._?"


class UrlRefusal(StrEnum):
    """Why a URL is not fetched. Each is a policy refusal, recorded as a blocked attempt."""

    MALFORMED = "malformed_url"
    URL_TOO_LONG = "url_too_long"
    SCHEME_NOT_ALLOWED = "scheme_not_allowed"
    CREDENTIALS_IN_URL = "credentials_in_url"
    PORT_NOT_ALLOWED = "port_not_allowed"
    HOST_NOT_ALLOWED = "host_not_allowed"
    ADDRESS_NOT_ALLOWED = "address_not_allowed"


@dataclass(frozen=True)
class CheckedUrl:
    """A URL that passed the checks, in the normalised form that is requested and recorded
    (lower-case scheme and host, the host in its ASCII form, no fragment)."""

    url: str
    scheme: str
    host: str
    port: int
    ip_literal: IPAddress | None


def address_refusal(address: IPAddress) -> UrlRefusal | None:
    """None for a public unicast address; otherwise the refusal. Every IPv6 form that embeds
    an IPv4 address (mapped, 6to4, Teredo, NAT64) is refused outright: none is needed to
    reach a public page, and each is a known way round an IPv4-only check."""
    if isinstance(address, ipaddress.IPv6Address) and (
        address.ipv4_mapped is not None
        or address.sixtofour is not None
        or address.teredo is not None
        or address in _NAT64
    ):
        return UrlRefusal.ADDRESS_NOT_ALLOWED
    if not address.is_global or address.is_multicast or address.is_reserved:
        return UrlRefusal.ADDRESS_NOT_ALLOWED
    return None


def _ip_literal(host: str) -> IPAddress | UrlRefusal:
    try:
        return ipaddress.IPv6Address(host)
    except ValueError:
        return UrlRefusal.HOST_NOT_ALLOWED  # a zone ID or any other non-address in brackets


def _name(host: str) -> str | IPAddress | UrlRefusal:
    """The host's ASCII name, or a canonical dotted-quad address, or the refusal."""
    if "%" in host:
        return UrlRefusal.HOST_NOT_ALLOWED
    host = host.removesuffix(".")
    try:
        ascii_host = host.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return UrlRefusal.HOST_NOT_ALLOWED
    labels = ascii_host.split(".")
    if all(_NUMERIC_LABEL.match(label) for label in labels):
        canonical = len(labels) == 4 and all(
            _DECIMAL_OCTET.match(label) and int(label) <= 255 for label in labels
        )
        return ipaddress.IPv4Address(ascii_host) if canonical else UrlRefusal.HOST_NOT_ALLOWED
    if (
        len(labels) < 2
        or len(ascii_host) > MAX_NAME_CHARS
        or _NUMERIC_LABEL.match(labels[-1])
        or not all(_LABEL.match(label) for label in labels)
        or ascii_host in LOCAL_NAMES
        or ascii_host.endswith(LOCAL_SUFFIXES)
    ):
        return UrlRefusal.HOST_NOT_ALLOWED
    return ascii_host


def check_url(
    raw: str, *, allowed_ports: frozenset[int] = ALLOWED_PORTS
) -> CheckedUrl | UrlRefusal:
    """`allowed_ports` is 80 and 443; only the controlled test server's port is ever added."""
    if len(raw) > MAX_URL_CHARS:
        return UrlRefusal.URL_TOO_LONG
    if any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F or ch == "\\" for ch in raw):
        return UrlRefusal.MALFORMED
    try:
        parts = urlsplit(raw)
        port = parts.port
    except ValueError:
        return UrlRefusal.PORT_NOT_ALLOWED if "]" not in raw else UrlRefusal.MALFORMED
    scheme = parts.scheme.lower()
    if scheme not in DEFAULT_PORTS:
        return UrlRefusal.SCHEME_NOT_ALLOWED
    if "@" in parts.netloc:
        return UrlRefusal.CREDENTIALS_IN_URL
    port = DEFAULT_PORTS[scheme] if port is None else port
    if port not in allowed_ports:
        return UrlRefusal.PORT_NOT_ALLOWED
    authority = parts.netloc.rsplit(":", 1)[0] if not parts.netloc.endswith("]") else parts.netloc
    bracketed = authority.startswith("[")
    if not parts.hostname:
        return UrlRefusal.HOST_NOT_ALLOWED
    found = _ip_literal(parts.hostname) if bracketed else _name(parts.hostname)
    if isinstance(found, UrlRefusal):
        return found
    ip = found if not isinstance(found, str) else None
    if ip is not None and address_refusal(ip) is not None:
        return UrlRefusal.ADDRESS_NOT_ALLOWED
    host = str(found)
    netloc = f"[{host}]" if isinstance(ip, ipaddress.IPv6Address) else host
    if port != DEFAULT_PORTS[scheme]:
        netloc = f"{netloc}:{port}"
    url = urlunsplit(
        (
            scheme,
            netloc,
            quote(parts.path or "/", safe=_PATH_SAFE),
            quote(parts.query, safe=_QUERY_SAFE),
            "",
        )
    )
    return CheckedUrl(url=url, scheme=scheme, host=host, port=port, ip_literal=ip)
