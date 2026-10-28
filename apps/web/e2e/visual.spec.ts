// The Sprint 1 visual review package (plan section 5, UI-11): every chapter and the shell's
// default, selected, empty, stale, unavailable and failed states at 1440×900, 390×844 and
// 768×1024, each with the automatable checks: axe (WCAG 2.0, 2.1 and 2.2 A/AA), horizontal
// overflow, a label overprinting its value, console errors and font loading. These checks are
// evidence for a human review, not the review itself (ruling R2).
//
// `pnpm run review-screenshots` writes the PNGs and checks-<viewport>.json to
// docs/reviews/sprint-1/screenshots/; otherwise (make acceptance) they go to the test output
// and only the checks gate.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken, saveElsewhere } from "./api";
import { type AxeViolation, axe, chapterUrl, liveUpdates, signIn } from "./helpers";
import { FIXTURE_WORKSPACE, stack } from "./stack";

const VIEWPORTS = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "390x844", width: 390, height: 844 },
] as const;

type Shot = {
  name: string;
  /** Who signs in (none: the signed-out page). */
  as: "ada" | "ben" | "uninvited" | null;
  /**
   * Shots that change what the page receives (a blocked stream, a failing request) get a
   * browser context of their own; the others share one per identity.
   */
  context?: string;
  url: string;
  /** Runs once, before the context signs in: request interception for that context. */
  prepare?: (page: Page) => Promise<unknown>;
  ready: (page: Page) => Promise<void>;
  /**
   * Expected refusals (403, 404, a stale save's 409) and blocked requests log a failed load;
   * those lines are not defects.
   */
  refused?: boolean;
};

const heading = (name: string) => async (page: Page) => {
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
  await expect(page.getByRole("banner").getByText(/^Saved, version \d+$/)).toBeVisible();
  await expect(liveUpdates(page, "Live")).toBeVisible();
};

/** `scratch` is a new, empty synthetic workspace of Ada's: nothing saved, no fixture. */
const shots = (scratch: string): Shot[] => [
  {
    name: "sign-in",
    as: null,
    url: "/sign-in",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "Sign in to Nessa" })).toBeVisible();
    },
  },
  { name: "you", as: "ada", url: chapterUrl("you"), ready: heading("You") },
  {
    name: "you--source-drawer",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await heading("You")(page);
      await page.getByRole("button", { name: "Source for total spending limit" }).click();
      await expect(page.getByText("Synthetic fixture", { exact: true })).toBeVisible();
    },
  },
  { name: "roles", as: "ada", url: chapterUrl("roles"), ready: heading("Roles") },
  { name: "skills", as: "ada", url: chapterUrl("skills"), ready: heading("Skills") },
  { name: "options", as: "ada", url: chapterUrl("options"), ready: heading("Options") },
  { name: "routes", as: "ada", url: chapterUrl("routes"), ready: heading("Routes") },
  {
    name: "routes--route-b",
    as: "ada",
    url: chapterUrl("routes"),
    ready: async (page) => {
      await heading("Routes")(page);
      await page.getByRole("button", { name: /^Route B/ }).click();
      await expect(page.getByText("Synthetic fixture route")).toBeVisible();
    },
  },
  { name: "plan", as: "ada", url: chapterUrl("plan"), ready: heading("Plan") },
  {
    name: "routes--empty",
    as: "ada",
    url: chapterUrl("routes", scratch),
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "No routes yet" })).toBeVisible();
      await expect(page.getByRole("banner").getByText("Nothing saved yet")).toBeVisible();
      await expect(liveUpdates(page, "Live")).toBeVisible();
    },
  },
  {
    name: "you--stale",
    as: "ada",
    url: chapterUrl("you", scratch),
    refused: true,
    ready: async (page) => {
      await expect(page.getByText("Nothing saved yet").first()).toBeVisible();
      await expect(liveUpdates(page, "Live")).toBeVisible();
      await page.getByLabel("How you answer current role").selectOption("provided");
      await page
        .getByRole("textbox", { name: "Current role", exact: true })
        .fill("Typed on this page");
      const made = await saveElsewhere(scratch, "ada", "current_role", "Saved in another tab");
      await page.getByRole("button", { name: "Save changes" }).click();
      const notice = page.getByText(`Version ${made} was saved while you were editing`);
      await expect(notice).toBeVisible();
      await expect(page.getByText(`Version ${made} has Saved in another tab here.`)).toBeVisible();
      // Saving scrolled to the button; the capture shows the notice and the first answers.
      await notice.scrollIntoViewIfNeeded();
    },
  },
  {
    name: "you--unavailable",
    as: "ada",
    context: "stream-blocked",
    url: chapterUrl("you"),
    prepare: (page) => page.route("**/events/stream*", (route) => route.abort()),
    refused: true,
    ready: async (page) => {
      await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
      await expect(liveUpdates(page, "Reconnecting")).toBeVisible();
    },
  },
  {
    name: "you--failed",
    as: "ada",
    context: "profile-blocked",
    url: chapterUrl("you"),
    prepare: (page) =>
      page.route(`**/api/v1/workspaces/${FIXTURE_WORKSPACE}/profile`, (route) => route.abort()),
    refused: true,
    ready: async (page) => {
      await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
      await expect(
        page.getByRole("alert").getByText("Nessa's service isn't reachable"),
      ).toBeVisible();
      await expect(
        page.getByRole("banner").getByText("What we know couldn't be loaded"),
      ).toBeVisible();
    },
  },
  {
    name: "home--empty",
    as: "ben",
    url: "/",
    ready: async (page) => {
      await expect(page.getByText("No workspaces yet")).toBeVisible();
    },
  },
  {
    name: "not-found",
    as: "ben",
    url: chapterUrl("you"),
    refused: true,
    ready: async (page) => {
      await expect(
        page.getByRole("heading", { name: "This workspace can't be shown" }),
      ).toBeVisible();
      await expect(page.getByText("Not found")).toBeVisible();
    },
  },
  {
    name: "not-invited",
    as: "uninvited",
    url: "/",
    refused: true,
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "This account isn't invited" })).toBeVisible();
    },
  },
];

type Result = {
  file: string;
  fonts: boolean;
  overflow: number;
  /** Description-list labels whose text overprints their value's text. */
  overprinted: string[];
  axe: AxeViolation[];
  errors: string[];
};

const target = process.env.NESSA_REVIEW_DIR;

/** Each `dt` whose painted text meets the painted text of the `dd` after it. */
function overprintedLabels(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const textBoxes = (element: Element) => {
      const range = document.createRange();
      range.selectNodeContents(element);
      return Array.from(range.getClientRects()).filter((box) => box.width > 0);
    };
    const meet = (a: DOMRect, b: DOMRect) =>
      Math.min(a.right, b.right) - Math.max(a.left, b.left) > 0.5 &&
      Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 0.5;
    const found: string[] = [];
    for (const label of document.querySelectorAll("dt")) {
      const value = label.nextElementSibling;
      if (value?.tagName !== "DD") continue;
      const values = textBoxes(value);
      if (textBoxes(label).some((box) => values.some((other) => meet(box, other)))) {
        found.push(label.textContent ?? "");
      }
    }
    return found;
  });
}

test.beforeAll(() => {
  // The named fixture workspace exactly as seeded: P01's answers, version 1.
  stack("reset-demo");
});

for (const viewport of VIEWPORTS) {
  test.describe(viewport.name, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test(`[UI-11][UI-06][UI-04] every chapter and state at ${viewport.name}`, async ({
      browser,
    }, testInfo) => {
      test.setTimeout(300_000);
      const directory = target ?? testInfo.outputPath("screenshots");
      mkdirSync(directory, { recursive: true });
      const scratch = (
        await asBrowser<{ workspace_id: string }>(
          "POST",
          "/v1/workspaces",
          await emulatorToken("ada"),
          { name: "New workspace (synthetic)", data_mode: "demo", synthetic: true },
        )
      ).workspace_id;
      const results: Result[] = [];
      const errors: string[] = [];
      const pages = new Map<string, Page>();

      for (const shot of shots(scratch)) {
        const key = shot.context ?? shot.as ?? "signed-out";
        let page = pages.get(key);
        if (page === undefined) {
          // A separate browser context per identity or condition: nothing carries over.
          const context = await browser.newContext({
            viewport: { width: viewport.width, height: viewport.height },
            reducedMotion: "reduce",
          });
          page = await context.newPage();
          page.on("console", (message) => {
            if (message.type() === "error") errors.push(message.text());
          });
          await shot.prepare?.(page);
          if (shot.as !== null) await signIn(page, shot.as, shot.url);
          pages.set(key, page);
        }
        errors.length = 0;
        await page.goto(shot.url);
        await shot.ready(page);
        await page.evaluate(() => document.fonts.ready);
        const fonts = await page.evaluate(
          () =>
            document.fonts.check('16px "Source Sans 3"') &&
            document.fonts.check('31px "Newsreader"'),
        );
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - window.innerWidth,
        );
        const overprinted = await overprintedLabels(page);
        const file = `${shot.name}--${viewport.name}.png`;
        await page.screenshot({ path: join(directory, file), fullPage: false });
        const violations = await axe(page);
        const unexpected = errors.filter(
          (line) => !(shot.refused && line.startsWith("Failed to load resource")),
        );
        results.push({
          file,
          fonts,
          overflow,
          overprinted,
          axe: violations,
          errors: [...unexpected],
        });
      }

      for (const page of pages.values()) await page.context().close();
      writeFileSync(
        join(directory, `checks-${viewport.name}.json`),
        `${JSON.stringify(results, null, 2)}\n`,
      );
      for (const result of results) {
        expect.soft(result.axe, `${result.file}: axe`).toEqual([]);
        expect.soft(result.overflow, `${result.file}: horizontal overflow`).toBeLessThanOrEqual(0);
        expect.soft(result.overprinted, `${result.file}: labels over values`).toEqual([]);
        expect.soft(result.errors, `${result.file}: console errors`).toEqual([]);
        expect.soft(result.fonts, `${result.file}: fonts loaded`).toBe(true);
      }
    });
  });
}
