import { describe, expect, it } from "vitest";
import { formatMoney, formatSignedMoney, parseMoneyInput } from "./money";

describe("[API-04] economic cost is signed: a gain shows with a minus sign, never as zero", () => {
  it.each([
    [60000, "£600"],
    [0, "£0"],
    [-50000, "−£500"],
    [-5, "−£0.05"],
  ])("formats %i minor units as %s", (minor, shown) => {
    expect(formatSignedMoney({ minor_units: minor, currency: "GBP" })).toBe(shown);
  });
});

describe("[API-04] money is shown from integer minor units, never through floats", () => {
  it.each([
    [0, "£0"],
    [150000, "£1,500"],
    [150050, "£1,500.50"],
    [5, "£0.05"],
    [485000, "£4,850"],
    [123456789012, "£1,234,567,890.12"],
  ])("formats %i minor units as %s", (minor, shown) => {
    expect(formatMoney({ minor_units: minor, currency: "GBP" })).toBe(shown);
  });

  it("keeps exactness beyond float-safe decimal arithmetic", () => {
    // 0.1 + 0.2 style errors would show up here if pounds were computed as floats.
    expect(formatMoney({ minor_units: 900719925474099, currency: "GBP" })).toBe(
      "£9,007,199,254,740.99",
    );
  });
});

describe("[API-04] typed amounts become integer minor units or a stated reason", () => {
  it.each([
    ["1500", 150000],
    ["1,500", 150000],
    ["£1,500.50", 150050],
    ["  £ 1500.5 ", 150050],
    ["0", 0],
    ["0.07", 7],
    [".5", 50],
  ])("reads %j as %i", (text, minor) => {
    expect(parseMoneyInput(text, "GBP")).toEqual({
      ok: true,
      money: { minor_units: minor, currency: "GBP" },
    });
  });

  it.each([
    ["", "empty"],
    ["   ", "empty"],
    ["-5", "negative"],
    ["−5", "negative"],
    ["12.345", "too_precise"],
    ["1.2.3", "not_a_number"],
    ["abc", "not_a_number"],
    ["1e5", "not_a_number"],
    ["12,34", "not_a_number"],
    ["99999999999999999", "too_large"],
  ])("rejects %j as %s", (text, reason) => {
    expect(parseMoneyInput(text, "GBP")).toEqual({ ok: false, reason });
  });

  it("round-trips every formatted amount", () => {
    for (const minor of [0, 1, 99, 100, 101, 150000, 485000, 999999999]) {
      const shown = formatMoney({ minor_units: minor, currency: "GBP" });
      expect(parseMoneyInput(shown, "GBP")).toEqual({
        ok: true,
        money: { minor_units: minor, currency: "GBP" },
      });
    }
  });
});
