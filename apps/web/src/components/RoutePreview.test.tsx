import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { RoutePreview as Preview, PreviewRoute } from "@/lib/fixtures/trace";
import { EvidenceDrawer, EvidenceProvider } from "./EvidenceDrawer";
import { RoutePreview } from "./RoutePreview";

const gbp = (minor: number) => ({ minor_units: minor, currency: "GBP" as const });

function route(letter: string, layer: number, overrides: Partial<PreviewRoute> = {}): PreviewRoute {
  return {
    key: `TRACE-01/${letter}`,
    letter,
    timeMonths: 4,
    economicCost: gbp(60000),
    directSpend: gbp(60000),
    paymentsByMonth: [gbp(15000)],
    incomeByMonth: [gbp(200000)],
    layer,
    condition: "once its assessed report is passed",
    start: "2027-01-01",
    finish: "2027-04-30",
    ...overrides,
  };
}

function preview(routes: PreviewRoute[]): Preview {
  return {
    state: "complete",
    source: {
      label: "TRACE-01 worked trace",
      locator: "fixtures/m0/worked_trace.json",
      sha256: "05f7",
      dataAsOf: "2027-01-01",
      purpose: "Synthetic trace",
    },
    traceId: "TRACE-01",
    targetTitle: "Data quality analyst",
    region: "Manchester, England",
    planningStart: "2027-01-01",
    horizonMonths: 6,
    routes,
    selected: { letter: "B", peakMonthlyPayment: gbp(15000), lowestBalance: gbp(485000) },
  };
}

function show(routes: PreviewRoute[]) {
  render(
    <EvidenceProvider>
      <RoutePreview preview={preview(routes)} />
      <EvidenceDrawer />
    </EvidenceProvider>,
  );
}

describe("[BND1-12] the fixture preview states only what the fixture's data says", () => {
  it("says every route shares a condition only when the data says so", () => {
    show([route("A", 1), route("B", 1, { condition: null })]);

    expect(screen.queryByText(/every route here is/)).not.toBeInTheDocument();
  });

  it("states the shared condition when every route has it", () => {
    show([route("A", 1), route("B", 1)]);

    expect(
      screen.getByText(/every route here is ready only once its assessed report is passed/),
    ).toBeInTheDocument();
  });

  it("orders layers as numbers and shows a negative economic cost with its sign", () => {
    show([route("A", 10), route("B", 2, { economicCost: gbp(-50000) })]);
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);

    expect(headings.indexOf("Layer 2bettered by at least one route above")).toBeLessThan(
      headings.indexOf("Layer 10bettered by at least one route above"),
    );
    expect(screen.getByText(/−£500 economic cost/)).toBeInTheDocument();
  });

  it("presents each route as a button that opens a dialog, not as a toggle", () => {
    show([route("A", 1)]);
    const card = screen.getByRole("button", { name: /^Route A/ });

    expect(card).toHaveAttribute("aria-haspopup", "dialog");
    expect(card).not.toHaveAttribute("aria-pressed");
  });
});

describe("[BND1-12][UI-09] each route keeps its condition and decision figures with it", () => {
  it("says Conditional beside each card's readiness, with its condition (V-01)", () => {
    show([route("A", 1, { timeMonths: 2 }), route("B", 1)]);

    for (const [letter, readiness] of [
      ["A", "2 months"],
      ["B", "4 months"],
    ]) {
      expect(
        screen.getByRole("button", { name: new RegExp(`^Route ${letter}`) }),
      ).toHaveTextContent(`Conditional: ready in ${readiness}, once its assessed report is passed`);
    }
    expect(screen.queryByText(/^Ready in/)).not.toBeInTheDocument();
  });

  it("says Ready in without a qualification only for a route the data says is ready", () => {
    show([route("A", 1, { condition: null })]);
    const card = screen.getByRole("button", { name: /^Route A/ });

    expect(card).toHaveTextContent("Ready in 4 months");
    expect(card).not.toHaveTextContent("Conditional");
  });

  it("states the cost, its baseline and horizon up front and keeps the rest behind a disclosure (V-03)", () => {
    show([route("A", 1)]);

    expect(
      screen.getByText(
        "Economic cost against the fixture's baseline, over the same 6 months for every route (January to June 2027).",
      ),
    ).toBeVisible();
    const details = screen.getByText("What's being compared").closest("details");
    expect(details).not.toHaveAttribute("open");
    expect(details).toHaveTextContent("fees plus pay lost against the fixture's baseline");
  });

  it("opens a route titled by its name, leading with its label, condition, readiness and costs (V-04)", async () => {
    show([route("A", 1), route("B", 1)]);
    await userEvent.setup().click(screen.getByRole("button", { name: /^Route B/ }));
    const drawer = screen.getByRole("dialog", { name: "Route B" });
    const lead = within(drawer).getByRole("group", { name: "Route B at a glance" });

    expect(within(lead).getByText("Synthetic fixture route")).toBeVisible();
    expect(lead).toHaveTextContent("Conditional: ready only once its assessed report is passed");
    const figures = within(lead)
      .getAllByRole("term")
      .map((term) => `${term.textContent} ${term.nextElementSibling?.textContent}`);
    expect(figures).toEqual(["Ready in 4 months", "Economic cost £600", "Direct spending £600"]);
    expect(within(drawer).getByRole("button", { name: "Close route B" })).toBeVisible();
  });
});
