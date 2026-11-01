// Model spending (MODEL-10) and the estimate before a paid run starts (MODEL-08), on a scripted
// API at the network edge: the spending line with a call whose cost is unknown, changing the
// limits, a demo workspace; and the estimate when it fits, when a limit would refuse it, and on a
// demo stand-in. Every value is synthetic.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { ModelSpending } from "@/components/ModelSpending";
import { RunEstimate } from "@/components/RunEstimate";
import type { RunEstimateOut, SpendOut } from "@/generated/api";
import { fakeApi, type Route } from "@/test/fakeApi";

const meta: Meta = { title: "Spending" };
export default meta;
type Story = StoryObj;

const WS = "w-story";
const spend: SpendOut = {
  run_limit_nano_usd: 750_000_000,
  period_limit_nano_usd: 5_120_000_000,
  version: 2,
  period_start: "2027-01-01",
  period_committed_nano_usd: 420_000_000,
  unknown_cost_attempts: 1,
};
const estimate: RunEstimateOut = {
  kind: "interview_turn",
  model_id: "muse-wonder-1.0",
  model_mode: "standard",
  per_run_nano_usd: 528_000_000,
  hard_maximum_nano_usd: 750_000_000,
  refused_scope: null,
};

function Api({ routes, children }: { routes: Route[]; children: ReactNode }) {
  const [queries] = useState(() => {
    fakeApi(routes);
    return new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  });
  return (
    <QueryClientProvider client={queries}>
      <div className="grid max-w-sm gap-12">{children}</div>
    </QueryClientProvider>
  );
}

const spending = (demo: boolean) => () => (
  <Api routes={[{ method: "GET", path: /\/spend$/, answer: spend }]}>
    <ModelSpending workspaceId={WS} demo={demo} />
  </Api>
);
export const SpendingThisMonth: Story = { render: spending(false) };
export const SpendingInADemo: Story = { render: spending(true) };

const shownEstimate = (answer: RunEstimateOut) => () => (
  <Api routes={[{ method: "GET", path: /\/spend\/estimate$/, answer }]}>
    <RunEstimate workspaceId={WS} kind="interview_turn" />
  </Api>
);
export const EstimateFits: Story = { render: shownEstimate(estimate) };
export const EstimateRefusedByTheMonth: Story = {
  render: shownEstimate({ ...estimate, refused_scope: "period" }),
};
// The API's maxima are clipped to the run limit here, so no cost is stated: only the refusal.
export const EstimateRefusedByTheRunLimit: Story = {
  render: shownEstimate({
    ...estimate,
    per_run_nano_usd: 150_000_000,
    hard_maximum_nano_usd: 150_000_000,
    refused_scope: "run",
  }),
};
export const EstimateOnADemoStandIn: Story = {
  render: shownEstimate({
    ...estimate,
    model_id: "careerwright-fixture-interviewer-1",
    model_mode: "fixture",
    per_run_nano_usd: 0,
    hard_maximum_nano_usd: 0,
  }),
};
