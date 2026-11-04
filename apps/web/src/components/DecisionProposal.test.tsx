import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { p01Checkpoint, p01Plan, p01Profile, p01Routes, p01Skills } from "@/test/p01DesignData";
import { DecisionProposal } from "./DecisionProposal";

const show = () =>
  render(
    <DecisionProposal
      routes={p01Routes}
      skills={p01Skills}
      plan={p01Plan}
      checkpoint={p01Checkpoint}
      profile={p01Profile}
    />,
  );

describe("P01 decision proposal", () => {
  beforeEach(() => {
    vi.stubGlobal("matchMedia", () => Object.assign(new EventTarget(), { matches: false }));
  });

  it("compares both routes and previews the alternative without replacing the saved plan", async () => {
    const user = userEvent.setup();
    show();
    const choices = within(screen.getByRole("group", { name: "Compare routes" }));
    const fullTime = choices.getByRole("button", { name: /Route 1 Full-time/ });
    const partTime = choices.getByRole("button", { name: /Route 2 Part-time/ });
    expect(within(fullTime).getByText("£1,800")).toBeVisible();
    expect(within(fullTime).getByText("March 2027")).toBeVisible();
    expect(within(partTime).getByText("£0")).toBeVisible();
    expect(within(partTime).getByText("April 2027")).toBeVisible();
    expect(partTime).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("SQL is still unresolved.")).toBeVisible();
    expect(
      screen.getByText("Your supplied figure, not checked. Provider quote not known yet."),
    ).toBeVisible();

    await user.click(fullTime);
    await user.click(screen.getByRole("button", { name: "Preview this plan" }));
    expect(screen.getByText("Local preview · not saved")).toBeVisible();
    expect(screen.getByRole("heading", { level: 1 })).toHaveFocus();
    expect(screen.getByText("0 / 1")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Return to your saved plan" }));
    expect(screen.getByText("Saved plan · Route 2")).toBeVisible();
    expect(screen.getByText("Proposed course start: 1 December 2026")).toBeVisible();
    expect(screen.getByText(/Confirm the place, timetable/)).toBeVisible();
    expect(screen.getByText("Not reported complete")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Back to route comparison" }));
    expect(screen.getByRole("button", { name: "Review saved plan" })).toBeVisible();
    expect(p01Plan.progress?.completed_steps).toEqual([]);
    expect(p01Plan.source.schedule_index).toBe(1);
  });

  it("keeps model qualifications, self-reported skills and unknown option costs distinct", async () => {
    const user = userEvent.setup();
    show();
    await user.click(screen.getByText("Assumptions and sources (8)"));
    expect(screen.getByText("Assumes a planned step gives you a skill.")).toBeVisible();
    expect(
      screen.getByText(
        /These are qualifications on the model's result, not qualifications you have achieved/,
      ),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Netcom Training: course source" })).toHaveAttribute(
      "href",
      "https://www.netcomtraining.co.uk/course/certificate-in-data/",
    );

    await user.click(screen.getByRole("button", { name: "Skills" }));
    expect(screen.getAllByText("Self-reported evidence")).toHaveLength(2);
    expect(screen.getByText("Unresolved")).toBeVisible();
    expect(screen.getByText(/You said you have not learned this yet/)).toBeVisible();
    expect(screen.queryByText("Your qualifications")).not.toBeInTheDocument();
    const firstExample = screen.getAllByText("Read your saved example")[0];
    if (!firstExample) throw new Error("Missing saved example disclosure");
    await user.click(firstExample);
    expect(
      screen.getAllByText(/Synthetic example: I traced duplicate stock records/)[0],
    ).toBeVisible();
    await user.click(screen.getByText("Other options: facts still missing"));
    expect(screen.getByText(/1 other option has an unknown cost/)).toBeVisible();
    expect(
      screen.getByText("Unknown costs remain unknown; they are never treated as £0."),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Compare routes for SQL" }));
    expect(
      screen.getByText("Your supplied figure, not checked. Provider quote not known yet."),
    ).toBeVisible();
  });
});
