import { describe, expect, it } from "vitest";
import type { ProfileDocument } from "@/generated/api";
import openapi from "@/generated/openapi.json";
import { listLimit } from "./bounds";
import { changedFields, describeField, draftFrom, inputFrom, rebaseDraft } from "./profile";
import { PROFILE_FIELDS, type ProfileFieldName } from "./vocabulary";

const SOURCE = "6f1d3c2a-0000-4000-8000-000000000001";

function document(overrides: Partial<ProfileDocument> = {}): ProfileDocument {
  return {
    schema_version: "2",
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
    enjoyed_tasks: { state: "unasked", value: null, source_ref_id: null },
    confident_tasks: { state: "unasked", value: null, source_ref_id: null },
    evidenced_tasks: { state: "unasked", value: null, source_ref_id: null },
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
        enjoyed_tasks: { state: "unasked" },
        confident_tasks: { state: "unasked" },
        evidenced_tasks: { state: "unasked" },
      },
    });
  });

  it("bounds each list by its own limit: three work areas, eight tasks", () => {
    const draft = draftFrom(document());
    draft.cities = { state: "provided", text: "", items: ["Leeds", "York", "Bath", "Ely"] };
    draft.enjoyed_tasks = {
      state: "provided",
      text: "",
      items: Array.from({ length: 8 }, (_, n) => `task ${n}`),
    };

    const result = inputFrom(draft);

    expect(result.ok).toBe(false);
    expect(!result.ok && result.problems).toEqual({ cities: { kind: "too_many", limit: 3 } });
  });

  it("takes every list bound from the API's published schema, never its own copy", () => {
    type Schema = {
      $ref?: string;
      type?: string;
      maxItems?: number;
      anyOf?: Schema[];
      properties?: Record<string, Schema>;
    };
    const schemas = openapi.components.schemas as unknown as Record<string, Schema>;
    const fields = schemas.ProfileInput?.properties ?? {};
    const lists = Object.entries(fields).map(([name, field]) => {
      const input = schemas[field.$ref?.split("/").pop() ?? ""];
      const array = input?.properties?.value?.anyOf?.find((option) => option.type === "array");
      return [name, array?.maxItems ?? 0, listLimit(name as ProfileFieldName)];
    });

    expect(lists.filter(([, published]) => published !== 0).map(([name]) => name)).toEqual([
      "cities",
      "target_titles",
      "enjoyed_tasks",
      "confident_tasks",
      "evidenced_tasks",
    ]);
    for (const [name, published, used] of lists) expect([name, used]).toEqual([name, published]);
  });

  it("states a list's bound in its hint from the same published schema", () => {
    for (const name of ["cities", "target_titles"] as const) {
      expect(PROFILE_FIELDS[name].hint).toContain(`Up to ${listLimit(name)} `);
    }
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

  it("names no conflict where the person's edit equals the newer version's answer", () => {
    const older = document();
    const newer = document({
      current_role: { state: "provided", value: "Analyst", source_ref_id: SOURCE },
    });
    const draft = draftFrom(older);
    draft.current_role = { state: "provided", text: "Analyst", items: [] };

    const rebased = rebaseDraft(draft, older, newer);

    expect(rebased.changedThere).toEqual(["current_role"]);
    expect(rebased.conflicts).toEqual([]);
    expect(rebased.draft).toEqual(draftFrom(newer));
  });

  it("lists the fields a newer version changed", () => {
    const newer = document({
      cities: { state: "provided", value: ["Leeds"], source_ref_id: SOURCE },
    });

    expect(changedFields(document(), newer)).toEqual(["cities"]);
  });
});
