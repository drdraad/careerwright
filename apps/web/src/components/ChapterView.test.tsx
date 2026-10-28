// A planned chapter as rendered: Unknown, Skipped and Prefer not to say are answers, so they
// never block it and never read as unanswered (spec section 3; the "unknown is never zero or
// ineligible" invariant).
import { render, screen } from "@testing-library/react";
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
      schema_version: "2",
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
      ...changes,
    },
  };
}

describe("[STATE-01][UI-04] a planned chapter treats every chosen state as an answer", () => {
  it("does not block Options on an Unknown, Skipped or Prefer-not-to-say budget", () => {
    render(<PlannedChapter id="options" profile={profile({})} workspaceId="w1" />);

    expect(screen.getByText("No options yet")).toBeInTheDocument();
    expect(screen.queryByText("Needs answers in You first")).not.toBeInTheDocument();
    expect(screen.queryByText(/not answered|not asked/i)).not.toBeInTheDocument();
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

    expect(screen.getByText("Needs answers in You first")).toBeInTheDocument();
    expect(screen.getByText(/Not asked yet: target roles/)).toBeInTheDocument();
  });

  it("says an Unknown target leaves nothing to start from, without blocking", () => {
    render(
      <PlannedChapter
        id="options"
        profile={profile({
          target_titles: { state: "unknown", value: null, source_ref_id: SRC },
        })}
        workspaceId="w1"
      />,
    );

    expect(screen.getByText("No options yet")).toBeInTheDocument();
    expect(screen.queryByText("Needs answers in You first")).not.toBeInTheDocument();
    expect(
      screen.getByText(/is not a specific one, so there is nothing to start from/),
    ).toBeVisible();
  });
});
