import { expect, test } from "@playwright/test";
import { chosenTargetWorkspace, emulatorToken } from "./api";
import { chapterUrl, signIn } from "./helpers";

test("[OPTN-03][OPTN-09] a person adds an option and sees its unreviewed source on the checkpoint", async ({
  page,
}) => {
  const { workspace, title } = await chosenTargetWorkspace(await emulatorToken("ada"));
  await signIn(page, "ada", chapterUrl("options", workspace));
  await expect(page.getByRole("heading", { level: 1, name: "Options" })).toBeVisible();
  await expect(page.getByRole("heading", { name: `For ${title}` })).toBeVisible();

  await page.getByRole("button", { name: "Add your own option" }).click();
  await page.getByLabel("What is it called?").fill("Evening course");
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByLabel(/Who offers it/).fill("Local college");
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByLabel(/Paste the page text/).fill("Local college evening course page.");
  await page.getByRole("button", { name: "Save this option" }).click();

  await expect(page.getByRole("button", { name: /Evening course/ })).toBeVisible();
  await expect(
    page
      .getByRole("region", { name: "Evening course details" })
      .getByText(/Your own option, not reviewed/),
  ).toBeVisible();
  await expect(page.getByText("Local college", { exact: true })).toBeVisible();
  await expect(page.getByText(/Not known yet: start date/)).toBeVisible();
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("an option is visible in the first screen without repeated planning guidance", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("options"));
    const first = page.locator(".option-detail").getByRole("heading", { level: 3 }).first();
    await expect(first).toBeVisible();
    const box = await first.boundingBox();
    expect(box).not.toBeNull();
    expect(box?.y).toBeGreaterThanOrEqual(0);
    expect(box ? box.y + box.height : null).toBeLessThanOrEqual(844);
    await expect(
      page.locator(".option-detail").getByText(/Not known yet: start date/),
    ).toBeVisible();
    await expect(page.getByRole("region", { name: "Your next step" })).toHaveCount(0);
  });
});

test("a person can revise a supplied option date after returning", async ({ page }) => {
  await signIn(page, "ada", chapterUrl("options"));
  const detail = page.locator(".option-detail");
  const first = detail.locator("form.figure-box").first();
  await expect(first).toBeVisible();
  const another = first.getByLabel(/Another day/);
  if (await another.count()) await another.check();
  await first.locator('input[type="date"]').fill("2027-09-01");
  await first.getByRole("button", { name: "Save" }).click();
  await expect(detail.getByText("1 September 2027")).toBeVisible();

  await page.reload();
  await detail.getByText("Change your figures").click();
  const revision = detail.locator("form.figure-box").filter({ hasText: "Start date: your figure" });
  await expect(revision.locator('input[type="date"]')).toHaveValue("2027-09-01");
  await revision.locator('input[type="date"]').fill("2027-10-01");
  await revision.getByRole("button", { name: "Save" }).click();
  await expect(detail.getByText("1 October 2027")).toBeVisible();
});
