// Synthetic Plan states, including month-only next steps and proposed calendar dates.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { EvidenceProvider } from "@/components/EvidenceDrawer";
import { PlanChapter } from "@/components/PlanChapter";
import { fakeApi, type Route } from "@/test/fakeApi";
import { planRoute, savedPlan } from "@/test/planData";

const meta: Meta = { title: "Plan", parameters: { surface: "reading" } };
export default meta;
type Story = StoryObj;

function Scene({
  answer,
  status = 200,
  changes = { new_solve_needed: false },
  candidate = false,
  revision = false,
}: {
  answer: object;
  status?: number;
  changes?: object;
  candidate?: boolean;
  revision?: boolean;
}) {
  const [queries] = useState(() => {
    const url = new URL(window.location.href);
    url.searchParams.delete("solve_run_id");
    url.searchParams.delete("schedule_index");
    if (candidate) {
      url.searchParams.set("solve_run_id", savedPlan.source.solve_run_id);
      url.searchParams.set("schedule_index", "1");
    }
    window.history.replaceState({}, "", url);
    const route: Route = {
      method: "GET",
      path: /\/planning\/plans\/current$/,
      status,
      answer,
    };
    fakeApi([
      route,
      { method: "GET", path: /\/planning\/plans\/changes$/, answer: changes },
      { method: "GET", path: /\/planning\/plans\/history$/, answer: [] },
      {
        method: "GET",
        path: /\/planning\/solves\/[^/]+$/,
        answer: {
          run: { run_id: savedPlan.source.solve_run_id, status: "complete" },
          target_title: savedPlan.target_title,
        },
      },
      { method: "GET", path: /\/schedules\/1$/, answer: planRoute },
      ...(revision
        ? [
            {
              method: "GET" as const,
              path: /\/planning\/plans\/revision-preview$/,
              answer: {
                from_version: savedPlan.version,
                proposed_solve_run_id: savedPlan.source.solve_run_id,
                proposed_schedule_index: 1,
                proposed_route: planRoute,
                proposed_search: savedPlan.search,
                completed_steps: ["step-1"],
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
                  remaining_horizon_recalculated: false,
                },
              },
            },
          ]
        : []),
    ]);
    return new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  });
  return (
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <div className="chapter on-reading chapter-panel">
          <PlanChapter workspaceId="story-plan" />
        </div>
      </EvidenceProvider>
    </QueryClientProvider>
  );
}

const missing = {
  error: {
    code: "NOT_FOUND",
    message: "No chosen plan",
    retryable: false,
    stage: "planning",
    correlation_id: "story",
    details: {},
  },
};
export const NoPlan: Story = { render: () => <Scene answer={missing} status={404} /> };
export const RouteAwaitingConfirmation: Story = {
  render: () => <Scene answer={missing} status={404} candidate />,
};
export const SavedWithMonthOnly: Story = { render: () => <Scene answer={savedPlan} /> };
export const RestRecorded: Story = {
  render: () => (
    <Scene
      answer={{
        ...savedPlan,
        progress: { completed_steps: ["step-1"], rest_until: "2027-01-01", activity: [] },
      }}
    />
  ),
};
export const RevisionAwaitingConfirmation: Story = {
  render: () => (
    <Scene
      answer={{
        ...savedPlan,
        progress: { completed_steps: ["step-1"], rest_until: null, activity: [] },
      }}
      candidate
      revision
    />
  ),
};
export const SourceChanged: Story = {
  render: () => (
    <Scene
      answer={savedPlan}
      changes={{
        plan_version: 1,
        profile: true,
        planning_inputs: false,
        capability: false,
        target_matrix: false,
        option_pack: false,
        possibly_affected_steps: ["step-1"],
        new_solve_needed: true,
      }}
    />
  ),
};
export const ProposedCalendarDate: Story = {
  render: () => (
    <Scene
      answer={{
        ...savedPlan,
        events: [
          {
            key: "step-1:start",
            kind: "start",
            variant_id: "step-1",
            title: "Data course",
            on: "2026-12-08",
            conditional: true,
            proposed: true,
          },
        ],
        next_action: {
          key: "step-1:start",
          kind: "start",
          variant_id: "step-1",
          title: "Data course",
          on: "2026-12-08",
          conditional: true,
          proposed: true,
        },
      }}
    />
  ),
};
export const SearchStopped: Story = {
  render: () => (
    <Scene
      answer={{ ...savedPlan, search: { ...savedPlan.search, coverage: "budget_truncated" } }}
    />
  ),
};
export const ServiceUnavailable: Story = {
  render: () => (
    <Scene
      answer={{
        error: {
          code: "DEPENDENCY_UNAVAILABLE",
          message: "Unavailable",
          retryable: true,
          stage: "planning",
          correlation_id: "story",
          details: {},
        },
      }}
      status={503}
    />
  ),
};
