import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { londonToday } from "@/lib/dates";
import { fakeApi } from "@/test/fakeApi";
import { planRoute, savedPlan } from "@/test/planData";
import { EvidenceProvider } from "./EvidenceDrawer";
import { PlanChapter, PlanContent } from "./PlanChapter";

const RUN = savedPlan.source.solve_run_id;
const firstStep = savedPlan.route.steps[0];
if (!firstStep) throw new Error("Plan fixture needs a route step");
const revision = {
  from_version: 1,
  proposed_solve_run_id: RUN,
  proposed_schedule_index: 1,
  proposed_route: planRoute,
  proposed_search: savedPlan.search,
  completed_steps: [],
  difference: {
    added_steps: [],
    removed_steps: [],
    changed_steps: [],
    old_readiness_month: "2027-05",
    new_readiness_month: "2027-05",
    old_direct_cost: planRoute.schedule.direct_cost,
    new_direct_cost: planRoute.schedule.direct_cost,
    old_economic_cost: null,
    new_economic_cost: null,
    same_accounting_basis: true,
    old_basis: savedPlan.route.basis,
    new_basis: planRoute.basis,
    remaining_horizon_recalculated: false,
  },
};
const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <EvidenceProvider>{children}</EvidenceProvider>
  </QueryClientProvider>
);

afterEach(() => window.history.replaceState({}, "", "/"));

describe("[PLAN-01][STATE-06] Plan saves a reviewed computed route", () => {
  it("shows the next month honestly when no exact date exists", async () => {
    render(<PlanContent plan={savedPlan} />, { wrapper });
    const overview = screen.getByRole("region", { name: "Chosen plan overview" });
    expect(
      within(overview).getByText(/Check when Data course can start in December 2026/),
    ).toBeVisible();
    expect(within(overview).getByText(/An exact date is not known yet/)).toBeVisible();
    await userEvent.click(screen.getByText("About this saved version"));
    expect(screen.getByText(/Later edits do not change it/)).toBeVisible();
    expect(screen.getAllByText("£1,200").length).toBeGreaterThan(0);
  });

  it("does not suggest a completed step or a new action during recorded rest", () => {
    render(
      <PlanContent
        plan={{
          ...savedPlan,
          progress: { completed_steps: ["step-1"], rest_until: "2027-01-01", activity: [] },
        }}
      />,
      { wrapper },
    );
    const overview = screen.getByRole("region", { name: "Chosen plan overview" });
    expect(within(overview).getByText(/Rest was recorded through 1 January 2027/)).toBeVisible();
    expect(
      within(overview).queryByText(/Check when Data course can start/),
    ).not.toBeInTheDocument();
  });

  it("says all steps are reported complete when no unfinished step remains", () => {
    render(
      <PlanContent
        plan={{ ...savedPlan, progress: { completed_steps: ["step-1"], activity: [] } }}
      />,
      { wrapper },
    );
    expect(
      within(screen.getByRole("region", { name: "Chosen plan overview" })).getByText(
        /You reported every step complete/,
      ),
    ).toBeVisible();
  });

  it("gives an employer check instead of calling a zero-step route complete", () => {
    render(
      <PlanContent
        plan={{ ...savedPlan, route: { ...savedPlan.route, steps: [] }, next_action: null }}
      />,
      { wrapper },
    );
    const overview = screen.getByRole("region", { name: "Chosen plan overview" });
    expect(
      within(overview).getByText(/Check current employer requirements and your evidence/),
    ).toBeVisible();
    expect(within(overview).getByRole("link", { name: "Roles" })).toHaveAttribute(
      "href",
      `/w/${savedPlan.workspace_id}/roles`,
    );
    expect(within(overview).queryByText(/0 of 0 steps/)).not.toBeInTheDocument();
  });

  it("shows a scheduled review as the next action", () => {
    render(
      <PlanContent
        plan={{
          ...savedPlan,
          next_action: {
            key: "plan:review",
            kind: "review",
            variant_id: "plan:review",
            title: "this plan",
            on: "2027-03-01",
            conditional: false,
            proposed: true,
          },
        }}
      />,
      { wrapper },
    );
    expect(
      within(screen.getByRole("region", { name: "Chosen plan overview" })).getByText(
        /Review this plan on 1 March 2027/,
      ),
    ).toBeVisible();
  });

  it("treats an elapsed start month as past when no exact action remains", () => {
    render(
      <PlanContent
        plan={{
          ...savedPlan,
          route: {
            ...savedPlan.route,
            steps: [{ ...firstStep, start_month: "2020-01" }],
          },
        }}
      />,
      { wrapper },
    );
    expect(
      within(screen.getByRole("region", { name: "Chosen plan overview" })).getByText(
        /The planned start month for Data course has passed/,
      ),
    ).toBeVisible();
  });

  it("builds a print copy without financial or person supplied details when omitted", () => {
    render(<PlanContent plan={savedPlan} printOmitFinancial printOmitSensitive />, { wrapper });
    const copy = screen.getByRole("region", {
      name: "Plan copy with omitted details",
      hidden: true,
    });
    expect(copy.closest("[data-print-redacted]")).toHaveAttribute("data-print-redacted", "true");
    expect(within(copy).getByText("Synthetic demo")).toBeInTheDocument();
    expect(
      within(screen.getByRole("region", { name: "Chosen plan overview" })).getByText(
        "Synthetic demo",
      ),
    ).toBeInTheDocument();
    expect(within(copy).queryByText(/£1,200|Your figures, not checked/)).toBeNull();
    expect(within(copy).getByText(/Data course, starts in December 2026/)).toBeInTheDocument();
  });

  it("does not label a live print copy synthetic", () => {
    render(
      <PlanContent
        plan={{
          ...savedPlan,
          route: {
            ...savedPlan.route,
            basis: { ...savedPlan.route.basis, synthetic: false },
            label: { ...savedPlan.route.label, synthetic: false },
          },
        }}
        printOmitSensitive
      />,
      { wrapper },
    );
    const copy = screen.getByRole("region", {
      name: "Plan copy with omitted details",
      hidden: true,
    });
    expect(within(copy).queryByText("Synthetic demo")).toBeNull();
    expect(
      within(screen.getByRole("region", { name: "Chosen plan overview" })).queryByText(
        "Synthetic demo",
      ),
    ).toBeNull();
  });

  it("hides an own option's title in the redacted print copy and next action", () => {
    const ownPlan = {
      ...savedPlan,
      next_action: {
        key: "step-1:start",
        kind: "start" as const,
        variant_id: "step-1",
        title: "Private evening course",
        on: "2027-01-01",
        conditional: false,
        proposed: true as const,
      },
      route: {
        ...savedPlan.route,
        steps: [
          {
            ...firstStep,
            title: "Private evening course",
            provider: "Private college",
            added_by_person: true,
          },
        ],
      },
    };
    render(<PlanContent plan={ownPlan} printOmitSensitive />, { wrapper });
    const copy = screen.getByRole("region", {
      name: "Plan copy with omitted details",
      hidden: true,
    });
    expect(within(copy).getByText(/Check the start of your option/)).toBeInTheDocument();
    expect(within(copy).getByText(/Your option, starts in December 2026/)).toBeInTheDocument();
    expect(within(copy).queryByText(/Private evening course|Private college/)).toBeNull();
  });

  it("opens the saved route details for browser printing, then restores the screen", async () => {
    fakeApi([{ method: "GET", path: /\/planning\/plans\/current$/, answer: savedPlan }]);
    render(<PlanChapter workspaceId="workspace" />, { wrapper });
    const overview = await screen.findByRole("region", { name: "Chosen plan overview" });
    expect(overview.parentElement).toHaveAttribute("data-print-redacted", "true");
    await userEvent.click(
      screen.getByRole("checkbox", {
        name: /Hide own option names, providers, requirements and source excerpts in the plan JSON and print/,
      }),
    );
    expect(overview.parentElement).toHaveAttribute("data-print-redacted", "false");
    const details = screen.getByText("Money month by month").closest("details");
    expect(details).not.toHaveAttribute("open");
    window.dispatchEvent(new Event("beforeprint"));
    expect(details).toHaveAttribute("open");
    window.dispatchEvent(new Event("afterprint"));
    expect(details).not.toHaveAttribute("open");
  });

  it("requires confirmation and sends the selected archive index with the current version", async () => {
    window.history.replaceState({}, "", `/?solve_run_id=${RUN}&schedule_index=1`);
    let chosen = false;
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/planning\/plans\/current$/,
        answer: () => (chosen ? { ...savedPlan, version: 2 } : savedPlan),
      },
      {
        method: "GET",
        path: /\/planning\/solves\/[^/]+$/,
        answer: { run: { run_id: RUN, status: "complete" }, target_title: "Data quality analyst" },
      },
      { method: "GET", path: /\/schedules\/1$/, answer: planRoute },
      {
        method: "GET",
        path: /\/planning\/plans\/revision-preview$/,
        answer: revision,
      },
      { method: "GET", path: /\/planning\/plans\/changes$/, answer: { new_solve_needed: false } },
      { method: "GET", path: /\/planning\/plans\/history$/, answer: [] },
      {
        method: "POST",
        path: /\/planning\/plans$/,
        answer: () => {
          chosen = true;
          return { ...savedPlan, version: 2 };
        },
      },
    ]);

    render(<PlanChapter workspaceId="workspace" />, { wrapper });
    await waitFor(() => expect(sent.length).toBeGreaterThanOrEqual(3));
    const save = await screen.findByRole("button", { name: "Save this plan" }, { timeout: 5000 });
    expect(save).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(save);
    expect(sent.some((request) => request.method === "POST")).toBe(false);
    await userEvent.click(screen.getByRole("checkbox", { name: /I have reviewed this route/ }));
    await userEvent.click(save);
    await waitFor(() => expect(sent.some((request) => request.method === "POST")).toBe(true));
    const post = sent.find((request) => request.method === "POST");
    expect(post?.body).toEqual({
      expected_version: 1,
      solve_run_id: RUN,
      schedule_index: 1,
      assumptions_confirmed: true,
    });
    const overview = await screen.findByRole("region", { name: "Chosen plan overview" });
    expect(within(overview).getByText(/Plan version 2/)).toBeVisible();
  });

  it("requires full-horizon acknowledgment before revising a plan with completed work", async () => {
    window.history.replaceState({}, "", `/?solve_run_id=${RUN}&schedule_index=1`);
    const previous = {
      ...savedPlan,
      progress: { completed_steps: ["step-1"], rest_until: null, review_on: null, activity: [] },
    };
    const sent = fakeApi([
      { method: "GET", path: /\/planning\/plans\/current$/, answer: previous },
      {
        method: "GET",
        path: /\/planning\/solves\/[^/]+$/,
        answer: { run: { run_id: RUN, status: "complete" }, target_title: "Data quality analyst" },
      },
      { method: "GET", path: /\/schedules\/1$/, answer: planRoute },
      {
        method: "GET",
        path: /\/planning\/plans\/revision-preview$/,
        answer: { ...revision, completed_steps: ["step-1"] },
      },
      { method: "GET", path: /\/planning\/plans\/changes$/, answer: { new_solve_needed: false } },
      { method: "GET", path: /\/planning\/plans\/history$/, answer: [] },
      { method: "POST", path: /\/planning\/plans$/, answer: { ...previous, version: 2 } },
    ]);

    render(<PlanChapter workspaceId="workspace" />, { wrapper });
    const save = await screen.findByRole("button", { name: "Save this plan" });
    expect(
      screen.getByText(/has not subtracted completed work or costs already paid/),
    ).toBeVisible();
    await userEvent.click(screen.getByRole("checkbox", { name: /I have reviewed this route/ }));
    expect(save).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(screen.getByRole("checkbox", { name: /I understand this is a fresh/ }));
    await userEvent.click(save);
    await waitFor(() => expect(sent.some((request) => request.method === "POST")).toBe(true));
    expect(sent.find((request) => request.method === "POST")?.body).toEqual({
      expected_version: 1,
      solve_run_id: RUN,
      schedule_index: 1,
      assumptions_confirmed: true,
      full_horizon_accounting_acknowledged: true,
    });
  });

  it("labels a remaining-horizon revision and does not ask for full-horizon acknowledgment", async () => {
    window.history.replaceState({}, "", `/?solve_run_id=${RUN}&schedule_index=1`);
    const previous = {
      ...savedPlan,
      progress: { completed_steps: ["step-1"], rest_until: null, review_on: null, activity: [] },
    };
    const remaining = {
      ...planRoute,
      basis: {
        ...planRoute.basis,
        planning_start: "2027-01",
        horizon_months: 4,
        opening_cash: { minor_units: 100000, currency: "GBP" as const },
        replan: {
          from_plan_version: 1,
          completed_variants: ["step-1"],
          excluded_variants: ["step-1"],
          sunk_paid: { minor_units: 50000, currency: "GBP" as const },
          remaining_payments: [],
        },
      },
    };
    const sent = fakeApi([
      { method: "GET", path: /\/planning\/plans\/current$/, answer: previous },
      {
        method: "GET",
        path: /\/planning\/solves\/[^/]+$/,
        answer: { run: { run_id: RUN, status: "complete" }, target_title: "Data quality analyst" },
      },
      { method: "GET", path: /\/schedules\/1$/, answer: remaining },
      {
        method: "GET",
        path: /\/planning\/plans\/revision-preview$/,
        answer: {
          ...revision,
          proposed_route: remaining,
          difference: {
            ...revision.difference,
            new_basis: remaining.basis,
            same_accounting_basis: false,
            remaining_horizon_recalculated: true,
          },
        },
      },
      { method: "GET", path: /\/planning\/plans\/changes$/, answer: { new_solve_needed: false } },
      { method: "GET", path: /\/planning\/plans\/history$/, answer: [] },
      { method: "POST", path: /\/planning\/plans$/, answer: { ...previous, version: 2 } },
    ]);
    render(<PlanChapter workspaceId="workspace" />, { wrapper });
    const candidate = await screen.findByRole("region", { name: "Route to choose" });
    expect(
      within(candidate).getByText(/covers 4 remaining months from January 2027/),
    ).toBeVisible();
    expect(within(candidate).queryByText(/fresh full-horizon comparison/)).toBeNull();
    await userEvent.click(
      within(candidate).getByRole("checkbox", { name: /I have reviewed this route/ }),
    );
    await userEvent.click(within(candidate).getByRole("button", { name: "Save this plan" }));
    await waitFor(() => expect(sent.some((request) => request.method === "POST")).toBe(true));
    expect(sent.find((request) => request.method === "POST")?.body).toEqual({
      expected_version: 1,
      solve_run_id: RUN,
      schedule_index: 1,
      assumptions_confirmed: true,
    });
  });

  it("starts a remaining-month search only after confirmed actuals and payments", async () => {
    const start = londonToday().slice(0, 7);
    const current = {
      ...savedPlan,
      progress: { completed_steps: ["step-1"], activity: [] },
      route: {
        ...savedPlan.route,
        basis: { ...savedPlan.route.basis, planning_start: start },
      },
    };
    const sent = fakeApi([
      { method: "GET", path: /\/planning\/plans\/current$/, answer: current },
      { method: "GET", path: /\/planning\/checkpoint$/, answer: { inputs_version: 8 } },
      {
        method: "POST",
        path: /\/planning\/solves\/replan$/,
        answer: { run: { status: "queued" } },
      },
    ]);
    render(<PlanChapter workspaceId="workspace" />, { wrapper });
    await userEvent.click(await screen.findByText("Recalculate the months left"));
    const form = screen.getByRole("button", { name: "Search the months left" }).closest("form");
    if (!form) throw new Error("Missing remaining-month form");
    await userEvent.type(
      within(form).getByLabelText("Cash available at the start, in pounds"),
      "1,200",
    );
    await userEvent.type(
      within(form).getByLabelText("Money already paid for this plan, in pounds"),
      "0",
    );
    await userEvent.click(within(form).getByRole("button", { name: "Add a remaining payment" }));
    await userEvent.type(within(form).getByLabelText("Due date"), "2099-01-01");
    await userEvent.type(within(form).getByLabelText("Amount in pounds"), "150");
    await userEvent.click(within(form).getByRole("button", { name: "Search the months left" }));
    expect(sent.some((request) => request.method === "POST")).toBe(false);
    await userEvent.click(
      within(form).getByRole("checkbox", { name: /I have listed every remaining payment/ }),
    );
    await userEvent.click(within(form).getByRole("button", { name: "Search the months left" }));
    await waitFor(() => expect(sent.some((request) => request.method === "POST")).toBe(true));
    expect(sent.find((request) => request.method === "POST")?.body).toEqual({
      expected_inputs_version: 8,
      expected_plan_version: 1,
      target: "Data quality analyst",
      planning_start: start,
      horizon_months: 24,
      opening_cash: { currency: "GBP", minor_units: 120000 },
      sunk_paid: { currency: "GBP", minor_units: 0 },
      remaining_payments: [
        {
          variant_id: "step-1",
          due: "2099-01-01",
          amount: { currency: "GBP", minor_units: 15000 },
        },
      ],
      all_remaining_payments_confirmed: true,
      no_ongoing_steps_confirmed: true,
    });
    expect(await within(form).findByRole("link", { name: "Open Routes" })).toHaveAttribute(
      "href",
      "/w/workspace/routes?target=Data%20quality%20analyst",
    );
  });

  it("does not offer a recalculation for a recorded unfinished commitment", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/planning\/plans\/current$/,
        answer: { ...savedPlan, commitments: ["step-1"] },
      },
    ]);
    render(<PlanChapter workspaceId="workspace" />, { wrapper });
    await userEvent.click(await screen.findByText("Recalculate the months left"));
    expect(screen.getByText(/cannot carry an unfinished commitment/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Search the months left" })).toBeNull();
  });

  it("keeps changed sources visible and records progress as a new saved version", async () => {
    let completed = false;
    const next = {
      ...savedPlan,
      version: 2,
      progress: { completed_steps: ["step-1"], rest_until: null, review_on: null, activity: [] },
    };
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/planning\/plans\/current$/,
        answer: () => (completed ? next : savedPlan),
      },
      {
        method: "GET",
        path: /\/planning\/plans\/changes$/,
        answer: {
          plan_version: 1,
          profile: true,
          planning_inputs: false,
          capability: false,
          target_matrix: false,
          option_pack: false,
          possibly_affected_steps: ["step-1"],
          new_solve_needed: true,
        },
      },
      {
        method: "GET",
        path: /\/planning\/plans\/history$/,
        answer: [
          {
            version: 1,
            plan_id: savedPlan.plan_id,
            target_title: savedPlan.target_title,
            selected_at: savedPlan.selected_at,
            last_activity_at: null,
            solve_run_id: RUN,
            schedule_index: 1,
            completed_steps: 0,
          },
        ],
      },
      { method: "GET", path: /\/planning\/plans\/1$/, answer: savedPlan },
      {
        method: "POST",
        path: /\/planning\/plans\/progress$/,
        answer: () => {
          completed = true;
          return next;
        },
      },
    ]);

    render(<PlanChapter workspaceId="workspace" />, { wrapper });
    expect(await screen.findByText("Some answers or sources changed")).toBeVisible();
    expect(screen.getByText(/Data course may need review/)).toBeVisible();
    await userEvent.click(screen.getByText("Saved plan versions"));
    await userEvent.click(screen.getByRole("button", { name: /Version 1: Data quality analyst/ }));
    await waitFor(() =>
      expect(sent.some((request) => request.path.endsWith("/plans/1"))).toBe(true),
    );
    await userEvent.click(screen.getByRole("button", { name: "Report step complete" }));
    await waitFor(() =>
      expect(
        sent.some(
          (request) =>
            request.path.endsWith("/plans/progress") &&
            JSON.stringify(request.body) ===
              JSON.stringify({ expected_version: 1, kind: "step_completed", variant_id: "step-1" }),
        ),
      ).toBe(true),
    );
    const overview = await screen.findByRole("region", { name: "Chosen plan overview" });
    await waitFor(() =>
      expect(within(overview).getByText(/Planning progress: 1 of 1/)).toBeVisible(),
    );
  });
});
