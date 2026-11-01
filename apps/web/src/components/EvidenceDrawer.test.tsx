import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { EvidenceDrawer, EvidenceProvider, useEvidence } from "./EvidenceDrawer";

function Opener() {
  const evidence = useEvidence();
  return (
    <button
      type="button"
      onClick={() => evidence.open({ title: "Where this came from", body: <p>Route B</p> })}
    >
      Inspect route B
    </button>
  );
}

function setup() {
  render(
    <EvidenceProvider>
      <main>
        <Opener />
        <a href="#later">Something after</a>
      </main>
      <EvidenceDrawer />
    </EvidenceProvider>,
  );
  return userEvent.setup();
}

describe("[UI-06][UI-09] the evidence drawer takes focus and gives it back", () => {
  it("moves focus to the drawer's title when it opens", async () => {
    const user = setup();
    await user.click(screen.getByRole("button", { name: "Inspect route B" }));

    expect(screen.getByRole("dialog", { name: "Where this came from" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Where this came from" })).toHaveFocus();
  });

  it.each([
    ["Escape", async (user: ReturnType<typeof userEvent.setup>) => user.keyboard("{Escape}")],
    [
      "the Close button",
      async (user: ReturnType<typeof userEvent.setup>) =>
        user.click(screen.getByRole("button", { name: "Close where this came from" })),
    ],
  ])("returns focus to the control that opened it after %s", async (_how, dismiss) => {
    const user = setup();
    const opener = screen.getByRole("button", { name: "Inspect route B" });
    await user.click(opener);
    await dismiss(user);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
  });

  it("stays open while the work beside it is used (non-modal)", async () => {
    const user = setup();
    await user.click(screen.getByRole("button", { name: "Inspect route B" }));
    await user.click(screen.getByRole("link", { name: "Something after" }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("offers More and Less on the phone sheet as a real toggle", async () => {
    const user = setup();
    await user.click(screen.getByRole("button", { name: "Inspect route B" }));
    const toggle = screen.getByRole("button", { name: "More" });

    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await user.click(toggle);
    expect(screen.getByRole("button", { name: "Less" })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("dialog")).toHaveAttribute("data-expanded", "true");
  });
});
