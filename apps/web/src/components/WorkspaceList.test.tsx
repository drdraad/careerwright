import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CreateWorkspace } from "./WorkspaceList";

function show() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <CreateWorkspace onCreated={() => undefined} />
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

describe("[UI-06] the data mode is a short choice with its full explanation beside it (V-05)", () => {
  it("names each mode in a word or two and explains the chosen one in wrapping text", async () => {
    const user = show();
    const mode = screen.getByRole("combobox", { name: "Data mode" });

    expect(Array.from(mode.querySelectorAll("option")).map((option) => option.textContent)).toEqual(
      ["Demo data", "Live-assisted"],
    );
    expect(mode).toHaveAccessibleDescription("Synthetic data only. Nothing leaves this computer.");

    await user.selectOptions(mode, "live_assisted");

    expect(mode).toHaveAccessibleDescription(
      "Uses your Meta API key for the interview and suggestions, so what you write is sent to Meta's model.",
    );
  });
});
