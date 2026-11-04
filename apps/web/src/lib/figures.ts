// A figure the person types for a fact an option lacks (Task 12b, OPTN-13; ADR 0013's Task 12b
// amendment): a start, a finish, hours a week or the whole cost, read into the API's shape
// exactly or refused with a reason. Shared by Options (the checkpoint's boxes) and Routes.
import type { MissingFact, Money, StartBasis } from "@/generated/api";
import { isDayInput } from "./dates";
import { parseMoneyInput } from "./money";
import { problemText } from "./profile";

/** The facts a person can supply as their own figure; the others are answers, not figures. */
export type FigureFact = Extract<
  MissingFact,
  "start_date" | "finish_date" | "weekly_hours" | "cost"
>;

export const FIGURE_FACTS: readonly FigureFact[] = [
  "start_date",
  "finish_date",
  "weekly_hours",
  "cost",
];

export const isFigureFact = (fact: MissingFact): fact is FigureFact =>
  (FIGURE_FACTS as readonly string[]).includes(fact);

export type Figure =
  | { fact: "start_date"; on: string; basis: StartBasis }
  | { fact: "finish_date"; on: string }
  | { fact: "weekly_hours"; hours: number }
  | { fact: "cost"; money: Money };

export type ReadFigure = { ok: true; value: Figure } | { ok: false; problem: string };

const MAX_HOURS = 168;

/** `basis`: for a start, whether the person chose one of the page's intakes or gave a day. */
export function readFigure(
  fact: FigureFact,
  typed: string,
  basis: StartBasis = "own_figure",
): ReadFigure {
  const text = typed.trim();
  switch (fact) {
    case "weekly_hours": {
      const hours = Number(text);
      return /^\d+$/.test(text) && hours <= MAX_HOURS
        ? { ok: true, value: { fact, hours } }
        : { ok: false, problem: `Enter whole hours from 0 to ${MAX_HOURS}.` };
    }
    case "cost": {
      const parsed = parseMoneyInput(text, "GBP");
      return parsed.ok
        ? { ok: true, value: { fact, money: parsed.money } }
        : { ok: false, problem: problemText({ kind: "money", reason: parsed.reason }) };
    }
    case "start_date":
      return isDayInput(text)
        ? { ok: true, value: { fact, on: text, basis } }
        : { ok: false, problem: "Choose a date." };
    case "finish_date":
      return isDayInput(text)
        ? { ok: true, value: { fact, on: text } }
        : { ok: false, problem: "Choose a date." };
  }
}
