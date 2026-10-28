// The Sprint 1 visual review package (plan section 5, UI-11): every chapter and the shell's
// states at 1440×900, 390×844 and 768×1024, each with the automatable checks: axe (WCAG 2.0,
// 2.1 and 2.2 A/AA), horizontal overflow, console errors and font loading. These checks are
// evidence for a human review, not the review itself (ruling R2).
//
// `pnpm run review-screenshots` writes the PNGs and checks.md to docs/reviews/sprint-1/;
// otherwise (make acceptance) they go to the test output and only the checks gate.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page, test } from "@playwright/test";
import { type AxeViolation, axe, chapterUrl, signIn } from "./helpers";
import { stack } from "./stack";

const VIEWPORTS = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "390x844", width: 390, height: 844 },
] as const;

type Shot = {
  name: string;
  /** Who signs in (none: the signed-out page). */
  as: "ada" | "uninvited" | null;
  url: string;
  ready: (page: Page) => Promise<void>;
  /** Expected refusals log a failed resource load; those lines are not defects. */
  refused?: boolean;
};

const heading = (name: string) => async (page: Page) => {
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
  await expect(page.getByRole("banner").getByText(/^Saved, version \d+$/)).toBeVisible();
  // The live-update state is in the strip on wider screens; phones show the saved state only.
  if ((page.viewportSize()?.width ?? 0) > 760) {
    await expect(page.getByRole("status").filter({ hasText: "Live" })).toBeVisible();
  }
};

const SHOTS: Shot[] = [
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
  axe: AxeViolation[];
  errors: string[];
};

const target = process.env.NESSA_REVIEW_DIR;

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
      test.setTimeout(240_000);
      const directory = target ?? testInfo.outputPath("screenshots");
      mkdirSync(directory, { recursive: true });
      const results: Result[] = [];
      const errors: string[] = [];
      const pages = new Map<Shot["as"], Page>();

      for (const shot of SHOTS) {
        let page = pages.get(shot.as);
        if (page === undefined) {
          // A separate browser context per identity: nothing carries over between them.
          const context = await browser.newContext({
            viewport: { width: viewport.width, height: viewport.height },
            reducedMotion: "reduce",
          });
          page = await context.newPage();
          page.on("console", (message) => {
            if (message.type() === "error") errors.push(message.text());
          });
          if (shot.as !== null) await signIn(page, shot.as, shot.url);
          pages.set(shot.as, page);
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
        const file = `${shot.name}--${viewport.name}.png`;
        await page.screenshot({ path: join(directory, file), fullPage: false });
        const violations = await axe(page);
        const unexpected = errors.filter(
          (line) => !(shot.refused && line.startsWith("Failed to load resource")),
        );
        results.push({ file, fonts, overflow, axe: violations, errors: [...unexpected] });
      }

      for (const page of pages.values()) await page.context().close();
      writeFileSync(
        join(directory, `checks-${viewport.name}.json`),
        `${JSON.stringify(results, null, 2)}\n`,
      );
      for (const result of results) {
        expect.soft(result.axe, `${result.file}: axe`).toEqual([]);
        expect.soft(result.overflow, `${result.file}: horizontal overflow`).toBeLessThanOrEqual(0);
        expect.soft(result.errors, `${result.file}: console errors`).toEqual([]);
        expect.soft(result.fonts, `${result.file}: fonts loaded`).toBe(true);
      }
    });
  });
}
