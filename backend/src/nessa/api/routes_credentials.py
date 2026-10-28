"""Key storage and spend limits. A key goes in once and never comes back out."""

import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from nessa.api.deps import CallerDep, Deps, IdempotencyKey
from nessa.api.envelope import ERROR_RESPONSES
from nessa.api.schemas import CredentialList, CredentialOut, SpendOut
from nessa.db import Tx, actor_transaction
from nessa.identity import credential_store
from nessa.identity.credentials import (
    StoreKey,
    revoke_credential,
    rotate_credential,
    store_credential,
)
from nessa.identity.receipts import CommandResult, fingerprint, run_idempotent
from nessa.identity.spend_limits import SetSpendLimits, set_spend_limits, spend_summary
from nessa.identity.workspaces import visible_workspace

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["credentials"]
)


def _key_request(workspace_id: uuid.UUID, body: StoreKey, **extra: str) -> dict[str, object]:
    # The key itself is never hashed into a receipt: a retry is the same logical command.
    return {
        "workspace_id": str(workspace_id),
        "consent": body.consent_to_encrypted_storage,
        **extra,
    }


@router.get("/credentials", response_model=CredentialList)
def list_credentials(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> CredentialList:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        visible_workspace(tx, workspace_id)
        return CredentialList(
            items=[CredentialOut.of(c) for c in credential_store.credentials(tx, workspace_id)]
        )


@router.post(
    "/credentials",
    status_code=201,
    response_model=CredentialOut,
    operation_id="store_credential",
)
def store(
    workspace_id: uuid.UUID, body: StoreKey, caller: CallerDep, deps: Deps, key: IdempotencyKey
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        stored = store_credential(
            tx, caller.actor, workspace_id, body, deps.keyring, deps.clock(), deps.spend_defaults
        )
        return CommandResult(201, CredentialOut.of(stored).model_dump(mode="json"), workspace_id)

    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "store_credential",
        fingerprint("store_credential", _key_request(workspace_id, body)),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.post(
    "/credentials/{credential_id}/rotate",
    status_code=201,
    response_model=CredentialOut,
    operation_id="rotate_credential",
)
def rotate(
    workspace_id: uuid.UUID,
    credential_id: uuid.UUID,
    body: StoreKey,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        rotated = rotate_credential(
            tx,
            caller.actor,
            workspace_id,
            credential_id,
            body,
            deps.keyring,
            deps.clock(),
            deps.spend_defaults,
        )
        return CommandResult(201, CredentialOut.of(rotated).model_dump(mode="json"), workspace_id)

    request = _key_request(workspace_id, body, credential_id=str(credential_id))
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "rotate_credential",
        fingerprint("rotate_credential", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.post(
    "/credentials/{credential_id}/revoke",
    response_model=CredentialOut,
    operation_id="revoke_credential",
)
def revoke(
    workspace_id: uuid.UUID,
    credential_id: uuid.UUID,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        revoked = revoke_credential(tx, caller.actor, workspace_id, credential_id)
        return CommandResult(200, CredentialOut.of(revoked).model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), "credential_id": str(credential_id)}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "revoke_credential",
        fingerprint("revoke_credential", request),
        execute,
    )
    return JSONResponse(response, status_code=status)


@router.get("/spend", response_model=SpendOut, tags=["spend"])
def get_spend(workspace_id: uuid.UUID, caller: CallerDep, deps: Deps) -> SpendOut:
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return SpendOut.of(spend_summary(tx, workspace_id, deps.clock(), deps.spend_defaults))


@router.put("/spend/limits", response_model=SpendOut, tags=["spend"])
def put_spend_limits(
    workspace_id: uuid.UUID,
    body: SetSpendLimits,
    caller: CallerDep,
    deps: Deps,
    key: IdempotencyKey,
) -> JSONResponse:
    def execute(tx: Tx) -> CommandResult:
        summary = set_spend_limits(tx, workspace_id, body, deps.clock(), deps.spend_defaults)
        return CommandResult(200, SpendOut.of(summary).model_dump(mode="json"), workspace_id)

    request = {"workspace_id": str(workspace_id), **body.model_dump(mode="json")}
    status, response = run_idempotent(
        deps.engine,
        caller.actor.actor_id,
        key,
        "set_spend_limits",
        fingerprint("set_spend_limits", request),
        execute,
    )
    return JSONResponse(response, status_code=status)
