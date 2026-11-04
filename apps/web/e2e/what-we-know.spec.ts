// What we know's targets and its answer form in the demo, against the real stack (Task W2F;
// session W2, findings 2 and 9): a target removed on its saved suggestion and in What we
// know, each with Undo where it was done, the suggestions staying current throughout; and the
// answer form's Save in reach while the form is open, on a wide screen and on a phone.
import { expect, test } from "@playwright/test";
import { asBrowser, chosenTargetWorkspace, emulatorToken } from "./api";
import { chapterUrl, inReach, saved, signIn, youView } from "./helpers";

test("[STATE-10][PROF-07] a target is removed on its suggestion and in What we know, each with Undo, and the suggestions stay current", async ({
  page,
}) => {
  test.setTimeout(180_000);
  // Answers (version 1) and a suggestion made a target from the slate (version 2).
  const { workspace, title } = await chosenTargetWorkspace(await emulatorToken("ada"));
  await signIn(page, "ada", chapterUrl("you", workspace));
  await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
  await expect(saved(page, 2)).toBeVisible();

  // On the saved suggestion: Remove, through the profile's save; what it did is said in place,
  // and Make this a target is the bright action again, never Suggest again.
  await youView(page, "Suggestions");
  const directions = page.getByRole("region", { name: "Directions to explore" });
  const first = directions.getByRole("article").first();
  await expect(first.getByRole("heading", { name: "Saved as one of your targets" })).toBeVisible({
    timeout: 60_000,
  });
  await first.getByRole("button", { name: /^Remove .* from your targets$/ }).click();
  await expect(saved(page, 3)).toBeVisible();
  await expect(
    first.getByRole("heading", { name: `Removed “${title}” from your targets` }),
  ).toBeFocused();
  await expect(first.getByRole("button", { name: /Make this a target/ })).toHaveClass(
    /btn-primary/,
  );
  await expect(directions.getByText("Based on your earlier answers")).toHaveCount(0);
  await expect(directions.getByRole("button", { name: "Suggest again" })).toHaveCount(0);
  // Undo, in place: the target is back, saved where it was chosen.
  await first.getByRole("button", { name: `Undo removing “${title}”` }).click();
  await expect(saved(page, 4)).toBeVisible();
  await expect(
    first.getByRole("heading", { name: `Undone: “${title}” is one of your targets again` }),
  ).toBeFocused();
  await expect(first.getByRole("heading", { name: "Saved as one of your targets" })).toBeVisible();

  // In What we know: the target in its own list with its Remove. Removing the only one leaves
  // the target roles Unknown (Task W2F's ruling), and the suggestions stay current.
  await youView(page, "What we know");
  const targets = page.getByRole("region", { name: "Your targets" });
  await targets.getByRole("button", { name: `Remove ${title} from your targets` }).click();
  await expect(saved(page, 5)).toBeVisible();
  await expect(
    targets.getByRole("heading", { name: `Removed “${title}” from your targets` }),
  ).toBeFocused();
  await expect(targets.getByText("Unknown", { exact: true })).toBeVisible();
  await expect(targets.getByRole("button", { name: `Undo removing “${title}”` })).toHaveClass(
    /btn-undo/,
  );
  await youView(page, "Suggestions");
  await expect(first.getByRole("button", { name: /Make this a target/ })).toHaveClass(
    /btn-primary/,
  );
  await expect(directions.getByText("Based on your earlier answers")).toHaveCount(0);
});

test("[STATE-06] earlier answers can be previewed and restored with their saved source", async ({
  page,
}) => {
  const token = await emulatorToken("ada");
  const { workspace } = await chosenTargetWorkspace(token);
  const base = `/v1/workspaces/${workspace}`;
  const first = await asBrowser<{
    document: { current_role: { source_ref_id: string | null } };
  }>("GET", `${base}/profile/versions/1`, token);
  await signIn(page, "ada", chapterUrl("you", workspace));
  await youView(page, "What we know");
  await page.getByText("Earlier answers", { exact: true }).click();
  await page.getByRole("button", { name: "View version 1" }).click();
  const preview = page.getByRole("region", { name: "Answers in version 1" });
  await expect(preview).toBeVisible();
  await preview.getByRole("button", { name: "Restore version 1" }).click();
  await expect(preview.getByText("Restore version 1 as a new saved version?")).toBeVisible();
  await preview.getByRole("button", { name: "Confirm restore" }).click();
  await expect(saved(page, 3)).toBeVisible();
  await expect(
    page.getByRole("status").filter({ hasText: "Version 1 was restored as a new saved version." }),
  ).toBeVisible();
  const restored = await asBrowser<{
    version: number;
    document: { current_role: { source_ref_id: string | null } };
  }>("GET", `${base}/profile`, token);
  expect(restored.version).toBe(3);
  expect(restored.document.current_role.source_ref_id).toBe(
    first.document.current_role.source_ref_id,
  );
});

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test(`[UI-06][UI-09] the answer form's Save stays in reach while the form is open, at ${viewport.width} px`, async ({
    browser,
  }) => {
    const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
    const page = await context.newPage();
    // The fixture workspace's answers: opening the form saves nothing.
    await signIn(page, "ada", chapterUrl("you"));
    await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
    await youView(page, "What we know");
    await page.getByRole("button", { name: "Edit answers directly" }).click();
    const save = page.getByRole("button", { name: "Save changes" });
    await expect(save).toBeVisible();
    // Each field at the top of the window, from the first to the last: Save is in view.
    for (const field of ["target_titles", "qualifications", "monthly_payment_cap", "work_style"]) {
      await page
        .locator(`[data-field='${field}']`)
        .evaluate((element) => element.scrollIntoView({ block: "start" }));
      expect(await inReach(save), `${field} at the top`).toBe(true);
    }
    await context.close();
  });
}
