// Fictional planning states for component tests and Storybook, never solver output.
import type { JourneyTarget } from "@/components/RouteExplorer";
import type { RouteDetail } from "@/generated/api";
import { routeDetailFixture } from "./routeDetailData";
import { expansionTargets } from "./routeExpansionData";

const fee = { minor_units: 12000, currency: "GBP" as const };
const course = routeDetailFixture.steps[0];
if (!course) throw new Error("Missing fictional course fixture");

export const completePlanningRoute: RouteDetail = {
  ...routeDetailFixture,
  label: { name: "Fictional planning state example", dated: "2026-11-04", synthetic: true },
  schedule: {
    ...routeDetailFixture.schedule,
    index: 0,
    route: ["fictional-course"],
    family_id: "fictional-course",
    point_id: 0,
    verdict: "affordable_and_feasible_with_qualifications",
    months_to_readiness: 2,
    readiness_month: "2027-03",
    objective_cost: fee,
    direct_cost: fee,
    qualifications: ["synthetic", "provisional_matrix", "conditional_application"],
    conditions: [
      {
        kind: "application",
        variant_id: "fictional-course",
        instrument_id: null,
        verification: "confirm_admission",
      },
    ],
    loans_to_repay: [],
  },
  basis: {
    objective_basis: "direct_spending",
    planning_start: "2027-01",
    horizon_months: 24,
    currency: "GBP",
    scenario: "base",
    baseline: null,
    synthetic: true,
  },
  costs: {
    objective_basis: "direct_spending",
    direct_cost: fee,
    economic_cost: null,
    pay_difference: null,
    peak_monthly_payment: fee,
    minimum_prefunded_cash: null,
    reserve: null,
    loans_to_repay: [],
  },
  months: [],
  beyond_horizon: [],
  unscheduled: [],
  before_start: [],
  debts: [],
  steps: [
    {
      ...course,
      variant_id: "fictional-course",
      concept_id: "fictional-course",
      offering_id: "fictional-course",
      title: "Reporting practice",
      provider: "Fictional Learning Centre",
      start_date: "2027-01-04",
      finish_date: "2027-02-26",
      start_month: "2027-01",
      finish_month: "2027-02",
      usable_month: "2027-03",
      active_months: ["2027-01", "2027-02"],
      weekly_hours: 6,
      payments: [{ kind: "fee", amount: fee, due: "2027-01-04", month: "2027-01" }],
      fee_loan: null,
      prerequisites: [],
      grants: [],
      records: [{ record: "offering", record_id: "fictional-course", review_state: "proposed" }],
      as_of: "2026-11-04",
      supplied: [],
      added_by_person: false,
      qualified_by: ["synthetic", "proposed_record"],
      sources: [
        {
          basis: "fixture",
          locator: "Fictional planning state example",
          excerpt:
            "Illustrative dates, hours and fee only. No provider, place or availability has been verified.",
        },
      ],
    },
  ],
  gates: [
    {
      kind: "application",
      variant_id: "fictional-course",
      instrument_id: null,
      verification: "confirm_admission",
      month: "2027-01",
    },
  ],
  waits: [],
  milestones: [{ kind: "readiness", month: "2027-03", months_to_readiness: 2 }],
  scenarios: [],
  self_paid: null,
};

export const planningStateTargets: JourneyTarget[] = [
  {
    id: "unsupported",
    title: "Fictional regulated role",
    routes: [],
    scheduleCount: 0,
    status: "unsupported",
  },
  {
    id: "partial",
    title: "Fictional data role",
    routes: expansionTargets[0]?.routes ?? [],
    status: "available",
  },
  {
    id: "complete",
    title: "Fictional reporting role",
    routes: [completePlanningRoute],
    status: "available",
  },
];
