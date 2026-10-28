"use client";
// Server state (TanStack Query) over the generated client. Every workspace-scoped query shares
// the `["ws", id]` prefix, so a status event refetches exactly what that workspace shows.
import { type QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
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
import { API_BASE, ApiError, ChangeKeys } from "./api";
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

type Page<T> = { items: T[]; next_cursor: string | null };
type PageQuery = { limit: number; cursor?: string };

/** Reads every page (a list the UI shows is never silently truncated). */
async function allPages<T>(read: (query: PageQuery) => Promise<Page<T>>): Promise<T[]> {
  const all: T[] = [];
  let cursor: string | null = null;
  do {
    const query: PageQuery = { limit: PAGE };
    if (cursor !== null) query.cursor = cursor;
    const page: Page<T> = await read(query);
    all.push(...page.items);
    cursor = page.next_cursor;
  } while (cursor !== null);
  return all;
}

export function useWorkspaces(enabled = true) {
  return useQuery({
    queryKey: keys.workspaces,
    queryFn: () =>
      allPages(async (query) => (await listWorkspaces({ query, throwOnError: true })).data),
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

/** The current profile; also used to fetch the latest version after a stale save. */
export function profileQuery(id: string) {
  return {
    queryKey: keys.profile(id),
    queryFn: async (): Promise<ProfileOut> =>
      (await getProfile({ path: { workspace_id: id }, throwOnError: true })).data,
    retry: retryable,
  };
}

export function useProfile(id: string, enabled = true) {
  return useQuery({ ...profileQuery(id), enabled });
}

/** Every source reference of the workspace (a provenance list is never truncated). */
export function useSources(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.sources(id),
    queryFn: (): Promise<SourceOut[]> =>
      allPages(
        async (query) =>
          (await listSources({ path: { workspace_id: id }, query, throwOnError: true })).data,
      ),
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

/** Creating a workspace; a retry of the same submission reuses its key, so it creates one. */
export function useCreateWorkspace() {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: async (body: CreateWorkspace) =>
      (
        await createWorkspace({
          body,
          headers: { "Idempotency-Key": changes.keyFor(body) },
          throwOnError: true,
        })
      ).data,
    onSuccess: () => {
      changes.settled();
      return queries.invalidateQueries({ queryKey: keys.workspaces });
    },
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
      void queries.invalidateQueries({ queryKey: keys.me });
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
/** The last event each workspace's stream received on this page, for a remounted stream. */
const lastSeen = new Map<string, number>();

export type WorkspaceEvents = { status: StreamStatus; restart(): void };

/**
 * Subscribes to the workspace's status events while mounted. A stream opened again on this
 * page resumes after the last event it saw; a newly opened page starts after `startAfter`,
 * the workspace's `last_event_seq` read with the workspace, so nothing is replayed and
 * nothing after that read is missed.
 */
export function useWorkspaceEvents(
  id: string,
  enabled: boolean,
  startAfter: number | undefined,
): WorkspaceEvents {
  const { token } = useAuth();
  const queries = useQueryClient();
  const [status, setStatus] = useState<StreamStatus>({ state: "connecting" });
  const [generation, setGeneration] = useState(0);
  // Read when the stream opens; a later workspace refetch must not restart it.
  const start = useRef(startAfter);
  start.current = startAfter;
  // biome-ignore lint/correctness/useExhaustiveDependencies: `generation` restarts the stream
  useEffect(() => {
    if (!enabled) return;
    const changed = invalidator(queries, id);
    const handle = openWorkspaceStream(
      {
        url: `${API_BASE}/v1/workspaces/${encodeURIComponent(id)}/events/stream`,
        fetch: (url, init) => fetch(url, init),
        token,
        sleep,
        onEvent: (event) => {
          lastSeen.set(id, event.seq);
          changed();
        },
        onStatus: (next) => {
          setStatus(next);
          if (next.state === "live") changed(); // reconnected: catch up on anything missed
        },
      },
      { lastEventId: lastSeen.get(id) ?? start.current },
    );
    return () => handle.stop();
  }, [id, enabled, token, queries, generation]);
  return { status, restart: () => setGeneration((value) => value + 1) };
}
