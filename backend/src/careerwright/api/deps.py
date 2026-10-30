"""Composition-root dependencies and per-request identity for the API."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from ipaddress import IPv4Network, IPv6Network
from typing import Annotated, Protocol

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr

from careerwright.capability.commands import CapabilityData, committed_data
from careerwright.catalogue.ai_resilience import AssessmentPacks, committed_packs
from careerwright.catalogue.pay import MappingReviewPack, committed_reviews
from careerwright.config import ApiSettings
from careerwright.db import Engine, system_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import store
from careerwright.identity.access import Actor, VerifiedIdentity, not_invited, unauthenticated
from careerwright.identity.keyring import Keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.spend import SpendLimits
from careerwright.localnet import LOOPBACK


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
    # Clients the API serves: loopback, plus the container's internal subnet when its
    # configuration enables it (`careerwright.localnet.client_networks` at the composition root).
    client_networks: tuple[IPv4Network | IPv6Network, ...] = LOOPBACK
    # The committed, dated assessment and mapping-review packs, loaded and checked when the
    # API starts, before any session: a pack's corrections invalidate the records they
    # affect then (AIR1-07, ADR 0010).
    assessment_packs: AssessmentPacks = field(default_factory=committed_packs)
    mapping_reviews: MappingReviewPack = field(default_factory=committed_reviews)
    # The option pack and the capability reference, checked against their pins and each
    # other when the API starts (ADR 0011, ADR 0012).
    capability: CapabilityData = field(default_factory=committed_data)

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
        raise CareerwrightError(
            ErrorCode.IDEMPOTENCY_KEY_REQUIRED,
            "State-changing requests need an Idempotency-Key header holding a UUID.",
            stage=ErrorStage.REQUEST,
        ) from None


Deps = Annotated[ApiDependencies, Depends(dependencies)]
CallerDep = Annotated[Caller, Depends(caller)]
IdempotencyKey = Annotated[uuid.UUID, Depends(idempotency_key)]
