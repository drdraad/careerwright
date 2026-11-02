"use client";
// Connecting a Meta key (spec section 16, MODEL-07): explicit consent to encrypted storage,
// in plain words about what is stored, where, what it is used for and what it is not, before
// the key is sent. Declining keeps editing and saved results usable. A stored key is never
// shown again; it can be rotated or revoked (once confirmed) here, and a key found already
// revoked is replaced by storing a new one. A typed key is cleared only once it is stored.
// The connect card leads the conversation while no key is stored; a stored key's details are
// a setting in the account menu (`MetaKeySetting`).
import { useQueryClient } from "@tanstack/react-query";
import { useId, useState } from "react";
import type { CredentialOut, WorkspaceOut } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { keys, useCredentials, useKeyChange } from "@/lib/queries";
import { NO_KEY_STORED } from "@/lib/vocabulary";
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
  /** Resolves whether the key was stored. */
  onSubmit(key: string): Promise<boolean>;
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
        if (consent && key.trim() !== "") {
          void onSubmit(key.trim()).then((stored) => {
            if (stored) setKey("");
          });
        }
      }}
    >
      <ul className="plain-list">
        <li>
          Careerwright stores the key encrypted (authenticated encryption) in its database on this
          computer. The master key that unlocks it is kept on this computer too, outside the
          database and the code.
        </li>
        <li>
          It is used only for this workspace's model calls that you start, such as interview replies
          and suggestions, within this workspace's spending limits.
        </li>
        <li>
          It is not end-to-end encrypted: Careerwright's own worker opens it just before each call.
          It is never shown again and Careerwright never keeps it in your browser; if your browser
          offers to save it, choose not to. It leaves this computer only in those calls to Meta.
        </li>
        {workspace.synthetic && (
          <li>
            This workspace is labelled synthetic, so Careerwright uses Meta's lower-cost test model,
            which Meta may train on. Enter only made-up details here.
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
          // Not a login password: ask password managers not to offer to save it.
          autoComplete="new-password"
          data-1p-ignore="true"
          data-lpignore="true"
          data-bwignore="true"
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
          I agree to Careerwright storing this key, encrypted, on this computer, as described above.
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
  const id = workspace.workspace_id;
  const queries = useQueryClient();
  const change = useKeyChange(id);
  const [rotating, setRotating] = useState(false);
  const [confirmRevoke, setConfirmRevoke] = useState(false);
  const active = credentials.find((credential) => credential.active);
  const revoked = change.error instanceof ApiError && change.error.code === "CREDENTIAL_REVOKED";

  // A key found already revoked: refresh the list (it is out of date) and offer a new key.
  const attempt = (pending: Promise<unknown>) =>
    pending.then(
      () => true,
      (error: unknown) => {
        if (error instanceof ApiError && error.code === "CREDENTIAL_REVOKED") {
          void queries.invalidateQueries({ queryKey: keys.credentials(id) });
        }
        return false;
      },
    );

  if (active === undefined || revoked) {
    return (
      <section className="card grid gap-12" aria-labelledby="key-title">
        <h2 id="key-title" className="section-title">
          Connect your Meta API key to talk with Careerwright
        </h2>
        {revoked ? (
          <p className="small">That key was already revoked. Store a new key to continue.</p>
        ) : (
          <p className="small">
            Not now? You can still edit your answers directly, and everything saved stays available.
          </p>
        )}
        <KeyForm
          workspace={workspace}
          primary={primary}
          submitLabel="Store the key"
          pending={change.isPending}
          onSubmit={(key) =>
            attempt(
              change.mutateAsync({
                action: "store",
                body: { api_key: key, consent_to_encrypted_storage: true },
              }),
            )
          }
        />
        {change.error !== null && !revoked && <RequestFailure error={change.error} />}
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
              attempt(
                change.mutateAsync({
                  action: "rotate",
                  credentialId: active.credential_id,
                  body: { api_key: key, consent_to_encrypted_storage: true },
                }),
              ).then((stored) => {
                if (stored) setRotating(false);
                return stored;
              })
            }
          />
        ) : confirmRevoke ? (
          <div className="grid gap-8">
            <p>
              Revoke this key? Calls that haven't started will stop, and Careerwright can't reply
              until you store a new key.
            </p>
            <div className="flex flex-wrap gap-8">
              <Button
                variant="secondary"
                onClick={() =>
                  void attempt(
                    change.mutateAsync({ action: "revoke", credentialId: active.credential_id }),
                  ).then(() => setConfirmRevoke(false))
                }
                disabledReason={change.isPending ? "Revoking…" : undefined}
              >
                Yes, revoke the key
              </Button>
              <Button variant="quiet" onClick={() => setConfirmRevoke(false)}>
                Keep the key
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap gap-8">
            <Button variant="secondary" onClick={() => setRotating(true)}>
              Rotate the key
            </Button>
            <Button variant="quiet" onClick={() => setConfirmRevoke(true)}>
              Revoke the key
            </Button>
          </div>
        )}
        {change.error !== null && <RequestFailure error={change.error} />}
      </div>
    </details>
  );
}

/**
 * The stored key as a setting in the account menu, beside model spending (session W2: its card
 * sat under every conversation). A stored key shows its date, with Rotate and Revoke one step
 * away; with none stored, one line says where to connect one (the conversation's card). A demo
 * workspace never calls a model, so it shows nothing and asks for no key.
 */
export function MetaKeySetting({ workspace }: { workspace: WorkspaceOut }) {
  const demo = workspace.data_mode === "demo";
  const credentials = useCredentials(workspace.workspace_id, !demo);
  if (demo) return null;
  if (credentials.data === undefined) {
    return credentials.error ? <RequestFailure error={credentials.error} /> : null;
  }
  if (!credentials.data.some((credential) => credential.active)) {
    return <p className="small muted">{NO_KEY_STORED}</p>;
  }
  return <KeySetup workspace={workspace} credentials={credentials.data} primary={false} />;
}
