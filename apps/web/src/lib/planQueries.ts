"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  type ChoosePlan,
  choosePlan,
  getCurrentPlan,
  getPlanChanges,
  getPlanVersion,
  getRouteSchedule,
  getRouteSolve,
  listPlanVersions,
  type ProgressUpdate,
  previewPlanRevision,
  type ReplanRequest,
  type RouteDetail,
  recordPlanProgress,
  requestRemainingRouteSolve,
  type SolveOut,
} from "@/generated/api";
import { ApiError, ChangeKeys } from "./api";

export type PlanCandidate = { runId: string; index: number };

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** A Plan link names a saved solver result and an archive index, never a fixture preview. */
export function readPlanCandidate(search: string): PlanCandidate | null {
  const params = new URLSearchParams(search);
  const runId = params.get("solve_run_id");
  const index = params.get("schedule_index");
  if (runId === null || !UUID.test(runId) || index === null || !/^(0|[1-9]\d*)$/.test(index))
    return null;
  const number = Number(index);
  return Number.isSafeInteger(number) ? { runId, index: number } : null;
}

const key = (id: string) => ["ws", id, "planning", "plans"] as const;
const currentKey = (id: string) => [...key(id), "current"] as const;
const retryable = (failures: number, error: unknown) =>
  !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failures < 2;

export function useCurrentPlan(id: string, enabled = true) {
  return useQuery({
    queryKey: currentKey(id),
    queryFn: async () => {
      try {
        return (await getCurrentPlan({ path: { workspace_id: id }, throwOnError: true })).data;
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    retry: retryable,
    enabled,
  });
}

export function usePlanCandidate(id: string, candidate: PlanCandidate | null) {
  return useQuery({
    queryKey: [...key(id), "candidate", candidate?.runId, candidate?.index],
    queryFn: async (): Promise<{ solve: SolveOut; route: RouteDetail | null }> => {
      if (candidate === null) throw new Error("Missing route selection");
      const solve = (
        await getRouteSolve({
          path: { workspace_id: id, run_id: candidate.runId },
          throwOnError: true,
        })
      ).data;
      if (solve.run.status !== "complete") return { solve, route: null };
      const route = (
        await getRouteSchedule({
          path: { workspace_id: id, run_id: candidate.runId, index: candidate.index },
          throwOnError: true,
        })
      ).data;
      if (route.schedule.index !== candidate.index) throw new Error("Route index changed");
      return { solve, route };
    },
    enabled: candidate !== null,
    retry: retryable,
  });
}

export function usePlanChanges(id: string, enabled: boolean) {
  return useQuery({
    queryKey: [...key(id), "changes"],
    queryFn: async () =>
      (await getPlanChanges({ path: { workspace_id: id }, throwOnError: true })).data,
    enabled,
    retry: retryable,
    // Expiring research may change the catalogue without a new saved workspace event.
    refetchInterval: 60_000,
  });
}

export function usePlanHistory(id: string, enabled: boolean) {
  return useQuery({
    queryKey: [...key(id), "history"],
    queryFn: async () =>
      (await listPlanVersions({ path: { workspace_id: id }, throwOnError: true })).data,
    enabled,
    retry: retryable,
  });
}

export function usePlanVersion(id: string, version: number | null) {
  return useQuery({
    queryKey: [...key(id), "version", version],
    queryFn: async () => {
      if (version === null) throw new Error("Missing plan version");
      return (await getPlanVersion({ path: { workspace_id: id, version }, throwOnError: true }))
        .data;
    },
    enabled: version !== null,
    retry: retryable,
  });
}

export function usePlanRevisionPreview(
  id: string,
  candidate: PlanCandidate | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: [...key(id), "revision-preview", candidate?.runId, candidate?.index],
    queryFn: async () => {
      if (candidate === null) throw new Error("Missing route selection");
      return (
        await previewPlanRevision({
          path: { workspace_id: id },
          query: { solve_run_id: candidate.runId, schedule_index: candidate.index },
          throwOnError: true,
        })
      ).data;
    },
    enabled: enabled && candidate !== null,
    retry: retryable,
  });
}

export function useRecordPlanProgress(id: string) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: async (body: ProgressUpdate) =>
      (
        await recordPlanProgress({
          path: { workspace_id: id },
          body,
          headers: { "Idempotency-Key": changes.keyFor(body) },
          throwOnError: true,
        })
      ).data,
    onSuccess: (plan) => {
      changes.settled();
      queries.setQueryData(currentKey(id), plan);
      return queries.invalidateQueries({ queryKey: ["ws", id] });
    },
  });
}

export function useChoosePlan(id: string) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: async (body: ChoosePlan) =>
      (
        await choosePlan({
          path: { workspace_id: id },
          body,
          headers: { "Idempotency-Key": changes.keyFor(body) },
          throwOnError: true,
        })
      ).data,
    onSuccess: (plan) => {
      changes.settled();
      queries.setQueryData(currentKey(id), plan);
      return queries.invalidateQueries({ queryKey: ["ws", id] });
    },
  });
}

export function useRequestRemainingRouteSolve(id: string) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: async (body: ReplanRequest): Promise<SolveOut> =>
      (
        await requestRemainingRouteSolve({
          path: { workspace_id: id },
          body,
          headers: { "Idempotency-Key": changes.keyFor(body) },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => {
      changes.settled();
      return queries.invalidateQueries({ queryKey: ["ws", id] });
    },
  });
}
