"""Loopback edge: publish fixed internal services on the host without giving them egress.

Docker does not publish ports of a container attached only to an `internal` network, and on
Docker Desktop no other network setting blocks egress. So every Nessa service sits on an
internal network with no route out, and this small TCP relay, the only service also on a
normal bridge, accepts the host-published ports and forwards each to one fixed target
(`compose.yaml` publishes its ports on 127.0.0.1 only). It never opens any other
connection. Standard library only.

Run: `python -m nessa.edge` with `NESSA_EDGE_ROUTES="8000=api:8000,9099=auth:9099"`, or
`python -m nessa.edge --check` as the health check.
"""

import asyncio
import os
import re
import signal
import socket
import sys
from dataclasses import dataclass

CONNECT_TIMEOUT_S = 5.0
CHUNK_BYTES = 65_536
_ROUTE = re.compile(r"^(?P<listen>[0-9]{1,5})=(?P<host>[a-z0-9.-]+):(?P<port>[0-9]{1,5})$")


@dataclass(frozen=True)
class Route:
    listen_port: int
    target_host: str
    target_port: int


def parse_routes(value: str) -> list[Route]:
    routes = []
    for part in (p.strip() for p in value.split(",")):
        match = _ROUTE.match(part)
        ports = (int(match.group("listen")), int(match.group("port"))) if match else (-1, -1)
        if match is None or not all(0 <= port < 65536 for port in ports):
            raise ValueError(f"malformed edge route {part!r}; expected listen=host:port")
        routes.append(Route(ports[0], match.group("host"), ports[1]))
    return routes


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(CHUNK_BYTES):
            writer.write(data)
            await writer.drain()
        if writer.can_write_eof():
            writer.write_eof()
    except (ConnectionError, OSError):
        writer.close()


async def _relay(
    route: Route, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
) -> None:
    try:
        upstream_reader, upstream_writer = await asyncio.wait_for(
            asyncio.open_connection(route.target_host, route.target_port), CONNECT_TIMEOUT_S
        )
    except (OSError, TimeoutError):
        client_writer.close()
        return
    await asyncio.gather(
        _pipe(client_reader, upstream_writer), _pipe(upstream_reader, client_writer)
    )
    for writer in (upstream_writer, client_writer):
        writer.close()


async def serve(routes: list[Route], *, host: str = "0.0.0.0") -> list[asyncio.Server]:  # noqa: S104 - inside the container; published on 127.0.0.1 only
    servers = []
    for route in routes:

        async def handle(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter, route: Route = route
        ) -> None:
            await _relay(route, reader, writer)

        servers.append(await asyncio.start_server(handle, host, route.listen_port))
    return servers


async def _run(routes: list[Route]) -> None:
    servers = await serve(routes)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    print(f"edge relaying {len(routes)} routes", flush=True)
    await stop.wait()
    for server in servers:
        server.close()


def _check(routes: list[Route]) -> int:
    for route in routes:
        try:
            socket.create_connection(("127.0.0.1", route.listen_port), timeout=2).close()
        except OSError:
            return 1
    return 0


def main() -> None:
    routes = parse_routes(os.environ["NESSA_EDGE_ROUTES"])
    if sys.argv[1:] == ["--check"]:
        sys.exit(_check(routes))
    asyncio.run(_run(routes))


if __name__ == "__main__":
    main()
