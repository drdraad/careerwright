// Fictional topology for interaction review, separate from P01 and solver output.
import type { JourneyTarget } from "@/components/RouteExplorer";
import type { RouteDetail, RouteStep } from "@/generated/api";

function step(
  id: string,
  title: string,
  kind: "learning" | "work",
  start: string,
  finish: string,
  usable: string,
  prerequisites: string[] = [],
): RouteStep {
  return {
    variant_id: id,
    concept_id: id,
    offering_id: id,
    kind,
    title,
    provider: null,
    start_date: null,
    finish_date: null,
    start_month: start,
    finish_month: finish,
    usable_month: usable,
    active_months: [],
    weekly_hours: null,
    payments: [],
    recurring: null,
    supports: [],
    fee_loan: null,
    work_pattern: null,
    wage: null,
    offer: kind === "work" ? { role_class: title, accepted: false } : null,
    application_deadline: null,
    prerequisites,
    grants: [`completion:${id}`],
    records: [],
    as_of: null,
    supplied: [],
    added_by_person: false,
    synthetic: true,
    qualified_by: ["synthetic"],
    sources: [
      {
        basis: "fixture",
        locator: "Fictional expansion example",
        excerpt: "Illustrative role and sequence only. No vacancy, provider or offer is confirmed.",
      },
    ],
  };
}

function route(index: number, steps: RouteStep[]): RouteDetail {
  const conditions = steps
    .filter((item) => item.kind === "work")
    .map((item) => ({
      kind: "offer" as const,
      variant_id: item.variant_id,
      instrument_id: null,
      verification: "confirm_offer_accepted" as const,
    }));
  return {
    schedule: {
      index,
      route: steps.map((item) => item.variant_id),
      family_id: `fictional:${index}`,
      point_id: index,
      verdict: "unresolved",
      months_to_readiness: 0,
      readiness_month: "2028-03",
      objective_cost: { minor_units: 0, currency: "GBP" },
      direct_cost: { minor_units: 0, currency: "GBP" },
      economic_cost: null,
      qualifications: ["synthetic", "conditional_offer", "readiness_not_assessed"],
      conditions,
      preferences: [],
      loans_to_repay: [],
      layer: null,
      view_layer: null,
    },
    label: { name: "Fictional structure example", dated: "2026-11-04", synthetic: true },
    basis: {
      objective_basis: "direct_spending",
      planning_start: "2026-11",
      horizon_months: 24,
      currency: "GBP",
      scenario: "base",
      baseline: null,
      synthetic: true,
    },
    costs: {
      objective_basis: "direct_spending",
      direct_cost: null,
      pay_difference: null,
      economic_cost: null,
      peak_monthly_payment: null,
      minimum_prefunded_cash: null,
      reserve: null,
      loans_to_repay: [],
    },
    months: [],
    beyond_horizon: [],
    unscheduled: [],
    before_start: [],
    debts: [],
    steps,
    gates: conditions.map((condition) => ({
      ...condition,
      month: steps.find((item) => item.variant_id === condition.variant_id)?.start_month ?? null,
    })),
    waits: [],
    milestones: [],
    scenarios: [],
    self_paid: null,
  };
}

const foundations = step(
  "data-foundations",
  "Data foundations",
  "learning",
  "2027-01",
  "2027-02",
  "2027-03",
);
const dataAssistant = step(
  "data-assistant",
  "Data assistant",
  "work",
  "2027-03",
  "2027-06",
  "2027-07",
  foundations.grants,
);
const reportingAssistant = step(
  "reporting-assistant",
  "Reporting assistant",
  "work",
  "2027-07",
  "2027-10",
  "2027-11",
  dataAssistant.grants,
);
const sql = step(
  "applied-sql",
  "Applied SQL",
  "learning",
  "2027-03",
  "2027-06",
  "2027-07",
  foundations.grants,
);
const dataTechnician = step(
  "data-technician",
  "Data technician",
  "work",
  "2027-03",
  "2027-08",
  "2027-09",
  foundations.grants,
);
const reportingAnalyst = step(
  "reporting-analyst",
  "Reporting analyst",
  "work",
  "2027-09",
  "2028-02",
  "2028-03",
  [...dataTechnician.grants, ...sql.grants],
);
const dashboards = step(
  "dashboards",
  "Building dashboards",
  "learning",
  "2027-07",
  "2027-08",
  "2027-09",
  dataAssistant.grants,
);
const insightsAssistant = step(
  "insights-assistant",
  "Insights assistant",
  "work",
  "2027-09",
  "2028-02",
  "2028-03",
  dashboards.grants,
);
const projectBasics = step(
  "project-foundations",
  "Project foundations",
  "learning",
  "2027-01",
  "2027-02",
  "2027-03",
);
const teamAdmin = step(
  "team-administrator",
  "Team administrator",
  "work",
  "2027-03",
  "2027-06",
  "2027-07",
  projectBasics.grants,
);
const projectAssistant = step(
  "project-assistant",
  "Project assistant",
  "work",
  "2027-07",
  "2028-02",
  "2028-03",
  teamAdmin.grants,
);
const operationsAssistant = step(
  "operations-assistant",
  "Operations assistant",
  "work",
  "2027-03",
  "2027-08",
  "2027-09",
  projectBasics.grants,
);
const deliveryAssistant = step(
  "delivery-assistant",
  "Delivery assistant",
  "work",
  "2027-09",
  "2028-02",
  "2028-03",
  operationsAssistant.grants,
);

export const expansionTargets: JourneyTarget[] = [
  {
    id: "data-quality",
    title: "Data quality analyst",
    routes: [
      route(0, [foundations, dataAssistant, reportingAssistant]),
      route(1, [foundations, sql, dataTechnician, reportingAnalyst]),
    ],
  },
  {
    id: "business-intelligence",
    title: "Business intelligence analyst",
    routes: [
      route(0, [foundations, dataAssistant, dashboards, insightsAssistant]),
      route(1, [foundations, sql, dataTechnician, reportingAnalyst]),
    ],
  },
  {
    id: "project-coordination",
    title: "Project coordinator",
    routes: [
      route(0, [projectBasics, teamAdmin, projectAssistant]),
      route(1, [projectBasics, operationsAssistant, deliveryAssistant]),
    ],
  },
];
