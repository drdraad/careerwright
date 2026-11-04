import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { RouteDetail } from "@/generated/api";
import { routeDetailFixture } from "@/test/routeDetailData";
import { EvidenceDrawer, EvidenceProvider } from "./EvidenceDrawer";
import { RouteDetailView } from "./RouteDetailView";

const detail = routeDetailFixture;

const show = (shown: RouteDetail = detail) =>
  render(
    <EvidenceProvider>
      <RouteDetailView detail={shown} />
      <EvidenceDrawer />
    </EvidenceProvider>,
  );

describe("[VIS2-01][FUNDING-06] a chosen route keeps its conditions, money and sources apart", () => {
  it("leads with the qualified verdict and a fee loan that is not the person's spending", () => {
    show();
    expect(screen.getByRole("heading", { name: "Route 2" })).toBeVisible();
    expect(screen.getByText(/Uses an option you added that has not been reviewed/)).toBeVisible();
    expect(screen.getByText(/Needs the loan to be approved and repaid later/)).toBeVisible();
    expect(
      screen.getByText(/Tuition Fee Loan: amount paid straight to the provider £9,250/),
    ).toBeVisible();
    expect(screen.getByText(/Repayment: Not known yet/)).toBeVisible();
    expect(screen.getByRole("heading", { name: "Nursing degree", hidden: true })).not.toBeVisible();
  });

  it("shows the monthly ledger, dates and cited span only after the person opens them", async () => {
    show();
    await userEvent.click(screen.getByText("How this route fits together"));
    expect(
      screen.getByRole("table", { name: "When each step is active in the monthly model" }),
    ).toBeVisible();
    expect(screen.getByText(/2 months, from July 2027 to August 2027/)).toBeVisible();

    await userEvent.click(screen.getByText("Steps and evidence"));
    expect(screen.getByRole("heading", { name: "Nursing degree" })).toBeVisible();
    expect(screen.getByText(/Course or job: Not reviewed yet/)).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "See evidence" }));
    expect(
      within(screen.getByRole("dialog")).getByText(/The course starts in September/),
    ).toBeVisible();

    await userEvent.click(screen.getByText("Money month by month"));
    const ledger = screen.getByRole("table", { name: "Money in each month of this route" });
    expect(within(ledger).getByText("£9,250")).toBeVisible();
    expect(within(ledger).getAllByText("Not known yet").length).toBeGreaterThan(0);
    expect(
      within(ledger).queryByText("Pay if you followed your other path"),
    ).not.toBeInTheDocument();
  });

  it("links a cited provider page when its URL is known", async () => {
    const step = detail.steps[0];
    const source = step?.sources[0];
    if (!step || !source) throw new Error("Missing test source");
    show({
      ...detail,
      steps: [
        {
          ...step,
          sources: [{ ...source, source_url: "https://example.com/course" }],
        },
      ],
    });
    await userEvent.click(screen.getByText("Steps and evidence"));
    await userEvent.click(screen.getByRole("button", { name: "See evidence" }));
    expect(
      within(screen.getByRole("dialog")).getByRole("link", { name: "Open source page" }),
    ).toHaveAttribute("href", "https://example.com/course");
  });

  it("keeps a stated month as a month when no exact day was given", async () => {
    const firstStep = detail.steps[0];
    if (firstStep === undefined) throw new Error("Missing test step");
    show({
      ...detail,
      steps: [{ ...firstStep, start_date: null, finish_date: null }],
    });
    await userEvent.click(screen.getByText("Steps and evidence"));
    expect(screen.getByText(/September 2027 to July 2030/)).toBeVisible();
    expect(screen.queryByText(/1 September 2027 to 1 July 2030/)).not.toBeInTheDocument();
  });

  it("keeps stress cases separate and uses the comparison's cost basis", async () => {
    show();
    await userEvent.click(screen.getByText("What could change"));
    expect(screen.getByText(/If the start is delayed/)).toBeVisible();
    expect(screen.getByText(/What you'd pay out: Not known yet/)).toBeVisible();
    expect(screen.getByText(/If you pay the fee yourself/)).toBeVisible();
    expect(screen.getByText(/What you'd pay out: £9,250/)).toBeVisible();
  });
});
