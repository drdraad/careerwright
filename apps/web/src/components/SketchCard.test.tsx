// The early sketch's words for how each target title matched ESCO: what the match did, never
// what ESCO holds (Task W2B re-review 5: a title ESCO writes another way, or shares only as a
// hidden label, made "not in ESCO" and "Several ESCO occupations have this title" untrue).
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ProfileOut, SketchOut } from "@/generated/api";
import { fakeApi } from "@/test/fakeApi";
import { SketchCard } from "./SketchCard";

const WS = "w-sketch";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const profile: ProfileOut = {
  workspace_id: WS,
  version: 1,
  created_by: null,
  created_at: "2027-01-01T00:00:00Z",
  document: {
    schema_version: "3",
    preferred_name: unasked,
    current_role: unasked,
    cities: unasked,
    target_titles: unasked,
    weekly_study_hours: unasked,
    direct_spend_cap: unasked,
    monthly_payment_cap: unasked,
    enjoyed_tasks: unasked,
    confident_tasks: unasked,
    evidenced_tasks: unasked,
    work_style: unasked,
    minimum_salary: unasked,
  },
};
const target = (title: string, resolution: SketchOut["targets"][number]["resolution"]) => ({
  title,
  resolution,
  occupations: [],
  close_matches: [],
  requirements: [],
  requirement_count: null,
  regulated: null,
  research_status: "Not researched.",
});

describe("[STATE-05][DIV1-03] the sketch says what matching each title did", () => {
  it("names a title matched to several, and the person's own title matched to none", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/sketch$/,
        answer: {
          label: "Early sketch, not a checked route",
          profile_version: 1,
          inputs: {},
          not_asked: [],
          targets: [
            target("bus operator", "ambiguous"),
            target("facade cleaner", "provisional"),
            target("orbital gardener", "not_found"),
          ],
          steps: [],
        } satisfies SketchOut,
      },
    ]);
    render(
      <QueryClientProvider client={new QueryClient()}>
        <SketchCard workspaceId={WS} profile={profile} />
      </QueryClientProvider>,
    );

    expect(
      await screen.findByText(": Matched to several occupations in ESCO", { exact: false }),
    ).toBeVisible();
    expect(
      screen.getByText(": Your own title: Careerwright couldn't match it in ESCO", {
        exact: false,
      }),
    ).toBeVisible();
    // A title matched to none: what the match did, never "Not found in ESCO" (a claim about
    // ESCO that another spelling or a hidden label can make untrue).
    expect(screen.getByText("Orbital gardener").closest("p")).toHaveTextContent(
      "Orbital gardener: Careerwright couldn't match it in ESCO",
    );
    expect(document.body.textContent).not.toMatch(
      /not in ESCO|Not found in ESCO|Several ESCO occupations have/,
    );
  });
});
