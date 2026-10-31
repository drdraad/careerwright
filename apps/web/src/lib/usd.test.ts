// Model spending in US dollars from integer nano-USD (MODEL-10): integer-only, never a float.
import { describe, expect, it } from "vitest";
import { formatUsd, parseUsdInput, usdAmount } from "./usd";

describe("[MODEL-10] dollars from nano-USD", () => {
  it("shows cents, rounding half up, and never a spend above zero as $0.00", () => {
    expect(formatUsd(0)).toBe("$0.00");
    expect(formatUsd(115_534_000)).toBe("$0.12");
    expect(formatUsd(5_000_000_000)).toBe("$5.00");
    expect(formatUsd(1_234_565_000_000)).toBe("$1,234.57");
    expect(formatUsd(1_608_000)).toBe("less than $0.01");
    expect(formatUsd(5_000_000)).toBe("$0.01");
    expect(usdAmount(750_000_000)).toBe("0.75");
  });

  it("reads a typed limit in dollars and cents, or says why it can't", () => {
    expect(parseUsdInput("5")).toEqual({ ok: true, nanoUsd: 5_000_000_000 });
    expect(parseUsdInput(" $0.75 ")).toEqual({ ok: true, nanoUsd: 750_000_000 });
    expect(parseUsdInput("1,000.5")).toEqual({ ok: true, nanoUsd: 1_000_500_000_000 });
    expect(parseUsdInput("")).toEqual({ ok: false, reason: "empty" });
    expect(parseUsdInput("-1")).toEqual({ ok: false, reason: "negative" });
    expect(parseUsdInput("five")).toEqual({ ok: false, reason: "not_a_number" });
    expect(parseUsdInput("0.755")).toEqual({ ok: false, reason: "too_precise" });
    expect(parseUsdInput("99999999999")).toEqual({ ok: false, reason: "too_large" });
  });
});
