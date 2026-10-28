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
  await page.getByLabel("Email").fill(`${handle}@nessa.test`);
  await page.getByLabel("Password").fill(`nessa-demo-${handle}`);
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

/** axe-core with the WCAG 2.0/2.1/2.2 A and AA rule tags (the same set as docs/design). */
export async function axe(page: Page): Promise<AxeViolation[]> {
  await page.addScriptTag({ content: axeSource });
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
 * The strip's live-update state, matched exactly: its text is "Updates: <state>", so a loose
 * match on "Live" would also match other states.
 */
export function liveUpdates(page: Page, state: "Live" | "Connecting" | "Reconnecting" | RegExp) {
  const pattern = state instanceof RegExp ? state : new RegExp(`^Updates: ${state}$`);
  return page.getByRole("status").filter({ hasText: pattern });
}
