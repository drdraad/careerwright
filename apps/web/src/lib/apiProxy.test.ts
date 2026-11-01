// @vitest-environment node
import { describe, expect, it } from "vitest";
import { forwardToApi } from "./apiProxy";

const API = "http://api:8000";

function recorder(answer: Response | Error) {
  const seen: { url: string; init: RequestInit }[] = [];
  const send = (async (url: URL | RequestInfo, init?: RequestInit) => {
    seen.push({ url: String(url), init: init ?? {} });
    if (answer instanceof Error) throw answer;
    return answer;
  }) as typeof fetch;
  return { seen, send };
}

describe("[BND1-13] the web origin forwards API calls without weakening the API's checks", () => {
  it("forwards the browser's Origin unchanged and only the contract's headers", async () => {
    const { seen, send } = recorder(
      new Response("{}", { status: 201, headers: { "content-type": "application/json" } }),
    );
    const request = new Request("http://127.0.0.1:53000/api/v1/workspaces/w1/profile?x=1", {
      method: "PUT",
      headers: {
        Origin: "http://evil.example",
        Authorization: "Bearer t",
        "Idempotency-Key": "k",
        "Content-Type": "application/json",
        Cookie: "session=1",
        "X-Forwarded-For": "8.8.8.8",
        Host: "127.0.0.1:53000",
      },
      body: '{"a":1}',
    });

    const response = await forwardToApi(request, ["v1", "workspaces", "w1", "profile"], API, send);

    expect(response.status).toBe(201);
    expect(seen[0]?.url).toBe("http://api:8000/v1/workspaces/w1/profile?x=1");
    const sent = new Headers(seen[0]?.init.headers);
    expect(Object.fromEntries(sent)).toEqual({
      authorization: "Bearer t",
      "content-type": "application/json",
      "idempotency-key": "k",
      origin: "http://evil.example",
    });
    expect(new TextDecoder().decode(seen[0]?.init.body as ArrayBuffer)).toBe('{"a":1}');
  });

  it("never adds an Origin the browser did not send", async () => {
    const { seen, send } = recorder(new Response("{}"));
    await forwardToApi(new Request("http://127.0.0.1:53000/api/v1/me"), ["v1", "me"], API, send);

    expect(new Headers(seen[0]?.init.headers).has("origin")).toBe(false);
  });

  it.each([[["openapi.json"]], [["healthz"]], [["v1", ".."]], [[]]])(
    "forwards nothing outside /v1 (%j)",
    async (path) => {
      const { seen, send } = recorder(new Response("{}"));
      const response = await forwardToApi(
        new Request("http://127.0.0.1:53000/api/x"),
        path,
        API,
        send,
      );

      expect(response.status).toBe(404);
      expect(seen).toHaveLength(0);
    },
  );

  it("reports an unreachable API as such, with no envelope", async () => {
    const { send } = recorder(new TypeError("connect ECONNREFUSED"));
    const response = await forwardToApi(
      new Request("http://127.0.0.1:53000/api/v1/me"),
      ["v1", "me"],
      API,
      send,
    );

    expect(response.status).toBe(502);
    expect(await response.text()).toBe("");
  });

  it("keeps the event stream unbuffered and the run location on the web origin", async () => {
    const { send } = recorder(
      new Response("retry: 2000\n\n", {
        status: 202,
        headers: {
          "content-type": "text/event-stream",
          location: "/v1/workspaces/w1/runs/r1",
          "x-correlation-id": "c1",
          "set-cookie": "a=b",
        },
      }),
    );
    const response = await forwardToApi(
      new Request("http://127.0.0.1:53000/api/v1/x"),
      ["v1", "x"],
      API,
      send,
    );

    expect(response.headers.get("cache-control")).toBe("no-store, no-transform");
    expect(response.headers.get("location")).toBe("/api/v1/workspaces/w1/runs/r1");
    expect(response.headers.get("x-correlation-id")).toBe("c1");
    expect(response.headers.get("set-cookie")).toBeNull();
    expect(await response.text()).toBe("retry: 2000\n\n");
  });
});
