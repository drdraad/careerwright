"""Idempotent consequential commands (Global Constraint 7, plan section 3).

A command runs with its idempotency key in one transaction that also records a receipt of
the response. Retrying with the same key and the same request returns the recorded response
instead of acting twice. The same key with a different request is refused. Only successes
are recorded; a failed command can be retried with the same key. A success that changed
nothing can opt out (`CommandResult.record`), so it leaves no trace of the request.
"""

import hashlib
import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from nessa.db import Engine, Tx, actor_transaction
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.identity import store
from nessa.identity.records import Receipt
from nessa.identity.store import DuplicateReceiptError


@dataclass(frozen=True)
class CommandResult:
    status_code: int
    response: dict[str, object]
    workspace_id: uuid.UUID  # the receipt is deleted with this workspace
    # False for a response that changed nothing and must leave no trace of the request (the
    # support response keeps not even a fingerprint of the message); a retry recomputes it.
    record: bool = True


Execute = Callable[[Tx], CommandResult]


def fingerprint(command: str, request: Mapping[str, object]) -> str:
    """SHA-256 of the canonical request. Callers replace secret fields before hashing."""
    canonical = json.dumps(
        {"command": command, "request": dict(request)}, sort_keys=True, default=str
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _replay(receipt: Receipt, command: str, request_sha256: str) -> tuple[int, dict[str, object]]:
    if (receipt.command, receipt.request_sha256) != (command, request_sha256):
        raise NessaError(
            ErrorCode.IDEMPOTENCY_KEY_REUSED,
            "This idempotency key was already used for a different request.",
            stage=ErrorStage.REQUEST,
        )
    return receipt.status_code, receipt.response


def run_idempotent(
    engine: Engine,
    actor_id: uuid.UUID,
    key: uuid.UUID,
    command: str,
    request_sha256: str,
    execute: Execute,
) -> tuple[int, dict[str, object]]:
    try:
        with actor_transaction(engine, actor_id) as tx:
            receipt = store.read_receipt(tx, actor_id, key)
            if receipt is not None:
                return _replay(receipt, command, request_sha256)
            result = execute(tx)
            if not result.record:
                return result.status_code, result.response
            store.write_receipt(
                tx,
                actor_id,
                key,
                Receipt(
                    command,
                    request_sha256,
                    result.status_code,
                    result.response,
                    result.workspace_id,
                ),
            )
            return result.status_code, result.response
    except (DuplicateReceiptError, NessaError):
        # A concurrent duplicate may have committed first (it then made this attempt stale
        # or took the receipt); if so, the command already happened: return its result.
        with actor_transaction(engine, actor_id) as tx:
            receipt = store.read_receipt(tx, actor_id, key)
        if receipt is None:
            raise
        return _replay(receipt, command, request_sha256)
