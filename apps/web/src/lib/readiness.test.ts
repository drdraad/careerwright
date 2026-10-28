import { describe, expect, it } from "vitest";
import type { ProfileDocument } from "@/generated/api";
import { chapterNeeds } from "./readiness";

const SRC = "8d1f6f8e-46a1-5c2b-9d0e-3f7a1b2c4d5e";

function document(overrides: Partial<ProfileDocument> = {}): ProfileDocument {
  return {
    schema_version: "1",
    preferred_name: { state: "unasked", value: null, source_ref_id: null },
    current_role: { state: "unasked", value: null, source_ref_id: null },
    cities: { state: "provided", value: ["Manchester"], source_ref_id: SRC },
    target_titles: { state: "provided", value: ["Data quality analyst"], source_ref_id: SRC },
    weekly_study_hours: { state: "unasked", value: null, source_ref_id: null },
    direct_spend_cap: { state: "unknown", value: null, source_ref_id: SRC },
    monthly_payment_cap: { state: "prefer_not_to_say", value: null, source_ref_id: SRC },
    ...overrides,
  };
}

describe("[STATE-08] Unknown, Skipped and Prefer not to say are answers, never a block", () => {
  it("does not block Options on a budget that only makes the result less precise", () => {
    const needs = chapterNeeds(
      "options",
      document({
        weekly_study_hours: { state: "skipped", value: null, source_ref_id: SRC },
      }),
    );

    expect(needs.notAsked).toEqual([]);
    expect(needs.lessPrecise).toEqual([
      "weekly_study_hours",
      "direct_spend_cap",
      "monthly_payment_cap",
    ]);
  });

  it("asks only for what was never asked, and only where the chapter cannot start without it", () => {
    const options = chapterNeeds("options", document());
    const roles = chapterNeeds(
      "roles",
      document({
        cities: { state: "unasked", value: null, source_ref_id: null },
      }),
    );

    expect(options.notAsked).toEqual([]); // weekly hours unasked: less precise, not blocking
    expect(roles.notAsked).toEqual(["cities"]);
  });

  it("treats an Unknown target as an answer that leaves the chapter without a starting point", () => {
    const needs = chapterNeeds(
      "roles",
      document({
        target_titles: { state: "unknown", value: null, source_ref_id: SRC },
      }),
    );

    expect(needs.notAsked).toEqual([]);
    expect(needs.withoutStart).toEqual(["target_titles"]);
  });
});
