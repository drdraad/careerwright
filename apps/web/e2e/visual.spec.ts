// The visual review package (plan section 5, UI-11): every chapter and the shell's default,
// selected, empty, stale, unavailable and failed states, and the You chapter's states as
// rebuilt in Sprint W and finished in Task W2E (the start with its reply field, what we know
// with the limits explained, a reply to review, a decided reply with Undo, the role-or-explore
// question with its two ways on, the slate in its own view with its written note written,
// pending and unavailable, a chosen target confirmed in place, the support panel, a failed
// reply, key consent, Unknown/Skipped/Prefer not to say, the scrolled stale conflict and its
// Save, and expanded phone sheets), Routes not built yet in the fixture workspace too (the
// route preview left the person's path, the audit's ruling), at
// 1440×900, 390×844 and 768×1024, plus the home page at 200 % zoom, each with the automatable
// checks: axe (WCAG 2.0, 2.1 and 2.2 A/AA), horizontal overflow, a label overprinting its
// value, a select cutting off its chosen option, console errors and font loading. These
// checks are evidence for a human review, not the review itself (ruling R2).
//
// `pnpm run review-screenshots` writes the PNGs and checks-<viewport>.json to
// docs/reviews/sprint-2/screenshots/; otherwise (make acceptance) they go to the test output
// and only the checks gate.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page, test } from "@playwright/test";
import {
  asBrowser,
  chosenTargetWorkspace,
  emulatorToken,
  roleQuestionWorkspace,
  saveElsewhere,
  talkedWorkspace,
} from "./api";
import { type AxeViolation, axe, chapterUrl, liveUpdates, saved, signIn, youView } from "./helpers";
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
  await expect(saved(page)).toHaveText("Answers saved");
  await expect(liveUpdates(page, "Live")).toBeVisible();
};

/** The You chapter, in one of its views. */
const inYou = (view: "What we know" | "Suggestions") => async (page: Page) => {
  await heading("You")(page);
  await youView(page, view);
};

let staleSaves = 0;

/**
 * A save refused as stale: an answer typed here while another tab saves a newer version.
 * Returns the notice and the field's inline note with the newer value.
 */
async function staleSave(page: Page, workspace: string) {
  await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
  await expect(liveUpdates(page, "Live")).toBeVisible();
  await youView(page, "What we know");
  await page.getByRole("button", { name: "Edit answers directly" }).click();
  await page.getByLabel("How you answer current role").selectOption("provided");
  await page.getByRole("textbox", { name: "Current role", exact: true }).fill("Typed on this page");
  // A new value each time, so every call makes a newer version (the same answer would not).
  staleSaves += 1;
  const elsewhere = `Saved in another tab (${staleSaves})`;
  await saveElsewhere(workspace, "ada", "current_role", elsewhere);
  await page.getByRole("button", { name: "Save changes" }).click();
  const notice = page.getByText("Your answers changed while you were editing");
  await expect(notice).toBeVisible();
  const inline = page.getByText(`The newer answers have ${elsewhere} here.`);
  await expect(inline).toBeVisible();
  return { notice, inline };
}

/** Opens the phone and tablet sheet to its full height; on a wide screen it is a column. */
async function expandSheet(page: Page, title = "Where this came from") {
  const sheet = page.getByRole("dialog", { name: title });
  const more = sheet.getByRole("button", { name: "More" });
  if (await more.isVisible()) {
    await more.click();
    await expect(sheet.getByRole("button", { name: "Less" })).toBeVisible();
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

/** The API's support panel (`careerwright.profile.safety.SUPPORT_NOTE` and its resources). */
const SUPPORT_NOTE = {
  policy_version: "support-policy-7",
  review_status:
    "accepted for L0 at session 1 (human gate H-12); the three phrasings added on 2026-10-28 " +
    "are not yet reviewed as built",
  message:
    "If anything you mentioned is about how you are feeling, support is available any time, " +
    "from people trained to help. Your message was sent to Careerwright as usual.",
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

/** The first suggestion's "Why this could suit you", once its written note reads `state`;
 *  a missing note is shown from the notice above the cards, which holds its action. */
const slateNote =
  (state: RegExp, notice = false) =>
  async (page: Page) => {
    await youView(page, "Suggestions");
    const directions = page.getByRole("region", { name: "Directions to explore" });
    const first = directions.getByRole("article").first();
    await expect(first.getByText(state)).toBeVisible({ timeout: 60_000 });
    const anchor = notice
      ? directions.getByText(/^No written note:/)
      : first.getByText("Why this could suit you");
    // The callback runs in the page, so the block is passed to it.
    await anchor.evaluate(
      (element, block) => element.scrollIntoView({ block }),
      notice ? ("start" as const) : ("center" as const),
    );
  };

type DiscoveryPage = {
  items: { explanation: { run: object; written: unknown; can_retry: boolean } | null }[];
};

/** The latest discovery as the API answers it, with its slate's written note shown in
 *  another state: still running, failed after its request (invalid twice), or refused
 *  before any request reached a model (over budget, so it may be tried again). */
const noteIn = (state: "running" | "failed" | "reached_no_model") => (page: Page) =>
  page.route("**/discoveries?*", async (route) => {
    const response = await route.fetch();
    const found = (await response.json()) as DiscoveryPage;
    for (const item of found.items) {
      if (item.explanation === null) continue;
      item.explanation.run = {
        ...item.explanation.run,
        status: state === "running" ? "running" : "failed",
        failure_class: {
          running: null,
          failed: "invalid_model_output",
          reached_no_model: "budget_exceeded",
        }[state],
      };
      item.explanation.can_retry = state === "reached_no_model";
      item.explanation.written = null;
    }
    await route.fulfill({ response, json: found });
  });

/** The latest discovery with no note asked for yet, and the request for one refused with
 *  `code` and `reason`, as the API refuses it before any run. */
const noteRefused = (code: string, reason: string) => async (page: Page) => {
  await page.route("**/discoveries?*", async (route) => {
    const response = await route.fetch();
    const found = (await response.json()) as DiscoveryPage;
    for (const item of found.items) item.explanation = null;
    await route.fulfill({ response, json: found });
  });
  await page.route("**/discoveries/*/explanation", (route) =>
    route.request().method() === "POST"
      ? route.fulfill({
          status: 422,
          json: {
            error: {
              code,
              message: "Refused.",
              retryable: false,
              stage: "profile",
              correlation_id: "visual",
              details: { reason },
            },
          },
        })
      : route.continue(),
  );
};

/** Workspaces the Sprint 2 shots start from, prepared through the API as a person would. */
type Scratch = {
  /** New and empty: nothing saved, nothing chosen. */
  empty: string;
  /** Answers saved, a reply to review and a completed discovery (demo interviewer). */
  talked: string;
  /** Live-assisted and synthetic, no key stored: the consent form. */
  live: string;
  /** As `talked`, for the shot that decides the reply's proposals (its own, so `talked` keeps
   *  its reply to review and its slate current). */
  decided: string;
  /** The early answers given, no target: "Do you have a role in mind…" with its two ways on. */
  asking: string;
  /** As `talked`, with the suggestion its slate opens on made a target from the slate. */
  chosen: string;
};

/** `scratch` workspaces are new synthetic workspaces of Ada's (see `Scratch`). */
const shots = (scratch: Scratch): Shot[] => [
  {
    name: "sign-in",
    as: null,
    url: "/sign-in",
    ready: async (page) => {
      await expect(page.getByRole("heading", { name: "Sign in to Careerwright" })).toBeVisible();
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
      // Chat is immediate (session 2): the reply field is there from the first screen.
      await expect(page.getByRole("textbox", { name: "Reply to Careerwright" })).toBeVisible();
    },
  },
  {
    // What we know, its own view: the answers, the two limits explained in plain words.
    name: "you--what-we-know",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await inYou("What we know")(page);
      await expect(page.getByText(/^The most you'd spend on the whole change/)).toBeVisible();
      await expect(page.getByText("Loading the early sketch")).toHaveCount(0); // B-M5
    },
  },
  {
    // The reply's proposals decided: what it saved, with Undo in its own colour.
    name: "you--saved",
    as: "ada",
    url: chapterUrl("you", scratch.decided),
    ready: async (page) => {
      const tray = page.getByRole("region", { name: /To review:/ });
      await expect(tray).toBeVisible();
      for (const choose of await tray.getByRole("button", { name: /^(Accept|Confirm)/ }).all()) {
        await choose.click();
      }
      await tray.getByRole("button", { name: /^Save \d to What we know/ }).click();
      await expect(page.getByRole("heading", { name: "Saved to What we know" })).toBeFocused();
      await expect(page.getByRole("button", { name: "Undo the last save" })).toBeVisible();
    },
  },
  {
    name: "you--source-drawer",
    as: "ada",
    url: chapterUrl("you"),
    ready: async (page) => {
      await inYou("What we know")(page);
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
      await inYou("What we know")(page);
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
      await inYou("What we know")(page);
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
      await inYou("What we know")(page);
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
    // The demo's role question: two ways on, which open existing views (STATE-09).
    name: "you--role-or-explore",
    as: "ada",
    url: chapterUrl("you", scratch.asking),
    ready: async (page) => {
      await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
      await expect(
        page.getByRole("heading", {
          name: "Do you have a role in mind, or would you like to explore?",
        }),
      ).toBeVisible();
      await expect(page.getByRole("button", { name: "Show me suggestions" })).toBeVisible();
    },
  },
  {
    // The slate with its written note (S2.7), here the demo explainer's.
    name: "you--slate",
    as: "ada",
    url: chapterUrl("you", scratch.talked),
    ready: slateNote(/Written by the demo explainer \(synthetic\)/),
  },
  {
    // A target chosen from the slate: confirmed in place, never "out of date" (STATE-10).
    name: "you--target-chosen",
    as: "ada",
    url: chapterUrl("you", scratch.chosen),
    ready: async (page) => {
      await heading("You")(page);
      await youView(page, "Suggestions");
      await expect(page.getByRole("heading", { name: "Saved as one of your targets" })).toBeVisible(
        { timeout: 60_000 },
      );
      await expect(page.getByText("Based on your earlier answers")).toHaveCount(0);
    },
  },
  {
    name: "you--slate-note-pending",
    as: "ada",
    context: "note-pending",
    url: chapterUrl("you", scratch.talked),
    prepare: noteIn("running"),
    ready: slateNote(/writing a note/),
  },
  {
    name: "you--slate-note-unavailable",
    as: "ada",
    context: "note-unavailable",
    url: chapterUrl("you", scratch.talked),
    prepare: noteIn("failed"),
    ready: slateNote(/The reply didn't pass Careerwright's checks twice\. Nothing from it/, true),
  },
  {
    name: "you--slate-note-retry",
    as: "ada",
    context: "note-retry",
    url: chapterUrl("you", scratch.talked),
    prepare: noteIn("reached_no_model"),
    ready: slateNote(/The spending limit for model calls is reached\. Nothing from it/, true),
  },
  {
    // Refused because no answer can be quoted: asking again would repeat it, so the notice
    // says to change the answers and offers no Try again.
    name: "you--slate-note-too-short",
    as: "ada",
    context: "note-too-short",
    url: chapterUrl("you", scratch.talked),
    prepare: noteRefused("INSUFFICIENT_EVIDENCE", "no_quotable_answer"),
    refused: true, // the intercepted 422 is logged as a failed load
    ready: slateNote(
      /Your answers can't be quoted on their own\. Careerwright didn't ask the model/,
      true,
    ),
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
        .getByRole("textbox", { name: "Reply to Careerwright" })
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
      await expect(
        page.getByText("The reply didn't pass Careerwright's checks twice"),
      ).toBeVisible();
      await page.getByRole("button", { name: "Try again" }).scrollIntoViewIfNeeded();
    },
  },
  {
    name: "you--key-consent",
    as: "ada",
    url: chapterUrl("you", scratch.live),
    ready: async (page) => {
      await expect(
        page.getByRole("heading", { name: "Connect your Meta API key to talk with Careerwright" }),
      ).toBeVisible();
    },
  },
  { name: "roles", as: "ada", url: chapterUrl("roles"), ready: heading("Roles") },
  { name: "skills", as: "ada", url: chapterUrl("skills"), ready: heading("Skills") },
  { name: "options", as: "ada", url: chapterUrl("options"), ready: heading("Options") },
  {
    // The fixture workspace too: the route preview left the person's path (Storybook keeps
    // it for design review until Routes is built).
    name: "routes",
    as: "ada",
    url: chapterUrl("routes"),
    ready: async (page) => {
      await heading("Routes")(page);
      await expect(page.getByText("Not built yet", { exact: true })).toBeVisible();
      await expect(page.getByText("Fixture preview: not your routes")).toHaveCount(0);
    },
  },
  { name: "plan", as: "ada", url: chapterUrl("plan"), ready: heading("Plan") },
  {
    name: "routes--empty",
    as: "ada",
    url: chapterUrl("routes", scratch.empty),
    ready: async (page) => {
      // A place not built yet: the reference's short card, one sentence on why it is empty
      // (its kicker; the rail's marks say it in lower case).
      await expect(page.getByText("Not built yet", { exact: true })).toBeVisible();
      await expect(page.getByText(/^Route search isn't ready yet/)).toBeVisible();
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
        page.getByRole("alert").getByText("Careerwright's service isn't reachable"),
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
  /** Selects whose chosen option is cut off (page overflow stays zero when it is: V-05). */
  clipped: string[];
  axe: AxeViolation[];
  errors: string[];
};

const target = process.env.CAREERWRIGHT_REVIEW_DIR;

/**
 * The chosen option of each visible select that is wider than the select can show it: a copy
 * holding only that option, sized to fit it (padding and the native arrow included), is
 * compared with the select's real width.
 */
function clippedSelects(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const found: string[] = [];
    for (const select of document.querySelectorAll("select")) {
      if (select.getClientRects().length === 0 || select.parentElement === null) continue;
      const text = select.selectedOptions[0]?.textContent ?? "";
      const copy = select.cloneNode(false) as HTMLSelectElement;
      copy.removeAttribute("id");
      copy.append(new Option(text));
      Object.assign(copy.style, {
        position: "absolute",
        visibility: "hidden",
        width: "auto",
        minWidth: "0",
        maxWidth: "none",
      });
      select.parentElement.append(copy);
      const needed = copy.getBoundingClientRect().width;
      copy.remove();
      if (needed > select.getBoundingClientRect().width + 0.5) found.push(text);
    }
    return found;
  });
}

/** The automatable checks on the page as it is, and its screenshot at `path`. */
async function measure(page: Page, path: string): Promise<Omit<Result, "file" | "errors">> {
  await page.evaluate(() => document.fonts.ready);
  const fonts = await page.evaluate(
    () => document.fonts.check('16px "Source Sans 3"') && document.fonts.check('600 39px "Outfit"'),
  );
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  const overprinted = await overprintedLabels(page);
  const clipped = await clippedSelects(page);
  await page.screenshot({ path, fullPage: false });
  return { fonts, overflow, overprinted, clipped, axe: await axe(page) };
}

/** `reflow: false` only below 320 CSS px, where WCAG 1.4.10 no longer asks for one column. */
function expectClean(results: Result[], reflow = true) {
  for (const result of results) {
    expect.soft(result.axe, `${result.file}: axe`).toEqual([]);
    if (reflow) {
      expect.soft(result.overflow, `${result.file}: horizontal overflow`).toBeLessThanOrEqual(0);
    }
    expect.soft(result.overprinted, `${result.file}: labels over values`).toEqual([]);
    expect.soft(result.clipped, `${result.file}: clipped select options`).toEqual([]);
    expect.soft(result.errors, `${result.file}: console errors`).toEqual([]);
    expect.soft(result.fonts, `${result.file}: fonts loaded`).toBe(true);
  }
}

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
        decided: await talkedWorkspace(token),
        asking: await roleQuestionWorkspace(token),
        chosen: (await chosenTargetWorkspace(token)).workspace,
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
        const file = `${shot.name}--${viewport.name}.png`;
        const checks = await measure(page, join(directory, file));
        const unexpected = errors.filter(
          (line) => !(shot.refused && line.startsWith("Failed to load resource")),
        );
        results.push({ file, ...checks, errors: [...unexpected] });
      }

      for (const page of pages.values()) await page.context().close();
      writeFileSync(
        join(directory, `checks-${viewport.name}.json`),
        `${JSON.stringify(results, null, 2)}\n`,
      );
      expectClean(results);
    });
  });
}

/** 200 % browser zoom: the same screen with half the CSS pixels at twice the density. */
const ZOOMED = [
  { name: "1440x900-zoom200", width: 720, height: 450 },
  { name: "390x844-zoom200", width: 195, height: 422 },
] as const;

test("[UI-06] the data mode's choice and its explanation at 200 % zoom (V-05)", async ({
  browser,
}, testInfo) => {
  const directory = target ?? testInfo.outputPath("screenshots");
  mkdirSync(directory, { recursive: true });
  const results: Result[] = [];
  for (const zoom of ZOOMED) {
    const context = await browser.newContext({
      viewport: { width: zoom.width, height: zoom.height },
      deviceScaleFactor: 2,
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    await signIn(page, "ben", "/");
    await expect(page.getByText("No workspaces yet")).toBeVisible();
    await page
      .getByRole("combobox", { name: "Data mode" })
      .evaluate((element) => element.scrollIntoView({ block: "center" }));
    const file = `home--empty--${zoom.name}.png`;
    results.push({ file, ...(await measure(page, join(directory, file))), errors });
    await context.close();
  }
  writeFileSync(join(directory, "checks-zoom200.json"), `${JSON.stringify(results, null, 2)}\n`);
  for (const [index, zoom] of ZOOMED.entries()) {
    const result = results[index];
    if (result !== undefined) expectClean([result], zoom.width >= 320);
  }
});
