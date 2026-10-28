"use client";
// Server state (TanStack Query) over the generated client. Every workspace-scoped query shares
// the `["ws", id]` prefix, so a status event refetches exactly what that workspace shows.
import { type QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import {
  type ChooseTarget,
  type CreateWorkspace,
  chooseTarget,
  createWorkspace,
  type DecideTurn,
  type DecisionResult,
  type DiscoveryOut,
  decideTurn,
  type Emphasis,
  EventKind,
  getMe,
  getPreferences,
  getProfile,
  getSketch,
  getSlate,
  getTurnReply,
  getWorkspace,
  listCredentials,
  listDiscoveries,
  listSources,
  listTurns,
  listWorkspaces,
  type PartialReplyOut,
  type PreferencesOut,
  type ProfileInput,
  type ProfileOut,
  putPreferences,
  putProfile,
  type RevertProfile,
  revertProfile,
  revokeCredential,
  rotateCredential,
  type SetPreferences,
  type SketchOut,
  type SlateOut,
  type SourceOut,
  type StoreKeyWritable,
  type SubmitDiscovery,
  type SubmitTurn,
  type SupportNoteOut,
  type SupportResponseOut,
  storeCredential,
  submitDiscovery,
  submitTurn,
  type TurnOut,
  type TurnSubmittedOut,
} from "@/generated/api";
import { API_BASE, ApiError, ChangeKeys } from "./api";
import { openWorkspaceStream, type StreamStatus } from "./events";

const PAGE = 200; // the API's maximum page size

export const keys = {
  me: ["me"] as const,
  workspaces: ["workspaces"] as const,
  workspace: (id: string) => ["ws", id, "workspace"] as const,
  profile: (id: string) => ["ws", id, "profile"] as const,
  sources: (id: string) => ["ws", id, "sources"] as const,
  scope: (id: string) => ["ws", id] as const,
  /** A turn's streamed reply (`GET .../interview/turns/{id}/reply`). */
  turnReply: (id: string, turnId: string) =>
    ["ws", id, "interview", "turns", turnId, "reply"] as const,
  turns: (id: string) => ["ws", id, "interview", "turns"] as const,
  preferences: (id: string) => ["ws", id, "interview", "preferences"] as const,
  latestDiscovery: (id: string) => ["ws", id, "discoveries", "latest"] as const,
  slate: (id: string, discoveryId: string, controls: SlateControls) =>
    ["ws", id, "discoveries", discoveryId, "slate", controls] as const,
  sketch: (id: string) => ["ws", id, "sketch"] as const,
  credentials: (id: string) => ["ws", id, "credentials"] as const,
};

/** The slate's view controls: never stored, never limits (ADR 0007 decision 5). */
export type SlateControls = {
  emphasis: Emphasis;
  excludeConcepts: string[];
  excludeFamilies: string[];
};

/** An access failure is final for this page; retrying cannot help. */
function retryable(failures: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false;
  return failures < 2;
}

type Load = { isError: boolean; data: unknown };

/** A first load failed: there is nothing to show, so the failure takes the page. */
export function firstLoadFailed(...loads: Load[]): boolean {
  return loads.some((load) => load.isError && load.data === undefined);
}

/** A refresh failed after a first load: what was last loaded stays on screen, marked. */
export function refreshFailed(...loads: Load[]): boolean {
  return loads.some((load) => load.isError && load.data !== undefined);
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

/**
 * A consequential command (Global Constraint 7): a retry of the same request reuses its
 * idempotency key, and success refreshes everything the workspace shows.
 */
function useCommand<Vars, Result>(
  id: string,
  send: (vars: Vars, idempotencyKey: string) => Promise<Result>,
) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: (vars: Vars) => send(vars, changes.keyFor(vars)),
    onSuccess: () => {
      changes.settled();
      return queries.invalidateQueries({ queryKey: keys.scope(id) });
    },
  });
}

const path = (id: string) => ({ workspace_id: id });

export function usePreferences(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.preferences(id),
    queryFn: async () => (await getPreferences({ path: path(id), throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

export function useSetPreferences(id: string) {
  return useCommand(
    id,
    async (body: SetPreferences, key: string) =>
      (
        await putPreferences({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as PreferencesOut,
  );
}

/** Every turn, oldest first (a conversation is never silently truncated). */
export function useTurns(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.turns(id),
    queryFn: async (): Promise<TurnOut[]> =>
      (
        await allPages(
          async (query) => (await listTurns({ path: path(id), query, throwOnError: true })).data,
        )
      ).reverse(),
    retry: retryable,
    enabled,
  });
}

/** A running turn's reply so far; refreshed by its `run.partial_updated` events. */
export function useTurnReply(id: string, turnId: string, enabled = true) {
  return useQuery({
    queryKey: keys.turnReply(id, turnId),
    queryFn: async (): Promise<PartialReplyOut> =>
      (
        await getTurnReply({
          path: { workspace_id: id, turn_id: turnId },
          throwOnError: true,
        })
      ).data,
    retry: retryable,
    enabled,
  });
}

/** A sent turn (with the support note when the message used a risk word), or, for first-
 *  person acute distress, the support response instead of sending (ADR 0007 decision 7). */
export type Submitted =
  | { kind: "turn"; turn: TurnSubmittedOut }
  | { kind: "support"; support: SupportResponseOut };

export function useSubmitTurn(id: string) {
  return useCommand(id, async (body: SubmitTurn, key: string): Promise<Submitted> => {
    const { data } = await submitTurn({
      path: path(id),
      body,
      headers: { "Idempotency-Key": key },
      throwOnError: true,
    });
    return "turn_id" in data ? { kind: "turn", turn: data } : { kind: "support", support: data };
  });
}

export type Decide = { turnId: string; body: DecideTurn };

export function useDecideTurn(id: string) {
  return useCommand(
    id,
    async ({ turnId, body }: Decide, key: string) =>
      (
        await decideTurn({
          path: { workspace_id: id, turn_id: turnId },
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as DecisionResult,
  );
}

/** Sending a message: a turn, or the support response for it. The support response is kept
 *  with the message it answered, so "send it anyway" sends that message, not whatever is in
 *  the reply field now. Resolves whether a turn was sent. */
export function useSendMessage(id: string) {
  const submit = useSubmitTurn(id);
  const [support, setSupport] = useState<{
    response: SupportResponseOut;
    message: string;
  } | null>(null);
  // The support note beside a sent message that used a risk word; kept until dismissed or
  // the next message is sent. It is never stored.
  const [note, setNote] = useState<SupportNoteOut | null>(null);
  const send = async (body: SubmitTurn): Promise<boolean> => {
    const sent = await submit.mutateAsync(body).catch(() => null);
    if (sent === null) return false;
    if (sent.kind === "support") {
      setSupport({ response: sent.support, message: body.message });
      return false;
    }
    setSupport(null);
    setNote(sent.turn.support_note);
    return true;
  };
  return {
    send,
    support,
    note,
    dismissNote: () => setNote(null),
    pending: submit.isPending,
    error: submit.error,
  };
}
export type MessageSender = ReturnType<typeof useSendMessage>;

/** Undo: an earlier version's answers, each with its own source, as a new version. */
export function useRevertProfile(id: string) {
  return useCommand(
    id,
    async (body: RevertProfile, key: string) =>
      (
        await revertProfile({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as ProfileOut,
  );
}

/** The newest discovery, or null if none has been asked for. */
export function useLatestDiscovery(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.latestDiscovery(id),
    queryFn: async (): Promise<DiscoveryOut | null> =>
      (await listDiscoveries({ path: path(id), query: { limit: 1 }, throwOnError: true })).data
        .items[0] ?? null,
    retry: retryable,
    enabled,
  });
}

export function useSubmitDiscovery(id: string) {
  return useCommand(
    id,
    async (body: SubmitDiscovery, key: string) =>
      (
        await submitDiscovery({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as DiscoveryOut,
  );
}

export function useSlate(id: string, discoveryId: string, controls: SlateControls, enabled = true) {
  return useQuery({
    queryKey: keys.slate(id, discoveryId, controls),
    queryFn: async (): Promise<SlateOut> =>
      (
        await getSlate({
          path: { workspace_id: id, discovery_id: discoveryId },
          query: {
            emphasis: controls.emphasis,
            exclude_concept: controls.excludeConcepts,
            exclude_family: controls.excludeFamilies,
          },
          throwOnError: true,
        })
      ).data,
    retry: retryable,
    placeholderData: (previous) => previous, // keep the last slate readable while it refreshes
    enabled,
  });
}

export function useChooseTarget(id: string) {
  return useCommand(
    id,
    async (body: ChooseTarget, key: string) =>
      (
        await chooseTarget({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as ProfileOut,
  );
}

export function useSketch(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.sketch(id),
    queryFn: async (): Promise<SketchOut> =>
      (await getSketch({ path: path(id), throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

export function useCredentials(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.credentials(id),
    queryFn: async () => (await listCredentials({ path: path(id), throwOnError: true })).data.items,
    retry: retryable,
    enabled,
  });
}

export type KeyChange =
  | { action: "store"; body: StoreKeyWritable }
  | { action: "rotate"; credentialId: string; body: StoreKeyWritable }
  | { action: "revoke"; credentialId: string };

/** Store, rotate or revoke the workspace's Meta key. The key is sent once and never read. */
export function useKeyChange(id: string) {
  return useCommand(id, async (change: KeyChange, key: string) => {
    const headers = { "Idempotency-Key": key };
    if (change.action === "store") {
      return (
        await storeCredential({ path: path(id), body: change.body, headers, throwOnError: true })
      ).data;
    }
    const credential = { workspace_id: id, credential_id: change.credentialId };
    if (change.action === "rotate") {
      return (
        await rotateCredential({ path: credential, body: change.body, headers, throwOnError: true })
      ).data;
    }
    return (await revokeCredential({ path: credential, headers, throwOnError: true })).data;
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

/**
 * The last event each workspace's stream received on this page, per signed-in session, for a
 * remounted stream: a different account signing in on the same page starts from its own read.
 */
const lastSeen = new Map<string, number>();

export type WorkspaceEvents = { status: StreamStatus; restart(): void };

type EventsOptions = {
  enabled: boolean;
  /** The workspace's `last_event_seq`, read with the workspace. */
  startAfter: number | undefined;
  /** The signed-in user's ID token (`useAuth().token`). */
  token: (forceRefresh: boolean) => Promise<string | null>;
  /** Who is signed in (their account ID), so one session never resumes another's stream. */
  session: string;
};

/**
 * Subscribes to the workspace's status events while mounted. A stream opened again on this
 * page, by the same session, resumes after the last event it saw; otherwise it starts after
 * `startAfter`, so nothing is replayed and nothing after that read is missed.
 */
export function useWorkspaceEvents(
  id: string,
  { enabled, startAfter, token, session }: EventsOptions,
): WorkspaceEvents {
  const seen = `${session}:${id}`;
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
          lastSeen.set(seen, event.seq);
          if (event.kind === EventKind.RUN_PARTIAL_UPDATED) {
            // A streamed reply moved (up to a few times a second): only that turn's reply.
            void queries.invalidateQueries({ queryKey: keys.turnReply(id, event.subject_id) });
            return;
          }
          changed();
        },
        onStatus: (next) => {
          setStatus(next);
          if (next.state === "live") changed(); // reconnected: catch up on anything missed
        },
      },
      { lastEventId: lastSeen.get(seen) ?? start.current },
    );
    return () => handle.stop();
  }, [id, seen, enabled, token, queries, generation]);
  return { status, restart: () => setGeneration((value) => value + 1) };
}
