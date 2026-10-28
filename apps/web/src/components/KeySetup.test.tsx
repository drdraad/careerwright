// Connecting a Meta key (MODEL-07): consent comes first, the key is sent once with it and is
// never shown again; a stored key can be rotated or revoked.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { CredentialOut, WorkspaceOut } from "@/generated/api";
import { fakeApi } from "@/test/fakeApi";
import { KeySetup } from "./KeySetup";

const workspace: WorkspaceOut = {
  workspace_id: "w-key",
  name: "Live (synthetic)",
  data_mode: "live_assisted",
  synthetic: true,
  fixture: false,
  version: 1,
  last_event_seq: 0,
  created_at: "2027-01-01T00:00:00Z",
  updated_at: "2027-01-01T00:00:00Z",
};
const stored: CredentialOut = {
  credential_id: "c1",
  provider: "meta",
  active: true,
  consented_at: "2027-01-01T00:00:00Z",
  created_by: "a1",
  created_at: "2027-01-01T00:00:00Z",
  revoked_at: null,
  replaced_by: null,
};

function renderKey(credentials: CredentialOut[]) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <KeySetup workspace={workspace} credentials={credentials} primary />
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

describe("[MODEL-07] a key is stored only after explicit consent to encrypted storage", () => {
  it("explains what is stored and where, and sends nothing until consent is given", async () => {
    const sent = fakeApi([{ method: "POST", path: /\/credentials$/, status: 201, answer: stored }]);
    const user = renderKey([]);
    const secret = "test-key-not-real-0123456789";

    expect(screen.getByText(/stores the key encrypted/)).toBeVisible();
    expect(screen.getByText(/test model, which Meta may train on/)).toBeVisible();
    expect(screen.getByText(/still edit your answers directly/)).toBeVisible();
    await user.type(screen.getByLabelText("Meta API key"), secret);
    await user.click(screen.getByRole("button", { name: "Store the key" }));
    expect(sent).toEqual([]); // no consent, no request
    expect(screen.getByText("Tick the consent box first.")).toBeVisible();

    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Store the key" }));

    await waitFor(() => expect(sent).toHaveLength(1));
    expect(sent[0]?.body).toEqual({ api_key: secret, consent_to_encrypted_storage: true });
    await waitFor(() => expect(screen.getByLabelText("Meta API key")).toHaveValue(""));
    expect(document.body.textContent).not.toContain(secret);
  });

  it("offers rotate and revoke for a stored key, which is never shown", async () => {
    const sent = fakeApi([
      { method: "POST", path: /\/credentials\/c1\/revoke$/, answer: { ...stored, active: false } },
    ]);
    const user = renderKey([stored]);

    await user.click(screen.getByText(/Meta key: stored/));
    await user.click(screen.getByRole("button", { name: "Revoke the key" }));

    await waitFor(() =>
      expect(sent.map((s) => s.path)).toEqual(["/v1/workspaces/w-key/credentials/c1/revoke"]),
    );
    expect(screen.getByRole("button", { name: "Rotate the key" })).toBeVisible();
  });
});
