// The world in the app (plan section 4, Sprint W SW.3): one persistent world behind the
// chapters; changing chapter travels to its place; the still world shows the same names as the
// moving one, under reduced motion, calm mode and pause, at every size; the controls hold the
// world still and leave sound off until asked (in the strip on a desktop, in the account menu
// below one), and calm mode lives in the account menu; the calm support panel stills the world;
// Roles shows its own place; every light's name sits beside it, clear of the panels; nothing leaves this
// machine. On the real stack, demo mode.
import { type Browser, expect, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken, talkedWorkspace } from "./api";
import {
  chapterUrl,
  externalRequests,
  liveUpdates,
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

const world = (page: Page) => page.locator(".world");
const words = (page: Page) => page.getByRole("complementary", { name: "Your world" });

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

/** The names in sight in the world, and whether the key to the lights is in sight. */
function inSight(page: Page) {
  return page.evaluate(() => ({
    names: [
      ...document.querySelectorAll<HTMLElement>(
        ".world-label[data-shown='true'] .world-label-name",
      ),
    ]
      .map((e) => e.textContent ?? "")
      .sort(),
    key: document.querySelector<HTMLElement>(".world-key")?.dataset.placed === "true",
  }));
}

/**
 * Shown names whose label is taller than the name itself: a mark left on a line of its own
 * above a long, wrapped name (the label's padding is 2 px above and below).
 */
function marksOnTheirOwn(page: Page) {
  return page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>(".world-label[data-shown='true']")]
      .filter((label) => {
        const name = label.querySelector(".world-label-name");
        return (
          name !== null &&
          label.getBoundingClientRect().height > name.getBoundingClientRect().height + 6
        );
      })
      .map((label) => label.textContent ?? ""),
  );
}

/** The visible names in the world, with their boxes, and the panels over it. */
function layout(page: Page) {
  return page.evaluate(() => {
    const box = (e: Element) => {
      const r = e.getBoundingClientRect();
      return { x: r.left, y: r.top, w: r.width, h: r.height };
    };
    const labels = [
      ...document.querySelectorAll<HTMLElement>(".world-label[data-shown='true']"),
    ].map((e) => ({
      name: e.querySelector(".world-label-name")?.textContent ?? "",
      // A light the key explains (every light but the person's).
      keyed: e.dataset.keyed === "true",
      ...box(e),
    }));
    const panels = [...document.querySelectorAll("[data-covers-world]")]
      .map(box)
      .filter((b) => b.w > 0 && b.h > 0);
    const key = document.querySelector(".world-key[data-placed='true']");
    return {
      labels,
      key: key === null ? null : box(key),
      panels,
      vw: window.innerWidth,
      vh: window.innerHeight,
    };
  });
}

const overlap = (
  a: { x: number; y: number; w: number; h: number },
  b: { x: number; y: number; w: number; h: number },
) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

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

/**
 * Opens a menu, stands the key to the lights where the menu is and reports whether the menu is
 * what shows there: wherever the two meet, the menu is on top.
 */
async function menuOverKey(page: Page, opener: { name: string | RegExp }) {
  await page.getByRole("button", opener).click();
  await expect(page.locator(".popover")).toBeVisible();
  // Let the world re-place its names for the open menu first (once a frame).
  await page.waitForTimeout(200);
  const onTop = await page.evaluate(() => {
    const key = document.querySelector<HTMLElement>(".world-key");
    const menu = document.querySelector<HTMLElement>(".popover");
    if (key === null || menu === null) return null;
    const m = menu.getBoundingClientRect();
    key.dataset.placed = "true";
    key.style.right = `${window.innerWidth - m.right}px`;
    key.style.bottom = `${window.innerHeight - m.bottom}px`;
    const k = key.getBoundingClientRect();
    const x = (Math.max(k.left, m.left) + Math.min(k.right, m.right)) / 2;
    const y = (Math.max(k.top, m.top) + Math.min(k.bottom, m.bottom)) / 2;
    return menu.contains(document.elementFromPoint(x, y));
  });
  await page.keyboard.press("Escape");
  return onTop;
}

test.describe("moving", () => {
  test.use({ reducedMotion: "no-preference" });

  test("[WLD-01][UI-09][UI-05][BND1-11] one world stays behind every chapter while the view travels", async ({
    page,
  }) => {
    const requests = recordRequests(page);
    await signIn(page, "ada", chapterUrl("you"));
    await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
    // Mark the canvas itself: if any chapter made a new one (and a new WebGL context), the
    // mark would be gone.
    await page.getByTestId("moving-world").evaluate((element) => {
      (element as HTMLElement & { persisted?: boolean }).persisted = true;
    });

    const rail = page.getByRole("navigation", { name: "Chapters" });
    for (const chapter of CHAPTERS) {
      await rail.getByRole("link", { name: new RegExp(`^${chapter}`) }).click();
      await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
      await expect(world(page)).toHaveAttribute("data-place", chapter.toLowerCase());
      expect(
        await page
          .getByTestId("moving-world")
          .evaluate((element) => (element as HTMLElement & { persisted?: boolean }).persisted),
      ).toBe(true);
    }
    // P01's own target stands on the horizon, named in the page.
    await expect(words(page).getByText("Data quality analyst")).toBeAttached();
    expect(externalRequests(requests)).toEqual([]);
  });

  test("[WLD-05][UI-05] holding the world still stops the ambient motion; calm mode, in the account menu, draws the world still and is kept", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("roles"));
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
    await expect(world(page)).toHaveAttribute("data-motion", "running");

    // Named apart from the interview's "Pause the interview" (the audit's F17).
    const pause = page.getByRole("button", { name: /^Hold the world still/ });
    await expect(page.getByRole("button", { name: /^Pause motion/ })).toHaveCount(0);
    await pause.click();
    await expect(pause).toHaveAttribute("aria-pressed", "true");
    await expect(world(page)).toHaveAttribute("data-motion", "still");
    await pause.click();
    await expect(pause).toHaveAttribute("aria-pressed", "false");
    await expect(world(page)).toHaveAttribute("data-motion", "running");

    const sound = page.getByRole("button", { name: /^Sound/ });
    await expect(sound).toHaveAttribute("aria-pressed", "false");
    // A setting, not on the first screen: calm mode is in the account menu only.
    await expect(page.getByRole("banner").getByRole("button", { name: /^Calm mode/ })).toHaveCount(
      0,
    );

    await toggleCalm(page);
    await expect(world(page)).toHaveAttribute("data-world-mode", "still");
    await expect(page.getByTestId("still-world")).toBeVisible();
    await page.reload();
    await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
    await expect(world(page)).toHaveAttribute("data-world-mode", "still");
    await toggleCalm(page);
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
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
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
    await page
      .getByRole("textbox", { name: "Reply to Careerwright" })
      .fill("Some days I just want to die.");
    await page.getByRole("button", { name: "Send" }).click();

    const panel = page.getByRole("region", { name: "Support is available" });
    await expect(panel).toBeVisible();
    await expect(world(page)).toHaveAttribute("data-world-mode", "still");
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
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
  });
});

test("[WLD-06][UI-06] the menus open over the key to the lights", async ({ page }) => {
  await signIn(page, "ada", chapterUrl("roles"));
  await expect(page.locator(".world-key")).toHaveAttribute("data-placed", "true");
  expect(await menuOverKey(page, { name: /^Workspace/ }), "the workspace menu").toBe(true);
  expect(await menuOverKey(page, { name: "Account and settings" }), "the account menu").toBe(true);
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

  test("[WLD-06][UI-06] the chapter menu opens over the key to the lights", async ({ page }) => {
    await signIn(page, "ada", chapterUrl("roles"));
    expect(await menuOverKey(page, { name: /open chapter menu/ })).toBe(true);
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

test("[WLD-02][UI-07][UI-05] with no light the key explains, the key is not shown", async ({
  page,
}) => {
  // W2A re-review 2, Minor 3: the empty-key case. A new workspace has no destination, skill or
  // opening: the person's light is named, and nothing it draws needs a key.
  const token = await emulatorToken("ada");
  const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    token,
    { name: "Nothing to explain (synthetic)", data_mode: "demo", synthetic: true },
  );
  await signIn(page, "ada", chapterUrl("you", id));
  for (const chapter of ["you", "roles"]) {
    await page.goto(chapterUrl(chapter, id));
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await page.waitForTimeout(900); // travel, then the names settle
    const { labels, key } = await layout(page);
    expect(
      labels.map((label) => label.name),
      chapter,
    ).toEqual(["You"]);
    expect(
      labels.some((label) => label.keyed),
      chapter,
    ).toBe(false);
    expect(key, `${chapter}: the key`).toBeNull();
    await expect(page.locator(".world-key")).toHaveCount(0);
  }
});

/**
 * The person's light's name, the key to the lights (when placed), the You console and its three
 * tabs, as they stand now, and whether each tab is what a tap at its centre reaches.
 */
function youBoxes(page: Page) {
  return page.evaluate(() => {
    const box = (e: Element | null) => {
      if (e === null) return null;
      const r = e.getBoundingClientRect();
      return { x: r.left, y: r.top, w: r.width, h: r.height };
    };
    const tabs = [...document.querySelectorAll<HTMLElement>("[role='tab']")];
    return {
      you: box(document.querySelector(".world-label[data-label='origin'][data-shown='true']")),
      key: box(document.querySelector(".world-key[data-placed='true']")),
      console: box(document.querySelector("[data-world-panel]")),
      tabs: tabs.map(box),
      onTop: tabs.map((tab) => {
        const r = tab.getBoundingClientRect();
        const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return hit !== null && tab.contains(hit);
      }),
    };
  });
}

for (const viewport of VIEWPORTS.filter((v) => v.width < 968)) {
  test(`[WLD-07][UI-07][UI-12][UI-05] after every change of view the person's light stands above the console, and the key covers neither it nor a tab (${viewport.width}×${viewport.height})`, async ({
    browser,
  }) => {
    // Re-review N1 (the audit's F8): the views switch by `hidden`, so the world must place
    // itself again with no scroll and no child added. Each box is read where it stands now,
    // after the change, never a value left by the view before.
    const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
    const page = await context.newPage();
    await signIn(page, "ada", chapterUrl("you"));
    await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
    for (const view of ["What we know", "Suggestions", "Conversation", "What we know"] as const) {
      const tab = page.getByRole("tab", { name: view });
      await tab.click(); // the tabs are in view at the top: the page does not scroll
      await expect(tab).toHaveAttribute("aria-selected", "true");
      expect(await page.evaluate(() => window.scrollY), `${view}: no scroll`).toBe(0);
      await page.waitForTimeout(300); // a frame or two: the world places itself again
      const { you, key, console: panel, tabs, onTop } = await youBoxes(page);
      expect(panel, view).not.toBeNull();
      expect(you, `${view}: the person's light is named, in view`).not.toBeNull();
      if (you === null || panel === null) continue;
      expect(you.y + you.h, `${view}: "You" above the console`).toBeLessThanOrEqual(panel.y);
      if (key !== null) {
        expect(overlap(key, panel), `${view}: the key over the console`).toBe(false);
        for (const [i, shown] of tabs.entries()) {
          if (shown !== null)
            expect(overlap(key, shown), `${view}: the key over tab ${i}`).toBe(false);
        }
      }
      // An "on top" check: a tap at each tab's centre reaches the tab, nothing over it (F8).
      expect(onTop, `${view}: each tab on top`).toEqual([true, true, true]);
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

test("[WLD-01][UI-09] Roles shows the chosen target and stays in its world place", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("roles"));
  await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
  await expect(page.getByText(/Explore the work behind a role/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Openings and examples" })).toBeVisible();
  await expect(world(page)).toHaveAttribute("data-place", "roles");
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

/**
 * Opens a chapter in a mode, waits until it has loaded (its heading shows while it still loads,
 * and the panel's size, which decides where names fit, changes when it has), then lets travel
 * finish (600 ms) and the names settle. With `targets`, it also waits until the world names
 * each of them (shown in sight or not): the world has the person's targets.
 */
async function open(
  page: Page,
  url: string,
  chapter: string,
  mode: Mode,
  targets: readonly string[] = [],
) {
  await page.goto(url);
  await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
  await expect(page.locator("main .skeleton").filter({ visible: true })).toHaveCount(0);
  for (const name of targets) {
    await expect(words(page).getByText(name, { exact: true })).toBeAttached();
  }
  await expect(world(page)).toHaveAttribute(
    "data-world-mode",
    mode === "moving" || mode === "paused" ? "moving" : "still",
  );
  if (mode === "paused") {
    await holdStill(page);
    await expect(world(page)).toHaveAttribute("data-motion", "still");
  }
  await page.waitForTimeout(900);
}

for (const viewport of VIEWPORTS) {
  test(`[WLD-03][UI-05][UI-07] the still world shows the same names as the moving one, in every chapter (${viewport.width}×${viewport.height}, three long targets)`, async ({
    browser,
  }) => {
    test.setTimeout(240_000);
    const workspace = await longTargetsWorkspace();
    const pages = new Map<Mode, Page>();
    for (const mode of MODES) pages.set(mode, await modePage(browser, viewport, mode));
    for (const chapter of CHAPTERS) {
      const url = chapterUrl(chapter.toLowerCase(), workspace);
      const seen = new Map<Mode, Awaited<ReturnType<typeof inSight>>>();
      for (const mode of MODES) {
        const page = pages.get(mode) as Page;
        await open(page, url, chapter, mode, LONG_TARGETS);
        seen.set(mode, await inSight(page));
      }
      const moving = seen.get("moving");
      for (const mode of MODES) {
        expect(seen.get(mode), `${chapter}, ${mode} against moving`).toEqual(moving);
      }
      // The larger Roles panel can cover decorative labels; their names remain in the world.
      if (chapter === "Roles") {
        const movingPage = pages.get("moving") as Page;
        await expect(words(movingPage).getByText("You", { exact: true })).toBeAttached();
        expect(await marksOnTheirOwn(movingPage), "Roles: marks").toEqual([]);
      }
    }
    for (const page of pages.values()) await page.context().close();
  });

  test(`[WLD-06][UI-07] every name in the world sits clear of the panels and of each other (${viewport.width}×${viewport.height})`, async ({
    browser,
  }) => {
    for (const reducedMotion of ["reduce", "no-preference"] as const) {
      const context = await browser.newContext({ viewport, reducedMotion });
      const page = await context.newPage();
      await signIn(page, "ada", chapterUrl("you"));
      for (const chapter of CHAPTERS) {
        await page.goto(chapterUrl(chapter.toLowerCase()));
        await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
        // Let travel finish (600 ms) and the names settle.
        await page.waitForTimeout(900);
        const { labels, key, panels, vw, vh } = await layout(page);
        for (const [i, label] of labels.entries()) {
          const where = `${chapter}, ${reducedMotion}: "${label.name}"`;
          expect(label.x, where).toBeGreaterThanOrEqual(0);
          expect(label.y, where).toBeGreaterThanOrEqual(0);
          expect(label.x + label.w, where).toBeLessThanOrEqual(vw);
          expect(label.y + label.h, where).toBeLessThanOrEqual(vh);
          for (const panel of panels) expect(overlap(label, panel), where).toBe(false);
          if (key !== null) expect(overlap(label, key), `${where} and the key`).toBe(false);
          for (const other of labels.slice(i + 1)) expect(overlap(label, other), where).toBe(false);
        }
        // A light the key explains is named in view: the key to the lights is shown too. The
        // person's own light needs no key (W2A re-review 2, Minor 3: "You" alone is no reason).
        if (labels.some((label) => label.keyed)) {
          expect(key, `${chapter}, ${reducedMotion}: lights in view, but no key`).not.toBeNull();
        }
        // The key to the lights, when shown, is not under a panel either.
        if (key !== null) {
          for (const panel of panels) {
            expect(overlap(key, panel), `${chapter}, ${reducedMotion}: the key`).toBe(false);
          }
        }
        if (chapter === "Roles")
          await expect(
            words(page).getByText("Data quality analyst", { exact: true }),
          ).toBeAttached();
      }
      await context.close();
    }
  });
}
