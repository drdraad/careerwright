// Directions to explore (REC-1, DIV-1): a grounded slate in words with no percentage; the
// controls change the view only; a suggestion becomes a target only when chosen.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { DiscoveryOut, ProfileOut, SlateOut, SuggestionOut } from "@/generated/api";
import { fakeApi } from "@/test/fakeApi";
import { Directions } from "./Directions";
import { EvidenceProvider } from "./EvidenceDrawer";

const WS = "w-dir";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const profile: ProfileOut = {
  workspace_id: WS,
  version: 2,
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
    enjoyed_tasks: { state: "provided", value: ["repairing bicycles"], source_ref_id: "s1" },
    confident_tasks: unasked,
    evidenced_tasks: unasked,
    work_style: unasked,
    minimum_salary: unasked,
  },
};
const discovery = {
  discovery_id: "d1",
  profile_version: 2,
  run: { status: "complete" },
  proposal: null,
} as unknown as DiscoveryOut;

const suggestion: SuggestionOut = {
  concept_id: "o1",
  concept_kind: "esco",
  title: "bicycle mechanic",
  esco_code: "7231.1",
  isco_group: { code: "7231", label: "Motor vehicle mechanics and repairers" },
  family: { code: "723", label: "Machinery mechanics and repairers" },
  sector: { code: "7", label: "Craft and related trades workers" },
  direction: "less_familiar",
  channels: ["tasks"],
  linked_evidence: [{ field: "enjoyed_tasks", text: "repairing bicycles" }],
  matched_queries: ["q1"],
  sources: [{ kind: "esco", uri: "http://data.europa.eu/esco/occupation/o1", release: "esco" }],
  workday: "Bicycle mechanics maintain and repair bicycles.",
  why_it_could_suit: ["What you enjoy: “repairing bicycles”."],
  what_might_not_suit: ["ESCO lists 9 essential skills, not yet compared with your experience."],
  entry_gates: ["Entry requirements aren't researched yet."],
  evidence_gaps: ["Pay, demand and listings in your work areas aren't researched yet."],
  try_it: ["Talk to someone who works as a bicycle mechanic about a typical week."],
};
const slate = (shown: SuggestionOut[]): SlateOut => ({
  discovery_id: "d1",
  profile_version: 2,
  release: {
    dataset_id: "esco",
    version: "v1.2.1",
    attribution: "This service uses ESCO.",
    adaptation: "Adapted.",
    sample: false,
  },
  emphasis: "balanced",
  target_size: 6,
  family_limit: 2,
  suggestions: shown,
  fewer_reasons:
    shown.length < 6 ? ["Only 1 occupation matched your answers closely enough to suggest."] : [],
  notes: [],
  limits_not_applied: [],
  pool_size: 4,
  pool_target: [60, 120],
  beyond_pool_limit: 0,
  excluded: { occupations: 0, families: 0 },
  queries: [
    {
      query_id: "q1",
      text: "bicycle repair",
      channel: "tasks",
      based_on: [{ field: "enjoyed_tasks", text: "repairing bicycles" }],
      hits: 4,
    },
  ],
  unsearchable_queries: [],
  unsupported_hypotheses: ["orbital gardener"],
  not_included: [
    {
      concept_id: "o2",
      title: "tree surgeon",
      family: { code: "621", label: "Forestry" },
      reason: "below_relevance_floor",
      duplicate_of: null,
      duplicate_of_title: null,
    },
  ],
});

function renderDirections() {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <Directions workspaceId={WS} profile={profile} discovery={discovery} />
      </EvidenceProvider>
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

describe("[REC1-05][REC1-07][REC1-08][DIV1-06] the slate in words, its controls, and choosing", () => {
  it("shows why, what might not suit and a small test, fewer with the reason, and no percentage", async () => {
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([suggestion]) }]);
    renderDirections();

    expect(await screen.findByRole("heading", { name: "Bicycle mechanic" })).toBeVisible();
    expect(screen.getByText("Why this could suit you")).toBeVisible();
    expect(screen.getByText("Try it before committing")).toBeVisible();
    expect(screen.getByText(/Only 1 occupation matched/)).toBeVisible();
    expect(screen.getByText(/orbital gardener/)).toBeVisible(); // never shown as a suggestion
    // Familiarity unknown: the group heading claims no relation to their current work.
    expect(screen.getByRole("heading", { name: "Directions to consider" })).toBeVisible();
    expect(document.body.textContent).not.toMatch(/\d\s?(%|per ?cent)/i); // a number as a percentage
  });

  it("excludes a title as a view only, and makes a target only when chosen", async () => {
    const sent = fakeApi([
      {
        method: "GET",
        path: /\/slate$/,
        answer: (request) =>
          slate(request.query.includes("exclude_concept=o1") ? [] : [suggestion]),
      },
      { method: "POST", path: /\/targets$/, status: 201, answer: profile },
    ]);
    const user = renderDirections();

    await user.click(await screen.findByRole("button", { name: /Make this a target/ }));
    await waitFor(() => expect(sent.some((s) => s.path.endsWith("/targets"))).toBe(true));
    expect(sent.find((s) => s.path.endsWith("/targets"))?.body).toEqual({
      expected_version: 2,
      concept_id: "o1",
      discovery_id: "d1",
    });
    await user.click(screen.getByRole("button", { name: /Not for me/ }));
    await waitFor(() =>
      expect(sent.some((s) => s.query.includes("exclude_concept=o1"))).toBe(true),
    );
    expect(sent.filter((s) => s.method !== "GET").map((s) => s.path)).toEqual([
      "/v1/workspaces/w-dir/targets",
    ]); // excluding wrote nothing
  });
});
