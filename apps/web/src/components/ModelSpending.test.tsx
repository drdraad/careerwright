// The spending line (MODEL-10; the audit's F10): spent this month, the limits and Change,
// through the spend endpoints, in US dollars as Meta bills.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { SpendOut } from "@/generated/api";
import { ERROR_STATEMENT, FAILURE_CLASS, RAISE_THE_LIMIT } from "@/lib/vocabulary";
import { fakeApi } from "@/test/fakeApi";
import { ModelSpending } from "./ModelSpending";

const spend: SpendOut = {
  run_limit_nano_usd: 750_000_000,
  period_limit_nano_usd: 5_120_000_000,
  version: 2,
  period_start: "2026-11-01",
  period_committed_nano_usd: 420_000_000,
  unknown_cost_attempts: 1,
};

function shown(demo = false) {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ModelSpending workspaceId="w-spend" demo={demo} />
    </QueryClientProvider>,
  );
}

describe("[MODEL-10] the spending line shows what was spent and the limit, and changes it", () => {
  it("states this month's spend, the limits and calls whose cost is unknown", async () => {
    fakeApi([{ method: "GET", path: /\/spend$/, answer: spend }]);
    shown();

    expect(await screen.findByText("$0.42 of $5.12 spent this month")).toBeVisible();
    expect(screen.getByRole("heading", { name: "Model spending" })).toBeVisible();
    expect(screen.getByText("Each run can use up to $0.75.")).toBeVisible();
    expect(
      screen.getByText(
        "Meta didn't report the cost of 1 call, so Careerwright counts it at its most.",
      ),
    ).toBeVisible();
    expect(screen.getByText("Meta bills in US dollars.")).toBeVisible();
  });

  it("changes the limits with the expected-version command, in dollars", async () => {
    const sent = fakeApi([
      { method: "GET", path: /\/spend$/, answer: spend },
      {
        method: "PUT",
        path: /\/spend\/limits$/,
        answer: { ...spend, version: 3, period_limit_nano_usd: 8_000_000_000 },
      },
    ]);
    shown();
    const user = userEvent.setup();

    await user.click(await screen.findByRole("button", { name: "Change" }));
    const month = screen.getByLabelText("Monthly limit, in US dollars");
    expect(month).toHaveValue("5.12");
    expect(screen.getByLabelText("Most for one run, in US dollars")).toHaveValue("0.75");
    await user.clear(month);
    await user.type(month, "8");
    await user.click(screen.getByRole("button", { name: "Save limits" }));

    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    expect(sent.find((s) => s.method === "PUT")?.body).toEqual({
      expected_version: 2,
      period_limit_nano_usd: 8_000_000_000,
      run_limit_nano_usd: 750_000_000,
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Saved.");
  });

  it("refuses an amount it can't read, saying why, and sends nothing", async () => {
    const sent = fakeApi([{ method: "GET", path: /\/spend$/, answer: spend }]);
    shown();
    const user = userEvent.setup();

    await user.click(await screen.findByRole("button", { name: "Change" }));
    const run = screen.getByLabelText("Most for one run, in US dollars");
    await user.clear(run);
    await user.type(run, "0.755");
    await user.click(screen.getByRole("button", { name: "Save limits" }));

    expect(screen.getByText("Use at most two digits after the point.")).toBeVisible();
    expect(run).toHaveAttribute("aria-invalid", "true");
    expect(sent.some((s) => s.method === "PUT")).toBe(false);
  });

  it("says a demo workspace spends nothing, and asks the API nothing", () => {
    const sent = fakeApi([]);
    shown(true);

    expect(
      screen.getByText("This demo workspace never calls a model, so it spends nothing."),
    ).toBeVisible();
    expect(sent).toEqual([]);
  });

  it("the words for a reached limit point to the spending line", () => {
    const where = "You can raise the limit under Model spending, in the Account and settings menu.";
    expect(RAISE_THE_LIMIT).toBe(where);
    expect(FAILURE_CLASS.budget_exceeded.action).toContain(where);
    expect(ERROR_STATEMENT.BUDGET_EXCEEDED.action).toContain(where);
  });
});
