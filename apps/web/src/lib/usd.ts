// Model spending in US dollars, because that is what Meta bills (spec section 16). The API
// states it in integer nano-USD (one billionth of a dollar); everything here is integer-only.
// No pounds figure is shown: Careerwright has no pinned exchange rate.

const NANO_PER_CENT = 10_000_000;
const CENTS_PER_DOLLAR = 100;
const grouping = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0, useGrouping: true });

/** "4.20" (no symbol), to the nearest cent, half up: how a limit reads in a form field. */
export function usdAmount(nanoUsd: number): string {
  const cents = Math.floor((nanoUsd + NANO_PER_CENT / 2) / NANO_PER_CENT);
  const fraction = cents % CENTS_PER_DOLLAR;
  const whole = (cents - fraction) / CENTS_PER_DOLLAR;
  return `${grouping.format(whole)}.${String(fraction).padStart(2, "0")}`;
}

/** "$4.20", to the nearest cent; "less than $0.01" for an amount above zero that rounds to 0. */
export function formatUsd(nanoUsd: number): string {
  if (nanoUsd > 0 && nanoUsd < NANO_PER_CENT / 2) return "less than $0.01";
  return `$${usdAmount(nanoUsd)}`;
}

export type UsdInputProblem = "empty" | "negative" | "not_a_number" | "too_precise" | "too_large";

export type ParsedUsd = { ok: true; nanoUsd: number } | { ok: false; reason: UsdInputProblem };

// Optional thousands separators in groups of three, then an optional fraction.
const AMOUNT = /^(?:(\d{1,3}(?:,\d{3})+)|(\d*))(?:\.(\d*))?$/;

/** A typed limit in dollars and cents ("5", "$0.75", "1,000.50") as integer nano-USD. */
export function parseUsdInput(text: string): ParsedUsd {
  const trimmed = text.replaceAll(/\s/g, "");
  if (trimmed === "") return { ok: false, reason: "empty" };
  if (/^[-−]/.test(trimmed)) return { ok: false, reason: "negative" };
  const match = AMOUNT.exec(trimmed.startsWith("$") ? trimmed.slice(1) : trimmed);
  if (match === null) return { ok: false, reason: "not_a_number" };
  const wholeText = (match[1] ?? match[2] ?? "").replaceAll(",", "");
  const fractionText = match[3] ?? "";
  if (wholeText === "" && fractionText === "") return { ok: false, reason: "not_a_number" };
  if (fractionText.length > 2) return { ok: false, reason: "too_precise" };
  const cents = BigInt(wholeText || "0") * 100n + BigInt(fractionText.padEnd(2, "0") || "0");
  const nano = cents * BigInt(NANO_PER_CENT);
  if (nano > BigInt(Number.MAX_SAFE_INTEGER)) return { ok: false, reason: "too_large" };
  return { ok: true, nanoUsd: Number(nano) };
}
