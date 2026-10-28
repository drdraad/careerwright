// Reading and editing the profile document (generated types only). A missing answer is shown
// in words by its state, never as a zero, a blank or a guess (spec section 3, STATE-08).
import type { FieldState, Money, ProfileDocument, ProfileInput } from "@/generated/api";
import { formatMoney, type MoneyInputProblem, parseMoneyInput } from "./money";
import { FIELD_STATE, PROFILE_FIELDS, type ProfileFieldName } from "./vocabulary";

type AnyField = ProfileDocument[ProfileFieldName];

/** The field as text: its value when answered, otherwise what its state means. */
export function describeField(field: AnyField): string {
  if (field.state !== "provided" || field.value === null || field.value === undefined) {
    return FIELD_STATE[field.state];
  }
  const value = field.value;
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return formatMoney(value as Money);
  if (typeof value === "number") return `${value} hours a week`;
  return value;
}

/** Editable form state: text for every value, so typing never loses what was typed. */
export type FieldDraft = { state: FieldState; text: string; items: string[] };
export type ProfileDraft = Record<ProfileFieldName, FieldDraft>;

export function draftFrom(document: ProfileDocument): ProfileDraft {
  const draft = {} as ProfileDraft;
  for (const name of Object.keys(PROFILE_FIELDS) as ProfileFieldName[]) {
    const field = document[name];
    const value = field.value;
    draft[name] = {
      state: field.state,
      text:
        field.state !== "provided" || value === null || value === undefined || Array.isArray(value)
          ? ""
          : typeof value === "object"
            ? formatMoney(value as Money).replace(/^£/, "")
            : String(value),
      items: Array.isArray(value) ? [...value] : [],
    };
  }
  return draft;
}

export type FieldProblem =
  | { kind: "required" }
  | { kind: "money"; reason: MoneyInputProblem }
  | { kind: "hours" }
  | { kind: "too_many"; limit: number }
  | { kind: "duplicate" };

export const LIST_LIMIT = 3; // spec BND-1: three cities, three active targets

export type DraftResult =
  | { ok: true; input: ProfileInput }
  | { ok: false; problems: Partial<Record<ProfileFieldName, FieldProblem>> };

/** Turns the draft into the API's input, or names each field that cannot be sent as typed. */
export function inputFrom(draft: ProfileDraft): DraftResult {
  const problems: Partial<Record<ProfileFieldName, FieldProblem>> = {};
  const input = {} as Record<ProfileFieldName, { state: FieldState; value?: unknown }>;
  for (const name of Object.keys(PROFILE_FIELDS) as ProfileFieldName[]) {
    const field = draft[name];
    if (field.state !== "provided") {
      input[name] = { state: field.state };
      continue;
    }
    const kind = PROFILE_FIELDS[name].kind;
    if (kind === "list") {
      const items = field.items.map((item) => item.trim()).filter((item) => item !== "");
      const folded = items.map((item) => item.toLocaleLowerCase("en-GB"));
      if (items.length === 0) problems[name] = { kind: "required" };
      else if (items.length > LIST_LIMIT) problems[name] = { kind: "too_many", limit: LIST_LIMIT };
      else if (new Set(folded).size !== folded.length) problems[name] = { kind: "duplicate" };
      input[name] = { state: "provided", value: items };
    } else if (kind === "money") {
      const parsed = parseMoneyInput(field.text, "GBP");
      if (!parsed.ok)
        problems[name] =
          parsed.reason === "empty"
            ? { kind: "required" }
            : { kind: "money", reason: parsed.reason };
      else input[name] = { state: "provided", value: parsed.money };
    } else if (kind === "hours") {
      const text = field.text.trim();
      const hours = Number(text);
      if (text === "") problems[name] = { kind: "required" };
      else if (!/^\d+(\.\d+)?$/.test(text) || hours > 168) problems[name] = { kind: "hours" };
      else input[name] = { state: "provided", value: hours };
    } else {
      const text = field.text.trim();
      if (text === "") problems[name] = { kind: "required" };
      input[name] = { state: "provided", value: text };
    }
  }
  return Object.keys(problems).length > 0
    ? { ok: false, problems }
    : { ok: true, input: input as unknown as ProfileInput };
}

/** Fields whose answer differs between two stored versions (shown after a stale save). */
export function changedFields(before: ProfileDocument, after: ProfileDocument): ProfileFieldName[] {
  return (Object.keys(PROFILE_FIELDS) as ProfileFieldName[]).filter(
    (name) =>
      before[name].state !== after[name].state ||
      JSON.stringify(before[name].value ?? null) !== JSON.stringify(after[name].value ?? null),
  );
}

export function problemText(problem: FieldProblem): string {
  switch (problem.kind) {
    case "required":
      return "Enter an answer, or choose another option such as Unknown.";
    case "hours":
      return "Enter a number of hours from 0 to 168.";
    case "too_many":
      return `At most ${problem.limit} are supported. Remove one first.`;
    case "duplicate":
      return "The same entry appears twice.";
    case "money":
      return {
        empty: "Enter an amount.",
        negative: "Enter an amount of £0 or more.",
        not_a_number: "Enter an amount in pounds, such as 1,500 or 1500.50.",
        too_precise: "Use at most two decimal places (pence).",
        too_large: "That amount is too large.",
      }[problem.reason];
  }
}
