import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { RoutePreview as Preview, PreviewRoute } from "@/lib/fixtures/trace";
import { EvidenceProvider } from "./EvidenceDrawer";
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
    condition: "ready only once its assessed report is passed",
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
