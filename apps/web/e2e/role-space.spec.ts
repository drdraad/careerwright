// Your title, recognised (Task 6d slice B; S2.8; ADR 0015): the role-space appendix's test, in
// the demo workspace with no key and nothing leaving this machine, on the full pinned ESCO
// release and UK job-title index. Each title appears as a UK job title from ONS; picking one
// keeps its words, the world answers within ten seconds (the API's part is within a second,
// `backend/tests/integration/test_first_answer.py`), and "Which of these is closest?" offers
// the ESCO occupations in its group with "None of these is my job". A title neither list holds
// is kept in the person's own words, and the world says what isn't known yet, asking no one to
// pick another job. A discovery's title ideas are the fixture's, which never invents a title,
// so acceptance 4 is the API's and the slate's tests (`test_role_space.py`, DSC-20,
// `Directions.test.tsx`).
import { expect, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken } from "./api";
import { chapterUrl, externalRequests, recordRequests, signIn, youView } from "./helpers";

const ANSWERED_WITHIN_MS = 10_000; // plan section 4: the world has answered within ten seconds

async function demoWorkspace(name: string): Promise<string> {
  const created = await asBrowser<{ workspace_id: string }>(
    "POST",
    "/v1/workspaces",
    await emulatorToken("ada"),
    { name, data_mode: "demo", synthetic: true },
  );
  return created.workspace_id;
}

type Origin = {
  role: { text: string | null; state: string; occupation: unknown };
  usual_skills: unknown[];
  destinations: unknown[];
};

/** The origin the page reads: what the world and the start state about the role. */
async function originOf(workspace: string): Promise<Origin> {
  return asBrowser<Origin>("GET", `/v1/workspaces/${workspace}/origin`, await emulatorToken("ada"));
}

/** Acceptance 5: nothing states skills or destinations for a role no ESCO occupation names.
 *  (This replaced a check that the world draws no skill labels, which it never does: design
 *  review M-6.) */
async function statesNoSkills(workspace: string) {
  const shown = await originOf(workspace);
  expect(shown.role.state).toBe("not_in_esco");
  expect(shown.role.occupation).toBeNull();
  expect(shown.usual_skills).toEqual([]);
  expect(shown.destinations).toEqual([]);
}

const field = (page: Page) => page.getByRole("combobox", { name: "Your job title" });
const origin = (page: Page) => page.locator(".world-label[data-label='origin']");
const ukTitle = (page: Page, title: string) =>
  page.getByRole("option", { name: new RegExp(`^${title}\\s*,\\s*UK job title \\(ONS\\)$`) });

/** Picks an option and returns how long the world took to answer: the person's light lit. */
async function answer(page: Page, pick: () => Promise<void>): Promise<number> {
  await expect(origin(page)).toContainText("Your light comes on with your first answer");
  const started = Date.now();
  await pick();
  await expect(origin(page)).toContainText("Your light, lit by your answers", {
    timeout: ANSWERED_WITHIN_MS,
  });
  return Date.now() - started;
}

test("[DIV1-13][DIV1-14][WLD-01] any UK title is offered as you type; picking one keeps its words, the world answers, and which is closest is asked", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const requests = recordRequests(page);
  const workspace = await demoWorkspace("Your title (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  await expect(
    page.getByRole("heading", { name: "What do you do now, or what did you do last?" }),
  ).toBeVisible();

  // Acceptance 1: each appears as a title to pick, marked as a UK job title from ONS, with the
  // person's own words always offered too.
  for (const title of ["Registered nurse", "Data quality analyst", "Prompt engineer", "Doula"]) {
    await field(page).fill(title);
    await expect(ukTitle(page, title)).toBeVisible();
    await expect(page.getByRole("option", { name: `Use my own words: “${title}”` })).toBeVisible();
  }

  // Acceptance 2: picking one keeps the exact words, the world answers, and the ESCO
  // occupations in its ISCO-08 group are offered with "None of these is my job".
  await field(page).fill("Registered nurse");
  const took = await answer(page, () => ukTitle(page, "Registered nurse").click());
  console.log(`the world answered the first answer in ${took} ms`);
  expect(took).toBeLessThan(ANSWERED_WITHIN_MS);
  await expect(page.getByRole("heading", { name: "Which of these is closest?" })).toBeFocused();
  // ISCO-08 group 2221, named in plain words (design review M-5).
  const group = page.getByRole("region", { name: "Nursing professionals" });
  await expect(group.getByRole("button", { name: "specialist nurse" })).toBeVisible();
  await expect(
    group.getByRole("button", { name: "nurse responsible for general care" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "None of these is my job" })).toBeVisible();
  await youView(page, "What we know");
  await expect(
    page.getByRole("tabpanel", { name: "What we know" }).getByText("Registered nurse", {
      exact: true,
    }),
  ).toBeVisible();
  await youView(page, "Conversation");

  // "None of these is my job": the role keeps the words, names no ESCO occupation, and the
  // world says what isn't known yet. Acceptance 5: it states no skills for it.
  await page.getByRole("button", { name: "None of these is my job" }).click();
  await expect(
    page.getByText(
      "Careerwright found “Registered nurse” in the UK job-title index and keeps it as your role, in your words. What this work asks for isn't known yet.",
    ),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "How would you like to start?" })).toBeFocused();
  await statesNoSkills(workspace);
  expect(externalRequests(requests)).toEqual([]);
});

test("[STATE-11][PROF-14] “I haven't had a job yet” lights the world within ten seconds, and nothing asks for a job again, in the demo with no key", async ({
  page,
}) => {
  // Task 6f: an answer about the role, never a job title, Skipped or Unknown.
  test.setTimeout(120_000);
  const requests = recordRequests(page);
  const workspace = await demoWorkspace("No job yet (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  await expect(
    page.getByRole("heading", { name: "What do you do now, or what did you do last?" }),
  ).toBeVisible();

  const took = await answer(page, () =>
    page.getByRole("button", { name: "I haven't had a job yet" }).click(),
  );
  console.log(`the world answered "I haven't had a job yet" in ${took} ms`);
  expect(took).toBeLessThan(ANSWERED_WITHIN_MS);
  await expect(page.getByRole("heading", { name: "How would you like to start?" })).toBeFocused();
  await expect(page.getByText(/what this work asks for/i)).toHaveCount(0);

  // Exploring opens without a job, and the demo's next question asks what they enjoy.
  await page.getByRole("button", { name: "Help me explore" }).click();
  await expect(
    page.getByRole("heading", { name: "What would you like your working life to be like?" }),
  ).toBeVisible();
  await page
    .getByRole("group", { name: "Example replies" })
    .getByRole("button", { name: "Skip" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "What do you enjoy doing, at school, at work or in your own time?",
    }),
  ).toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole("combobox", { name: "Your job title" })).toHaveCount(0);

  await youView(page, "What we know");
  await expect(
    page.getByRole("tabpanel", { name: "What we know" }).getByText("I haven't had a job yet", {
      exact: true,
    }),
  ).toBeVisible();
  expect(externalRequests(requests)).toEqual([]);
});

test("[PROF-11] seniority and industry beside the role, and a skill ESCO lists marked not part of my job, in the demo", async ({
  page,
}) => {
  // Task 6d slice C: each optional and never a default; the mark is a display state, never
  // evidence. No key, nothing leaves this machine.
  test.setTimeout(120_000);
  const requests = recordRequests(page);
  const workspace = await demoWorkspace("Seniority and industry (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));
  await field(page).fill("Registered nurse");
  await ukTitle(page, "Registered nurse").click();
  await page.getByRole("button", { name: "specialist nurse" }).click();
  await expect(page.getByRole("heading", { name: "How would you like to start?" })).toBeFocused();

  await youView(page, "What we know");
  const details = page.getByRole("region", { name: "Seniority and industry" });
  await expect(details.getByText("Seniority and industry: not given.")).toBeVisible();
  await details
    .getByRole("button", { name: "Add seniority or industry for Registered nurse" })
    .click();
  await details.getByLabel("Seniority (optional)").fill("Band 6");
  await details.getByRole("button", { name: "Save" }).click();
  await expect(details.getByText("Seniority: Band 6. Industry: not given.")).toBeVisible();

  await details.getByText(/skills that ESCO, .* lists for this kind of work$/).click();
  const mark = details.getByRole("button", { name: /^Not part of my job\s*:/ }).first();
  await expect(mark).toHaveAttribute("aria-pressed", "false");
  await mark.click();
  await expect(mark).toHaveAttribute("aria-pressed", "true");
  const shown = await asBrowser<{
    usual_skills: { state: string; not_part_of_job: boolean }[];
  }>("GET", `/v1/workspaces/${workspace}/origin`, await emulatorToken("ada"));
  const marked = shown.usual_skills.filter((skill) => skill.not_part_of_job);
  expect(marked).toHaveLength(1);
  expect(marked[0]?.state).toBe("usual_in_role"); // still ESCO's, never the person's evidence
  expect(externalRequests(requests)).toEqual([]);
});

test("[DIV1-13][DIV1-03][WLD-01] a title neither list holds is kept in the person's own words, and the world still answers", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const requests = recordRequests(page);
  const workspace = await demoWorkspace("Own words (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));

  // Acceptance 3: ESCO's closest titles are asked about, and "None of these is my job" keeps
  // the words as typed.
  await field(page).fill("Bookkeeping assistant");
  await expect(
    page.getByText(
      "Careerwright couldn't match that title in ESCO, the EU's list of jobs and skills. Is it one of these?",
    ),
  ).toBeVisible();
  const own = page.getByRole("option", { name: /^None of these is my job/ });
  await expect(own).toContainText("Use my own words: “Bookkeeping assistant”");
  const took = await answer(page, () => own.click());
  expect(took).toBeLessThan(ANSWERED_WITHIN_MS);

  await expect(
    page.getByText(
      "Careerwright keeps “Bookkeeping assistant” as your role, in your words. It couldn't match it in ESCO or the UK job-title index, so what this work asks for isn't known yet.",
    ),
  ).toBeVisible();
  // It asks no one to pick a different job: no closest question, straight on to how to start.
  await expect(page.getByRole("heading", { name: "Which of these is closest?" })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "How would you like to start?" })).toBeVisible();
  await statesNoSkills(workspace);
  await youView(page, "What we know");
  await expect(
    page.getByRole("tabpanel", { name: "What we know" }).getByText("Bookkeeping assistant", {
      exact: true,
    }),
  ).toBeVisible();
  expect(externalRequests(requests)).toEqual([]);
});

test("[PROF-09][DIV1-13][WLD-08] a risk phrase at the first question shows the calm panel, stills the world and keeps nothing", async ({
  page,
}) => {
  // Design review I-3, in the demo: the title field goes through the support screen as a
  // message does. The phrase is the support tests' own (`conversation.spec.ts`).
  test.setTimeout(120_000);
  const workspace = await demoWorkspace("Support at the start (synthetic)");
  await signIn(page, "ada", chapterUrl("you", workspace));

  await field(page).fill("Some days I just want to die.");
  const panel = page.getByRole("region", { name: "Support is available" });
  await expect(panel).toContainText(
    "Careerwright keeps it as your job title only if you choose to. You can also type again or skip this question.",
  );
  await expect(panel).toContainText("Samaritans: Call 116 123");
  await expect(panel).toContainText("Childline: Call 0800 1111"); // support-policy-12
  await expect(page.locator(".world")).toHaveAttribute("data-distress", "true");
  await expect(page.getByRole("option")).toHaveCount(0); // nothing offered in those words
  await field(page).press("Enter");

  // Nothing kept by itself: no role. The person can keep it by their own choice (offered, not
  // taken here), type again or skip (fix round 2, re-review R-M3).
  expect((await originOf(workspace)).role).toMatchObject({ text: null, state: "not_answered" });
  await expect(panel.getByRole("button", { name: "Keep it as my job title" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Skip for now" })).toBeVisible();
  await panel.getByRole("button", { name: "Dismiss the support note" }).click();
  await expect(page.locator(".world")).toHaveAttribute("data-distress", "false");
  await expect(field(page)).toBeFocused();
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("[PROF-09][UI-12] at 390 × 844 the title field's support panel is above the field, its heading in view while the field has focus", async ({
    page,
  }) => {
    // Design re-review R-I1: below the field, a phone's keyboard would cover the panel while the
    // person types; the message panel sits above the reply field. This checks the layout only:
    // a real phone's keyboard is a human check. The phrase is the support tests' own.
    test.setTimeout(120_000);
    const workspace = await demoWorkspace("Support at the start, phone (synthetic)");
    await signIn(page, "ada", chapterUrl("you", workspace));

    await field(page).fill("Some days I just want to die.");
    const panel = page.getByRole("region", { name: "Support is available" });
    await expect(panel).toBeVisible();
    await expect(field(page)).toBeFocused();
    const shown = await panel.boundingBox();
    const heading = await panel
      .getByRole("heading", { name: "Support is available" })
      .boundingBox();
    const typed = await field(page).boundingBox();
    expect(shown && heading && typed).toBeTruthy();
    if (shown === null || heading === null || typed === null) return;
    expect(shown.y + shown.height).toBeLessThanOrEqual(typed.y); // above the field
    expect(heading.y).toBeGreaterThanOrEqual(0); // in view as it appears, nothing scrolled
    expect(heading.y + heading.height).toBeLessThanOrEqual(844);
    // Design re-review 2, R2-M1: the choice the panel's line names sits next to that line,
    // above the services, so it is in the first screen too.
    const line = await panel
      .getByText(/keeps it as your job title only if you choose/)
      .boundingBox();
    const keep = await panel.getByRole("button", { name: "Keep it as my job title" }).boundingBox();
    const services = await panel.getByRole("list").boundingBox();
    expect(line && keep && services).toBeTruthy();
    if (line === null || keep === null || services === null) return;
    expect(keep.y).toBeGreaterThanOrEqual(line.y + line.height); // right after the line
    expect(keep.y + keep.height).toBeLessThanOrEqual(services.y); // before the services
    expect(keep.y + keep.height).toBeLessThanOrEqual(844); // in the first screen
  });
});
