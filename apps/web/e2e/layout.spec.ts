import { expect, test } from "@playwright/test";
import { chapterUrl, signIn } from "./helpers";

test("[UI-09] a chosen direction has a filled mark while available work stays open", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("you"));
  const rail = page.getByRole("navigation", { name: "Chapters" });
  const chosen = rail.getByRole("link", { name: "You, direction chosen" });
  const available = rail.getByRole("link", { name: "Roles, available" });
  await expect(chosen).toHaveAttribute("data-progress", "complete");
  await expect(available).toHaveAttribute("data-progress", "available");
  const backgrounds = await Promise.all(
    [chosen, available].map((item) =>
      item.locator(".landmark").evaluate((mark) => getComputedStyle(mark).backgroundColor),
    ),
  );
  expect(backgrounds[0]).not.toBe(backgrounds[1]);
});

test("[UI-09] the rail names saved milestones and leaves blocked chapters out of navigation", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("you"));
  const rail = page.getByRole("navigation", { name: "Chapters" });
  await expect(rail.getByRole("link", { name: "You, direction chosen" })).toBeVisible();
  for (const chapter of ["Roles", "Skills", "Options"]) {
    await expect(rail.getByRole("link", { name: `${chapter}, available` })).toBeVisible();
  }
  for (const chapter of ["Routes", "Plan"]) {
    await expect(rail.getByRole("link", { name: chapter })).toHaveCount(0);
    await expect(rail.getByText(new RegExp(`${chapter}.*Locked`))).toBeVisible();
  }
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("[UI-09] the chapter menu gives the same availability and saved milestone", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("you"));
    await page.getByRole("button", { name: /open chapter menu/ }).click();
    const menu = page.getByRole("navigation", { name: "Chapters" });
    await expect(menu.getByRole("link", { name: "You, direction chosen" })).toBeVisible();
    await expect(menu.getByRole("link", { name: "Roles, available" })).toBeVisible();
    await expect(menu.getByText(/Routes.*Locked/)).toBeVisible();
    await expect(menu.getByRole("link", { name: /Routes/ })).toHaveCount(0);
  });
});

test("[UI-09] a direct Routes URL explains the missing step without a fixture preview", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("routes"));
  await expect(
    page.getByRole("heading", { level: 1, name: "Routes needs an earlier step" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Open Options" })).toBeVisible();
  await expect(page.getByText("Fixture preview: not your routes")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Route A/ })).toHaveCount(0);
});
