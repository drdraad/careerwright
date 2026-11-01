// Asserts that every fixture value the compositions use (compositions/data.js, FIXTURES)
// equals the fixture files under fixtures/. Exits 1 on the first mismatch.
//   pnpm --dir docs/design run check-data
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { runInNewContext } from "node:vm";
import { deepStrictEqual, strictEqual } from "node:assert/strict";

const designRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = join(designRoot, "..", "..");
const json = (path) => JSON.parse(readFileSync(join(repoRoot, path), "utf8"));

const sandbox = { window: {} };
runInNewContext(readFileSync(join(designRoot, "compositions/data.js"), "utf8"), sandbox);
// Round-trip through JSON: arrays built inside the vm context have another realm's
// prototype, which deepStrictEqual treats as unequal.
const f = JSON.parse(JSON.stringify(sandbox.window.CAREERWRIGHT.FIXTURES));

const trace = json("fixtures/m0/worked_trace.json");
const p01 = json("fixtures/m0/personas/P01.json");
const p02 = json("fixtures/m0/personas/P02.json");
const directai = json("fixtures/reconstructed/directai.json");
let checks = 0;
const eq = (actual, expected, what) => {
  deepStrictEqual(actual, expected, what);
  checks += 1;
};

const t = f.trace01;
eq(t.id, trace.id, "trace id");
eq(t.targetTitle, trace.target.title, "target title");
eq(t.region, trace.expected.print_snapshot.region, "region");
eq(t.planningStart, trace.planning_start, "planning start");
eq(t.horizonMonths, trace.comparison_horizon_months, "horizon");
eq(t.baselineIncomeByMonthMinor, trace.baseline_income_by_month_minor, "baseline income");
eq(t.livingByMonthMinor, trace.living_outgoings_by_month_minor, "living costs");
eq(t.openingCashMinor, trace.opening_cash_minor, "opening cash");
eq(t.reserveMinor, trace.minimum_reserve_minor, "reserve");
eq(t.admissionCompletedOn, trace.application_gates.completed_on, "admission date");
eq(t.fronts, trace.expected.fronts, "fronts");
eq(t.selectedRoute, trace.expected.selected_route, "selected route");
eq(t.availableWeeklyHours, trace.available_weekly_hours_envelope, "weekly hours");
eq(t.syllabusText, trace.syllabus_text, "syllabus text");
eq(t.aiScore, {
  range: trace.expected.score_record.range,
  minimumFilter: trace.expected.score_record.minimum_filter,
  lowerBoundFilterPasses: trace.expected.score_record.lower_bound_filter_passes,
  synthetic: trace.expected.score_record.synthetic,
}, "AI score record");
const snap = trace.expected.print_snapshot;
eq(t.print, {
  timeMonths: snap.time_months,
  directMinor: snap.direct_spend_minor,
  economicMinor: snap.economic_cost_minor,
  peakPaymentMinor: snap.peak_monthly_payment_minor,
  minimumPrefundedCashMinor: snap.minimum_prefunded_cash_minor,
  horizonMonths: snap.comparison_horizon_months,
}, "print snapshot");
strictEqual(t.routes.length, trace.routes.length, "route count");
for (const route of t.routes) {
  const source = trace.routes.find((r) => r.id === route.id);
  const action = trace.catalogue.actions.find((a) => a.id === source.action_ids[0]);
  eq([route.timeMonths, route.directMinor, route.economicMinor], [source.time_months, source.direct_spend_minor, source.economic_cost_minor], `route ${route.id} objectives`);
  eq(route.familyId, source.family_id, `route ${route.id} family`);
  eq(route.paymentsMinor, source.payments_by_month_minor, `route ${route.id} payments`);
  eq(route.incomeMinor, source.income_by_month_minor, `route ${route.id} income`);
  eq([route.start, route.finish], [source.actual_start_date, source.actual_finish_date], `route ${route.id} dates`);
  eq([route.studyHours, route.workHoursWhileActive], [action.weekly_study_envelope, action.weekly_work_envelope_while_active], `route ${route.id} workload`);
  eq(t.weeklyWorkAfterCompletion, action.weekly_work_after_completion, `route ${route.id} work after completion`);
}

eq(f.p01.cities, p01.cities, "P01 cities");
eq(f.p01.targetTitles, p01.target_titles, "P01 targets");
eq(f.p01.enjoyedTasks, p01.personality_optional.enjoyed_tasks, "P01 enjoyed tasks");
eq(f.p01.preferredEnvironment, p01.personality_optional.preferred_environment, "P01 environment");
eq([f.p01.currentNetIncomeMinor, f.p01.livingMinor, f.p01.openingCashMinor, f.p01.reserveMinor],
  [p01.current_net_income_minor, p01.living_outgoings_minor, p01.opening_cash_minor, p01.reserve_minor], "P01 money");
eq([f.p01.directSpendCapMinor, f.p01.monthlyPaymentCapMinor, f.p01.weeklyTotalAvailabilityHours],
  [p01.direct_spend_cap_minor, p01.monthly_payment_cap_minor, p01.weekly_total_availability_hours], "P01 caps and hours");

eq(f.p02.cities, p02.cities, "P02 cities");
eq(f.p02.enjoyedTasks, p02.personality_optional.enjoyed_tasks, "P02 enjoyed tasks");
eq(f.p02.preferredEnvironment, p02.personality_optional.preferred_environment, "P02 environment");
eq(f.p02.incomeBaselineStatus, p02.income_baseline_status, "P02 baseline status");
eq(f.p02.weeklyStudyHours, p02.weekly_study_hours, "P02 study hours");

eq(f.directai.id, directai.id, "DIRECTAI id");
eq(f.directai.routes, directai.routes.map((r) => ({ id: r.label, timeMonths: r.time_months, directMinor: r.direct_spend_minor, layer: r.expected_layer })), "DIRECTAI routes");

console.log(`fixture data check passed: ${checks} assertions against fixtures/m0 and fixtures/reconstructed`);
