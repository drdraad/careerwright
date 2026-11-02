// Connecting a Meta key (MODEL-07): consent comes first, the key is sent once with it and is
// never shown again; a stored key can be rotated or revoked.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { CredentialOut, WorkspaceOut } from "@/generated/api";
import { keys } from "@/lib/queries";
import { fakeApi } from "@/test/fakeApi";
import { KeySetup, MetaKeySetting } from "./KeySetup";

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

function renderKey(credentials: CredentialOut[], queries = new QueryClient()) {
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

  it("offers rotate and revoke for a stored key, and revokes only once confirmed", async () => {
    const sent = fakeApi([
      { method: "POST", path: /\/credentials\/c1\/revoke$/, answer: { ...stored, active: false } },
    ]);
    const user = renderKey([stored]);

    await user.click(screen.getByText(/Meta key: stored/));
    expect(screen.getByRole("button", { name: "Rotate the key" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Revoke the key" }));
    expect(sent.filter((s) => s.method === "POST")).toEqual([]); // not yet: it asks first
    expect(screen.getByText(/Calls that haven't started will stop/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Yes, revoke the key" }));

    await waitFor(() =>
      expect(sent.filter((s) => s.method === "POST").map((s) => s.path)).toEqual([
        "/v1/workspaces/w-key/credentials/c1/revoke",
      ]),
    );
  });

  it("answers an already revoked key in words and offers to store a new one", async () => {
    const sent = fakeApi([
      {
        method: "POST",
        path: /\/credentials\/c1\/revoke$/,
        status: 409,
        answer: {
          error: {
            code: "CREDENTIAL_REVOKED",
            message: "That key was already revoked.",
            retryable: false,
            stage: "request",
            correlation_id: "c2",
            details: {},
          },
        },
      },
    ]);
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queries.setQueryData(keys.credentials("w-key"), [stored]);
    const user = renderKey([stored], queries);

    await user.click(screen.getByText(/Meta key: stored/));
    await user.click(screen.getByRole("button", { name: "Revoke the key" }));
    await user.click(screen.getByRole("button", { name: "Yes, revoke the key" }));

    expect(await screen.findByText(/already revoked\. Store a new key/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Store the key" })).toBeVisible();
    expect(sent.filter((s) => s.method === "POST")).toHaveLength(1);
    // The stored list is out of date: it is marked for a refresh.
    expect(queries.getQueryState(keys.credentials("w-key"))?.isInvalidated).toBe(true);
  });

  it("keeps the typed key when storing it fails, and never offers it to the browser", async () => {
    fakeApi([
      {
        method: "POST",
        path: /\/credentials$/,
        status: 503,
        answer: {
          error: {
            code: "STORE_UNAVAILABLE",
            message: "The database is unavailable.",
            retryable: true,
            stage: "storage",
            correlation_id: "c3",
            details: {},
          },
        },
      },
    ]);
    const user = renderKey([]);
    const field = screen.getByLabelText("Meta API key");

    expect(field).toHaveAttribute("autocomplete", "new-password");
    await user.type(field, "test-key-not-real-0123456789");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Store the key" }));

    expect(await screen.findByRole("alert")).toBeVisible();
    expect(field).toHaveValue("test-key-not-real-0123456789");
  });
});

describe("[MODEL-07] the stored key is a setting in the account menu (session W2)", () => {
  function renderSetting(where: WorkspaceOut) {
    render(
      <QueryClientProvider
        client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
      >
        <MetaKeySetting workspace={where} />
      </QueryClientProvider>,
    );
    return userEvent.setup();
  }

  it("shows a stored key's date, with Rotate and Revoke one step away", async () => {
    fakeApi([{ method: "GET", path: /\/credentials$/, answer: { items: [stored] } }]);
    const user = renderSetting(workspace);

    await user.click(await screen.findByText(/^Meta key: stored \d+ \w+ \d{4}$/));
    expect(screen.getByRole("button", { name: "Rotate the key" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Revoke the key" })).toBeVisible();
  });

  it("says when no key is stored, and where to connect one", async () => {
    fakeApi([
      { method: "GET", path: /\/credentials$/, answer: { items: [{ ...stored, active: false }] } },
    ]);
    renderSetting(workspace);

    expect(
      await screen.findByText("Meta key: none stored. Connect one in the conversation."),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Store the key" })).toBeNull();
  });

  it("shows nothing in a demo workspace, which never calls a model, and asks for no key", () => {
    const sent = fakeApi([]);
    const { container } = render(
      <QueryClientProvider client={new QueryClient()}>
        <MetaKeySetting workspace={{ ...workspace, data_mode: "demo" }} />
      </QueryClientProvider>,
    );

    expect(container).toBeEmptyDOMElement();
    expect(sent).toEqual([]);
  });
});
