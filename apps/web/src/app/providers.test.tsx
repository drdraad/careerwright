import { useQueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { type ReactNode, useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { useEvidence } from "@/components/EvidenceDrawer";
import type { AuthState } from "@/lib/auth";
import { Providers } from "./providers";

const auth = vi.hoisted(() => ({
  state: { status: "signed_in", uid: "ada", email: "ada@example.test" } as AuthState,
  token: async () => "test-token",
}));

vi.mock("@/lib/auth", () => ({
  AuthProvider: ({ children }: { children: ReactNode }) => children,
  useAuth: () => auth,
}));

function AccountContent() {
  const queries = useQueryClient();
  const evidence = useEvidence();
  const [draft, setDraft] = useState("");
  return (
    <>
      <input aria-label="Draft" value={draft} onChange={(event) => setDraft(event.target.value)} />
      <button
        type="button"
        onClick={() => {
          queries.setQueryData(["me"], "Ada's private account");
          evidence.open({ title: "Ada's evidence", body: "Private evidence" });
        }}
      >
        Save account state
      </button>
      <p>Cached account: {queries.getQueryData<string>(["me"]) ?? "empty"}</p>
      <p>Evidence: {evidence.evidence?.title ?? "closed"}</p>
    </>
  );
}

describe("[AUTH-01][UI-09] account state isolation", () => {
  it("discards cached data, drafts and evidence when one signed-in identity replaces another", async () => {
    const settings = { emulatorUrl: "http://127.0.0.1:9099", projectId: "test" };
    const view = () => (
      <Providers auth={settings}>
        <AccountContent />
      </Providers>
    );
    const user = userEvent.setup();
    const { rerender } = render(view());
    await user.type(screen.getByRole("textbox", { name: "Draft" }), "Ada's draft");
    await user.click(screen.getByRole("button", { name: "Save account state" }));
    expect(screen.getByText("Evidence: Ada's evidence")).toBeVisible();

    auth.state = { status: "signed_in", uid: "ben", email: "ben@example.test" };
    rerender(view());

    expect(screen.getByText("Cached account: empty")).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Draft" })).toHaveValue("");
    expect(screen.getByText("Evidence: closed")).toBeVisible();
  });
});
