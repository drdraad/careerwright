// The planning inputs as the web writes them back (Task 12b, screens half): the API replaces the
// whole document on each write, so every change starts from what is stored, keeps every other
// answer, and sends back only what a client may send (no stamps, no schema version).
import { describe, expect, it } from "vitest";
import type { PlanningInputsDocument } from "@/generated/api";
import { submitted, withExcluded, withFigure, withVariant } from "./planningInputs";

const gbp = (minor_units: number) => ({ minor_units, currency: "GBP" as const });
const STAMP = {
  recorded_by: "00000000-0000-4000-8000-000000000001",
  recorded_at: "2026-11-03T10:00:00Z",
};

const stored: PlanningInputsDocument = {
  schema_version: "1",
  objective_basis: "economic",
  living_costs: gbp(100000),
  offering_figures: [{ offering_id: "offering:C01#full_time", weekly_hours: 9 }],
  variants: [{ variant_id: "offering:C08", entry_requirements_met: true }],
  excluded_variants: ["offering:C04~instalments"],
  outcome_decisions: [{ outcome_id: "outcome:1", decision: "accept", ...STAMP }],
  own_options: [
    {
      option_id: "evening-course",
      target: "Data quality analyst",
      title: { typed: "Evening data course" },
      ...STAMP,
    },
  ],
};

describe("[OPTN-13] a change to the planning inputs keeps every other answer", () => {
  it("sends back the stored document without its stamps or schema version", () => {
    expect(submitted(stored)).toEqual({
      objective_basis: "economic",
      living_costs: gbp(100000),
      offering_figures: [{ offering_id: "offering:C01#full_time", weekly_hours: 9 }],
      variants: [{ variant_id: "offering:C08", entry_requirements_met: true }],
      excluded_variants: ["offering:C04~instalments"],
      outcome_decisions: [{ outcome_id: "outcome:1", decision: "accept" }],
      own_options: [
        {
          option_id: "evening-course",
          target: "Data quality analyst",
          title: { typed: "Evening data course" },
        },
      ],
    });
  });

  it("adds a figure beside the offering's others, and a first figure for another offering", () => {
    const inputs = submitted(stored);
    const start = withFigure(inputs, "offering:C01#full_time", {
      fact: "start_date",
      on: "2027-01-04",
      basis: "own_figure",
    });
    const cost = withFigure(start, "offering:C08", { fact: "cost", money: gbp(3015000) });

    expect(cost.offering_figures).toEqual([
      {
        offering_id: "offering:C01#full_time",
        weekly_hours: 9,
        start: { on: "2027-01-04", basis: "own_figure" },
      },
      { offering_id: "offering:C08", cost: gbp(3015000) },
    ]);
    expect(cost.living_costs).toEqual(gbp(100000));
    expect(inputs.offering_figures).toEqual(stored.offering_figures); // never changed in place
  });

  it("changes one option's answers and keeps the rest of them", () => {
    const inputs = withVariant(submitted(stored), "offering:C08", {
      tuition_fee_loan: {
        amount: null,
        eligibility: "potentially_eligible",
        application: "not_applied",
      },
    });
    const other = withVariant(inputs, "offering:C11", { entry_requirements_met: false });

    expect(other.variants).toEqual([
      {
        variant_id: "offering:C08",
        entry_requirements_met: true,
        tuition_fee_loan: {
          amount: null,
          eligibility: "potentially_eligible",
          application: "not_applied",
        },
      },
      { variant_id: "offering:C11", entry_requirements_met: false },
    ]);
  });

  it("leaves an option out of the route search, or brings it back, once each", () => {
    const inputs = submitted(stored);

    expect(withExcluded(inputs, "offering:C10", true).excluded_variants).toEqual([
      "offering:C04~instalments",
      "offering:C10",
    ]);
    expect(withExcluded(inputs, "offering:C04~instalments", true).excluded_variants).toEqual([
      "offering:C04~instalments",
    ]);
    expect(withExcluded(inputs, "offering:C04~instalments", false).excluded_variants).toEqual([]);
  });
});
