"""Which addresses count as this machine or its internal Compose network (A-M1, A-M11)."""

from ipaddress import ip_network

import pytest

from nessa.localnet import LOOPBACK, internal_networks, is_permitted

# /proc/net/route of a container on an internal network (eth0, no gateway) and a normal
# bridge (eth1, which carries the default route). Addresses are little-endian hex.
EDGE_CONTAINER = """\
Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
eth1	00000000	0100A8C0	0003	0	0	0	00000000	0	0	0
eth0	000013AC	00000000	0001	0	0	0	0000FFFF	0	0	0
eth1	0000A8C0	00000000	0001	0	0	0	00F0FFFF	0	0	0
"""
INTERNAL_ONLY_CONTAINER = """\
Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
eth0	000013AC	00000000	0001	0	0	0	0000FFFF	0	0	0
"""
LAPTOP_ON_A_LAN = """\
Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
wlan0	00000000	0101A8C0	0003	0	0	600	00000000	0	0	0
wlan0	0001A8C0	00000000	0001	0	0	600	00FFFFFF	0	0	0
"""


def test_the_internal_network_is_the_connected_subnet_without_a_default_route() -> None:
    assert internal_networks(EDGE_CONTAINER) == [ip_network("172.19.0.0/16")]
    assert internal_networks(INTERNAL_ONLY_CONTAINER) == [ip_network("172.19.0.0/16")]


def test_a_lan_that_carries_the_default_route_is_never_internal() -> None:
    assert internal_networks(LAPTOP_ON_A_LAN) == []


@pytest.mark.parametrize(
    ("address", "permitted"),
    [
        ("127.0.0.1", True),
        ("::1", True),
        ("172.19.0.5", True),
        ("192.168.1.20", False),  # a LAN client
        ("8.8.8.8", False),
        ("testclient", False),  # not an address at all
        ("", False),
    ],
)
def test_only_loopback_and_internal_addresses_are_permitted(address: str, permitted: bool) -> None:
    networks = (*LOOPBACK, *internal_networks(EDGE_CONTAINER))

    assert is_permitted(address, networks) is permitted
