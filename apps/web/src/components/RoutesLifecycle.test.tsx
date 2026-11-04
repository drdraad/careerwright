import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { PlanningInputsOut, RouteDetail, SolveOut } from "@/generated/api";
import { useWritePlanningInputs } from "@/lib/queries";
import { fakeApi } from "@/test/fakeApi";
import { p01Checkpoint, p01Profile } from "@/test/p01DesignData";
import {
  lifecycleComparison,
  lifecycleRunId,
  lifecycleSolve,
  lifecycleTarget,
} from "@/test/routeLifecycleData";
import { completePlanningRoute } from "@/test/routeStateData";
import { EvidenceProvider } from "./EvidenceDrawer";
import { RoutesChapter } from "./RoutesChapter";

const workspaceId = "w-route-lifecycle";
const refreshedRunId = "90000000-0000-4000-8000-000000000002";

afterEach(() => vi.useRealTimers());

function AcceptHours() {
  const write = useWritePlanningInputs(workspaceId);
  return (
    <button
      type="button"
      onClick={() =>
        write.mutate({
          expected_version: 1,
          inputs: { offering_figures: [{ offering_id: "fictional-course", weekly_hours: 8 }] },
        })
      }
    >
      Save stated hours
    </button>
  );
}

function show(initialRoute = completePlanningRoute) {
  const comparison = lifecycleComparison(initialRoute);
  const first = lifecycleSolve(initialRoute);
  const target = p01Checkpoint.targets[0];
  if (!target) throw new Error("The checkpoint fixture needs a target.");
  const checkpoint = {
    ...p01Checkpoint,
    inputs_version: 1,
    targets: [
      {
        ...target,
        target_title: lifecycleTarget,
        label: initialRoute.label,
        options: [
          {
            variant_id: "fictional-course",
            offering_id: "fictional-course",
            concept_id: "fictional-course",
            plan_id: null,
            review_states: ["proposed" as const],
            as_of: "2026-11-04",
            added_by_person: false,
            missing: [],
            supplied: [],
            stated_intakes: [],
            entry_requirements: [],
            entry_requirements_met: null,
            entry_expected: false,
            eligibility_conditions: [],
            age_rules: [],
            outcomes: [],
            left_out: false,
          },
        ],
      },
    ],
  };
  const state = {
    checkpoint,
    comparison,
    runs: [first.run],
    solves: new Map<string, SolveOut>([[lifecycleRunId, first]]),
    routes: new Map<string, RouteDetail>([[lifecycleRunId, initialRoute]]),
  };
  const sent = fakeApi([
    { method: "GET", path: /\/planning\/checkpoint$/, answer: () => state.checkpoint },
    {
      method: "GET",
      path: /\/profile$/,
      answer: {
        ...p01Profile,
        document: {
          ...p01Profile.document,
          target_titles: { state: "provided", value: [lifecycleTarget], source_ref_id: null },
        },
      },
    },
    { method: "GET", path: /\/runs$/, answer: () => ({ items: state.runs, next_cursor: null }) },
    {
      method: "GET",
      path: /\/solves\/[^/]+$/,
      answer: ({ path }) => state.solves.get(path.split("/").at(-1) ?? ""),
    },
    {
      method: "GET",
      path: /\/comparison$/,
      answer: ({ path }) =>
        path.includes(refreshedRunId)
          ? lifecycleComparison(state.routes.get(refreshedRunId))
          : state.comparison,
    },
    {
      method: "GET",
      path: /\/schedules$/,
      answer: ({ path }) => ({
        rank_scope: "recorded",
        layers_exact: true,
        retained: 1,
        total: 1,
        items: [
          state.routes.get(path.includes(refreshedRunId) ? refreshedRunId : lifecycleRunId)
            ?.schedule,
        ],
        next_cursor: null,
        pinned: [],
      }),
    },
    {
      method: "GET",
      path: /\/schedules\/0$/,
      answer: ({ path }) =>
        state.routes.get(path.includes(refreshedRunId) ? refreshedRunId : lifecycleRunId),
    },
    {
      method: "PUT",
      path: /\/planning\/inputs$/,
      answer: ({ body }) => {
        state.comparison.changed_since.planning_inputs = true;
        state.checkpoint.inputs_version = 2;
        const value = body as { inputs: PlanningInputsOut["inputs"] };
        return {
          version: 2,
          inputs: value.inputs,
          created_by: null,
          created_at: "2026-11-04T12:01:00Z",
          profile_version: 1,
          direct_spend_cap: p01Checkpoint.direct_spend_cap,
          monthly_payment_cap: p01Checkpoint.monthly_payment_cap,
          needs: [],
          synthetic: true,
          data_mode: "demo",
        } satisfies PlanningInputsOut;
      },
    },
  ]);
  const queries = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  });
  render(
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <AcceptHours />
        <RoutesChapter workspaceId={workspaceId} />
      </EvidenceProvider>
    </QueryClientProvider>,
  );
  return { state, sent, queries };
}

const overview = () =>
  within(screen.getByRole("region", { name: "Explore possible destinations" }));

describe("[STATE-07][API-02][VIS-1] the route landscape follows accepted server information", () => {
  it("keeps old routes stale after an accepted answer, then updates the selected step after the server finishes a newer solve", async () => {
    const { state, sent, queries } = show();
    const archive = await screen.findByRole("region", { name: "Route archive" });
    await waitFor(() =>
      expect(
        overview().getByRole("button", {
          name: /Fictional reporting role.*Planning information complete/,
        }),
      ).toBeVisible(),
    );
    await userEvent.click(within(archive).getByRole("button", { name: /Route 1/ }));
    await userEvent.click(screen.getByRole("button", { name: /Reporting practice/ }));
    const inspector = document.querySelector(".route-journey-inspector");
    if (!(inspector instanceof HTMLElement))
      throw new Error("The selected step needs an inspector.");
    expect(within(inspector).getByText(/6 hours a week/)).toBeVisible();

    await userEvent.click(screen.getByRole("button", { name: "Save stated hours" }));
    await screen.findByText(/Your answers changed after this search/);
    expect(screen.getByRole("region", { name: "Your possible routes" })).toHaveAttribute(
      "data-route-state",
      "stale",
    );
    expect(
      screen.queryByRole("link", { name: "Choose this route in Plan" }),
    ).not.toBeInTheDocument();
    expect(within(inspector).getByText(/6 hours a week/)).toBeVisible();
    expect(sent.filter((request) => request.method !== "GET")).toEqual([
      expect.objectContaining({
        method: "PUT",
        path: `/v1/workspaces/${workspaceId}/planning/inputs`,
      }),
    ]);

    const updated = structuredClone(completePlanningRoute);
    const step = updated.steps[0];
    if (!step) throw new Error("The fictional route needs a learning step.");
    step.weekly_hours = 8;
    step.supplied = ["weekly_hours"];
    step.qualified_by.push("supplied_figures");
    updated.schedule.qualifications.push("supplied_figures");
    state.routes.set(refreshedRunId, updated);
    const next = lifecycleSolve(updated, refreshedRunId);
    next.inputs_version = 2;
    next.input_version = "fictional-monthly-input-2";
    if (next.result) next.result.input_version = next.input_version;
    state.solves.set(refreshedRunId, {
      ...next,
      run: { ...next.run, status: "running", finished_at: null },
      result: null,
      stage: "searching",
    });
    state.runs = [state.solves.get(refreshedRunId)?.run ?? next.run, ...state.runs];
    await act(async () => {
      await queries.invalidateQueries({ queryKey: ["ws", workspaceId] });
    });
    await waitFor(() =>
      expect(screen.getByRole("region", { name: "Your possible routes" })).toHaveAttribute(
        "data-route-state",
        "pending",
      ),
    );
    expect(within(inspector).getByText(/6 hours a week/)).toBeVisible();

    state.solves.set(refreshedRunId, next);
    state.runs = [next.run, ...state.runs.slice(1)];
    await act(async () => {
      await queries.invalidateQueries({ queryKey: ["ws", workspaceId] });
    });
    await waitFor(() =>
      expect(screen.getByRole("region", { name: "Your possible routes" })).toHaveAttribute(
        "data-route-state",
        "complete",
      ),
    );
    const currentInspector = document.querySelector(".route-journey-inspector");
    if (!(currentInspector instanceof HTMLElement))
      throw new Error("The selected step needs an inspector after refresh.");
    expect(within(currentInspector).getByText(/8 hours a week/)).toBeVisible();
    expect(within(currentInspector).queryByText(/6 hours a week/)).not.toBeInTheDocument();
    expect(
      sent.some((request) => request.method === "POST" && request.path.endsWith("/solves")),
    ).toBe(false);
  });

  it("keeps an old complete route explicitly stale when its option is removed", async () => {
    const { state, queries, sent } = show();
    await waitFor(() =>
      expect(
        overview().getByRole("button", {
          name: /Fictional reporting role.*Planning information complete/,
        }),
      ).toBeVisible(),
    );
    const target = state.checkpoint.targets[0];
    if (!target) throw new Error("The route lifecycle fixture needs a target.");
    target.options = [];
    state.comparison.changed_since.option_pack = true;
    await act(async () => {
      await queries.invalidateQueries({ queryKey: ["ws", workspaceId] });
    });
    expect(
      await screen.findByText(/The target definition or option research changed after this search/),
    ).toBeVisible();
    expect(
      overview().getByRole("button", {
        name: /Fictional reporting role.*Saved results need updating/,
      }),
    ).toHaveAttribute("data-route-state", "stale");
    expect(
      screen.queryByText("No supported route found in this monthly model"),
    ).not.toBeInTheDocument();
    expect(sent.every((request) => request.method === "GET")).toBe(true);
  });

  it("marks retained geometry stale when research expires without a save or workspace event", async () => {
    vi.useFakeTimers();
    const { state, sent } = show();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(
      overview().getByRole("button", {
        name: /Fictional reporting role.*Planning information complete/,
      }),
    ).toBeVisible();
    state.comparison.changed_since.option_pack = true;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60_000);
    });
    expect(
      overview().getByRole("button", {
        name: /Fictional reporting role.*Saved results need updating/,
      }),
    ).toHaveAttribute("data-route-state", "stale");
    expect(
      screen.getByText(/The target definition or option research changed after this search/),
    ).toBeVisible();
    expect(sent.filter((request) => request.path.endsWith("/comparison"))).toHaveLength(2);
    expect(sent.every((request) => request.method === "GET")).toBe(true);
  });

  it("shows a valid zero-step direct route without inventing training or missing payments", async () => {
    const direct = structuredClone(completePlanningRoute);
    direct.steps = [];
    direct.gates = [];
    direct.milestones = [{ kind: "readiness", month: "2027-01", months_to_readiness: 0 }];
    direct.schedule = {
      ...direct.schedule,
      route: [],
      conditions: [],
      qualifications: ["synthetic", "provisional_matrix"],
      months_to_readiness: 0,
      readiness_month: "2027-01",
      objective_cost: { minor_units: 0, currency: "GBP" },
      direct_cost: { minor_units: 0, currency: "GBP" },
    };
    direct.costs = {
      ...direct.costs,
      direct_cost: { minor_units: 0, currency: "GBP" },
      peak_monthly_payment: { minor_units: 0, currency: "GBP" },
    };
    show(direct);
    await waitFor(() =>
      expect(
        overview().getByRole("button", {
          name: /Fictional reporting role.*Planning information complete/,
        }),
      ).toBeVisible(),
    );
    const archive = screen.getByRole("region", { name: "Route archive" });
    await userEvent.click(within(archive).getByRole("button", { name: /Route 1.*£0/ }));
    await userEvent.click(screen.getByText("Read route steps and dependencies"));
    expect(
      screen.getByText(
        "No additional training or job steps in this route. Check its readiness conditions.",
      ),
    ).toBeVisible();
    expect(screen.queryByText("Payments unknown")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Reporting practice/ })).not.toBeInTheDocument();
  });
});
