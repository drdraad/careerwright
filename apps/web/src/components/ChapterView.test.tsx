// A planned chapter as rendered: Unknown, Skipped and Prefer not to say are answers, so they
// never block it and never read as unanswered (spec section 3; the "unknown is never zero or
// ineligible" invariant). Its card is short (the design reference's five elements); what it
// will hold and the answers it uses are one step away, under "More about this place".
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { ProfileDocument, ProfileOut } from "@/generated/api";
import { PlannedChapter } from "./ChapterView";

const SRC = "8d1f6f8e-46a1-5c2b-9d0e-3f7a1b2c4d5e";

function profile(changes: Partial<ProfileDocument>): ProfileOut {
  return {
    workspace_id: "w1",
    version: 2,
    created_by: null,
    created_at: "2027-01-01T00:00:00Z",
    document: {
      schema_version: "4",
      work_status: { state: "unasked", value: null, source_ref_id: null },
      qualifications: { state: "unasked", value: null, source_ref_id: null },
      preferred_name: { state: "unasked", value: null, source_ref_id: null },
      current_role: { state: "unasked", value: null, source_ref_id: null },
      cities: { state: "provided", value: ["Leeds"], source_ref_id: SRC },
      target_titles: { state: "provided", value: ["Data quality analyst"], source_ref_id: SRC },
      weekly_study_hours: { state: "unknown", value: null, source_ref_id: SRC },
      direct_spend_cap: { state: "skipped", value: null, source_ref_id: SRC },
      monthly_payment_cap: { state: "prefer_not_to_say", value: null, source_ref_id: SRC },
      enjoyed_tasks: { state: "unasked", value: null, source_ref_id: null },
      confident_tasks: { state: "unasked", value: null, source_ref_id: null },
      evidenced_tasks: { state: "unasked", value: null, source_ref_id: null },
      work_style: { state: "unasked", value: null, source_ref_id: null },
      minimum_salary: { state: "unasked", value: null, source_ref_id: null },
      ...changes,
    },
  };
}

/** Opens "More about this place", one step away. */
async function more() {
  await userEvent.setup().click(screen.getByText("More about this place"));
}

describe("[STATE-01][UI-04] a planned chapter treats every chosen state as an answer", () => {
  it("does not block Options on an Unknown, Skipped or Prefer-not-to-say budget", async () => {
    render(<PlannedChapter id="options" profile={profile({})} workspaceId="w1" />);

    expect(screen.getByText(/^Option research isn't ready yet/)).toBeVisible();
    expect(screen.queryByText(/Needs answers in You first/)).not.toBeInTheDocument();
    expect(screen.queryByText(/not answered|not asked/i)).not.toBeInTheDocument();
    await more();
    expect(screen.getByText(/Less precise without weekly study hours \(Unknown\)/)).toBeVisible();
    expect(screen.getByText(/Less precise without total spending limit \(Skipped\)/)).toBeVisible();
    expect(
      screen.getByText(/Less precise without monthly payment limit \(Prefer not to say\)/),
    ).toBeVisible();
  });

  it("asks first only for a starting answer that was never asked", () => {
    render(
      <PlannedChapter
        id="options"
        profile={profile({
          target_titles: { state: "unasked", value: null, source_ref_id: null },
        })}
        workspaceId="w1"
      />,
    );

    expect(
      screen.getByText("Needs answers in You first. Not asked yet: target roles."),
    ).toBeVisible();
  });

  it.each([
    ["roles", "Roles", "The horizon: places you could head for."],
    ["skills", "Skills", "The ground between you and a destination."],
    ["options", "Options", /^Bridges across the dark stretches/],
    ["plan", "Plan", /^The path you choose, made solid/],
  ] as const)("shows %s as its place in the world, honestly not built yet", (id, title, where) => {
    render(<PlannedChapter id={id} profile={profile({})} workspaceId="w1" />);

    expect(screen.getByText("Not built yet")).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: title })).toBeVisible();
    expect(screen.getByText(where)).toBeVisible();
  });

  it("is the reference's short card: one state, one sentence, one action, the rest one step away", () => {
    render(<PlannedChapter id="roles" profile={profile({})} workspaceId="w1" />);

    // One honest-state heading only: the place's own name.
    expect(screen.getAllByRole("heading")).toHaveLength(1);
    expect(
      screen.getByText("Role research isn't ready yet, so no listings have been searched."),
    ).toBeVisible();
    expect(screen.getAllByRole("link")).toHaveLength(1);
    expect(screen.getByText(/Role cards and a map of employers/)).not.toBeVisible();
    expect(screen.getByText("Uses these answers from You")).not.toBeVisible();
  });

  it("says plan selection isn't built, and what its one action is for (V-06)", () => {
    render(<PlannedChapter id="plan" profile={profile({})} workspaceId="w1" />);

    expect(
      screen.getByText(/Plan selection isn't ready yet, so no plan has been made/),
    ).toBeVisible();
    expect(screen.getByText(/never from a fixture preview/)).toBeVisible();
    expect(screen.queryByText(/route you select in Routes/)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review your answers in You" })).toHaveAttribute(
      "href",
      "/w/w1/you",
    );
  });

  it("says an Unknown target leaves nothing to start from, without blocking", async () => {
    render(
      <PlannedChapter
        id="options"
        profile={profile({
          target_titles: { state: "unknown", value: null, source_ref_id: SRC },
        })}
        workspaceId="w1"
      />,
    );

    expect(screen.getByText(/^Option research isn't ready yet/)).toBeVisible();
    expect(screen.queryByText(/Needs answers in You first/)).not.toBeInTheDocument();
    await more();
    expect(
      screen.getByText(/is not a specific one, so there is nothing to start from/),
    ).toBeVisible();
  });
});
