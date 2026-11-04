// The words the Options and Routes chapters share (Task 12b, screens half): each API fact worded
// once, plain, with unknown never read as zero and a loan never read as the person's money.
import { describe, expect, it } from "vitest";
import {
  ageRuleWords,
  conditionWords,
  entryWords,
  LOAN_TO_REPAY,
  missingLine,
  NEEDED_INPUT,
  notWorkingWords,
  optionState,
  packLine,
  paymentCapMeaning,
  suppliedLabel,
} from "./optionWords";

const gbp = (minor_units: number) => ({ minor_units, currency: "GBP" as const });

describe("[OPTN-13] the missing-fact line names each fact the route search lacks, plainly", () => {
  it("names the figures and the answers still to give, in the order the API lists them", () => {
    expect(missingLine(["start_date", "weekly_hours", "cost", "entry_confirmation"])).toBe(
      "Not known yet: start date, hours a week, cost, whether you meet the entry requirements.",
    );
  });

  it("names the funding conditions as the person's answer still to give", () => {
    expect(missingLine(["eligibility_confirmation"])).toBe(
      "Not known yet: whether the funding conditions apply to you.",
    );
  });

  it("says nothing is missing only when the API lists nothing", () => {
    expect(missingLine([])).toBeNull();
  });
});

describe("[OPTN-09][R9] each option says whether it is reviewed and how old its page is", () => {
  it("reads a reviewed option with its page's date", () => {
    expect(
      optionState({
        review_states: ["reviewed", "reviewed"],
        added_by_person: false,
        as_of: "2026-10-29",
      }),
    ).toBe("Reviewed. From its page on 29 October 2026.");
  });

  it("reads an option as not reviewed while either of its records is proposed", () => {
    expect(
      optionState({
        review_states: ["proposed", "reviewed"],
        added_by_person: false,
        as_of: "2026-11-01",
      }),
    ).toBe("Not reviewed yet. From its page on 1 November 2026.");
  });

  it("does not call an option reviewed without any review records", () => {
    expect(optionState({ review_states: [], added_by_person: false, as_of: null })).toBe(
      "Not reviewed yet.",
    );
  });

  it("reads the person's own option as theirs, never reviewed, with the day they added it", () => {
    expect(
      optionState({
        review_states: ["proposed", "proposed"],
        added_by_person: true,
        as_of: "2026-11-03",
      }),
    ).toBe("Your own option, not reviewed. Added on 3 November 2026.");
  });

  it("dates the list it comes from", () => {
    expect(packLine("2026-11-01")).toBe(
      "From Careerwright's list of courses and funding in England, dated 1 November 2026.",
    );
  });
});

describe("[OPTN-13] a figure the person supplied is labelled theirs and not checked", () => {
  it("labels it beside the fact", () => {
    expect(suppliedLabel).toBe("your own figure, not checked");
  });
});

describe("[FUNDING-06] a tuition fee loan reads as a loan to repay, never as the person's money", () => {
  it("says who it is paid to, that it is repaid, and that it isn't their money", () => {
    expect(LOAN_TO_REPAY).toBe(
      "Paid straight to the university or college. It's a loan you repay later, not your own money.",
    );
  });
});

describe("[PROF-13] an entry requirement read against an expected qualification", () => {
  it("reads 'if you get your grades' for a qualification the person expects, never met", () => {
    expect(
      entryWords({
        qualification: "A levels in Biology, Chemistry and Psychology",
        status: "expected",
        standing: "expected_not_met",
      }),
    ).toBe("Your A levels in Biology, Chemistry and Psychology: if you get your grades.");
  });

  it("reads an achieved qualification as what the person said, not as checked", () => {
    expect(
      entryWords({ qualification: "GCSE maths", status: "achieved", standing: "achieved_stated" }),
    ).toBe("Your GCSE maths: you said you have it.");
  });
});

describe("[OPTN-15] an age rule is shown and never applied to an age Careerwright doesn't know", () => {
  it.each([
    [{ minimum_age: 19 }, "Aged 19 or over"],
    [
      { minimum_age: 19, on: "first day of the course" },
      "Aged 19 or over on the first day of the course",
    ],
    ["under 19 on 31 August 2026", "Under 19 on 31 August 2026"],
  ])("words %j as %j", (value, words) => {
    expect(ageRuleWords(value)).toBe(words);
  });
});

describe("[FUNDING-04] a funding condition is worded from its page, never as a verdict", () => {
  it.each([
    [
      "eligibility_area",
      "Greater Manchester or the West Midlands",
      "Where you live or work: Greater Manchester or the West Midlands",
    ],
    ["eligibility_age", { minimum_age: 19 }, "Age: aged 19 or over"],
    [
      "eligibility_earnings",
      { below_annual_gross: gbp(3240000), area: "Greater Manchester" },
      "Earnings: under £32,400 a year before tax (Greater Manchester)",
    ],
    ["eligibility_no_other_funded_training", true, "No other funded training at the same time"],
    ["eligibility_residency", ["London", "West Midlands"], "Where you live: London, West Midlands"],
    [
      "eligibility_work_rights",
      "right to work in the UK",
      "Right to work: right to work in the UK",
    ],
  ])("words %s", (field, value, words) => {
    expect(conditionWords(field, value)).toBe(words);
  });

  it("never prints a shape it can't word: it says the condition is on the page", () => {
    expect(conditionWords("eligibility_other", { odd: [1, 2] })).toBe("A condition on its page");
  });
});

describe("[FUNDING-06] the monthly payment limit's meaning (session 2, D15 yes)", () => {
  it("counts every payment for the change and any debt repayments that month", () => {
    expect(paymentCapMeaning("payments_and_debt_repayments")).toBe(
      "The most you'd pay in any one month: every payment for the change, plus any debt repayments that month.",
    );
  });
});

describe("[OPTN-15] someone not working reads their own 0 hours and £0, said plainly", () => {
  it("reads the stated figures, never an unknown", () => {
    expect(notWorkingWords).toBe("Not working: 0 hours, £0");
  });

  it("asks each input a route search needs in plain words", () => {
    expect(NEEDED_INPUT.baseline.name).toBe("If you don't make a change");
    expect(NEEDED_INPUT.opening_cash.name).toBe("Money you have now");
  });
});
