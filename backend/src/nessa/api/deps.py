"""Composition-root dependencies and per-request identity for the API."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from ipaddress import IPv4Network, IPv6Network
from typing import Annotated, Protocol

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr

from nessa.config import ApiSettings
from nessa.db import Engine, system_transaction
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity import store
from nessa.identity.access import Actor, VerifiedIdentity, not_invited, unauthenticated
from nessa.identity.keyring import Keyring
from nessa.identity.model_choice import ModelChoice
from nessa.identity.spend import SpendLimits
from nessa.localnet import LOOPBACK


class TokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedIdentity: ...


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ApiDependencies:
    settings: ApiSettings
    engine: Engine
    verifier: TokenVerifier
    keyring: Keyring
    models: ModelChoice
    clock: Callable[[], datetime] = _utc_now
    # Clients the API serves: loopback, plus the internal network inside a container
    # (`nessa.localnet.local_networks()` at the composition root).
    client_networks: tuple[IPv4Network | IPv6Network, ...] = LOOPBACK

    @property
    def spend_defaults(self) -> SpendLimits:
        return SpendLimits(
            run_limit_nano_usd=self.settings.default_run_spend_limit_nano_usd,
            period_limit_nano_usd=self.settings.default_period_spend_limit_nano_usd,
        )


@dataclass(frozen=True)
class Caller:
    actor: Actor
    identity: VerifiedIdentity
    token: SecretStr  # for long-lived responses that re-verify it; never logged or stored


def dependencies(request: Request) -> ApiDependencies:
    deps: ApiDependencies = request.app.state.deps
    return deps


_bearer = HTTPBearer(auto_error=False, description="A Firebase ID token from the Auth emulator.")


def caller(
    deps: Annotated[ApiDependencies, Depends(dependencies)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Caller:
    """Verified token, then an active invitation. Workspace ownership is checked by the
    database on every later statement (row-level security)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthenticated()
    identity = deps.verifier.verify(credentials.credentials)
    with system_transaction(deps.engine) as tx:
        actor = store.resolve_active_actor(tx, identity.firebase_uid, identity.email)
    if actor is None:
        raise not_invited()
    return Caller(actor, identity, SecretStr(credentials.credentials))


def idempotency_key(
    key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="A UUID chosen by the client per intended change; retries reuse it.",
        ),
    ] = None,
) -> uuid.UUID:
    try:
        return uuid.UUID(key or "")
    except ValueError:
        raise NessaError(
            ErrorCode.IDEMPOTENCY_KEY_REQUIRED,
            "State-changing requests need an Idempotency-Key header holding a UUID.",
            stage=ErrorStage.REQUEST,
        ) from None


Deps = Annotated[ApiDependencies, Depends(dependencies)]
CallerDep = Annotated[Caller, Depends(caller)]
IdempotencyKey = Annotated[uuid.UUID, Depends(idempotency_key)]
