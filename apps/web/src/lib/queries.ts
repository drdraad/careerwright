"use client";
// Server state (TanStack Query) over the generated client. Every workspace-scoped query shares
// the `["ws", id]` prefix, so a status event refetches exactly what that workspace shows.
import {
  type QueryClient,
  useMutation,
  useMutationState,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  type ChooseClosest,
  type ChooseRole,
  type ChooseTarget,
  type CreateWorkspace,
  chooseClosest,
  chooseRole,
  chooseTarget,
  createWorkspace,
  type DecideTurn,
  type DecisionSavedOut,
  type DiscoveryOut,
  decideTurn,
  type Emphasis,
  EventKind,
  type ExplanationRunOut,
  estimateRun,
  getMe,
  getOrigin,
  getPreferences,
  getProfile,
  getSketch,
  getSlate,
  getSpend,
  getTitleDetails,
  getTurnReply,
  getWorkspace,
  listCredentials,
  listDiscoveries,
  listSources,
  listTargets,
  listTurns,
  listWorkspaces,
  matchTitles,
  type NameRole,
  type NoJobYet,
  nameRole,
  noJobYet,
  type OriginOut,
  type PartialReplyOut,
  type PreferencesOut,
  type ProfileInput,
  type ProfileOut,
  type ProfileSavedOut,
  putPreferences,
  putProfile,
  putSpendLimits,
  putTitleDetails,
  type RevertProfile,
  type RunKind,
  revertProfile,
  revokeCredential,
  rotateCredential,
  type SetPreferences,
  type SetSpendLimits,
  type SetTitleDetails,
  type SketchOut,
  type SlateOut,
  type SourceOut,
  type SpendOut,
  type StoreKeyWritable,
  type SubmitDiscovery,
  type SubmitExplanation,
  type SubmitTurn,
  type SupportNoteOut,
  storeCredential,
  submitDiscovery,
  submitExplanation,
  submitTurn,
  type TargetRecordsOut,
  type TitleDetailsListOut,
  type TitleDetailsSavedOut,
  type TitleMatchesOut,
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
  /** The requests for a discovery's written note (mutations, kept for the page's life). */
  noteRequests: (id: string, discoveryId: string) =>
    ["ws", id, "discoveries", discoveryId, "note-requests"] as const,
  sketch: (id: string) => ["ws", id, "sketch"] as const,
  targets: (id: string) => ["ws", id, "targets"] as const,
  origin: (id: string) => ["ws", id, "origin"] as const,
  titleDetails: (id: string) => ["ws", id, "profile", "titles"] as const,
  credentials: (id: string) => ["ws", id, "credentials"] as const,
  spend: (id: string) => ["ws", id, "spend"] as const,
  estimate: (id: string, kind: RunKind) => ["ws", id, "spend", "estimate", kind] as const,
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
      ).data as ProfileSavedOut,
    onSuccess: ({ support_note: _shownBesideTheForm, ...saved }) => {
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
  /** Kept in the query client under this key for the page's life, never collected. */
  kept?: readonly unknown[],
) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    ...(kept === undefined ? {} : { mutationKey: kept, gcTime: Number.POSITIVE_INFINITY }),
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

/** This workspace's model spending this month and its limits (MODEL-10). */
export function useSpend(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.spend(id),
    queryFn: async () => (await getSpend({ path: path(id), throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

export function useSetSpendLimits(id: string) {
  return useCommand(
    id,
    async (body: SetSpendLimits, key: string) =>
      (
        await putSpendLimits({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as SpendOut,
  );
}

/** What one run of `kind` may cost, before the person starts it (spec section 16). */
export function useRunEstimate(id: string, kind: RunKind, enabled = true) {
  return useQuery({
    queryKey: keys.estimate(id, kind),
    queryFn: async () =>
      (await estimateRun({ path: path(id), query: { kind }, throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
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

/** A sent turn, with the support panel when its message holds a risk stem (ADR 0007
 *  decision 7). */
export function useSubmitTurn(id: string) {
  return useCommand(
    id,
    async (body: SubmitTurn, key: string): Promise<TurnSubmittedOut> =>
      (
        await submitTurn({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data,
  );
}

export type Decide = { turnId: string; body: DecideTurn };

/** A turn's decision. Answers typed in the review step go through the support screen, so the
 *  result (or the refusal's `ApiError`) may carry the calm panel; it is never stored. */
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
      ).data as DecisionSavedOut,
  );
}

/** Sending a message. Resolves whether a turn was sent. */
export function useSendMessage(id: string) {
  const submit = useSubmitTurn(id);
  // The support panel the API sent with the last attempt, whether the message was sent or
  // refused; kept until dismissed or the next attempt. It is never stored.
  const [support, setSupport] = useState<{ note: SupportNoteOut; sent: boolean } | null>(null);
  const send = async (body: SubmitTurn): Promise<boolean> => {
    try {
      const sent = await submit.mutateAsync(body);
      setSupport(sent.support_note === null ? null : { note: sent.support_note, sent: true });
      return true;
    } catch (error) {
      const note = error instanceof ApiError ? error.supportNote : null;
      setSupport(note === null ? null : { note, sent: false });
      return false;
    }
  };
  return {
    send,
    support,
    dismissNote: () => setSupport(null),
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

/** Asks for a slate's one written explanation (ADR 0007 decision 12). Asking again, from any
 *  view, answers with the same run: a slate never has a second call. */
/**
 * Asking for a slate's written note (S2.7, ADR 0007 decision 12). Every request for a
 * discovery is kept in the query client for the page's life, so whether the note was asked
 * for, and the last refusal, outlive the slate: changing view or chapter never asks again. A
 * refused request is sent again only by the person's click (`askAgain`).
 */
export function useNoteRequests(id: string, discoveryId: string) {
  const queries = useQueryClient();
  const kept = keys.noteRequests(id, discoveryId);
  const submit = useCommand(
    id,
    async (body: SubmitExplanation, key: string) =>
      (
        await submitExplanation({
          path: { workspace_id: id, discovery_id: discoveryId },
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as ExplanationRunOut,
    kept,
  );
  const last = useMutationState({
    filters: { mutationKey: kept, exact: true },
    select: (request) => request.state,
  }).at(-1);
  const ask = submit.mutate;
  // Unless this page already asked for this discovery's note: read from the cache at the
  // moment of asking, so a slate that shows twice at once still asks once.
  const askOnce = useCallback(
    (body: SubmitExplanation) => {
      const asked = queries.getMutationCache().findAll({
        mutationKey: keys.noteRequests(id, discoveryId),
        exact: true,
      });
      if (asked.length === 0) ask(body);
    },
    [queries, id, discoveryId, ask],
  );
  return {
    askOnce,
    askAgain: ask,
    asked: last !== undefined,
    sending: last?.status === "pending",
    error: last?.status === "error" ? last.error : null,
  };
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

/** Words worth matching: a letter or a digit (the API refuses anything else). */
const searchable = (text: string) => /[\p{L}\p{N}]/u.test(text);

/** The first question's type-ahead (`GET /v1/taxonomy/titles`): ESCO's titles and the UK
 *  job-title index's, deterministic and offline, so it works without a key and in the demo.
 *  The pinned releases never change while the page is open. An earlier list is never kept
 *  while the next loads: it would stand for words it wasn't found for (design review I-1). */
export function useTitleMatches(typed: string, limit: number) {
  const q = typed.trim();
  return useQuery({
    queryKey: ["titles", q, limit] as const,
    queryFn: async ({ signal }): Promise<TitleMatchesOut> =>
      (await matchTitles({ query: { q, limit }, signal, throwOnError: true })).data,
    enabled: searchable(q),
    staleTime: Number.POSITIVE_INFINITY,
    retry: retryable,
  });
}

/** The world's answer to the first question (`GET .../origin`), computed with no model call. */
export function useOrigin(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.origin(id),
    queryFn: async (): Promise<OriginOut> =>
      (await getOrigin({ path: path(id), throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

/** The person's own details beside their role and each target (`GET .../profile/titles`). */
export function useTitleDetails(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.titleDetails(id),
    queryFn: async (): Promise<TitleDetailsListOut> =>
      (await getTitleDetails({ path: path(id), throwOnError: true })).data,
    retry: retryable,
    enabled,
  });
}

/** Saving a title's details: seniority, industry and the skills marked not part of the job.
 *  Its words go through the support screen, so the result (or the refusal's `ApiError`) may
 *  carry the calm panel; it is never stored. */
export function useSaveTitleDetails(id: string) {
  return useCommand(
    id,
    async (body: SetTitleDetails, key: string) =>
      (
        await putTitleDetails({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as TitleDetailsSavedOut,
  );
}

/** The first answer: an ESCO occupation the person picked from the type-ahead. */
export function useChooseRole(id: string) {
  return useCommand(
    id,
    async (body: ChooseRole, key: string) =>
      (
        await chooseRole({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as ProfileOut,
  );
}

/** The first answer in the person's own words: a UK job title, or anything typed. */
export function useNameRole(id: string) {
  return useCommand(
    id,
    async (body: NameRole, key: string) =>
      (
        await nameRole({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as ProfileOut,
  );
}

/** The first answer "I haven't had a job yet" (Task 6f): an answer about the current role,
 *  never a job title, Skipped or Unknown. */
export function useNoJobYet(id: string) {
  return useCommand(
    id,
    async (body: NoJobYet, key: string) =>
      (
        await noJobYet({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as ProfileOut,
  );
}

/** "Which of these is closest?": an occupation offered, or null for "None of these is my job". */
export function useChooseClosest(id: string) {
  return useCommand(
    id,
    async (body: ChooseClosest, key: string) =>
      (
        await chooseClosest({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data as ProfileOut,
  );
}

/** Each target as it is stored once, with what it names and its coverage: every view that
 *  asks which occupation a target is reads this, never the title (Task 6d slice A). */
export function useTargets(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.targets(id),
    queryFn: async (): Promise<TargetRecordsOut> =>
      (await listTargets({ path: path(id), throwOnError: true })).data,
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
