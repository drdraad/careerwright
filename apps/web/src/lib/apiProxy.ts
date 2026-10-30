// Same-origin access to the API (plan section 2, "route API/events through the web origin").
// The browser calls `/api/v1/...` on the web origin; the web server forwards it to the API on
// the internal Compose network. The API's own checks stay meaningful:
//   - the browser's Origin header is forwarded unchanged (never added or rewritten), so the
//     API still refuses a foreign origin and a state-changing request without one;
//   - the Host is the API's internal name, which the API allowlists; the web server checks
//     the browser's Host itself (src/proxy.ts), so DNS rebinding is still refused;
//   - only the headers the API contract uses pass; cookies and forwarding headers do not.
// Responses stream through, so the status-event stream is not buffered.

const REQUEST_HEADERS = [
  "accept",
  "authorization",
  "content-type",
  "idempotency-key",
  "last-event-id",
  "origin",
];
const RESPONSE_HEADERS = [
  "cache-control",
  "content-type",
  "location",
  "retry-after",
  "x-correlation-id",
];

export const PROXY_PREFIX = "/api";

export async function forwardToApi(
  request: Request,
  path: readonly string[],
  apiOrigin: string,
  send: typeof fetch = fetch,
): Promise<Response> {
  if (
    path[0] !== "v1" ||
    path.some((segment) => segment === "" || segment === "." || segment === "..")
  ) {
    return new Response(null, { status: 404 });
  }
  const target = new URL(`/${path.map(encodeURIComponent).join("/")}`, apiOrigin);
  target.search = new URL(request.url).search;
  const headers = new Headers();
  for (const name of REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value !== null) headers.set(name, value);
  }
  const hasBody = !["GET", "HEAD"].includes(request.method);
  let upstream: Response;
  try {
    upstream = await send(target, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      redirect: "manual",
      signal: request.signal,
      cache: "no-store",
    });
  } catch {
    // No envelope: the API was not reached, and the browser client reports exactly that.
    return new Response(null, {
      status: 502,
      headers: { "x-careerwright-proxy": "api-unreachable" },
    });
  }
  const out = new Headers();
  for (const name of RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value !== null) out.set(name, value);
  }
  const location = out.get("location");
  if (location?.startsWith("/v1/")) out.set("location", `${PROXY_PREFIX}${location}`);
  if (out.get("content-type")?.startsWith("text/event-stream")) {
    out.set("cache-control", "no-store, no-transform");
    out.set("x-accel-buffering", "no");
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
}
