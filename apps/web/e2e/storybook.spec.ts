// Every Storybook state renders without errors and passes axe (UI-04, UI-06); What we know's
// long answers stay clear of their labels, and the open answer form keeps Save in reach, at
// three widths (Task W2F). Runs against the static build (`pnpm run build-storybook`, done
// first by `make acceptance`), served on an ephemeral loopback port; it needs no stack.
import { existsSync, readFileSync } from "node:fs";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";
import { axe, inReach, overprintedLabels } from "./helpers";

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

const WIDTHS = [
  { width: 1440, height: 900 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
] as const;

test("[UI-11] What we know's long answers: no label is printed over its value at any width (session W2, finding 1)", async ({
  browser,
}) => {
  for (const viewport of WIDTHS) {
    const page = await browser.newPage({ viewport });
    await page.goto(`${origin}/iframe.html?id=what-we-know--long-values&viewMode=story`);
    await expect(page.locator(".fact").first()).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    expect(await page.locator(".fact").count()).toBeGreaterThanOrEqual(6);
    expect(await overprintedLabels(page), `${viewport.width} px`).toEqual([]);
    await page.close();
  }
});

test("[UI-06][UI-09] the answer form's Save stays in reach while the form is open (session W2, finding 9)", async ({
  browser,
}) => {
  for (const viewport of WIDTHS) {
    const page = await browser.newPage({ viewport });
    await page.goto(`${origin}/iframe.html?id=what-we-know--answer-form-open&viewMode=story`);
    const save = page.getByRole("button", { name: "Save changes" });
    await expect(save).toBeVisible();
    // Each field at the top of the window, from the first to the last: Save is in view.
    for (const field of ["target_titles", "qualifications", "monthly_payment_cap", "work_style"]) {
      await page
        .locator(`[data-field='${field}']`)
        .evaluate((element) => element.scrollIntoView({ block: "start" }));
      expect(await inReach(save), `${viewport.width} px, ${field} at the top`).toBe(true);
    }
    await page.close();
  }
});

test("[UI-06] tabbing through the open answer form, the Save bar never covers the focused control (WCAG 2.2 2.4.11; Task W2F review, Important 1)", async ({
  browser,
}) => {
  for (const viewport of WIDTHS) {
    const page = await browser.newPage({ viewport });
    await page.goto(`${origin}/iframe.html?id=what-we-know--answer-form-open&viewMode=story`);
    await expect(page.getByRole("button", { name: "Save changes" })).toBeVisible();
    // Laid out in its own fonts first, so nothing moves after a stop is measured.
    await page.evaluate(() => document.fonts.ready);
    await page.locator("#edit-answers form :is(button, select, input)").first().focus();
    // Forward through the form, stop by stop, until focus reaches the bar itself.
    const covered: string[] = [];
    let stops = 0;
    for (; stops < 200; stops += 1) {
      const focused = await page.evaluate(() => {
        const element = document.activeElement;
        const bar = document.querySelector(".form-save");
        if (element === null || bar === null || bar.contains(element)) return null;
        if (element.closest("form") === null) return null;
        const box = element.getBoundingClientRect();
        const under = bar.getBoundingClientRect();
        return {
          name: element.getAttribute("aria-label") ?? element.textContent ?? element.tagName,
          covered: box.bottom > under.top && box.top < under.bottom,
        };
      });
      if (focused === null) break;
      if (focused.covered) covered.push(focused.name.trim());
      await page.keyboard.press("Tab");
    }
    expect(stops, `${viewport.width} px: stops tabbed`).toBeGreaterThan(30);
    expect(covered, `${viewport.width} px: focused controls under the Save bar`).toEqual([]);
    await page.close();
  }
});

test("[UI-06][STATE-06] tabbing through a waiting review card, its Save bar never covers the focused control, at 320 px too (WCAG 2.2 2.4.11; Task W2F slice E)", async ({
  browser,
}) => {
  // The bar wraps to three rows at 320 px (135 px), taller than the fixed 96 px of room the
  // window kept for it: Source, Edit and Skip went under it. The room is now its own height.
  for (const viewport of [{ width: 320, height: 844 }, ...WIDTHS]) {
    const page = await browser.newPage({ viewport });
    await page.goto(`${origin}/iframe.html?id=you--reply-changes-lists&viewMode=story`);
    await expect(page.getByRole("button", { name: "Keep none" })).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    await page.locator(".proposal button").first().focus();
    const covered: string[] = [];
    let stops = 0;
    for (; stops < 60; stops += 1) {
      const focused = await page.evaluate(() => {
        const element = document.activeElement;
        const bar = document.querySelector(".tray-actions");
        if (element === null || bar === null || element.closest(".proposal") === null) return null;
        const box = element.getBoundingClientRect();
        const under = bar.getBoundingClientRect();
        return {
          name: element.getAttribute("aria-label") ?? element.textContent ?? element.tagName,
          covered: box.bottom > under.top && box.top < under.bottom,
        };
      });
      if (focused === null) break;
      if (focused.covered) covered.push(focused.name.trim());
      await page.keyboard.press("Tab");
    }
    expect(stops, `${viewport.width} px: stops tabbed`).toBeGreaterThan(15);
    expect(covered, `${viewport.width} px: focused controls under the Save bar`).toEqual([]);
    await page.close();
  }
});
