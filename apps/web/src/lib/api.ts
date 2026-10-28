// The generated API client, configured for the browser: same-origin `/api` (the web server
// forwards to the API on the internal network), the signed-in user's ID token, and failures
// as typed `ApiError`s. Failure is never an empty success: every non-2xx response throws.
import type { ErrorBody } from "@/generated/api";
import { client } from "@/generated/api/client.gen";

export const API_BASE = "/api";

export class ApiError extends Error {
  constructor(
    /** HTTP status, or 0 when no response arrived. */
    readonly status: number,
    /** The API's typed envelope; null when the API was not reached (the web server answered). */
    readonly body: ErrorBody | null,
  ) {
    super(body === null ? `API unreachable (${status})` : `${body.code} (${status})`);
    this.name = "ApiError";
  }

  get code(): ErrorBody["code"] | null {
    return this.body?.code ?? null;
  }
}

function envelopeOf(error: unknown): ErrorBody | null {
  if (typeof error !== "object" || error === null || !("error" in error)) return null;
  const body = (error as { error: unknown }).error;
  if (typeof body !== "object" || body === null || !("code" in body)) return null;
  return body as ErrorBody;
}

export function toApiError(error: unknown, response: Response | undefined): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError(response?.status ?? 0, envelopeOf(error));
}

let configured = false;

/** Wires the shared generated client once; `token` returns the current ID token or null. */
export function configureApiClient(token: () => Promise<string | null>): void {
  client.setConfig({
    baseUrl: API_BASE,
    throwOnError: true,
    auth: async () => (await token()) ?? undefined,
  });
  if (!configured) {
    client.interceptors.error.use((error, response) => toApiError(error, response));
    configured = true;
  }
}

/** Key order does not matter: the same fields and values are the same request. */
function fingerprint(request: unknown): string {
  return JSON.stringify(request, (_key, value: unknown) =>
    value !== null && typeof value === "object" && !Array.isArray(value)
      ? Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)))
      : value,
  );
}

/**
 * Idempotency keys for one form (ADR 0004 decision 7): sending the same request again, after
 * a failure or a lost response, reuses its key, so the API applies it at most once; a
 * different request gets a new key; `settled()` after success starts the next change afresh.
 */
export class ChangeKeys {
  private last: { fingerprint: string; key: string } | null = null;

  keyFor(request: unknown): string {
    const print = fingerprint(request);
    if (this.last?.fingerprint !== print)
      this.last = { fingerprint: print, key: crypto.randomUUID() };
    return this.last.key;
  }

  settled(): void {
    this.last = null;
  }
}
