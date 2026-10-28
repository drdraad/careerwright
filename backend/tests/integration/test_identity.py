"""Sign-in is not authorisation: a verified token must also match an active invitation."""

import uuid

import pytest

from nessa.seed import INVITED_ACTORS
from tests.support.client import ApiClient
from tests.support.infra import (
    Infra,
    create_emulator_user,
    delete_emulator_user,
    revoke_tokens,
    sign_in,
    sign_in_seeded,
)

pytestmark = pytest.mark.integration


def error_code(response: object) -> str:
    return str(response.json()["error"]["code"])  # type: ignore[attr-defined]


def test_seeded_invited_identity_signs_in(api: ApiClient, ada: str) -> None:
    response = api.get("/v1/me", ada)

    assert response.status_code == 200
    assert response.json() == {
        "actor_id": str(INVITED_ACTORS[0].actor_id),
        "email": "ada@nessa.test",
        "display_name": "Ada Demo",
    }


@pytest.mark.req("SEC-01")
def test_missing_or_malformed_tokens_are_unauthenticated(api: ApiClient) -> None:
    for token in (None, "not-a-jwt", "eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0."):
        response = api.get("/v1/me", token)
        assert (response.status_code, error_code(response)) == (401, "UNAUTHENTICATED")


@pytest.mark.req("SEC-01")
def test_the_seeded_uninvited_identity_is_refused_everywhere(api: ApiClient, ada: str) -> None:
    uninvited = sign_in_seeded("uninvited")
    workspace = api.create_workspace(ada)

    for path in ("/v1/me", "/v1/workspaces", f"/v1/workspaces/{workspace['workspace_id']}"):
        response = api.get(path, uninvited)
        assert (response.status_code, error_code(response)) == (403, "NOT_INVITED"), path
    created = api.write(
        "POST", "/v1/workspaces", uninvited, {"name": "x", "data_mode": "demo", "synthetic": True}
    )
    assert (created.status_code, error_code(created)) == (403, "NOT_INVITED")


@pytest.mark.req("SEC-01")
def test_revoked_tokens_are_refused(api: ApiClient, infra: Infra) -> None:
    uid = f"revoke-{uuid.uuid4().hex[:8]}"
    create_emulator_user(uid, f"{uid}@nessa.test", "password-123456")
    token = sign_in(f"{uid}@nessa.test", "password-123456")
    infra.query(
        "INSERT INTO nessa.actors (actor_id, email, display_name, access) "
        "VALUES (%s, %s, 'Revoked tokens', 'active')",
        (uuid.uuid4(), f"{uid}@nessa.test"),
    )
    assert api.get("/v1/me", token).status_code == 200

    revoke_tokens(uid)

    response = api.get("/v1/me", token)
    assert (response.status_code, error_code(response)) == (401, "UNAUTHENTICATED")


@pytest.mark.req("SEC-01")
def test_a_revoked_invitation_loses_access_at_once(api: ApiClient, infra: Infra) -> None:
    uid = f"uninvite-{uuid.uuid4().hex[:8]}"
    email = f"{uid}@nessa.test"
    create_emulator_user(uid, email, "password-123456")
    token = sign_in(email, "password-123456")
    infra.query(
        "INSERT INTO nessa.actors (actor_id, email, display_name, access) "
        "VALUES (%s, %s, 'Soon revoked', 'active')",
        (uuid.uuid4(), email),
    )
    workspace = api.create_workspace(token)

    infra.query("UPDATE nessa.actors SET access = 'revoked' WHERE email = %s", (email,))

    for path in ("/v1/me", f"/v1/workspaces/{workspace['workspace_id']}"):
        response = api.get(path, token)
        assert (response.status_code, error_code(response)) == (403, "NOT_INVITED")


@pytest.mark.req("SEC-01")
def test_an_unverified_email_cannot_claim_an_invitation(api: ApiClient, infra: Infra) -> None:
    uid = f"unverified-{uuid.uuid4().hex[:8]}"
    email = f"{uid}@nessa.test"
    infra.query(
        "INSERT INTO nessa.actors (actor_id, email, display_name, access) "
        "VALUES (%s, %s, 'Unverified', 'active')",
        (uuid.uuid4(), email),
    )
    create_emulator_user(uid, email, "password-123456", verified=False)

    response = api.get("/v1/me", sign_in(email, "password-123456"))

    assert (response.status_code, error_code(response)) == (401, "UNAUTHENTICATED")


@pytest.mark.req("SEC-01")
def test_an_invitation_binds_to_the_first_account_and_refuses_a_second(
    api: ApiClient, infra: Infra
) -> None:
    email = f"bind-{uuid.uuid4().hex[:8]}@nessa.test"
    infra.query(
        "INSERT INTO nessa.actors (actor_id, email, display_name, access) "
        "VALUES (%s, %s, 'Bound', 'active')",
        (uuid.uuid4(), email),
    )
    first, second = f"first-{uuid.uuid4().hex[:8]}", f"second-{uuid.uuid4().hex[:8]}"
    create_emulator_user(first, email, "password-123456")
    assert api.get("/v1/me", sign_in(email, "password-123456")).status_code == 200
    # The first account is replaced by another account holding the same email.
    delete_emulator_user(first)
    create_emulator_user(second, email, "password-123456")

    response = api.get("/v1/me", sign_in(email, "password-123456"))

    assert (response.status_code, error_code(response)) == (403, "NOT_INVITED")
    [row] = infra.query("SELECT firebase_uid FROM nessa.actors WHERE email = %s", (email,))
    assert row["firebase_uid"] == first
