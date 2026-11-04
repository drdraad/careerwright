"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  estimateOptionResearch,
  listOptionResearch,
  readOptionPages,
  type StartOptionResearch,
  startOptionResearch,
} from "@/generated/api";
import { ApiError, ChangeKeys } from "./api";

const key = (id: string) => ["ws", id, "option-research"] as const;
const retryable = (failures: number, error: unknown) =>
  !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failures < 2;

export function useOptionResearchEstimate(id: string, enabled: boolean) {
  return useQuery({
    queryKey: [...key(id), "estimate"],
    queryFn: async () =>
      (await estimateOptionResearch({ path: { workspace_id: id }, throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

export function useOptionResearchList(id: string, enabled: boolean) {
  return useQuery({
    queryKey: [...key(id), "list"],
    queryFn: async () =>
      (await listOptionResearch({ path: { workspace_id: id }, throwOnError: true })).data,
    retry: retryable,
    enabled,
    refetchInterval: (query) =>
      query.state.data?.some((item) => item.status === "searching" || item.status === "reading")
        ? 2_000
        : false,
  });
}

export function useStartOptionResearch(id: string) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: async (body: StartOptionResearch) =>
      (
        await startOptionResearch({
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

export function useReadOptionPages(id: string) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: async (researchId: string) =>
      (
        await readOptionPages({
          path: { workspace_id: id, research_id: researchId },
          headers: { "Idempotency-Key": changes.keyFor(researchId) },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => {
      changes.settled();
      return queries.invalidateQueries({ queryKey: ["ws", id] });
    },
  });
}
