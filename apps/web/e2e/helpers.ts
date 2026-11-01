import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import type { Page } from "@playwright/test";
import { AUTH_ORIGIN, FIXTURE_WORKSPACE, WEB_ORIGIN } from "./stack";

const require = createRequire(import.meta.url);
const axeSource = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

export const chapterUrl = (chapter: string, workspace = FIXTURE_WORKSPACE) =>
  `/w/${workspace}/${chapter}`;

/** Signs in through the page, as a person would, with a seeded emulator identity. */
export async function signIn(page: Page, handle: "ada" | "ben" | "uninvited", next = "/") {
  await page.goto(`/sign-in?next=${encodeURIComponent(next)}`);
  await page.getByLabel("Email").fill(`${handle}@careerwright.test`);
  await page.getByLabel("Password").fill(`careerwright-demo-${handle}`);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/sign-in"));
}

/** Every request the page makes, so a test can prove none left this machine (BND1-11). */
export function recordRequests(page: Page): string[] {
  const urls: string[] = [];
  page.on("request", (request) => urls.push(request.url()));
  return urls;
}

const ALLOWED_ORIGINS = new Set([WEB_ORIGIN, AUTH_ORIGIN]);

export function externalRequests(urls: string[]): string[] {
  return urls.filter((url) => {
    if (url.startsWith("data:") || url.startsWith("blob:")) return false;
    return !ALLOWED_ORIGINS.has(new URL(url).origin);
  });
}

export type AxeViolation = { id: string; impact: string | null; nodes: number; target: string };

/**
 * axe-core with the WCAG 2.0/2.1/2.2 A and AA rule tags (the same set as docs/design). In
 * Storybook the a11y addon runs its own scan after each story renders; a scan already in
 * progress is waited for, never skipped.
 */
export async function axe(page: Page): Promise<AxeViolation[]> {
  await page.addScriptTag({ content: axeSource });
  for (let attempt = 1; ; attempt += 1) {
    try {
      return await scan(page);
    } catch (error) {
      const busy = error instanceof Error && error.message.includes("Axe is already running");
      if (!busy || attempt >= 40) throw error;
      await page.waitForTimeout(250);
    }
  }
}

function scan(page: Page): Promise<AxeViolation[]> {
  return page.evaluate(async () => {
    const engine = (
      window as unknown as {
        axe: {
          run: (...args: unknown[]) => Promise<{
            violations: Array<{
              id: string;
              impact: string | null;
              nodes: Array<{ target: unknown }>;
            }>;
          }>;
        };
      }
    ).axe;
    const result = await engine.run(document, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    });
    return result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.length,
      target: JSON.stringify(v.nodes[0]?.target ?? ""),
    }));
  });
}

/**
 * The strip's live-update state. Live updates that work say nothing (plain words, Task W2C), so
 * "Live" is the strip's `data-events`; any other state is its words, matched exactly ("Updates:
 * <state>"), so a loose match would not also match another state.
 */
export function liveUpdates(page: Page, state: "Live" | "Connecting" | "Reconnecting" | RegExp) {
  if (state === "Live") return page.locator(".strip[data-events='live']");
  const pattern = state instanceof RegExp ? state : new RegExp(`^Updates: ${state}$`);
  return page.getByRole("status").filter({ hasText: pattern });
}

/**
 * The strip's saved state: "Answers saved" or "Nothing saved yet" in words, with the saved
 * version in `data-version` (any version, or the one given).
 */
export function saved(page: Page, version?: number) {
  return page
    .getByRole("banner")
    .locator(version === undefined ? "[data-version]" : `[data-version="${version}"]`);
}

/** The saved version the strip holds. */
export async function savedVersion(page: Page): Promise<number> {
  return Number(await saved(page).getAttribute("data-version"));
}

/**
 * The controls in view in the chapter filled with a bright colour, read from the computed
 * style, not the class: the one primary action's sea-glass, and the decision colours, so a
 * chosen Accept drawn as a second bright fill would count (design review M1).
 */
export async function brightFills(page: Page): Promise<number> {
  return page.evaluate(() => {
    const fill = (token: string) => {
      const probe = document.createElement("span");
      probe.style.background = `var(${token})`;
      document.body.append(probe);
      const colour = getComputedStyle(probe).backgroundColor;
      probe.remove();
      return colour;
    };
    const bright = ["--action-reading", "--decision-accept", "--decision-undo"].map(fill);
    return [...document.querySelectorAll("main button, main a")].filter(
      (control) =>
        control.getClientRects().length > 0 &&
        bright.includes(getComputedStyle(control).backgroundColor),
    ).length;
  });
}

/** The first question leads a new workspace (Task 6d slice B): "Skip for now" goes on to how
 *  to start, saving nothing, as a person who'd rather not say would. */
export async function skipFirstQuestion(page: Page) {
  await page.getByRole("button", { name: "Skip for now" }).click();
}

/** Opens one of the You chapter's views (its tabs: Conversation, What we know, Suggestions). */
export async function youView(page: Page, view: "Conversation" | "What we know" | "Suggestions") {
  await page.getByRole("tab", { name: view }).click();
}
