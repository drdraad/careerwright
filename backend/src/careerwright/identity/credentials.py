"""Credential commands: store (with explicit consent), rotate and revoke a workspace's Meta key.

A key is sealed the moment it arrives (AES-256-GCM, associated data = kind, workspace and
credential ID) and is never returned, logged or exported. Background work needs explicit
consent to encrypted storage (spec section 16); without a key, editing and saved work stay
usable. Revocation and rotation affect every queued run at once, because the worker resolves
the workspace's active key just before each call.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity import credential_store, store
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring, RecordContext
from careerwright.identity.records import Credential, EventKind, Workspace
from careerwright.identity.spend import SpendLimits
from careerwright.identity.workspaces import visible_workspace
from careerwright.vocabulary import DataMode

CREDENTIAL_KIND = "credential"
MIN_KEY_LENGTH = 16
MAX_KEY_LENGTH = 1024


class StoreKey(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key: SecretStr
    consent_to_encrypted_storage: bool

    @field_validator("api_key")
    @classmethod
    def _plausible_key(cls, value: SecretStr) -> SecretStr:
        key = value.get_secret_value().strip()
        if not MIN_KEY_LENGTH <= len(key) <= MAX_KEY_LENGTH or not key.isprintable() or " " in key:
            # The message names the rule, never the value.
            raise ValueError("an API key is 16-1024 printable characters without spaces")
        return SecretStr(key)


def credential_context(workspace_id: uuid.UUID, credential_id: uuid.UUID) -> RecordContext:
    return RecordContext(CREDENTIAL_KIND, str(workspace_id), str(credential_id))


def _accepts_keys(workspace: Workspace, command: StoreKey) -> None:
    if workspace.data_mode is DataMode.DEMO:
        raise CareerwrightError(
            ErrorCode.MODE_NOT_SUPPORTED,
            "Demo workspaces run on fixtures only and never use a key.",
            stage=ErrorStage.CREDENTIAL,
        )
    if not command.consent_to_encrypted_storage:
        raise CareerwrightError(
            ErrorCode.CONSENT_REQUIRED,
            "Background work needs your agreement to store the key encrypted. Without it you "
            "can still edit your profile and use saved work.",
            stage=ErrorStage.CREDENTIAL,
        )


def _insert(
    tx: Tx,
    actor: Actor,
    workspace: Workspace,
    command: StoreKey,
    keyring: Keyring,
    now: datetime,
    defaults: SpendLimits,
) -> uuid.UUID:
    credential_id = uuid.uuid4()
    sealed = keyring.seal(
        command.api_key.get_secret_value().encode(),
        credential_context(workspace.workspace_id, credential_id),
    )
    credential_store.insert_credential(
        tx,
        credential_id=credential_id,
        workspace_id=workspace.workspace_id,
        sealed=sealed,
        consented_at=now,
        created_by=actor.actor_id,
    )
    credential_store.ensure_spend_limits(tx, workspace.workspace_id, defaults)
    return credential_id


def _found(tx: Tx, workspace_id: uuid.UUID, credential_id: uuid.UUID) -> Credential:
    found = credential_store.credential(tx, workspace_id, credential_id)
    if found is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such credential.", stage=ErrorStage.CREDENTIAL
        )
    return found


def _active(tx: Tx, workspace_id: uuid.UUID, credential_id: uuid.UUID) -> Credential:
    found = _found(tx, workspace_id, credential_id)
    if found.revoked_at is not None:
        # Distinct from "no such key" (Global Constraint 6): the key exists and is retired.
        raise CareerwrightError(
            ErrorCode.CREDENTIAL_REVOKED,
            "That key is already revoked. Store a new key instead.",
            stage=ErrorStage.CREDENTIAL,
            details={"credential_id": str(credential_id)},
        )
    return found


def store_credential(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: StoreKey,
    keyring: Keyring,
    now: datetime,
    defaults: SpendLimits,
) -> Credential:
    workspace = visible_workspace(tx, workspace_id, lock=True)
    _accepts_keys(workspace, command)
    active = [c for c in credential_store.credentials(tx, workspace_id) if c.revoked_at is None]
    if active:
        raise CareerwrightError(
            ErrorCode.CREDENTIAL_EXISTS,
            "This workspace already has an active key. Rotate it to replace it.",
            stage=ErrorStage.CREDENTIAL,
            details={"credential_id": str(active[0].credential_id)},
        )
    credential_id = _insert(tx, actor, workspace, command, keyring, now, defaults)
    store.append_event(tx, workspace_id, EventKind.CREDENTIAL_STORED, str(credential_id))
    return _found(tx, workspace_id, credential_id)


def rotate_credential(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    credential_id: uuid.UUID,
    command: StoreKey,
    keyring: Keyring,
    now: datetime,
    defaults: SpendLimits,
) -> Credential:
    workspace = visible_workspace(tx, workspace_id, lock=True)
    _accepts_keys(workspace, command)
    _active(tx, workspace_id, credential_id)
    # One active key per provider: retire the old one before the new one exists.
    credential_store.revoke(tx, credential_id, revoked_by=actor.actor_id)
    new_id = _insert(tx, actor, workspace, command, keyring, now, defaults)
    credential_store.set_replaced_by(tx, credential_id, new_id)
    store.append_event(
        tx,
        workspace_id,
        EventKind.CREDENTIAL_ROTATED,
        str(new_id),
        detail={"replaces": str(credential_id)},
    )
    return _found(tx, workspace_id, new_id)


def revoke_credential(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, credential_id: uuid.UUID
) -> Credential:
    visible_workspace(tx, workspace_id, lock=True)
    _active(tx, workspace_id, credential_id)
    credential_store.revoke(tx, credential_id, revoked_by=actor.actor_id)
    store.append_event(tx, workspace_id, EventKind.CREDENTIAL_REVOKED, str(credential_id))
    return _found(tx, workspace_id, credential_id)
