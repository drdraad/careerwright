// The missing-fact line with its box, as the person sees it (Task 12b, OPTN-13): the fact named
// plainly, one place to type their own figure, labelled theirs, and Save as the one action.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MissingFactBox } from "./MissingFactBox";

describe("[OPTN-13] a missing fact is named plainly, with a box for the person's own figure", () => {
  it("names the fact and labels the box as the person's own figure, not checked", () => {
    render(<MissingFactBox fact="weekly_hours" primary saving={false} onSave={() => {}} />);

    expect(screen.getByText("Hours a week: not known yet")).toBeVisible();
    expect(
      screen.getByLabelText("How many hours a week would it take? (your own figure, not checked)"),
    ).toBeVisible();
    expect(screen.getByRole("button", { name: "Save" })).toHaveClass("btn-primary");
  });

  it("saves exactly what was typed, in the API's shape", async () => {
    const onSave = vi.fn();
    render(<MissingFactBox fact="cost" primary saving={false} onSave={onSave} />);

    await userEvent.type(screen.getByRole("textbox"), "30,150");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onSave).toHaveBeenCalledWith({
      fact: "cost",
      money: { minor_units: 3015000, currency: "GBP" },
    });
  });

  it("says why a figure can't be saved, and saves nothing", async () => {
    const onSave = vi.fn();
    render(<MissingFactBox fact="weekly_hours" primary saving={false} onSave={onSave} />);

    await userEvent.type(screen.getByRole("textbox"), "7.5");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Enter whole hours from 0 to 168.");
    expect(onSave).not.toHaveBeenCalled();
  });

  it("offers the page's own intake months as a start, needing no typing", async () => {
    const onSave = vi.fn();
    render(
      <MissingFactBox
        fact="start_date"
        statedIntakes={["2026-02-01", "2026-03-01"]}
        primary
        saving={false}
        onSave={onSave}
      />,
    );

    await userEvent.click(screen.getByLabelText("March 2026, as its page states"));
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onSave).toHaveBeenCalledWith({
      fact: "start_date",
      on: "2026-03-01",
      basis: "stated_intake",
    });
    expect(screen.getByLabelText("Another day (your own figure, not checked)")).toBeVisible();
  });

  it("waits for the person to choose an intake instead of saving the first one by default", async () => {
    const onSave = vi.fn();
    render(
      <MissingFactBox
        fact="start_date"
        statedIntakes={["2026-02-01", "2026-03-01"]}
        primary
        saving={false}
        onSave={onSave}
      />,
    );

    expect(screen.getByLabelText("February 2026, as its page states")).not.toBeChecked();
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Choose a date.");
    expect(onSave).not.toHaveBeenCalled();
  });

  it("prefills saved dates and lets the person choose a different day", async () => {
    const onSave = vi.fn();
    render(
      <MissingFactBox
        fact="start_date"
        current={{ fact: "start_date", on: "2027-09-01", basis: "stated_intake" }}
        statedIntakes={["2027-09-01"]}
        primary={false}
        saving={false}
        onSave={onSave}
      />,
    );
    expect(screen.getByText("Start date: your choice from its page")).toBeVisible();
    expect(screen.getByLabelText("September 2027, as its page states")).toBeChecked();
    await userEvent.click(screen.getByLabelText("Another day (your own figure, not checked)"));
    const date = screen.getByLabelText("Your start date");
    expect(date).toHaveValue("2027-09-01");
    await userEvent.clear(date);
    await userEvent.type(date, "2027-10-01");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onSave).toHaveBeenCalledWith({
      fact: "start_date",
      on: "2027-10-01",
      basis: "own_figure",
    });
  });

  it("says it is saving instead of sending twice", async () => {
    const onSave = vi.fn();
    render(<MissingFactBox fact="weekly_hours" primary saving onSave={onSave} />);

    await userEvent.type(screen.getByRole("textbox"), "9");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(screen.getByText("Saving…")).toBeVisible();
    expect(onSave).not.toHaveBeenCalled();
  });
});
