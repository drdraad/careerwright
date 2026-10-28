"""Encrypted key storage with consent, rotation and revocation (MODEL-05/06/07)."""

import secrets
import uuid
from typing import Any

import psycopg
import pytest
from cryptography.exceptions import InvalidTag

from nessa.identity.credentials import credential_context
from nessa.identity.keyring import SealedValue, load_keyring
from nessa.seed import FIXTURE_WORKSPACE_ID, INVITED_ACTORS
from tests.support.client import ApiClient
from tests.support.infra import Infra
from tools.leak_scan import Needle, scan

pytestmark = pytest.mark.integration

ADA = str(INVITED_ACTORS[0].actor_id)


def new_key() -> str:
    return secrets.token_urlsafe(32)  # no fixed prefix, so fragment scans cannot misfire


def store_key(api: ApiClient, token: str, workspace_id: str, key: str, consent: bool = True) -> Any:
    return api.write(
        "POST",
        f"/v1/workspaces/{workspace_id}/credentials",
        token,
        {"api_key": key, "consent_to_encrypted_storage": consent},
    )


@pytest.mark.req("MODEL-07")
def test_storing_a_key_needs_explicit_consent(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]

    refused = store_key(api, ada, workspace_id, new_key(), consent=False)

    assert (refused.status_code, refused.json()["error"]["code"]) == (422, "CONSENT_REQUIRED")
    assert api.get(f"/v1/workspaces/{workspace_id}/credentials", ada).json() == {"items": []}
    # Declining keeps editing usable.
    assert api.get(f"/v1/workspaces/{workspace_id}/profile", ada).status_code == 200


@pytest.mark.req("MODEL-05", "MODEL-06")
def test_a_stored_key_is_sealed_bound_to_its_record_and_never_returned(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    key = new_key()

    stored = store_key(api, ada, workspace_id, key)
    listed = api.get(f"/v1/workspaces/{workspace_id}/credentials", ada)

    assert stored.status_code == 201
    assert key not in stored.text + listed.text
    [row] = infra.query(
        "SELECT credential_id::text, workspace_id::text, key_version, nonce, ciphertext "
        "FROM nessa.credentials WHERE workspace_id = %s",
        (workspace_id,),
    )
    keyring = load_keyring(infra.home / "keys")
    sealed = SealedValue(row["key_version"], bytes(row["nonce"]), bytes(row["ciphertext"]))
    context = credential_context(uuid.UUID(workspace_id), uuid.UUID(row["credential_id"]))
    assert keyring.open(sealed, context).decode() == key
    assert key.encode() not in bytes(row["ciphertext"])
    # Bound to its record: the same ciphertext does not open as another workspace's key.
    with pytest.raises(InvalidTag):
        keyring.open(sealed, credential_context(uuid.uuid4(), uuid.UUID(str(row["credential_id"]))))


@pytest.mark.req("MODEL-05")
def test_the_api_role_cannot_read_sealed_key_material(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    store_key(api, ada, workspace_id, new_key())

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        infra.as_role("pg_api", "SELECT ciphertext FROM nessa.credentials", actor=ADA)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        infra.as_role("pg_api", "SELECT nonce FROM nessa.credentials", actor=ADA)


def test_a_second_key_must_rotate_the_first(api: ApiClient, ada: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    first = store_key(api, ada, workspace_id, new_key()).json()

    second = store_key(api, ada, workspace_id, new_key())

    assert (second.status_code, second.json()["error"]["code"]) == (409, "CREDENTIAL_EXISTS")
    assert second.json()["error"]["details"] == {"credential_id": first["credential_id"]}


@pytest.mark.req("MODEL-05")
def test_rotation_replaces_the_active_key_and_revocation_retires_it(
    api: ApiClient, ada: str
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    base = f"/v1/workspaces/{workspace_id}/credentials"
    first = store_key(api, ada, workspace_id, new_key()).json()

    rotated = api.write(
        "POST",
        f"{base}/{first['credential_id']}/rotate",
        ada,
        {"api_key": new_key(), "consent_to_encrypted_storage": True},
    ).json()
    revoked = api.write("POST", f"{base}/{rotated['credential_id']}/revoke", ada).json()
    listed = {c["credential_id"]: c for c in api.get(base, ada).json()["items"]}

    assert listed[first["credential_id"]]["active"] is False
    assert listed[first["credential_id"]]["replaced_by"] == rotated["credential_id"]
    assert (revoked["active"], listed[rotated["credential_id"]]["active"]) == (False, False)
    kinds = [
        e["kind"] for e in api.get(f"/v1/workspaces/{workspace_id}/events", ada).json()["items"]
    ]
    assert kinds[-3:] == ["credential.stored", "credential.rotated", "credential.revoked"]


def test_demo_workspaces_never_take_a_key(api: ApiClient, ada: str) -> None:
    response = store_key(api, ada, str(FIXTURE_WORKSPACE_ID), new_key())

    assert (response.status_code, response.json()["error"]["code"]) == (422, "MODE_NOT_SUPPORTED")


@pytest.mark.req("SEC-01")
def test_another_actor_cannot_store_or_revoke_keys(api: ApiClient, ada: str, ben: str) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    stored = store_key(api, ada, workspace_id, new_key()).json()

    planted = store_key(api, ben, workspace_id, new_key())
    revoked = api.write(
        "POST", f"/v1/workspaces/{workspace_id}/credentials/{stored['credential_id']}/revoke", ben
    )

    assert planted.status_code == revoked.status_code == 404
    assert api.get(f"/v1/workspaces/{workspace_id}/credentials", ada).json()["items"][0]["active"]


@pytest.mark.req("MODEL-06", "SEC-04")
def test_a_key_is_never_echoed_by_errors_receipts_or_exports(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = api.create_workspace(ada)["workspace_id"]
    key = new_key()
    store_key(api, ada, workspace_id, key)
    responses = [
        store_key(api, ada, workspace_id, key),  # CREDENTIAL_EXISTS
        store_key(api, ada, workspace_id, key + " with a space"),  # validation error
        store_key(api, ada, workspace_id, key, consent=False),
        api.get(f"/v1/workspaces/{workspace_id}/export", ada),
    ]

    texts = [("response", r.text) for r in responses]
    cells = infra.database_cells("nessa_app")
    findings = scan([*texts, *cells], [Needle("key", key, fragment_length=12)])
    assert findings == []
    assert responses[1].json()["error"]["code"] == "VALIDATION_FAILED"
