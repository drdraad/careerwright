// The world shows only what the API computed (plan section 4, ADR 0014 decision 4): the
// person's light is lit by an answer, destinations are the targets they chose, and nothing is
// guessed or ranked.
import { describe, expect, it } from "vitest";
import type { ProfileDocument, ProfileOut } from "@/generated/api";
import { EMPTY_WORLD, worldFromProfile } from "./model";

const unasked = { state: "unasked", value: null, source_ref_id: null } as const;

function profile(changes: Partial<ProfileDocument>, version = 1): ProfileOut {
  return {
    workspace_id: "w1",
    version,
    created_by: null,
    created_at: "2027-01-01T00:00:00Z",
    document: {
      schema_version: "3",
      preferred_name: unasked,
      current_role: unasked,
      cities: unasked,
      target_titles: unasked,
      weekly_study_hours: unasked,
      direct_spend_cap: unasked,
      monthly_payment_cap: unasked,
      enjoyed_tasks: unasked,
      confident_tasks: unasked,
      evidenced_tasks: unasked,
      work_style: unasked,
      minimum_salary: unasked,
      ...changes,
    },
  };
}

describe("[UI-04] the world draws what the person has said, and nothing else", () => {
  it("waits, dark, with one unlit light while nothing is loaded or answered", () => {
    expect(worldFromProfile(undefined)).toEqual(EMPTY_WORLD);
    expect(worldFromProfile(profile({}, 0))).toEqual(EMPTY_WORLD);
  });

  it.each([
    ["an answer", { state: "provided", value: "Barista", source_ref_id: null }],
    ["Unknown", { state: "unknown", value: null, source_ref_id: null }],
    ["Skipped", { state: "skipped", value: null, source_ref_id: null }],
    ["Prefer not to say", { state: "prefer_not_to_say", value: null, source_ref_id: null }],
  ] as const)("lights the person's light once they give %s", (_, field) => {
    expect(worldFromProfile(profile({ current_role: field })).lit).toBe(true);
  });

  it("makes the chosen targets its destinations, in title order, each once", () => {
    const world = worldFromProfile(
      profile({
        target_titles: {
          state: "provided",
          value: ["Statistician", " Data quality analyst", "Statistician", "Archivist"],
          source_ref_id: null,
        },
      }),
    );
    expect(world.destinations.map((d) => d.title)).toEqual([
      "Archivist",
      "Data quality analyst",
      "Statistician",
    ]);
    // Nothing is known yet about what the person shares with them.
    expect(world.destinations.every((d) => d.shared.length === 0)).toBe(true);
  });

  it.each(["unknown", "skipped", "prefer_not_to_say"] as const)(
    "draws no destination for a target answered %s: never a guess",
    (state) => {
      const world = worldFromProfile(
        profile({ target_titles: { state, value: null, source_ref_id: null } }),
      );
      expect(world.destinations).toEqual([]);
      expect(world.lit).toBe(true);
    },
  );

  it("computes no skills and no openings: they arrive with the chapters that compute them", () => {
    const world = worldFromProfile(
      profile({
        current_role: { state: "provided", value: "Data analyst", source_ref_id: null },
        target_titles: { state: "provided", value: ["Statistician"], source_ref_id: null },
      }),
    );
    expect(world.skills).toEqual([]);
    expect(world.openings).toBe(0);
  });
});
