// The visual review package (plan section 5, UI-11): every chapter and the shell's default,
// selected, empty, stale, unavailable and failed states, and Sprint 2's conversation states
// (the start, a reply to review, the slate, the support panel, a failed reply, key
// consent, Unknown/Skipped/Prefer not to say, the scrolled stale conflict and its Save, and
// expanded phone sheets), at 1440×900, 390×844 and 768×1024, each with the automatable
// checks: axe (WCAG 2.0, 2.1 and 2.2 A/AA), horizontal overflow, a label overprinting its
// value, console errors and font loading. These checks are evidence for a human review, not
// the review itself (ruling R2).
//
// `pnpm run review-screenshots` writes the PNGs and checks-<viewport>.json to
// docs/reviews/sprint-2/screenshots/; otherwise (make acceptance) they go to the test output
// and only the checks gate.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken, saveElsewhere } from "./api";
import { type AxeViolation, axe, chapterUrl, liveUpdates, signIn } from "./helpers";
import { FIXTURE_WORKSPACE, stack } from "./stack";

const VIEWPORTS = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "390x844", width: 390, height: 844 },
] as const;

type Shot = {
  name: string;
  /** Who signs in (none: the signed-out page). */
  as: "ada" | "ben" | "uninvited" | null;
  /**
   * Shots that change what the page receives (a blocked stream, a failing request) get a
   * browser context of their own; the others share one per identity.
   */
  context?: string;
  url: string;
  /** Runs once, before the context signs in: request interception for that context. */
  prepare?: (page: Page) => Promise<unknown>;
  ready: (page: Page) => Promise<void>;
  /**
   * Expected refusals (403, 404, a stale save's 409) and blocked requests log a failed load;
   * those lines are not defects.
   */
  refused?: boolean;
};

const heading = (name: string) => async (page: Page) => {
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
  await expect(page.getByRole("banner").getByText(/^Saved, version \d+$/)).toBeVisible();
  await expect(liveUpdates(page, "Live")).toBeVisible();
};

let staleSaves = 0;

/**
 * A save refused as stale: an answer typed here while another tab saves a newer version.
 * Returns the notice and the field's inline note with the newer value.
 */
async function staleSave(page: Page, workspace: string) {
  await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
  await expect(liveUpdates(page, "Live")).toBeVisible();
  await page.getByRole("button", { name: "Edit answers directly" }).click();
  await page.getByLabel("How you answer current role").selectOption("provided");
  await page.getByRole("textbox", { name: "Current role", exact: true }).fill("Typed on this page");
  // A new value each time, so every call makes a newer version (the same answer would not).
  staleSaves += 1;
  const elsewhere = `Saved in another tab (${staleSaves})`;
  const made = await saveElsewhere(workspace, "ada", "current_role", elsewhere);
  await page.getByRole("button", { name: "Save changes" }).click();
  const notice = page.getByText(`Version ${made} was saved while you were editing`);
  await expect(notice).toBeVisible();
  const inline = page.getByText(`Version ${made} has ${elsewhere} here.`);
  await expect(inline).toBeVisible();
  return { notice, inline };
}

/** Answers, a reply to review and a completed discovery, through the API (demo mode). */
async function talkedWorkspace(token: string): Promise<string> {
  const { workspace_id: id } = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    token,
    { name: "Conversation (synthetic)", data_mode: "demo", synthetic: true },
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
  profile.enjoyed_tasks = { state: "provided", value: ["fixing bikes", "working outdoors"] };
  profile.cities = { state: "provided", value: ["Leeds"] };
  await asBrowser("PUT", `${base}/profile`, token, { expected_version: 0, profile });
  await asBrowser("PUT", `${base}/interview/preferences`, token, {
    expected_version: 0,
    entry_mode: "unsure",
    conversation_mode: null,
    paused: false,
  });
  const turn = await asBrowser<{ turn_id: string }>("POST", `${base}/interview/turns`, token, {
    expected_profile_version: 1,
    message: "Synthetic: I could do 5 hours a week, and spend up to £600.",
  });
  const found = await asBrowser<{ discovery_id: string }>("POST", `${base}/discoveries`, token, {
    expected_profile_version: 1,
  });
  for (const path of [
    `${base}/interview/turns/${turn.turn_id}`,
    `${base}/discoveries/${found.discovery_id}`,
  ]) {
    await expect
      .poll(
        async () => (await asBrowser<{ run: { status: string } }>("GET", path, token)).run.status,
        {
          timeout: 60_000,
        },
      )
      .toBe("complete");
  }
  return id;
}

/** Opens the phone and tablet sheet to its full height; on a wide screen it is a column. */
async function expandSheet(page: Page) {
  const more = page.getByRole("dialog", { name: "Where this came from" }).getByRole("button", {
    name: "More",
  });
  if (await more.isVisible()) {
    await more.click();
    await expect(page.getByRole("button", { name: "Less" })).toBeVisible();
  }
}

const FAILED_TURN = {
  turn_id: "00000000-0000-4000-8000-0000000000f1",
  message_id: "00000000-0000-4000-8000-0000000000f2",
  message: "Synthetic: I could work in Leeds and give 6 hours a week.",
  profile_version: 1,
  created_at: "2027-01-01T10:00:00Z",
  run: {
    run_id: "00000000-0000-4000-8000-0000000000f1",
    kind: "interview_turn",
    status: "failed",
    failure_class: "invalid_model_output",
    data_mode: "demo",
    synthetic: true,
    model_id: "nessa-fixture-interviewer-1",
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

/** The API's support panel (`nessa.profile.safety.SUPPORT_NOTE` and its resources). */
const SUPPORT_NOTE = {
  policy_version: "support-policy-4",
  review_status: "provisional: needs reviewed sign-off (human gate H-12)",
  message:
    "If anything you mentioned is about how you are feeling, support is available any time, " +
    "from people trained to help. Your message was sent to Nessa as usual.",
  resources: [
    {
      name: "Emergency services",
      contact: "Call 999 or go to A&E",
      when: "If your life is at risk now, or you can't keep yourself safe",
      source_url:
        "https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/",
      checked_on: "2026-10-28",
    },
    {
      name: "NHS 111",
      contact: "Call 111 and choose the mental health option, or use 111 online",
      when: "For urgent mental health help and advice",
      source_url:
        "https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/",
      checked_on: "2026-10-28",
    },
    {
      name: "Samaritans",
      contact: "Call 116 123 (free, any time, day or night)",
      when: "To talk to someone who will listen",
      source_url: "https://www.samaritans.org/how-we-can-help/contact-samaritan/",
      checked_on: "2026-10-28",
    },
    {
      name: "Shout",
      contact: "Text SHOUT to 85258 (free, 24/7)",
      when: "If you would rather text than talk",
      source_url: "https://giveusashout.org/get-help/",
      checked_on: "2026-10-28",
    },
  ],
};

/** Workspaces the Sprint 2 shots start from, prepared through the API as a person would. */
type Scratch = {
  /** New and empty: nothing saved, nothing chosen. */
  empty: string;
  /** Answers saved, a reply to review and a completed discovery (demo interviewer). */
  talked: string;
  /** Live-assisted and synthetic, no key stored: the consent form. */
  live: string;
};

/** `scratch` workspaces are new synthetic workspaces of Ada's (see `Scratch`). */
const shots = (scratch: Scratch): Shot[] => [
  {
    name: "sign-in",
    as: null,
    url: "/sign-in",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "Sign in to Nessa" })).toBeVisible();
    },
  },
  {
    name: "you",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await heading("You")(page);
      await expect(
        page.getByRole("heading", { name: "How would you like to start?" }),
      ).toBeVisible();
      await expect(page.getByText("Loading the early sketch")).toHaveCount(0); // B-M5
    },
  },
  {
    name: "you--source-drawer",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await heading("You")(page);
      await page.getByRole("button", { name: "Edit answers directly" }).click();
      await page.getByRole("button", { name: "Source for total spending limit" }).click();
      await expect(page.getByText("Synthetic fixture", { exact: true })).toBeVisible();
    },
  },
  {
    name: "you--source-drawer-expanded",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await heading("You")(page);
      await page.getByRole("button", { name: "Edit answers directly" }).click();
      await page.getByRole("button", { name: "Source for total spending limit" }).click();
      await expect(page.getByText("Synthetic fixture", { exact: true })).toBeVisible();
      await expandSheet(page);
    },
  },
  {
    name: "you--answer-states",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await heading("You")(page);
      await page.getByRole("button", { name: "Edit answers directly" }).click();
      // Three neighbouring answers, so all three states are in view at every size (B-M5).
      await page.getByLabel("How you answer total spending limit").selectOption("unknown");
      await page.getByLabel("How you answer monthly payment limit").selectOption("skipped");
      await page
        .getByLabel("How you answer lowest pay you'd accept")
        .selectOption("prefer_not_to_say");
      await page
        .getByLabel("How you answer monthly payment limit")
        .evaluate((element) => element.scrollIntoView({ block: "center" }));
    },
  },
  {
    name: "you--salary-floor",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await heading("You")(page);
      await page.getByRole("button", { name: "Edit answers directly" }).click();
      await page.getByLabel("How you answer lowest pay you'd accept").selectOption("provided");
      await page.getByLabel("Lowest pay you'd accept, in pounds").fill("2,100");
      await page.getByLabel("Lowest pay you'd accept, per").selectOption("month");
      await page
        .getByLabel("Lowest pay you'd accept, in pounds")
        .evaluate((element) => element.scrollIntoView({ block: "center" }));
    },
  },
  {
    name: "you--reply-to-review",
    as: "ada",
    url: chapterUrl("you", scratch.talked),
    ready: async (page) => {
      await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
      await expect(page.getByText(/^Demo interviewer \(synthetic\):/)).toBeVisible();
      await expect(page.getByRole("region", { name: /To review:/ })).toBeVisible();
    },
  },
  {
    name: "you--slate",
    as: "ada",
    url: chapterUrl("you", scratch.talked),
    ready: async (page) => {
      const directions = page.getByRole("region", { name: "Directions to explore" });
      await expect(directions.getByRole("article").first()).toBeVisible();
      await directions.getByRole("article").first().scrollIntoViewIfNeeded();
    },
  },
  {
    // A message with a risk stem is sent as usual, with the support panel beside it. The
    // send is answered here so the scratch conversation is left as it was.
    name: "you--support-note",
    as: "ada",
    context: "support-note",
    url: chapterUrl("you", scratch.talked),
    prepare: async (page) => {
      await page.route("**/interview/turns", (route) =>
        route.request().method() === "POST"
          ? route.fulfill({ status: 202, json: { ...FAILED_TURN, support_note: SUPPORT_NOTE } })
          : route.continue(),
      );
    },
    ready: async (page) => {
      await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
      await page
        .getByRole("textbox", { name: "Reply to Nessa" })
        .fill("I volunteer on a suicide prevention helpline and want paid work like it.");
      await page.getByRole("button", { name: "Send" }).click();
      const note = page.getByRole("region", { name: "Support is available" });
      await expect(note).toBeVisible();
      await note.scrollIntoViewIfNeeded();
    },
  },
  {
    name: "you--reply-failed",
    as: "ada",
    context: "turn-failed",
    url: chapterUrl("you", scratch.talked),
    prepare: async (page) => {
      await page.route("**/interview/turns?*", (route) =>
        route.fulfill({ json: { items: [FAILED_TURN], next_cursor: null } }),
      );
      await page.route("**/interview/turns/*/reply", (route) =>
        route.fulfill({
          json: {
            turn_id: FAILED_TURN.turn_id,
            completeness: "incomplete",
            seq: 1,
            text: null,
            updated_at: null,
          },
        }),
      );
    },
    ready: async (page) => {
      await expect(page.getByText("The reply didn't pass Nessa's checks twice")).toBeVisible();
      await page.getByRole("button", { name: "Try again" }).scrollIntoViewIfNeeded();
    },
  },
  {
    name: "you--key-consent",
    as: "ada",
    url: chapterUrl("you", scratch.live),
    ready: async (page) => {
      await expect(
        page.getByRole("heading", { name: "Connect your Meta API key to talk with Nessa" }),
      ).toBeVisible();
    },
  },
  { name: "roles", as: "ada", url: chapterUrl("roles"), ready: heading("Roles") },
  { name: "skills", as: "ada", url: chapterUrl("skills"), ready: heading("Skills") },
  { name: "options", as: "ada", url: chapterUrl("options"), ready: heading("Options") },
  { name: "routes", as: "ada", url: chapterUrl("routes"), ready: heading("Routes") },
  {
    name: "routes--route-b",
    as: "ada",
    url: chapterUrl("routes"),
    ready: async (page) => {
      await heading("Routes")(page);
      await page.getByRole("button", { name: /^Route B/ }).click();
      await expect(page.getByText("Synthetic fixture route")).toBeVisible();
    },
  },
  {
    name: "routes--route-b-expanded",
    as: "ada",
    url: chapterUrl("routes"),
    ready: async (page) => {
      await heading("Routes")(page);
      await page.getByRole("button", { name: /^Route B/ }).click();
      await expect(page.getByText("Synthetic fixture route")).toBeVisible();
      await expandSheet(page);
    },
  },
  { name: "plan", as: "ada", url: chapterUrl("plan"), ready: heading("Plan") },
  {
    name: "routes--empty",
    as: "ada",
    url: chapterUrl("routes", scratch.empty),
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "No routes yet" })).toBeVisible();
      await expect(page.getByRole("banner").getByText("Nothing saved yet")).toBeVisible();
      await expect(liveUpdates(page, "Live")).toBeVisible();
    },
  },
  {
    name: "you--stale",
    as: "ada",
    url: chapterUrl("you", scratch.empty),
    refused: true,
    ready: async (page) => {
      const { notice } = await staleSave(page, scratch.empty);
      // Saving scrolled to the button; the capture shows the notice and the first answers.
      await notice.scrollIntoViewIfNeeded();
    },
  },
  {
    name: "you--stale-conflict",
    as: "ada",
    url: chapterUrl("you", scratch.empty),
    refused: true,
    ready: async (page) => {
      const { inline } = await staleSave(page, scratch.empty);
      await inline.scrollIntoViewIfNeeded(); // the field, with the newer version's value beside it
    },
  },
  {
    name: "you--stale-save",
    as: "ada",
    url: chapterUrl("you", scratch.empty),
    refused: true,
    ready: async (page) => {
      await staleSave(page, scratch.empty);
      await page.getByRole("button", { name: "Save changes" }).scrollIntoViewIfNeeded();
    },
  },
  {
    name: "you--unavailable",
    as: "ada",
    context: "stream-blocked",
    url: chapterUrl("you"),
    prepare: (page) => page.route("**/events/stream*", (route) => route.abort()),
    refused: true,
    ready: async (page) => {
      await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
      await expect(liveUpdates(page, "Reconnecting")).toBeVisible();
    },
  },
  {
    name: "you--failed",
    as: "ada",
    context: "profile-blocked",
    url: chapterUrl("you"),
    prepare: (page) =>
      page.route(`**/api/v1/workspaces/${FIXTURE_WORKSPACE}/profile`, (route) => route.abort()),
    refused: true,
    ready: async (page) => {
      await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
      await expect(
        page.getByRole("alert").getByText("Nessa's service isn't reachable"),
      ).toBeVisible();
      await expect(page.getByRole("button", { name: "Try again" })).toBeVisible(); // V-02
      await expect(
        page.getByRole("banner").getByText("Your answers couldn't be loaded"),
      ).toBeVisible();
    },
  },
  {
    name: "home--empty",
    as: "ben",
    url: "/",
    ready: async (page) => {
      await expect(page.getByText("No workspaces yet")).toBeVisible();
    },
  },
  {
    name: "not-found",
    as: "ben",
    url: chapterUrl("you"),
    refused: true,
    ready: async (page) => {
      await expect(
        page.getByRole("heading", { name: "This workspace can't be shown" }),
      ).toBeVisible();
      await expect(page.getByText("Not found")).toBeVisible();
    },
  },
  {
    name: "not-invited",
    as: "uninvited",
    url: "/",
    refused: true,
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "This account isn't invited" })).toBeVisible();
    },
  },
];

type Result = {
  file: string;
  fonts: boolean;
  overflow: number;
  /** Description-list labels whose text overprints their value's text. */
  overprinted: string[];
  axe: AxeViolation[];
  errors: string[];
};

const target = process.env.NESSA_REVIEW_DIR;

/** Each `dt` whose painted text meets the painted text of the `dd` after it. */
function overprintedLabels(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const textBoxes = (element: Element) => {
      const range = document.createRange();
      range.selectNodeContents(element);
      return Array.from(range.getClientRects()).filter((box) => box.width > 0);
    };
    const meet = (a: DOMRect, b: DOMRect) =>
      Math.min(a.right, b.right) - Math.max(a.left, b.left) > 0.5 &&
      Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 0.5;
    const found: string[] = [];
    for (const label of document.querySelectorAll("dt")) {
      const value = label.nextElementSibling;
      if (value?.tagName !== "DD") continue;
      const values = textBoxes(value);
      if (textBoxes(label).some((box) => values.some((other) => meet(box, other)))) {
        found.push(label.textContent ?? "");
      }
    }
    return found;
  });
}

test.beforeAll(() => {
  // The named fixture workspace exactly as seeded: P01's answers, version 1.
  stack("reset-demo");
});

for (const viewport of VIEWPORTS) {
  test.describe(viewport.name, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test(`[UI-11][UI-06][UI-04] every chapter and state at ${viewport.name}`, async ({
      browser,
    }, testInfo) => {
      test.setTimeout(300_000);
      const directory = target ?? testInfo.outputPath("screenshots");
      mkdirSync(directory, { recursive: true });
      const token = await emulatorToken("ada");
      const create = async (name: string, mode: "demo" | "live_assisted") =>
        (
          await asBrowser<{ workspace_id: string }>("POST", "/v1/workspaces", token, {
            name,
            data_mode: mode,
            synthetic: true,
          })
        ).workspace_id;
      const scratch: Scratch = {
        empty: await create("New workspace (synthetic)", "demo"),
        talked: await talkedWorkspace(token),
        live: await create("Live, no key yet (synthetic)", "live_assisted"),
      };
      const results: Result[] = [];
      const errors: string[] = [];
      const pages = new Map<string, Page>();

      for (const shot of shots(scratch)) {
        const key = shot.context ?? shot.as ?? "signed-out";
        let page = pages.get(key);
        if (page === undefined) {
          // A separate browser context per identity or condition: nothing carries over.
          const context = await browser.newContext({
            viewport: { width: viewport.width, height: viewport.height },
            reducedMotion: "reduce",
          });
          page = await context.newPage();
          page.on("console", (message) => {
            if (message.type() === "error") errors.push(message.text());
          });
          await shot.prepare?.(page);
          if (shot.as !== null) await signIn(page, shot.as, shot.url);
          pages.set(key, page);
        }
        errors.length = 0;
        await page.goto(shot.url);
        await shot.ready(page);
        await page.evaluate(() => document.fonts.ready);
        const fonts = await page.evaluate(
          () =>
            document.fonts.check('16px "Source Sans 3"') &&
            document.fonts.check('31px "Newsreader"'),
        );
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - window.innerWidth,
        );
        const overprinted = await overprintedLabels(page);
        const file = `${shot.name}--${viewport.name}.png`;
        await page.screenshot({ path: join(directory, file), fullPage: false });
        const violations = await axe(page);
        const unexpected = errors.filter(
          (line) => !(shot.refused && line.startsWith("Failed to load resource")),
        );
        results.push({
          file,
          fonts,
          overflow,
          overprinted,
          axe: violations,
          errors: [...unexpected],
        });
      }

      for (const page of pages.values()) await page.context().close();
      writeFileSync(
        join(directory, `checks-${viewport.name}.json`),
        `${JSON.stringify(results, null, 2)}\n`,
      );
      for (const result of results) {
        expect.soft(result.axe, `${result.file}: axe`).toEqual([]);
        expect.soft(result.overflow, `${result.file}: horizontal overflow`).toBeLessThanOrEqual(0);
        expect.soft(result.overprinted, `${result.file}: labels over values`).toEqual([]);
        expect.soft(result.errors, `${result.file}: console errors`).toEqual([]);
        expect.soft(result.fonts, `${result.file}: fonts loaded`).toBe(true);
      }
    });
  });
}
