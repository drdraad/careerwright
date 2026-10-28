"use client";
// Server state (TanStack Query) over the generated client. Every workspace-scoped query shares
// the `["ws", id]` prefix, so a status event refetches exactly what that workspace shows.
import { type QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  type CreateWorkspace,
  createWorkspace,
  getMe,
  getProfile,
  getWorkspace,
  listSources,
  listWorkspaces,
  type ProfileInput,
  type ProfileOut,
  putProfile,
  type SourceOut,
} from "@/generated/api";
import { API_BASE, ApiError, newIdempotencyKey } from "./api";
import { useAuth } from "./auth";
import { openWorkspaceStream, type StreamStatus } from "./events";

const PAGE = 200; // the API's maximum page size

export const keys = {
  me: ["me"] as const,
  workspaces: ["workspaces"] as const,
  workspace: (id: string) => ["ws", id, "workspace"] as const,
  profile: (id: string) => ["ws", id, "profile"] as const,
  sources: (id: string) => ["ws", id, "sources"] as const,
  scope: (id: string) => ["ws", id] as const,
};

/** An access failure is final for this page; retrying cannot help. */
function retryable(failures: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false;
  return failures < 2;
}

export function useMe(enabled = true) {
  return useQuery({
    queryKey: keys.me,
    queryFn: async () => (await getMe({ throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

export function useWorkspaces(enabled = true) {
  return useQuery({
    queryKey: keys.workspaces,
    queryFn: async () =>
      (await listWorkspaces({ query: { limit: PAGE }, throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

export function useWorkspace(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.workspace(id),
    queryFn: async () =>
      (await getWorkspace({ path: { workspace_id: id }, throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

export function useProfile(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.profile(id),
    queryFn: async () =>
      (await getProfile({ path: { workspace_id: id }, throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

/** Every source reference of the workspace, all pages (a provenance list is never truncated). */
export function useSources(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.sources(id),
    queryFn: async () => {
      const all: SourceOut[] = [];
      let cursor: string | null = null;
      do {
        const query: { limit: number; cursor?: string } = { limit: PAGE };
        if (cursor !== null) query.cursor = cursor;
        const { data } = await listSources({
          path: { workspace_id: id },
          query,
          throwOnError: true,
        });
        all.push(...data.items);
        cursor = data.next_cursor;
      } while (cursor !== null);
      return all;
    },
    retry: retryable,
    enabled,
  });
}

export type SaveProfile = {
  expectedVersion: number;
  profile: ProfileInput;
  idempotencyKey: string;
};

export function useSaveProfile(id: string) {
  const queries = useQueryClient();
  return useMutation({
    mutationFn: async ({ expectedVersion, profile, idempotencyKey }: SaveProfile) =>
      (
        await putProfile({
          path: { workspace_id: id },
          body: { expected_version: expectedVersion, profile },
          headers: { "Idempotency-Key": idempotencyKey },
          throwOnError: true,
        })
      ).data as ProfileOut,
    onSuccess: (saved) => {
      queries.setQueryData(keys.profile(id), saved);
      void queries.invalidateQueries({ queryKey: keys.scope(id) });
    },
  });
}

export function useCreateWorkspace() {
  const queries = useQueryClient();
  return useMutation({
    mutationFn: async (body: CreateWorkspace) =>
      (
        await createWorkspace({
          body,
          headers: { "Idempotency-Key": newIdempotencyKey() },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => queries.invalidateQueries({ queryKey: keys.workspaces }),
  });
}

/** Coalesces a burst of events (a replay after reconnecting) into one refetch. */
function invalidator(queries: QueryClient, id: string): () => void {
  let pending = false;
  return () => {
    if (pending) return;
    pending = true;
    setTimeout(() => {
      pending = false;
      void queries.invalidateQueries({ queryKey: keys.scope(id) });
      void queries.invalidateQueries({ queryKey: keys.workspaces });
    }, 50);
  };
}

const sleep = (ms: number, signal: AbortSignal) =>
  new Promise<void>((resolve) => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener("abort", () => {
      clearTimeout(timer);
      resolve();
    });
  });

/** Subscribes to the workspace's status events while mounted; returns the stream's status. */
export function useWorkspaceEvents(id: string, enabled: boolean): StreamStatus {
  const { token } = useAuth();
  const queries = useQueryClient();
  const [status, setStatus] = useState<StreamStatus>({ state: "connecting" });
  useEffect(() => {
    if (!enabled) return;
    const changed = invalidator(queries, id);
    const handle = openWorkspaceStream({
      url: `${API_BASE}/v1/workspaces/${encodeURIComponent(id)}/events/stream`,
      fetch: (url, init) => fetch(url, init),
      token,
      sleep,
      onEvent: changed,
      onStatus: (next) => {
        setStatus(next);
        if (next.state === "live") changed(); // reconnected: catch up on anything missed
      },
    });
    return () => handle.stop();
  }, [id, enabled, token, queries]);
  return status;
}
