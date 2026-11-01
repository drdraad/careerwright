"""A local fake HTTPS proxy for the fetcher's proxy mode (ADR 0009, 2026-11-01 amendment). It
speaks only CONNECT, as the cloud session's proxy does (anything else is a 405), records every
request line it receives, and tunnels each permitted `host:port` to a loopback port the test
names, or answers the status the test gives (a 403 policy denial). Nothing leaves loopback."""

import socket
import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from socketserver import BaseRequestHandler, ThreadingTCPServer


@dataclass
class FakeProxy:
    port: int
    routes: dict[str, int | str] = field(default_factory=dict)  # authority -> port or status
    lines: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def connects(self) -> list[str]:
        return [line.split(" ")[1] for line in self.lines if line.startswith("CONNECT ")]


def _pipe(source: socket.socket, sink: socket.socket) -> None:
    with suppress(OSError):
        while data := source.recv(65536):
            sink.sendall(data)
    with suppress(OSError):
        sink.shutdown(socket.SHUT_WR)


@contextmanager
def fake_proxy(routes: dict[str, int | str] | None = None) -> Iterator[FakeProxy]:
    state: FakeProxy

    class Handler(BaseRequestHandler):
        def handle(self) -> None:
            client: socket.socket = self.request
            head = b""
            while b"\r\n\r\n" not in head:
                chunk = client.recv(4096)
                if not chunk:
                    return
                head += chunk
            line = head.split(b"\r\n", 1)[0].decode("latin-1")
            state.lines.append(line)
            method, _, rest = line.partition(" ")
            authority = rest.partition(" ")[0]
            route = state.routes.get(authority, "403 Forbidden")
            if method != "CONNECT":
                client.sendall(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n")
                return
            if isinstance(route, str):
                client.sendall(f"HTTP/1.1 {route}\r\nContent-Length: 0\r\n\r\n".encode())
                return
            with socket.create_connection(("127.0.0.1", route)) as upstream:
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                back = threading.Thread(target=_pipe, args=(upstream, client), daemon=True)
                back.start()
                _pipe(client, upstream)
                back.join(5)

    server = ThreadingTCPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    state = FakeProxy(port=server.server_address[1], routes=dict(routes or {}))
    thread = threading.Thread(target=server.serve_forever, args=(0.02,), daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
