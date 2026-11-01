import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceOut } from "@/generated/api";
import { client } from "@/generated/api/client.gen";
import { configureApiClient } from "./api";
import {
  firstLoadFailed,
  keys,
  refreshFailed,
  useCreateWorkspace,
  useWorkspaceEvents,
  useWorkspaces,
} from "./queries";

function workspace(n: number): WorkspaceOut {
  return {
    workspace_id: `w${n}`,
    name: `Workspace ${n}`,
    data_mode: "demo",
    synthetic: true,
    fixture: false,
    version: 1,
    last_event_seq: 1,
    created_at: "2027-01-01T00:00:00Z",
    updated_at: "2027-01-01T00:00:00Z",
  };
}

function wrapper({ children }: { children: ReactNode }) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queries}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  configureApiClient(async () => "token");
  client.setConfig({ baseUrl: "http://localhost:3000/api" });
});

describe("[API-01] creating a workspace is idempotent across a retry", () => {
  it("sends the same key when the same submission is retried after a failure", async () => {
    const sentKeys: Array<string | null> = [];
    let attempts = 0;
    client.setConfig({
      fetch: async (input: RequestInfo | URL) => {
        sentKeys.push((input as Request).headers.get("Idempotency-Key"));
        attempts += 1;
        if (attempts === 1) throw new TypeError("network");
        return new Response(JSON.stringify(workspace(9)), {
          status: 201,
          headers: { "content-type": "application/json" },
        });
      },
    });
    const { result } = renderHook(() => useCreateWorkspace(), { wrapper });
    const body = { name: "Leeds plan", data_mode: "demo", synthetic: true } as const;

    await expect(result.current.mutateAsync(body)).rejects.toBeDefined();
    await result.current.mutateAsync({ ...body });

    expect(sentKeys).toHaveLength(2);
    expect(sentKeys[0]).toBe(sentKeys[1]);
  });
});

describe("[API-01] the workspace list is never silently truncated", () => {
  it("follows next_cursor until every page is read", async () => {
    const cursors: Array<string | null> = [];
    client.setConfig({
      fetch: async (input: RequestInfo | URL) => {
        const cursor = new URL((input as Request).url).searchParams.get("cursor");
        cursors.push(cursor);
        const page =
          cursor === null
            ? { items: [workspace(1), workspace(2)], next_cursor: "c2" }
            : { items: [workspace(3)], next_cursor: null };
        return new Response(JSON.stringify(page), {
          headers: { "content-type": "application/json" },
        });
      },
    });

    const { result } = renderHook(() => useWorkspaces(true), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.map((w) => w.workspace_id)).toEqual(["w1", "w2", "w3"]);
    expect(cursors).toEqual([null, "c2"]);
  });
});

describe("[STATE-07][UI-09] a failed first load and a failed refresh are told apart", () => {
  const loaded = { isError: false, data: workspace(1) };
  const refreshFailedAfterLoad = { isError: true, data: workspace(1) };
  const neverLoaded = { isError: true, data: undefined };

  it("replaces the page only when a first load failed", () => {
    expect(firstLoadFailed(loaded, neverLoaded)).toBe(true);
    expect(firstLoadFailed(loaded, refreshFailedAfterLoad)).toBe(false);
    expect(firstLoadFailed(loaded, { isError: false, data: undefined })).toBe(false);
  });

  it("says 'showing what was last loaded' only when something was loaded", () => {
    expect(refreshFailed(loaded, refreshFailedAfterLoad)).toBe(true);
    expect(refreshFailed(loaded, neverLoaded)).toBe(false);
    expect(refreshFailed(loaded)).toBe(false);
  });
});

/** An open event stream: the given frames, then it stays open until the page closes it. */
function openStream(frames: string): Response {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(frames));
    },
  });
  return new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function eventFrame(seq: number, workspaceId: string, kind = "profile.version_created"): string {
  const event = {
    seq,
    kind,
    subject_id: workspaceId,
    state: null,
    detail: {},
    created_at: "2027-01-01T00:00:00Z",
  };
  return `id: ${seq}\ndata: ${JSON.stringify(event)}\n\n`;
}

describe("[STATE-07][DUR-03] a workspace's stream on one page", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("resumes after the last event it saw when it is opened again, not from the workspace read", async () => {
    const id = "w-remount";
    const sent: Array<string | null> = [];
    vi.stubGlobal("fetch", async (_url: string, init: RequestInit) => {
      sent.push(new Headers(init.headers).get("Last-Event-ID"));
      return openStream(`retry: 1000\n\n${eventFrame(5, id)}`);
    });
    const options = { enabled: true, startAfter: 2, token: async () => "token", session: "ada" };

    const first = renderHook(() => useWorkspaceEvents(id, options), { wrapper });
    await waitFor(() => expect(first.result.current.status.state).toBe("live"));
    await waitFor(() => expect(sent).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 20)); // the event is read
    first.unmount();
    renderHook(() => useWorkspaceEvents(id, options), { wrapper });

    await waitFor(() => expect(sent).toHaveLength(2));
    expect(sent).toEqual(["2", "5"]);
  });

  it("never resumes another signed-in session's place in the stream", async () => {
    const id = "w-sessions";
    const sent: Array<string | null> = [];
    vi.stubGlobal("fetch", async (_url: string, init: RequestInit) => {
      sent.push(new Headers(init.headers).get("Last-Event-ID"));
      return openStream(`retry: 1000\n\n${eventFrame(9, id)}`);
    });
    const ada = { enabled: true, startAfter: 2, token: async () => "token", session: "ada" };

    const first = renderHook(() => useWorkspaceEvents(id, ada), { wrapper });
    await waitFor(() => expect(first.result.current.status.state).toBe("live"));
    await new Promise((resolve) => setTimeout(resolve, 20)); // the event is read
    first.unmount();
    renderHook(() => useWorkspaceEvents(id, { ...ada, session: "ben", startAfter: 3 }), {
      wrapper,
    });

    await waitFor(() => expect(sent).toHaveLength(2));
    expect(sent).toEqual(["2", "3"]); // Ben starts from his own read, not Ada's last event
  });

  it("refreshes only the turn's reply on a streamed-reply event, not the whole workspace", async () => {
    const id = "w-partial";
    const turn = "t-1";
    vi.stubGlobal("fetch", async () => {
      // The event arrives after the stream's own catch-up refresh has gone out.
      const body = new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new TextEncoder().encode("retry: 1000\n\n"));
          setTimeout(() => {
            const frame = eventFrame(7, id, "run.partial_updated").replace(`"${id}"`, `"${turn}"`);
            controller.enqueue(new TextEncoder().encode(frame));
          }, 120);
        },
      });
      return new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } });
    });
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidated: unknown[] = [];
    vi.spyOn(queries, "invalidateQueries").mockImplementation(async (filters) => {
      invalidated.push(filters?.queryKey);
    });
    const own = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queries}>{children}</QueryClientProvider>
    );
    const options = { enabled: true, startAfter: 0, token: async () => "token", session: "ada" };

    renderHook(() => useWorkspaceEvents(id, options), { wrapper: own });

    await waitFor(() => expect(invalidated).toContainEqual(keys.turnReply(id, turn)));
    await new Promise((resolve) => setTimeout(resolve, 100)); // any coalesced refresh is out
    // The workspace was refreshed once, when the stream went live; the event added nothing.
    expect(
      invalidated.filter((key) => JSON.stringify(key) === JSON.stringify(keys.scope(id))),
    ).toHaveLength(1);
  });

  it("says it is connecting again as soon as Reconnect opens a new stream", async () => {
    vi.stubGlobal(
      "fetch",
      async () =>
        new Response(JSON.stringify({ error: { code: "NOT_FOUND" } }), {
          status: 404,
          headers: { "content-type": "application/json" },
        }),
    );
    const options = { enabled: true, startAfter: 0, token: async () => "token", session: "ada" };
    const { result } = renderHook(() => useWorkspaceEvents("w-restart", options), { wrapper });
    await waitFor(() => expect(result.current.status.state).toBe("stopped"));

    vi.stubGlobal("fetch", () => new Promise<Response>(() => {}));
    act(() => result.current.restart());

    expect(result.current.status.state).toBe("connecting");
  });
});
