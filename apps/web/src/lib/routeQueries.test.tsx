import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fakeApi } from "@/test/fakeApi";
import { lifecycleComparison, lifecycleRunId } from "@/test/routeLifecycleData";
import { completePlanningRoute } from "@/test/routeStateData";
import {
  useLatestRouteSolve,
  useRouteComparison,
  useRouteJourneyDetails,
  useRouteSchedule,
} from "./routeQueries";

afterEach(() => vi.useRealTimers());

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
);

describe("[API-02] the latest route search remains findable after other runs", () => {
  it("follows run pages until it finds a route solve, then reads its current state", async () => {
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/runs$/,
        answer: ({ query }) =>
          query === "?limit=200"
            ? {
                items: [{ run_id: "other", kind: "interview_turn", status: "complete" }],
                next_cursor: "older",
              }
            : {
                items: [{ run_id: "solve-1", kind: "route_solve", status: "complete" }],
                next_cursor: null,
              },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/solve-1$/,
        answer: { run: { run_id: "solve-1", status: "complete" }, target_title: "Nurse" },
      },
    ]);

    const { result } = renderHook(() => useLatestRouteSolve("workspace-1", "Nurse"), { wrapper });

    await waitFor(() => expect(result.current.data?.latest?.target_title).toBe("Nurse"));
    expect(sent.map((request) => request.path)).toEqual([
      "/v1/workspaces/workspace-1/runs",
      "/v1/workspaces/workspace-1/runs",
      "/v1/workspaces/workspace-1/planning/solves/solve-1",
    ]);
    expect(sent[1]?.query).toContain("cursor=older");
  });

  it("shows no previous search only after every run page was checked", async () => {
    fakeApi([{ method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } }]);
    const { result } = renderHook(() => useLatestRouteSolve("workspace-2", "Nurse"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ latest: null, kept: null });
  });

  it("keeps the earlier completed routes when the newest search failed", async () => {
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/runs$/,
        answer: {
          items: [
            { run_id: "failed", kind: "route_solve", status: "failed" },
            { run_id: "complete", kind: "route_solve", status: "complete" },
          ],
          next_cursor: null,
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/failed$/,
        answer: { run: { run_id: "failed", status: "failed" }, target_title: "Nurse" },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/complete$/,
        answer: { run: { run_id: "complete", status: "complete" }, target_title: "Nurse" },
      },
    ]);

    const { result } = renderHook(() => useLatestRouteSolve("workspace-3", "Nurse"), { wrapper });
    await waitFor(() => expect(result.current.data?.kept?.run.run_id).toBe("complete"));

    expect(result.current.data?.latest?.run.status).toBe("failed");
    expect(sent).toHaveLength(3);
  });

  it("keeps the earlier result for the same target, past another target's result", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/runs$/,
        answer: {
          items: [
            { run_id: "failed-nurse", kind: "route_solve", status: "failed" },
            { run_id: "complete-teacher", kind: "route_solve", status: "complete" },
            { run_id: "complete-nurse", kind: "route_solve", status: "complete" },
          ],
          next_cursor: null,
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/failed-nurse$/,
        answer: { run: { run_id: "failed-nurse", status: "failed" }, target_title: "Nurse" },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/complete-teacher$/,
        answer: {
          run: { run_id: "complete-teacher", status: "complete" },
          target_title: "Teacher",
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/complete-nurse$/,
        answer: { run: { run_id: "complete-nurse", status: "complete" }, target_title: "Nurse" },
      },
    ]);

    const { result } = renderHook(() => useLatestRouteSolve("workspace-4", "Nurse"), { wrapper });
    await waitFor(() => expect(result.current.data?.kept?.run.run_id).toBe("complete-nurse"));
  });

  it("finds an earlier target after a newer target has completed", async () => {
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/runs$/,
        answer: {
          items: [
            { run_id: "teacher", kind: "route_solve", status: "complete" },
            { run_id: "nurse", kind: "route_solve", status: "complete" },
          ],
          next_cursor: null,
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/teacher$/,
        answer: { run: { run_id: "teacher", status: "complete" }, target_title: "Teacher" },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/nurse$/,
        answer: { run: { run_id: "nurse", status: "complete" }, target_title: "Nurse" },
      },
    ]);

    const { result } = renderHook(() => useLatestRouteSolve("workspace-5", "Nurse"), { wrapper });
    await waitFor(() => expect(result.current.data?.latest?.run.run_id).toBe("nurse"));
    expect(sent.map((request) => request.path)).toContain(
      "/v1/workspaces/workspace-5/planning/solves/nurse",
    );
  });

  it("reports a completed search for any target in a multi-target workspace", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/runs$/,
        answer: {
          items: [{ run_id: "other-target", kind: "route_solve", status: "complete" }],
          next_cursor: null,
        },
      },
      {
        method: "GET",
        path: /\/planning\/solves\/other-target$/,
        answer: {
          run: { run_id: "other-target", status: "complete" },
          target_title: "Teacher",
        },
      },
    ]);
    const { result } = renderHook(() => useLatestRouteSolve("workspace-6", null), { wrapper });
    await waitFor(() => expect(result.current.data?.latest?.target_title).toBe("Teacher"));
  });
});

describe("[API-02][VIS-1] route details share a bounded query cache", () => {
  it("loads at most six distinct details and shares the selected detail's cache entry", async () => {
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/schedules\/\d+$/,
        answer: ({ path }) => ({
          ...completePlanningRoute,
          schedule: { ...completePlanningRoute.schedule, index: Number(path.split("/").at(-1)) },
        }),
      },
    ]);
    const queries = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: Infinity } },
    });
    const provider = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queries}>{children}</QueryClientProvider>
    );
    const { result } = renderHook(
      () => ({
        landscape: useRouteJourneyDetails("w-bounded", lifecycleRunId, [0, 1, 0, 2, 3, 4, 5, 6, 7]),
        selected: useRouteSchedule("w-bounded", lifecycleRunId, 2),
      }),
      { wrapper: provider },
    );
    await waitFor(() =>
      expect(result.current.landscape.every((query) => query.isSuccess)).toBe(true),
    );
    expect(result.current.landscape).toHaveLength(6);
    expect(sent.map((request) => request.path.split("/").at(-1)).sort()).toEqual([
      "0",
      "1",
      "2",
      "3",
      "4",
      "5",
    ]);
    expect(result.current.selected.data).toBe(result.current.landscape[2]?.data);
    expect(
      queries
        .getQueryCache()
        .findAll({ queryKey: ["ws", "w-bounded", "routes", lifecycleRunId, "schedules"] }),
    ).toHaveLength(6);
    expect(sent.every((request) => request.method === "GET")).toBe(true);
  });

  it("does not load detail records before a saved solve exists", () => {
    const sent = fakeApi([]);
    renderHook(() => useRouteJourneyDetails("w-empty", null, [0, 1]), { wrapper });
    expect(sent).toHaveLength(0);
  });
});

describe("[STATE-07] route research expiry is checked without a new solve", () => {
  it("polls the server's changed flags when research expires without a workspace event", async () => {
    vi.useFakeTimers();
    let expired = false;
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/comparison$/,
        answer: () => ({
          ...lifecycleComparison(),
          changed_since: { ...lifecycleComparison().changed_since, option_pack: expired },
        }),
      },
    ]);
    const { result } = renderHook(() => useRouteComparison("w-expiry", lifecycleRunId, true), {
      wrapper,
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(result.current.data?.changed_since.option_pack).toBe(false);
    expired = true;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60_000);
    });
    expect(result.current.data?.changed_since.option_pack).toBe(true);
    expect(sent.length).toBeGreaterThanOrEqual(2);
    expect(
      sent.every((request) => request.method === "GET" && request.path.endsWith("/comparison")),
    ).toBe(true);
  });
});
