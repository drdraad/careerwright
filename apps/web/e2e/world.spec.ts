// The world in the app (plan section 4, Sprint W SW.3): one persistent world behind all six
// chapters; changing chapter travels to its place; the still world tells the same story with
// the same words; the visible controls pause motion, keep calm mode and leave sound off until
// asked; a chapter not built yet says so in its place; every light's name sits beside it,
// clear of the panels; and nothing leaves this machine. On the real stack, demo mode.
import { expect, type Page, test } from "@playwright/test";
import { chapterUrl, externalRequests, recordRequests, signIn } from "./helpers";

const CHAPTERS = ["You", "Roles", "Skills", "Options", "Routes", "Plan"] as const;

const world = (page: Page) => page.locator(".world");
const words = (page: Page) => page.getByRole("complementary", { name: "Your world" });

/** The visible names in the world, with their boxes, and the panels over it. */
function layout(page: Page) {
  return page.evaluate(() => {
    const box = (e: Element) => {
      const r = e.getBoundingClientRect();
      return { x: r.left, y: r.top, w: r.width, h: r.height };
    };
    const labels = [
      ...document.querySelectorAll<HTMLElement>(".world-label[data-shown='true']"),
    ].map((e) => ({ name: e.textContent ?? "", ...box(e) }));
    const panels = [...document.querySelectorAll("[data-covers-world]")]
      .map(box)
      .filter((b) => b.w > 0 && b.h > 0);
    const key = document.querySelector(".world-legend:not([data-shown='false'])");
    return {
      labels,
      key: key === null ? null : box(key),
      panels,
      vw: window.innerWidth,
      vh: window.innerHeight,
    };
  });
}

const overlap = (
  a: { x: number; y: number; w: number; h: number },
  b: { x: number; y: number; w: number; h: number },
) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

test.describe("moving", () => {
  test.use({ reducedMotion: "no-preference" });

  test("[UI-09][UI-05][BND1-11] one world stays behind every chapter while the view travels", async ({
    page,
  }) => {
    const requests = recordRequests(page);
    await signIn(page, "ada", chapterUrl("you"));
    await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
    // Mark the world's node: if any chapter replaced it, the mark would be gone.
    await world(page).evaluate((element) => {
      (element as HTMLElement & { persisted?: boolean }).persisted = true;
    });

    const rail = page.getByRole("navigation", { name: "Chapters" });
    for (const chapter of CHAPTERS) {
      await rail.getByRole("link", { name: new RegExp(`^${chapter}`) }).click();
      await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
      await expect(world(page)).toHaveAttribute("data-place", chapter.toLowerCase());
      expect(
        await world(page).evaluate(
          (element) => (element as HTMLElement & { persisted?: boolean }).persisted,
        ),
      ).toBe(true);
    }
    // P01's own target stands on the horizon, named in the page.
    await expect(words(page).getByText("Data quality analyst")).toBeAttached();
    expect(externalRequests(requests)).toEqual([]);
  });

  test("[UI-05] pause stills the ambient motion; calm mode draws the world still and is kept", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("roles"));
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
    await expect(world(page)).toHaveAttribute("data-motion", "running");

    const pause = page.getByRole("button", { name: /^Pause motion/ });
    await pause.click();
    await expect(pause).toHaveAttribute("aria-pressed", "true");
    await expect(world(page)).toHaveAttribute("data-motion", "still");
    await pause.click();
    await expect(world(page)).toHaveAttribute("data-motion", "running");

    const sound = page.getByRole("button", { name: /^Sound/ });
    await expect(sound).toHaveAttribute("aria-pressed", "false");

    await page.getByRole("button", { name: /^Calm mode/ }).click();
    await expect(world(page)).toHaveAttribute("data-world-mode", "still");
    await expect(page.getByTestId("still-world")).toBeVisible();
    await page.reload();
    await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
    await expect(world(page)).toHaveAttribute("data-world-mode", "still");
    await page.getByRole("button", { name: /^Calm mode/ }).click();
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
  });
});

test("[UI-05][UI-07] the still world says what the moving world says, word for word", async ({
  browser,
}) => {
  const read = async (reducedMotion: "reduce" | "no-preference") => {
    const context = await browser.newContext({ reducedMotion });
    const page = await context.newPage();
    await signIn(page, "ada", chapterUrl("roles"));
    await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
    await expect(world(page)).toHaveAttribute(
      "data-world-mode",
      reducedMotion === "reduce" ? "still" : "moving",
    );
    await expect(words(page).getByText("Data quality analyst")).toBeAttached();
    const text = await words(page).innerText();
    await context.close();
    return text;
  };
  const still = await read("reduce");
  const moving = await read("no-preference");
  expect(still).toContain("You");
  expect(still).toBe(moving);
});

test("[UI-09] a chapter not built yet shows its place, and says so", async ({ page }) => {
  await signIn(page, "ada", chapterUrl("skills"));
  await expect(page.getByRole("heading", { level: 1, name: "Skills" })).toBeVisible();
  await expect(page.getByText("Not built yet")).toBeVisible();
  await expect(page.getByText("The ground between you and a destination.")).toBeVisible();
  await expect(world(page)).toHaveAttribute("data-place", "skills");
});

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
]) {
  test(`[UI-07] every name in the world sits clear of the panels and of each other (${viewport.width}×${viewport.height})`, async ({
    browser,
  }) => {
    for (const reducedMotion of ["reduce", "no-preference"] as const) {
      const context = await browser.newContext({ viewport, reducedMotion });
      const page = await context.newPage();
      await signIn(page, "ada", chapterUrl("you"));
      for (const chapter of CHAPTERS) {
        await page.goto(chapterUrl(chapter.toLowerCase()));
        await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
        // Let travel finish (600 ms) and the names settle.
        await page.waitForTimeout(900);
        const { labels, key, panels, vw, vh } = await layout(page);
        for (const [i, label] of labels.entries()) {
          const where = `${chapter}, ${reducedMotion}: "${label.name}"`;
          expect(label.x, where).toBeGreaterThanOrEqual(0);
          expect(label.y, where).toBeGreaterThanOrEqual(0);
          expect(label.x + label.w, where).toBeLessThanOrEqual(vw);
          expect(label.y + label.h, where).toBeLessThanOrEqual(vh);
          for (const panel of panels) expect(overlap(label, panel), where).toBe(false);
          for (const other of labels.slice(i + 1)) expect(overlap(label, other), where).toBe(false);
        }
        // The key to the lights, when shown, is not under a panel either.
        if (key !== null) {
          for (const panel of panels) {
            expect(overlap(key, panel), `${chapter}, ${reducedMotion}: the key`).toBe(false);
          }
        }
      }
      await context.close();
    }
  });
}
