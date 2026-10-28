"""A controlled HTTP server for acquisition tests (plan section 7: "deterministic failure
servers"; ACQ-01, ACQ-02). It runs on loopback in a thread, answers each path from a table
of scripted responses and records every request it receives (path, Host and User-Agent), so
a test can prove what was and was not requested.

Every page it serves is synthetic and labelled so (`SYNTHETIC_MARKER`); none is evidence.
"""

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SYNTHETIC_MARKER = "<!-- synthetic test page: not a real source -->"


@dataclass(frozen=True)
class Scripted:
    status: int = 200
    headers: tuple[tuple[str, str], ...] = (("Content-Type", "text/html; charset=utf-8"),)
    body: bytes | Callable[[], Iterator[bytes]] = b""  # a callable streams chunk by chunk
    delay_s: float = 0.0  # before the status line


@dataclass(frozen=True)
class Seen:
    path: str
    host: str | None
    user_agent: str | None


@dataclass
class SourceServer:
    port: int
    routes: dict[str, Scripted] = field(default_factory=dict)
    seen: list[Seen] = field(default_factory=list)

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def paths(self) -> list[str]:
        return [s.path for s in self.seen]


def html(text: str) -> bytes:
    return (
        f"<!doctype html><html><head>{SYNTHETIC_MARKER}</head><body>{text}</body></html>".encode()
    )


@contextmanager
def source_server(routes: dict[str, Scripted] | None = None) -> Iterator[SourceServer]:
    state: SourceServer

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:  # quiet
            return

        def do_GET(self) -> None:
            state.seen.append(
                Seen(self.path, self.headers.get("Host"), self.headers.get("User-Agent"))
            )
            script = state.routes.get(self.path, Scripted(404, body=b"not found"))
            if script.delay_s:
                time.sleep(script.delay_s)
            self.send_response(script.status)
            for name, value in script.headers:
                self.send_header(name, value)
            if callable(script.body):
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                try:
                    for chunk in script.body():
                        self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                        self.wfile.flush()
                    self.wfile.write(b"0\r\n\r\n")
                except (BrokenPipeError, ConnectionResetError):
                    return  # the client stopped reading, as a bounded client should
                return
            if not any(name.lower() == "content-length" for name, _ in script.headers):
                self.send_header("Content-Length", str(len(script.body)))
            self.end_headers()
            try:
                self.wfile.write(script.body)
            except (BrokenPipeError, ConnectionResetError):
                return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    state = SourceServer(port=server.server_address[1], routes=dict(routes or {}))
    thread = threading.Thread(target=server.serve_forever, args=(0.02,), daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
