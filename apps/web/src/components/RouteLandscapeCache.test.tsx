import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { RouteDetail } from "@/generated/api";
import { useCachedRouteLandscapes } from "@/lib/routeQueries";
import { fakeApi } from "@/test/fakeApi";
import { p01Checkpoint, p01Profile } from "@/test/p01DesignData";
import { lifecycleComparison, lifecycleSolve } from "@/test/routeLifecycleData";
import { completePlanningRoute } from "@/test/routeStateData";
import { EvidenceProvider } from "./EvidenceDrawer";
import { RouteExplorer } from "./RouteExplorer";
import { RoutesChapter } from "./RoutesChapter";

const workspace = "w-landscape-cache";
const titles = ["Reporting role", "Data role", "Regulated role", "Unopened role"];
const key = (runId: string) => ["ws", workspace, "routes", runId] as const;

function store(queries: QueryClient, title: string, routes: RouteDetail[], runId: string) {
  const solve = {
    ...lifecycleSolve(routes[0] ?? completePlanningRoute, runId),
    target_title: title,
  };
  queries.setQueryData(["ws", workspace, "routes", "latest", title], { latest: solve, kept: null });
  queries.setQueryData([...key(runId), "comparison"], {
    ...lifecycleComparison(),
    schedules_total: routes.length,
    ...(routes.length === 0
      ? {
          lead: "no_route_in_bounded_model",
          outcome: "no_route_in_bounded_model",
          code: "NO_ROUTE_IN_BOUNDED_MODEL",
        }
      : {}),
  });
  queries.setQueryData([...key(runId), "schedules", { limit: 6 }], {
    items: routes.map((route) => route.schedule),
    total: routes.length,
    retained: routes.length,
    next_cursor: null,
  });
  for (const route of routes)
    queries.setQueryData([...key(runId), "schedules", route.schedule.index], route);
}

function CachedLandscape() {
  const cached = useCachedRouteLandscapes(workspace, titles);
  return (
    <RouteExplorer
      targets={titles.map((title) => ({ id: title, title, routes: [], ...cached[title] }))}
      startLabel="Today"
    />
  );
}

function show(queries: QueryClient) {
  return render(
    <QueryClientProvider client={queries}>
      <CachedLandscape />
    </QueryClientProvider>,
  );
}

describe("[STATE-07] previously inspected destinations reuse their route cache", () => {
  it("keeps complete empty results unresolved until the checker confirms no route", async () => {
    fakeApi([]);
    const queries = new QueryClient();
    store(queries, "Regulated role", [], "regulated");
    queries.setQueryData([...key("regulated"), "comparison"], {
      ...lifecycleComparison(),
      lead: "unresolved",
      outcome: "unresolved",
      schedules_total: 0,
      readiness_unknown: 1,
    });
    show(queries);
    const destination = screen.getByRole("button", { name: /Regulated role 0 routes/ });
    expect(destination).toHaveAttribute("data-route-state", "unresolved");
    expect(destination).toHaveTextContent(
      "Route support not established; planning facts still needed",
    );
    expect(
      screen.queryByText("No supported route found in this monthly model"),
    ).not.toBeInTheDocument();
  });
  it("keeps the first target supported in the production overview after opening another cached target", async () => {
    const sent = fakeApi([]);
    const queries = new QueryClient({
      defaultOptions: { queries: { staleTime: Infinity, retry: false } },
    });
    const checkpointTarget = p01Checkpoint.targets[0];
    if (!checkpointTarget) throw new Error("Missing checkpoint fixture target");
    queries.setQueryData(["ws", workspace, "planning", "checkpoint"], {
      ...p01Checkpoint,
      inputs_version: 1,
      targets: titles.slice(0, 2).map((title) => ({ ...checkpointTarget, target_title: title })),
    });
    queries.setQueryData(["ws", workspace, "profile"], p01Profile);
    queries.setQueryData(["ws", workspace, "planning", "plans", "current"], null);
    for (const [index, title] of titles.slice(0, 2).entries()) {
      const runId = `run-${index}`;
      store(queries, title, [completePlanningRoute], runId);
      queries.setQueryData([...key(runId), "schedules", { limit: 20, rerank: false }], {
        items: [completePlanningRoute.schedule],
        total: 1,
        retained: 1,
        next_cursor: null,
      });
    }
    render(
      <QueryClientProvider client={queries}>
        <EvidenceProvider>
          <RoutesChapter workspaceId={workspace} />
        </EvidenceProvider>
      </QueryClientProvider>,
    );
    const archive = () => within(screen.getByRole("region", { name: "Route archive" }));
    await userEvent.click(archive().getByRole("button", { name: /Route 1/ }));
    expect(archive().getByRole("button", { name: /Route 1/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    await userEvent.click(screen.getByRole("button", { name: /Data role 1 route/ }));
    expect(archive().getByRole("button", { name: /Route 1/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    await userEvent.click(screen.getByRole("button", { name: /Reporting role 1 route/ }));
    expect(archive().getByRole("button", { name: /Route 1/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    expect(screen.getByRole("button", { name: /Reporting role 1 route/ })).toHaveAttribute(
      "data-route-state",
      "complete",
    );
    expect(screen.getByRole("button", { name: /Data role 1 route/ })).toHaveAttribute(
      "data-route-state",
      "complete",
    );
    expect(sent).toHaveLength(0);
  });
  it("keeps supported, partial and unsupported destinations visible while another target is inspected without fetching", async () => {
    const sent = fakeApi([]);
    const queries = new QueryClient();
    store(queries, titles[0] ?? "", [completePlanningRoute], "reporting");
    store(
      queries,
      titles[1] ?? "",
      [
        {
          ...completePlanningRoute,
          steps: completePlanningRoute.steps.map((step) => ({ ...step, weekly_hours: null })),
        },
      ],
      "data",
    );
    store(queries, titles[2] ?? "", [], "regulated");
    const { container } = show(queries);
    const reporting = screen.getByRole("button", { name: /Reporting role 1 route/ });
    const position = reporting.getAttribute("style");
    expect(reporting).toHaveAttribute("data-route-state", "complete");
    expect(screen.getByRole("button", { name: /Data role 1 route/ })).toHaveAttribute(
      "data-route-state",
      "partial",
    );
    expect(screen.getByRole("button", { name: /Regulated role 0 routes/ })).toHaveAttribute(
      "data-route-state",
      "unsupported",
    );
    expect(
      screen.getByRole("button", { name: /Unopened role Route count not checked/ }),
    ).toHaveAttribute("data-route-state", "unloaded");
    await userEvent.click(screen.getByRole("button", { name: /Data role 1 route/ }));
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    expect(screen.getByRole("button", { name: /Reporting role 1 route/ })).toHaveAttribute(
      "data-route-state",
      "complete",
    );
    expect(
      screen.getByRole("button", { name: /Reporting role 1 route/ }).getAttribute("style"),
    ).toBe(position);
    expect(container.querySelector('g[data-route-state="unsupported"]')).toBeInTheDocument();
    expect(sent).toHaveLength(0);
  });

  it("marks invalidated cached results stale without changing their stored steps or issuing a background fetch", async () => {
    const sent = fakeApi([]);
    const queries = new QueryClient();
    store(queries, "Reporting role", [completePlanningRoute], "reporting");
    show(queries);
    await act(() => queries.invalidateQueries({ queryKey: [...key("reporting"), "comparison"] }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Reporting role 1 route/ })).toHaveAttribute(
        "data-route-state",
        "stale",
      ),
    );
    await userEvent.click(screen.getByRole("button", { name: /Reporting role 1 route/ }));
    await userEvent.click(screen.getByRole("button", { name: "Route 1 Selected" }));
    expect(screen.getByRole("button", { name: /Reporting practice/ })).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("Saved results need updating");
    expect(sent).toHaveLength(0);
    await act(() => {
      queries.setQueryData([...key("reporting"), "comparison"], lifecycleComparison());
    });
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("Planning information complete"),
    );
  });

  it("marks an inactive target stale when cached planning inputs advance before route invalidation arrives", async () => {
    const sent = fakeApi([]);
    const queries = new QueryClient();
    store(queries, "Reporting role", [completePlanningRoute], "reporting");
    queries.setQueryData(["ws", workspace, "planning", "checkpoint"], {
      ...p01Checkpoint,
      inputs_version: 1,
    });
    show(queries);
    expect(screen.getByRole("button", { name: /Reporting role 1 route/ })).toHaveAttribute(
      "data-route-state",
      "complete",
    );
    await act(() => {
      queries.setQueryData(["ws", workspace, "planning", "checkpoint"], {
        ...p01Checkpoint,
        inputs_version: 2,
      });
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Reporting role 1 route/ })).toHaveAttribute(
        "data-route-state",
        "stale",
      ),
    );
    expect(sent).toHaveLength(0);
  });

  it("reads only six unfiltered cached schedules and reacts to their replacement and removal", async () => {
    const sent = fakeApi([]);
    const queries = new QueryClient();
    const routes = Array.from({ length: 8 }, (_, index) => ({
      ...completePlanningRoute,
      schedule: { ...completePlanningRoute.schedule, index },
    }));
    store(queries, "Reporting role", routes, "reporting");
    queries.setQueryData([...key("reporting"), "schedules", { limit: 20, family_id: "hidden" }], {
      items: [],
      total: 0,
      retained: 0,
      next_cursor: null,
    });
    show(queries);
    expect(screen.getByRole("button", { name: /Reporting role 8 routes/ })).toHaveTextContent(
      "6 route summaries loaded",
    );
    await act(() => {
      queries.setQueryData([...key("reporting"), "comparison"], {
        ...lifecycleComparison(),
        schedules_total: 8,
        changed_since: { ...lifecycleComparison().changed_since, option_pack: true },
      });
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Reporting role 8 routes/ })).toHaveAttribute(
        "data-route-state",
        "stale",
      ),
    );
    await act(() => {
      queries.removeQueries({ queryKey: ["ws", workspace, "routes", "latest", "Reporting role"] });
    });
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /Reporting role Route count not checked/ }),
      ).toHaveAttribute("data-route-state", "unloaded"),
    );
    expect(sent).toHaveLength(0);
  });
});
