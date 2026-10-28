"""The loopback edge relays bytes both ways, only to fixed routes, and only to targets inside
the internal network (BND1-13, A-M1)."""

import asyncio
import time
from ipaddress import ip_network

import pytest

from nessa import edge
from nessa.edge import Route, parse_routes, serve
from nessa.localnet import LOOPBACK

ONLY_TEN = (ip_network("10.0.0.0/8"),)


def test_routes_parse_from_listen_port_to_internal_target() -> None:
    assert parse_routes("8000=api:8000, 9099=auth:9099") == [
        Route(8000, "api", 8000),
        Route(9099, "auth", 9099),
    ]


@pytest.mark.parametrize("bad", ["", "8000", "8000=api", "x=api:1", "8000=api:99999"])
def test_malformed_routes_are_refused(bad: str) -> None:
    with pytest.raises(ValueError, match="route"):
        parse_routes(bad)


async def _echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    while data := await reader.read(1024):
        writer.write(data.upper())
        await writer.drain()
    writer.close()


def test_bytes_are_relayed_both_ways_and_eof_propagates() -> None:
    async def scenario() -> tuple[bytes, bytes]:
        upstream = await asyncio.start_server(_echo, "127.0.0.1", 0)
        upstream_port = upstream.sockets[0].getsockname()[1]
        servers = await serve(
            [Route(0, "127.0.0.1", upstream_port)], host="127.0.0.1", allowed=LOOPBACK
        )
        edge_port = servers[0].sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", edge_port)
        writer.write(b"hello ")
        writer.write(b"edge")
        await writer.drain()
        first = await reader.readexactly(10)
        writer.write_eof()
        rest = await asyncio.wait_for(reader.read(), timeout=5)
        writer.close()
        for server in (*servers, upstream):
            server.close()
        return first, rest

    first, rest = asyncio.run(scenario())

    assert first == b"HELLO EDGE"
    assert rest == b""  # upstream closed after our EOF, and the edge passed that back


def test_an_unreachable_target_closes_the_client_connection() -> None:
    async def scenario() -> bytes:
        servers = await serve([Route(0, "127.0.0.1", 1)], host="127.0.0.1", allowed=LOOPBACK)
        edge_port = servers[0].sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", edge_port)
        data = await asyncio.wait_for(reader.read(), timeout=10)
        writer.close()
        for server in servers:
            server.close()
        return data

    assert asyncio.run(scenario()) == b""


def relay_attempt(target_host: str, allowed: tuple[object, ...]) -> tuple[bytes, list[bool]]:
    """Connect through the edge to a listening upstream; report what the upstream saw."""
    reached: list[bool] = []

    async def note(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        reached.append(True)
        writer.close()

    async def scenario() -> bytes:
        upstream = await asyncio.start_server(note, "127.0.0.1", 0)
        port = upstream.sockets[0].getsockname()[1]
        servers = await serve(
            [Route(0, target_host, port)],
            host="127.0.0.1",
            allowed=allowed,  # type: ignore[arg-type]
        )
        edge_port = servers[0].sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", edge_port)
        writer.write(b"Authorization: Bearer must-not-leave")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(), timeout=10)
        writer.close()
        await asyncio.sleep(0.1)
        for server in (*servers, upstream):
            server.close()
        return data

    return asyncio.run(scenario()), reached


@pytest.mark.req("BND1-11")
def test_a_target_resolving_outside_the_internal_network_is_never_contacted() -> None:
    data, reached = relay_attempt("127.0.0.1", ONLY_TEN)

    assert (data, reached) == (b"", [])


@pytest.mark.req("BND1-11")
def test_an_unresolvable_target_is_refused() -> None:
    data, reached = relay_attempt("nessa-absent-target.invalid", LOOPBACK)

    assert (data, reached) == (b"", [])


@pytest.mark.req("BND1-11")
def test_a_resolver_that_never_answers_releases_the_client_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """N7: resolution is bounded like the connect, so a slow resolver cannot hold relays.
    Numeric addresses (the test's own sockets) never reach `getaddrinfo`."""

    async def never_answers(*args: object, **kwargs: object) -> list[object]:
        await asyncio.sleep(60)
        return []

    monkeypatch.setattr(asyncio.BaseEventLoop, "getaddrinfo", never_answers)
    monkeypatch.setattr(edge, "CONNECT_TIMEOUT_S", 0.2)
    started = time.monotonic()

    data, reached = relay_attempt("api", LOOPBACK)

    assert (data, reached) == (b"", [])
    assert time.monotonic() - started < 5
