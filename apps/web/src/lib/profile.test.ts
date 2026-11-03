import { describe, expect, it } from "vitest";
import type { ProfileDocument } from "@/generated/api";
import openapi from "@/generated/openapi.json";
import { listLimit } from "./bounds";
import {
  changedFields,
  describeField,
  draftFrom,
  inputFrom,
  isStateCode,
  rebaseDraft,
} from "./profile";
import { PROFILE_FIELDS, type ProfileFieldName } from "./vocabulary";

const SOURCE = "6f1d3c2a-0000-4000-8000-000000000001";

function document(overrides: Partial<ProfileDocument> = {}): ProfileDocument {
  return {
    schema_version: "5",
    work_status: { state: "unasked", value: null, source_ref_id: null },
    qualifications: { state: "unasked", value: null, source_ref_id: null },
    disliked_tasks: { state: "unasked", value: null, source_ref_id: null },
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
    work_style: { state: "unasked", value: null, source_ref_id: null },
    minimum_salary: { state: "unasked", value: null, source_ref_id: null },
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

  // Task W2F slice E (the product owner's re-test): a role saved as the text "no_job_yet"
  // showed the code itself. A state's code is never shown as a value.
  it("reads a state's code saved as a value in the state's words", () => {
    const saved = document({
      current_role: { state: "provided", value: "no_job_yet", source_ref_id: SOURCE },
      enjoyed_tasks: {
        state: "provided",
        value: ["fixing bikes", "Prefer-not-to-say"],
        source_ref_id: SOURCE,
      },
    });

    expect(describeField(saved.current_role, "current_role")).toBe("I haven't had a job yet");
    expect(describeField(saved.enjoyed_tasks, "enjoyed_tasks")).toBe(
      "fixing bikes, Prefer not to say",
    );
    expect(isStateCode("No job yet")).toBe(true);
    expect(isStateCode("Unknown Soldier tour guide")).toBe(false);
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
        work_style: { state: "unasked" },
        minimum_salary: { state: "unasked" },
        work_status: { state: "unasked" },
        qualifications: { state: "unasked" },
        disliked_tasks: { state: "unasked" },
      },
    });
  });

  it("[PROF-13][STATE-11] round-trips no job yet, what the person is doing now and an expected qualification", () => {
    const stored = document({
      current_role: { state: "no_job_yet", value: null, source_ref_id: SOURCE },
      work_status: { state: "provided", value: "in_education_or_training", source_ref_id: SOURCE },
      qualifications: {
        state: "provided",
        value: [
          { name: "GCSE maths", status: "achieved" },
          { name: "A-level biology", status: "expected" },
        ],
        source_ref_id: SOURCE,
      },
    });

    const result = inputFrom(draftFrom(stored));

    expect(result.ok && result.input.current_role).toEqual({ state: "no_job_yet" });
    expect(result.ok && result.input.work_status).toEqual({
      state: "provided",
      value: "in_education_or_training",
    });
    expect(result.ok && result.input.qualifications).toEqual({
      state: "provided",
      value: [
        { name: "GCSE maths", status: "achieved" },
        { name: "A-level biology", status: "expected" },
      ],
    });
    // In words: an expected qualification always says so, never reads as achieved.
    expect(describeField(stored.current_role, "current_role")).toBe("I haven't had a job yet");
    expect(describeField(stored.work_status, "work_status")).toBe("In education or training");
    expect(describeField(stored.qualifications, "qualifications")).toBe(
      "GCSE maths (achieved), A-level biology (expected, not achieved yet)",
    );
  });

  it("[PROF-04] sends a salary floor as gross pounds with its period, never converted", () => {
    const floor = {
      amount: { minor_units: 1250, currency: "GBP" as const },
      period: "hour" as const,
    };
    const stored = document({
      minimum_salary: { state: "provided", value: floor, source_ref_id: SOURCE },
    });

    const draft = draftFrom(stored);
    const result = inputFrom(draft);

    expect(draft.minimum_salary).toEqual({
      state: "provided",
      text: "12.50",
      items: [],
      period: "hour",
    });
    expect(result.ok && result.input.minimum_salary).toEqual({ state: "provided", value: floor });
    expect(describeField(stored.minimum_salary)).toBe("£12.50 an hour, before tax");
    draft.minimum_salary = { state: "provided", text: "28,000", items: [] };
    const yearly = inputFrom(draft);
    expect(yearly.ok && yearly.input.minimum_salary).toEqual({
      state: "provided",
      value: { amount: { minor_units: 2_800_000, currency: "GBP" }, period: "year" },
    });
    draft.minimum_salary = { state: "unknown", text: "", items: [] };
    const unknown = inputFrom(draft);
    expect(unknown.ok && unknown.input.minimum_salary).toEqual({ state: "unknown" });
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
      "work_style",
      "qualifications", // Task 6f
      "disliked_tasks", // Task W2F
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
