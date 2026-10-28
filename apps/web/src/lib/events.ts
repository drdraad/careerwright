// The workspace status-event stream (DUR-03, STATE-07): resumable, and re-authenticating
// rather than looping.
//
// - Every reconnect sends `Last-Event-ID`, so the server resumes after the last event this
//   page saw and nothing is missed (sequence numbers increase in commit order).
// - `event: reauthenticate` (the token expired) reconnects at once with a force-refreshed
//   token. If the refresh finds the user signed out, or the fresh token is refused again
//   before anything arrives, the stream stops and says why; it never retries a dead token.
// - When access ends (`stream_ended`, or a 403/404 envelope) it stops for good.
// - Transport failures (the API or the web server restarting) back off: the server's retry
//   interval, doubling, capped at 30 s; a good connection resets it.
//
// Events only tell the page what to refetch; the API's resources stay authoritative.
import type { ErrorCode, EventOut } from "@/generated/api";
import { SseParser } from "./sse";

export type StopReason = "signed_out" | "access_ended" | "reauthentication_failed" | "closed";

export type StreamStatus =
  | { state: "connecting" }
  | { state: "live" }
  | { state: "reconnecting"; attempt: number; delayMs: number }
  | { state: "stopped"; reason: StopReason; code?: ErrorCode };

export type StreamDeps = {
  url: string;
  fetch: (url: string, init: RequestInit) => Promise<Response>;
  /** The current ID token, or a freshly issued one when `forceRefresh`; null if signed out. */
  token: (forceRefresh: boolean) => Promise<string | null>;
  sleep: (ms: number, signal: AbortSignal) => Promise<void>;
  onEvent: (event: EventOut) => void;
  onStatus: (status: StreamStatus) => void;
  now?: () => number;
};

export type StreamHandle = { stop(): void; lastEventId(): number | undefined };

const DEFAULT_RETRY_MS = 2000;
// The server's `retry:` value is honoured, but never below this floor.
const MIN_RETRY_MS = 1000;
const MAX_RETRY_MS = 30_000;
// A fresh token that is sent back for re-authentication within this time, with no event in
// between, is not working (a clock or account problem): stop rather than refresh again.
const REAUTH_SETTLE_MS = 10_000;
const ACCESS_ENDED: ReadonlySet<ErrorCode> = new Set<ErrorCode>(["NOT_INVITED", "NOT_FOUND"]);
/**
 * The control events the API's stream sends besides plain messages
 * (backend/src/nessa/api/routes_events.py). They are not in the OpenAPI document, which
 * describes only the `EventOut` messages, so they are named once here.
 */
const STREAM_EVENT = {
  message: "message",
  reauthenticate: "reauthenticate",
  streamEnded: "stream_ended",
} as const;

type Outcome =
  | { kind: "reconnect" } // the stream ended or the transport failed: back off
  | { kind: "reauthenticate"; code?: ErrorCode } // refresh the token, reconnect at once
  | { kind: "stop"; reason: StopReason; code?: ErrorCode };

async function errorCode(response: Response): Promise<ErrorCode | undefined> {
  try {
    const body = (await response.json()) as { error?: { code?: ErrorCode } };
    return body.error?.code;
  } catch {
    return undefined;
  }
}

export function openWorkspaceStream(
  deps: StreamDeps,
  options: { lastEventId?: number } = {},
): StreamHandle {
  const controller = new AbortController();
  let lastEventId = options.lastEventId;
  let retryMs = DEFAULT_RETRY_MS;
  let stopped = false;

  const finish = (status: Extract<StreamStatus, { state: "stopped" }>) => {
    if (stopped) return;
    stopped = true;
    controller.abort();
    deps.onStatus(status);
  };

  // One connection: resolves with what to do next. `live` reports the first bytes through the
  // stream body (so a buffering hop can never pass for live; the backoff starts afresh);
  // `progress` reports an event, which re-authentication waits for.
  async function connect(token: string, live: () => void, progress: () => void): Promise<Outcome> {
    const headers: Record<string, string> = {
      Accept: "text/event-stream",
      Authorization: `Bearer ${token}`,
    };
    if (lastEventId !== undefined) headers["Last-Event-ID"] = String(lastEventId);
    let response: Response;
    try {
      response = await deps.fetch(deps.url, {
        headers,
        signal: controller.signal,
        cache: "no-store",
      });
    } catch {
      return { kind: "reconnect" };
    }
    if (response.status === 401) {
      const code = await errorCode(response);
      return code === undefined ? { kind: "reauthenticate" } : { kind: "reauthenticate", code };
    }
    if (!response.ok || response.body === null) {
      const code = await errorCode(response);
      if (code !== undefined && ACCESS_ENDED.has(code)) {
        return { kind: "stop", reason: "access_ended", code };
      }
      return { kind: "reconnect" };
    }
    const parser = new SseParser();
    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let delivering = false;
    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) return { kind: "reconnect" };
        if (!delivering) {
          delivering = true;
          live();
          deps.onStatus({ state: "live" });
        }
        for (const item of parser.push(value)) {
          if (item.type === "retry") {
            retryMs = Math.max(MIN_RETRY_MS, item.ms);
            continue;
          }
          if (item.event === STREAM_EVENT.reauthenticate) return { kind: "reauthenticate" };
          if (item.event === STREAM_EVENT.streamEnded) {
            const code = (JSON.parse(item.data) as { code?: ErrorCode }).code;
            if (code === "UNAUTHENTICATED") return { kind: "reauthenticate", code };
            if (code !== undefined && ACCESS_ENDED.has(code)) {
              return { kind: "stop", reason: "access_ended", code };
            }
            return { kind: "reconnect" };
          }
          if (item.event !== STREAM_EVENT.message) continue;
          const received = JSON.parse(item.data) as EventOut;
          if (item.id !== undefined) lastEventId = Number(item.id);
          progress();
          deps.onEvent(received);
        }
      }
    } catch {
      return { kind: "reconnect" };
    } finally {
      reader.cancel().catch(() => {});
    }
  }

  async function run(): Promise<void> {
    const now = deps.now ?? Date.now;
    let attempt = 0;
    let forceRefresh = false;
    // True after a re-authentication until the new token has proved itself.
    let reauthenticating = false;
    const backOff = async () => {
      attempt += 1;
      const delayMs = Math.min(MAX_RETRY_MS, retryMs * 2 ** (attempt - 1));
      deps.onStatus({ state: "reconnecting", attempt, delayMs });
      await deps.sleep(delayMs, controller.signal);
    };
    while (!stopped) {
      deps.onStatus({ state: "connecting" });
      let token: string | null;
      try {
        token = await deps.token(forceRefresh);
      } catch {
        // Sign-in is unreachable for now (a restart): keep the refresh pending and back off.
        if (stopped) return;
        await backOff();
        continue;
      }
      if (stopped) return;
      if (token === null) return finish({ state: "stopped", reason: "signed_out" });
      forceRefresh = false;
      let delivered = false;
      const opened = now();
      const outcome = await connect(
        token,
        () => {
          attempt = 0;
        },
        () => {
          delivered = true;
          reauthenticating = false;
        },
      );
      if (stopped) return;
      if (now() - opened >= REAUTH_SETTLE_MS) reauthenticating = false;
      if (outcome.kind === "stop") {
        const { reason, code } = outcome;
        return finish(
          code === undefined ? { state: "stopped", reason } : { state: "stopped", reason, code },
        );
      }
      if (outcome.kind === "reauthenticate") {
        if (reauthenticating && !delivered) {
          const { code } = outcome;
          return finish(
            code === undefined
              ? { state: "stopped", reason: "reauthentication_failed" }
              : { state: "stopped", reason: "reauthentication_failed", code },
          );
        }
        reauthenticating = true;
        forceRefresh = true;
        continue;
      }
      await backOff();
    }
  }

  void run();

  return {
    stop: () => finish({ state: "stopped", reason: "closed" }),
    lastEventId: () => lastEventId,
  };
}
