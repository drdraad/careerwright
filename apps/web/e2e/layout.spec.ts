// Layout contracts from the Sprint 0–1 visual review (Task 6c): what must stay in view, at
// which size, once a finding is corrected. Each asserts geometry or drawing on the real
// stack; the captures in the visual package are the evidence a person looks at.
import { expect, type Locator, test } from "@playwright/test";
import { chapterUrl, signIn } from "./helpers";

async function box(locator: Locator) {
  await expect(locator).toBeVisible();
  const found = await locator.boundingBox();
  if (found === null) throw new Error("not rendered");
  return found;
}

test.describe("phone", () => {
  const PHONE = { width: 390, height: 844 };
  test.use({ viewport: PHONE });

  test.beforeEach(async ({ page }) => {
    await signIn(page, "ada", chapterUrl("routes"));
    await expect(page.getByRole("heading", { level: 1, name: "Routes" })).toBeVisible();
  });

  test("[UI-09] Routes leads with its first route card, after the synthetic notice (V-03)", async ({
    page,
  }) => {
    const notice = await box(page.getByText("Fixture preview: not your routes"));
    const first = await box(page.getByRole("button", { name: /^Route A/ }));

    expect(notice.y + notice.height).toBeLessThan(first.y);
    expect(first.y + first.height).toBeLessThanOrEqual(PHONE.height);
  });

  test("[UI-09] the route sheet's peek shows the route, its label, condition, readiness and costs (V-04)", async ({
    page,
  }) => {
    await page.getByRole("button", { name: /^Route B/ }).click();
    const sheet = page.getByRole("dialog", { name: "Route B" });
    const peek = await box(sheet);
    expect(peek.height).toBe(212);
    const lead = sheet.getByRole("group", { name: "Route B at a glance" });
    await expect(lead.getByText("Synthetic fixture route")).toBeVisible();
    await expect(lead.getByText(/^Conditional: ready only once/)).toBeVisible();
    await expect(lead.getByRole("term")).toHaveText([
      "Ready in",
      "Economic cost",
      "Direct spending",
    ]);

    for (const part of [sheet.getByRole("heading", { name: "Route B" }), lead]) {
      const shown = await box(part);
      expect(shown.y).toBeGreaterThanOrEqual(peek.y);
      expect(shown.y + shown.height).toBeLessThanOrEqual(peek.y + peek.height);
    }
  });

  test("[UI-06] with the sheet open, a route brought into view by focus is not under it (S0-V07)", async ({
    page,
  }) => {
    await page.getByRole("button", { name: /^Route B/ }).click();
    await expect(page.getByRole("dialog", { name: "Route B" })).toBeVisible();
    const last = page.getByRole("button", { name: /^Route E/ });
    await last.focus();

    const onTop = await last.evaluate((card) => {
      const shown = card.getBoundingClientRect();
      const hit = document.elementFromPoint(
        shown.left + shown.width / 2,
        shown.top + shown.height / 2,
      );
      return hit !== null && card.contains(hit);
    });
    expect(onTop).toBe(true);
  });
});

test("[UI-09] on a tablet the first three routes are in the first view (V-03)", async ({
  browser,
}) => {
  const context = await browser.newContext({ viewport: { width: 768, height: 1024 } });
  const page = await context.newPage();
  await signIn(page, "ada", chapterUrl("routes"));
  const third = await box(page.getByRole("button", { name: /^Route C/ }));

  expect(third.y + third.height).toBeLessThanOrEqual(1024);
  await context.close();
});

test("[UI-09] a visited chapter is a ring, never the filled mark of finished work (V-09)", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("roles"));
  await page.goto(chapterUrl("plan"));
  const rail = page.getByRole("navigation", { name: "Chapters" });
  const look = (name: RegExp) =>
    rail
      .getByRole("link", { name })
      .locator(".landmark")
      .evaluate((mark) => {
        const style = getComputedStyle(mark);
        const surface = getComputedStyle(mark.closest(".rail") ?? document.body);
        return {
          filled: style.backgroundColor !== surface.backgroundColor,
          ring: style.borderTopColor,
        };
      });
  const visited = await look(/^Roles\s*, visited$/);
  const notStarted = await look(/^Skills\s*, not started$/);

  expect(visited.filled).toBe(false);
  expect(notStarted.filled).toBe(false);
  expect(visited.ring).not.toBe(notStarted.ring);
});
