"""Who is asking: a verified Firebase identity mapped to an invited actor.

Sign-in alone is not authorisation (spec section 17): the identity must match an active
invitation, and every workspace access is then checked again by row-level security.
"""

import uuid
from dataclasses import dataclass

from nessa.errors import ErrorCode, ErrorStage, NessaError


@dataclass(frozen=True)
class VerifiedIdentity:
    """Claims from a verified, unrevoked ID token. The token itself is never kept."""

    firebase_uid: str
    email: str
    expires_at: int  # Unix seconds


@dataclass(frozen=True)
class Actor:
    actor_id: uuid.UUID
    email: str
    display_name: str


def unauthenticated() -> NessaError:
    return NessaError(
        ErrorCode.UNAUTHENTICATED,
        "Sign in again: the request has no valid, unrevoked ID token.",
        stage=ErrorStage.IDENTITY,
    )


def not_invited() -> NessaError:
    return NessaError(
        ErrorCode.NOT_INVITED,
        "This account is not invited to Nessa, or its invitation was revoked.",
        stage=ErrorStage.IDENTITY,
    )


def workspace_not_found() -> NessaError:
    # Another actor's workspace looks exactly like a missing one: existence is not disclosed.
    return NessaError(
        ErrorCode.NOT_FOUND, "No such workspace for this account.", stage=ErrorStage.WORKSPACE
    )
