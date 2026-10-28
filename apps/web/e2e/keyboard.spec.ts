// Keyboard only (UI-06): every chapter and the evidence drawer are reachable with Tab and
// Enter, and closing the drawer returns focus to what opened it. Desktop rail and phone menu.
import { expect, type Locator, type Page, test } from "@playwright/test";
import { chapterUrl, signIn } from "./helpers";

/** Presses Tab until `target` has focus; failing to get there is a keyboard trap or a gap. */
async function tabTo(page: Page, target: Locator, limit = 80) {
  for (let presses = 0; presses < limit; presses += 1) {
    if (await target.evaluate((element) => element === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error(`not reachable with Tab within ${limit} presses`);
}

const CHAPTERS = ["You", "Roles", "Skills", "Options", "Routes", "Plan"] as const;

test.beforeEach(async ({ page }) => {
  await signIn(page, "ada", chapterUrl("you"));
  await expect(page).toHaveURL(chapterUrl("you"));
  await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
});

test("[UI-06][UI-09] Tab and Enter reach every chapter from the rail", async ({ page }) => {
  await page.locator("body").focus();
  const rail = page.getByRole("navigation", { name: "Chapters" });
  for (const chapter of CHAPTERS) {
    const link = rail.getByRole("link", { name: new RegExp(`^${chapter}`) });
    await tabTo(page, link);
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(chapterUrl(chapter.toLowerCase()));
    await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
    await expect(link).toHaveAttribute("aria-current", "page");
  }
});

test("[UI-06] the skip link moves past the rail to the chapter", async ({ page }) => {
  await page.locator("body").focus();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to the chapter" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("main#main")).toBeFocused();
});

test("[UI-06] the drawer opens from the keyboard and returns focus when it closes", async ({
  page,
}) => {
  await page.goto(chapterUrl("routes"));
  const routeA = page.getByRole("button", { name: /^Route A/ });
  await tabTo(page, routeA);
  await page.keyboard.press("Enter");
  const drawer = page.getByRole("dialog", { name: "Route A" });
  await expect(drawer.getByRole("heading", { name: "Route A" })).toBeFocused();
  await tabTo(page, drawer.getByRole("button", { name: "Close route A" }), 20);
  await page.keyboard.press("Enter");
  await expect(drawer).toBeHidden();
  await expect(routeA).toBeFocused();

  await page.keyboard.press("Enter");
  await expect(drawer).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(routeA).toBeFocused();
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("[UI-06][UI-09] the chapter menu and the bottom sheet work from the keyboard", async ({
    page,
  }) => {
    const menu = page.getByRole("button", { name: /open chapter menu/ });
    await page.locator("body").focus();
    await tabTo(page, menu);
    await page.keyboard.press("Enter");
    const skills = page
      .getByRole("navigation", { name: "Chapters" })
      .getByRole("link", { name: "Skills" });
    await tabTo(page, skills, 10);
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(chapterUrl("skills"));

    await page.goto(chapterUrl("routes"));
    const routeB = page.getByRole("button", { name: /^Route B/ });
    await tabTo(page, routeB);
    await page.keyboard.press("Enter");
    const drawer = page.getByRole("dialog", { name: "Route B" });
    const more = drawer.getByRole("button", { name: "More" });
    await expect(more).toHaveAttribute("aria-expanded", "false");
    const peek = (await drawer.boundingBox())?.height ?? 0;
    await tabTo(page, more, 10);
    await page.keyboard.press("Enter");
    await expect(drawer.getByRole("button", { name: "Less" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    const expanded = (await drawer.boundingBox())?.height ?? 0;
    expect(peek).toBe(212);
    expect(expanded).toBeGreaterThan(600);
    await page.keyboard.press("Escape");
    await expect(drawer).toBeHidden();
    await expect(routeB).toBeFocused();
  });
});
