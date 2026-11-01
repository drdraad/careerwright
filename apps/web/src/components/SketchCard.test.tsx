// The early sketch's words for how each target title matched ESCO: what the match did, never
// what ESCO holds (Task W2B re-review 5: a title ESCO writes another way, or shares only as a
// hidden label, made "not in ESCO" and "Several ESCO occupations have this title" untrue).
// Since Task 6d slice A the API sends facts and the web words them: the label, each target's
// research status and coverage, and each step.
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
type Target = SketchOut["targets"][number];
const target = (
  title: string,
  resolution: Target["resolution"],
  coverage: Target["coverage"] = "not_covered",
): Target => ({
  title,
  resolution,
  occupations: [],
  close_matches: [],
  requirements: [],
  requirement_count: null,
  regulated: null,
  coverage,
});

function renderSketch(sketch: SketchOut) {
  fakeApi([{ method: "GET", path: /\/sketch$/, answer: sketch }]);
  render(
    <QueryClientProvider client={new QueryClient()}>
      <SketchCard workspaceId={WS} profile={profile} />
    </QueryClientProvider>,
  );
}

const INPUTS: SketchOut["inputs"] = {
  target_titles: "provided",
  current_role: "unasked",
  weekly_study_hours: "provided",
  direct_spend_cap: "prefer_not_to_say",
  cities: "unasked",
};

describe("[STATE-05][DIV1-03] the sketch says what matching each title did", () => {
  it("names a title matched to several, and the person's own title matched to none", async () => {
    renderSketch({
      profile_version: 1,
      inputs: {},
      not_asked: [],
      targets: [
        target("bus operator", "ambiguous"),
        target("facade cleaner", "provisional"),
        target("orbital gardener", "not_found"),
      ],
      steps: [],
    });

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

  it("[PROF-10] words its label, each research status, each step and each target's coverage", async () => {
    renderSketch({
      profile_version: 2,
      inputs: INPUTS,
      not_asked: [],
      targets: [
        target("registered nurse", "not_found", "pack_target"),
        target("bus operator", "ambiguous"),
        target("orbital gardener", "not_found"),
      ],
      steps: [
        { step: "compare", state: "unresolved" },
        { step: "find_options", state: "unresolved" },
        { step: "check_time_and_cost", state: "unresolved" },
      ],
    });

    expect(await screen.findByText("Early sketch, not a checked route")).toBeVisible();
    expect(
      screen.getByText("Careerwright can check skills, options and routes for this role."),
    ).toBeVisible();
    expect(
      screen.getAllByText("Careerwright can't check skills, options or routes for this role yet."),
    ).toHaveLength(2);
    // Only the title no pack target covers reads "Not researched" (fix round 1).
    expect(
      screen.getByText(
        "Careerwright couldn't match this title to an occupation in ESCO, so there's no requirement list yet. Not researched.",
      ),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Careerwright matched this title to several occupations in ESCO. Choose the one you mean.",
      ),
    ).toBeVisible();
    const steps = screen.getAllByRole("listitem").map((item) => item.textContent);
    expect(steps).toEqual([
      "Compare these requirements with what you have done. Not resolved yet. Not compared yet: nothing is marked missing or met.",
      "Find courses, work routes or funding for any gaps. Not resolved yet. Not researched yet: no providers, prices or dates.",
      "Check the time and cost against your week and budget. Not resolved yet. Uses your weekly hours. Your spending limit isn't known, so costs can't be checked yet.",
    ]);
  });

  it("[PROF-10] never says a pack role ESCO doesn't name is not researched", async () => {
    // Task 6d slice A fix round 1 (review I-1): three of the option pack's four titles are no
    // ESCO label, so the sketch said both "Careerwright can check skills, options and routes
    // for this role" and "… there's no requirement list yet. Not researched." The option pack
    // researched them; its coverage line says what Careerwright can check.
    renderSketch({
      profile_version: 1,
      inputs: INPUTS,
      not_asked: [],
      targets: [
        target("Registered nurse", "not_found", "pack_target"),
        target("Data quality analyst", "not_found", "pack_target"),
        target("Bookkeeping assistant", "provisional", "pack_target"),
      ],
      // The three steps the API sends whenever there is a target (fix round 2).
      steps: [
        { step: "compare", state: "unresolved" },
        { step: "find_options", state: "unresolved" },
        { step: "check_time_and_cost", state: "unresolved" },
      ],
    });

    expect(
      await screen.findAllByText(
        "Careerwright can check skills, options and routes for this role.",
      ),
    ).toHaveLength(3);
    for (const title of ["Registered nurse", "Data quality analyst", "Bookkeeping assistant"]) {
      const line = screen.getByText(title).closest("p");
      expect(line).toHaveTextContent(
        `${title}: ${title === "Bookkeeping assistant" ? "Your own title: " : ""}Careerwright couldn't match it in ESCO`,
      );
      // The target's own block; the steps below it are the sketch's, shared by every target.
      expect(line?.parentElement).not.toHaveTextContent(/Not researched|no requirement list/);
    }
    // Step 2 keeps its words; session W2 judges them beside the coverage line.
    expect(screen.getAllByRole("listitem").map((item) => item.textContent)).toContain(
      "Find courses, work routes or funding for any gaps. Not resolved yet. Not researched yet: no providers, prices or dates.",
    );
  });

  it("[PROF-11] calls a target's skills ESCO's list for this kind of work, and names ESCO plainly once", async () => {
    // The product owner's ESCO research: ESCO's list is ESCO's, never the person's skills or
    // what the work "usually" asks for.
    const listed = (title: string): Target => ({
      ...target(title, "esco"),
      occupations: [{ concept_id: title, title, isco_group: { code: "7231", label: "Mechanics" } }],
      requirements: ["adjust brakes", "fit tyres"],
      requirement_count: 9,
    });
    renderSketch({
      profile_version: 1,
      inputs: INPUTS,
      not_asked: [],
      targets: [listed("bicycle mechanic"), listed("motorcycle mechanic")],
      steps: [],
    });

    expect(await screen.findAllByText("ESCO lists these for this kind of work:")).toHaveLength(2);
    expect(
      screen.getAllByText(
        "Careerwright looked up each target in ESCO, the European Union's public list of occupations and skills.",
      ),
    ).toHaveLength(1);
    expect(screen.getAllByText("Adjust brakes")).toHaveLength(2);
    expect(document.body.textContent).not.toMatch(/usually/);
  });
});
