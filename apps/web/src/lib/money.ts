// Money in integer minor units (Global Constraint 4). Unknown money is null at the API and is
// never passed here as zero: callers show the unknown state instead.
//
// The minor-unit exponent is currency metadata. L0 is GBP only, so the table has one row; the
// arithmetic below is integer-only (quotient and remainder of whole numbers), never float.
import type { Money, SignedMoney } from "@/generated/api";

export type { SignedMoney };

type Currency = Money["currency"];

const MINOR_DIGITS: Record<Currency, number> = { GBP: 2 };
const SYMBOL: Record<Currency, string> = { GBP: "£" };
const grouping = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0, useGrouping: true });

/** "£1,500" for whole amounts, "£1,500.50" otherwise. */
export function formatMoney(money: Money): string {
  const digits = MINOR_DIGITS[money.currency];
  const scale = 10 ** digits;
  const fraction = money.minor_units % scale;
  const whole = (money.minor_units - fraction) / scale;
  const body =
    grouping.format(whole) + (fraction === 0 ? "" : `.${String(fraction).padStart(digits, "0")}`);
  return SYMBOL[money.currency] + body;
}

/**
 * Economic values (spec section 18) are the generated `SignedMoney`: signed, because a route
 * can cost less than the baseline. "−£500" for a negative amount (a true minus sign),
 * otherwise as `formatMoney`.
 */
export function formatSignedMoney(money: SignedMoney): string {
  const magnitude = formatMoney({
    minor_units: Math.abs(money.minor_units),
    currency: money.currency,
  });
  return money.minor_units < 0 ? `−${magnitude}` : magnitude;
}

export type MoneyInputProblem = "empty" | "negative" | "not_a_number" | "too_precise" | "too_large";

export type ParsedMoney = { ok: true; money: Money } | { ok: false; reason: MoneyInputProblem };

// Optional thousands separators in groups of three, then an optional fraction.
const AMOUNT = /^(?:(\d{1,3}(?:,\d{3})+)|(\d*))(?:\.(\d*))?$/;

/** Reads a typed amount ("1,500", "£1500.5") into minor units without floating point. */
export function parseMoneyInput(text: string, currency: Currency): ParsedMoney {
  const symbol = SYMBOL[currency];
  const trimmed = text.replaceAll(/\s/g, "");
  if (trimmed === "") return { ok: false, reason: "empty" };
  if (/^[-−]/.test(trimmed)) return { ok: false, reason: "negative" };
  const unsigned = trimmed.startsWith(symbol) ? trimmed.slice(symbol.length) : trimmed;
  const match = AMOUNT.exec(unsigned);
  if (match === null) return { ok: false, reason: "not_a_number" };
  const wholeText = (match[1] ?? match[2] ?? "").replaceAll(",", "");
  const fractionText = match[3] ?? "";
  if (wholeText === "" && fractionText === "") return { ok: false, reason: "not_a_number" };
  const digits = MINOR_DIGITS[currency];
  if (fractionText.length > digits) return { ok: false, reason: "too_precise" };
  const minor =
    BigInt(wholeText || "0") * 10n ** BigInt(digits) +
    BigInt(fractionText.padEnd(digits, "0") || "0");
  if (minor > BigInt(Number.MAX_SAFE_INTEGER)) return { ok: false, reason: "too_large" };
  return { ok: true, money: { minor_units: Number(minor), currency } };
}
