// Saved P01 synthetic scenario responses; provider facts and planning assumptions retain their source labels.
import type {
  CheckpointOut,
  PlanSnapshot,
  ProfileOut,
  RouteDetail,
  SkillsOut,
} from "@/generated/api";

export const p01Routes: RouteDetail[] = [
  {
    schedule: {
      index: 0,
      route: ["offering:C01#full_time"],
      family_id: "family:08b9a229c2a4da3d",
      point_id: 0,
      months_to_readiness: 4,
      readiness_month: "2027-03",
      objective_cost: {
        minor_units: 180000,
        currency: "GBP",
      },
      direct_cost: {
        minor_units: 0,
        currency: "GBP",
      },
      economic_cost: {
        minor_units: 180000,
        currency: "GBP",
      },
      verdict: "affordable_and_feasible_with_qualifications",
      qualifications: [
        "proposed_records",
        "synthetic",
        "supplied_figures",
        "provisional_matrix",
        "proposed_rubrics",
        "self_reported_evidence",
        "planned_outcome_assumption",
        "user_assumption",
      ],
      conditions: [],
      preferences: [],
      loans_to_repay: [],
      layer: 1,
      view_layer: null,
    },
    label: {
      name: "nessa-england-option-pack 0.4.0",
      dated: "2026-11-01",
      synthetic: false,
      research_fingerprint: null,
    },
    basis: {
      objective_basis: "economic",
      planning_start: "2026-11",
      horizon_months: 24,
      currency: "GBP",
      scenario: "base",
      baseline: {
        kind: "current_role",
        net_income_by_month: [
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
        ],
      },
      synthetic: true,
      opening_cash: {
        minor_units: 600000,
        currency: "GBP",
      },
      replan: null,
    },
    costs: {
      objective_basis: "economic",
      direct_cost: {
        minor_units: 0,
        currency: "GBP",
      },
      pay_difference: {
        minor_units: 180000,
        currency: "GBP",
      },
      economic_cost: {
        minor_units: 180000,
        currency: "GBP",
      },
      peak_monthly_payment: {
        minor_units: 0,
        currency: "GBP",
      },
      minimum_prefunded_cash: {
        minor_units: 500000,
        currency: "GBP",
      },
      reserve: {
        minor_units: 50000,
        currency: "GBP",
      },
      loans_to_repay: [],
    },
    months: [
      {
        month: "2026-11",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 600000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 500000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 700000,
          currency: "GBP",
        },
      },
      {
        month: "2026-12",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 140000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 60000,
          currency: "GBP",
        },
        opening: {
          minor_units: 700000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 600000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 140000,
          currency: "GBP",
        },
        closing: {
          minor_units: 740000,
          currency: "GBP",
        },
      },
      {
        month: "2027-01",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 140000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 60000,
          currency: "GBP",
        },
        opening: {
          minor_units: 740000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 640000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 140000,
          currency: "GBP",
        },
        closing: {
          minor_units: 780000,
          currency: "GBP",
        },
      },
      {
        month: "2027-02",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 140000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 60000,
          currency: "GBP",
        },
        opening: {
          minor_units: 780000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 680000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 140000,
          currency: "GBP",
        },
        closing: {
          minor_units: 820000,
          currency: "GBP",
        },
      },
      {
        month: "2027-03",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 820000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 720000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 920000,
          currency: "GBP",
        },
      },
      {
        month: "2027-04",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 920000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 820000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1020000,
          currency: "GBP",
        },
      },
      {
        month: "2027-05",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1020000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 920000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1120000,
          currency: "GBP",
        },
      },
      {
        month: "2027-06",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1120000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1020000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1220000,
          currency: "GBP",
        },
      },
      {
        month: "2027-07",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1220000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1120000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1320000,
          currency: "GBP",
        },
      },
      {
        month: "2027-08",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1320000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1220000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1420000,
          currency: "GBP",
        },
      },
      {
        month: "2027-09",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1420000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1320000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1520000,
          currency: "GBP",
        },
      },
      {
        month: "2027-10",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1520000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1420000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1620000,
          currency: "GBP",
        },
      },
      {
        month: "2027-11",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1620000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1520000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1720000,
          currency: "GBP",
        },
      },
      {
        month: "2027-12",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1720000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1620000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1820000,
          currency: "GBP",
        },
      },
      {
        month: "2028-01",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1820000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1720000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1920000,
          currency: "GBP",
        },
      },
      {
        month: "2028-02",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1920000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1820000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2020000,
          currency: "GBP",
        },
      },
      {
        month: "2028-03",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2020000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1920000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2120000,
          currency: "GBP",
        },
      },
      {
        month: "2028-04",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2120000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2020000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2220000,
          currency: "GBP",
        },
      },
      {
        month: "2028-05",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2220000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2120000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2320000,
          currency: "GBP",
        },
      },
      {
        month: "2028-06",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2320000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2220000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2420000,
          currency: "GBP",
        },
      },
      {
        month: "2028-07",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2420000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2320000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2520000,
          currency: "GBP",
        },
      },
      {
        month: "2028-08",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2520000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2420000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2620000,
          currency: "GBP",
        },
      },
      {
        month: "2028-09",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2620000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2520000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2720000,
          currency: "GBP",
        },
      },
      {
        month: "2028-10",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2720000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2620000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2820000,
          currency: "GBP",
        },
      },
    ],
    beyond_horizon: [],
    unscheduled: [],
    before_start: [],
    debts: [],
    steps: [
      {
        variant_id: "offering:C01#full_time",
        concept_id: "option:C01",
        offering_id: "offering:C01#full_time",
        kind: "learning",
        title: "Certificate in Data",
        provider: "Netcom Training",
        start_date: "2026-12-01",
        finish_date: "2027-02-08",
        start_month: "2026-12",
        finish_month: "2027-02",
        usable_month: "2027-03",
        active_months: ["2026-12", "2027-01", "2027-02"],
        weekly_hours: 18,
        payments: [
          {
            kind: "fee",
            amount: {
              minor_units: 0,
              currency: "GBP",
            },
            month: "2026-12",
            due: null,
          },
        ],
        recurring: null,
        supports: [],
        fee_loan: null,
        work_pattern: {
          kind: "reduced_hours",
          hours_per_week: 20,
          net_income: {
            minor_units: 140000,
            currency: "GBP",
          },
        },
        wage: null,
        offer: null,
        application_deadline: null,
        prerequisites: [],
        grants: [],
        records: [
          {
            record: "concept",
            record_id: "option:C01",
            review_state: "proposed",
          },
          {
            record: "offering",
            record_id: "offering:C01#full_time",
            review_state: "proposed",
          },
        ],
        as_of: "2026-10-29",
        supplied: ["start_date", "weekly_hours", "cost"],
        added_by_person: false,
        synthetic: false,
        qualified_by: ["proposed_record", "supplied_figures"],
        sources: [
          {
            basis: "source",
            claim_id: "C01.title",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 2368-2387",
            excerpt: "Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.credential",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 58911-58943",
            excerpt: "NCFE Level 3 Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.level",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 58911-58943",
            excerpt: "NCFE Level 3 Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.awarding_body",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 58911-58943",
            excerpt: "NCFE Level 3 Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.delivery_mode",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 56502-56522",
            excerpt: "100% online learning",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.assessment",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 60061-60084",
            excerpt: "Learn, certify, succeed",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.stated_hours",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 57939-57948",
            excerpt: "195 hours",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.duration",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 55850-55888",
            excerpt: "10 weeks full-time, 17 weeks part-time",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.funding_route",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 59794-59835",
            excerpt: "Adult Skills Fund / Free Courses for Jobs",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_area",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 62203-62254",
            excerpt: "You live in the West Midlands or Greater Manchester",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_age",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 62482-62510",
            excerpt: "You&#8217;re aged 19 or over",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_earnings",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 62738-62826",
            excerpt:
              "You earn below the gross annual wage cap of £34,194 (West Midlands)/£32,400 (Manchester)",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_no_other_funded_training",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 63054-63129",
            excerpt: "You&#8217;re not currently undertaking any other government-funded training",
            retrieved_on: "2026-10-29",
          },
        ],
      },
    ],
    gates: [],
    waits: [
      {
        first_month: "2026-11",
        last_month: "2026-11",
        months: 1,
      },
    ],
    milestones: [
      {
        kind: "readiness",
        month: "2027-03",
        months_to_readiness: 4,
      },
      {
        kind: "verify_assessed_completion",
        month: "2027-03",
        months_to_readiness: 4,
      },
    ],
    scenarios: [
      {
        scenario: "delay",
        feasibility: "feasible",
        verdict: "affordable_and_feasible_with_qualifications",
        months_to_readiness: 4,
        readiness_month: "2027-03",
        objective_cost: {
          minor_units: 180000,
          currency: "GBP",
        },
        direct_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        economic_cost: {
          minor_units: 180000,
          currency: "GBP",
        },
        findings: [],
        same_as_base: true,
      },
      {
        scenario: "no_award",
        feasibility: "feasible",
        verdict: "affordable_and_feasible_with_qualifications",
        months_to_readiness: 4,
        readiness_month: "2027-03",
        objective_cost: {
          minor_units: 180000,
          currency: "GBP",
        },
        direct_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        economic_cost: {
          minor_units: 180000,
          currency: "GBP",
        },
        findings: [],
        same_as_base: true,
      },
      {
        scenario: "no_offer",
        feasibility: "feasible",
        verdict: "affordable_and_feasible_with_qualifications",
        months_to_readiness: 4,
        readiness_month: "2027-03",
        objective_cost: {
          minor_units: 180000,
          currency: "GBP",
        },
        direct_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        economic_cost: {
          minor_units: 180000,
          currency: "GBP",
        },
        findings: [],
        same_as_base: true,
      },
    ],
    self_paid: null,
  },
  {
    schedule: {
      index: 1,
      route: ["offering:C01#part_time"],
      family_id: "family:6683f795d1c8bc3d",
      point_id: 1,
      months_to_readiness: 5,
      readiness_month: "2027-04",
      objective_cost: {
        minor_units: 0,
        currency: "GBP",
      },
      direct_cost: {
        minor_units: 0,
        currency: "GBP",
      },
      economic_cost: {
        minor_units: 0,
        currency: "GBP",
      },
      verdict: "affordable_and_feasible_with_qualifications",
      qualifications: [
        "proposed_records",
        "synthetic",
        "supplied_figures",
        "provisional_matrix",
        "proposed_rubrics",
        "self_reported_evidence",
        "planned_outcome_assumption",
        "user_assumption",
      ],
      conditions: [],
      preferences: [],
      loans_to_repay: [],
      layer: 1,
      view_layer: null,
    },
    label: {
      name: "nessa-england-option-pack 0.4.0",
      dated: "2026-11-01",
      synthetic: false,
      research_fingerprint: null,
    },
    basis: {
      objective_basis: "economic",
      planning_start: "2026-11",
      horizon_months: 24,
      currency: "GBP",
      scenario: "base",
      baseline: {
        kind: "current_role",
        net_income_by_month: [
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
          {
            minor_units: 200000,
            currency: "GBP",
          },
        ],
      },
      synthetic: true,
      opening_cash: {
        minor_units: 600000,
        currency: "GBP",
      },
      replan: null,
    },
    costs: {
      objective_basis: "economic",
      direct_cost: {
        minor_units: 0,
        currency: "GBP",
      },
      pay_difference: {
        minor_units: 0,
        currency: "GBP",
      },
      economic_cost: {
        minor_units: 0,
        currency: "GBP",
      },
      peak_monthly_payment: {
        minor_units: 0,
        currency: "GBP",
      },
      minimum_prefunded_cash: {
        minor_units: 500000,
        currency: "GBP",
      },
      reserve: {
        minor_units: 50000,
        currency: "GBP",
      },
      loans_to_repay: [],
    },
    months: [
      {
        month: "2026-11",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 600000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 500000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 700000,
          currency: "GBP",
        },
      },
      {
        month: "2026-12",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 700000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 600000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 800000,
          currency: "GBP",
        },
      },
      {
        month: "2027-01",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 800000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 700000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 900000,
          currency: "GBP",
        },
      },
      {
        month: "2027-02",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 900000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 800000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1000000,
          currency: "GBP",
        },
      },
      {
        month: "2027-03",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1000000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 900000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1100000,
          currency: "GBP",
        },
      },
      {
        month: "2027-04",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1100000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1000000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1200000,
          currency: "GBP",
        },
      },
      {
        month: "2027-05",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1200000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1100000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1300000,
          currency: "GBP",
        },
      },
      {
        month: "2027-06",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1300000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1200000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1400000,
          currency: "GBP",
        },
      },
      {
        month: "2027-07",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1400000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1300000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1500000,
          currency: "GBP",
        },
      },
      {
        month: "2027-08",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1500000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1400000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1600000,
          currency: "GBP",
        },
      },
      {
        month: "2027-09",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1600000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1500000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1700000,
          currency: "GBP",
        },
      },
      {
        month: "2027-10",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1700000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1600000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1800000,
          currency: "GBP",
        },
      },
      {
        month: "2027-11",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1800000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1700000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 1900000,
          currency: "GBP",
        },
      },
      {
        month: "2027-12",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 1900000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1800000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2000000,
          currency: "GBP",
        },
      },
      {
        month: "2028-01",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2000000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 1900000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2100000,
          currency: "GBP",
        },
      },
      {
        month: "2028-02",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2100000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2000000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2200000,
          currency: "GBP",
        },
      },
      {
        month: "2028-03",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2200000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2100000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2300000,
          currency: "GBP",
        },
      },
      {
        month: "2028-04",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2300000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2200000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2400000,
          currency: "GBP",
        },
      },
      {
        month: "2028-05",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2400000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2300000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2500000,
          currency: "GBP",
        },
      },
      {
        month: "2028-06",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2500000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2400000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2600000,
          currency: "GBP",
        },
      },
      {
        month: "2028-07",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2600000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2500000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2700000,
          currency: "GBP",
        },
      },
      {
        month: "2028-08",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2700000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2600000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2800000,
          currency: "GBP",
        },
      },
      {
        month: "2028-09",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2800000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2700000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 2900000,
          currency: "GBP",
        },
      },
      {
        month: "2028-10",
        payments: {
          minor_units: 0,
          currency: "GBP",
        },
        paid_to_provider: {
          minor_units: 0,
          currency: "GBP",
        },
        support: {
          minor_units: 0,
          currency: "GBP",
        },
        baseline_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        route_income: {
          minor_units: 200000,
          currency: "GBP",
        },
        pay_difference: {
          minor_units: 0,
          currency: "GBP",
        },
        opening: {
          minor_units: 2900000,
          currency: "GBP",
        },
        early_receipts: {
          minor_units: 0,
          currency: "GBP",
        },
        living: {
          minor_units: 100000,
          currency: "GBP",
        },
        debt_service: {
          minor_units: 0,
          currency: "GBP",
        },
        lower_bound: {
          minor_units: 2800000,
          currency: "GBP",
        },
        later_receipts: {
          minor_units: 200000,
          currency: "GBP",
        },
        closing: {
          minor_units: 3000000,
          currency: "GBP",
        },
      },
    ],
    beyond_horizon: [],
    unscheduled: [],
    before_start: [],
    debts: [],
    steps: [
      {
        variant_id: "offering:C01#part_time",
        concept_id: "option:C01",
        offering_id: "offering:C01#part_time",
        kind: "learning",
        title: "Certificate in Data",
        provider: "Netcom Training",
        start_date: "2026-12-01",
        finish_date: "2027-03-29",
        start_month: "2026-12",
        finish_month: "2027-03",
        usable_month: "2027-04",
        active_months: ["2026-12", "2027-01", "2027-02", "2027-03"],
        weekly_hours: 9,
        payments: [
          {
            kind: "fee",
            amount: {
              minor_units: 0,
              currency: "GBP",
            },
            month: "2026-12",
            due: null,
          },
        ],
        recurring: null,
        supports: [],
        fee_loan: null,
        work_pattern: {
          kind: "retain_work",
          hours_per_week: 30,
          net_income: {
            minor_units: 200000,
            currency: "GBP",
          },
        },
        wage: null,
        offer: null,
        application_deadline: null,
        prerequisites: [],
        grants: [],
        records: [
          {
            record: "concept",
            record_id: "option:C01",
            review_state: "proposed",
          },
          {
            record: "offering",
            record_id: "offering:C01#part_time",
            review_state: "proposed",
          },
        ],
        as_of: "2026-10-29",
        supplied: ["start_date", "weekly_hours", "cost"],
        added_by_person: false,
        synthetic: false,
        qualified_by: ["proposed_record", "supplied_figures"],
        sources: [
          {
            basis: "source",
            claim_id: "C01.title",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 2368-2387",
            excerpt: "Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.credential",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 58911-58943",
            excerpt: "NCFE Level 3 Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.level",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 58911-58943",
            excerpt: "NCFE Level 3 Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.awarding_body",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 58911-58943",
            excerpt: "NCFE Level 3 Certificate in Data",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.delivery_mode",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 56502-56522",
            excerpt: "100% online learning",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.assessment",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 60061-60084",
            excerpt: "Learn, certify, succeed",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.stated_hours",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 57939-57948",
            excerpt: "195 hours",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.duration",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 55850-55888",
            excerpt: "10 weeks full-time, 17 weeks part-time",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.funding_route",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 59794-59835",
            excerpt: "Adult Skills Fund / Free Courses for Jobs",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_area",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 62203-62254",
            excerpt: "You live in the West Midlands or Greater Manchester",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_age",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 62482-62510",
            excerpt: "You&#8217;re aged 19 or over",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_earnings",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 62738-62826",
            excerpt:
              "You earn below the gross annual wage cap of £34,194 (West Midlands)/£32,400 (Manchester)",
            retrieved_on: "2026-10-29",
          },
          {
            basis: "source",
            claim_id: "C01.eligibility_no_other_funded_training",
            source_id: "C01",
            source_hash: "00a3683af61602af7371c734ae6991d9b17b12551cbdf33736fc53b793373215",
            source_url: "https://www.netcomtraining.co.uk/course/certificate-in-data/",
            locator: "offsets 63054-63129",
            excerpt: "You&#8217;re not currently undertaking any other government-funded training",
            retrieved_on: "2026-10-29",
          },
        ],
      },
    ],
    gates: [],
    waits: [
      {
        first_month: "2026-11",
        last_month: "2026-11",
        months: 1,
      },
    ],
    milestones: [
      {
        kind: "readiness",
        month: "2027-04",
        months_to_readiness: 5,
      },
      {
        kind: "verify_assessed_completion",
        month: "2027-04",
        months_to_readiness: 5,
      },
    ],
    scenarios: [
      {
        scenario: "delay",
        feasibility: "feasible",
        verdict: "affordable_and_feasible_with_qualifications",
        months_to_readiness: 5,
        readiness_month: "2027-04",
        objective_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        direct_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        economic_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        findings: [],
        same_as_base: true,
      },
      {
        scenario: "no_award",
        feasibility: "feasible",
        verdict: "affordable_and_feasible_with_qualifications",
        months_to_readiness: 5,
        readiness_month: "2027-04",
        objective_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        direct_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        economic_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        findings: [],
        same_as_base: true,
      },
      {
        scenario: "no_offer",
        feasibility: "feasible",
        verdict: "affordable_and_feasible_with_qualifications",
        months_to_readiness: 5,
        readiness_month: "2027-04",
        objective_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        direct_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        economic_cost: {
          minor_units: 0,
          currency: "GBP",
        },
        findings: [],
        same_as_base: true,
      },
    ],
    self_paid: null,
  },
];

export const p01Skills: SkillsOut = {
  version: 3,
  profile_version: 1,
  synthetic: true,
  data_mode: "demo",
  pack: {
    pack_version: "0.4.0",
    dated: "2026-11-01",
    label_review:
      "the school-leaver pack session (H-07), 2026-11-01: the product owner's record, applied by Task 7f, for the records new or changed in 0.3.0 and offering:C08's deadline; the other records keep session 2's review (2026-10-29 to 2026-10-30); each record states its review_state and review",
    records_proposed: 67,
    records_reviewed: 62,
  },
  reference: {
    reference_version: "0.2.0",
    dated: "2026-10-30",
    review_state: "proposed",
    label_review:
      "session 2 (H-07), 2026-10-29 to 2026-10-30: R1-R40 checked by an AI and adopted by the product owner's ruling of 2026-10-30; 23 yes, 8 '?' (every required level) and 9 no (every anchor set, and the NMC check), so the reference stays proposed",
  },
  targets: [
    {
      target_key: "data quality analyst",
      target_title: "Data quality analyst",
      matrix_version: "m-46cbf14319135210",
      definition_version: "d-a39b6cdec163f0b1",
      synthetic: true,
      seed: "esco_occupation",
      occupation: {
        concept_id: "8a8272c7-bec5-5ace-bef5-e6b86d2c755f",
        label: "data quality specialist",
        basis: "pack_crosswalk",
        regulated: false,
      },
      occupation_note: null,
      esco_release: "esco-v1.2.1-en-csv",
      pack_target: {
        target_id: "data-quality-analyst-manchester",
        title: "Data quality analyst",
        city: "Manchester",
        basis: "title",
      },
      pack_target_note: null,
      details_version: 0,
      esco_listed: [
        {
          skill_id: "930fc173-f753-5cc1-9b70-7e3489de28ac",
          subject: "esco:930fc173-f753-5cc1-9b70-7e3489de28ac",
          label: "address problems critically",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:930fc173-f753-5cc1-9b70-7e3489de28ac",
          not_part_of_job: false,
        },
        {
          skill_id: "c2bdb1fa-747e-5df1-9680-95299af746ef",
          subject: "esco:c2bdb1fa-747e-5df1-9680-95299af746ef",
          label: "data ethics",
          skill_type: "knowledge",
          relation: "essential",
          row_id: "esco:c2bdb1fa-747e-5df1-9680-95299af746ef",
          not_part_of_job: false,
        },
        {
          skill_id: "6e9d196b-d418-52f4-a6f9-cae9a6f6ffc7",
          subject: "esco:6e9d196b-d418-52f4-a6f9-cae9a6f6ffc7",
          label: "database",
          skill_type: "knowledge",
          relation: "essential",
          row_id: "esco:6e9d196b-d418-52f4-a6f9-cae9a6f6ffc7",
          not_part_of_job: false,
        },
        {
          skill_id: "4d6f6fca-d322-576d-9311-7e7338e1b3ca",
          subject: "esco:4d6f6fca-d322-576d-9311-7e7338e1b3ca",
          label: "define data quality criteria",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:4d6f6fca-d322-576d-9311-7e7338e1b3ca",
          not_part_of_job: false,
        },
        {
          skill_id: "ba0334ef-4189-5628-a9e4-5dee0f304ce3",
          subject: "esco:ba0334ef-4189-5628-a9e4-5dee0f304ce3",
          label: "design database scheme",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:ba0334ef-4189-5628-a9e4-5dee0f304ce3",
          not_part_of_job: false,
        },
        {
          skill_id: "92e2d855-192f-5298-81fd-70659c73323c",
          subject: "esco:92e2d855-192f-5298-81fd-70659c73323c",
          label: "establish data processes",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:92e2d855-192f-5298-81fd-70659c73323c",
          not_part_of_job: false,
        },
        {
          skill_id: "662f4706-c2c2-549d-855c-0a2c52c0e197",
          subject: "esco:662f4706-c2c2-549d-855c-0a2c52c0e197",
          label: "handle data samples",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:662f4706-c2c2-549d-855c-0a2c52c0e197",
          not_part_of_job: false,
        },
        {
          skill_id: "f14984b5-1e16-517b-a9ec-e5b7298710a3",
          subject: "esco:f14984b5-1e16-517b-a9ec-e5b7298710a3",
          label: "implement data quality processes",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "pack:data-quality-analyst-manchester:data-validation",
          not_part_of_job: false,
        },
        {
          skill_id: "36927b22-4b46-552b-959b-c27aa0505f23",
          subject: "esco:36927b22-4b46-552b-959b-c27aa0505f23",
          label: "information structure",
          skill_type: "knowledge",
          relation: "essential",
          row_id: "esco:36927b22-4b46-552b-959b-c27aa0505f23",
          not_part_of_job: false,
        },
        {
          skill_id: "7943c93e-b83a-5058-8e81-132f314115a9",
          subject: "esco:7943c93e-b83a-5058-8e81-132f314115a9",
          label: "manage data",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:7943c93e-b83a-5058-8e81-132f314115a9",
          not_part_of_job: false,
        },
        {
          skill_id: "8be9a5f2-d349-582b-abe2-a5ee3ed5c431",
          subject: "esco:8be9a5f2-d349-582b-abe2-a5ee3ed5c431",
          label: "manage database",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:8be9a5f2-d349-582b-abe2-a5ee3ed5c431",
          not_part_of_job: false,
        },
        {
          skill_id: "7bf19b14-c4d8-599b-b181-f676fbc4d811",
          subject: "esco:7bf19b14-c4d8-599b-b181-f676fbc4d811",
          label: "manage standards for data exchange",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:7bf19b14-c4d8-599b-b181-f676fbc4d811",
          not_part_of_job: false,
        },
        {
          skill_id: "93aedd8b-e2ee-5780-aa00-e686f931ab39",
          subject: "esco:93aedd8b-e2ee-5780-aa00-e686f931ab39",
          label: "normalise data",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:93aedd8b-e2ee-5780-aa00-e686f931ab39",
          not_part_of_job: false,
        },
        {
          skill_id: "39b1fae8-a97b-546e-999f-1ad4b54fc042",
          subject: "esco:39b1fae8-a97b-546e-999f-1ad4b54fc042",
          label: "perform data cleansing",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:39b1fae8-a97b-546e-999f-1ad4b54fc042",
          not_part_of_job: false,
        },
        {
          skill_id: "8c5f6b25-ad18-5345-bfbc-4470f0e52cb1",
          subject: "esco:8c5f6b25-ad18-5345-bfbc-4470f0e52cb1",
          label: "process data",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:8c5f6b25-ad18-5345-bfbc-4470f0e52cb1",
          not_part_of_job: false,
        },
        {
          skill_id: "a8c8543d-f6f2-55a7-bac5-8033c729c5e8",
          subject: "esco:a8c8543d-f6f2-55a7-bac5-8033c729c5e8",
          label: "query languages",
          skill_type: "knowledge",
          relation: "essential",
          row_id: "pack:data-quality-analyst-manchester:independent-querying",
          not_part_of_job: false,
        },
        {
          skill_id: "8d589d38-85e8-5293-805f-965f40b67815",
          subject: "esco:8d589d38-85e8-5293-805f-965f40b67815",
          label: "report analysis results",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "pack:data-quality-analyst-manchester:communication",
          not_part_of_job: false,
        },
        {
          skill_id: "e0e0067a-4e11-5353-ad07-2f20b864e71c",
          subject: "esco:e0e0067a-4e11-5353-ad07-2f20b864e71c",
          label: "resource description framework query language",
          skill_type: "knowledge",
          relation: "essential",
          row_id: "esco:e0e0067a-4e11-5353-ad07-2f20b864e71c",
          not_part_of_job: false,
        },
        {
          skill_id: "4eab520b-938e-5c90-86d3-12ef6ede4d48",
          subject: "esco:4eab520b-938e-5c90-86d3-12ef6ede4d48",
          label: "use data processing techniques",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:4eab520b-938e-5c90-86d3-12ef6ede4d48",
          not_part_of_job: false,
        },
        {
          skill_id: "45e379e8-4ccc-534d-9e90-241901baa79d",
          subject: "esco:45e379e8-4ccc-534d-9e90-241901baa79d",
          label: "utilise regular expressions",
          skill_type: "skill/competence",
          relation: "essential",
          row_id: "esco:45e379e8-4ccc-534d-9e90-241901baa79d",
          not_part_of_job: false,
        },
        {
          skill_id: "17418abd-6927-5c55-a223-dfafac363b3b",
          subject: "esco:17418abd-6927-5c55-a223-dfafac363b3b",
          label: "LDAP",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:17418abd-6927-5c55-a223-dfafac363b3b",
          not_part_of_job: false,
        },
        {
          skill_id: "020809c7-93b0-5578-973d-766fff41227d",
          subject: "esco:020809c7-93b0-5578-973d-766fff41227d",
          label: "LINQ",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:020809c7-93b0-5578-973d-766fff41227d",
          not_part_of_job: false,
        },
        {
          skill_id: "9939b917-9933-5b71-bff9-df051e3e39ed",
          subject: "esco:9939b917-9933-5b71-bff9-df051e3e39ed",
          label: "MDX",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:9939b917-9933-5b71-bff9-df051e3e39ed",
          not_part_of_job: false,
        },
        {
          skill_id: "a4a66a83-bd20-5d73-83e6-95ad643843e1",
          subject: "esco:a4a66a83-bd20-5d73-83e6-95ad643843e1",
          label: "N1QL",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:a4a66a83-bd20-5d73-83e6-95ad643843e1",
          not_part_of_job: false,
        },
        {
          skill_id: "b4bd987b-d969-5f55-8c4b-f4ab6df4244c",
          subject: "esco:b4bd987b-d969-5f55-8c4b-f4ab6df4244c",
          label: "SPARQL",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:b4bd987b-d969-5f55-8c4b-f4ab6df4244c",
          not_part_of_job: false,
        },
        {
          skill_id: "09786d0f-aa94-59bf-bcc7-06a4446d1bf4",
          subject: "esco:09786d0f-aa94-59bf-bcc7-06a4446d1bf4",
          label: "XQuery",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:09786d0f-aa94-59bf-bcc7-06a4446d1bf4",
          not_part_of_job: false,
        },
        {
          skill_id: "f90978e6-2c5f-5395-a61b-4a0698cad0c0",
          subject: "esco:f90978e6-2c5f-5395-a61b-4a0698cad0c0",
          label: "build business relationships",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:f90978e6-2c5f-5395-a61b-4a0698cad0c0",
          not_part_of_job: false,
        },
        {
          skill_id: "4d9f3964-69d2-5a07-b7ea-8907715e4e8c",
          subject: "esco:4d9f3964-69d2-5a07-b7ea-8907715e4e8c",
          label: "business processes",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:4d9f3964-69d2-5a07-b7ea-8907715e4e8c",
          not_part_of_job: false,
        },
        {
          skill_id: "b6afe0f7-e871-5f45-b7bf-eb8da44bf11c",
          subject: "esco:b6afe0f7-e871-5f45-b7bf-eb8da44bf11c",
          label: "data engineering",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:b6afe0f7-e871-5f45-b7bf-eb8da44bf11c",
          not_part_of_job: false,
        },
        {
          skill_id: "6c44a4cc-6a49-5c10-a632-a5f7a33b14b7",
          subject: "esco:6c44a4cc-6a49-5c10-a632-a5f7a33b14b7",
          label: "data quality assessment",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:6c44a4cc-6a49-5c10-a632-a5f7a33b14b7",
          not_part_of_job: false,
        },
        {
          skill_id: "5dee2692-2bf5-5e48-a2ef-795410839ad8",
          subject: "esco:5dee2692-2bf5-5e48-a2ef-795410839ad8",
          label: "design database in the cloud",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:5dee2692-2bf5-5e48-a2ef-795410839ad8",
          not_part_of_job: false,
        },
        {
          skill_id: "68062c65-aa6d-5102-9411-6af2937fbc75",
          subject: "esco:68062c65-aa6d-5102-9411-6af2937fbc75",
          label: "execute ICT audits",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:68062c65-aa6d-5102-9411-6af2937fbc75",
          not_part_of_job: false,
        },
        {
          skill_id: "6f17d679-3128-59f7-931f-5726bade0c59",
          subject: "esco:6f17d679-3128-59f7-931f-5726bade0c59",
          label: "execute analytical mathematical calculations",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:6f17d679-3128-59f7-931f-5726bade0c59",
          not_part_of_job: false,
        },
        {
          skill_id: "371b9ba9-a5f2-53fb-b81e-92839a8a1981",
          subject: "esco:371b9ba9-a5f2-53fb-b81e-92839a8a1981",
          label: "healthcare analytics",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:371b9ba9-a5f2-53fb-b81e-92839a8a1981",
          not_part_of_job: false,
        },
        {
          skill_id: "e812c754-6cae-5e1d-ab75-5212110892ed",
          subject: "esco:e812c754-6cae-5e1d-ab75-5212110892ed",
          label: "manage schedule of tasks",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:e812c754-6cae-5e1d-ab75-5212110892ed",
          not_part_of_job: false,
        },
        {
          skill_id: "9c3a5e1e-641c-59e8-b1b6-4cbc5638b570",
          subject: "esco:9c3a5e1e-641c-59e8-b1b6-4cbc5638b570",
          label: "perform data analysis",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:9c3a5e1e-641c-59e8-b1b6-4cbc5638b570",
          not_part_of_job: false,
        },
        {
          skill_id: "80c97cea-dc13-5c9b-8f16-fec1164bf2b7",
          subject: "esco:80c97cea-dc13-5c9b-8f16-fec1164bf2b7",
          label: "perform project management",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:80c97cea-dc13-5c9b-8f16-fec1164bf2b7",
          not_part_of_job: false,
        },
        {
          skill_id: "be06ec2e-7ce4-587e-b654-eb31f6beec15",
          subject: "esco:be06ec2e-7ce4-587e-b654-eb31f6beec15",
          label: "statistics",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:be06ec2e-7ce4-587e-b654-eb31f6beec15",
          not_part_of_job: false,
        },
        {
          skill_id: "9da348b6-7ed6-58c0-a342-96dc38bd74a9",
          subject: "esco:9da348b6-7ed6-58c0-a342-96dc38bd74a9",
          label: "train employees",
          skill_type: "skill/competence",
          relation: "optional",
          row_id: "esco:9da348b6-7ed6-58c0-a342-96dc38bd74a9",
          not_part_of_job: false,
        },
        {
          skill_id: "83065714-8639-5d46-a39a-963f92e2e4e2",
          subject: "esco:83065714-8639-5d46-a39a-963f92e2e4e2",
          label: "visual presentation techniques",
          skill_type: "knowledge",
          relation: "optional",
          row_id: "esco:83065714-8639-5d46-a39a-963f92e2e4e2",
          not_part_of_job: false,
        },
      ],
      examples: [],
      requirements: [
        {
          row_id: "pack:data-quality-analyst-manchester:independent-querying",
          subject: "esco:a8c8543d-f6f2-55a7-bac5-8033c729c5e8",
          label: "Querying data independently (SQL)",
          kind: "skill",
          scope: "target",
          importance: "disputed",
          gate: null,
          rubric_version: "pack:data-quality-analyst-manchester:independent-querying@0.1.0",
          rubric_review_state: "proposed",
          required_level: 2,
          review_state: "proposed",
          as_of: "2026-10-29",
          employer_specific: true,
          entry_facts: [],
          latest_holding: null,
          source_urls: [
            "https://www.jobs.nhs.uk/candidate/jobadvert/C9242-25-0210",
            "https://www.reed.co.uk/jobs/data-analyst/57376369",
            "https://www.reed.co.uk/jobs/data-analyst/57482544",
            "https://www.reed.co.uk/jobs/junior-data-analyst/57492098",
          ],
          rubric_anchors: {
            "0": "No evidence yet of writing a query against a database.",
            "1": "Writes a simple query with a filter when given an example or step-by-step help.",
            "2": "Independently joins two tables, explains how missing keys change the row count and checks the result.",
            "3": "Writes multi-step queries (grouping, subqueries or window functions) on unfamiliar tables and finds why a result looks wrong.",
            "4": "Designs the querying approach for others, reviews their queries and justifies trade-offs between correctness, clarity and speed.",
          },
          latest_skill: {
            answer: "not_learned",
            self_assessed_level: null,
            example: null,
            last_done: null,
          },
        },
        {
          row_id: "pack:data-quality-analyst-manchester:data-validation",
          subject: "esco:f14984b5-1e16-517b-a9ec-e5b7298710a3",
          label: "Investigating and resolving data quality issues",
          kind: "skill",
          scope: "target",
          importance: "essential",
          gate: null,
          rubric_version: "pack:data-quality-analyst-manchester:data-validation@0.1.0",
          rubric_review_state: "proposed",
          required_level: 2,
          review_state: "proposed",
          as_of: "2026-10-29",
          employer_specific: true,
          entry_facts: [],
          latest_holding: null,
          source_urls: [
            "https://www.jobs.nhs.uk/candidate/jobadvert/C9242-25-0210",
            "https://www.reed.co.uk/jobs/data-analyst/57482544",
          ],
          rubric_anchors: {
            "0": "No evidence yet of checking data for quality problems.",
            "1": "Spots an obvious problem, such as a blank or a duplicate, when shown what to look for.",
            "2": "Independently checks a dataset for missing, duplicated and inconsistent values, traces a problem to its source and records the fix.",
            "3": "Investigates problems that cross systems or have no obvious cause, and designs checks that stop them recurring.",
            "4": "Sets data quality rules and processes for a team and justifies which problems to fix first.",
          },
          latest_skill: {
            answer: "done_independently",
            self_assessed_level: 2,
            example:
              "Synthetic example: I traced duplicate stock records to a repeated import, corrected them and explained the limits of the fix to the shift team.",
            last_done: "2026-10",
          },
        },
        {
          row_id: "pack:data-quality-analyst-manchester:communication",
          subject: "esco:8d589d38-85e8-5293-805f-965f40b67815",
          label: "Communicating findings to non-technical colleagues",
          kind: "skill",
          scope: "target",
          importance: "disputed",
          gate: null,
          rubric_version: "pack:data-quality-analyst-manchester:communication@0.1.0",
          rubric_review_state: "proposed",
          required_level: 2,
          review_state: "proposed",
          as_of: "2026-10-29",
          employer_specific: true,
          entry_facts: [],
          latest_holding: null,
          source_urls: [
            "https://www.jobs.nhs.uk/candidate/jobadvert/C9242-25-0210",
            "https://www.reed.co.uk/jobs/data-analyst/57376369",
            "https://www.reed.co.uk/jobs/data-analyst/57482544",
            "https://www.reed.co.uk/jobs/junior-data-analyst/57492098",
          ],
          rubric_anchors: {
            "0": "No evidence yet of explaining findings to others.",
            "1": "Shares results for others to interpret, or explains them with help.",
            "2": "Independently explains a finding and its limits in plain words to a non-technical colleague and checks they understood it.",
            "3": "Handles a disagreement or a difficult message about the data, adapting the explanation to different audiences.",
            "4": "Leads how findings are reported across a team and justifies what to leave out and why.",
          },
          latest_skill: {
            answer: "done_independently",
            self_assessed_level: 2,
            example:
              "Synthetic example: I traced duplicate stock records to a repeated import, corrected them and explained the limits of the fix to the shift team.",
            last_done: "2026-10",
          },
        },
      ],
      assessment_state: "assessed",
      not_assessed_reason: null,
      readiness: {
        target_key: "data quality analyst",
        target_title: "Data quality analyst",
        matrix_version: "m-46cbf14319135210",
        definition_version: "d-a39b6cdec163f0b1",
        evidence_version: 3,
        pack_version: "0.4.0",
        reference_version: "0.2.0",
        synthetic: true,
        scenario: "current",
        completed: [],
        state: "not_ready",
        primary_action: "address_gaps",
        training_required: true,
        show_route_chart: true,
        qualifications: [
          "provisional_matrix",
          "proposed_records",
          "proposed_rubrics",
          "self_reported_evidence",
        ],
        rows: [
          {
            row_id: "pack:data-quality-analyst-manchester:independent-querying",
            subject: "esco:a8c8543d-f6f2-55a7-bac5-8033c729c5e8",
            label: "Querying data independently (SQL)",
            kind: "skill",
            importance: "disputed",
            mandatory: true,
            protected: false,
            required_level: 2,
            status: "below_required",
            evidence: {
              level: 0,
              basis: "self_reported",
              confidence: "provisional",
              answer: "not_learned",
              self_assessed_level: 0,
              demonstrated_level: null,
              last_done: null,
              independence: "independent",
              tools: null,
              ai_assisted: null,
              evidence_ids: ["0a76f770-c3e5-4d54-9c07-33ad9f06ea58"],
              shared_from_other_rubric: false,
              conflict: false,
            },
            statement: null,
            planned_level: null,
            eligible_to_apply_after_completion: false,
            review_state: "proposed",
            modelled: true,
          },
          {
            row_id: "pack:data-quality-analyst-manchester:data-validation",
            subject: "esco:f14984b5-1e16-517b-a9ec-e5b7298710a3",
            label: "Investigating and resolving data quality issues",
            kind: "skill",
            importance: "essential",
            mandatory: true,
            protected: false,
            required_level: 2,
            status: "met",
            evidence: {
              level: 2,
              basis: "self_reported",
              confidence: "provisional",
              answer: "done_independently",
              self_assessed_level: 2,
              demonstrated_level: null,
              last_done: "2026-10",
              independence: "independent",
              tools: null,
              ai_assisted: null,
              evidence_ids: ["1558cefc-0778-45ac-ab30-cd534d204db6"],
              shared_from_other_rubric: false,
              conflict: false,
            },
            statement: null,
            planned_level: null,
            eligible_to_apply_after_completion: false,
            review_state: "proposed",
            modelled: true,
          },
          {
            row_id: "pack:data-quality-analyst-manchester:communication",
            subject: "esco:8d589d38-85e8-5293-805f-965f40b67815",
            label: "Communicating findings to non-technical colleagues",
            kind: "skill",
            importance: "disputed",
            mandatory: true,
            protected: false,
            required_level: 2,
            status: "met",
            evidence: {
              level: 2,
              basis: "self_reported",
              confidence: "provisional",
              answer: "done_independently",
              self_assessed_level: 2,
              demonstrated_level: null,
              last_done: "2026-10",
              independence: "independent",
              tools: null,
              ai_assisted: null,
              evidence_ids: ["afbbd131-6c33-4efa-a3aa-e11578b63e36"],
              shared_from_other_rubric: false,
              conflict: false,
            },
            statement: null,
            planned_level: null,
            eligible_to_apply_after_completion: false,
            review_state: "proposed",
            modelled: true,
          },
        ],
        blockers: [
          {
            row_id: "pack:data-quality-analyst-manchester:independent-querying",
            kind: "below_required",
          },
        ],
        gaps: [
          {
            gap_id: "gap:pack:data-quality-analyst-manchester:independent-querying",
            row_id: "pack:data-quality-analyst-manchester:independent-querying",
            subject: "esco:a8c8543d-f6f2-55a7-bac5-8033c729c5e8",
            label: "Querying data independently (SQL)",
            kind: "learn",
            mandatory: true,
            required_level: 2,
            evidenced_level: 0,
            evidence_ids: ["0a76f770-c3e5-4d54-9c07-33ad9f06ea58"],
            statement_id: null,
            review_state: "proposed",
          },
        ],
        actions: [
          {
            action_id: "action:pack:data-quality-analyst-manchester:independent-querying",
            kind: "learn",
            label: "Querying data independently (SQL)",
            rows: ["pack:data-quality-analyst-manchester:independent-querying"],
            mandatory: true,
            prerequisites: [],
            candidates: [
              {
                outcome_id: "outcome:C01.1",
                option_id: "option:C01",
                offering_id: "offering:C01",
                option_title: "Certificate in Data",
                outcome_type: "skill_level",
                evidence_kind: "topic_mention",
                confidence: "unsupported",
                level_on_completion: null,
                review_state: "proposed",
                provenance: "provider_claim",
                addresses: false,
                numeric_use: "excluded_missing_level",
                months_minimum: 3,
                outside_planning_model: false,
                as_of: "2026-10-29",
              },
              {
                outcome_id: "outcome:C04.1",
                option_id: "option:C04",
                offering_id: "offering:C04",
                option_title: "Junior Data Analyst",
                outcome_type: "skill_level",
                evidence_kind: "practice",
                confidence: "provisional",
                level_on_completion: null,
                review_state: "reviewed",
                provenance: "provider_claim",
                addresses: true,
                numeric_use: "excluded_missing_level",
                months_minimum: null,
                outside_planning_model: false,
                as_of: "2026-10-29",
              },
            ],
            state: "open",
            code: null,
          },
        ],
        employer_checks: [
          {
            row_id: "posting:req:J05.3",
            requirement_id: "req:J05.3",
            posting_id: "job:J05",
            posting_title: "Data Quality Analyst",
            text: "Advanced skills in Microsoft Excel",
            kind: "skill",
          },
          {
            row_id: "posting:req:J05.4",
            requirement_id: "req:J05.4",
            posting_id: "job:J05",
            posting_title: "Data Quality Analyst",
            text: "Experience of Microsoft Power BI (report building, dashboards, DAX)",
            kind: "skill",
          },
          {
            row_id: "posting:req:J05.5",
            requirement_id: "req:J05.5",
            posting_id: "job:J05",
            posting_title: "Data Quality Analyst",
            text: "Educated to degree level or equivalent",
            kind: "credential",
          },
          {
            row_id: "posting:req:J18.4",
            requirement_id: "req:J18.4",
            posting_id: "job:J18",
            posting_title: "Data Analyst",
            text: "Experience in a data analysis or similar analytical role.",
            kind: "experience",
          },
          {
            row_id: "posting:req:J20.2",
            requirement_id: "req:J20.2",
            posting_id: "job:J20",
            posting_title: "Junior Data Analyst",
            text: "Experience creating dashboards and visualisations in Power BI, Tableau or a similar tool",
            kind: "skill",
          },
          {
            row_id: "posting:req:J20.4",
            requirement_id: "req:J20.4",
            posting_id: "job:J20",
            posting_title: "Junior Data Analyst",
            text: "Previous experience in a Data Analyst, Insight Analyst or Reporting Analyst role",
            kind: "experience",
          },
        ],
        optional_development: [],
        not_modelled_rows: 42,
      },
      rubric_review: "proposed",
    },
  ],
  questions: {
    state: "enough",
    synthetic: true,
    evidence_version: 3,
    targets: [
      {
        target_key: "data quality analyst",
        target_title: "Data quality analyst",
        matrix_version: "m-46cbf14319135210",
        definition_version: "d-a39b6cdec163f0b1",
      },
    ],
    prompts: [],
    initial: [],
    coverage: {
      gates_known: 0,
      gates: 0,
      required_rows_with_usable_evidence: 3,
      required_rows: 3,
      weighted_with_usable_evidence: 7,
      weighted_required: 7,
      unresolved: [],
    },
  },
  usual_in_role: null,
  qualifications: [],
};

export const p01Checkpoint: CheckpointOut = {
  inputs_version: 2,
  profile_version: 1,
  synthetic: true,
  data_mode: "demo",
  pack: {
    pack_version: "0.4.0",
    dated: "2026-11-01",
    label_review:
      "the school-leaver pack session (H-07), 2026-11-01: the product owner's record, applied by Task 7f, for the records new or changed in 0.3.0 and offering:C08's deadline; the other records keep session 2's review (2026-10-29 to 2026-10-30); each record states its review_state and review",
    records_proposed: 67,
    records_reviewed: 62,
  },
  needs: [],
  direct_spend_cap: {
    minor_units: 150000,
    currency: "GBP",
  },
  monthly_payment_cap: {
    minor_units: 150000,
    currency: "GBP",
  },
  payment_cap_basis: "payments_and_debt_repayments",
  work_status: null,
  baseline: {
    kind: "current_role",
    net_income: {
      minor_units: 200000,
      currency: "GBP",
    },
  },
  continuation: {
    hours_per_week: 30,
    net_income: {
      minor_units: 200000,
      currency: "GBP",
    },
  },
  not_working: false,
  targets: [
    {
      target_title: "Data quality analyst",
      pack_target_id: "data-quality-analyst-manchester",
      note: null,
      label: {
        name: "nessa-england-option-pack 0.4.0",
        dated: "2026-11-01",
        synthetic: false,
        research_fingerprint: null,
      },
      reviewed_options: 0,
      options: [
        {
          variant_id: "offering:C01#full_time",
          offering_id: "offering:C01#full_time",
          concept_id: "option:C01",
          plan_id: "as-stated",
          review_states: ["proposed", "proposed"],
          as_of: "2026-10-29",
          added_by_person: false,
          missing: [],
          supplied: ["start_date", "weekly_hours", "cost"],
          stated_intakes: [],
          entry_requirements: [],
          entry_requirements_met: null,
          entry_expected: false,
          eligibility_conditions: [
            {
              field: "eligibility_area",
              value: "Greater Manchester or the West Midlands",
              status: "confirmed",
            },
            {
              field: "eligibility_age",
              value: {
                minimum_age: 19,
              },
              status: "confirmed",
            },
            {
              field: "eligibility_earnings",
              value: {
                below_annual_gross: {
                  currency: "GBP",
                  minor_units: 3240000,
                },
                area: "Greater Manchester",
              },
              status: "confirmed",
            },
            {
              field: "eligibility_no_other_funded_training",
              value: true,
              status: "confirmed",
            },
          ],
          age_rules: [
            {
              field: "eligibility_age",
              value: {
                minimum_age: 19,
              },
              applied: false,
            },
          ],
          outcomes: [
            {
              outcome_id: "outcome:C01.1",
              skill_id: "pack:data-quality-analyst-manchester:independent-querying",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "topic_mention",
              review_state: "proposed",
              decision: "override",
            },
            {
              outcome_id: "outcome:C01.2",
              skill_id: "pack:data-quality-analyst-manchester:data-validation",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "topic_mention",
              review_state: "proposed",
              decision: null,
            },
            {
              outcome_id: "outcome:C01.3",
              skill_id: "pack:data-quality-analyst-manchester:communication",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "practice",
              review_state: "proposed",
              decision: null,
            },
          ],
          left_out: false,
        },
        {
          variant_id: "offering:C01#part_time",
          offering_id: "offering:C01#part_time",
          concept_id: "option:C01",
          plan_id: "as-stated",
          review_states: ["proposed", "proposed"],
          as_of: "2026-10-29",
          added_by_person: false,
          missing: [],
          supplied: ["start_date", "weekly_hours", "cost"],
          stated_intakes: [],
          entry_requirements: [],
          entry_requirements_met: null,
          entry_expected: false,
          eligibility_conditions: [
            {
              field: "eligibility_area",
              value: "Greater Manchester or the West Midlands",
              status: "confirmed",
            },
            {
              field: "eligibility_age",
              value: {
                minimum_age: 19,
              },
              status: "confirmed",
            },
            {
              field: "eligibility_earnings",
              value: {
                below_annual_gross: {
                  currency: "GBP",
                  minor_units: 3240000,
                },
                area: "Greater Manchester",
              },
              status: "confirmed",
            },
            {
              field: "eligibility_no_other_funded_training",
              value: true,
              status: "confirmed",
            },
          ],
          age_rules: [
            {
              field: "eligibility_age",
              value: {
                minimum_age: 19,
              },
              applied: false,
            },
          ],
          outcomes: [
            {
              outcome_id: "outcome:C01.1",
              skill_id: "pack:data-quality-analyst-manchester:independent-querying",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "topic_mention",
              review_state: "proposed",
              decision: "override",
            },
            {
              outcome_id: "outcome:C01.2",
              skill_id: "pack:data-quality-analyst-manchester:data-validation",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "topic_mention",
              review_state: "proposed",
              decision: null,
            },
            {
              outcome_id: "outcome:C01.3",
              skill_id: "pack:data-quality-analyst-manchester:communication",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "practice",
              review_state: "proposed",
              decision: null,
            },
          ],
          left_out: false,
        },
        {
          variant_id: "offering:C04~pay-in-full",
          offering_id: "offering:C04",
          concept_id: "option:C04",
          plan_id: "pay-in-full",
          review_states: ["proposed", "proposed"],
          as_of: "2026-10-29",
          added_by_person: false,
          missing: ["start_date", "finish_date", "weekly_hours"],
          supplied: [],
          stated_intakes: [],
          entry_requirements: [],
          entry_requirements_met: null,
          entry_expected: false,
          eligibility_conditions: [],
          age_rules: [],
          outcomes: [
            {
              outcome_id: "outcome:C04.1",
              skill_id: "pack:data-quality-analyst-manchester:independent-querying",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "practice",
              review_state: "reviewed",
              decision: null,
            },
            {
              outcome_id: "outcome:C04.2",
              skill_id: "pack:data-quality-analyst-manchester:data-validation",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "practice",
              review_state: "reviewed",
              decision: null,
            },
          ],
          left_out: false,
        },
        {
          variant_id: "offering:C04~instalments",
          offering_id: "offering:C04",
          concept_id: "option:C04",
          plan_id: "instalments",
          review_states: ["proposed", "proposed"],
          as_of: "2026-10-29",
          added_by_person: false,
          missing: ["start_date", "finish_date", "weekly_hours", "cost"],
          supplied: [],
          stated_intakes: [],
          entry_requirements: [],
          entry_requirements_met: null,
          entry_expected: false,
          eligibility_conditions: [],
          age_rules: [],
          outcomes: [
            {
              outcome_id: "outcome:C04.1",
              skill_id: "pack:data-quality-analyst-manchester:independent-querying",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "practice",
              review_state: "reviewed",
              decision: null,
            },
            {
              outcome_id: "outcome:C04.2",
              skill_id: "pack:data-quality-analyst-manchester:data-validation",
              outcome_type: "skill_level",
              level_on_completion: null,
              evidence_kind: "practice",
              review_state: "reviewed",
              decision: null,
            },
          ],
          left_out: false,
        },
      ],
      schemes: [
        {
          instrument_id: "funding:F01",
          kind: "fee_waiver",
          review_state: "proposed",
          as_of: "2026-10-29",
          age_rules: [
            {
              field: "rule_age",
              value: {
                minimum_age: 19,
              },
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F02",
          kind: "loan",
          review_state: "proposed",
          as_of: "2026-11-01",
          age_rules: [
            {
              field: "rule_age",
              value: {
                minimum_age: 19,
                on: "first day of the course",
              },
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F03",
          kind: "programme",
          review_state: "reviewed",
          as_of: "2026-10-29",
          age_rules: [
            {
              field: "rule_age",
              value: {
                minimum_age: 19,
              },
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F05",
          kind: "loan",
          review_state: "reviewed",
          as_of: "2026-11-01",
          age_rules: [
            {
              field: "rule_age_limit",
              value: "no upper age limit for a Tuition Fee Loan",
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F05.maintenance",
          kind: "loan",
          review_state: "reviewed",
          as_of: "2026-11-01",
          age_rules: [
            {
              field: "rule_age_limit",
              value:
                "aged 60 or over on the first day of the first academic year: limited Maintenance Loan funding",
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F10",
          kind: "programme",
          review_state: "reviewed",
          as_of: "2026-11-01",
          age_rules: [
            {
              field: "rule_age",
              value: {
                minimum_age: 16,
                on: "31 August 2026",
              },
              applied: false,
            },
            {
              field: "rule_age_band",
              value: "under 19 on 31 August 2026",
              applied: false,
            },
            {
              field: "rule_age_exception",
              value:
                "19 or over: only if continuing a course started aged 16 to 18 (or with an EHC plan)",
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F12",
          kind: "loan",
          review_state: "reviewed",
          as_of: "2026-11-01",
          age_rules: [
            {
              field: "rule_age_limit",
              value: "under 60 on the first day of the course, to apply for a Tuition Fee Loan",
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F12.maintenance",
          kind: "loan",
          review_state: "reviewed",
          as_of: "2026-11-01",
          age_rules: [
            {
              field: "rule_age_limit",
              value:
                "aged 60 or above: may be able to apply for an additional loan to help cover living costs",
              applied: false,
            },
          ],
        },
        {
          instrument_id: "funding:F04",
          kind: "programme",
          review_state: "proposed",
          as_of: "2026-11-01",
          age_rules: [
            {
              field: "rule_age_band",
              value:
                "an employer not paying the levy: the government pays 100% (up to the funding band maximum) for an apprentice aged 16 to 24",
              applied: false,
            },
          ],
        },
      ],
      scope: {
        concepts: 2,
        max_concepts: 24,
        most_starts: 2,
        max_starts: 2,
        over_starts: [],
        code: null,
      },
    },
  ],
};

export const p01Profile: ProfileOut = {
  workspace_id: "74fa4514-899d-5316-80fd-4161dc0dbda0",
  version: 1,
  document: {
    schema_version: "5",
    preferred_name: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    current_role: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    cities: {
      state: "provided",
      value: ["Manchester"],
      source_ref_id: "a5a481e4-fb2b-5052-aeed-90aba3ed9e41",
    },
    target_titles: {
      state: "provided",
      value: ["Data quality analyst"],
      source_ref_id: "a5a481e4-fb2b-5052-aeed-90aba3ed9e41",
    },
    weekly_study_hours: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    direct_spend_cap: {
      state: "provided",
      value: {
        minor_units: 150000,
        currency: "GBP",
      },
      source_ref_id: "a5a481e4-fb2b-5052-aeed-90aba3ed9e41",
    },
    monthly_payment_cap: {
      state: "provided",
      value: {
        minor_units: 150000,
        currency: "GBP",
      },
      source_ref_id: "a5a481e4-fb2b-5052-aeed-90aba3ed9e41",
    },
    enjoyed_tasks: {
      state: "provided",
      value: ["finding inconsistencies", "explaining evidence"],
      source_ref_id: "a5a481e4-fb2b-5052-aeed-90aba3ed9e41",
    },
    confident_tasks: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    evidenced_tasks: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    work_style: {
      state: "provided",
      value: ["structured", "collaborative"],
      source_ref_id: "a5a481e4-fb2b-5052-aeed-90aba3ed9e41",
    },
    minimum_salary: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    work_status: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    qualifications: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
    disliked_tasks: {
      state: "unasked",
      value: null,
      source_ref_id: null,
    },
  },
  created_by: null,
  created_at: "2026-11-04T12:35:29.374283Z",
};

const savedRoute = p01Routes[1];
if (!savedRoute) throw new Error("P01 needs its saved part-time route.");

export const p01Plan: PlanSnapshot = {
  ...{
    plan_id: "10141bd6-cf62-415d-89fa-fa28b8c8bc3a",
    version: 2,
    workspace_id: "74fa4514-899d-5316-80fd-4161dc0dbda0",
    selected_at: "2026-11-04T18:04:58.048884Z",
    selected_by: "9fbb9445-0dfc-5f9d-94ca-0d01fec6683c",
    assumptions_confirmed: true,
    commitments: [],
    target_title: "Data quality analyst",
    source: {
      solve_run_id: "e31be37d-1129-435c-9b27-ecac2806f210",
      solve_id: "solve:2b6f55a063e50eb8",
      schedule_index: 1,
      profile_version: 1,
      inputs_version: 2,
      capability_version: 3,
      input_version: "monthly-input:d0e68ba4acc284eb",
      matrix_version: "m-46cbf14319135210",
      definition_version: "d-a39b6cdec163f0b1",
      algorithm_version: "canonical-dfs-1",
      pruning_version: "sound-pruning-6",
    },
    search: {
      coverage: "complete",
      stop_reason: null,
      instance: {
        concepts: 2,
        starts_per_concept: 2,
        months: 24,
        variants: 4,
        selection_space: 9,
      },
      limits: {
        max_actions: 24,
        max_starts_per_action: 2,
        max_selected_actions: 6,
        max_months: 24,
        wall_seconds: 30,
        max_states: 1000000,
        max_feasible_archive: 50000,
      },
    },
    events: [
      {
        key: "offering:C01#part_time:start",
        kind: "start",
        variant_id: "offering:C01#part_time",
        title: "Certificate in Data",
        on: "2026-12-01",
        conditional: false,
        proposed: true,
      },
      {
        key: "offering:C01#part_time:finish",
        kind: "finish",
        variant_id: "offering:C01#part_time",
        title: "Certificate in Data",
        on: "2027-03-29",
        conditional: false,
        proposed: true,
      },
    ],
    next_action: {
      key: "offering:C01#part_time:start",
      kind: "start",
      variant_id: "offering:C01#part_time",
      title: "Certificate in Data",
      on: "2026-12-01",
      conditional: false,
      proposed: true,
    },
    progress: {
      completed_steps: [],
      rest_until: null,
      review_on: null,
      activity: [],
    },
  },
  route: savedRoute,
};
