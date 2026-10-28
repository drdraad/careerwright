import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import type { WorkspaceOut } from "@/generated/api";
import { client } from "@/generated/api/client.gen";
import { configureApiClient } from "./api";
import { useCreateWorkspace, useWorkspaces } from "./queries";

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
