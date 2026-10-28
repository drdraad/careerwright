"""Opaque cursors for keyset pagination. A malformed cursor is a typed validation error."""

import base64
import binascii
import json
import uuid
from datetime import datetime

from nessa.errors import ErrorCode, ErrorStage, NessaError

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def _bad_cursor() -> NessaError:
    return NessaError(
        ErrorCode.VALIDATION_FAILED,
        "The cursor is not one this API issued.",
        stage=ErrorStage.REQUEST,
        details={"field": "cursor"},
    )


def encode(value: object) -> str:
    return base64.urlsafe_b64encode(json.dumps(value, default=str).encode()).decode().rstrip("=")


def _decode(cursor: str) -> object:
    try:
        return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise _bad_cursor() from None


def decode_timestamped(cursor: str | None) -> tuple[datetime, uuid.UUID] | None:
    if cursor is None:
        return None
    value = _decode(cursor)
    if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, str) for v in value)):
        raise _bad_cursor()
    try:
        return datetime.fromisoformat(value[0]), uuid.UUID(value[1])
    except ValueError:
        raise _bad_cursor() from None


def decode_int(cursor: str | None) -> int | None:
    if cursor is None:
        return None
    value = _decode(cursor)
    if not isinstance(value, int) or isinstance(value, bool):
        raise _bad_cursor()
    return value
