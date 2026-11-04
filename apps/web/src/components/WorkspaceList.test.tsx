import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { SupportNoteOut, WorkspaceSavedOut } from "@/generated/api";
import { fakeApi, type Route } from "@/test/fakeApi";
import { CreateWorkspace } from "./WorkspaceList";

function show(onCreated: (id: string) => void = () => undefined) {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <CreateWorkspace onCreated={onCreated} />
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

// The existing support-test sentence (web), and the panel's words as the API sends them.
const SCREENED = "I volunteer on a suicide prevention helpline.";
const panel = (message: string): SupportNoteOut => ({
  policy_version: "support-policy-11",
  review_status: "not yet reviewed as built",
  message,
  resources: [
    {
      name: "Samaritans",
      contact: "call 116 123",
      when: "any time",
      source_url: "https://www.samaritans.org/",
      checked_on: "2026-10-28",
    },
  ],
});
const created = (support_note: SupportNoteOut | null): WorkspaceSavedOut => ({
  workspace_id: "w-new",
  name: SCREENED,
  data_mode: "demo",
  synthetic: true,
  fixture: false,
  version: 1,
  last_event_seq: 0,
  created_at: "2026-11-01T10:00:00Z",
  updated_at: "2026-11-01T10:00:00Z",
  support_note,
});
const post = (status: number, answer: object): Route => ({
  method: "POST",
  path: /\/v1\/workspaces$/,
  status,
  answer,
});

describe("[PROF-09] a workspace's name goes through the support screen, as What we know's entries do", () => {
  it("creates the workspace as usual and shows the calm panel beside it, never moving on past it", async () => {
    const opened: string[] = [];
    const sent = fakeApi([
      post(
        201,
        created(panel("If anything you typed is about how you are feeling… saved as usual.")),
      ),
    ]);
    const user = show((id) => opened.push(id));

    await user.type(screen.getByRole("textbox", { name: "Name" }), SCREENED);
    await user.click(screen.getByRole("button", { name: "Create workspace" }));

    const shown = await screen.findByRole("region", { name: "Support is available" });
    expect(shown).toHaveTextContent("saved as usual.");
    expect(shown).toHaveTextContent("Samaritans");
    expect(sent.filter((s) => s.method === "POST")).toHaveLength(1);
    expect(opened).toEqual([]); // the panel is not skipped by a page change
    await user.click(within(shown).getByRole("button", { name: "Open the new workspace" }));
    expect(opened).toEqual(["w-new"]);
  });

  it("opens the new workspace straight away when its name brings no panel", async () => {
    const opened: string[] = [];
    fakeApi([post(201, { ...created(null), name: "My plan" })]);
    const user = show((id) => opened.push(id));

    await user.type(screen.getByRole("textbox", { name: "Name" }), "My plan");
    await user.click(screen.getByRole("button", { name: "Create workspace" }));

    await waitFor(() => expect(opened).toEqual(["w-new"]));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
  });

  it("shows the calm panel with a refusal, beside the refusal's own words", async () => {
    fakeApi([
      post(409, {
        error: {
          code: "IDEMPOTENCY_KEY_REUSED",
          message: "",
          retryable: false,
          stage: "request",
          correlation_id: "c2",
          details: {},
        },
        support_note: panel("If anything you typed… Your answers were not saved."),
      }),
    ]);
    const user = show();

    await user.type(screen.getByRole("textbox", { name: "Name" }), SCREENED);
    await user.click(screen.getByRole("button", { name: "Create workspace" }));

    const shown = await screen.findByRole("region", { name: "Support is available" });
    expect(shown).toHaveTextContent("Your answers were not saved.");
    expect(screen.getByText("The request was refused as a duplicate")).toBeVisible();
    await user.click(within(shown).getByRole("button", { name: /Dismiss/ }));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
  });
});

describe("[UI-06] the data mode is a short choice with its full explanation beside it (V-05)", () => {
  it("names each mode in a word or two and explains the chosen one in wrapping text", async () => {
    const user = show();
    const mode = screen.getByRole("combobox", { name: "Data mode" });

    expect(Array.from(mode.querySelectorAll("option")).map((option) => option.textContent)).toEqual(
      ["Demo mode", "Live-assisted"],
    );
    expect(mode).toHaveAccessibleDescription(
      "Uses synthetic records without a model key. A new workspace starts blank; preloaded sample workspaces have example answers.",
    );

    await user.selectOptions(mode, "live_assisted");

    expect(mode).toHaveAccessibleDescription(
      "Uses your Meta API key for the interview and suggestions, so what you write is sent to Meta's model.",
    );
  });
});
