// The Sprint 1 journey (plan, Sprint 1 demonstrable outcome): sign in as a seeded identity,
// edit the profile, inspect the fixture route, restart every service, reopen the same work.
// Throughout, the browser talks only to the web origin and the local Auth emulator.
import { expect, test } from "@playwright/test";
import { chapterUrl, externalRequests, recordRequests, signIn } from "./helpers";
import { FIXTURE_WORKSPACE, stack } from "./stack";

test("[BND1-14][STATE-07][DUR-03][BND1-11] sign in, edit, inspect a fixture route, restart, reopen", async ({
  page,
}) => {
  test.setTimeout(420_000);
  const requests = recordRequests(page);

  await signIn(page, "ada");
  await page.getByRole("link", { name: /P01 demo \(synthetic\)/ }).click();
  await expect(page).toHaveURL(chapterUrl("you"));
  const saved = page.getByRole("banner").getByText(/^Saved, version \d+$/);
  await expect(saved).toBeVisible();
  const version = Number((await saved.textContent())?.replace(/\D/g, ""));
  await expect(page.getByRole("banner").getByText("Synthetic demo")).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "Live" })).toBeVisible();

  // Edit: a second work area and weekly study hours, saved as the next version.
  await page.getByRole("button", { name: "Add another work area" }).click();
  await page.getByRole("textbox", { name: "Work area 2" }).fill("Leeds");
  await page.getByLabel("How you answer weekly study hours").selectOption("provided");
  await page.getByLabel("Weekly study hours, hours a week").fill("6");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText(`Saved as version ${version + 1}.`)).toBeVisible();
  await expect(page.getByRole("banner").getByText(`Saved, version ${version + 1}`)).toBeVisible();
  await expect(page.getByRole("banner").getByText("Manchester, Leeds")).toBeVisible();

  // Its provenance: a direct entry by the signed-in person, not the fixture.
  await page.getByRole("button", { name: "Source for work areas" }).click();
  const drawer = page.getByRole("dialog", { name: "Where this came from" });
  await expect(drawer.getByText("You entered this directly.")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();

  // The fixture route preview, labelled as such, and route B's figures from the fixture.
  await page
    .getByRole("navigation", { name: "Chapters" })
    .getByRole("link", { name: "Routes" })
    .click();
  await expect(page.getByText("Fixture preview: not your routes")).toBeVisible();
  const routeB = page.getByRole("button", { name: /^Route B/ });
  await routeB.click();
  await expect(drawer.getByText("Synthetic fixture route")).toBeVisible();
  await expect(drawer.getByText("lowest balance of £4,850", { exact: false })).toBeVisible();
  await expect(
    drawer
      .getByRole("definition")
      .filter({ hasText: /^£600$/ })
      .first(),
  ).toBeVisible();
  await drawer.getByRole("button", { name: "Close where this came from" }).click();
  await expect(routeB).toBeFocused();

  // Restart every service. The open page notices, reconnects, and keeps working.
  const stopped = Date.now();
  stack("stop");
  const stopSeconds = (Date.now() - stopped) / 1000;
  await expect(page.getByRole("status").filter({ hasText: /Reconnecting|Connecting/ })).toBeVisible(
    {
      timeout: 60_000,
    },
  );
  // While Nessa is down the work stays on screen, marked as not refreshed (never a blank or
  // an error page in place of it).
  await expect(page.getByRole("heading", { level: 1, name: "Routes" })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Route B/ })).toBeVisible();
  stack("demo");
  await expect(page.getByRole("status").filter({ hasText: "Live" })).toBeVisible({
    timeout: 120_000,
  });
  await expect(page.getByText("Couldn't refresh: showing what was last loaded")).toBeHidden();
  expect(stopSeconds).toBeLessThan(90);

  // Reopen the same work: a fresh load of the same address shows the saved version.
  await page.goto(chapterUrl("you"));
  await expect(page.getByRole("banner").getByText(`Saved, version ${version + 1}`)).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Work area 2" })).toHaveValue("Leeds");
  await expect(page.getByLabel("Weekly study hours, hours a week")).toHaveValue("6");
  expect(page.url()).toContain(FIXTURE_WORKSPACE);

  expect(externalRequests(requests)).toEqual([]);
});
