// The world in the app (plan section 4, Sprint W SW.3): one persistent world behind all six
// chapters; changing chapter travels to its place; the still world shows the same names as the
// moving one, under reduced motion, calm mode and pause, at every size; the visible controls
// pause motion and leave sound off until asked, and calm mode lives in the account menu; the
// calm support panel stills the world; a chapter not built yet says so in its place, above a
// short card; every light's name sits beside it, clear of the panels; and nothing leaves this
// machine. On the real stack, demo mode.
import { type Browser, expect, type Page, test } from "@playwright/test";
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

const CHAPTERS = ["You", "Roles", "Skills", "Options", "Routes", "Plan"] as const;
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

  test("[UI-09][UI-05][BND1-11] one world stays behind every chapter while the view travels", async ({
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

  test("[UI-05] pause stills the ambient motion; calm mode, in the account menu, draws the world still and is kept", async ({
    page,
  }) => {
    await signIn(page, "ada", chapterUrl("roles"));
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
    await expect(world(page)).toHaveAttribute("data-motion", "running");

    const pause = page.getByRole("button", { name: /^Pause motion/ });
    await pause.click();
    await expect(pause).toHaveAttribute("aria-pressed", "true");
    await expect(world(page)).toHaveAttribute("data-motion", "still");
    await pause.click();
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

  test("[UI-05][PROF-09] the calm support panel stills the world, and Pause keeps the person's own choice", async ({
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
    await expect(page.getByRole("button", { name: /^Pause motion/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    await panel.getByRole("button", { name: "Dismiss the support note" }).click();
    await expect(world(page)).toHaveAttribute("data-distress", "false");
    await expect(world(page)).toHaveAttribute("data-world-mode", "moving");
  });
});

test("[UI-06] the menus open over the key to the lights", async ({ page }) => {
  await signIn(page, "ada", chapterUrl("roles"));
  await expect(page.locator(".world-key")).toHaveAttribute("data-placed", "true");
  expect(await menuOverKey(page, { name: /^Workspace/ }), "the workspace menu").toBe(true);
  expect(await menuOverKey(page, { name: "Account and settings" }), "the account menu").toBe(true);
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("[UI-05] calm mode in the account menu keeps its words and its switch", async ({ page }) => {
    await signIn(page, "ada", chapterUrl("you"));
    await page.getByRole("button", { name: "Account and settings" }).click();
    const calm = page.getByRole("button", { name: /^Calm mode/ });
    await expect(calm).toBeVisible();
    // The strip's own controls become glyph buttons on a phone; the menu's must not.
    const words = await calm.getByText("Calm mode", { exact: true }).boundingBox();
    expect(words?.width ?? 0, "calm mode's words are shown").toBeGreaterThan(40);
    await expect(calm.locator(".world-switch")).toBeVisible();
  });

  test("[UI-06] the chapter menu opens over the key to the lights", async ({ page }) => {
    await signIn(page, "ada", chapterUrl("roles"));
    expect(await menuOverKey(page, { name: /open chapter menu/ })).toBe(true);
  });

  test("[UI-05][PROF-09] the support status sits in the top bar and adds no row to the strip", async ({
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

test("[UI-07][UI-05] with no light the key explains, the key is not shown", async ({ page }) => {
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

/** The chapter's words as read: the same in every way of drawing the world. */
const chapterText = (page: Page) => page.locator("main").innerText();

for (const viewport of VIEWPORTS) {
  test(`[UI-05][UI-07] the You chapter says the same in the moving and the still world, in every view (${viewport.width}×${viewport.height})`, async ({
    browser,
  }) => {
    test.setTimeout(180_000);
    const seen = new Map<Mode, string[]>();
    for (const mode of MODES) {
      const page = await modePage(browser, viewport, mode);
      await open(page, chapterUrl("you"), "You", mode);
      const views: string[] = [];
      for (const view of ["Conversation", "What we know", "Suggestions"] as const) {
        await youView(page, view);
        await expect(page.getByRole("tab", { name: view })).toHaveAttribute(
          "aria-selected",
          "true",
        );
        await expect(page.getByText("Loading the early sketch")).toHaveCount(0);
        views.push(await chapterText(page));
      }
      seen.set(mode, views);
      await page.context().close();
    }
    const moving = seen.get("moving");
    expect(moving?.[0]).toContain("Reply to Careerwright");
    for (const mode of MODES) expect(seen.get(mode), `${mode} against moving`).toEqual(moving);
  });
}

test("[UI-09] a chapter not built yet shows its place, and says so", async ({ page }) => {
  await signIn(page, "ada", chapterUrl("skills"));
  await expect(page.getByRole("heading", { level: 1, name: "Skills" })).toBeVisible();
  await expect(page.getByText("Not built yet")).toBeVisible();
  await expect(page.getByText("The ground between you and a destination.")).toBeVisible();
  await expect(world(page)).toHaveAttribute("data-place", "skills");
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

/** Opens a chapter in a mode, lets travel finish (600 ms) and the names settle. */
async function open(page: Page, url: string, chapter: string, mode: Mode) {
  await page.goto(url);
  await expect(page.getByRole("heading", { level: 1, name: chapter })).toBeVisible();
  await expect(world(page)).toHaveAttribute(
    "data-world-mode",
    mode === "moving" || mode === "paused" ? "moving" : "still",
  );
  if (mode === "paused") {
    await page.getByRole("button", { name: /^Pause motion/ }).click();
    await expect(world(page)).toHaveAttribute("data-motion", "still");
  }
  await page.waitForTimeout(900);
}

for (const viewport of VIEWPORTS) {
  test(`[UI-05][UI-07] the still world shows the same names as the moving one, in every chapter (${viewport.width}×${viewport.height}, three long targets)`, async ({
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
        await open(page, url, chapter, mode);
        seen.set(mode, await inSight(page));
      }
      const moving = seen.get("moving");
      for (const mode of MODES) {
        expect(seen.get(mode), `${chapter}, ${mode} against moving`).toEqual(moving);
      }
      // At Roles the person and a destination are named at every size, in every mode, and a
      // long name's mark stays on its first line.
      if (chapter === "Roles") {
        expect(moving?.names, "Roles: the person is named").toContain("You");
        expect(
          moving?.names.some((name) => LONG_TARGETS.includes(name)),
          "Roles: a destination is named",
        ).toBe(true);
        expect(await marksOnTheirOwn(pages.get("moving") as Page), "Roles: marks").toEqual([]);
      }
    }
    for (const page of pages.values()) await page.context().close();
  });

  test(`[UI-07] every name in the world sits clear of the panels and of each other (${viewport.width}×${viewport.height})`, async ({
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
        // At Roles, P01's place stands clear of the card: the person and the target are named.
        if (chapter === "Roles") {
          const names = labels.map((label) => label.name);
          expect(names, `Roles, ${reducedMotion}`).toContain("You");
          expect(names, `Roles, ${reducedMotion}`).toContain("Data quality analyst");
        }
      }
      await context.close();
    }
  });
}
