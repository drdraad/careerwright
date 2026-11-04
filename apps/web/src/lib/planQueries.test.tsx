import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { fakeApi } from "@/test/fakeApi";
import { planRoute } from "@/test/planData";
import { readPlanCandidate, useCurrentPlan, usePlanCandidate } from "./planQueries";

const RUN = "d0666439-268d-48ee-b383-b5e8556305de";
const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
);

describe("a Plan link points to one computed route", () => {
  it("rejects malformed run IDs and archive indexes before requesting them", () => {
    expect(readPlanCandidate(`?solve_run_id=${RUN}&schedule_index=1`)).toEqual({
      runId: RUN,
      index: 1,
    });
    expect(readPlanCandidate("?solve_run_id=fixture&schedule_index=1")).toBeNull();
    expect(readPlanCandidate(`?solve_run_id=${RUN}&schedule_index=-1`)).toBeNull();
    expect(readPlanCandidate(`?solve_run_id=${RUN}&schedule_index=1.5`)).toBeNull();
    expect(readPlanCandidate(`?solve_run_id=${RUN}&schedule_index=999999999999999999`)).toBeNull();
  });

  it("treats no saved plan as an empty state, not a request failure", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/planning\/plans\/current$/,
        status: 404,
        answer: {
          error: {
            code: "NOT_FOUND",
            message: "No chosen plan",
            retryable: false,
            stage: "planning",
            correlation_id: "test",
            details: {},
          },
        },
      },
    ]);
    const { result } = renderHook(() => useCurrentPlan("workspace"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });

  it("only opens a route detail after its solve has completed", async () => {
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/planning\/solves\/[^/]+$/,
        answer: { run: { run_id: RUN, status: "running" }, target_title: "Data quality analyst" },
      },
      { method: "GET", path: /\/schedules\/1$/, answer: planRoute },
    ]);
    const { result } = renderHook(() => usePlanCandidate("workspace", { runId: RUN, index: 1 }), {
      wrapper,
    });
    await waitFor(() => expect(result.current.data?.route).toBeNull());
    expect(sent.some((request) => request.path.endsWith("/schedules/1"))).toBe(false);
  });
});
