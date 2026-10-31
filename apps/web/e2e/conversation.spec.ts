// The Sprint 2 journey in demo mode (plan Sprint 2, demonstrable outcome), in the You chapter
// rebuilt as its place in the world (Sprint W, SW.4): choose how to start, talk with the demo
// interviewer, review and confirm its proposals, undo a save, ask for directions in their own
// view, choose one as a target and see the early sketch in what we know. Then the phone layout
// keeps the reply field, its recovery action and "What we know" reachable beside the bottom
// sheet (S0-V01, S0-V02), checked by what is actually on top at their centre, not by
// screenshots.
import { expect, type Locator, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken } from "./api";
import {
  chapterUrl,
  externalRequests,
  liveUpdates,
  recordRequests,
  saved,
  signIn,
  youView,
} from "./helpers";
import { FIXTURE_WORKSPACE, stack } from "./stack";

async function demoWorkspace(name: string): Promise<string> {
  const created = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    await emulatorToken("ada"),
    { name, data_mode: "demo", synthetic: true },
  );
  return created.workspace_id;
}

async function send(page: Page, message: string) {
  await page.getByRole("textbox", { name: "Reply to Careerwright" }).fill(message);
  await page.getByRole("button", { name: "Send" }).click();
}

/** In the viewport and on top at its centre: nothing (such as the sheet) covers it. */
async function expectReachable(page: Page, target: Locator) {
  await target.scrollIntoViewIfNeeded();
  await expectOnTop(page, target);
}

/** Where it is now (after focus scrolled it, say): in the viewport and uncovered. */
async function expectOnTop(page: Page, target: Locator) {
  const box = await target.boundingBox();
  const viewport = page.viewportSize();
  expect(box).not.toBeNull();
  expect(viewport).not.toBeNull();
  if (box === null || viewport === null) return;
  expect(box.y).toBeGreaterThanOrEqual(0);
  expect(box.y + box.height).toBeLessThanOrEqual(viewport.height);
  const onTop = await target.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const hit = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
    return hit !== null && (hit === element || element.contains(hit));
  });
  expect(onTop).toBe(true);
}

test("[PROF-08][MODEL-03][STATE-06][PROF-04][REC1-07][REC1-11][STATE-05][BND1-11] talk, review, undo, explore and sketch", async ({
  page,
}) => {
  test.setTimeout(240_000);
  const requests = recordRequests(page);
  const workspace = await demoWorkspace("Conversation (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  const banner = page.getByRole("banner");

  // The first task leads: how to start. Exploring asks the opening question first.
  await page.getByRole("button", { name: "Help me explore" }).click();
  await expect(
    page.getByRole("heading", {
      name: "What would you most like to be different about your working life?",
    }),
  ).toBeVisible();

  await send(
    page,
    "I am a warehouse supervisor. I enjoy fixing bikes. I could do 5 hours a week in Leeds.",
  );
  // The demo interviewer's checked reply replaces whatever streamed.
  await expect(page.getByText(/^Demo interviewer \(synthetic\): I noted 4 things/)).toBeVisible({
    timeout: 60_000,
  });
  await expect(page.getByText(/not checked yet/)).toHaveCount(0);
  const tray = page.getByRole("region", { name: /To review: 4 changes/ });
  await expect(tray.getByText(/needs your confirmation/).first()).toBeVisible();
  await tray.getByRole("button", { name: "Accept current role" }).click();
  await tray.getByRole("button", { name: "Accept tasks you enjoy" }).click();
  await tray.getByRole("button", { name: "Confirm weekly study hours as a limit" }).click();
  await tray.getByRole("button", { name: "Confirm work areas as a limit" }).click();
  await tray.getByRole("button", { name: /Save 4 to What we know/ }).click();
  await expect(saved(page, 1)).toHaveText("Answers saved");
  await expect(banner.getByText("Leeds")).toBeVisible();
  // Right where the decision was made: what it did, focused, with Undo in its own colour.
  await expect(page.getByRole("heading", { name: "Saved to What we know" })).toBeFocused();

  // Undo restores the answers from before the save, as a new version.
  await page.getByRole("button", { name: "Undo the last save" }).click();
  await expect(saved(page, 2)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Save undone" })).toBeFocused();
  await youView(page, "What we know");
  await expect(page.getByRole("region", { name: "Not asked yet" })).toContainText("Current role");

  // Tell it again, keep the answers, and ask for directions.
  await youView(page, "Conversation");
  await send(page, "I am a warehouse supervisor. I enjoy fixing bikes.");
  const again = page.getByRole("region", { name: /To review: 2 changes/ });
  await again.getByRole("button", { name: "Accept current role" }).click({ timeout: 60_000 });
  await again.getByRole("button", { name: "Accept tasks you enjoy" }).click();
  await again.getByRole("button", { name: /Save 2 to What we know/ }).click();
  await expect(saved(page, 3)).toBeVisible();

  // The suggestions are a view of their own; asking for them is its bright action.
  await youView(page, "Suggestions");
  const suggest = page.getByRole("button", { name: "Suggest directions" });
  await expect(suggest).toHaveClass(/btn-primary/);
  await suggest.click();
  const directions = page.getByRole("region", { name: "Directions to explore" });
  const first = directions.getByRole("article").first();
  await expect(first).toBeVisible({ timeout: 60_000 });
  await expect(first.getByText("Why this could suit you")).toBeVisible();
  // The slate's one written note (S2.7), here the demo explainer's: labelled, its quotations
  // checked, and above how Careerwright found the suggestion, which stays.
  await expect(first.getByText(/Written by the demo explainer \(synthetic\)/)).toBeVisible({
    timeout: 60_000,
  });
  await expect(first.getByText("You said:").first()).toBeVisible();
  await expect(first.getByText("How Careerwright found it")).toBeVisible();
  await expect(directions).not.toContainText(/\d\s?%/);
  const title = (await first.getByRole("heading").textContent()) ?? "";
  // One suggestion is open; its "Make this a target" is the view's one bright action.
  const choose = first.getByRole("button", { name: /Make this a target/ });
  await expect(choose).toHaveClass(/btn-primary/);
  await expect(page.locator("main .btn-primary")).toHaveCount(1);
  await choose.click();
  await expect(saved(page, 4)).toBeVisible();
  await expect(banner.getByText(title, { exact: false })).toBeVisible();

  // The early sketch: ESCO's requirements for the target, every step not resolved yet.
  await youView(page, "What we know");
  const sketch = page.getByRole("region", { name: "Early sketch, not a checked route" });
  await expect(sketch.getByText("What this work usually asks for, from ESCO:")).toBeVisible();
  await expect(sketch.getByText(/Not resolved yet/).first()).toBeVisible();

  expect(externalRequests(requests)).toEqual([]);
});

test("[PROF-09] a message with a risk stem is sent as usual, with the support panel and a smaller step", async ({
  page,
}) => {
  const workspace = await demoWorkspace("Support (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  await page.getByRole("button", { name: "Help me explore" }).click();
  const opening = page.getByRole("heading", {
    name: "What would you most like to be different about your working life?",
  });
  await expect(opening).toBeVisible();

  await send(page, "Some days I just want to die.");

  const panel = page.getByRole("region", { name: "Support is available" });
  await expect(panel).toContainText("Samaritans: Call 116 123");
  await expect(panel).toContainText("Call 999 or go to A&E");
  await expect(page.getByText(/^You, \d\d:\d\d$/)).toHaveCount(1); // sent, with no extra step
  // The demo interviewer got the smaller-step instruction for this turn: it acknowledges the
  // message, offers a smaller step and asks no question.
  await expect(
    page.getByText(/^Demo interviewer \(synthetic\): Thank you for telling me\./),
  ).toBeVisible({ timeout: 60_000 });
  await panel.getByRole("button", { name: "Dismiss the support note" }).click();
  await expect(panel).toHaveCount(0);
  await expect(page.getByRole("textbox", { name: "Reply to Careerwright" })).toBeFocused();
  await expect(opening).toHaveCount(0);
  await expect(page.locator(".question")).toHaveCount(0);
});

test("[UI-09] V-08: the strip keeps its height when updates are interrupted", async ({
  browser,
}) => {
  const height = async (blocked: boolean) => {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    if (blocked) await page.route("**/events/stream*", (route) => route.abort());
    await signIn(page, "ada", chapterUrl("you"));
    await expect(saved(page)).toHaveText("Answers saved");
    await expect(liveUpdates(page, blocked ? "Reconnecting" : "Live")).toBeVisible();
    const box = await page.getByRole("banner").boundingBox();
    await context.close();
    return box?.height ?? 0;
  };

  const live = await height(false);
  const reconnecting = await height(true);

  expect(live).toBeGreaterThan(0);
  expect(reconnecting).toBe(live);
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test.beforeAll(() => {
    stack("reset-demo");
  });

  test("[S0-V01][S0-V02][UI-06][UI-09] what we know, the reply field and Try again stay reachable beside the sheet", async ({
    page,
  }) => {
    test.setTimeout(180_000);
    const token = await emulatorToken("ada");
    await asBrowser("PUT", `/v1/workspaces/${FIXTURE_WORKSPACE}/interview/preferences`, token, {
      expected_version: 0,
      entry_mode: "unsure",
      conversation_mode: null,
      paused: false,
    });
    await signIn(page, "ada", chapterUrl("you"));
    await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();

    // S0-V01: "What we know" is on the phone too (its own view), and the way in to edit it.
    await expectReachable(page, page.getByRole("tab", { name: "What we know" }));
    await youView(page, "What we know");
    await expectReachable(page, page.getByRole("heading", { name: "What we know" }));
    await page.getByRole("button", { name: "Edit answers directly" }).click();
    await page.getByRole("button", { name: "Source for total spending limit" }).click();
    const sheet = page.getByRole("dialog", { name: "Where this came from" });
    await expect(sheet).toBeVisible();
    // S0-V02: with the sheet open at its peek, the reply field and Send are not under it.
    await youView(page, "Conversation");
    await expectReachable(page, page.getByRole("textbox", { name: "Reply to Careerwright" }));
    await expectReachable(page, page.getByRole("button", { name: "Send" }));

    // A failed reply: Try again, the recovery action, is reachable beside the sheet too.
    const failed = {
      turn_id: "00000000-0000-4000-8000-0000000000f1",
      message_id: "00000000-0000-4000-8000-0000000000f2",
      message: "I could work in Leeds.",
      profile_version: 1,
      created_at: "2027-01-01T10:00:00Z",
      run: {
        run_id: "00000000-0000-4000-8000-0000000000f1",
        kind: "interview_turn",
        status: "failed",
        failure_class: "invalid_model_output",
        data_mode: "demo",
        synthetic: true,
        model_id: "careerwright-fixture-interviewer-1",
        model_mode: "fixture",
        created_at: "2027-01-01T10:00:00Z",
        started_at: null,
        finished_at: null,
        attempts: [],
        output: null,
        profile_version: 1,
      },
      proposal: null,
      decision: null,
    };
    await page.route("**/interview/turns?*", (route) =>
      route.fulfill({ json: { items: [failed], next_cursor: null } }),
    );
    await page.route("**/interview/turns/*/reply", (route) =>
      route.fulfill({
        json: {
          turn_id: failed.turn_id,
          completeness: "incomplete",
          seq: 1,
          text: null,
          updated_at: null,
        },
      }),
    );
    await page.reload();
    await expect(page.getByText("The reply didn't pass Careerwright's checks twice")).toBeVisible();
    // Nothing covers Try again either, with the sheet closed.
    const tryAgain = page.getByRole("button", { name: "Try again" });
    const yourself = page.getByRole("button", { name: "Add the details yourself" });
    await expectReachable(page, tryAgain);
    await expectReachable(page, yourself);
    // Keyboard (B-M6): focus alone brings Try again into view, uncovered.
    await page.evaluate(() => window.scrollTo(0, 0));
    await tryAgain.focus();
    await expectOnTop(page, tryAgain);
    // "Add the details yourself" opens the answer form in What we know.
    await yourself.click();
    await expect(page.getByRole("tab", { name: "What we know" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await page.getByRole("button", { name: "Source for total spending limit" }).click();
    await expect(sheet).toBeVisible();
    await youView(page, "Conversation");
    await expectReachable(page, tryAgain);
    await expectReachable(page, yourself);
    await expectReachable(page, page.getByRole("textbox", { name: "Reply to Careerwright" }));
    await page.evaluate(() => window.scrollTo(0, 0));
    await tryAgain.focus();
    await expectOnTop(page, tryAgain);
    const sent = page.waitForRequest(
      (request) => request.method() === "POST" && request.url().endsWith("/interview/turns"),
    );
    await page.keyboard.press("Enter");
    await sent; // Enter on the focused Try again sends the message again
  });
});

test("[UI-09] V-02: a failed profile load recovers in place with Try again", async ({ page }) => {
  let failing = true;
  await page.route("**/v1/workspaces/*/profile", (route) =>
    failing ? route.abort() : route.continue(),
  );
  await signIn(page, "ada", chapterUrl("you"));
  await expect(page.getByRole("banner").getByText("Your answers couldn't be loaded")).toBeVisible({
    timeout: 30_000,
  });
  const where = page.url();

  failing = false;
  await page.getByRole("button", { name: "Try again" }).click();

  await expect(page.getByRole("tab", { name: "What we know" })).toBeVisible();
  await expect(saved(page)).toHaveText("Answers saved");
  expect(page.url()).toBe(where); // recovered without navigating away
});
