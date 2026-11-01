"""The person's selection of spans in their own example adverts (Task 10, backend half;
MAP1-01; ADR 0012, its Task 10 amendment line; ADR 0009, its Task 10 amendment line).

- `advert_span_selections`: for one target (its `title_key`) and one of the person's own
  pasted examples for it (`job_id`), the spans they chose, as UTF-16 code-unit offsets into the
  example's kept text, with that text's SHA-256. Offsets only: the words are read back from
  the sealed text, so no advert text is stored here. Append-only for the API role: each save
  is a new row taking the next capability version, and the latest for a target and example
  stands (an empty list clears it).
- `careerwright.pasted_example_document(attempt)`: the sealed body of a text the person
  pasted themselves (route `pasted_text`), and only in a workspace the calling actor owns
  while their access is active. The API role still reads no other source body: a fetched
  page's body stays the worker's alone (ADR 0009).

The CHECKs repeat the domain rules (`careerwright.capability.adverts`): at most twelve spans
per example, each an object with whole-number offsets.

Forward-only (see `docs/runbook.md`).

Revision ID: 0045
"""

from careerwright.migrations.sql import run_script

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE careerwright.advert_span_selections (
    selection_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    state_version integer NOT NULL CHECK (state_version >= 1),
    target_key text NOT NULL CHECK (char_length(target_key) BETWEEN 1 AND 200),
    job_id uuid NOT NULL,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    spans jsonb NOT NULL CHECK (
        jsonb_typeof(spans) = 'array'
        AND jsonb_array_length(spans) <= 12
        AND NOT jsonb_path_exists(
            spans,
            'lax $[*] ? (@.type() != "object" || !(exists(@.start)) || !(exists(@.end))'
            ' || @.start.type() != "number" || @.end.type() != "number"'
            ' || @.start < 0 || @.end <= @.start)'
        )
    ),
    recorded_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX advert_span_selections_by_target ON careerwright.advert_span_selections
    (workspace_id, target_key, job_id, recorded_at);
COMMENT ON TABLE careerwright.advert_span_selections IS
    'The spans the person chose in one of their own example adverts for a target, as offsets '
    'into its kept text (no advert text stored here). Append-only: the latest stands.';

CREATE FUNCTION careerwright.pasted_example_document(p_attempt uuid)
    RETURNS TABLE (content_sha256 text, key_version integer, nonce bytea, ciphertext bytea)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $$
        SELECT d.content_sha256, d.key_version, d.nonce, d.ciphertext
        FROM careerwright.source_documents d
        JOIN careerwright.source_attempts a ON a.attempt_id = d.attempt_id
        JOIN careerwright.workspaces w ON w.workspace_id = d.workspace_id
        JOIN careerwright.actors ac ON ac.actor_id = w.owner_actor_id
        WHERE d.attempt_id = p_attempt
          AND a.route = 'pasted_text'
          AND w.owner_actor_id = careerwright.current_actor_id()
          AND ac.access = 'active'
    $$;
COMMENT ON FUNCTION careerwright.pasted_example_document(uuid) IS
    'The sealed body of text the person pasted themselves, in a workspace the calling actor '
    'owns: never a fetched page''s body.';
REVOKE ALL ON FUNCTION careerwright.pasted_example_document(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION careerwright.pasted_example_document(uuid) TO careerwright_api;
"""

POLICIES = """
ALTER TABLE careerwright.advert_span_selections ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.advert_span_selections TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.advert_span_selections TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA + POLICIES)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
