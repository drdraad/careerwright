"""What counts as "this machine or its internal Compose network" (Global Constraint 9).

A container on Careerwright's `internal` network has a directly connected subnet there and no
default route through it (Docker gives internal networks no gateway). So the internal
subnets are the connected routes on interfaces that carry no default route, read from the
kernel's IPv4 route table. That reading holds only inside a Careerwright container: on a host,
docker0, a VPN or a second NIC also has no default route. So the edge (always a container)
uses it for its targets, and the API uses it for clients only when its container's
configuration says so (`client_networks`); otherwise the API is loopback-only. Standard
library only.
"""

import socket
import struct
from collections.abc import Iterable
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network
from pathlib import Path

ROUTE_TABLE = Path("/proc/net/route")
LOOPBACK: tuple[IPv4Network | IPv6Network, ...] = (ip_network("127.0.0.0/8"), ip_network("::1/128"))

Networks = Iterable[IPv4Network | IPv6Network]


def _ipv4(little_endian_hex: str) -> str:
    return socket.inet_ntoa(struct.pack("<I", int(little_endian_hex, 16)))


def internal_networks(route_table: str) -> list[IPv4Network]:
    rows = [line.split() for line in route_table.splitlines()[1:] if line.strip()]
    routed = {row[0] for row in rows if row[1] == "00000000"}  # interfaces with a default route
    return [
        ip_network(f"{_ipv4(row[1])}/{_ipv4(row[7])}")  # type: ignore[misc]
        for row in rows
        if row[1] != "00000000" and row[2] == "00000000" and row[0] not in routed
    ]


def client_networks(
    *, internal: bool, route_table: Path = ROUTE_TABLE
) -> tuple[IPv4Network | IPv6Network, ...]:
    """The clients the API serves: loopback, plus this namespace's internal subnets only
    when `internal` is set by the container's configuration. On a host, a subnet without a
    default route (docker0, a VPN, a second NIC) is not internal to Careerwright, so a host is
    loopback-only. Enabled without any internal network found, it fails closed."""
    if not internal:
        return LOOPBACK
    try:
        found = internal_networks(route_table.read_text(encoding="ascii"))
    except OSError:
        found = []
    if not found:
        raise RuntimeError("internal network clients are enabled but no internal network found")
    return (*LOOPBACK, *found)


def is_permitted(address: str, networks: Networks) -> bool:
    try:
        parsed = ip_address(address)
    except ValueError:
        return False
    return any(parsed in network for network in networks)
