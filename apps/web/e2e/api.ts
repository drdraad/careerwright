// Direct calls for test set-up and boundary checks: an emulator ID token, and raw HTTP to the
// web origin so Host and Origin are exactly what a test says.
import { request as httpRequest } from "node:http";
import { AUTH_ORIGIN, PORTS, WEB_ORIGIN } from "./stack";

export type Raw = { status: number; body: string };

export const WEB_HOST = `127.0.0.1:${PORTS.web}`;

export function raw(
  method: string,
  path: string,
  headers: Record<string, string>,
  body?: string,
): Promise<Raw> {
  return new Promise<Raw>((resolve, reject) => {
    const call = httpRequest(
      { host: "127.0.0.1", port: PORTS.web, method, path, headers },
      (response) => {
        let text = "";
        response.setEncoding("utf8");
        response.on("data", (chunk: string) => {
          text += chunk;
        });
        response.on("end", () => resolve({ status: response.statusCode ?? 0, body: text }));
      },
    );
    call.on("error", reject);
    if (body !== undefined) call.write(body);
    call.end();
  });
}

export async function emulatorToken(handle: string): Promise<string> {
  const response = await fetch(
    `${AUTH_ORIGIN}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=emulator`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        email: `${handle}@careerwright.test`,
        password: `careerwright-demo-${handle}`,
        returnSecureToken: true,
      }),
    },
  );
  return ((await response.json()) as { idToken: string }).idToken;
}

/** An API call through the web origin as the browser would make it (its Origin, a key). */
export async function asBrowser<T>(
  method: string,
  path: string,
  token: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = { Host: WEB_HOST, Authorization: `Bearer ${token}` };
  if (method !== "GET") {
    headers.Origin = WEB_ORIGIN;
    headers["Idempotency-Key"] = crypto.randomUUID();
    headers["Content-Type"] = "application/json";
  }
  const answer = await raw(
    method,
    `/api${path}`,
    headers,
    body === undefined ? undefined : JSON.stringify(body),
  );
  if (answer.status >= 400) throw new Error(`${method} ${path}: ${answer.status} ${answer.body}`);
  return JSON.parse(answer.body) as T;
}

/**
 * Another client saves one text answer on top of the latest version, as a second tab would.
 * Returns the version it made.
 */
export async function saveElsewhere(
  workspace: string,
  handle: string,
  name: string,
  value: string,
): Promise<number> {
  const token = await emulatorToken(handle);
  const path = `/v1/workspaces/${workspace}/profile`;
  const current = await asBrowser<{ version: number; document: Record<string, unknown> }>(
    "GET",
    path,
    token,
  );
  const profile = Object.fromEntries(
    Object.entries(current.document)
      .filter(([field]) => field !== "schema_version")
      .map(([field, answer]) => {
        const { state, value: shown } = answer as { state: string; value?: unknown };
        return [field, state === "provided" ? { state, value: shown } : { state }];
      }),
  );
  profile[name] = { state: "provided", value };
  const saved = await asBrowser<{ version: number }>("PUT", path, token, {
    expected_version: current.version,
    profile,
  });
  return saved.version;
}
