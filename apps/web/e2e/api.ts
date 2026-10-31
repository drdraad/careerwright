// Direct calls for test set-up and boundary checks: an emulator ID token, and raw HTTP to the
// web origin so Host and Origin are exactly what a test says.
import { request as httpRequest } from "node:http";
import { expect } from "@playwright/test";
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

/** Answers, a reply to review and a completed discovery, through the API (demo mode). */
export async function talkedWorkspace(token: string): Promise<string> {
  const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    token,
    { name: "Conversation (synthetic)", data_mode: "demo", synthetic: true },
  );
  const base = `/v1/workspaces/${id}`;
  const blank = await asBrowser<{ document: Record<string, unknown> }>(
    "GET",
    `${base}/profile`,
    token,
  );
  const profile: Record<string, unknown> = Object.fromEntries(
    Object.keys(blank.document)
      .filter((field) => field !== "schema_version")
      .map((field) => [field, { state: "unasked" }]),
  );
  profile.current_role = { state: "provided", value: "warehouse supervisor" };
  profile.enjoyed_tasks = { state: "provided", value: ["fixing bikes", "working outdoors"] };
  profile.cities = { state: "provided", value: ["Leeds"] };
  await asBrowser("PUT", `${base}/profile`, token, { expected_version: 0, profile });
  await asBrowser("PUT", `${base}/interview/preferences`, token, {
    expected_version: 0,
    entry_mode: "unsure",
    conversation_mode: null,
    paused: false,
  });
  const turn = await asBrowser<{ turn_id: string }>("POST", `${base}/interview/turns`, token, {
    expected_profile_version: 1,
    message: "Synthetic: I could do 5 hours a week, and spend up to £600.",
  });
  const found = await asBrowser<{ discovery_id: string }>("POST", `${base}/discoveries`, token, {
    expected_profile_version: 1,
  });
  for (const path of [
    `${base}/interview/turns/${turn.turn_id}`,
    `${base}/discoveries/${found.discovery_id}`,
  ]) {
    await expect
      .poll(
        async () => (await asBrowser<{ run: { status: string } }>("GET", path, token)).run.status,
        {
          timeout: 60_000,
        },
      )
      .toBe("complete");
  }
  return id;
}
