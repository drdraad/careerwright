import type { CheckpointOut, OptionFacts, OptionsOut } from "@/generated/api";

const gbp = (minor_units: number) => ({ minor_units, currency: "GBP" as const });
const cited = { basis: "fixture" as const, excerpt: "Fees of £9,250", retrieved_on: "2026-11-01" };
const pack = {
  pack_version: "0.4.0",
  dated: "2026-11-01",
  label_review: "reviewed",
  records_proposed: 0,
  records_reviewed: 3,
};

const facts = (
  variant_id: string,
  offering_id: string,
  concept_id: string,
  missing: OptionFacts["missing"],
): OptionFacts => ({
  variant_id,
  offering_id,
  concept_id,
  plan_id: variant_id === "degree" ? "degree-fee" : null,
  review_states: ["reviewed", "reviewed"],
  as_of: "2026-11-01",
  added_by_person: false,
  missing,
  supplied: [],
  stated_intakes: variant_id === "degree" ? ["2027-09-01"] : [],
  entry_requirements: [],
  entry_requirements_met: null,
  entry_expected: variant_id === "t-level",
  eligibility_conditions: [],
  age_rules: [],
  outcomes: [],
  left_out: false,
});

export const optionsFixture: OptionsOut = {
  profile_version: 2,
  synthetic: true,
  data_mode: "demo",
  pack,
  targets: [
    {
      target_title: "Data quality analyst",
      pack_target_id: "target:1",
      note: null,
      catalogue: {
        label: { name: "England options (synthetic)", dated: "2026-11-01", synthetic: true },
        concepts: [
          {
            concept_id: "degree",
            kind: "learning",
            title: "Data science degree",
            provider: "North College",
            review_state: "reviewed",
            synthetic: true,
            cited,
          },
          {
            concept_id: "apprentice",
            kind: "apprenticeship",
            title: "Data apprenticeship",
            provider: "City employer",
            review_state: "reviewed",
            synthetic: true,
          },
          {
            concept_id: "t-level",
            kind: "learning",
            title: "Digital T Level",
            provider: "South College",
            review_state: "reviewed",
            synthetic: true,
          },
        ],
        offerings: [
          {
            offering_id: "degree-offering",
            concept_id: "degree",
            review_state: "reviewed",
            start: null,
            finish: null,
            weekly_hours: null,
            stated_intakes: ["2027-09-01"],
            payment_plans: [
              { plan_id: "degree-fee", payments: [{ kind: "fee", amount: gbp(925000), cited }] },
            ],
            synthetic: true,
          },
          {
            offering_id: "apprentice-offering",
            concept_id: "apprentice",
            review_state: "reviewed",
            start: "2027-02-01",
            finish: "2028-02-01",
            weekly_hours: 32,
            synthetic: true,
          },
          {
            offering_id: "t-level-offering",
            concept_id: "t-level",
            review_state: "reviewed",
            start: "2027-09-01",
            finish: "2029-07-01",
            weekly_hours: 18,
            synthetic: true,
          },
        ],
        variants: [
          {
            variant_id: "degree",
            offering_id: "degree-offering",
            plan_id: "degree-fee",
            tuition_fee_loan: {
              amount: gbp(925000),
              eligibility: "potentially_eligible",
              application: "not_applied",
              review_state: "accepted_assumption",
              cited,
            },
          },
          { variant_id: "apprentice", offering_id: "apprentice-offering" },
          { variant_id: "t-level", offering_id: "t-level-offering" },
        ],
      },
    },
  ],
};

export const checkpointFixture: CheckpointOut = {
  inputs_version: 1,
  profile_version: 2,
  synthetic: true,
  data_mode: "demo",
  pack,
  needs: [{ input: "objective_basis", effect: "blocks_a_solve" }],
  direct_spend_cap: gbp(150000),
  monthly_payment_cap: gbp(100000),
  payment_cap_basis: "payments_and_debt_repayments",
  work_status: "in_education_or_training",
  baseline: { kind: "staying_in_education", net_income: gbp(0) },
  continuation: { hours_per_week: 0, net_income: gbp(0) },
  not_working: true,
  targets: [
    {
      target_title: "Data quality analyst",
      pack_target_id: "target:1",
      note: null,
      label: { name: "England options (synthetic)", dated: "2026-11-01", synthetic: true },
      reviewed_options: 3,
      options: [
        facts("degree", "degree-offering", "degree", ["start_date"]),
        facts("apprentice", "apprentice-offering", "apprentice", ["entry_confirmation"]),
        facts("t-level", "t-level-offering", "t-level", ["cost"]),
      ],
      schemes: [],
      scope: {
        concepts: 3,
        max_concepts: 24,
        most_starts: 1,
        max_starts: 2,
        over_starts: [],
        code: null,
      },
    },
  ],
};
