"""Typed, stable error codes (spec section 18) shared by domain code and the API envelope.

A `NessaError` carries a code, the affected stage, whether retrying can help and a
human-readable message written by our code. It never carries provider text, request input
or exception messages, so it is safe to return and to log.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    # Specification section 18 (required codes).
    SOURCE_BLOCKED = "SOURCE_BLOCKED"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    SOLVE_LIMIT_REACHED = "SOLVE_LIMIT_REACHED"
    STALE_INPUT_VERSION = "STALE_INPUT_VERSION"
    FEATURE_NOT_IN_M0 = "FEATURE_NOT_IN_M0"
    MODEL_SCOPE_EXCEEDED = "MODEL_SCOPE_EXCEEDED"
    COARSE_MODEL_UNRESOLVED = "COARSE_MODEL_UNRESOLVED"
    NO_ROUTE_IN_BOUNDED_MODEL = "NO_ROUTE_IN_BOUNDED_MODEL"
    # Platform codes (identity, request integrity, commands).
    UNAUTHENTICATED = "UNAUTHENTICATED"
    NOT_INVITED = "NOT_INVITED"
    NOT_FOUND = "NOT_FOUND"
    HOST_NOT_ALLOWED = "HOST_NOT_ALLOWED"
    ORIGIN_NOT_ALLOWED = "ORIGIN_NOT_ALLOWED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    IDEMPOTENCY_KEY_REQUIRED = "IDEMPOTENCY_KEY_REQUIRED"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    CREDENTIAL_EXISTS = "CREDENTIAL_EXISTS"
    CREDENTIAL_REVOKED = "CREDENTIAL_REVOKED"
    CREDENTIAL_REQUIRED = "CREDENTIAL_REQUIRED"
    MODE_NOT_SUPPORTED = "MODE_NOT_SUPPORTED"
    STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
    AUTH_UNAVAILABLE = "AUTH_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorStage(StrEnum):
    """Which part of the product the failure affects."""

    REQUEST = "request"
    IDENTITY = "identity"
    WORKSPACE = "workspace"
    PROFILE = "profile"
    CREDENTIAL = "credential"
    EXECUTION = "execution"
    SPEND = "spend"
    INTERNAL = "internal"


class NessaError(Exception):
    """A failure the caller can act on. `details` holds identifiers and limits only."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        stage: ErrorStage,
        retryable: bool = False,
        details: dict[str, str | int | list[str]] | None = None,
    ) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code
        self.message = message
        self.stage = stage
        self.retryable = retryable
        self.details = details or {}
