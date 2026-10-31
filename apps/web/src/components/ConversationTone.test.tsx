// How Careerwright talks with you is a preference (session 2: "ditch the tone selection - this
// should be in preferences"): kept in the account menu, saved with the same expected-version
// command as before.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { PreferencesOut } from "@/generated/api";
import { fakeApi } from "@/test/fakeApi";
import { ConversationTone } from "./ConversationTone";

const preferences: PreferencesOut = {
  version: 2,
  entry_mode: "unsure",
  conversation_mode: null,
  paused: false,
  updated_at: null,
};

describe("[PROF-08][UI-09] the tone is a preference, saved as an expected-version command", () => {
  it("offers the three tones and saves the choice with everything else unchanged", async () => {
    const sent = fakeApi([
      { method: "GET", path: /\/interview\/preferences$/, answer: preferences },
      {
        method: "PUT",
        path: /\/interview\/preferences$/,
        answer: { ...preferences, version: 3, conversation_mode: "gentle" },
      },
    ]);
    render(
      <QueryClientProvider client={new QueryClient()}>
        <ConversationTone workspaceId="w-tone" />
      </QueryClientProvider>,
    );
    const user = userEvent.setup();

    const tone = await screen.findByLabelText("How Careerwright talks with you");
    expect(tone).toHaveDisplayValue("Choose a tone");
    await user.selectOptions(tone, "Help me explore gently");

    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    expect(sent.find((s) => s.method === "PUT")?.body).toEqual({
      expected_version: 2,
      entry_mode: "unsure",
      conversation_mode: "gentle",
      paused: false,
    });
  });
});
