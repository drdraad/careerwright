import { describe, expect, it } from "vitest";
import type { ProfileDocument } from "@/generated/api";
import { changedFields, describeField, draftFrom, inputFrom, rebaseDraft } from "./profile";

const SOURCE = "6f1d3c2a-0000-4000-8000-000000000001";

function document(overrides: Partial<ProfileDocument> = {}): ProfileDocument {
  return {
    schema_version: "1",
    preferred_name: { state: "unasked", value: null, source_ref_id: null },
    current_role: { state: "unknown", value: null, source_ref_id: SOURCE },
    cities: { state: "provided", value: ["Manchester"], source_ref_id: SOURCE },
    target_titles: { state: "provided", value: ["Data quality analyst"], source_ref_id: SOURCE },
    weekly_study_hours: { state: "skipped", value: null, source_ref_id: SOURCE },
    direct_spend_cap: {
      state: "provided",
      value: { minor_units: 150000, currency: "GBP" },
      source_ref_id: SOURCE,
    },
    monthly_payment_cap: { state: "prefer_not_to_say", value: null, source_ref_id: SOURCE },
    ...overrides,
  };
}

describe("[API-04] a missing answer reads as its state, never as zero or blank", () => {
  it.each([
    ["preferred_name", "Not asked yet"],
    ["current_role", "Unknown"],
    ["weekly_study_hours", "Skipped"],
    ["monthly_payment_cap", "Prefer not to say"],
    ["direct_spend_cap", "£1,500"],
    ["cities", "Manchester"],
  ] as const)("%s reads %j", (name, text) => {
    expect(describeField(document()[name])).toBe(text);
  });
});

describe("[API-04] the profile form sends exactly what was answered, in integer money", () => {
  it("round-trips a stored document into the same input", () => {
    expect(inputFrom(draftFrom(document()))).toEqual({
      ok: true,
      input: {
        preferred_name: { state: "unasked" },
        current_role: { state: "unknown" },
        cities: { state: "provided", value: ["Manchester"] },
        target_titles: { state: "provided", value: ["Data quality analyst"] },
        weekly_study_hours: { state: "skipped" },
        direct_spend_cap: { state: "provided", value: { minor_units: 150000, currency: "GBP" } },
        monthly_payment_cap: { state: "prefer_not_to_say" },
      },
    });
  });

  it("reads typed pounds and pence as integer minor units", () => {
    const draft = draftFrom(document());
    draft.monthly_payment_cap = { state: "provided", text: "1,250.75", items: [] };
    draft.weekly_study_hours = { state: "provided", text: "7.5", items: [] };

    const result = inputFrom(draft);

    expect(result.ok && result.input.monthly_payment_cap).toEqual({
      state: "provided",
      value: { minor_units: 125075, currency: "GBP" },
    });
    expect(result.ok && result.input.weekly_study_hours).toEqual({ state: "provided", value: 7.5 });
  });

  it("names each field that cannot be sent: empty answers, bad amounts, limits, repeats", () => {
    const draft = draftFrom(document());
    draft.current_role = { state: "provided", text: "  ", items: [] };
    draft.direct_spend_cap = { state: "provided", text: "-20", items: [] };
    draft.weekly_study_hours = { state: "provided", text: "200", items: [] };
    draft.cities = { state: "provided", text: "", items: ["Leeds", "York", "Hull", "Bath"] };
    draft.target_titles = { state: "provided", text: "", items: ["Analyst", "analyst "] };

    expect(inputFrom(draft)).toEqual({
      ok: false,
      problems: {
        current_role: { kind: "required" },
        direct_spend_cap: { kind: "money", reason: "negative" },
        weekly_study_hours: { kind: "hours" },
        cities: { kind: "too_many", limit: 3 },
        target_titles: { kind: "duplicate" },
      },
    });
  });

  it("rebases a draft on a newer version: untouched answers follow it, edits stay, clashes are named", () => {
    const older = document();
    const newer = document({
      direct_spend_cap: {
        state: "provided",
        value: { minor_units: 90000, currency: "GBP" },
        source_ref_id: SOURCE,
      },
      current_role: { state: "provided", value: "Analyst", source_ref_id: SOURCE },
    });
    const draft = draftFrom(older);
    draft.cities = { state: "provided", text: "", items: ["Leeds"] };
    draft.current_role = { state: "provided", text: "Data steward", items: [] };

    const rebased = rebaseDraft(draft, older, newer);

    expect(rebased.draft.cities.items).toEqual(["Leeds"]);
    expect(rebased.draft.direct_spend_cap).toEqual({ state: "provided", text: "900", items: [] });
    expect(rebased.draft.current_role.text).toBe("Data steward");
    expect(rebased.changedThere).toEqual(["current_role", "direct_spend_cap"]);
    expect(rebased.conflicts).toEqual(["current_role"]);
  });

  it("lists the fields a newer version changed", () => {
    const newer = document({
      cities: { state: "provided", value: ["Leeds"], source_ref_id: SOURCE },
    });

    expect(changedFields(document(), newer)).toEqual(["cities"]);
  });
});
