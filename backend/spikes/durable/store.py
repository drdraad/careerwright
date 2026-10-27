"""Application database for the spike: sealed private records, runs, outbox and attempts.

Workflows only ever see identifiers from here. Private text and credentials are stored
sealed and opened inside the bounded activity, after the ownership and revocation checks.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256

import psycopg
from pydantic import SecretStr

from spikes.durable.sealing import Keyring, RecordContext, SealedValue

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS credentials (
    credential_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    key_version integer NOT NULL,
    nonce bytea NOT NULL,
    ciphertext bytea NOT NULL,
    revoked_at timestamptz
);
CREATE TABLE IF NOT EXISTS private_payloads (
    payload_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    key_version integer NOT NULL,
    nonce bytea NOT NULL,
    ciphertext bytea NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    run_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    payload_id uuid NOT NULL REFERENCES private_payloads,
    credential_id uuid NOT NULL REFERENCES credentials,
    status text NOT NULL CHECK (status IN ('queued', 'succeeded', 'failed')),
    output_id uuid,
    failure_class text,
    CHECK ((status = 'succeeded') = (output_id IS NOT NULL)),
    CHECK ((status = 'failed') = (failure_class IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS run_outputs (
    output_id uuid PRIMARY KEY,
    run_id uuid NOT NULL UNIQUE REFERENCES runs,
    workspace_id uuid NOT NULL,
    key_version integer NOT NULL,
    nonce bytea NOT NULL,
    ciphertext bytea NOT NULL,
    content_sha256 text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE IF NOT EXISTS outbox (
    outbox_id bigserial PRIMARY KEY,
    workflow_id text NOT NULL UNIQUE,
    run_id uuid NOT NULL REFERENCES runs,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    dispatched_at timestamptz
);
CREATE TABLE IF NOT EXISTS activity_attempts (
    attempt_id bigserial PRIMARY KEY,
    run_id uuid NOT NULL REFERENCES runs,
    model_id text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    outcome text,
    input_tokens integer,
    cached_input_tokens integer,
    output_tokens integer,
    reasoning_tokens integer,
    web_search_queries integer,
    provider_response_id text
);
"""


class CredentialUnavailableError(Exception):
    """The run's credential is revoked or belongs to another workspace."""


def _required[T](row: T | None, what: str) -> T:
    if row is None:
        raise LookupError(f"expected a row: {what}")
    return row


@dataclass(frozen=True)
class OutboxEntry:
    outbox_id: int
    workflow_id: str
    run_id: str


@dataclass(frozen=True)
class ActivityInputs:
    workspace_id: str
    private_text: str
    api_key: SecretStr


@dataclass(frozen=True)
class AcceptedOutput:
    output_id: str
    newly_accepted: bool


@dataclass(frozen=True)
class AttemptUsage:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    web_search_queries: int
    provider_response_id: str | None


class AppStore:
    def __init__(self, conninfo: str, keyring: Keyring) -> None:
        self._conninfo = conninfo
        self._keyring = keyring

    @contextmanager
    def _transaction(self) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self._conninfo) as conn, conn.transaction():
            yield conn

    def install_schema(self) -> None:
        with self._transaction() as conn:
            conn.execute(SCHEMA_SQL)

    def store_credential(self, workspace_id: str, api_key: SecretStr) -> str:
        credential_id = str(uuid.uuid4())
        sealed = self._keyring.seal(
            api_key.get_secret_value().encode(),
            RecordContext("credential", workspace_id, credential_id),
        )
        with self._transaction() as conn:
            conn.execute(
                "INSERT INTO credentials VALUES (%s, %s, %s, %s, %s, NULL)",
                (credential_id, workspace_id, sealed.key_version, sealed.nonce, sealed.ciphertext),
            )
        return credential_id

    def revoke_credential(self, credential_id: str) -> None:
        with self._transaction() as conn:
            conn.execute(
                "UPDATE credentials SET revoked_at = clock_timestamp() WHERE credential_id = %s",
                (credential_id,),
            )

    def submit_run(self, workspace_id: str, credential_id: str, private_text: str) -> OutboxEntry:
        """Record the run and its outbox entry in one transaction (transactional outbox)."""
        run_id, payload_id = str(uuid.uuid4()), str(uuid.uuid4())
        workflow_id = f"profile-run-{run_id}"
        sealed = self._keyring.seal(
            private_text.encode(), RecordContext("payload", workspace_id, payload_id)
        )
        with self._transaction() as conn:
            conn.execute(
                "INSERT INTO private_payloads VALUES (%s, %s, %s, %s, %s)",
                (payload_id, workspace_id, sealed.key_version, sealed.nonce, sealed.ciphertext),
            )
            conn.execute(
                "INSERT INTO runs (run_id, workspace_id, payload_id, credential_id, status) "
                "VALUES (%s, %s, %s, %s, 'queued')",
                (run_id, workspace_id, payload_id, credential_id),
            )
            row = conn.execute(
                "INSERT INTO outbox (workflow_id, run_id) VALUES (%s, %s) RETURNING outbox_id",
                (workflow_id, run_id),
            ).fetchone()
        outbox_id = _required(row, "outbox insert")[0]
        return OutboxEntry(outbox_id=outbox_id, workflow_id=workflow_id, run_id=run_id)

    def pending_outbox(self) -> list[OutboxEntry]:
        with self._transaction() as conn:
            rows = conn.execute(
                "SELECT outbox_id, workflow_id, run_id::text FROM outbox "
                "WHERE dispatched_at IS NULL ORDER BY outbox_id"
            ).fetchall()
        return [OutboxEntry(*row) for row in rows]

    def mark_dispatched(self, outbox_id: int) -> None:
        with self._transaction() as conn:
            conn.execute(
                "UPDATE outbox SET dispatched_at = clock_timestamp() WHERE outbox_id = %s",
                (outbox_id,),
            )

    def begin_attempt(self, run_id: str, model_id: str) -> int:
        with self._transaction() as conn:
            row = conn.execute(
                "INSERT INTO activity_attempts (run_id, model_id) VALUES (%s, %s) "
                "RETURNING attempt_id",
                (run_id, model_id),
            ).fetchone()
        return int(_required(row, "attempt insert")[0])

    def finish_attempt(self, attempt_id: int, outcome: str, usage: AttemptUsage | None) -> None:
        with self._transaction() as conn:
            conn.execute(
                "UPDATE activity_attempts SET finished_at = clock_timestamp(), outcome = %s, "
                "input_tokens = %s, cached_input_tokens = %s, output_tokens = %s, "
                "reasoning_tokens = %s, web_search_queries = %s, provider_response_id = %s "
                "WHERE attempt_id = %s",
                (
                    outcome,
                    usage.input_tokens if usage else None,
                    usage.cached_input_tokens if usage else None,
                    usage.output_tokens if usage else None,
                    usage.reasoning_tokens if usage else None,
                    usage.web_search_queries if usage else None,
                    usage.provider_response_id if usage else None,
                    attempt_id,
                ),
            )

    def resolve_activity_inputs(self, run_id: str) -> ActivityInputs:
        """Open the run's private payload and credential, after ownership and revocation."""
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT r.workspace_id::text, p.payload_id::text, p.key_version, p.nonce, "
                "p.ciphertext, c.credential_id::text, c.workspace_id::text, c.revoked_at, "
                "c.key_version, c.nonce, c.ciphertext "
                "FROM runs r JOIN private_payloads p USING (payload_id) "
                "JOIN credentials c USING (credential_id) WHERE r.run_id = %s",
                (run_id,),
            ).fetchone()
        if row is None:
            raise LookupError(f"unknown run {run_id}")
        (workspace_id, payload_id, p_ver, p_nonce, p_ct) = row[:5]
        (credential_id, credential_workspace, revoked_at, c_ver, c_nonce, c_ct) = row[5:]
        if credential_workspace != workspace_id or revoked_at is not None:
            raise CredentialUnavailableError(credential_id)
        private_text = self._keyring.open(
            SealedValue(p_ver, p_nonce, p_ct), RecordContext("payload", workspace_id, payload_id)
        ).decode()
        api_key = self._keyring.open(
            SealedValue(c_ver, c_nonce, c_ct),
            RecordContext("credential", workspace_id, credential_id),
        ).decode()
        return ActivityInputs(workspace_id, private_text, SecretStr(api_key))

    def accept_output(self, run_id: str, workspace_id: str, validated_json: str) -> AcceptedOutput:
        """Persist the first validated output for a run; a re-executed activity reuses it."""
        output_id = str(uuid.uuid4())
        sealed = self._keyring.seal(
            validated_json.encode(), RecordContext("run_output", workspace_id, output_id)
        )
        with self._transaction() as conn:
            inserted = conn.execute(
                "INSERT INTO run_outputs (output_id, run_id, workspace_id, key_version, nonce, "
                "ciphertext, content_sha256) VALUES (%s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (run_id) DO NOTHING RETURNING output_id::text",
                (
                    output_id,
                    run_id,
                    workspace_id,
                    sealed.key_version,
                    sealed.nonce,
                    sealed.ciphertext,
                    sha256(validated_json.encode()).hexdigest(),
                ),
            ).fetchone()
            if inserted is not None:
                return AcceptedOutput(inserted[0], newly_accepted=True)
            existing = conn.execute(
                "SELECT output_id::text FROM run_outputs WHERE run_id = %s", (run_id,)
            ).fetchone()
        return AcceptedOutput(_required(existing, "accepted output")[0], newly_accepted=False)

    def open_output(self, output_id: str) -> str:
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT workspace_id::text, key_version, nonce, ciphertext FROM run_outputs "
                "WHERE output_id = %s",
                (output_id,),
            ).fetchone()
        workspace_id, version, nonce, ciphertext = _required(row, f"output {output_id}")
        return self._keyring.open(
            SealedValue(version, nonce, ciphertext),
            RecordContext("run_output", workspace_id, output_id),
        ).decode()

    def complete_run(self, run_id: str, outcome: dict[str, str]) -> None:
        with self._transaction() as conn:
            if outcome["status"] == "succeeded":
                conn.execute(
                    "UPDATE runs SET status = 'succeeded', output_id = %s WHERE run_id = %s",
                    (outcome["output_id"], run_id),
                )
            else:
                conn.execute(
                    "UPDATE runs SET status = 'failed', failure_class = %s WHERE run_id = %s",
                    (outcome["failure_class"], run_id),
                )
