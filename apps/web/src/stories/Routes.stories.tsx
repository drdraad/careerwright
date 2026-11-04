// Synthetic route-search states for reviewing the Routes chapter in the reading panel.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { EvidenceDrawer, EvidenceProvider } from "@/components/EvidenceDrawer";
import { RouteDetailView } from "@/components/RouteDetailView";
import { RoutesChapter } from "@/components/RoutesChapter";
import { fakeApi, type Route } from "@/test/fakeApi";
import { routeDetailFixture } from "@/test/routeDetailData";

const meta: Meta = { title: "Routes", parameters: { surface: "reading" } };
export default meta;
type Story = StoryObj;

const checkpoint = {
  inputs_version: 4,
  targets: [{ target_title: "Data quality analyst", options: [], schemes: [] }],
  needs: [],
};
const noRuns: Route = { method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } };
const completeSolve: Route = {
  method: "GET",
  path: /\/planning\/solves\/solve-story$/,
  answer: {
    run: { run_id: "solve-story", status: "complete" },
    target_title: "Data quality analyst",
  },
};
const completeRun: Route[] = [
  {
    method: "GET",
    path: /\/runs$/,
    answer: {
      items: [{ run_id: "solve-story", kind: "route_solve", status: "complete" }],
      next_cursor: null,
    },
  },
  completeSolve,
];
const comparison = {
  lead: "best_trade_offs_found",
  coverage: "complete",
  layers_exact: true,
  changed_since: { planning_inputs: false, profile: false },
  basis: {
    objective_basis: "direct_spending",
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
  schedules_total: 2,
  points_shown: 2,
  points_total: 2,
  points: [
    {
      point_id: 1,
      months_to_readiness: 6,
      objective_cost: { minor_units: 200000, currency: "GBP" },
      layer: 1,
      schedule_count: 1,
      schedules: [0],
    },
    {
      point_id: 2,
      months_to_readiness: 9,
      objective_cost: { minor_units: 120000, currency: "GBP" },
      layer: 1,
      schedule_count: 1,
      schedules: [1],
    },
  ],
  families: [],
  families_shown: 0,
  families_total: 0,
  blocking_inputs: [],
  starting_violations: [],
  longer_than_model: [],
  beyond_horizon: [],
  set_aside: [],
  narrowings: [],
};
const archive = {
  retained: 2,
  total: 2,
  next_cursor: null,
  items: [
    {
      index: 0,
      layer: 1,
      view_layer: null,
      months_to_readiness: 6,
      readiness_month: "2027-05",
      objective_cost: { minor_units: 200000, currency: "GBP" },
      verdict: "affordable_and_feasible_with_qualifications",
      conditions: [],
      qualifications: ["supplied_figures"],
    },
    {
      index: 1,
      layer: 1,
      view_layer: null,
      months_to_readiness: 9,
      readiness_month: "2027-08",
      objective_cost: { minor_units: 120000, currency: "GBP" },
      verdict: "affordable_and_feasible_with_qualifications",
      conditions: [],
      qualifications: ["proposed_records"],
    },
  ],
};

function Scene({ routes }: { routes: Route[] }) {
  const [queries] = useState(() => {
    fakeApi(routes);
    return new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  });
  return (
    <QueryClientProvider client={queries}>
      <div className="chapter on-reading chapter-panel">
        <RoutesChapter workspaceId="story-routes" />
      </div>
    </QueryClientProvider>
  );
}

const scene =
  (checkpointAnswer: object, extra: Route[] = [noRuns]) =>
  () => (
    <Scene
      routes={[
        { method: "GET", path: /\/planning\/checkpoint$/, answer: checkpointAnswer },
        ...extra,
      ]}
    />
  );

export const NoTarget: Story = {
  render: scene({ ...checkpoint, targets: [] }),
};
export const MissingFigure: Story = {
  render: scene({
    ...checkpoint,
    needs: [{ input: "direct_spend_cap", effect: "blocks_a_solve" }],
  }),
};
export const ReadyToSearch: Story = { render: scene(checkpoint) };
export const RoutesFound: Story = {
  render: scene(checkpoint, [
    ...completeRun,
    { method: "GET", path: /\/comparison$/, answer: comparison },
    { method: "GET", path: /\/schedules$/, answer: archive },
  ]),
};
export const SearchStopped: Story = {
  render: scene(checkpoint, [
    ...completeRun,
    {
      method: "GET",
      path: /\/comparison$/,
      answer: {
        ...comparison,
        coverage: "budget_truncated",
        layers_exact: false,
        narrowings: ["fewer_concepts", "one_start"],
      },
    },
    { method: "GET", path: /\/schedules$/, answer: archive },
  ]),
};

export const EarlierResultKept: Story = {
  render: scene(checkpoint, [
    {
      method: "GET",
      path: /\/runs$/,
      answer: {
        items: [
          { run_id: "failed-story", kind: "route_solve", status: "failed" },
          { run_id: "solve-story", kind: "route_solve", status: "complete" },
        ],
        next_cursor: null,
      },
    },
    {
      method: "GET",
      path: /\/planning\/solves\/failed-story$/,
      answer: {
        run: { run_id: "failed-story", status: "failed" },
        target_title: "Data quality analyst",
      },
    },
    completeSolve,
    { method: "GET", path: /\/comparison$/, answer: comparison },
    { method: "GET", path: /\/schedules$/, answer: archive },
  ]),
};

export const LongerThanModel: Story = {
  render: scene(checkpoint, [
    ...completeRun,
    {
      method: "GET",
      path: /\/comparison$/,
      answer: {
        ...comparison,
        lead: "longer_than_model",
        schedules_total: 0,
        points_shown: 0,
        points_total: 0,
        points: [],
        longer_than_model: [{ variant_id: "degree" }],
      },
    },
    {
      method: "GET",
      path: /\/schedules$/,
      answer: { retained: 0, total: 0, next_cursor: null, items: [] },
    },
  ]),
};

export const SelectedRoute: Story = {
  render: () => (
    <EvidenceProvider>
      <div className="chapter on-reading chapter-panel">
        <RouteDetailView detail={routeDetailFixture} />
      </div>
      <EvidenceDrawer />
    </EvidenceProvider>
  ),
};
