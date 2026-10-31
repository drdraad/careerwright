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
  await signIn(page, "ada", chapterUrl("you", await demoWorkspace("Your title (synthetic)")));
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
  await expect(page.locator(".world-label[data-kind='skill']")).toHaveCount(0);
  expect(externalRequests(requests)).toEqual([]);
});

test("[DIV1-13][DIV1-03][WLD-01] a title neither list holds is kept in the person's own words, and the world still answers", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const requests = recordRequests(page);
  await signIn(page, "ada", chapterUrl("you", await demoWorkspace("Own words (synthetic)")));

  // Acceptance 3: ESCO's closest titles are asked about, and "None of these is my job" keeps
  // the words as typed.
  await field(page).fill("Bookkeeping assistant");
  await expect(
    page.getByText("Careerwright couldn't match that title in ESCO. Is it one of these?"),
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
  await expect(page.locator(".world-label[data-kind='skill']")).toHaveCount(0);
  await youView(page, "What we know");
  await expect(
    page.getByRole("tabpanel", { name: "What we know" }).getByText("Bookkeeping assistant", {
      exact: true,
    }),
  ).toBeVisible();
  expect(externalRequests(requests)).toEqual([]);
});
