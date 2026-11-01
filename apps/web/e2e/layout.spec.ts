// Layout contracts from the Sprint 0–1 visual review (Task 6c): what must stay in view, at
// which size, once a finding is corrected. Each asserts geometry or drawing on the real
// stack; the captures in the visual package are the evidence a person looks at.
//
// Task W2E: the fixture route preview left the person's path (the audit's ruling), so its
// layout contracts (V-03's first route cards, V-04's route sheet, S0-V07's focused card) left
// with it; the component keeps its unit tests (`RoutePreview.test.tsx`) and its Storybook
// stories (axe-checked) until Routes is built (Task 14).
import { expect, test } from "@playwright/test";
import { chapterUrl, signIn } from "./helpers";

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
  const visited = await look(/^Roles\s*, not built yet\s*, visited$/);
  const notStarted = await look(/^Skills\s*, not built yet\s*, not started$/);

  expect(visited.filled).toBe(false);
  expect(notStarted.filled).toBe(false);
  expect(visited.ring).not.toBe(notStarted.ring);
});

test("[UI-09] every chapter not built yet is marked in the rail, in sight, before it is clicked (F2)", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("you"));
  const rail = page.getByRole("navigation", { name: "Chapters" });
  for (const chapter of ["Roles", "Skills", "Options", "Routes", "Plan"]) {
    const link = rail.getByRole("link", { name: new RegExp(`^${chapter}\\s*, not built yet`) });
    await expect(link.getByText("not built yet")).toBeVisible();
  }
  await expect(rail.getByRole("link", { name: /^You/ }).getByText("not built yet")).toHaveCount(0);
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("[UI-09] the chapter menu marks every chapter not built yet (F2)", async ({ page }) => {
    await signIn(page, "ada", chapterUrl("you"));
    await page.getByRole("button", { name: /open chapter menu/ }).click();
    const menu = page.getByRole("navigation", { name: "Chapters" });
    for (const chapter of ["Roles", "Skills", "Options", "Routes", "Plan"]) {
      await expect(
        menu
          .getByRole("link", { name: new RegExp(`^${chapter}\\s*, not built yet`) })
          .getByText("not built yet"),
      ).toBeVisible();
    }
  });
});

test("[UI-09] Routes is a place not built yet in every workspace, the fixture's too", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("routes"));
  await expect(page.getByRole("heading", { level: 1, name: "Routes" })).toBeVisible();
  await expect(page.getByText("Not built yet", { exact: true })).toBeVisible();
  await expect(page.getByText(/^Route search isn't ready yet/)).toBeVisible();
  await expect(page.getByText("Fixture preview: not your routes")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Route A/ })).toHaveCount(0);
});
