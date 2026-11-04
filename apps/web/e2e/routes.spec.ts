import { readFile } from "node:fs/promises";
import { expect, type Locator, type Page, test } from "@playwright/test";
import type { NeededInput } from "../src/generated/api";
import { MISSING_FACT, NEEDED_INPUT } from "../src/lib/optionWords";
import { asBrowser, emulatorToken } from "./api";
import { chapterUrl, signIn } from "./helpers";
import { FIXTURE_WORKSPACE, stack } from "./stack";

const BASE = `/v1/workspaces/${FIXTURE_WORKSPACE}`;
const OFFERING = "offering:C01#full_time";
const TARGET = "Data quality analyst";

type Need = { input: NeededInput };
type Option = {
  variant_id: string;
  concept_id: string;
  missing: string[];
  eligibility_conditions: { field: string; status: string | null }[];
};
type Checkpoint = {
  needs: Need[];
  targets: { target_title: string; options: Option[] }[];
};

async function checkpoint(token: string): Promise<Checkpoint> {
  return asBrowser("GET", `${BASE}/planning/checkpoint`, token);
}

async function answerPlanningNeed(form: Locator, input: string) {
  switch (input) {
    case "objective_basis":
      await form.getByLabel("Choose one").selectOption("economic");
      break;
    case "baseline":
      await form.getByLabel("Choose one").selectOption("current_role");
      await form.getByLabel("Pounds").fill("2000");
      break;
    case "continuation":
      await form.getByLabel("Hours a week you work now").fill("30");
      await form.getByLabel("Pounds").fill("2000");
      break;
    case "opening_cash":
      await form.getByLabel("Pounds").fill("6000");
      break;
    case "living_costs":
      await form.getByLabel("Pounds").fill("1000");
      break;
    case "reserve":
      await form.getByLabel("Pounds").fill("500");
      break;
    case "weekly_availability":
      await form.getByLabel("Hours a week").fill("40");
      break;
    case "scenario_delay_months":
      await form.getByLabel("Months late to plan for").fill("2");
      break;
    case "work_rights":
      await form.getByLabel("Choose one").selectOption("held");
      break;
    case "commitments":
    case "existing_debts":
      await form.getByLabel("I have none").check();
      break;
    default:
      throw new Error(`The test needs a value for ${input}`);
  }
  await form.getByRole("button", { name: "Save this answer" }).click();
}

function optionIn(data: Checkpoint): Option {
  const option = data.targets
    .find((target) => target.target_title === TARGET)
    ?.options.find((item) => item.variant_id === OFFERING);
  if (!option) throw new Error("The seeded P01 option is missing");
  return option;
}

async function giveOptionFacts(page: Page, token: string) {
  const data = await checkpoint(token);
  const target = data.targets.find((item) => item.target_title === TARGET);
  if (!target) throw new Error("The seeded P01 target is missing");
  const index = target.options.findIndex((item) => item.variant_id === OFFERING);
  if (index < 0) throw new Error("The seeded P01 offering is missing");
  await page.locator(".option-grid button").nth(index).click();
  const detail = page.locator(".option-detail");
  const start = new Date();
  start.setUTCDate(1);
  start.setUTCMonth(start.getUTCMonth() + 1);
  const nextMonth = start.toISOString().slice(0, 10);

  for (const [fact, value] of [
    ["start_date", nextMonth],
    ["weekly_hours", "9"],
    ["cost", "0"],
  ] as const) {
    await expect
      .poll(async () => optionIn(await checkpoint(token)).missing.includes(fact))
      .toBe(true);
    const box = detail.locator("form.figure-box:visible");
    await expect(box).toContainText(MISSING_FACT[fact].ask);
    if (fact === "start_date") {
      const ownDay = box.getByLabel(/Another day/);
      if (await ownDay.count()) await ownDay.check();
      await box.locator('input[type="date"]').fill(value);
    } else {
      await box.locator("input.figure-input").fill(value);
    }
    const save = box.getByRole("button", { name: "Save" });
    await expect(save).not.toHaveAttribute("aria-disabled", "true");
    await save.click();
    await expect
      .poll(async () => optionIn(await checkpoint(token)).missing.includes(fact))
      .toBe(false);
  }

  for (let remaining = 4; remaining > 0; remaining -= 1) {
    const before = optionIn(await checkpoint(token)).eligibility_conditions.filter(
      (condition) => condition.status !== "confirmed",
    ).length;
    if (before === 0) break;
    const form = detail.locator("form");
    await form.getByRole("combobox").selectOption("confirmed");
    await form.getByRole("button", { name: "Save this answer" }).click();
    await expect
      .poll(
        async () =>
          optionIn(await checkpoint(token)).eligibility_conditions.filter(
            (condition) => condition.status !== "confirmed",
          ).length,
      )
      .toBe(before - 1);
    if (before > 1) await expect(detail.getByRole("combobox")).toHaveValue("");
    else await expect(detail.getByRole("combobox")).toHaveCount(0);
  }
}

test.beforeEach(() => {
  stack("reset-demo");
});

test("[OPTN-13][VIS2-08][PLAN-01][STATE-06] P01 computes a route, saves a plan and reviews progress", async ({
  page,
}) => {
  test.setTimeout(300_000);
  const token = await emulatorToken("ada");
  // The seeded profile has no skills examples; this synthetic setup makes its required rows
  // ready so the journey can exercise the planning checkpoint and route search.
  const matrices = await asBrowser<{
    matrices: {
      target_title: string;
      rows: {
        required: boolean;
        subject: string;
        rubric: { version_id: string };
        required_level: string;
      }[];
    }[];
  }>("GET", `${BASE}/capability/matrices`, token);
  const matrix = matrices.matrices.find((item) => item.target_title === TARGET);
  if (!matrix) throw new Error("The seeded P01 skills matrix is missing");
  for (const [version, row] of matrix.rows.filter((item) => item.required).entries()) {
    await asBrowser("POST", `${BASE}/capability/evidence`, token, {
      expected_version: version,
      subject: row.subject,
      rubric_version: row.rubric.version_id,
      answer: "done_independently",
      self_assessed_level: row.required_level,
      example: "Synthetic: checked a data import and corrected its errors",
      last_done: "2026-08",
      context: "paid_work",
      independence: "independent",
    });
  }

  await signIn(page, "ada", chapterUrl("options"));
  const chapters = page.getByRole("navigation", { name: "Chapters" });
  await expect(chapters.getByRole("link", { name: "Options, available" })).toBeVisible();
  await expect(chapters.getByRole("link", { name: /Routes/ })).toHaveCount(0);
  await page.getByRole("button", { name: /Before a route search/ }).click();
  const review = page.getByRole("region", { name: "Review before a route search" });
  await expect(review.getByText(/Careerwright still needs/)).toBeVisible();
  for (let step = 0; step < 12; step += 1) {
    const need = (await checkpoint(token)).needs.find(
      (item) => item.input !== "direct_spend_cap" && item.input !== "monthly_payment_cap",
    );
    if (!need) break;
    await expect(review.locator("form h3")).toHaveText(NEEDED_INPUT[need.input].name);
    await answerPlanningNeed(review.locator("form"), need.input);
    await expect
      .poll(async () => (await checkpoint(token)).needs.some((item) => item.input === need.input))
      .toBe(false);
  }
  await expect(
    review.getByText("Careerwright has the answers it needs to try a route search."),
  ).toBeVisible();

  await page.getByRole("button", { name: "Explore options" }).click();
  await giveOptionFacts(page, token);
  const selectedOption = page.locator(".option-detail");
  await expect(
    selectedOption.getByText(
      /Careerwright used start date, weekly hours, cost from your own figure, not checked/,
    ),
  ).toBeVisible();
  await expect(selectedOption.getByText("9 (your own figure, not checked)")).toBeVisible();
  await expect(selectedOption.getByText(/£0 course fee/)).toBeVisible();
  await expect(chapters.getByRole("link", { name: "Options, ready for routes" })).toBeVisible();
  await expect(chapters.getByRole("link", { name: "Routes, available" })).toBeVisible();
  await page.goto(chapterUrl("routes"));
  await expect(page.getByRole("heading", { level: 1, name: "Routes" })).toBeVisible();
  await page.getByRole("button", { name: "Find routes" }).click();
  await expect(page.getByRole("heading", { name: "Best trade-offs found" })).toBeVisible({
    timeout: 90_000,
  });
  await expect(chapters.getByRole("link", { name: "Routes, route found" })).toBeVisible();
  await expect(chapters.getByRole("link", { name: /Plan/ })).toHaveCount(0);
  const qualified = page
    .getByRole("button", {
      name: /Uses a figure you supplied that has not been checked/,
    })
    .first();
  await expect(qualified).toBeVisible();
  const title = (await qualified.locator(".font-semibold").textContent()) ?? "";
  const figures = (await qualified.locator(".tnum").textContent()) ?? "";
  const route = /Route (\d+)/.exec(title)?.[1];
  const months = /(\d+) months to/.exec(figures)?.[1];
  const rank = /in (F[123])/.exec(figures)?.[1];
  if (!route || !months || !rank) throw new Error(`Unrecognised route card: ${title} ${figures}`);
  await qualified.click();
  await expect(page.getByRole("heading", { name: `Route ${route}` })).toBeVisible();
  await expect(
    page.getByText(/Uses a figure you supplied that has not been checked/).last(),
  ).toBeVisible();
  await page.getByText("Filter this view").click();
  const filtered = page.waitForResponse(
    (response) =>
      response.url().includes(`/schedules?`) && response.url().includes(`max_months=${months}`),
  );
  await page.getByRole("spinbutton", { name: "Exact maximum months" }).fill(months);
  await filtered;
  await expect(
    page.getByRole("button", { name: new RegExp(`Route ${route}.*in ${rank}`) }),
  ).toBeVisible();
  await expect(page.getByText(/Recorded ranks do not change when you filter/)).toBeVisible();

  await page.getByRole("link", { name: "Choose this route in Plan" }).click();
  await expect(page).toHaveURL(
    new RegExp(`/plan\\?solve_run_id=.+&schedule_index=${Number(route) - 1}$`),
  );
  await expect(chapters.getByRole("link", { name: "Plan, available" })).toBeVisible();
  const candidate = page.getByRole("region", { name: "Route to choose" });
  await expect(
    candidate.getByRole("heading", { name: "Review this route before choosing it" }),
  ).toBeVisible();
  await expect(
    candidate.getByText(/Uses a figure you supplied that has not been checked/),
  ).toBeVisible();
  const save = candidate.getByRole("button", { name: "Save this plan" });
  await expect(save).toBeDisabled();
  await candidate.getByRole("checkbox", { name: /I have reviewed this route/ }).check();
  await save.click();

  const overview = page.getByRole("region", { name: "Chosen plan overview" });
  await expect(overview.getByRole("heading", { name: TARGET })).toBeVisible();
  await expect(overview.getByText(/^Next action:/)).toBeVisible();
  await expect(overview.getByText(/Plan version 1/)).toBeVisible();
  await expect(chapters.getByRole("link", { name: "Plan, plan saved" })).toBeVisible();
  const snapshot = await asBrowser<{
    version: number;
    route: { schedule: { index: number }; steps: { variant_id: string }[] };
  }>("GET", `${BASE}/planning/plans/current`, token);
  expect(snapshot.version).toBe(1);
  expect(snapshot.route.schedule.index).toBe(Number(route) - 1);

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download plan JSON" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("careerwright-plan-v1.json");
  const exported = JSON.parse(await readFile(await download.path(), "utf8")) as {
    version: number;
    route: { schedule: { index: number } };
    selected_by?: string;
  };
  expect(exported.version).toBe(snapshot.version);
  expect(exported.route.schedule.index).toBe(snapshot.route.schedule.index);
  expect(exported).not.toHaveProperty("selected_by");

  // A plan must be usable on a later visit, without the route-selection URL or its in-memory state.
  await page.goto(chapterUrl("plan"));
  await expect(page.getByRole("region", { name: "Chosen plan overview" })).toContainText(
    "Plan version 1",
  );
  await expect(page.getByRole("region", { name: "Chosen plan overview" })).toContainText(TARGET);

  await page
    .getByRole("checkbox", { name: "Leave financial detail out of the plan JSON and print" })
    .check();
  await page.emulateMedia({ media: "print" });
  const printCopy = page.getByRole("region", { name: "Plan copy with omitted details" });
  await expect(printCopy).toBeVisible();
  await expect(printCopy).toContainText("Next action:");
  await expect(printCopy).not.toContainText("£");
  await expect(printCopy).not.toContainText("What you supplied");
  await expect(overview).toBeHidden();
  const pdf = await page.pdf();
  expect(pdf.subarray(0, 5).toString()).toBe("%PDF-");
  await page.emulateMedia({ media: "screen" });

  const firstStep = snapshot.route.steps[0];
  if (!firstStep) throw new Error("The chosen route has no step to report complete");
  const progress = page.getByRole("region", { name: "Planning progress" });
  await progress.getByRole("button", { name: "Report step complete" }).first().click();
  await expect(overview.getByText(/Plan version 2/)).toBeVisible();
  const updated = await asBrowser<{
    version: number;
    progress: { completed_steps: string[] };
  }>("GET", `${BASE}/planning/plans/current`, token);
  expect(updated.version).toBe(2);
  expect(updated.progress.completed_steps).toContain(firstStep.variant_id);

  await page.goto(chapterUrl("routes"));
  await page
    .getByRole("button", { name: /Uses a figure you supplied that has not been checked/ })
    .first()
    .click();
  await page.getByRole("link", { name: "Choose this route in Plan" }).click();
  await expect(candidate.getByRole("region", { name: "Proposed plan changes" })).toBeVisible();
  await expect(
    candidate.getByText(/fresh full horizon; it has not subtracted completed work/),
  ).toBeVisible();
  await candidate.getByRole("checkbox", { name: /I have reviewed this route/ }).check();
  await expect(save).toBeDisabled();
  await candidate
    .getByRole("checkbox", { name: /I understand this is a fresh full-horizon comparison/ })
    .check();
  await expect(save).toBeEnabled();
  await save.click();
  await expect(overview.getByText(/Plan version 3/)).toBeVisible();
  const revised = await asBrowser<{
    version: number;
    route: { schedule: { index: number } };
  }>("GET", `${BASE}/planning/plans/current`, token);
  expect(revised.version).toBe(3);
  expect(revised.route.schedule.index).toBe(Number(route) - 1);
  await page.reload();
  await expect(overview.getByText(/Plan version 3/)).toBeVisible();
  await progress.getByRole("button", { name: "Record my commitment" }).first().click();
  await expect(overview.getByText(/Plan version 4/)).toBeVisible();
  await page.reload();
  await progress.getByRole("button", { name: "Correct commitment report" }).first().click();
  await expect(overview.getByText(/Plan version 5/)).toBeVisible();
  const corrected = await asBrowser<{
    commitments: string[];
    progress: { activity: { kind: string }[] };
  }>("GET", `${BASE}/planning/plans/current`, token);
  expect(corrected.commitments).toEqual([]);
  expect(corrected.progress.activity.map((item) => item.kind)).toContain("commitment_accepted");
  expect(corrected.progress.activity.map((item) => item.kind)).toContain("commitment_retracted");
});
