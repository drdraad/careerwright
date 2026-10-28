// Every Storybook state renders without errors and passes axe (UI-04, UI-06). Runs against the
// static build (`pnpm run build-storybook`, done first by `make acceptance`), served on an
// ephemeral loopback port; it needs no stack.
import { existsSync, readFileSync } from "node:fs";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";
import { axe } from "./helpers";

const STATIC = fileURLToPath(new URL("../storybook-static/", import.meta.url));
const TYPES: Record<string, string> = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".ttf": "font/ttf",
  ".woff2": "font/woff2",
};

let server: Server;
let origin: string;

test.beforeAll(async () => {
  expect(existsSync(join(STATIC, "index.json")), "run `pnpm run build-storybook` first").toBe(true);
  server = createServer((request, response) => {
    const path = normalize(decodeURIComponent(new URL(request.url ?? "/", "http://x").pathname));
    const file = join(STATIC, path === "/" ? "index.html" : path);
    if (!file.startsWith(STATIC) || !existsSync(file)) {
      response.writeHead(404).end();
      return;
    }
    response.writeHead(200, { "content-type": TYPES[extname(file)] ?? "application/octet-stream" });
    response.end(readFileSync(file));
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});

test.afterAll(() => new Promise<void>((resolve) => server.close(() => resolve())));

test("[UI-04][UI-06] every story renders cleanly and passes axe", async ({ page }) => {
  test.setTimeout(180_000);
  const index = JSON.parse(readFileSync(join(STATIC, "index.json"), "utf8")) as {
    entries: Record<string, { type: string }>;
  };
  const stories = Object.entries(index.entries)
    .filter(([, entry]) => entry.type === "story")
    .map(([id]) => id);
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  const failures: Record<string, unknown> = {};

  for (const id of stories) {
    errors.length = 0;
    await page.goto(`${origin}/iframe.html?id=${id}&viewMode=story`);
    await expect(page.locator("#storybook-root > *").first()).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    const violations = await axe(page);
    if (violations.length > 0 || errors.length > 0)
      failures[id] = { violations, errors: [...errors] };
  }

  expect(stories.length).toBeGreaterThanOrEqual(25);
  expect(failures).toEqual({});
});
