// The Sprint 2 journey in demo mode (plan Sprint 2, demonstrable outcome), in the You chapter
// rebuilt as its place in the world (Sprint W, SW.4): choose how to start, talk with the demo
// interviewer, review and confirm its proposals, undo a save, ask for directions in their own
// view, choose one as a target and see the early sketch in what we know. Then the phone layout
// keeps the reply field, its recovery action and "What we know" reachable beside the bottom
// sheet (S0-V01, S0-V02), checked by what is actually on top at their centre, not by
// screenshots.
import { expect, type Locator, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken, roleQuestionWorkspace, talkedWorkspace } from "./api";
import {
  brightFills,
  chapterUrl,
  externalRequests,
  liveUpdates,
  recordRequests,
  saved,
  signIn,
  skipFirstQuestion,
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

  // The first task leads: how to start (after the first question, skipped here; Task 6d slice
  // B). Exploring asks the opening question first.
  await skipFirstQuestion(page);
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
  // One decision at a time (design review I4): the next question waits for the tray.
  await expect(page.locator(".question")).toHaveCount(0);
  await tray.getByRole("button", { name: "Accept current role" }).click();
  await tray.getByRole("button", { name: "Accept tasks you enjoy" }).click();
  await tray.getByRole("button", { name: "Confirm weekly study hours as a limit" }).click();
  await tray.getByRole("button", { name: "Confirm work areas as a limit" }).click();
  // Four chosen, and still one bright fill in view: Save (design review M1).
  expect(await brightFills(page)).toBe(1);
  await tray.getByRole("button", { name: /Save 4 to What we know/ }).click();
  await expect(saved(page, 1)).toHaveText("Answers saved");
  await expect(banner.getByText("Leeds")).toBeVisible();
  // Right where the decision was made: what it did, focused, with Undo in its own colour; the
  // next question follows it.
  await expect(page.getByRole("heading", { name: "Saved to What we know" })).toBeFocused();
  await expect(page.locator(".question")).toHaveCount(1);

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
  // The other views stay mounted, hidden: only the view shown counts.
  await expect(page.locator("main .btn-primary:visible")).toHaveCount(1);
  expect(await brightFills(page)).toBe(1);
  await choose.click();
  await expect(saved(page, 4)).toBeVisible();
  await expect(banner.getByText(title, { exact: false })).toBeVisible();
  // Confirmed where it was chosen, with what it usually asks for, and never "out of date": the
  // only change since the slate was this choice from it (STATE-10).
  await expect(first.getByRole("heading", { name: "Saved as one of your targets" })).toBeFocused();
  await expect(first.getByText("What this work usually asks for, from ESCO:")).toBeVisible();
  await expect(directions.getByText("Based on your earlier answers")).toHaveCount(0);
  await expect(directions.getByRole("button", { name: "Suggest again" })).toHaveCount(0);

  // The early sketch, one step away in What we know (a second idea there, design review M6):
  // ESCO's requirements for the target, every step not resolved yet.
  await youView(page, "What we know");
  await page.getByText("The early sketch for your target").click();
  const sketch = page.getByRole("region", { name: "Early sketch, not a checked route" });
  await expect(sketch.getByText("What this work usually asks for, from ESCO:")).toBeVisible();
  await expect(sketch.getByText(/Not resolved yet/).first()).toBeVisible();

  expect(externalRequests(requests)).toEqual([]);
});

/** Accepts or confirms every change the reply proposes and saves them. */
async function keepAll(page: Page) {
  const tray = page.getByRole("region", { name: /To review:/ });
  await expect(tray).toBeVisible({ timeout: 60_000 });
  for (const choose of await tray.getByRole("button", { name: /^(Accept|Confirm)/ }).all()) {
    await choose.click();
  }
  await tray.getByRole("button", { name: /^Save \d+ to What we know/ }).click();
  await expect(page.getByRole("heading", { name: "Saved to What we know" })).toBeFocused();
}

/** The question in view, or null once there is none. */
async function questionShown(page: Page): Promise<string | null> {
  const question = page.locator(".question h2");
  return (await question.count()) === 0 ? null : ((await question.textContent()) ?? "");
}

test("[STATE-09][STATE-08][BND1-02] the demo takes a target in the person's words and Skip, and never asks the same question twice", async ({
  page,
}) => {
  test.setTimeout(300_000);
  const workspace = await demoWorkspace("Never loops, sure (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  // Before the first answer: what Careerwright is for (session 2: "not sure" what the start
  // page was for) and covers, and the entry choice as the bright action, never Send on an
  // empty field (F17).
  await expect(
    page.getByText(
      "Careerwright helps you find work that could suit you, see what it would take, and plan a route you can afford.",
    ),
  ).toBeVisible();
  await expect(page.getByText("Careerwright covers England for now.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Send" })).not.toHaveClass(/btn-primary/);
  await skipFirstQuestion(page);
  await page.getByRole("button", { name: "I know my direction" }).click();
  const opening = "Which role are you aiming for, and at what level?";
  await expect(page.getByRole("heading", { name: opening })).toBeVisible();
  const asked = [await questionShown(page)];
  expect(asked[0]).toBe(opening);

  await send(page, "I want to be a nurse");
  await keepAll(page);
  // Then the last example under each question (Skip, Unknown or Prefer not to say), until the
  // demo has nothing left to ask.
  for (let question = await questionShown(page); question !== null; ) {
    expect(asked, "never the same question twice").not.toContain(question);
    asked.push(question);
    await page.getByRole("group", { name: "Example replies" }).getByRole("button").last().click();
    await keepAll(page);
    question = await questionShown(page);
  }
  expect(asked).toHaveLength(5); // the target, then the four practical questions, each once
  await youView(page, "What we know");
  await expect(
    page.getByRole("tabpanel", { name: "What we know" }).getByText("nurse", { exact: true }),
  ).toBeVisible();
});

test("[STATE-09] exploring by example replies reaches the role question, whose Show me suggestions opens and starts them", async ({
  page,
}) => {
  test.setTimeout(300_000);
  const workspace = await demoWorkspace("Never loops, explore (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  await skipFirstQuestion(page);
  await page.getByRole("button", { name: "Help me explore" }).click();
  await expect(
    page.getByRole("heading", {
      name: "What would you most like to be different about your working life?",
    }),
  ).toBeVisible();
  const role = "Do you have a role in mind, or would you like to explore?";
  const asked: string[] = [];
  for (let question = await questionShown(page); question !== role; ) {
    expect(question).not.toBeNull();
    expect(asked, "never the same question twice").not.toContain(question);
    asked.push(question ?? "");
    await page.getByRole("group", { name: "Example replies" }).getByRole("button").first().click();
    await keepAll(page);
    question = await questionShown(page);
  }
  expect(asked).toHaveLength(5); // the opening, then the four practical questions

  // Two ways on, which open existing views; neither commits anything by itself.
  await expect(page.getByRole("group", { name: "Example replies" })).toHaveCount(0);
  const started = page.waitForRequest(
    (request) => request.method() === "POST" && request.url().endsWith("/discoveries"),
  );
  await page.getByRole("button", { name: "Show me suggestions" }).click();
  await started;
  await expect(page.getByRole("tab", { name: "Suggestions" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByRole("heading", { name: "Directions to explore" })).toBeFocused();
  await expect(page.getByRole("button", { name: "Suggest directions" })).toHaveCount(0);
});

/** Sends a message and returns the demo interviewer's checked reply to it (each message
 *  sent here is different, so its turn is found by its words). */
async function replyTo(page: Page, message: string): Promise<string> {
  await send(page, message);
  const words = page
    .locator(".turn-you", { has: page.getByText(message, { exact: true }) })
    .locator("xpath=following-sibling::div[contains(@class, 'turn-careerwright')]")
    .locator("p");
  await expect(words).toHaveText(/^Demo interviewer \(synthetic\): /, { timeout: 60_000 });
  await expect(page.getByText(/not checked yet/)).toHaveCount(0);
  return (await words.textContent()) ?? "";
}

/** Every question the demo asks already answered: nothing is left to ask (demo mode). */
async function answeredWorkspace(token: string): Promise<string> {
  const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    token,
    { name: "Everything answered (synthetic)", data_mode: "demo", synthetic: true },
  );
  const base = `/v1/workspaces/${id}`;
  const blank = await asBrowser<{ document: Record<string, unknown> }>(
    "GET",
    `${base}/profile`,
    token,
  );
  const profile: Record<string, unknown> = Object.fromEntries(
    Object.keys(blank.document)
      .filter((field) => field !== "schema_version")
      .map((field) => [field, { state: "unasked" }]),
  );
  profile.current_role = { state: "provided", value: "warehouse supervisor" };
  profile.cities = { state: "provided", value: ["Leeds"] };
  profile.weekly_study_hours = { state: "unknown" };
  profile.direct_spend_cap = { state: "prefer_not_to_say" };
  profile.target_titles = { state: "provided", value: ["nurse"] };
  await asBrowser("PUT", `${base}/profile`, token, { expected_version: 0, profile });
  await asBrowser("PUT", `${base}/interview/preferences`, token, {
    expected_version: 0,
    entry_mode: "unsure",
    conversation_mode: null,
    paused: false,
  });
  return id;
}

test("[STATE-09] the demo's way on names only what is in sight: the role question's two buttons, and after the last question the views (app review I1)", async ({
  page,
}) => {
  test.setTimeout(180_000);
  const token = await emulatorToken("ada");

  // The first probe: at the role question, the natural typed answer. Its two buttons are in
  // sight there, never example replies, so the reply names the buttons.
  await signIn(page, "ada", chapterUrl("you", await roleQuestionWorkspace(token)));
  const role = page.getByRole("heading", {
    name: "Do you have a role in mind, or would you like to explore?",
  });
  await expect(role).toBeVisible();
  const explore = await replyTo(page, "Explore");
  await expect(role).toBeVisible(); // still unanswered: asked again, with the way on
  await expect(page.getByRole("group", { name: "Example replies" })).toHaveCount(0);
  expect(explore).not.toMatch(/example repl/i);
  for (const name of ["Show me suggestions", "Name a role"]) {
    expect(explore, "the reply names the buttons in sight").toContain(name);
    await expect(page.getByRole("button", { name })).toBeVisible();
  }

  // The second probe: after the last question nothing is in front, so there are no example
  // replies and Skip has nothing to answer. Every reply says what to do next, in views that
  // are in sight, and never sends the person back to Skip (it looped).
  await page.goto(chapterUrl("you", await answeredWorkspace(token)));
  const replies = [await replyTo(page, "What next?")];
  await expect(page.locator(".question")).toHaveCount(0);
  replies.push(await replyTo(page, "Skip"), await replyTo(page, "Skip."));
  for (const said of replies) {
    expect(said, "never points to Skip or to examples").not.toMatch(/Skip|example repl/i);
    expect(said).toContain("Suggestions");
    expect(said).toContain("What we know");
  }
  await expect(page.locator(".question")).toHaveCount(0);
  await expect(page.getByRole("group", { name: "Example replies" })).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "Suggestions" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "What we know" })).toBeVisible();
});

test("[PROF-09] a message with a risk stem is sent as usual, with the support panel and a smaller step", async ({
  page,
}) => {
  const workspace = await demoWorkspace("Support (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  await skipFirstQuestion(page);
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

test("[UI-09] V-08: the strip keeps its height when updates are interrupted, on a phone too", async ({
  browser,
}) => {
  // App review M1: on a phone, "Updates: Reconnecting" pushed the account menu to a second row.
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    const height = async (blocked: boolean) => {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      if (blocked) await page.route("**/events/stream*", (route) => route.abort());
      await signIn(page, "ada", chapterUrl("you"));
      await expect(saved(page)).toHaveText("Answers saved");
      await expect(liveUpdates(page, blocked ? "Reconnecting" : "Live")).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      const box = await page.getByRole("banner").boundingBox();
      await context.close();
      return box?.height ?? 0;
    };

    const live = await height(false);
    const reconnecting = await height(true);

    expect(live, `${viewport.width} px`).toBeGreaterThan(0);
    expect(reconnecting, `${viewport.width} px: one row while reconnecting`).toBe(live);
  }
});

test("[UI-09] on a phone a stopped update says why in words read whole, not cut off (re-review N2)", async ({
  browser,
}) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.route("**/events/stream*", (route) =>
    route.fulfill({
      status: 404,
      json: {
        error: {
          code: "NOT_FOUND",
          message: "",
          retryable: false,
          stage: "request",
          correlation_id: "n2",
          details: {},
        },
      },
    }),
  );
  await signIn(page, "ada", chapterUrl("you"));
  const stopped = liveUpdates(page, /^Updates: Stopped: access to this workspace ended$/);
  await expect(stopped).toBeVisible();
  const words = stopped.locator("span").last();
  const cut = await words.evaluate((element) => element.scrollWidth > element.clientWidth + 1);
  expect(cut, "the stopped state's reason is shown whole").toBe(false);
  const box = await words.boundingBox();
  expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(390);
  await expect(page.getByRole("button", { name: "Account and settings" })).toBeVisible();
  await context.close();
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
    // "Add the details yourself" opens the answer form in What we know, and focus goes with
    // it (app review I2: it fell to the page).
    await yourself.click();
    await expect(page.getByRole("tab", { name: "What we know" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(page.getByRole("heading", { name: "Edit your answers" })).toBeFocused();
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

test.describe("phone, first screen", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  /** At the top of the view, wholly in the first screen and on top at its centre. */
  async function firstScreen(page: Page, target: Locator) {
    await expect(target).toBeVisible({ timeout: 60_000 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await expectOnTop(page, target);
  }

  test("[UI-12][F7] at 390 × 844 each view's first decision is in the first screen", async ({
    page,
  }) => {
    test.setTimeout(180_000);
    const token = await emulatorToken("ada");
    // The start: the first question's field (Task 6d slice B), then the entry choice.
    await signIn(page, "ada", chapterUrl("you", await demoWorkspace("Start (synthetic)")));
    const titleField = page.getByRole("combobox", { name: "Your job title" });
    await firstScreen(page, titleField);
    // The person's own answer to the type-ahead is in the first screen however many titles it
    // offers (fix round 2, design re-review R-I2): "Use my own words" over a list of UK job
    // titles, and "None of these is my job" over a partial list of ESCO's guesses.
    await titleField.fill("Registered nurse");
    await expect(
      page.getByRole("option", { name: /^Registered nurse\s*,\s*UK job title \(ONS\)$/ }),
    ).toBeVisible();
    await firstScreen(
      page,
      page.getByRole("option", { name: "Use my own words: “Registered nurse”" }),
    );
    await titleField.fill("Bookkeeping assistant");
    await expect(
      page.getByText("Careerwright couldn't match that title in ESCO. Is it one of these?"),
    ).toBeVisible();
    await firstScreen(page, page.getByRole("option", { name: /^None of these is my job/ }));
    await titleField.fill("");
    await skipFirstQuestion(page);
    await firstScreen(page, page.getByRole("button", { name: "Help me explore" }));

    // The closest step and the entry choice with its kept-words line (Task 6d slice B fix
    // round 1, design review M-3): their decisions are in the first screen too.
    await page.goto(chapterUrl("you", await demoWorkspace("Closest, phone (synthetic)")));
    await page.getByRole("combobox", { name: "Your job title" }).fill("Registered nurse");
    await page
      .getByRole("option", { name: /^Registered nurse\s*,\s*UK job title \(ONS\)$/ })
      .click();
    await expect(page.getByRole("heading", { name: "Which of these is closest?" })).toBeFocused();
    const none = page.getByRole("button", { name: "None of these is my job" });
    await firstScreen(page, none);
    await firstScreen(
      page,
      page.getByRole("region", { name: "Nursing professionals" }).getByRole("button").first(),
    );
    await none.click();
    await firstScreen(
      page,
      page.getByText(
        "Careerwright found “Registered nurse” in the UK job-title index and keeps it as your role, in your words. What this work asks for isn't known yet.",
      ),
    );
    await firstScreen(page, page.getByRole("button", { name: "Help me explore" }));

    // What we know in the fixture workspace: four answers, two of them limits explained, and a
    // long "Not asked yet" (design review I3: three short answers fitted where these didn't).
    await page.goto(chapterUrl("you"));
    await youView(page, "What we know");
    await expect(page.getByRole("region", { name: "Not asked yet" })).toBeVisible();
    await firstScreen(page, page.getByRole("button", { name: "Edit answers directly" }));

    // A reply to review and the suggestions, each at the top of its view.
    await page.goto(chapterUrl("you", await talkedWorkspace(token)));
    const tray = page.getByRole("region", { name: /To review:/ });
    await firstScreen(page, tray.getByRole("button", { name: /^(Accept|Confirm)/ }).first());
    await youView(page, "Suggestions");
    const directions = page.getByRole("region", { name: "Directions to explore" });
    await firstScreen(
      page,
      directions
        .getByRole("article")
        .first()
        .getByRole("button", { name: /Make this a target/ }),
    );
  });
});

test("[UI-12] in a window too short for a band (a phone turned sideways) the console starts in the first screen (re-review N3)", async ({
  browser,
}) => {
  const context = await browser.newContext({ viewport: { width: 844, height: 390 } });
  const page = await context.newPage();
  await signIn(page, "ada", chapterUrl("you", await demoWorkspace("Sideways (synthetic)")));
  const start = page.getByRole("combobox", { name: "Your job title" });
  await expect(start).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await expectOnTop(page, start);
  await context.close();
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
