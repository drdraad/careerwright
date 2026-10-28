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

/** A fresh key per intended change; a retry of the same change reuses it (ADR 0004 decision 7). */
export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}
