// The words the Options and Routes chapters share (Task 12b, screens half; R11 "facts, not
// sentences"): the API sends codes, numbers, money and dates, and this file words each one,
// with exhaustive maps (`Record<Code, …>`) so a new code fails the type check until it has
// words. Unknown is "not known yet", never zero; a loan is a loan to repay, never the person's
// money or support; an age rule is shown, never applied; a figure the person supplied is
// labelled theirs. The sentence rule holds: each line says what Careerwright did or checked, or
// what the person said, never what a list contains.
import type {
  ActionKind,
  AwardState,
  BaselineKind,
  EligibilityStatus,
  EntryFact,
  FeeLoanKind,
  InstrumentKind,
  MissingFact,
  NeedEffect,
  NeededInput,
  RecordState,
  SuppliedFact,
  WorkRights,
} from "@/generated/api";
import { formatDay } from "./dates";
import { formatMoney } from "./money";

/** What the API leaves unknown: never zero, never "none". */
export const NOT_KNOWN = "Not known yet";

/** Each fact the route search may lack for an option: its name mid-sentence, and the box's
 *  question for the ones the person can supply as a figure. */
export const MISSING_FACT: Record<MissingFact, { name: string; ask: string }> = {
  start_date: { name: "start date", ask: "When would you start?" },
  finish_date: { name: "finish date", ask: "When would it finish?" },
  weekly_hours: { name: "hours a week", ask: "How many hours a week would it take?" },
  cost: { name: "cost", ask: "What would you pay for it in total?" },
  entry_confirmation: {
    name: "whether you meet the entry requirements",
    ask: "Do you meet the entry requirements?",
  },
  eligibility_confirmation: {
    name: "whether the funding conditions apply to you",
    ask: "Do the funding conditions apply to you?",
  },
};

/** The missing-fact line: what the route search still lacks for an option; null when nothing. */
export function missingLine(missing: readonly MissingFact[]): string | null {
  if (missing.length === 0) return null;
  return `Not known yet: ${missing.map((fact) => MISSING_FACT[fact].name).join(", ")}.`;
}

/** A fact the person supplied, by name. */
export const SUPPLIED_FACT: Record<SuppliedFact, string> = {
  start_date: "Start date",
  finish_date: "Finish date",
  weekly_hours: "Hours a week",
  cost: "Cost",
};

/** Beside a figure the person supplied: theirs, and nobody has checked it. */
export const suppliedLabel = "your own figure, not checked";

/** A record's review state in a few words (R9: every surface shows it). */
export const RECORD_STATE: Record<RecordState, string> = {
  reviewed: "Reviewed",
  proposed: "Not reviewed yet",
  accepted_assumption: "Your assumption",
};

/** An option's review state and date: reviewed only when its course and its intake both are;
 *  the person's own option is always theirs and never reviewed (OPTN-09). */
export function optionState(option: {
  review_states: readonly RecordState[];
  added_by_person: boolean;
  as_of: string | null;
}): string {
  if (option.added_by_person) {
    const added = option.as_of === null ? "" : ` Added on ${formatDay(option.as_of)}.`;
    return `Your own option, not reviewed.${added}`;
  }
  const reviewed =
    option.review_states.length > 0 && option.review_states.every((state) => state === "reviewed");
  const state = reviewed ? RECORD_STATE.reviewed : RECORD_STATE.proposed;
  const dated = option.as_of === null ? "" : ` From its page on ${formatDay(option.as_of)}.`;
  return `${state}.${dated}`;
}

/** The pack's date, wherever its records appear (R9). */
export function packLine(dated: string): string {
  return `From Careerwright's list of courses and funding in England, dated ${formatDay(dated)}.`;
}

/** What kind of step an option is. */
export const ACTION_KIND: Record<ActionKind, string> = {
  learning: "Course",
  apprenticeship: "Apprenticeship: a paid job with training",
  work: "A job",
  application: "An application",
};

/** A funding scheme's kind: a loan is always a loan to repay. */
export const INSTRUMENT_KIND: Record<InstrumentKind, string> = {
  fee_waiver: "Free or cheaper course fees",
  grant: "A grant",
  bursary: "A bursary",
  employer_support: "Paid by an employer",
  loan: "A loan to repay",
  programme: "A funded programme",
};

/** A loan paid straight to the provider (FUNDING-06): never the person's money, never support. */
export const LOAN_TO_REPAY =
  "Paid straight to the university or college. It's a loan you repay later, not your own money.";

export const FEE_LOAN_KIND: Record<FeeLoanKind, string> = {
  tuition_fee_loan: "Tuition Fee Loan",
  advanced_learner_loan: "Advanced Learner Loan",
};

/** The person's answer about a scheme or a condition: theirs, never computed. */
export const ELIGIBILITY_STATUS: Record<EligibilityStatus, string> = {
  confirmed: "Yes",
  potentially_eligible: "Probably",
  ineligible: "No",
  insufficient_information: "Not sure yet",
};

/** Whether a loan or an award was applied for and decided. */
export const AWARD_STATE: Record<AwardState, string> = {
  not_applied: "Not applied yet",
  applied: "Applied, waiting to hear",
  approved: "Approved",
  refused: "Turned down",
};

/** An entry requirement beside a qualification the person named (Task 6f): an expected one is
 *  met only if they get their grades, so never met here. */
export function entryWords(fact: EntryFact): string {
  return fact.standing === "expected_not_met"
    ? `Your ${fact.qualification}: if you get your grades.`
    : `Your ${fact.qualification}: you said you have it.`;
}

type Shape = Record<string, unknown>;

const isShape = (value: unknown): value is Shape =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const capitalised = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

/** An age rule as its page states it ("Aged 19 or over"). Shown beside its scheme or option,
 *  never applied: Careerwright doesn't know the person's age. */
export function ageRuleWords(value: unknown): string {
  if (typeof value === "string") return capitalised(value);
  if (isShape(value) && typeof value.minimum_age === "number") {
    // The pack states the day as a date ("31 August 2026") or a day of the course.
    const on =
      typeof value.on === "string" ? ` on ${/^\d/.test(value.on) ? "" : "the "}${value.on}` : "";
    return `Aged ${value.minimum_age} or over${on}`;
  }
  return "An age rule on its page";
}

/** Why an age rule is beside its scheme but not used. */
export const AGE_NOT_APPLIED = "Careerwright doesn't know your age, so it hasn't used these.";

const isMoney = (value: unknown): value is { minor_units: number; currency: "GBP" } =>
  isShape(value) && typeof value.minor_units === "number" && value.currency === "GBP";

/** A condition of an option's stated fee, worded from its page by its field. Its shape is the
 *  pack's; one this file can't word reads as a condition on the page, never as raw data. */
export function conditionWords(field: string, value: unknown): string {
  const list = (items: unknown) =>
    Array.isArray(items) && items.every((item) => typeof item === "string")
      ? items.join(", ")
      : null;
  switch (field) {
    case "eligibility_area":
      if (typeof value === "string") return `Where you live or work: ${value}`;
      break;
    case "eligibility_age":
      return `Age: ${ageRuleWords(value).toLowerCase()}`;
    case "eligibility_earnings":
      if (isShape(value) && isMoney(value.below_annual_gross)) {
        const area = typeof value.area === "string" ? ` (${value.area})` : "";
        return `Earnings: under ${formatMoney(value.below_annual_gross)} a year before tax${area}`;
      }
      break;
    case "eligibility_no_other_funded_training":
      if (value === true) return "No other funded training at the same time";
      break;
    case "eligibility_residency": {
      const places = typeof value === "string" ? value : list(value);
      if (places !== null) return `Where you live: ${places}`;
      break;
    }
    case "eligibility_work_rights":
      if (typeof value === "string") return `Right to work: ${value}`;
      break;
  }
  return "A condition on its page";
}

/** What the monthly payment limit counts, as the route check applies it (session 2, D15). */
export function paymentCapMeaning(basis: "payments_and_debt_repayments"): string {
  const counted: Record<typeof basis, string> = {
    payments_and_debt_repayments:
      "every payment for the change, plus any debt repayments that month",
  };
  return `The most you'd pay in any one month: ${counted[basis]}.`;
}

/** The person's own "0 hours, £0" (plan v1.6): a stated figure, never an unknown read as zero. */
export const notWorkingWords = "Not working: 0 hours, £0";

/** Each input a route search needs from the person: its name and what it means. */
export const NEEDED_INPUT: Record<NeededInput, { name: string; meaning: string }> = {
  objective_basis: {
    name: "How to compare routes",
    meaning: "By what you'd pay out, or by the total cost including pay you'd give up.",
  },
  continuation: {
    name: "Your work and pay now",
    meaning: "Your hours a week and take-home pay a month. Every route starts from here.",
  },
  opening_cash: { name: "Money you have now", meaning: "Cash you could put towards a change." },
  living_costs: {
    name: "Living costs a month",
    meaning: "Rent, bills, food and everything else you pay every month.",
  },
  commitments: {
    name: "Other time each week",
    meaning: "Hours you give to caring, travel or a second job.",
  },
  existing_debts: {
    name: "Debts you repay",
    meaning: "What you repay each month on loans or cards.",
  },
  scenario_delay_months: {
    name: "If a start comes late",
    meaning:
      "How many months late Careerwright should also plan for, if a place or funding is late.",
  },
  direct_spend_cap: {
    name: "Total spending limit",
    meaning: "The most you'd spend on the change in total. You set it in You.",
  },
  monthly_payment_cap: {
    name: "Monthly payment limit",
    meaning: "The most you'd pay in any one month. You set it in You.",
  },
  reserve: { name: "Cash to keep", meaning: "The least cash you always want to have left." },
  weekly_availability: {
    name: "Hours you can give",
    meaning: "Hours a week for work, study and your other time together.",
  },
  baseline: {
    name: "If you don't make a change",
    meaning: "What you'd do instead, and your take-home pay a month then.",
  },
  work_rights: {
    name: "Right to work in the UK",
    meaning: "Careerwright doesn't check visas. Without this, no route can be checked as working.",
  },
};

/** What an input still to give does to the route search. */
export const NEED_EFFECT: Record<NeedEffect, string> = {
  blocks_a_solve: "The route search can't start without it.",
  leaves_every_route_unresolved: "Without it, Careerwright can't say whether any route works.",
};

/** What the person would do instead of a change (FIN1-11): never assumed. */
export const BASELINE_KIND: Record<BaselineKind, string> = {
  current_role: "Stay in my current job",
  job_search: "Keep looking for work",
  staying_in_education: "Stay in education",
  other: "Something else",
};

export const WORK_RIGHTS: Record<WorkRights, string> = {
  held: "Yes",
  not_held: "No, I'd need a visa",
  unknown: "Not sure",
};

/** The two ways to compare routes: their words are kept apart (TRACE-01 and DIRECTAI). */
export const OBJECTIVE_BASIS: Record<"direct_spending" | "economic", string> = {
  direct_spending: "What you'd pay out",
  economic: "Total cost, including pay you'd give up",
};
