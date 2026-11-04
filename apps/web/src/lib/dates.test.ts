import { describe, expect, it } from "vitest";
import { formatDay, formatMonth, isDayInput } from "./dates";

describe("[API-04] a date from the API reads in plain English, never shifted by a time zone", () => {
  it.each([
    ["2027-09-01", "1 September 2027"],
    ["2030-08-31", "31 August 2030"],
    ["2026-02-01", "1 February 2026"],
    // A stored timestamp's day is the day it names, whatever the browser's time zone.
    ["2026-11-03T23:30:00Z", "3 November 2026"],
  ])("reads %s as %s", (iso, shown) => {
    expect(formatDay(iso)).toBe(shown);
  });

  it.each([
    ["2027-09-01", "September 2027"],
    ["2026-03-01", "March 2026"],
  ])("reads the month of %s as %s", (iso, shown) => {
    expect(formatMonth(iso)).toBe(shown);
  });

  it("refuses what is not a calendar date, rather than showing a wrong one", () => {
    expect(() => formatDay("2027-13-01")).toThrow();
    expect(() => formatDay("1 September")).toThrow();
  });
});

describe("a typed day is a real calendar date or it is refused", () => {
  it.each(["2027-01-04", "2028-02-29"])("accepts %s", (text) => {
    expect(isDayInput(text)).toBe(true);
  });

  it.each(["", "0000-01-01", "2027-02-30", "2027-1-4", "04/01/2027", "2027-02-29"])(
    "refuses %j",
    (text) => {
      expect(isDayInput(text)).toBe(false);
    },
  );
});
