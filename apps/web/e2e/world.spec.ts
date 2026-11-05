// The persistent atmosphere and saved career facts across chapters: controls, motion settings,
// support, keyboard access and readable facts on the real demo stack. Nothing leaves this machine.
import { type Browser, expect, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken, talkedWorkspace } from "./api";
import {
  chapterUrl,
  externalRequests,
  liveUpdates,
  overprintedLabels,
  recordRequests,
  saved,
  signIn,
  skipFirstQuestion,
  youView,
} from "./helpers";

const CHAPTERS = ["You", "Roles", "Skills", "Options"] as const;
const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
] as const;
/** Plan section 5: long role names and three targets. Synthetic, in a workspace of Ada's. */
const LONG_TARGETS = [
  "Data quality analyst",
  "Senior data governance and information quality manager",
  "Clinical data standards and interoperability specialist",
];

const world = (page: Page) => page.locator(".decision-atmosphere");
const light = (page: Page) => page.locator(".decision-atmosphere-light");

/** A new synthetic demo workspace whose three targets have long names. */
async function longTargetsWorkspace(): Promise<string> {
  const token = await emulatorToken("ada");
  const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    token,
    { name: "Three long targets (synthetic)", data_mode: "demo", synthetic: true },
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
  profile.target_titles = { state: "provided", value: LONG_TARGETS };
  profile.cities = { state: "provided", value: ["Manchester"] };
  await asBrowser("PUT", `${base}/profile`, token, { expected_version: 0, profile });
  return id;
}

/** Opens the account menu and turns calm mode on or off. */
async function toggleCalm(page: Page) {
  await page.getByRole("button", { name: "Account and settings" }).click();
  await page.getByRole("button", { name: /^Calm mode/ }).click();
  await page.keyboard.press("Escape");
}

/** "Hold the world still": in the strip on a desktop, in the account menu below one (F14). */
async function holdStill(page: Page) {
  const hold = page.getByRole("button", { name: /^Hold the world still/ });
  const inMenu = (await hold.count()) === 0;
  if (inMenu) await page.getByRole("button", { name: "Account and settings" }).click();
  await hold.click();
  if (inMenu) await page.keyboard.press("Escape");
}

/** Menus receive pointer input above the atmosphere and return keyboard focus on Escape. */
async function menuOnTop(page: Page, opener: { name: string | RegExp }) {
  const trigger = page.getByRole("button", opener);
  await trigger.click();
  const menu = page.locator(".popover");
  await expect(menu).toBeVisible();
  const onTop = await menu.evaluate((element) => {
    const box = element.getBoundingClientRect();
    return element.contains(
      document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2),
    );
  });
  await page.keyboard.press("Escape");
  await expect(menu).toHaveCount(0);
  await expect(trigger).toBeFocused();
  return onTop;
}

test.describe("moving", () => {
  test.use({ reducedMotion: "no-preference" });

  test("[WLD-01][UI-09][UI-05][BND1-11] one atmosphere stays behind every chapter and navigation names its current place", async ({
    page,
  }) => {
    const requests = recordRequests(page);
    await signIn(page, "ada", chapterUrl("you"));
    await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
    await expect(light(page)).toHaveCSS("animation-play-state", "running");
    // Changing chapter keeps the same atmosphere and its current motion state.
    await world(page).evaluate((element) => {
      (element as HTMLElement & { persisted?: boolean }).persisted = true;
    });

    const rail = page.getByRole("navigation", { name: "Chapters" });
    for (const chapter of CHAPTERS) {
      await rail.getByRole("link", { name: new RegExp(`^${chapter}`) }).click();
      await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
      await expect(rail.getByRole("link", { name: new RegExp(`^${chapter}`) })).toHaveAttribute(
        "aria-current",
        "page",
      );
      expect(
        await page
          .locator(".decision-atmosphere")
          .evaluate((element) => (element as HTMLElement & { persisted?: boolean }).persisted),
      ).toBe(true);
    }
    // The chapter keeps the person's chosen target in view.
    await expect(page.getByRole("banner").locator(".strip-target")).toContainText(
      "Data quality analyst",
    );
    expect(externalRequests(requests)).toEqual([]);
  });

  test("[WLD-05][UI-05] holding the world still stops the ambient motion; calm mode, in the account menu, draws the world still and is kept", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("roles"));
    await expect(light(page)).toHaveCSS("animation-play-state", "running");

    // Named apart from the interview's "Pause the interview" (the audit's F17).
    const pause = page.getByRole("button", { name: /^Hold the world still/ });
    await expect(page.getByRole("button", { name: /^Pause motion/ })).toHaveCount(0);
    await pause.click();
    await expect(pause).toHaveAttribute("aria-pressed", "true");
    await expect(light(page)).toHaveCSS("animation-play-state", "paused");
    await pause.click();
    await expect(pause).toHaveAttribute("aria-pressed", "false");
    await expect(light(page)).toHaveCSS("animation-play-state", "running");

    const sound = page.getByRole("button", { name: /^Sound/ });
    await expect(sound).toHaveAttribute("aria-pressed", "false");
    // A setting, not on the first screen: calm mode is in the account menu only.
    await expect(page.getByRole("banner").getByRole("button", { name: /^Calm mode/ })).toHaveCount(
      0,
    );

    await toggleCalm(page);
    await expect(light(page)).toHaveCSS("animation-play-state", "paused");
    await page.reload();
    await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
    await expect(light(page)).toHaveCSS("animation-play-state", "paused");
    await toggleCalm(page);
    await expect(light(page)).toHaveCSS("animation-play-state", "running");
  });

  test("[WLD-08][UI-05][PROF-09] the calm support panel stills the world, and holding it keeps the person's own choice", async ({
    page,
  }) => {
    const token = await emulatorToken("ada");
    const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
      "POST",
      "/v1/workspaces",
      token,
      { name: "Support, moving (synthetic)", data_mode: "demo", synthetic: true },
    );
    await signIn(page, "ada", chapterUrl("you", id));
    await skipFirstQuestion(page);
    await page.getByRole("button", { name: "Help me explore" }).click();
    await expect(light(page)).toHaveCSS("animation-play-state", "running");
    await page
      .getByRole("textbox", { name: "Reply to Careerwright" })
      .fill("Some days I just want to die.");
    await page.getByRole("button", { name: "Send" }).click();

    const panel = page.getByRole("region", { name: "Support is available" });
    await expect(panel).toBeVisible();
    await expect(light(page)).toHaveCSS("animation-play-state", "paused");
    await expect(world(page)).toHaveAttribute("data-distress", "true");
    await expect(
      page.getByRole("status").filter({ hasText: "Still while support is shown" }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /^Hold the world still/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    await panel.getByRole("button", { name: "Dismiss the support note" }).click();
    await expect(world(page)).toHaveAttribute("data-distress", "false");
    await expect(light(page)).toHaveCSS("animation-play-state", "running");
  });
});

test("[WLD-06][UI-06] the menus open above the atmosphere", async ({ page }) => {
  await signIn(page, "ada", chapterUrl("roles"));
  await expect(light(page)).toBeAttached();
  expect(await menuOnTop(page, { name: /^Workspace/ }), "the workspace menu").toBe(true);
  expect(await menuOnTop(page, { name: "Account and settings" }), "the account menu").toBe(true);
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("[WLD-05][UI-05] calm mode in the account menu keeps its words and its switch", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("you"));
    await page.getByRole("button", { name: "Account and settings" }).click();
    const calm = page.getByRole("button", { name: /^Calm mode/ });
    await expect(calm).toBeVisible();
    // The strip's own controls become glyph buttons on a phone; the menu's must not.
    const words = await calm.getByText("Calm mode", { exact: true }).boundingBox();
    expect(words?.width ?? 0, "calm mode's words are shown").toBeGreaterThan(40);
    await expect(calm.locator(".world-switch")).toBeVisible();
  });

  test("[WLD-06][UI-06] the mobile account menu receives input above the atmosphere and restores focus", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("roles"));
    expect(await menuOnTop(page, { name: "Account and settings" })).toBe(true);
  });

  test("[WLD-08][UI-05][PROF-09] the support status sits in the top bar and adds no row to the strip", async ({
    page,
  }) => {
    const token = await emulatorToken("ada");
    const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
      "POST",
      "/v1/workspaces",
      token,
      { name: "Support, phone (synthetic)", data_mode: "demo", synthetic: true },
    );
    await signIn(page, "ada", chapterUrl("you", id));
    const strip = page.getByRole("banner");
    // Measured once the strip has settled: its words loaded, updates live, the fonts in and
    // the same height two frames running (it measured 105 px, then 57, mid-load).
    const before = await settledHeight(page);
    await skipFirstQuestion(page);
    await page.getByRole("button", { name: "Help me explore" }).click();
    await page
      .getByRole("textbox", { name: "Reply to Careerwright" })
      .fill("Some days I just want to die.");
    await page.getByRole("button", { name: "Send" }).click();

    await expect(page.getByRole("region", { name: "Support is available" })).toBeVisible();
    await expect(
      page
        .locator(".topbar")
        .getByRole("status")
        .filter({ hasText: "Still while support is shown" }),
    ).toBeVisible();
    expect(await settledHeight(page), "the strip keeps its height").toBe(before);
    expect((await strip.boundingBox())?.height, "the strip keeps its height").toBe(before);
  });
});

/**
 * The strip's height once nothing is still arriving: the saved state and live updates in, the
 * fonts loaded, and the same height on two animation frames in a row.
 */
async function settledHeight(page: Page): Promise<number> {
  await expect(saved(page)).toHaveText(/^(Answers saved|Nothing saved yet)$/);
  await expect(liveUpdates(page, "Live")).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  return page.evaluate(
    () =>
      new Promise<number>((resolve) => {
        const strip = document.querySelector("header.strip");
        let last = -1;
        const check = () => {
          const height = strip?.getBoundingClientRect().height ?? 0;
          if (height === last) resolve(height);
          else {
            last = height;
            requestAnimationFrame(() => requestAnimationFrame(check));
          }
        };
        check();
      }),
  );
}

test("[WLD-02][UI-07][UI-05] an unanswered workspace keeps its starting facts unknown", async ({
  page,
}) => {
  const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    await emulatorToken("ada"),
    { name: "Nothing answered (synthetic)", data_mode: "demo", synthetic: true },
  );
  await signIn(page, "ada", chapterUrl("you", id));
  const startingPoint = page.getByRole("complementary", { name: "Your starting point" });
  await expect(startingPoint.getByRole("definition")).toHaveText([
    "Not asked yet",
    "Not asked yet",
    "Not asked yet",
  ]);
  await expect(saved(page)).toHaveText("Nothing saved yet");
  await page.goto(chapterUrl("roles", id));
  await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Your target roles" })).toHaveCount(0);
});

for (const viewport of VIEWPORTS.filter((v) => v.width < 968)) {
  test(`[WLD-07][UI-07][UI-12][UI-05] chapter tabs remain unobscured after every view change (${viewport.width}×${viewport.height})`, async ({
    browser,
  }) => {
    const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
    const page = await context.newPage();
    await signIn(page, "ada", chapterUrl("you"));
    for (const view of ["What we know", "Suggestions", "Conversation", "What we know"] as const) {
      const tab = page.getByRole("tab", { name: view });
      await tab.click();
      await expect(tab).toHaveAttribute("aria-selected", "true");
      expect(await page.evaluate(() => window.scrollY), `${view}: no scroll`).toBe(0);
      const reachable = await page.getByRole("tab").evaluateAll((tabs) =>
        tabs.map((tab) => {
          const box = tab.getBoundingClientRect();
          return tab.contains(
            document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2),
          );
        }),
      );
      expect(reachable, `${view}: every tab receives input`).toEqual([true, true, true]);
    }
    await context.close();
  });
}

/**
 * The strip's facts as the person reads them: each one's words, whether its label sits on one
 * line, and whether its value is cut (an ellipsis) or runs past the strip.
 */
function stripFacts(page: Page) {
  return page.getByRole("banner").evaluate((strip) => {
    const edge = strip.getBoundingClientRect().right;
    return [...strip.querySelectorAll<HTMLElement>(".strip-target, .strip-fact")].map((fact) => {
      const value = fact.querySelector("strong");
      const label = document.createRange();
      if (fact.firstChild !== null) label.selectNodeContents(fact.firstChild);
      const rows = new Set([...label.getClientRects()].map((rect) => Math.round(rect.top)));
      return {
        words: fact.innerText.replace(/\s+/g, " ").trim(),
        labelRows: rows.size,
        cut: value === null || value.scrollWidth > value.clientWidth + 1,
        past: fact.getBoundingClientRect().right > edge + 1,
      };
    });
  });
}

/** Every fact in sight, its label on one line and its words whole (D-I1). */
async function expectFactsWhole(page: Page, expected: RegExp[]) {
  await page.evaluate(() => document.fonts.ready);
  const facts = await stripFacts(page);
  expect(facts.map((fact) => fact.words)).toEqual(
    expected.map((pattern) => expect.stringMatching(pattern)),
  );
  for (const fact of facts) {
    expect(fact.labelRows, `${fact.words}: its label on one line`).toBe(1);
    expect(fact.cut, `${fact.words}: its value is shown whole`).toBe(false);
    expect(fact.past, `${fact.words}: inside the strip`).toBe(false);
  }
}

test("[WLD-05][UI-09][UI-05] below a desktop's width the strip keeps the person's facts, and the world's controls are in the account menu (F14)", async ({
  browser,
}) => {
  for (const viewport of [
    { width: 768, height: 1024 },
    { width: 390, height: 844 },
  ]) {
    // Motion allowed, so holding the world still is the person's own choice to make.
    const context = await browser.newContext({ viewport, reducedMotion: "no-preference" });
    const page = await context.newPage();
    await signIn(page, "ada", chapterUrl("you"));
    const strip = page.getByRole("banner");
    await expect(saved(page)).toHaveText("Answers saved");
    if (viewport.width > 760) {
      await expect(strip.getByText(/^Work area /)).toBeVisible();
      await expect(strip.getByText(/^Budget /)).toBeVisible();
      // Each fact has the room its words need, a money value never cut inside its digits
      // (design review I1: "Budget Up to £1,50…" with room to spare).
      await expectFactsWhole(page, [
        /^Target Data quality analyst$/,
        /^Work area \S.*$/,
        /^Budget Up to £[\d,]+, at most £[\d,]+ a month$/,
      ]);
      // Three long targets and a budget not confirmed: still whole, "Not confirmed" included.
      await page.goto(chapterUrl("you", await longTargetsWorkspace()));
      await expect(saved(page)).toHaveText("Answers saved");
      await expectFactsWhole(page, [
        new RegExp(`^Target ${LONG_TARGETS[0]}, .*${LONG_TARGETS[2]}$`),
        /^Work area Manchester$/,
        /^Budget Not confirmed$/,
      ]);
      await page.goto(chapterUrl("you"));
      await expect(saved(page)).toHaveText("Answers saved");
    }
    await expect(strip.getByRole("button", { name: /^Hold the world still/ })).toHaveCount(0);
    await expect(strip.getByRole("button", { name: /^Sound/ })).toHaveCount(0);

    await page.getByRole("button", { name: "Account and settings" }).click();
    const hold = page.getByRole("button", { name: /^Hold the world still/ });
    await expect(hold).toBeVisible();
    await expect(hold.locator(".world-switch")).toBeVisible(); // its switch, with its words
    await expect(page.getByRole("button", { name: /^Sound/ })).toBeVisible();
    await hold.click();
    await expect(hold).toHaveAttribute("aria-pressed", "true");
    await context.close();
  }
});

/** The chapter's words as read: the same in every way of drawing the world. */
const chapterText = (page: Page) => page.locator("main").innerText();

for (const viewport of VIEWPORTS) {
  test(`[WLD-03][UI-05][UI-07] the You chapter says the same in the moving and the still world, in every view (${viewport.width}×${viewport.height})`, async ({
    browser,
  }) => {
    test.setTimeout(300_000);
    // Fix round 1, concern 4: the fixture workspace, and one that isn't the fixture's, with a
    // reply to review, a slate and its written note.
    const talked = await talkedWorkspace(await emulatorToken("ada"));
    for (const workspace of [undefined, talked]) {
      const seen = new Map<Mode, string[]>();
      for (const mode of MODES) {
        const page = await modePage(browser, viewport, mode);
        await open(page, chapterUrl("you", workspace), "You", mode);
        const views: string[] = [];
        for (const view of ["Conversation", "What we know", "Suggestions"] as const) {
          await youView(page, view);
          await expect(page.getByRole("tab", { name: view })).toHaveAttribute(
            "aria-selected",
            "true",
          );
          await expect(page.getByText("Loading the early sketch")).toHaveCount(0);
          if (workspace === talked && view === "What we know") {
            // The role's ESCO list arrives independently of the chapter's loading state.
            await expect(
              page.getByRole("tabpanel", { name: view }).getByText(/^The \d+ skills that ESCO,/),
            ).toBeVisible();
          }
          if (workspace === talked && view === "Suggestions") {
            // The note is asked for when the slate first shows; its words settle first.
            await expect(
              page.getByText(/Written by the demo explainer \(synthetic\)/).first(),
            ).toHaveCount(1, { timeout: 60_000 });
          }
          views.push(await chapterText(page));
        }
        seen.set(mode, views);
        await page.context().close();
      }
      const moving = seen.get("moving");
      // The conversation's own heading: there whether or not the start's choice is made (the
      // reply field comes only once it is, Task W2F slice E).
      expect(moving?.[0]).toContain("Conversation with Careerwright");
      for (const mode of MODES) {
        expect(seen.get(mode), `${workspace ?? "fixture"}: ${mode} against moving`).toEqual(moving);
      }
    }
  });
}

test("[WLD-01][UI-09] Roles shows the chosen target alongside openings and examples", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("roles"));
  await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
  await expect(page.getByText(/Explore the work behind a role/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Openings and examples" })).toBeVisible();
  await expect(page.getByRole("banner").locator(".strip-target")).toContainText(
    "Data quality analyst",
  );
});

type Mode = "moving" | "reduced motion" | "calm" | "paused";
const MODES: readonly Mode[] = ["moving", "reduced motion", "calm", "paused"];

/** A signed-in page in one way of drawing the world. */
async function modePage(browser: Browser, viewport: (typeof VIEWPORTS)[number], mode: Mode) {
  const context = await browser.newContext({
    viewport,
    reducedMotion: mode === "reduced motion" ? "reduce" : "no-preference",
  });
  if (mode === "calm") {
    await context.addInitScript(() => window.localStorage.setItem("careerwright.calm", "true"));
  }
  const page = await context.newPage();
  await signIn(page, "ada", chapterUrl("you"));
  return page;
}

/** Wait for saved chapter facts before comparing motion settings. */
async function open(page: Page, url: string, chapter: string, mode: Mode) {
  await page.goto(url);
  await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
  await expect(page.locator("main .skeleton").filter({ visible: true })).toHaveCount(0);
  await expect(saved(page)).toHaveText("Answers saved");
  if (mode === "paused") await holdStill(page);
  if (mode === "reduced motion") await expect(light(page)).toHaveCSS("animation-name", "none");
  else
    await expect(light(page)).toHaveCSS(
      "animation-play-state",
      mode === "moving" ? "running" : "paused",
    );
}

for (const viewport of VIEWPORTS) {
  test(`[WLD-06][UI-07] chapter labels do not cover their values and facts stay inside the page (${viewport.width}×${viewport.height})`, async ({
    browser,
  }) => {
    for (const reducedMotion of ["reduce", "no-preference"] as const) {
      const context = await browser.newContext({ viewport, reducedMotion });
      const page = await context.newPage();
      await signIn(page, "ada", chapterUrl("you"));
      for (const chapter of CHAPTERS) {
        await page.goto(chapterUrl(chapter.toLowerCase()));
        await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
        await expect(page.locator("main .skeleton").filter({ visible: true })).toHaveCount(0);
        await page.evaluate(() => document.fonts.ready);
        expect(await overprintedLabels(page), `${chapter}: labels and values`).toEqual([]);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - window.innerWidth,
        );
        expect(overflow, `${chapter}: no horizontal scrolling`).toBeLessThanOrEqual(1);
      }
      await context.close();
    }
  });
}
