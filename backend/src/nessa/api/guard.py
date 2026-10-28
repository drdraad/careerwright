"""Loopback request guard (Global Constraint 9): Host and Origin allowlists, correlation IDs
and the access log. Pure ASGI, so streamed responses pass through untouched.

- The Host header must be one of the configured local `host:port` values, which defeats DNS
  rebinding: a hostile page cannot address the API under another name.
- A request that carries an Origin must come from the Nessa web origin, and a state-changing
  request must carry one. Another local origin, such as a different app on 127.0.0.1, cannot
  trigger authenticated changes even if it obtained a token.
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from nessa.api.envelope import envelope
from nessa.errors import ErrorCode, ErrorStage, NessaError

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_log = logging.getLogger("nessa.api.access")


def rejection(
    scope: Scope, allowed_hosts: frozenset[str], allowed_origins: frozenset[str]
) -> NessaError | None:
    headers = {key.lower(): value for key, value in scope.get("headers", [])}
    host = headers.get(b"host", b"").decode("latin-1").strip().lower()
    if host not in allowed_hosts:
        return NessaError(
            ErrorCode.HOST_NOT_ALLOWED,
            "This API answers only on its local address.",
            stage=ErrorStage.REQUEST,
        )
    origin = headers.get(b"origin")
    if origin is not None and origin.decode("latin-1") not in allowed_origins:
        return NessaError(
            ErrorCode.ORIGIN_NOT_ALLOWED,
            "Requests from this origin are not accepted.",
            stage=ErrorStage.REQUEST,
        )
    if origin is None and scope["method"] not in SAFE_METHODS:
        return NessaError(
            ErrorCode.ORIGIN_NOT_ALLOWED,
            "State-changing requests must come from the Nessa web origin.",
            stage=ErrorStage.REQUEST,
        )
    return None


class RequestGuard:
    def __init__(
        self, app: ASGIApp, *, allowed_hosts: frozenset[str], allowed_origins: frozenset[str]
    ) -> None:
        self._app = app
        self._hosts = allowed_hosts
        self._origins = allowed_origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
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

        refused = rejection(scope, self._hosts, self._origins)
        try:
            if refused is not None:
                await envelope(refused, correlation)(scope, receive, send_with_id)
            else:
                await self._app(scope, receive, send_with_id)
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
