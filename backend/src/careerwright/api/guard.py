"""Loopback request guard (Global Constraint 9): client address, Host and Origin allowlists,
correlation IDs, the access log and the last-resort error envelope. Pure ASGI, so streamed
responses pass through untouched.

- The client must be on loopback or the API's own internal network (`careerwright.localnet`). The
  emulator's tokens are unsigned, so this keeps them out of reach of the LAN even if the API
  were ever started on a public interface, whatever Host header a client forges.
- The Host header must be one of the configured local `host:port` values, which defeats DNS
  rebinding: a hostile page cannot address the API under another name.
- A request that carries an Origin must come from the Careerwright web origin, and a state-changing
  request must carry one. Another local origin, such as a different app on 127.0.0.1, cannot
  trigger authenticated changes even if it obtained a token.
- WebSocket scopes are refused: the API has none, so none may slip past these checks.
- An unexpected exception becomes the `INTERNAL_ERROR` envelope here, inside Starlette's
  server-error middleware, so a 500 still carries its correlation ID and is logged as 500.
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from ipaddress import IPv4Network, IPv6Network
from typing import Any

from careerwright.api.envelope import envelope, internal_error
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.localnet import is_permitted

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
POLICY_VIOLATION = 1008  # WebSocket close code
_log = logging.getLogger("careerwright.api.access")
_errors = logging.getLogger("careerwright.api")


def rejection(
    scope: Scope,
    allowed_hosts: frozenset[str],
    allowed_origins: frozenset[str],
    client_networks: tuple[IPv4Network | IPv6Network, ...],
) -> CareerwrightError | None:
    client = scope.get("client")
    if client is None or not is_permitted(str(client[0]), client_networks):
        return CareerwrightError(
            ErrorCode.CLIENT_NOT_ALLOWED,
            "This API serves only this machine.",
            stage=ErrorStage.REQUEST,
        )
    headers = {key.lower(): value for key, value in scope.get("headers", [])}
    host = headers.get(b"host", b"").decode("latin-1").strip().lower()
    if host not in allowed_hosts:
        return CareerwrightError(
            ErrorCode.HOST_NOT_ALLOWED,
            "This API answers only on its local address.",
            stage=ErrorStage.REQUEST,
        )
    origin = headers.get(b"origin")
    if origin is not None and origin.decode("latin-1") not in allowed_origins:
        return CareerwrightError(
            ErrorCode.ORIGIN_NOT_ALLOWED,
            "Requests from this origin are not accepted.",
            stage=ErrorStage.REQUEST,
        )
    if origin is None and scope["method"] not in SAFE_METHODS:
        return CareerwrightError(
            ErrorCode.ORIGIN_NOT_ALLOWED,
            "State-changing requests must come from the Careerwright web origin.",
            stage=ErrorStage.REQUEST,
        )
    return None


class RequestGuard:
    def __init__(
        self,
        app: ASGIApp,
        *,
        allowed_hosts: frozenset[str],
        allowed_origins: frozenset[str],
        client_networks: tuple[IPv4Network | IPv6Network, ...],
    ) -> None:
        self._app = app
        self._hosts = allowed_hosts
        self._origins = allowed_origins
        self._clients = client_networks

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self._app(scope, receive, send)
            return
        if scope["type"] != "http":
            if scope["type"] == "websocket":
                await receive()  # websocket.connect
                await send({"type": "websocket.close", "code": POLICY_VIOLATION})
            return
        correlation = uuid.uuid4().hex
        scope.setdefault("state", {})["correlation_id"] = correlation
        started = time.monotonic()
        status: list[int] = []

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                status.append(message["status"])
                message.setdefault("headers", []).append(
                    (b"x-correlation-id", correlation.encode())
                )
            await send(message)

        refused = rejection(scope, self._hosts, self._origins, self._clients)
        try:
            if refused is not None:
                await envelope(refused, correlation)(scope, receive, send_with_id)
            else:
                await self._app(scope, receive, send_with_id)
        except Exception as error:
            _errors.error(
                "unexpected error",
                exc_info=error,
                extra={"correlation_id": correlation, "path": scope["path"]},
            )
            if status:
                raise  # the response has started; the server closes the connection
            await envelope(internal_error(), correlation)(scope, receive, send_with_id)
        finally:
            # Path only: no query string, headers or body ever reach the access log.
            _log.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status[0] if status else 0,
                    "duration_ms": round((time.monotonic() - started) * 1000),
                    "correlation_id": correlation,
                },
            )
