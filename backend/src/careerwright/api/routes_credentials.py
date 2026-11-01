"""Key storage, spend limits and the estimate before a run starts. A key goes in once and
never comes back out."""

import uuid
from collections.abc import Callable, Mapping

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from careerwright.api.deps import CallerDep, Deps, IdempotencyKey
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.api.schemas import CredentialList, CredentialOut, RunEstimateOut, SpendOut
from careerwright.capability import strength
from careerwright.db import Tx, actor_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import search
from careerwright.identity import connection_check, credential_store
from careerwright.identity.credentials import (
    StoreKey,
    revoke_credential,
    rotate_credential,
    store_credential,
)
from careerwright.identity.receipts import CommandResult, fingerprint, run_idempotent
from careerwright.identity.records import RunKind
from careerwright.identity.spend_limits import (
    SetSpendLimits,
    run_estimate,
    set_spend_limits,
    spend_summary,
)
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import discovery, interview, slate_explanation

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["credentials"]
)

# The runs a person starts, by one attempt's worst case: the functions their run tasks
# reserve with (`careerwright.worker.TASKS`; a fast test keeps the two the same). A new kind a
# person starts (role or option research) adds its own here. A page extraction is started by
# an acquisition, which states its own maximum (`acquisition_model_spend`).
ESTIMATED_KINDS: Mapping[RunKind, Callable[[str], int]] = {
    RunKind.CONNECTION_CHECK: connection_check.worst_case_nano_usd,
    RunKind.INTERVIEW_TURN: interview.worst_case_nano_usd,
    RunKind.DISCOVERY: discovery.worst_case_nano_usd,
    RunKind.SLATE_EXPLANATION: slate_explanation.worst_case_nano_usd,
    RunKind.SOURCE_SEARCH: search.worst_case_nano_usd,
    RunKind.STRENGTH_PROPOSAL: strength.worst_case_nano_usd,
}


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


@router.get(
    "/spend/estimate",
    response_model=RunEstimateOut,
    tags=["spend"],
    operation_id="estimate_run",
)
def estimate_run(
    workspace_id: uuid.UUID, kind: RunKind, caller: CallerDep, deps: Deps
) -> RunEstimateOut:
    """What one run of `kind` may spend on this workspace's key, before the person starts it.
    A kind no person starts has no estimate (`422`, reason `no_estimate_for_kind`)."""
    attempt_worst_case = ESTIMATED_KINDS.get(kind)
    if attempt_worst_case is None:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "This kind of run has no estimate.",
            stage=ErrorStage.SPEND,
            details={"field": "kind", "reason": "no_estimate_for_kind"},
        )
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        return RunEstimateOut.of(
            run_estimate(
                tx,
                workspace_id,
                kind,
                attempt_worst_case,
                models=deps.models,
                now=deps.clock(),
                defaults=deps.spend_defaults,
            )
        )


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
