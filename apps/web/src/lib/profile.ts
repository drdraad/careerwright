// Reading and editing the profile document (generated types only). A missing answer is shown
// in words by its state, never as a zero, a blank or a guess (spec section 3, STATE-08).
import type {
  FieldEdit,
  FieldState,
  Money,
  PayPeriod,
  ProfileDocument,
  ProfileInput,
  SalaryFloor,
} from "@/generated/api";
import { listLimit } from "./bounds";
import { formatMoney, type MoneyInputProblem, parseMoneyInput } from "./money";
import { FIELD_STATE, PAY_PERIOD, PROFILE_FIELDS, type ProfileFieldName } from "./vocabulary";

type AnyField = ProfileDocument[ProfileFieldName];
type AnswerValue = NonNullable<AnyField["value"]>;

function isSalary(value: AnswerValue): value is SalaryFloor {
  return typeof value === "object" && !Array.isArray(value) && "period" in value;
}

/** A salary floor as the person gave it: never annualised, always gross. */
export function describeSalary(floor: SalaryFloor): string {
  return `${formatMoney(floor.amount)} ${PAY_PERIOD[floor.period]}, before tax`;
}

/** An answer's value as text (a proposal's value reads the same way). */
export function describeValue(value: AnswerValue): string {
  if (Array.isArray(value)) return value.join(", ");
  if (isSalary(value)) return describeSalary(value);
  if (typeof value === "object") return formatMoney(value as Money);
  if (typeof value === "number") return `${value} hours a week`;
  return value;
}

/** The field as text: its value when answered, otherwise what its state means. */
export function describeField(field: AnyField): string {
  if (field.state !== "provided" || field.value === null || field.value === undefined) {
    return FIELD_STATE[field.state];
  }
  return describeValue(field.value);
}

/** Editable form state: text for every value, so typing never loses what was typed. */
export type FieldDraft = {
  state: FieldState;
  text: string;
  items: string[];
  /** A salary floor's period; a year unless the person chooses another. */
  period?: PayPeriod;
};
export type ProfileDraft = Record<ProfileFieldName, FieldDraft>;

function textOf(value: AnyField["value"]): string {
  if (value === null || value === undefined || Array.isArray(value)) return "";
  if (typeof value === "object") {
    const money = isSalary(value) ? value.amount : (value as Money);
    return formatMoney(money).replace(/^£/, "");
  }
  return String(value);
}

export function fieldDraft(field: AnyField): FieldDraft {
  const value = field.value;
  const provided = field.state === "provided";
  const draft: FieldDraft = {
    state: field.state,
    text: provided ? textOf(value) : "",
    items: Array.isArray(value) ? [...value] : [],
  };
  if (provided && value !== null && value !== undefined && isSalary(value)) {
    draft.period = value.period;
  }
  return draft;
}

export function draftFrom(document: ProfileDocument): ProfileDraft {
  const draft = {} as ProfileDraft;
  for (const name of Object.keys(PROFILE_FIELDS) as ProfileFieldName[]) {
    draft[name] = fieldDraft(document[name]);
  }
  return draft;
}

export type FieldProblem =
  | { kind: "required" }
  | { kind: "money"; reason: MoneyInputProblem }
  | { kind: "hours" }
  | { kind: "too_many"; limit: number }
  | { kind: "duplicate" };

export type DraftResult =
  | { ok: true; input: ProfileInput }
  | { ok: false; problems: Partial<Record<ProfileFieldName, FieldProblem>> };

/** One field's API input, or why it cannot be sent as typed. */
export type Read<T> = { ok: true; input: T } | { ok: false; problem: FieldProblem };
export type FieldAnswer = FieldEdit["answer"];

function unanswered(field: FieldDraft): { state: Exclude<FieldState, "provided"> } | null {
  return field.state === "provided" ? null : { state: field.state };
}

function readText(field: FieldDraft): Read<ProfileInput["current_role"]> {
  const other = unanswered(field);
  if (other !== null) return { ok: true, input: other };
  const text = field.text.trim();
  if (text === "") return { ok: false, problem: { kind: "required" } };
  return { ok: true, input: { state: "provided", value: text } };
}

function readList(field: FieldDraft, limit: number): Read<ProfileInput["cities"]> {
  const other = unanswered(field);
  if (other !== null) return { ok: true, input: other };
  const items = field.items.map((item) => item.trim()).filter((item) => item !== "");
  const folded = items.map((item) => item.toLocaleLowerCase("en-GB"));
  if (items.length === 0) return { ok: false, problem: { kind: "required" } };
  if (items.length > limit) {
    return { ok: false, problem: { kind: "too_many", limit } };
  }
  if (new Set(folded).size !== folded.length) return { ok: false, problem: { kind: "duplicate" } };
  return { ok: true, input: { state: "provided", value: items } };
}

function readHours(field: FieldDraft): Read<ProfileInput["weekly_study_hours"]> {
  const other = unanswered(field);
  if (other !== null) return { ok: true, input: other };
  const text = field.text.trim();
  if (text === "") return { ok: false, problem: { kind: "required" } };
  const hours = Number(text);
  if (!/^\d+(\.\d+)?$/.test(text) || hours > 168) return { ok: false, problem: { kind: "hours" } };
  return { ok: true, input: { state: "provided", value: hours } };
}

function readMoney(field: FieldDraft): Read<ProfileInput["direct_spend_cap"]> {
  const other = unanswered(field);
  if (other !== null) return { ok: true, input: other };
  const parsed = parseMoneyInput(field.text, "GBP");
  if (parsed.ok) return { ok: true, input: { state: "provided", value: parsed.money } };
  return {
    ok: false,
    problem:
      parsed.reason === "empty" ? { kind: "required" } : { kind: "money", reason: parsed.reason },
  };
}

function readSalary(field: FieldDraft): Read<ProfileInput["minimum_salary"]> {
  const other = unanswered(field);
  if (other !== null) return { ok: true, input: other };
  const parsed = parseMoneyInput(field.text, "GBP");
  if (parsed.ok) {
    return {
      ok: true,
      input: {
        state: "provided",
        value: { amount: parsed.money, period: field.period ?? "year" },
      },
    };
  }
  return {
    ok: false,
    problem:
      parsed.reason === "empty" ? { kind: "required" } : { kind: "money", reason: parsed.reason },
  };
}

/** One field's answer as the API takes it, or why it cannot be sent as typed. */
export function readField(name: ProfileFieldName, draft: FieldDraft): Read<FieldAnswer> {
  switch (PROFILE_FIELDS[name].kind) {
    case "list":
      return readList(draft, listLimit(name));
    case "salary":
      return readSalary(draft);
    case "hours":
      return readHours(draft);
    case "money":
      return readMoney(draft);
    default:
      return readText(draft);
  }
}

/** Turns the draft into the API's input, or names each field that cannot be sent as typed. */
export function inputFrom(draft: ProfileDraft): DraftResult {
  const list = (name: ProfileFieldName) => readList(draft[name], listLimit(name));
  const read = {
    preferred_name: readText(draft.preferred_name),
    current_role: readText(draft.current_role),
    cities: list("cities"),
    target_titles: list("target_titles"),
    weekly_study_hours: readHours(draft.weekly_study_hours),
    direct_spend_cap: readMoney(draft.direct_spend_cap),
    monthly_payment_cap: readMoney(draft.monthly_payment_cap),
    enjoyed_tasks: list("enjoyed_tasks"),
    confident_tasks: list("confident_tasks"),
    evidenced_tasks: list("evidenced_tasks"),
    work_style: list("work_style"),
    minimum_salary: readSalary(draft.minimum_salary),
  };
  const problems: Partial<Record<ProfileFieldName, FieldProblem>> = {};
  for (const name of Object.keys(read) as ProfileFieldName[]) {
    const field = read[name];
    if (!field.ok) problems[name] = field.problem;
  }
  if (
    !read.preferred_name.ok ||
    !read.current_role.ok ||
    !read.cities.ok ||
    !read.target_titles.ok ||
    !read.weekly_study_hours.ok ||
    !read.direct_spend_cap.ok ||
    !read.monthly_payment_cap.ok ||
    !read.enjoyed_tasks.ok ||
    !read.confident_tasks.ok ||
    !read.evidenced_tasks.ok ||
    !read.work_style.ok ||
    !read.minimum_salary.ok
  ) {
    return { ok: false, problems };
  }
  const input: ProfileInput = {
    preferred_name: read.preferred_name.input,
    current_role: read.current_role.input,
    cities: read.cities.input,
    target_titles: read.target_titles.input,
    weekly_study_hours: read.weekly_study_hours.input,
    direct_spend_cap: read.direct_spend_cap.input,
    monthly_payment_cap: read.monthly_payment_cap.input,
    enjoyed_tasks: read.enjoyed_tasks.input,
    confident_tasks: read.confident_tasks.input,
    evidenced_tasks: read.evidenced_tasks.input,
    work_style: read.work_style.input,
    minimum_salary: read.minimum_salary.input,
  };
  return { ok: true, input };
}

/** The whole document as input, so one answer can be changed and the rest sent as stored. */
export function inputOf(document: ProfileDocument): ProfileInput {
  const result = inputFrom(draftFrom(document));
  if (!result.ok) throw new Error("a stored profile is always valid input");
  return result.input;
}

export type Rebased = {
  draft: ProfileDraft;
  /** Fields the newer version changed. */
  changedThere: ProfileFieldName[];
  /** Fields the person edited that the newer version changed differently: their edit is kept. */
  conflicts: ProfileFieldName[];
};

/**
 * After a stale save (409): a draft on the newer version. Answers the person did not touch
 * take the newer version's values, so saving never reverts them; the person's edits stay;
 * a field both changed to different answers is named as a conflict. Nothing is merged
 * silently.
 */
export function rebaseDraft(
  draft: ProfileDraft,
  base: ProfileDocument,
  latest: ProfileDocument,
): Rebased {
  const before = draftFrom(base);
  const after = draftFrom(latest);
  const changedThere = changedFields(base, latest);
  const next = { ...after };
  const conflicts: ProfileFieldName[] = [];
  for (const name of Object.keys(PROFILE_FIELDS) as ProfileFieldName[]) {
    const edit = JSON.stringify(draft[name]);
    // Untouched, or edited to exactly what the newer version has: take the newer answer.
    if (edit === JSON.stringify(before[name]) || edit === JSON.stringify(after[name])) continue;
    next[name] = draft[name];
    if (changedThere.includes(name)) conflicts.push(name);
  }
  return { draft: next, changedThere, conflicts };
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
