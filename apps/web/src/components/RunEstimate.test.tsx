// What a paid run may cost, before it starts (spec section 16; MODEL-08): the API's two
// maxima in dollars, and where to raise a limit that would refuse it.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { RunEstimateOut } from "@/generated/api";
import { fakeApi } from "@/test/fakeApi";
import { RunEstimate } from "./RunEstimate";

const estimate: RunEstimateOut = {
  kind: "interview_turn",
  model_id: "muse-wonder-1.0",
  model_mode: "standard",
  per_run_nano_usd: 528_000_000,
  hard_maximum_nano_usd: 750_000_000,
  refused_scope: null,
};

function shown(answer: RunEstimateOut) {
  const sent = fakeApi([{ method: "GET", path: /\/spend\/estimate$/, answer }]);
  render(
    <QueryClientProvider client={new QueryClient()}>
      <RunEstimate workspaceId="w-estimate" kind="interview_turn" />
    </QueryClientProvider>,
  );
  return sent;
}

describe("[MODEL-08] a paid run's estimated cost shows before it starts", () => {
  it("states the most it can cost, and the most if it has to restart", async () => {
    const sent = shown(estimate);

    expect(
      await screen.findByText(
        "This can cost up to $0.53 on your Meta key. If it has to restart, never more than $0.75.",
      ),
    ).toBeVisible();
    expect(sent[0]?.query).toBe("?kind=interview_turn");
  });

  it("says which limit would refuse it, and where to raise it", async () => {
    shown({ ...estimate, refused_scope: "period" });

    expect(
      await screen.findByText(
        "This month's spending limit doesn't leave room for it. You can raise the limit under Model spending, in the menu at the top.",
      ),
    ).toBeVisible();
  });

  it("when the run limit refuses it, never states that limit as its cost", async () => {
    // One attempt needs more than the run limit, so the API's maximum is clipped to it.
    shown({
      ...estimate,
      per_run_nano_usd: 150_000_000,
      hard_maximum_nano_usd: 150_000_000,
      refused_scope: "run",
    });

    expect(
      await screen.findByText(
        "It needs more than this workspace's limit for one run. You can raise the limit under Model spending, in the menu at the top.",
      ),
    ).toBeVisible();
    expect(screen.queryByText(/can cost/)).toBeNull();
    expect(screen.queryByText(/\$0\.15/)).toBeNull();
  });

  it("says a demo stand-in costs nothing", async () => {
    shown({ ...estimate, model_mode: "fixture", per_run_nano_usd: 0, hard_maximum_nano_usd: 0 });

    expect(
      await screen.findByText("This uses the demo's stand-in, so it costs nothing."),
    ).toBeVisible();
  });
});
