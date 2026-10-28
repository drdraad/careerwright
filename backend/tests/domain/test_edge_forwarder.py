"""The loopback edge relays bytes both ways and parses only fixed internal routes (BND1-13)."""

import asyncio

import pytest

from nessa.edge import Route, parse_routes, serve


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
        servers = await serve([Route(0, "127.0.0.1", upstream_port)], host="127.0.0.1")
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
        servers = await serve([Route(0, "127.0.0.1", 1)], host="127.0.0.1")
        edge_port = servers[0].sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", edge_port)
        data = await asyncio.wait_for(reader.read(), timeout=10)
        writer.close()
        for server in servers:
            server.close()
        return data

    assert asyncio.run(scenario()) == b""
