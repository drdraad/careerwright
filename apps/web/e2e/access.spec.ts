// The request boundary through the web origin (BND1-13, SEC-01, DUR-04): identity and
// invitation, another person's workspace, foreign Host and Origin values, and a stale save.
import { request as httpRequest } from "node:http";
import { expect, test } from "@playwright/test";
import { chapterUrl, signIn } from "./helpers";
import { AUTH_ORIGIN, FIXTURE_WORKSPACE, PORTS, WEB_ORIGIN } from "./stack";

type Raw = { status: number; body: string };

/** A raw HTTP call to the web origin, so Host and Origin are exactly what the test says. */
function raw(method: string, path: string, headers: Record<string, string>, body?: string) {
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

async function token(handle: string): Promise<string> {
  const response = await fetch(
    `${AUTH_ORIGIN}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=emulator`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        email: `${handle}@nessa.test`,
        password: `nessa-demo-${handle}`,
        returnSecureToken: true,
      }),
    },
  );
  return ((await response.json()) as { idToken: string }).idToken;
}

const HOST = `127.0.0.1:${PORTS.web}`;

test("[SEC-01] an uninvited account can sign in but is refused, and says so", async ({ page }) => {
  await signIn(page, "uninvited");
  await expect(page.getByRole("heading", { name: "This account isn't invited" })).toBeVisible();
  await expect(page.getByText("Sign in with an invited account.")).toBeVisible();
});

test("[SEC-01] another person's workspace is not shown, and an empty home says what to do", async ({
  page,
}) => {
  await signIn(page, "ben");
  await expect(page.getByText("No workspaces yet")).toBeVisible();
  await page.goto(chapterUrl("you"));
  await expect(page.getByRole("heading", { name: "This workspace can't be shown" })).toBeVisible();
  await expect(page.getByText("Not found")).toBeVisible();
});

test("[BND1-13] the web origin refuses a foreign Host (DNS rebinding)", async () => {
  const refused = await raw("GET", "/", { Host: `rebound.example:${PORTS.web}` });
  const api = await raw("GET", "/api/v1/me", { Host: `rebound.example:${PORTS.web}` });
  const allowed = await raw("GET", "/sign-in", { Host: HOST });

  expect(refused.status).toBe(400);
  expect(api.status).toBe(400);
  expect(allowed.status).toBe(200);
});

test("[BND1-13] a write through the web origin from a foreign or missing Origin changes nothing", async () => {
  const ada = await token("ada");
  const path = `/api/v1/workspaces/${FIXTURE_WORKSPACE}/profile`;
  const before = JSON.parse(
    (await raw("GET", path, { Host: HOST, Authorization: `Bearer ${ada}` })).body,
  );
  const body = JSON.stringify({ expected_version: before.version, profile: {} });
  const write = (origin?: string) =>
    raw(
      "PUT",
      path,
      {
        Host: HOST,
        Authorization: `Bearer ${ada}`,
        "Content-Type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
        ...(origin === undefined ? {} : { Origin: origin }),
      },
      body,
    );

  const foreign = await write("http://evil.example");
  const missing = await write();
  const after = JSON.parse(
    (await raw("GET", path, { Host: HOST, Authorization: `Bearer ${ada}` })).body,
  );

  expect(foreign.status).toBe(403);
  expect(JSON.parse(foreign.body).error.code).toBe("ORIGIN_NOT_ALLOWED");
  expect(missing.status).toBe(403);
  expect(after.version).toBe(before.version);
});

test("[DUR-04][VERSIONS-01] a save based on an older version is refused and the edits are kept", async ({
  browser,
}) => {
  const ada = await token("ada");
  const created = await raw(
    "POST",
    "/api/v1/workspaces",
    {
      Host: HOST,
      Origin: WEB_ORIGIN,
      Authorization: `Bearer ${ada}`,
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    JSON.stringify({ name: "Two tabs (synthetic)", data_mode: "demo", synthetic: true }),
  );
  const workspace = JSON.parse(created.body).workspace_id as string;
  const first = await browser.newPage();
  const second = await browser.newPage();
  await signIn(first, "ada", chapterUrl("you", workspace));
  await signIn(second, "ada", chapterUrl("you", workspace));
  for (const page of [first, second]) {
    await expect(page.getByText("Nothing saved yet").first()).toBeVisible();
    await page.getByLabel("How you answer current role").selectOption("provided");
  }
  const role = { name: "Current role", exact: true } as const;
  await second.getByRole("textbox", role).fill("Second tab's answer");
  await first.getByRole("textbox", role).fill("First tab's answer");
  await first.getByRole("button", { name: "Save changes" }).click();
  await expect(first.getByText("Saved as version 1.")).toBeVisible();

  await second.getByRole("button", { name: "Save changes" }).click();
  await expect(second.getByText("Version 1 was saved while you were editing")).toBeVisible();
  await expect(second.getByText(/Version 1 changed: Current role/)).toBeVisible();
  await expect(second.getByRole("textbox", role)).toHaveValue("Second tab's answer");
  // Close both tabs: open pages would keep streaming into the next test's restart.
  await first.close();
  await second.close();
});
