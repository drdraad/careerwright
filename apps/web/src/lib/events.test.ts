// @vitest-environment node
import { describe, expect, it } from "vitest";
import type { EventOut } from "@/generated/api";
import { openWorkspaceStream, type StreamStatus } from "./events";

const URL = "/api/v1/workspaces/w1/events/stream";

function event(seq: number): EventOut {
  return {
    seq,
    kind: "profile.version_created",
    subject_id: "w1",
    state: null,
    detail: {},
    created_at: "2027-01-01T00:00:00Z",
  };
}

function frame(e: EventOut): string {
  return `id: ${e.seq}\ndata: ${JSON.stringify(e)}\n\n`;
}

function stream(...chunks: string[]): Response {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk));
      controller.close();
    },
  });
  return new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function envelope(status: number, code: string): Response {
  return new Response(
    JSON.stringify({
      error: { code, message: "m", retryable: false, stage: "request", correlation_id: "c" },
    }),
    { status, headers: { "content-type": "application/json" } },
  );
}

type Call = { url: string; headers: Record<string, string> };

/** Scripted transport: each fetch takes the next response; the script ends by blocking. */
function harness(
  script: Array<Response | Error>,
  tokens: Array<string | null> = [],
  now: () => number = () => 0,
) {
  const calls: Call[] = [];
  const statuses: StreamStatus[] = [];
  const events: number[] = [];
  const sleeps: number[] = [];
  const refreshes: boolean[] = [];
  let token = 0;
  let done!: () => void;
  const finished = new Promise<void>((resolve) => {
    done = resolve;
  });
  const handle = openWorkspaceStream({
    url: URL,
    fetch: async (url, init) => {
      calls.push({ url, headers: { ...(init.headers as Record<string, string>) } });
      const next = script.shift();
      if (next === undefined) {
        done();
        return new Promise<Response>((_, reject) => {
          init.signal?.addEventListener("abort", () => reject(new DOMException("", "AbortError")));
        });
      }
      if (next instanceof Error) throw next;
      return next;
    },
    token: async (force) => {
      refreshes.push(force);
      if (!force) return "t0";
      const next = tokens[token++];
      return next === undefined ? `t${token}` : next;
    },
    sleep: async (ms) => {
      sleeps.push(ms);
    },
    onEvent: (e) => events.push(e.seq),
    onStatus: (s) => {
      statuses.push(s);
      if (s.state === "stopped") done();
    },
    now,
  });
  return { calls, statuses, events, sleeps, refreshes, handle, finished };
}

describe("[DUR-03][STATE-07] the workspace event stream resumes and re-authenticates", () => {
  it("delivers events and, when the stream drops, resumes after the last event it saw", async () => {
    const h = harness([stream("retry: 2000\n\n", frame(event(4)), frame(event(5)))]);
    await h.finished;
    h.handle.stop();

    expect(h.events).toEqual([4, 5]);
    expect(h.calls[0]?.headers["Last-Event-ID"]).toBeUndefined();
    expect(h.calls[0]?.headers.Authorization).toBe("Bearer t0");
    expect(h.calls[1]?.headers["Last-Event-ID"]).toBe("5");
    expect(h.sleeps).toEqual([2000]);
    expect(h.statuses.map((s) => s.state)).toContain("live");
  });

  it("starts from a given event so a reopened page does not replay old events", async () => {
    const h = harness([stream(frame(event(9)))]);
    h.handle.stop();
    const resumed = openWorkspaceStream(
      {
        url: URL,
        fetch: async (_url, init) => {
          expect((init.headers as Record<string, string>)["Last-Event-ID"]).toBe("8");
          return new Promise<Response>(() => {});
        },
        token: async () => "t",
        sleep: async () => {},
        onEvent: () => {},
        onStatus: () => {},
      },
      { lastEventId: 8 },
    );
    resumed.stop();
  });

  it("re-authenticates with a refreshed token when told to, without waiting", async () => {
    const h = harness([
      stream(frame(event(1)), "event: reauthenticate\ndata: {}\n\n"),
      stream(frame(event(2))),
    ]);
    await h.finished;
    h.handle.stop();

    expect(h.refreshes.slice(0, 2)).toEqual([false, true]);
    expect(h.calls[1]?.headers.Authorization).toBe("Bearer t1");
    expect(h.calls[1]?.headers["Last-Event-ID"]).toBe("1");
    expect(h.sleeps).toEqual([2000]); // only after the second stream ended, not before re-auth
    expect(h.events).toEqual([1, 2]);
  });

  it("stops when re-authentication finds the user signed out", async () => {
    const h = harness([stream("event: reauthenticate\ndata: {}\n\n")], [null]);
    await h.finished;

    expect(h.statuses.at(-1)).toEqual({ state: "stopped", reason: "signed_out" });
    expect(h.calls).toHaveLength(1);
  });

  it("stops instead of looping when a fresh token is refused again", async () => {
    const h = harness([
      stream("event: reauthenticate\ndata: {}\n\n"),
      stream("event: reauthenticate\ndata: {}\n\n"),
      stream(frame(event(1))),
    ]);
    await h.finished;

    expect(h.statuses.at(-1)).toEqual({ state: "stopped", reason: "reauthentication_failed" });
    expect(h.calls).toHaveLength(2);
  });

  it("re-authenticates again an hour later even if the stream stayed quiet", async () => {
    let clock = 0;
    const h = harness(
      [
        stream("event: reauthenticate\ndata: {}\n\n"),
        stream("event: reauthenticate\ndata: {}\n\n"),
        stream(frame(event(1))),
      ],
      [],
      () => {
        clock += 30 * 60_000; // each reading is half an hour after the last
        return clock;
      },
    );
    await h.finished;
    h.handle.stop();

    expect(h.refreshes.slice(0, 3)).toEqual([false, true, true]);
    expect(h.events).toEqual([1]);
  });

  it("refreshes once on 401, then stops if the API still refuses the token", async () => {
    const h = harness([envelope(401, "UNAUTHENTICATED"), envelope(401, "UNAUTHENTICATED")]);
    await h.finished;

    expect(h.refreshes).toEqual([false, true]);
    expect(h.statuses.at(-1)).toEqual({
      state: "stopped",
      reason: "reauthentication_failed",
      code: "UNAUTHENTICATED",
    });
  });

  it.each([
    ["stream_ended", 'event: stream_ended\ndata: {"code": "NOT_INVITED"}\n\n', "NOT_INVITED"],
    ["404", envelope(404, "NOT_FOUND"), "NOT_FOUND"],
    ["403", envelope(403, "NOT_INVITED"), "NOT_INVITED"],
  ])("ends for good when access ends (%s)", async (_name, answer, code) => {
    const h = harness([typeof answer === "string" ? stream(answer) : answer, stream()]);
    await h.finished;

    expect(h.statuses.at(-1)).toEqual({ state: "stopped", reason: "access_ended", code });
    expect(h.calls).toHaveLength(1);
  });

  it("backs off on transport failures, bounded, and resets after a good connection", async () => {
    const h = harness([
      new TypeError("network"),
      new Response(null, { status: 502 }),
      new TypeError("network"),
      new TypeError("network"),
      new TypeError("network"),
      new TypeError("network"),
      stream(frame(event(3))),
      new TypeError("network"),
    ]);
    await h.finished;
    h.handle.stop();

    expect(h.sleeps).toEqual([2000, 4000, 8000, 16000, 30000, 30000, 2000, 4000]);
    expect(h.statuses).toContainEqual({ state: "reconnecting", attempt: 5, delayMs: 30000 });
  });

  it("backs off, keeping the refresh pending, while sign-in itself is unreachable", async () => {
    const calls: Call[] = [];
    const refreshes: boolean[] = [];
    const sleeps: number[] = [];
    let failures = 2;
    let done!: () => void;
    const finished = new Promise<void>((resolve) => {
      done = resolve;
    });
    const handle = openWorkspaceStream({
      url: URL,
      fetch: async (url, init) => {
        calls.push({ url, headers: { ...(init.headers as Record<string, string>) } });
        if (calls.length === 1) return stream("event: reauthenticate\ndata: {}\n\n");
        done();
        return new Promise<Response>(() => {});
      },
      token: async (force) => {
        refreshes.push(force);
        if (force && failures-- > 0) throw new Error("auth/network-request-failed");
        return force ? "fresh" : "t0";
      },
      sleep: async (ms) => {
        sleeps.push(ms);
      },
      onEvent: () => {},
      onStatus: () => {},
    });
    await finished;
    handle.stop();

    expect(refreshes).toEqual([false, true, true, true]);
    expect(sleeps).toEqual([2000, 4000]);
    expect(calls[1]?.headers.Authorization).toBe("Bearer fresh");
  });

  it("stops cleanly and makes no further request after stop()", async () => {
    const h = harness([]);
    await h.finished;
    h.handle.stop();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(h.calls).toHaveLength(1);
    expect(h.statuses.at(-1)).toEqual({ state: "stopped", reason: "closed" });
  });
});
