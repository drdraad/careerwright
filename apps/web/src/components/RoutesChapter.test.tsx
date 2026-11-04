import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fakeApi } from "@/test/fakeApi";
import { routeDetailFixture } from "@/test/routeDetailData";
import { RoutesChapter } from "./RoutesChapter";

vi.mock("./RouteDetailView", () => ({ RouteDetailView: () => <div>Route details</div> }));

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
);

const checkpoint = {
  inputs_version: 4,
  targets: [{ target_title: "Nurse", options: [], schemes: [] }],
  needs: [],
};

afterEach(() => window.history.replaceState({}, "", "/"));

describe("[API-05][OPTN-13] Routes starts from the review checkpoint", () => {
  it("opens the plan's target when returning from a remaining-month search", async () => {
    window.history.replaceState({}, "", "/?target=Analyst");
    fakeApi([
      {
        method: "GET",
        path: /\/planning\/checkpoint$/,
        answer: {
          ...checkpoint,
          targets: [checkpoint.targets[0], { target_title: "Analyst", options: [], schemes: [] }],
        },
      },
      { method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } },
    ]);
    render(<RoutesChapter workspaceId="w-target" />, { wrapper });
    expect(await screen.findByRole("combobox", { name: "Destination" })).toHaveValue("Analyst");
  });

  it("clears the previous target's family filter when the destination changes", async () => {
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/planning\/checkpoint$/,
        answer: {
          ...checkpoint,
          targets: [
            { target_title: "Nurse", options: [], schemes: [] },
            { target_title: "Analyst", options: [], schemes: [] },
          ],
        },
      },
      {
        method: "GET",
        path: /\/runs$/,
        answer: {
          items: [
            { run_id: "solve-nurse", kind: "route_solve", status: "complete" },
            { run_id: "solve-analyst", kind: "route_solve", status: "complete" },
          ],
          next_cursor: null,
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/solve-(nurse|analyst)$/,
        answer: (request) => ({
          run: { run_id: request.path.split("/").at(-1), status: "complete" },
          target_title: request.path.endsWith("solve-nurse") ? "Nurse" : "Analyst",
        }),
      },
      {
        method: "GET",
        path: /\/comparison$/,
        answer: {
          lead: "best_trade_offs_found",
          coverage: "complete",
          changed_since: { planning_inputs: false, profile: false, capability: false },
          basis: {
            objective_basis: "direct_spending",
            horizon_months: 24,
            planning_start: "2026-11",
          },
          label: { dated: "2026-11-01" },
          limits: {},
          instance: { variants: 1, concepts: 1, months: 24 },
          schedules_total: 1,
          points: [],
          families: [
            { family_id: "nurse-family", best_schedule: 0, schedule_count: 1, best_layer: 1 },
          ],
          families_shown: 1,
          families_total: 1,
          blocking_inputs: [],
          starting_violations: [],
          longer_than_model: [],
          beyond_horizon: [],
          set_aside: [],
        },
      },
      {
        method: "GET",
        path: /\/schedules$/,
        answer: { items: [], total: 0, retained: 0, next_cursor: null },
      },
    ]);
    render(<RoutesChapter workspaceId="w-two" />, { wrapper });
    await userEvent.click(await screen.findByText("Filter this view"));
    await userEvent.selectOptions(screen.getByLabelText("Similar steps"), "nurse-family");
    await waitFor(() =>
      expect(
        sent.some(
          (request) =>
            request.path.includes("solve-nurse/schedules") &&
            request.query.includes("family_id=nurse-family"),
        ),
      ).toBe(true),
    );
    await userEvent.click(screen.getByText("Change comparison"));
    await userEvent.selectOptions(screen.getByLabelText("Destination"), "Analyst");
    await waitFor(() =>
      expect(
        sent.some(
          (request) =>
            request.path.includes("solve-analyst/schedules") &&
            !request.query.includes("family_id="),
        ),
      ).toBe(true),
    );
  });

  it("offers one next step when there is no target", async () => {
    fakeApi([
      { method: "GET", path: /\/planning\/checkpoint$/, answer: { ...checkpoint, targets: [] } },
      { method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } },
    ]);

    render(<RoutesChapter workspaceId="w-1" />, { wrapper });

    expect(await screen.findByText(/Choose a target in You/)).toBeVisible();
    expect(screen.getByRole("link", { name: "Open You" })).toHaveAttribute("href", "/w/w-1/you");
    expect(screen.queryByRole("button", { name: "Find routes" })).not.toBeInTheDocument();
  });

  it("names a blocking input and directs the person to where they can give it", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/planning\/checkpoint$/,
        answer: {
          ...checkpoint,
          needs: [{ input: "direct_spend_cap", effect: "blocks_a_solve" }],
        },
      },
      { method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } },
    ]);

    render(<RoutesChapter workspaceId="w-2" />, { wrapper });

    expect(await screen.findByText("Total spending limit")).toBeVisible();
    expect(screen.getByRole("link", { name: "Open You" })).toHaveAttribute("href", "/w/w-2/you");
    expect(screen.getByRole("button", { name: "Find routes" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });

  it("keeps a target without an option catalogue from starting an invalid search", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/planning\/checkpoint$/,
        answer: {
          ...checkpoint,
          targets: [{ target_title: "AI safety evaluator", label: null, options: [], schemes: [] }],
        },
      },
      { method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } },
    ]);
    render(<RoutesChapter workspaceId="w-unsupported" />, { wrapper });
    expect(await screen.findByText(/no option catalogue for this target yet/)).toBeVisible();
    expect(screen.getByRole("link", { name: "Options" })).toHaveAttribute(
      "href",
      "/w/w-unsupported/options",
    );
    expect(screen.getByRole("button", { name: "Find routes" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });

  it("shows the solver's comparison and filters its archive without changing recorded ranks", async () => {
    const sent = fakeApi([
      { method: "GET", path: /\/planning\/checkpoint$/, answer: checkpoint },
      {
        method: "GET",
        path: /\/runs$/,
        answer: {
          items: [{ run_id: "solve-1", kind: "route_solve", status: "complete" }],
          next_cursor: null,
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/solve-1$/,
        answer: { run: { run_id: "solve-1", status: "complete" }, target_title: "Nurse" },
      },
      {
        method: "GET",
        path: /\/comparison$/,
        answer: {
          lead: "best_trade_offs_found",
          coverage: "complete",
          changed_since: { planning_inputs: false, profile: false, capability: false },
          basis: {
            objective_basis: "economic",
            horizon_months: 24,
            planning_start: "2026-11",
            currency: "GBP",
            synthetic: true,
          },
          label: { dated: "2026-11-01" },
          limits: {
            max_actions: 12,
            max_starts_per_action: 2,
            max_months: 24,
            max_states: 50000,
            wall_seconds: 30,
          },
          instance: { variants: 3, concepts: 2, months: 24 },
          schedules_total: 1,
          points_shown: 1,
          points_total: 1,
          points: [
            {
              point_id: 1,
              months_to_readiness: 6,
              objective_cost: { minor_units: 200000, currency: "GBP" },
              layer: 1,
              schedule_count: 1,
              schedules: [0],
            },
          ],
          families: [],
          blocking_inputs: [],
          starting_violations: [],
          longer_than_model: [],
          beyond_horizon: [],
          set_aside: [],
        },
      },
      {
        method: "GET",
        path: /\/schedules$/,
        answer: {
          retained: 1,
          total: 1,
          next_cursor: null,
          items: [
            {
              index: 0,
              layer: 1,
              view_layer: null,
              months_to_readiness: 6,
              readiness_month: "2027-05",
              objective_cost: { minor_units: 200000, currency: "GBP" },
              verdict: "affordable_and_feasible",
              conditions: [],
              qualifications: ["proposed_records", "supplied_figures"],
            },
          ],
        },
      },
      {
        method: "GET",
        path: /\/schedules\/0$/,
        answer: { ...routeDetailFixture, schedule: { ...routeDetailFixture.schedule, index: 0 } },
      },
    ]);

    render(<RoutesChapter workspaceId="w-3" />, { wrapper });
    await userEvent.click(await screen.findByText("About this search and its assumptions"));
    expect(screen.getByText("Best trade-offs found")).toBeVisible();
    expect(screen.getByRole("button", { name: /Route 1/ })).toHaveTextContent("£2,000");
    await userEvent.click(screen.getByText("Route 1: conditions and assumptions"));
    expect(screen.getByText("Uses a figure you supplied that has not been checked.")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: /Route 1/ }));
    expect(await screen.findByRole("link", { name: "Choose this route in Plan" })).toHaveAttribute(
      "href",
      "/w/w-3/plan?solve_run_id=solve-1&schedule_index=0",
    );
    await userEvent.click(screen.getByText("Filter this view"));
    await userEvent.clear(screen.getByRole("spinbutton", { name: "Exact maximum months" }));
    await userEvent.type(screen.getByRole("spinbutton", { name: "Exact maximum months" }), "8");

    await waitFor(() =>
      expect(
        sent.some(
          (request) =>
            request.path.endsWith("/schedules") && request.query.includes("max_months=8"),
        ),
      ).toBe(true),
    );
    await userEvent.type(
      screen.getByRole("textbox", { name: "Exact maximum cost in pounds" }),
      "0.29",
    );
    await waitFor(() =>
      expect(
        sent.some(
          (request) =>
            request.path.endsWith("/schedules") && request.query.includes("max_cost_minor=29"),
        ),
      ).toBe(true),
    );
    expect(screen.getByText(/Recorded ranks do not change when you filter/)).toBeVisible();
  });

  it.each([
    ["capability", /Your skill evidence changed after this search/],
    ["target_matrix", /The target definition or option research changed after this search/],
    ["option_pack", /The target definition or option research changed after this search/],
  ])(
    "keeps a stale route reviewable but prevents choosing it after %s changes",
    async (field, notice) => {
      fakeApi([
        { method: "GET", path: /\/planning\/checkpoint$/, answer: checkpoint },
        {
          method: "GET",
          path: /\/runs$/,
          answer: {
            items: [{ run_id: "solve-1", kind: "route_solve", status: "complete" }],
            next_cursor: null,
          },
        },
        {
          method: "GET",
          path: /\/planning\/solves\/solve-1$/,
          answer: { run: { run_id: "solve-1", status: "complete" }, target_title: "Nurse" },
        },
        {
          method: "GET",
          path: /\/comparison$/,
          answer: {
            lead: "best_trade_offs_found",
            coverage: "complete",
            changed_since: {
              planning_inputs: false,
              profile: false,
              capability: false,
              [field]: true,
            },
            basis: {
              objective_basis: "direct_spending",
              horizon_months: 24,
              planning_start: "2026-11",
            },
            label: { dated: "2026-11-01" },
            limits: {},
            instance: { variants: 1, concepts: 1, months: 24 },
            schedules_total: 1,
            points: [],
            families: [],
            blocking_inputs: [],
            starting_violations: [],
            longer_than_model: [],
            beyond_horizon: [],
            set_aside: [],
          },
        },
        {
          method: "GET",
          path: /\/schedules$/,
          answer: {
            items: [
              {
                index: 0,
                layer: 1,
                months_to_readiness: 0,
                readiness_month: "2026-11",
                objective_cost: { minor_units: 0, currency: "GBP" },
                verdict: "affordable_and_feasible",
                conditions: [],
                qualifications: [],
              },
            ],
            total: 1,
            retained: 1,
            next_cursor: null,
          },
        },
        {
          method: "GET",
          path: /\/schedules\/0$/,
          answer: { ...routeDetailFixture, schedule: { ...routeDetailFixture.schedule, index: 0 } },
        },
      ]);
      render(<RoutesChapter workspaceId="w-stale" />, { wrapper });
      expect(await screen.findByText(notice)).toBeVisible();
      await userEvent.click(screen.getByRole("button", { name: /Route 1/ }));
      await userEvent.click(await screen.findByText("Full breakdown for Route 1"));
      expect(await screen.findByText("Route details")).toBeVisible();
      expect(screen.queryByRole("link", { name: "Choose this route in Plan" })).toBeNull();
      expect(screen.getByRole("button", { name: "Search again" })).toBeVisible();
    },
  );

  it("explains the evidence gap when a remaining solve finds no route after reported completion", async () => {
    fakeApi([
      { method: "GET", path: /\/planning\/checkpoint$/, answer: checkpoint },
      {
        method: "GET",
        path: /\/runs$/,
        answer: {
          items: [{ run_id: "solve-1", kind: "route_solve", status: "complete" }],
          next_cursor: null,
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/solve-1$/,
        answer: { run: { run_id: "solve-1", status: "complete" }, target_title: "Nurse" },
      },
      {
        method: "GET",
        path: /\/comparison$/,
        answer: {
          lead: "no_route_in_bounded_model",
          coverage: "complete",
          changed_since: { planning_inputs: false, profile: false, capability: false },
          basis: {
            objective_basis: "direct_spending",
            horizon_months: 4,
            planning_start: "2027-01",
            currency: "GBP",
            synthetic: true,
            replan: { completed_variants: ["step-1"], remaining_payments: [] },
          },
          label: { dated: "2026-11-01" },
          limits: {},
          instance: { variants: 0, concepts: 0, months: 4 },
          schedules_total: 0,
          points_shown: 0,
          points_total: 0,
          points: [],
          families: [],
          readiness_unknown: 1,
          feasible_without_milestone: 0,
          blocking_inputs: [],
          starting_violations: [],
          longer_than_model: [],
          beyond_horizon: [],
          set_aside: [],
        },
      },
      { method: "GET", path: /\/schedules$/, answer: { items: [], total: 0, retained: 0 } },
    ]);
    render(<RoutesChapter workspaceId="w-4" />, { wrapper });
    const result = await screen.findByRole("region", { name: "Route search result" });
    expect(result).toHaveTextContent(/has not checked what it taught you/);
    expect(within(result).getByRole("link", { name: "Skills" })).toHaveAttribute(
      "href",
      "/w/w-4/skills",
    );
    expect(within(result).getByRole("link", { name: "Open Skills" })).toHaveAttribute(
      "href",
      "/w/w-4/skills",
    );
  });
});
