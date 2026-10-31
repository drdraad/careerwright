// Keyboard only (UI-06): every chapter and the evidence drawer are reachable with Tab and
// Enter, and closing the drawer returns focus to what opened it; the You chapter completes from
// the keyboard, its views are tabs, and focus lands on what each decision did. Desktop rail and
// phone menu.
import { expect, type Locator, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken, talkedWorkspace } from "./api";
import { chapterUrl, saved, signIn } from "./helpers";

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

/** Opens What we know's answer form, where each answer's Source opens the evidence drawer.
 *  (Task W2E: the route preview, the drawer's earlier example here, left the person's path.) */
async function answerForm(page: Page) {
  await page.getByRole("tab", { name: "What we know" }).click();
  await page.getByRole("button", { name: "Edit answers directly" }).click();
  return page.getByRole("button", { name: "Source for total spending limit" });
}

test("[UI-06] the drawer opens from the keyboard and returns focus when it closes", async ({
  page,
}) => {
  const source = await answerForm(page);
  await tabTo(page, source);
  await page.keyboard.press("Enter");
  const drawer = page.getByRole("dialog", { name: "Where this came from" });
  await expect(drawer.getByRole("heading", { name: "Where this came from" })).toBeFocused();
  await tabTo(page, drawer.getByRole("button", { name: "Close where this came from" }), 20);
  await page.keyboard.press("Enter");
  await expect(drawer).toBeHidden();
  await expect(source).toBeFocused();

  await page.keyboard.press("Enter");
  await expect(drawer).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(source).toBeFocused();
});

test("[UI-06][STATE-06][PROF-04] the You chapter completes from the keyboard, and focus returns to what each step did", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    await emulatorToken("ada"),
    { name: "Keyboard (synthetic)", data_mode: "demo", synthetic: true },
  );
  await page.goto(chapterUrl("you", id));
  await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
  await page.locator("body").focus();

  // Start, then answer: the first question takes focus once the choice is saved.
  await tabTo(page, page.getByRole("button", { name: "Help me explore" }));
  await page.keyboard.press("Enter");
  const opening = page.getByRole("heading", {
    name: "What would you most like to be different about your working life?",
  });
  await expect(opening).toBeFocused();
  await tabTo(page, page.getByRole("textbox", { name: "Reply to Careerwright" }), 10);
  await page.keyboard.type("I am a warehouse supervisor. I enjoy fixing bikes.");
  await tabTo(page, page.getByRole("button", { name: "Send" }), 5);
  await page.keyboard.press("Enter");

  // Decide what the reply proposes: accept both, save; focus lands on what the save did.
  const tray = page.getByRole("region", { name: /To review: 2 changes/ });
  await expect(tray).toBeVisible({ timeout: 60_000 });
  await page.locator("body").focus();
  for (const name of ["Accept current role", "Accept tasks you enjoy"]) {
    const accept = tray.getByRole("button", { name });
    await tabTo(page, accept);
    await page.keyboard.press("Enter");
    await expect(accept).toHaveAttribute("aria-pressed", "true");
  }
  await tabTo(page, tray.getByRole("button", { name: /Save 2 to What we know/ }), 10);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Saved to What we know" })).toBeFocused();
  await tabTo(page, page.getByRole("button", { name: "Undo the last save" }), 5);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Save undone" })).toBeFocused();

  // The views are tabs: arrow keys move between them, and the view follows.
  const conversation = page.getByRole("tab", { name: "Conversation" });
  await page.locator("body").focus();
  await tabTo(page, conversation);
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "What we know" })).toBeFocused();
  await expect(page.getByRole("heading", { name: "What we know" })).toBeVisible();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Suggestions" })).toBeFocused();
  await expect(page.getByRole("heading", { name: "Directions to explore" })).toBeVisible();
  await page.keyboard.press("Home");
  await expect(conversation).toBeFocused();
  await expect(page.getByRole("textbox", { name: "Reply to Careerwright" })).toBeVisible();
});

test("[UI-06][REC1-07] a suggestion opens and becomes a target from the keyboard", async ({
  page,
}) => {
  // App review M4: the keyboard journey stopped before the suggestions.
  test.setTimeout(120_000);
  const id = await talkedWorkspace(await emulatorToken("ada"));
  await page.goto(chapterUrl("you", id));
  await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
  await page.locator("body").focus();
  await tabTo(page, page.getByRole("tab", { name: "Conversation" }));
  await page.keyboard.press("End");
  await expect(page.getByRole("tab", { name: "Suggestions" })).toBeFocused();

  const directions = page.getByRole("region", { name: "Directions to explore" });
  await expect(directions.getByRole("article").first()).toBeVisible({ timeout: 60_000 });
  const second = directions.getByRole("article").last();
  const title = (await second.getByRole("heading").textContent()) ?? "";
  const toggle = second.getByRole("button", { name: title.trim(), exact: true });
  await tabTo(page, toggle);
  await page.keyboard.press("Enter");
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(toggle).toBeFocused(); // the open card's header keeps focus
  await tabTo(page, second.getByRole("button", { name: /Make this a target/ }), 5);
  await page.keyboard.press("Enter");
  await expect(saved(page, 2)).toBeVisible();
  // The choice gives way to the words that say it is saved, and focus goes there (STATE-10).
  await expect(second.getByRole("heading", { name: "Saved as one of your targets" })).toBeFocused();
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

    await page.goto(chapterUrl("you"));
    await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
    const source = await answerForm(page);
    await tabTo(page, source);
    await page.keyboard.press("Enter");
    const drawer = page.getByRole("dialog", { name: "Where this came from" });
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
    await expect(source).toBeFocused();
  });
});
