import { expect, type Page, test } from "@playwright/test";
import { asBrowser, emulatorToken } from "./api";
import { chapterUrl, signIn, youView } from "./helpers";
import { stack } from "./stack";

type Workspace = { workspace_id: string; name: string };
type Profile = {
  version: number;
  document: {
    current_role: { state: string };
    work_status: { state: string; value?: string };
    qualifications: { state: string; value?: { name: string; status: string }[] };
    target_titles: { state: string; value?: string[] };
    direct_spend_cap: { state: string; value?: { minor_units: number; currency: string } };
    monthly_payment_cap: { state: string; value?: { minor_units: number; currency: string } };
  };
};

async function persona(id: "P01" | "P02" | "P03" | "P04" | "P05") {
  const token = await emulatorToken("ada");
  let cursor: string | null = null;
  do {
    const path: string = `/v1/workspaces${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`;
    const listed: { items: Workspace[]; next_cursor: string | null } = await asBrowser<{
      items: Workspace[];
      next_cursor: string | null;
    }>("GET", path, token);
    const workspace = listed.items.find((item) => item.name.startsWith(`${id} · `));
    if (workspace) return { token, workspace: workspace.workspace_id };
    cursor = listed.next_cursor;
  } while (cursor !== null);
  throw new Error(`The ${id} demo workspace is missing`);
}

async function openPersona(page: Page, id: "P01" | "P02" | "P03" | "P04" | "P05") {
  const found = await persona(id);
  await signIn(page, "ada", chapterUrl("you", found.workspace));
  await expect(page.getByRole("heading", { level: 1, name: "You" })).toBeVisible();
  await expect(page.getByRole("banner")).toContainText("Synthetic demo");
  return found;
}

test.beforeEach(() => {
  stack("reset-demo");
});

test("[JOURNEY-01] a new school leaver can start without a job and return to the saved answers", async ({
  page,
}) => {
  test.setTimeout(180_000);
  await signIn(page, "ada");
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("School leaver journey");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(page).toHaveURL(/\/w\/[\da-f-]+\/you$/);
  const workspace = /\/w\/([\da-f-]+)\/you$/.exec(new URL(page.url()).pathname)?.[1];
  if (!workspace) throw new Error("The new workspace did not open in You");

  const chapters = page.getByRole("navigation", { name: "Chapters" });
  await expect(chapters.getByRole("link", { name: "You, available" })).toBeVisible();
  await expect(chapters.getByText(/Routes.*Locked/)).toBeVisible();
  await expect(chapters.getByRole("link", { name: /Routes/ })).toHaveCount(0);
  await page.goto(chapterUrl("routes", workspace));
  await expect(
    page.getByRole("heading", { level: 1, name: "Routes needs an earlier step" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Open You" }).click();
  await page.goto(chapterUrl("plan", workspace));
  await expect(
    page.getByRole("heading", { level: 1, name: "Plan needs an earlier step" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Open You" }).click();

  await expect(
    page.getByRole("heading", { name: "What do you do now, or what did you do last?" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "I haven't had a job yet" }).click();
  await expect(page.getByRole("heading", { name: "How would you like to start?" })).toBeVisible();

  await youView(page, "What we know");
  await page.getByRole("button", { name: "Edit answers directly" }).click();
  await page.getByLabel("How you answer what you're doing now").selectOption("provided");
  await page
    .getByRole("combobox", { name: "What you're doing now", exact: true })
    .selectOption("in_education_or_training");
  await page.getByLabel("How you answer qualifications").selectOption("provided");
  await page.getByRole("textbox", { name: "Qualification 1" }).fill("GCSE maths");
  await page
    .getByRole("combobox", { name: "Qualification 1: achieved or expected" })
    .selectOption("expected");
  await page.getByLabel("How you answer target roles").selectOption("provided");
  await page.getByRole("textbox", { name: "Target role 1" }).fill("Registered nurse");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.locator("#edit-answers").getByText("Saved.", { exact: true })).toBeVisible();
  await expect(chapters.getByRole("link", { name: "You, direction chosen" })).toBeVisible();
  for (const chapter of ["Roles", "Skills", "Options"]) {
    await expect(chapters.getByRole("link", { name: `${chapter}, available` })).toBeVisible();
  }
  await expect(chapters.getByRole("link", { name: /Routes/ })).toHaveCount(0);

  const token = await emulatorToken("ada");
  const saved = await asBrowser<Profile>("GET", `/v1/workspaces/${workspace}/profile`, token);
  expect(saved.document.current_role.state).toBe("no_job_yet");
  expect(saved.document.work_status).toMatchObject({
    state: "provided",
    value: "in_education_or_training",
  });
  expect(saved.document.qualifications).toMatchObject({
    state: "provided",
    value: [{ name: "GCSE maths", status: "expected" }],
  });
  expect(saved.document.target_titles.value).toContain("Registered nurse");

  await page.reload();
  await youView(page, "What we know");
  const known = page.getByRole("tabpanel", { name: "What we know" });
  await expect(known.getByText("I haven't had a job yet", { exact: true })).toBeVisible();
  await expect(known).toContainText("GCSE maths");
  await expect(known).toContainText("Registered nurse");
});

test("[JOURNEY-01] an empty demo discovery gives a school leaver a way to continue", async ({
  page,
}) => {
  test.setTimeout(180_000);
  await signIn(page, "ada");
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("School activity discovery");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await page.getByRole("button", { name: "I haven't had a job yet" }).click();
  const workspace = /\/w\/([\da-f-]+)\/you$/.exec(new URL(page.url()).pathname)?.[1];
  if (!workspace) throw new Error("The school activity workspace did not open in You");
  const token = await emulatorToken("ada");
  await expect
    .poll(
      async () =>
        (await asBrowser<Profile>("GET", `/v1/workspaces/${workspace}/profile`, token)).document
          .current_role.state,
    )
    .toBe("no_job_yet");
  await youView(page, "What we know");
  await page.getByRole("button", { name: "Edit answers directly" }).click();
  await page.getByLabel("How you answer tasks you enjoy").selectOption("provided");
  await page
    .getByRole("textbox", { name: "Task you enjoy 1" })
    .fill("Helping younger students with maths");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.locator("#edit-answers").getByText("Saved.", { exact: true })).toBeVisible();

  await youView(page, "Suggestions");
  await page.getByRole("button", { name: "Suggest directions" }).click();
  const empty = page.getByRole("region", { name: "No directions found" });
  await expect(empty).toContainText("This synthetic demo searches your words in ESCO skill names", {
    timeout: 60_000,
  });
  await empty.getByRole("button", { name: "Add a concrete task" }).click();
  await expect(page.getByRole("tab", { name: "What we know" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByRole("heading", { name: "Edit your answers" })).toBeFocused();
  await expect(page.getByRole("textbox", { name: "Task you enjoy 1" })).toHaveValue(
    "Helping younger students with maths",
  );
});

test("[JOURNEY-02] the unsure demo has no assumed target and can discover directions", async ({
  page,
}) => {
  test.setTimeout(180_000);
  const { token, workspace } = await openPersona(page, "P02");
  const profile = await asBrowser<Profile>("GET", `/v1/workspaces/${workspace}/profile`, token);
  expect(profile.document.target_titles.value ?? []).toEqual([]);

  await youView(page, "Suggestions");
  const suggest = page.getByRole("button", { name: "Suggest directions" });
  await expect(suggest).toBeVisible();
  await suggest.click();
  const directions = page.getByRole("region", { name: "Directions to explore" });
  await expect(directions.getByRole("article").first()).toBeVisible({ timeout: 60_000 });
  const target = directions.getByRole("article").first();
  await expect(target.getByRole("button", { name: /Make this a target/ })).toBeVisible();
  await target.getByRole("button", { name: /Make this a target/ }).click();
  await expect(target.getByRole("heading", { name: "Saved as one of your targets" })).toBeVisible();
  const chosen = await asBrowser<Profile>("GET", `/v1/workspaces/${workspace}/profile`, token);
  expect(chosen.document.target_titles.value).toHaveLength(1);
  const title = chosen.document.target_titles.value?.[0];
  if (!title) throw new Error("The discovered role was not saved as a target");
  const chapters = page.getByRole("navigation", { name: "Chapters" });
  await expect(chapters.getByRole("link", { name: "Skills, available" })).toBeVisible();
  await chapters.getByRole("link", { name: "Options, available" }).click();
  await page.getByRole("button", { name: /Before a route search/ }).click();
  const review = page.getByRole("region", { name: "Review before a route search" });
  await review.locator("form").getByLabel("Choose one").selectOption("economic");
  await review.locator("form").getByRole("button", { name: "Save this answer" }).click();
  await expect(review).toContainText("if you don't make a change");
  await expect(chapters.getByRole("link", { name: /Routes/ })).toHaveCount(0);
  await page.goto(chapterUrl("you", workspace));
  await youView(page, "What we know");
  const targets = page.getByRole("region", { name: "Your targets" });
  await targets.getByRole("button", { name: `Remove ${title} from your targets` }).click();
  await expect(chapters.getByRole("link", { name: /Skills/ })).toHaveCount(0);
  await expect(chapters.getByText(/Skills.*Locked/)).toBeVisible();
  await targets.getByRole("button", { name: `Undo removing “${title}”` }).click();
  await expect(chapters.getByRole("link", { name: "Skills, available" })).toBeVisible();
});

test("[JOURNEY-03] the limited-budget demo shows its stated spending limits and options", async ({
  page,
}) => {
  const { token, workspace } = await openPersona(page, "P03");
  const profile = await asBrowser<Profile>("GET", `/v1/workspaces/${workspace}/profile`, token);
  expect(profile.document.target_titles.value).toContain("IT support technician");
  expect(profile.document.direct_spend_cap.value?.minor_units).toBe(30_000);
  expect(profile.document.monthly_payment_cap.value?.minor_units).toBe(10_000);
  await youView(page, "What we know");
  const known = page.getByRole("tabpanel", { name: "What we know" });
  await expect(known).toContainText("£300");
  await expect(known).toContainText("£100");
  await page.goto(chapterUrl("options", workspace));
  await expect(page.getByRole("heading", { level: 1, name: "Options" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "For IT support technician" })).toBeVisible();
  await expect(page.getByText("Funding that may apply to this target")).toBeVisible();
  await page.getByRole("button", { name: /Before a route search/ }).click();
  const review = page.getByRole("region", { name: "Review before a route search" });
  await review.getByText(/Your planning answers/).click();
  const answer = (label: string) =>
    review.locator("dt", { hasText: label }).locator("xpath=following-sibling::dd");
  await expect(answer("Money you have now")).toContainText("£200");
  await expect(answer("Cash to keep")).toContainText("£100");
  await expect(review.locator("dt")).toHaveCount(2);
});

test("[JOURNEY-04] the regulated target keeps its statutory gate unresolved", async ({ page }) => {
  const { token, workspace } = await openPersona(page, "P04");
  const profile = await asBrowser<Profile>("GET", `/v1/workspaces/${workspace}/profile`, token);
  expect(profile.document.target_titles.value).toContain("Registered nurse");
  await page.goto(chapterUrl("skills", workspace));
  await expect(page.getByRole("heading", { level: 1, name: "Skills" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Registered nurse" })).toBeVisible();
  await expect(page.getByText("Must be checked at its source.").first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Check the NMC register" })).toHaveAttribute(
    "href",
    "https://www.nmc.org.uk/registration/search-the-register/",
  );
  const question = page.getByRole("form", { name: "One skills question" });
  await question.getByLabel("Not sure").click();
  await question.getByRole("button", { name: "Save answer" }).click();
  await expect(question).toHaveCount(0);
  await page.reload();
  await page.getByText("Change your answer").first().click();
  await expect(page.getByLabel("Not sure").first()).toBeChecked();
  await page.getByLabel("Not yet").first().click();
  await page.getByRole("button", { name: "Save changed answer" }).first().click();
  await expect(page.getByLabel("Not yet").first()).toBeChecked();
  await expect(page.getByText(/modelled requirements met/)).toHaveCount(0);
  await page.goto(chapterUrl("roles", workspace));
  await expect(page.getByRole("heading", { level: 1, name: "Roles" })).toBeVisible();
  await expect(page.getByText(/0 vacancies in this workspace/)).toBeVisible();
  await expect(page.getByText(/No sources checked yet/)).toBeVisible();
});

test("[JOURNEY-01] a claimed skill with a concrete example advances the assessment", async ({
  page,
}) => {
  const { token, workspace } = await openPersona(page, "P01");
  await page.goto(chapterUrl("skills", workspace));
  const question = page.getByRole("form", { name: "One skills question" });
  for (let attempt = 0; attempt < 12; attempt += 1) {
    await expect(question).toBeVisible();
    if (await question.getByLabel("I have done this independently").count()) break;
    await question.getByLabel("Not sure").click();
    await question.getByRole("button", { name: "Save answer" }).click();
  }
  await expect(question.getByLabel("I have done this independently")).toBeVisible();
  const asked = await question.locator("h3").textContent();
  await question.getByLabel("I have done this independently").click();
  await question.getByLabel("Which description matches what you did?").selectOption("2");
  await question
    .getByLabel("An example, in your words")
    .fill("I checked data quality independently at work.");
  await question.getByLabel("When did you last do this?").fill("2026-10");
  await question.getByRole("button", { name: "Save answer" }).click();
  await expect(question.locator("h3")).not.toHaveText(asked ?? "");
  const saved = await asBrowser<{
    questions: { coverage: { required_rows_with_usable_evidence: number } };
  }>("GET", `/v1/workspaces/${workspace}/capability/skills`, token);
  expect(saved.questions.coverage.required_rows_with_usable_evidence).toBeGreaterThan(0);
  await page.reload();
  await expect(question.locator("h3")).not.toHaveText(asked ?? "");
  const correction = page.getByText("Correct your skill answer");
  if (!(await correction.isVisible())) await page.getByText(/^See all \d+ requirements$/).click();
  await correction.click();
  const form = page.getByRole("form", { name: "Correct your skill answer" });
  await expect(form.getByLabel("I have done this independently")).toBeChecked();
  await form.getByLabel("I am not sure").click();
  await form.getByRole("button", { name: "Save correction" }).click();
  await expect
    .poll(async () => {
      const current = await asBrowser<{
        questions: { coverage: { required_rows_with_usable_evidence: number } };
      }>("GET", `/v1/workspaces/${workspace}/capability/skills`, token);
      return current.questions.coverage.required_rows_with_usable_evidence;
    })
    .toBe(0);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Data quality analyst" })).toBeVisible();
  if (!(await correction.isVisible())) await page.getByText(/^See all \d+ requirements$/).click();
  await correction.click();
  await expect(form.getByLabel("I am not sure")).toBeChecked();
});

test("[JOURNEY-05] the returner sees a concrete target and its current assessment", async ({
  page,
}) => {
  const { token, workspace } = await persona("P05");
  await signIn(page, "ada");
  await page.getByRole("link", { name: /P05 · Bookkeeping returner/ }).click();
  await expect(page).toHaveURL(chapterUrl("you", workspace));
  await expect(page.getByRole("banner")).toContainText("Synthetic demo");
  const profile = await asBrowser<Profile>("GET", `/v1/workspaces/${workspace}/profile`, token);
  expect(profile.document.target_titles.value).toContain("Bookkeeping assistant");
  await page.goto(chapterUrl("skills", workspace));
  await expect(page.getByRole("heading", { level: 1, name: "Skills" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Bookkeeping assistant" })).toBeVisible();
  await expect(page.getByText("Not assessed yet. Here is what this role asks for.")).toBeVisible();
  await expect(page.getByText(/modelled requirements met/)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "What you can already show" })).toBeVisible();
});

test("[JOURNEY-05] a returner can answer and revise a course entry requirement", async ({
  page,
}) => {
  const { token, workspace } = await persona("P05");
  const options = await asBrowser<{
    targets: {
      target_title: string;
      catalogue: {
        concepts: { concept_id: string; title: string | null; entry_requirements: unknown[] }[];
      } | null;
    }[];
  }>("GET", `/v1/workspaces/${workspace}/planning/options`, token);
  const catalogue = options.targets.find(
    (item) => item.target_title === "Bookkeeping assistant",
  )?.catalogue;
  const course = catalogue?.concepts.find((item) => item.entry_requirements.length > 0);
  if (!course?.title) throw new Error("P05 has no course with an entry requirement");

  await signIn(page, "ada", chapterUrl("options", workspace));
  await page.getByRole("button").filter({ hasText: course.title }).first().click();
  const detail = page.locator(".option-detail");
  await expect(
    detail.getByLabel("Do you meet the entry requirements? Your answer is not checked."),
  ).toBeVisible();
  await detail
    .getByLabel("Do you meet the entry requirements? Your answer is not checked.")
    .selectOption("yes");
  await detail.getByRole("button", { name: "Save entry answer" }).click();
  await expect(detail.getByText(/You said you meet the entry requirements/)).toBeVisible();

  await page.reload();
  await page.getByRole("button").filter({ hasText: course.title }).first().click();
  await expect(detail.getByText(/You said you meet the entry requirements/)).toBeVisible();
  await detail.getByText("Change entry answer").click();
  await detail
    .getByLabel("Do you meet the entry requirements? Your answer is not checked.")
    .selectOption("no");
  await detail.getByRole("button", { name: "Save entry answer" }).click();
  await expect(detail.getByText(/You said you do not meet the entry requirements/)).toBeVisible();
});

test("[JOURNEY-06] a target in the person's own words stays explorable without invented evidence", async ({
  page,
}) => {
  await signIn(page, "ada");
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("Own-words target journey");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(page).toHaveURL(/\/w\/[\da-f-]+\/you$/);
  const workspace = /\/w\/([\da-f-]+)\/you$/.exec(new URL(page.url()).pathname)?.[1];
  if (!workspace) throw new Error("The own-words workspace did not open in You");

  await youView(page, "What we know");
  await page.getByRole("button", { name: "Edit answers directly" }).click();
  await page.getByLabel("How you answer target roles").selectOption("provided");
  await page.getByRole("textbox", { name: "Target role 1" }).fill("Canopy astronaut");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.locator("#edit-answers").getByText("Saved.", { exact: true })).toBeVisible();

  await page
    .getByRole("navigation", { name: "Chapters" })
    .getByRole("link", { name: /Skills/ })
    .click();
  await expect(page.getByRole("heading", { level: 1, name: "Skills" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Canopy astronaut" })).toBeVisible();
  await expect(
    page.getByText("Careerwright has no reviewed course or role pack for this target yet."),
  ).toBeVisible();
  await expect(
    page.getByText("Careerwright has no checked requirements for this target yet."),
  ).toBeVisible();

  await page
    .getByRole("navigation", { name: "Chapters" })
    .getByRole("link", { name: /Options/ })
    .click();
  await expect(page.getByRole("heading", { name: "For Canopy astronaut" })).toBeVisible();
  await expect(
    page.getByText(
      "No reviewed option found yet. That does not mean there are none. You can add one you know about.",
    ),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Add your own option" })).toBeVisible();
});
