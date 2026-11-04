import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { PlanningInputsDocument, PlanningInputsIn } from "@/generated/api";
import { checkpointFixture, optionsFixture } from "@/test/optionsFixture";
import { OptionsScreen } from "./OptionsChapter";

const display = (
  checkpoint = checkpointFixture,
  options = optionsFixture,
  inputs: PlanningInputsDocument = {},
) => {
  const onWrite = vi.fn(async (_update: (inputs: PlanningInputsIn) => PlanningInputsIn) => true);
  const onAdd = vi.fn(async () => "own:new");
  render(
    <OptionsScreen
      workspaceId="w1"
      options={options}
      checkpoint={checkpoint}
      inputs={inputs}
      busy={false}
      failure={null}
      onWrite={onWrite}
      onAdd={onAdd}
    />,
  );
  return { onWrite, onAdd };
};

describe("[OPTN-13][FUNDING-06] Options uses the API's facts, not guessed figures", () => {
  it("shows the degree, apprenticeship and T Level, with a loan to repay and an unknown start", async () => {
    display();
    expect(screen.getByRole("heading", { level: 1, name: "Options" })).toBeVisible();
    expect(screen.getByRole("button", { name: /Data science degree/ })).toBeVisible();
    expect(screen.getByRole("button", { name: /Data apprenticeship/ })).toBeVisible();
    expect(screen.getByRole("button", { name: /Digital T Level/ })).toBeVisible();
    expect(screen.getByText(/£9,250\. Paid straight to the university or college/)).toBeVisible();
    expect(screen.getByText("Not known yet: start date.")).toBeVisible();
    await userEvent.click(screen.getByText("About these option records"));
    expect(
      screen.getByText(
        "From Careerwright's list of courses and funding in England, dated 1 November 2026.",
      ),
    ).toBeVisible();
    expect(
      screen.getAllByRole("button").filter((button) => button.classList.contains("btn-primary")),
    ).toHaveLength(1);
  });

  it("links to the cited provider page when the catalogue includes its URL", async () => {
    const options = structuredClone(optionsFixture);
    const concept = options.targets[0]?.catalogue?.concepts[0];
    if (!concept?.cited) throw new Error("fixture has no cited concept");
    concept.cited.source_url = "https://example.org/course";
    display(checkpointFixture, options);
    await userEvent.click(screen.getByText("Sources and conditions"));
    expect(screen.getByRole("link", { name: "Open source page" })).toHaveAttribute(
      "href",
      "https://example.org/course",
    );
    expect(screen.getByRole("link", { name: "Open source page" })).toHaveAttribute(
      "rel",
      "noopener noreferrer nofollow",
    );
  });

  it("keeps a page's intake unchosen until the person picks it, then saves their choice", async () => {
    const { onWrite } = display();
    expect(screen.getByLabelText("September 2027, as its page states")).not.toBeChecked();
    await userEvent.click(screen.getByLabelText("September 2027, as its page states"));
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    const update = onWrite.mock.calls[0]?.[0];
    expect(update?.({})).toEqual({
      offering_figures: [
        { offering_id: "degree-offering", start: { on: "2027-09-01", basis: "stated_intake" } },
      ],
    });
  });

  it("lets a person revise every saved offering figure after reopening Options", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    const option = checkpoint.targets[0]?.options[0];
    if (!option) throw new Error("fixture has no option");
    option.missing = [];
    const { onWrite } = display(checkpoint, optionsFixture, {
      offering_figures: [
        {
          offering_id: "degree-offering",
          start: { on: "2027-09-01", basis: "stated_intake" },
          finish: "2030-06-01",
          weekly_hours: 9,
          cost: { minor_units: 30000, currency: "GBP" },
        },
      ],
    });
    await userEvent.click(screen.getByText("Change your figures"));
    expect(screen.getByText("1 September 2027 (your choice of a stated intake)")).toBeVisible();
    expect(screen.getByText("1 June 2030 (your own figure, not checked)")).toBeVisible();
    expect(screen.getByText("9 (your own figure, not checked)")).toBeVisible();
    expect(screen.getByLabelText("September 2027, as its page states")).toBeChecked();
    expect(
      screen.getByLabelText("When would it finish? (your own figure, not checked)"),
    ).toHaveValue("2030-06-01");
    expect(
      screen.getByLabelText("How many hours a week would it take? (your own figure, not checked)"),
    ).toHaveValue("9");
    const cost = screen.getByLabelText(
      "What would you pay for it in total? (your own figure, not checked)",
    );
    expect(cost).toHaveValue("300.00");
    await userEvent.clear(cost);
    await userEvent.type(cost, "250");
    const form = cost.closest("form");
    if (!form) throw new Error("cost is outside a form");
    await userEvent.click(within(form).getByRole("button", { name: "Save" }));
    const update = onWrite.mock.calls[0]?.[0];
    expect(
      update?.({ offering_figures: [{ offering_id: "degree-offering", weekly_hours: 9 }] }),
    ).toEqual({
      offering_figures: [
        {
          offering_id: "degree-offering",
          weekly_hours: 9,
          cost: { minor_units: 25000, currency: "GBP" },
        },
      ],
    });
  });

  it("shows a supplied total when the page has no payment figure", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    const option = checkpoint.targets[0]?.options[2];
    if (!option) throw new Error("fixture has no T Level");
    option.missing = [];
    display(checkpoint, optionsFixture, {
      offering_figures: [
        { offering_id: "t-level-offering", cost: { minor_units: 0, currency: "GBP" } },
      ],
    });
    await userEvent.click(screen.getByRole("button", { name: /Digital T Level/ }));
    expect(screen.getByText("£0 (your own figure, not checked)")).toBeVisible();
  });

  it("keeps a researched price quote separate from a payable total", () => {
    const options = structuredClone(optionsFixture);
    const offering = options.targets[0]?.catalogue?.offerings[0];
    if (!offering) throw new Error("The Options fixture needs an offering");
    offering.payment_plans = [
      { plan_id: "degree-fee", payments: [], unknown: "total unconfirmed" },
    ];
    offering.facts = [{ field: "quoted_cost", value: "£9,250" }];
    display(checkpointFixture, options);
    const payment = screen.getByRole("heading", { name: "What you would pay" }).parentElement;
    if (!payment) throw new Error("The payment heading needs a section");
    expect(within(payment).getByText("Not known yet")).toBeVisible();
    expect(
      screen.getByText(
        "Its page quotes £9,250. This does not confirm the total payable or when it is due.",
      ),
    ).toBeVisible();
  });

  it("labels figures returned by the answered catalogue as the person's unchecked figures", () => {
    const checkpoint = structuredClone(checkpointFixture);
    const options = structuredClone(optionsFixture);
    const option = checkpoint.targets[0]?.options[0];
    const offering = options.targets[0]?.catalogue?.offerings[0];
    if (!option || !offering) throw new Error("The Options fixture needs an offering");
    option.supplied = ["start_date", "weekly_hours"];
    offering.start = "2027-09-01";
    offering.weekly_hours = 9;
    display(checkpoint, options);
    expect(screen.getByText("1 September 2027 (your own figure, not checked)")).toBeVisible();
    expect(screen.getByText("9 (your own figure, not checked)")).toBeVisible();
  });

  it("lets a person correct confirmed eligibility without losing another answer", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    const option = checkpoint.targets[0]?.options[0];
    if (!option) throw new Error("fixture has no option");
    option.eligibility_conditions = [
      { field: "eligibility_area", value: "England", status: "confirmed" },
      { field: "eligibility_work_rights", value: "UK", status: "confirmed" },
    ];
    const { onWrite } = display(checkpoint, optionsFixture, {
      variants: [
        {
          variant_id: "degree",
          condition_statuses: {
            eligibility_area: "confirmed",
            eligibility_work_rights: "confirmed",
          },
        },
      ],
    });
    await userEvent.click(screen.getByText("Change eligibility answers"));
    await userEvent.selectOptions(
      screen.getByLabelText(/Where you live or work: England/),
      "ineligible",
    );
    const field = screen.getByLabelText(/Where you live or work: England/);
    const form = field.closest("form");
    if (!form) throw new Error("eligibility answer is outside a form");
    await userEvent.click(within(form).getByRole("button", { name: "Save this answer" }));
    const update = onWrite.mock.calls[0]?.[0];
    expect(
      update?.({
        variants: [
          {
            variant_id: "degree",
            condition_statuses: {
              eligibility_area: "confirmed",
              eligibility_work_rights: "confirmed",
            },
          },
        ],
      }),
    ).toEqual({
      variants: [
        {
          variant_id: "degree",
          condition_statuses: {
            eligibility_area: "ineligible",
            eligibility_work_rights: "confirmed",
          },
        },
      ],
    });
  });

  it("shows what a school leaver's T Level still needs, without counting expected grades as met", async () => {
    display();
    await userEvent.click(screen.getByRole("button", { name: /Digital T Level/ }));
    expect(screen.getByText(/if you get your grades/)).toBeVisible();
    expect(screen.getByText("Not known yet: cost.")).toBeVisible();
    expect(
      screen.getByLabelText("What would you pay for it in total? (your own figure, not checked)"),
    ).toBeVisible();
  });

  it("records an unchecked entry answer while retaining the expected-grade caveat", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    const option = checkpoint.targets[0]?.options[1];
    if (!option) throw new Error("fixture has no apprenticeship");
    option.entry_requirements = [
      {
        field: "entry_requirement",
        value: "A-level mathematics",
        qualifications: [
          {
            qualification: "A-level mathematics",
            status: "expected",
            standing: "expected_not_met",
          },
        ],
      },
    ];
    option.entry_expected = true;
    const { onWrite } = display(checkpoint);
    await userEvent.click(screen.getByRole("button", { name: /Data apprenticeship/ }));
    expect(screen.getByText(/if you get your grades/)).toBeVisible();
    expect(screen.getByText(/expected qualification is not achieved yet/)).toBeVisible();
    await userEvent.selectOptions(
      screen.getByLabelText("Do you meet the entry requirements? Your answer is not checked."),
      "yes",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save entry answer" }));
    expect(onWrite.mock.calls[0]?.[0]({})).toEqual({
      variants: [{ variant_id: "apprentice", entry_requirements_met: true }],
    });
  });

  it("lets a person revise a saved entry answer without losing other variant inputs", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    const option = checkpoint.targets[0]?.options[1];
    if (!option) throw new Error("fixture has no apprenticeship");
    option.entry_requirements = [
      { field: "entry_requirement", value: "Maths qualification", qualifications: [] },
    ];
    option.entry_requirements_met = true;
    option.missing = [];
    const { onWrite } = display(checkpoint, optionsFixture, {
      variants: [
        {
          variant_id: "apprentice",
          entry_requirements_met: true,
          condition_statuses: { area: "confirmed" },
        },
      ],
    });
    await userEvent.click(screen.getByRole("button", { name: /Data apprenticeship/ }));
    expect(screen.getByText(/You said you meet the entry requirements/)).toBeVisible();
    await userEvent.click(screen.getByText("Change entry answer"));
    await userEvent.selectOptions(
      screen.getByLabelText("Do you meet the entry requirements? Your answer is not checked."),
      "not_sure",
    );
    expect(screen.getByText("This stays unresolved in route searches.")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Save entry answer" }));
    expect(
      onWrite.mock.calls[0]?.[0]({
        variants: [{ variant_id: "apprentice", condition_statuses: { area: "confirmed" } }],
      }),
    ).toEqual({
      variants: [
        {
          variant_id: "apprentice",
          condition_statuses: { area: "confirmed" },
          entry_requirements_met: null,
        },
      ],
    });
  });

  it("shows each funding scheme's stated age rule without applying it to an unknown age", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    const target = checkpoint.targets[0];
    if (!target) throw new Error("fixture has no target");
    target.schemes = [
      {
        instrument_id: "grant-1",
        kind: "grant",
        review_state: "reviewed",
        as_of: "2026-11-01",
        age_rules: [{ field: "age", value: { minimum_age: 19 } }],
      },
    ];
    const options = structuredClone(optionsFixture);
    const catalogue = options.targets[0]?.catalogue;
    if (catalogue) {
      catalogue.instruments = [
        {
          instrument_id: "grant-1",
          programme: "Learner Support",
          kind: "grant",
          jurisdiction: "England",
          review_state: "reviewed",
        },
      ];
    }
    display(checkpoint, options);
    await userEvent.click(screen.getByText("Funding that may apply to this target"));
    expect(screen.getByText(/Learner Support\. Reviewed\. Aged 19 or over/)).toBeVisible();
    expect(screen.getByText(/Careerwright doesn't know your age/)).toBeVisible();
  });

  it("leaves a variant out only when the person asks, without removing its card", async () => {
    const { onWrite } = display();
    await userEvent.click(screen.getByRole("button", { name: "Leave this out of route searches" }));
    const update = onWrite.mock.calls[0]?.[0];
    expect(update?.({ excluded_variants: [] })).toEqual({ excluded_variants: ["degree"] });
    expect(screen.getByRole("button", { name: /Data science degree/ })).toBeVisible();
  });

  it("pins an option in the view without changing planning inputs", async () => {
    const { onWrite } = display();
    await userEvent.click(screen.getByRole("button", { name: "Pin on this screen" }));
    expect(screen.getByRole("button", { name: /Data science degree.*pinned/ })).toBeVisible();
    expect(screen.getByRole("button", { name: "Unpin from this screen" })).toBeVisible();
    expect(onWrite).not.toHaveBeenCalled();
  });

  it("asks one planning question at a time and writes the answer to the whole document", async () => {
    const { onWrite } = display();
    await userEvent.click(screen.getByRole("button", { name: /Before a route search/ }));
    expect(screen.getByText("Not working: 0 hours, £0")).toBeVisible();
    await userEvent.selectOptions(screen.getByLabelText("Choose one"), "direct_spending");
    await userEvent.click(screen.getByRole("button", { name: "Save this answer" }));
    const update = onWrite.mock.calls[0]?.[0];
    expect(update?.({ living_costs: { minor_units: 45000, currency: "GBP" } })).toEqual({
      objective_basis: "direct_spending",
      living_costs: { minor_units: 45000, currency: "GBP" },
    });
  });

  it("offers a way forward when the catalogue has no bridge for the target", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    const target = checkpoint.targets[0];
    if (!target) throw new Error("fixture has no target");
    target.options = [];
    target.reviewed_options = 0;
    display(checkpoint);
    expect(screen.getByText(/No bridge found yet/)).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Add an option you know" }));
    expect(screen.getByRole("heading", { name: /Add an option for/ })).toBeVisible();
    expect(screen.getByLabelText("What is it called?")).toBeVisible();
  });

  it("shows a saved planning answer and lets the person change it at the checkpoint", async () => {
    const { onWrite } = display(checkpointFixture, optionsFixture, {
      objective_basis: "economic",
      opening_cash: { minor_units: 50000, currency: "GBP" },
    });
    await userEvent.click(screen.getByRole("button", { name: /Before a route search/ }));
    await userEvent.click(screen.getByText("Your planning answers (2)"));
    expect(screen.getByText("£500")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Change Money you have now" }));
    expect(screen.getByLabelText("Pounds")).toHaveValue("500");
    await userEvent.clear(screen.getByLabelText("Pounds"));
    await userEvent.type(screen.getByLabelText("Pounds"), "650");
    await userEvent.click(screen.getByRole("button", { name: "Save this answer" }));
    expect(onWrite.mock.calls[0]?.[0]({ objective_basis: "economic" })).toEqual({
      objective_basis: "economic",
      opening_cash: { minor_units: 65000, currency: "GBP" },
    });
  });

  it("keeps every stated weekly commitment in the planning answer", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    checkpoint.needs = [{ input: "commitments", effect: "blocks_a_solve" }];
    const { onWrite } = display(checkpoint);
    await userEvent.click(screen.getByRole("button", { name: /Before a route search/ }));
    await userEvent.selectOptions(screen.getByLabelText("Choose one"), "care");
    await userEvent.type(screen.getByLabelText("Hours a week"), "12");
    await userEvent.click(screen.getByRole("button", { name: "Add another commitment" }));
    await userEvent.selectOptions(screen.getByLabelText("Choose one"), "second_job");
    await userEvent.type(screen.getByLabelText("Hours a week"), "8");
    await userEvent.click(screen.getByRole("button", { name: "Save this answer" }));
    expect(onWrite.mock.calls[0]?.[0]({})).toEqual({
      commitments: [
        { kind: "care", hours_per_week: 12 },
        { kind: "second_job", hours_per_week: 8 },
      ],
    });
  });

  it("does not discard an invalid last debt after earlier monthly repayments", async () => {
    const checkpoint = structuredClone(checkpointFixture);
    checkpoint.needs = [{ input: "existing_debts", effect: "blocks_a_solve" }];
    const { onWrite } = display(checkpoint);
    await userEvent.click(screen.getByRole("button", { name: /Before a route search/ }));
    await userEvent.type(screen.getByLabelText("Pounds"), "25");
    await userEvent.click(screen.getByRole("button", { name: "Add another debt" }));
    await userEvent.type(screen.getByLabelText("Pounds"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: "Save this answer" }));
    expect(onWrite).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toBeVisible();
    await userEvent.clear(screen.getByLabelText("Pounds"));
    await userEvent.type(screen.getByLabelText("Pounds"), "30");
    await userEvent.click(screen.getByRole("button", { name: "Save this answer" }));
    expect(onWrite.mock.calls[0]?.[0]({})).toEqual({
      existing_debts: [
        { monthly_repayment: { minor_units: 2500, currency: "GBP" } },
        { monthly_repayment: { minor_units: 3000, currency: "GBP" } },
      ],
    });
  });

  it("records the person's loan answer without treating it as a grant or their own cash", async () => {
    const { onWrite } = display();
    await userEvent.click(screen.getByRole("button", { name: "Change fee loan answer" }));
    expect(screen.getByText(/It's a loan you repay later/)).toBeVisible();
    await userEvent.selectOptions(
      screen.getByLabelText("Do the conditions apply to you?"),
      "confirmed",
    );
    await userEvent.selectOptions(
      screen.getByLabelText("What happened when you applied?"),
      "approved",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save loan answer" }));
    const update = onWrite.mock.calls[0]?.[0];
    expect(update?.({})).toEqual({
      variants: [
        {
          variant_id: "degree",
          tuition_fee_loan: {
            kind: "tuition_fee_loan",
            amount: { minor_units: 925000, currency: "GBP" },
            eligibility: "confirmed",
            application: "approved",
          },
        },
      ],
    });
  });

  it("refuses an approved loan without confirmed eligibility before any write", async () => {
    const { onWrite } = display();
    await userEvent.click(screen.getByRole("button", { name: "Change fee loan answer" }));
    await userEvent.selectOptions(
      screen.getByLabelText("What happened when you applied?"),
      "approved",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save loan answer" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "An approved loan needs a confirmed eligibility answer.",
    );
    expect(onWrite).not.toHaveBeenCalled();
  });

  it("adds the person's own option with typed words and optional pasted source text", async () => {
    const { onAdd } = display();
    await userEvent.click(screen.getByRole("button", { name: "Add your own option" }));
    await userEvent.type(screen.getByLabelText("What is it called?"), "Evening data course");
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await userEvent.type(screen.getByLabelText(/Who offers it/), "Local college");
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await userEvent.type(
      screen.getByLabelText(/Paste the page text/),
      "Course starts in September.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save this option" }));
    expect(onAdd).toHaveBeenCalledWith("Data quality analyst", {
      title: "Evening data course",
      provider: "Local college",
      kind: "learning",
      text: "Course starts in September.",
    });
  });

  it("names a comparison beyond bounds and keeps every option visible", () => {
    const checkpoint = structuredClone(checkpointFixture);
    checkpoint.targets = checkpoint.targets.map((target) => ({
      ...target,
      scope: {
        concepts: 25,
        max_concepts: 24,
        most_starts: 3,
        max_starts: 2,
        over_starts: [],
        code: "retain_variants",
      },
    }));
    display(checkpoint);
    expect(screen.getByRole("status")).toHaveTextContent("nothing has been hidden");
    expect(
      screen.getAllByRole("button", {
        name: /Data science degree|Data apprenticeship|Digital T Level/,
      }),
    ).toHaveLength(3);
  });

  it("says why no option appears for a target outside the pack", () => {
    const checkpoint = structuredClone(checkpointFixture);
    checkpoint.targets = checkpoint.targets.map((target) => ({
      ...target,
      options: [],
      reviewed_options: 0,
    }));
    const options = structuredClone(optionsFixture);
    options.targets = options.targets.map((target) => ({ ...target, catalogue: null }));
    display(checkpoint, options);
    expect(screen.getByText(/No reviewed option found yet/)).toBeVisible();
    expect(screen.getByText(/No bridge found yet/)).toBeVisible();
  });
});

describe("[OPTN-13] Options connects the bridge list with its working view", () => {
  it("distinguishes option timings and keeps a chosen intake separate from an unreviewed figure", () => {
    display(checkpointFixture, optionsFixture, {
      offering_figures: [
        {
          offering_id: "degree-offering",
          weekly_hours: 9,
          start: { on: "2027-09-01", basis: "stated_intake" },
        },
      ],
    });
    const landscape = within(screen.getByRole("complementary", { name: /Ways toward/ }));
    const degree = landscape.getByRole("button", { name: /Data science degree/ });
    expect(degree).toHaveTextContent("9h / week (your own figure, not checked)");
    expect(degree).toHaveTextContent("Starts September 2027 (your choice of a stated intake)");
    const apprenticeship = landscape.getByRole("button", { name: /Data apprenticeship/ });
    expect(apprenticeship).toHaveTextContent("32h / week");
    expect(apprenticeship).toHaveTextContent("Starts February 2027");
    expect(apprenticeship).not.toHaveTextContent("your own figure");
  });

  it("opens the chosen option from the checkpoint without changing saved inputs", async () => {
    const { onWrite } = display();
    await userEvent.click(screen.getByRole("button", { name: /Before a route search/ }));
    const landscape = within(screen.getByRole("complementary", { name: /Ways toward/ }));
    await userEvent.click(landscape.getByRole("button", { name: /Digital T Level/ }));
    expect(screen.getByRole("region", { name: "Digital T Level details" })).toBeVisible();
    expect(landscape.getByRole("button", { name: /Digital T Level/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Explore options" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(onWrite).not.toHaveBeenCalled();
  });
});
