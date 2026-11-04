import { describe, expect, it } from "vitest";
import { comparatorWords, findingWords, ROUTE_LEAD, ROUTE_QUALIFICATION } from "./routeWords";

describe("[VIS2-01][API-04] route results use the solver's facts in plain words", () => {
  it("keeps an incomplete search distinct from a complete search that found no route", () => {
    expect(ROUTE_LEAD.none_found_before_limit).toContain("before the search limit");
    expect(ROUTE_LEAD.no_route_in_bounded_model).toContain("within this monthly model");
    expect(ROUTE_LEAD.longer_than_model).toContain("longer");
  });

  it("qualifies routes using a person's unchecked figure or an unapproved loan", () => {
    expect(ROUTE_QUALIFICATION.supplied_figures).toContain("not been checked");
    expect(ROUTE_QUALIFICATION.conditional_loan).toContain("approved");
  });

  it("shows an exact money breach with the person's limit, never a bare code", () => {
    expect(
      findingWords({
        code: "direct_spend_cap",
        kind: "violation",
        amount: 3015000,
        limit: 2000000,
        unit: "minor_units",
      }),
    ).toBe("Above your total spending limit: £30,150 against £20,000.");
    expect(
      findingWords({
        code: "reserve",
        kind: "violation",
        month: "2027-09",
        amount: -50000,
        limit: 0,
        unit: "minor_units",
      }),
    ).toBe("Would leave less cash than you want to keep: −£500 against £0 in September 2027.");
  });

  it("names how a point in a higher layer betters this one", () => {
    expect(
      comparatorWords({
        point_id: 4,
        dominance: "sooner_and_cheaper",
        months_sooner: 2,
        cost_less: { minor_units: 50000, currency: "GBP" },
      }),
    ).toBe("Point 4 is 2 months sooner and £500 cheaper.");
  });
});
