"""Which addresses count as this machine or its internal Compose network (A-M1, A-M11)."""

from ipaddress import ip_network
from pathlib import Path

import pytest

from careerwright.localnet import LOOPBACK, client_networks, internal_networks, is_permitted

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


# A Linux host running Docker: docker0 (172.17/16) is connected and has no default route.
LINUX_HOST_WITH_DOCKER = """\
Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
eth0	00000000	0101A8C0	0003	0	0	100	00000000	0	0	0
eth0	0001A8C0	00000000	0001	0	0	100	00FFFFFF	0	0	0
docker0	000011AC	00000000	0001	0	0	0	0000FFFF	0	0	0
"""


@pytest.mark.req("BND1-13")
def test_the_api_serves_loopback_only_unless_its_container_says_otherwise(
    tmp_path: Path,
) -> None:
    """N4: on a Linux host, docker0, libvirt or a VPN look internal by route alone, so
    internal subnets count only when the container's configuration enables them."""
    host = tmp_path / "host-route"
    host.write_text(LINUX_HOST_WITH_DOCKER, encoding="ascii")
    container = tmp_path / "container-route"
    container.write_text(INTERNAL_ONLY_CONTAINER, encoding="ascii")

    assert client_networks(internal=False, route_table=host) == LOOPBACK
    assert client_networks(internal=False, route_table=container) == LOOPBACK
    assert client_networks(internal=True, route_table=container) == (
        *LOOPBACK,
        ip_network("172.19.0.0/16"),
    )


def test_enabling_internal_clients_without_an_internal_network_fails_closed(
    tmp_path: Path,
) -> None:
    lan = tmp_path / "route"
    lan.write_text(LAPTOP_ON_A_LAN, encoding="ascii")

    for table in (lan, tmp_path / "missing"):
        with pytest.raises(RuntimeError, match="no internal network"):
            client_networks(internal=True, route_table=table)
