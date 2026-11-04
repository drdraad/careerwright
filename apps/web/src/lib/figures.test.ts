// A figure the person types for a fact an option lacks (Task 12b, OPTN-13): read into the API's
// shape exactly, or refused with a reason, never guessed and never zero by default.
import { describe, expect, it } from "vitest";
import { readFigure } from "./figures";

describe("[OPTN-13] a typed figure becomes the API's value, or a stated reason", () => {
  it("reads hours a week as whole hours from 0 to 168", () => {
    expect(readFigure("weekly_hours", "12")).toEqual({
      ok: true,
      value: { fact: "weekly_hours", hours: 12 },
    });
    expect(readFigure("weekly_hours", " 0 ")).toEqual({
      ok: true,
      value: { fact: "weekly_hours", hours: 0 },
    });
    for (const typed of ["", "169", "7.5", "ten", "-1"]) {
      expect(readFigure("weekly_hours", typed)).toEqual({
        ok: false,
        problem: "Enter whole hours from 0 to 168.",
      });
    }
  });

  it("reads a cost as integer pence, never through a float", () => {
    expect(readFigure("cost", "£30,150.50")).toEqual({
      ok: true,
      value: { fact: "cost", money: { minor_units: 3015050, currency: "GBP" } },
    });
    expect(readFigure("cost", "")).toEqual({ ok: false, problem: "Enter an amount." });
    expect(readFigure("cost", "12.345")).toEqual({
      ok: false,
      problem: "Use at most two decimal places (pence).",
    });
  });

  it("reads a start as a real day the person gave, or one of the page's intake months", () => {
    expect(readFigure("start_date", "2027-01-04")).toEqual({
      ok: true,
      value: { fact: "start_date", on: "2027-01-04", basis: "own_figure" },
    });
    expect(readFigure("start_date", "2026-02-01", "stated_intake")).toEqual({
      ok: true,
      value: { fact: "start_date", on: "2026-02-01", basis: "stated_intake" },
    });
    expect(readFigure("finish_date", "2027-02-30")).toEqual({
      ok: false,
      problem: "Choose a date.",
    });
  });
});
