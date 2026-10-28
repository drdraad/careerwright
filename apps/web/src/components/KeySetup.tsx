"use client";
// Connecting a Meta key (spec section 16, MODEL-07): explicit consent to encrypted storage,
// in plain words about what is stored, where, what it is used for and what it is not, before
// the key is sent. Declining keeps editing and saved results usable. A stored key is never
// shown again; it can be rotated or revoked here, and a revoked key is replaced by a new one.
import { useId, useState } from "react";
import type { CredentialOut, WorkspaceOut } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { useKeyChange } from "@/lib/queries";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

const when = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" });

function KeyForm({
  workspace,
  primary,
  submitLabel,
  onSubmit,
  pending,
}: {
  workspace: WorkspaceOut;
  primary: boolean;
  submitLabel: string;
  onSubmit(key: string): Promise<void>;
  pending: boolean;
}) {
  const id = useId();
  const [key, setKey] = useState("");
  const [consent, setConsent] = useState(false);
  return (
    <form
      className="grid gap-12"
      onSubmit={(event) => {
        event.preventDefault();
        if (consent && key.trim() !== "") void onSubmit(key.trim()).then(() => setKey(""));
      }}
    >
      <ul className="plain-list">
        <li>
          Nessa stores the key encrypted (authenticated encryption) in its database on this
          computer. The master key that unlocks it is kept on this computer too, outside the
          database and the code.
        </li>
        <li>
          It is used only for this workspace's model calls that you start, such as interview replies
          and suggestions, within this workspace's spending limits.
        </li>
        <li>
          It is not end-to-end encrypted: Nessa's own worker opens it just before each call. It is
          never shown again, never kept in your browser, and it leaves this computer only in those
          calls to Meta.
        </li>
        {workspace.synthetic && (
          <li>
            This workspace is labelled synthetic, so Nessa uses Meta's lower-cost test model, which
            Meta may train on. Enter only made-up details here.
          </li>
        )}
        <li>
          You can rotate or revoke it at any time. Revoking stops every call that hasn't started.
        </li>
      </ul>
      <div className="grid gap-4">
        <label htmlFor={`${id}-key`} className="small muted">
          Meta API key
        </label>
        <input
          id={`${id}-key`}
          className="input"
          type="password"
          autoComplete="off"
          spellCheck={false}
          value={key}
          onChange={(event) => setKey(event.target.value)}
        />
      </div>
      <label className="flex items-start gap-8 small">
        <input
          type="checkbox"
          checked={consent}
          onChange={(event) => setConsent(event.target.checked)}
        />
        <span>
          I agree to Nessa storing this key, encrypted, on this computer, as described above.
        </span>
      </label>
      <div>
        <Button
          type="submit"
          variant={primary ? "primary" : "secondary"}
          disabledReason={
            pending
              ? "Saving…"
              : !consent
                ? "Tick the consent box first."
                : key.trim() === ""
                  ? "Enter the key first."
                  : undefined
          }
        >
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}

export function KeySetup({
  workspace,
  credentials,
  primary,
}: {
  workspace: WorkspaceOut;
  credentials: CredentialOut[];
  primary: boolean;
}) {
  const change = useKeyChange(workspace.workspace_id);
  const [rotating, setRotating] = useState(false);
  const active = credentials.find((credential) => credential.active);
  const revokedError =
    change.error instanceof ApiError && change.error.code === "CREDENTIAL_REVOKED";

  if (active === undefined) {
    return (
      <section className="card grid gap-12" aria-labelledby="key-title">
        <h2 id="key-title" className="section-title">
          Connect your Meta API key to talk with Nessa
        </h2>
        <p className="small">
          Not now? You can still edit your answers directly, and everything saved stays available.
        </p>
        <KeyForm
          workspace={workspace}
          primary={primary}
          submitLabel="Store the key"
          pending={change.isPending}
          onSubmit={(key) =>
            change
              .mutateAsync({
                action: "store",
                body: { api_key: key, consent_to_encrypted_storage: true },
              })
              .then(() => undefined)
              .catch(() => undefined)
          }
        />
        {change.error !== null && <RequestFailure error={change.error} />}
      </section>
    );
  }
  return (
    <details className="details small">
      <summary>Meta key: stored {when.format(new Date(active.created_at))}</summary>
      <div className="grid gap-12 mt-8">
        {rotating ? (
          <KeyForm
            workspace={workspace}
            primary={false}
            submitLabel="Replace the key"
            pending={change.isPending}
            onSubmit={(key) =>
              change
                .mutateAsync({
                  action: "rotate",
                  credentialId: active.credential_id,
                  body: { api_key: key, consent_to_encrypted_storage: true },
                })
                .then(() => setRotating(false))
                .catch(() => undefined)
            }
          />
        ) : (
          <div className="flex flex-wrap gap-8">
            <Button variant="secondary" onClick={() => setRotating(true)}>
              Rotate the key
            </Button>
            <Button
              variant="quiet"
              onClick={() =>
                void change
                  .mutateAsync({ action: "revoke", credentialId: active.credential_id })
                  .catch(() => undefined)
              }
            >
              Revoke the key
            </Button>
          </div>
        )}
        {revokedError ? (
          <p className="small">That key was already revoked. Store a new key to continue.</p>
        ) : (
          change.error !== null && <RequestFailure error={change.error} />
        )}
      </div>
    </details>
  );
}
