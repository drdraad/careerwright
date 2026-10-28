"""Revocations are final in the database; idempotency receipts belong to their workspace.

- A BEFORE UPDATE trigger makes a credential's revocation and its replacement link final,
  so no role (the API's included) can undo a revocation, even through an application bug.
  Only a revoked credential can name a replacement.
- Receipts hold copies of command responses (profile documents among them), so they gain a
  `workspace_id` that cascades: deleting a workspace, or `reset-demo`, leaves none behind.
  Existing receipts are attributed from their response where it names the workspace; the
  rest (run submission, credential and spend-limit receipts, whose responses carry no
  workspace ID) are dropped. They are retry caches only: a dropped one means a retry with
  that key runs the command again. Profile and spend-limit writes then meet their expected
  version and credential commands the credential's state, but run submission has no
  precondition, so a retried pre-upgrade submission would create a second run. Accepted
  because no released install has receipts to upgrade.

Forward-only (see `docs/runbook.md`).

Revision ID: 0003
"""

from nessa.migrations.sql import run_script

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE FUNCTION nessa.credential_revocation_is_final() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, pg_temp
    AS $$
BEGIN
    IF OLD.revoked_at IS NOT NULL AND (NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
                                       OR NEW.revoked_by IS DISTINCT FROM OLD.revoked_by) THEN
        RAISE EXCEPTION 'credential revocations and replacements are final'
            USING ERRCODE = 'check_violation';
    END IF;
    IF OLD.replaced_by IS NOT NULL AND NEW.replaced_by IS DISTINCT FROM OLD.replaced_by THEN
        RAISE EXCEPTION 'credential revocations and replacements are final'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER credential_revocation_is_final BEFORE UPDATE ON nessa.credentials
    FOR EACH ROW EXECUTE FUNCTION nessa.credential_revocation_is_final();
ALTER TABLE nessa.credentials ADD CONSTRAINT replacements_are_revoked
    CHECK (replaced_by IS NULL OR revoked_at IS NOT NULL);

ALTER TABLE nessa.command_receipts ADD COLUMN workspace_id uuid
    REFERENCES nessa.workspaces ON DELETE CASCADE;
UPDATE nessa.command_receipts r
    SET workspace_id = (r.response ->> 'workspace_id')::uuid
    WHERE r.response ? 'workspace_id'
      AND EXISTS (SELECT 1 FROM nessa.workspaces w
                  WHERE w.workspace_id = (r.response ->> 'workspace_id')::uuid);
DELETE FROM nessa.command_receipts WHERE workspace_id IS NULL;
ALTER TABLE nessa.command_receipts ALTER COLUMN workspace_id SET NOT NULL;
CREATE INDEX command_receipts_workspace ON nessa.command_receipts (workspace_id);
ALTER POLICY api_self ON nessa.command_receipts
    USING (actor_id = nessa.current_actor_id())
    WITH CHECK (
        actor_id = nessa.current_actor_id()
        AND workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w)
    );
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
