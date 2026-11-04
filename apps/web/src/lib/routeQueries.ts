"use client";
import {
  notifyManager,
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useCallback, useState, useSyncExternalStore } from "react";
import {
  type CheckpointOut,
  type ComparisonOut,
  getRouteComparison,
  getRouteSchedule,
  getRouteSolve,
  type ListRouteSchedulesData,
  listRouteSchedules,
  listRuns,
  type ProfileOut,
  type RouteDetail,
  type RunPage,
  requestRouteSolve,
  type SchedulePageOut,
  type SolveOut,
  type SolveRequest,
} from "@/generated/api";
import { ApiError, ChangeKeys } from "./api";
import type { RouteResultStatus } from "./routeState";

const routeKey = (id: string) => ["ws", id, "routes"] as const;
const latestKey = (id: string, target: string | null) =>
  [...routeKey(id), "latest", target] as const;
const path = (id: string, runId: string) => ({ workspace_id: id, run_id: runId });
const retryable = (failures: number, error: unknown) =>
  !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failures < 2;

type RouteHistory = { latest: SolveOut | null; kept: SolveOut | null };

/** Find the newest search for one target, or any target when null, and a kept completed result. */
export function useLatestRouteSolve(id: string, target: string | null) {
  return useQuery({
    queryKey: latestKey(id, target),
    queryFn: async (): Promise<RouteHistory> => {
      let cursor: string | null = null;
      let latest: SolveOut | null = null;
      let kept: SolveOut | null = null;
      do {
        const page: RunPage = (
          await listRuns({
            path: { workspace_id: id },
            query: { limit: 200, ...(cursor === null ? {} : { cursor }) },
            throwOnError: true,
          })
        ).data;
        for (const run of page.items) {
          if (run.kind !== "route_solve") continue;
          const candidate = (
            await getRouteSolve({ path: path(id, run.run_id), throwOnError: true })
          ).data;
          if (target !== null && candidate.target_title !== target) continue;
          if (latest === null) {
            latest = candidate;
            if (latest.run.status === "complete") break;
          } else if (run.status === "complete") {
            kept = candidate;
            break;
          }
        }
        cursor = page.next_cursor;
      } while (latest?.run.status !== "complete" && kept === null && cursor !== null);
      return { latest, kept };
    },
    enabled: target !== "",
    retry: retryable,
    refetchInterval: (query) =>
      query.state.data?.latest?.run.status === "queued" ||
      query.state.data?.latest?.run.status === "running"
        ? 2000
        : false,
  });
}

/** One route search over the inputs the person saw; retries keep the same idempotency key. */
export function useRequestRouteSolve(id: string) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: async (body: SolveRequest): Promise<SolveOut> =>
      (
        await requestRouteSolve({
          path: { workspace_id: id },
          body,
          headers: { "Idempotency-Key": changes.keyFor(body) },
          throwOnError: true,
        })
      ).data,
    onSuccess: (solve) => {
      changes.settled();
      const key = latestKey(id, solve.target_title);
      const previous = queries.getQueryData<RouteHistory>(key);
      queries.setQueryData(key, {
        latest: solve,
        kept:
          previous?.latest?.run.status === "complete" ? previous.latest : (previous?.kept ?? null),
      });
      return queries.invalidateQueries({ queryKey: ["ws", id] });
    },
  });
}

export function useRouteComparison(id: string, runId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: [...routeKey(id), runId, "comparison"],
    queryFn: async () =>
      (await getRouteComparison({ path: path(id, runId ?? ""), throwOnError: true })).data,
    enabled: enabled && runId !== null,
    retry: retryable,
    // Research can expire without a workspace event; the server owns its freshness rules.
    refetchInterval: 60_000,
  });
}

export type RouteView = NonNullable<ListRouteSchedulesData["query"]>;

export function useRouteSchedules(
  id: string,
  runId: string | null,
  view: RouteView,
  enabled: boolean,
) {
  return useQuery({
    queryKey: [...routeKey(id), runId, "schedules", view],
    queryFn: async () =>
      (
        await listRouteSchedules({
          path: path(id, runId ?? ""),
          query: view,
          throwOnError: true,
        })
      ).data,
    enabled: enabled && runId !== null,
    retry: retryable,
  });
}

export function useRouteSchedule(id: string, runId: string | null, index: number | null) {
  return useQuery({
    queryKey: [...routeKey(id), runId, "schedules", index],
    queryFn: async () =>
      (
        await getRouteSchedule({
          path: { ...path(id, runId ?? ""), index: index ?? 0 },
          throwOnError: true,
        })
      ).data,
    enabled: runId !== null && index !== null,
    retry: retryable,
  });
}

/** The landscape opens a bounded page of journeys; other routes stay in the paged archive. */
export function useRouteJourneyDetails(id: string, runId: string | null, indexes: number[]) {
  return useQueries({
    queries: [...new Set(indexes)].slice(0, 6).map((index) => ({
      queryKey: [...routeKey(id), runId, "schedules", index],
      queryFn: async () =>
        (
          await getRouteSchedule({
            path: { ...path(id, runId ?? ""), index },
            throwOnError: true,
          })
        ).data,
      enabled: runId !== null,
      retry: retryable,
    })),
  });
}

type CachedRouteLandscape = {
  routes: RouteDetail[];
  status: RouteResultStatus;
  scheduleCount?: number;
  detailStatus?: "pending" | "error";
  routeSetId?: string;
};

const landscapeQueryKey = (key: readonly unknown[], id: string) =>
  key[0] === "ws" &&
  key[1] === id &&
  (key[2] === "routes" ||
    (key[2] === "profile" && key.length === 3) ||
    (key[2] === "planning" && key[3] === "checkpoint"));

/** Keep visited destinations visible without fetching the other targets' route archives. */
export function useCachedRouteLandscapes(id: string, targets: string[]) {
  const queries = useQueryClient();
  const cache = queries.getQueryCache();
  const subscribe = useCallback(
    (changed: () => void) => {
      const notify = notifyManager.batchCalls(changed);
      return cache.subscribe((event) => {
        if (event.type !== "updated" && event.type !== "removed") return;
        const key = event.query.queryKey;
        if (landscapeQueryKey(key, id)) notify();
      });
    },
    [cache, id],
  );
  const snapshot = useCallback(
    () =>
      cache
        .findAll({ queryKey: ["ws", id] })
        .filter((query) => landscapeQueryKey(query.queryKey, id))
        .filter(
          (query) =>
            query.state.dataUpdateCount > 0 ||
            query.state.errorUpdateCount > 0 ||
            query.state.isInvalidated,
        )
        .map((query) => {
          const state = query.state;
          return `${query.queryHash}:${state.dataUpdateCount}:${state.errorUpdateCount}:${state.status}:${state.fetchStatus}:${state.isInvalidated}`;
        })
        .join("|"),
    [cache, id],
  );
  useSyncExternalStore(subscribe, snapshot, () => "");
  const checkpoint = queries.getQueryData<CheckpointOut>(["ws", id, "planning", "checkpoint"]);
  const profile = queries.getQueryData<ProfileOut>(["ws", id, "profile"]);
  return Object.fromEntries(
    targets.map((target): [string, CachedRouteLandscape] => {
      const history = queries.getQueryState<RouteHistory>(latestKey(id, target));
      const active = history?.data?.latest;
      const shown = active?.run.status === "complete" ? active : history?.data?.kept;
      const runId = shown?.run.run_id;
      const comparison = queries.getQueryState<ComparisonOut>([
        ...routeKey(id),
        runId,
        "comparison",
      ]);
      const schedules = queries.getQueryState<SchedulePageOut>([
        ...routeKey(id),
        runId,
        "schedules",
        { limit: 6 },
      ]);
      const details =
        schedules?.data?.items
          .slice(0, 6)
          .map((schedule) =>
            queries.getQueryState<RouteDetail>([
              ...routeKey(id),
              runId,
              "schedules",
              schedule.index,
            ]),
          ) ?? [];
      const routes = details.flatMap((detail) => (detail?.data ? [detail.data] : []));
      const invalidated = [history, comparison, schedules, ...details].some(
        (query) => query?.isInvalidated,
      );
      const changed =
        (comparison?.data && Object.values(comparison.data.changed_since).some(Boolean)) ||
        (shown?.inputs_version != null &&
          checkpoint !== undefined &&
          shown.inputs_version !== checkpoint.inputs_version) ||
        (shown?.run.profile_version != null &&
          profile !== undefined &&
          shown.run.profile_version !== profile.version);
      const status: RouteResultStatus =
        active?.run.status === "queued" || active?.run.status === "running"
          ? "pending"
          : invalidated || changed || (shown && shown !== active)
            ? "stale"
            : history?.error || comparison?.error || schedules?.error
              ? "error"
              : !history?.data
                ? "unloaded"
                : !shown
                  ? active
                    ? "error"
                    : "not_searched"
                  : !comparison?.data
                    ? "pending"
                    : comparison.data.schedules_total > 0
                      ? "available"
                      : comparison.data.coverage !== "complete"
                        ? "limited"
                        : comparison.data.lead === "no_route_in_bounded_model"
                          ? "unsupported"
                          : "unresolved";
      return [
        target,
        {
          routes,
          status,
          scheduleCount: comparison?.data?.schedules_total,
          routeSetId: runId,
          detailStatus: details.some((detail) => detail?.error)
            ? "error"
            : (comparison?.data?.schedules_total ?? 0) > routes.length &&
                (!schedules?.data || details.some((detail) => !detail?.data))
              ? "pending"
              : undefined,
        },
      ];
    }),
  );
}
