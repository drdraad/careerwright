"""Idempotent consequential commands (Global Constraint 7, plan section 3).

A command runs with its idempotency key in one transaction that also records a receipt of
the response. Retrying with the same key and the same request returns the recorded response
instead of acting twice. The same key with a different request is refused. Only successes
are recorded; a failed command can be retried with the same key.
"""

import hashlib
import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from careerwright.db import Engine, Tx, actor_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import store
from careerwright.identity.records import Receipt
from careerwright.identity.store import DuplicateReceiptError


@dataclass(frozen=True)
class CommandResult:
    status_code: int
    response: dict[str, object]
    workspace_id: uuid.UUID  # the receipt is deleted with this workspace


Execute = Callable[[Tx], CommandResult]


def fingerprint(command: str, request: Mapping[str, object]) -> str:
    """SHA-256 of the canonical request. Callers replace secret fields before hashing."""
    canonical = json.dumps(
        {"command": command, "request": dict(request)}, sort_keys=True, default=str
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _replay(receipt: Receipt, command: str, request_sha256: str) -> tuple[int, dict[str, object]]:
    if (receipt.command, receipt.request_sha256) != (command, request_sha256):
        raise CareerwrightError(
            ErrorCode.IDEMPOTENCY_KEY_REUSED,
            # The fingerprint covers the request's format too, so a retry sent across a change
            # to that format (fix round 4 removed `send_after_support`) lands here as well.
            "This idempotency key was already used for a different request, or for this "
            "request in an earlier request format. Send it again with a new key.",
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
    except (DuplicateReceiptError, CareerwrightError):
        # A concurrent duplicate may have committed first (it then made this attempt stale
        # or took the receipt); if so, the command already happened: return its result.
        with actor_transaction(engine, actor_id) as tx:
            receipt = store.read_receipt(tx, actor_id, key)
        if receipt is None:
            raise
        return _replay(receipt, command, request_sha256)
