// A scripted API at the network edge (the generated client's fetch), for component tests:
// each route answers a method and a path pattern; every request is recorded with its body.
import { client } from "@/generated/api/client.gen";
import { configureApiClient } from "@/lib/api";

export type Sent = { method: string; path: string; query: string; body: unknown };
type Answer = ((sent: Sent) => unknown) | object;
export type Route = { method: string; path: RegExp; status?: number; answer: Answer };

export function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** Routes the client's requests; an unrouted request is a 404 envelope, never a hang. */
export function fakeApi(routes: Route[]): Sent[] {
  configureApiClient(async () => "token");
  const sent: Sent[] = [];
  client.setConfig({
    baseUrl: "http://localhost:3000/api",
    fetch: async (input: RequestInfo | URL) => {
      const request = input as Request;
      const url = new URL(request.url);
      const text = request.method === "GET" ? "" : await request.text();
      const record: Sent = {
        method: request.method,
        path: url.pathname.replace(/^\/api/, ""),
        query: url.search,
        body: text ? JSON.parse(text) : null,
      };
      sent.push(record);
      const route = routes.find((r) => r.method === request.method && r.path.test(record.path));
      if (route === undefined) {
        return json(404, {
          error: {
            code: "NOT_FOUND",
            message: "",
            retryable: false,
            stage: "request",
            correlation_id: "c0",
            details: {},
          },
        });
      }
      // An answer may be a promise, to hold a request open while the test acts.
      const body = await (typeof route.answer === "function" ? route.answer(record) : route.answer);
      return json(route.status ?? 200, body);
    },
  });
  return sent;
}
