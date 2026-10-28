"""What counts as "this machine or its internal Compose network" (Global Constraint 9).

A container on Nessa's `internal` network has a directly connected subnet there and no
default route through it (Docker gives internal networks no gateway). So the internal
subnets are the connected routes on interfaces that carry no default route, read from the
kernel's IPv4 route table. On a host, the LAN interface carries the default route, so a
LAN is never treated as internal. Standard library only (the edge uses it too).
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


def local_networks(route_table: Path = ROUTE_TABLE) -> tuple[IPv4Network | IPv6Network, ...]:
    """Loopback plus the internal subnets of this process's network namespace."""
    try:
        table = route_table.read_text(encoding="ascii")
    except OSError:
        return LOOPBACK  # not Linux, or no route table: loopback only
    return (*LOOPBACK, *internal_networks(table))


def is_permitted(address: str, networks: Networks) -> bool:
    try:
        parsed = ip_address(address)
    except ValueError:
        return False
    return any(parsed in network for network in networks)
