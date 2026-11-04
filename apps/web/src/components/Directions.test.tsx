// Directions to explore (REC-1, DIV-1): a grounded slate in words with no percentage; the
// controls change the view only; a suggestion becomes a target only when chosen.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type {
  DiscoveryOut,
  ProfileOut,
  SlateExplanationOut,
  SlateOut,
  SuggestionOut,
  TargetRecordsOut,
  WorkState,
} from "@/generated/api";
import { UK_TITLE_IDEAS } from "@/lib/vocabulary";
import { fakeApi, type Route, type Sent } from "@/test/fakeApi";
import { Directions } from "./Directions";
import { EvidenceDrawer, EvidenceProvider } from "./EvidenceDrawer";

const WS = "w-dir";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const profile: ProfileOut = {
  workspace_id: WS,
  version: 2,
  created_by: null,
  created_at: "2027-01-01T00:00:00Z",
  document: {
    schema_version: "5",
    work_status: unasked,
    qualifications: unasked,
    disliked_tasks: unasked,
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
const explanation = (
  status: WorkState,
  written: SlateExplanationOut["written"] = null,
  // A failed run that sent no request (refused for its budget) may be tried again.
  reachedNoModel = false,
): SlateExplanationOut =>
  ({
    explanation_id: "e1",
    discovery_id: "d1",
    run: {
      run_id: "e1",
      kind: "slate_explanation",
      status,
      failure_class:
        status === "failed" ? (reachedNoModel ? "budget_exceeded" : "invalid_model_output") : null,
    },
    can_retry: reachedNoModel,
    written,
  }) as unknown as SlateExplanationOut;
const WRITTEN: SlateExplanationOut["written"] = {
  origin: "model",
  prompt_version: "slate-explanation-1",
  profile_version: 2,
  release: "esco",
  suggestions: [
    {
      concept_id: "o1",
      title: "bicycle mechanic",
      claims: [
        {
          text: "You enjoy fixing bikes, and this work is mostly maintaining and repairing them.",
          quotations: [
            {
              source: "answer",
              answer_field: "enjoyed_tasks",
              record_part: null,
              text: "repairing bicycles",
            },
            {
              source: "esco",
              answer_field: null,
              record_part: "description",
              text: "maintain and repair bicycles",
            },
          ],
        },
      ],
    },
  ],
};
const discoveryWith = (found: SlateExplanationOut | null): DiscoveryOut =>
  ({
    discovery_id: "d1",
    profile_version: 2,
    current: true,
    run: { status: "complete" },
    proposal: null,
    explanation: found,
  }) as unknown as DiscoveryOut;
// Already explained, so these tests see no request for a note.
const discovery = discoveryWith(explanation("complete", WRITTEN));

const suggestion: SuggestionOut = {
  concept_id: "o1",
  concept_kind: "esco",
  title: "bicycle mechanic",
  esco_code: "7231.1",
  isco_group: { code: "7231", label: "Motor vehicle mechanics and repairers" },
  family: { code: "723", label: "Machinery mechanics and repairers" },
  sector: { code: "7", label: "Craft and related trades workers" },
  horizon: "next_step",
  skill_level: 2,
  direction: "less_familiar",
  channels: ["tasks"],
  linked_evidence: [{ field: "enjoyed_tasks", text: "repairing bicycles" }],
  matched_queries: ["q1"],
  sources: [{ kind: "esco", uri: "http://data.europa.eu/esco/occupation/o1", release: "esco" }],
  workday: "Bicycle mechanics maintain and repair bicycles.",
  reasons: [
    {
      reason: "searched_through_skill",
      outcome: "found_work",
      field: "enjoyed_tasks",
      answer: "repairing bicycles",
      search: "bicycle repair",
      skill: "repair bicycles",
    },
  ],
  essential_skill_count: 9,
  essential_skills: ["repair bicycles", "tune bicycles", "sell bicycles"],
  regulated: false,
  different_kind_of_work: false,
  shared_skills: [],
};
/** A title Careerwright thought of, from the person's enjoyed bicycle repairs. */
const titleIdea = (
  title: string,
  reason: SlateOut["title_ideas"][number]["reason"],
  more: Partial<SlateOut["title_ideas"][number]> = {},
): SlateOut["title_ideas"][number] => ({
  title,
  based_on: [{ field: "enjoyed_tasks", text: "repairing bicycles" }],
  reason,
  outcome: "not_matched",
  occupations: 0,
  groups: [],
  skill_level: null,
  horizon: null,
  position: null,
  left_out: false,
  ...more,
});
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
  reference: { basis: "unknown", level: null },
  suggestions: shown,
  fewer_reasons:
    shown.length < 6 ? [{ reason: "few_matched", count: 1, horizon: "next_step" }] : [],
  notes: [],
  salary_floor: null,
  ai_resilience_filter: {
    minimum: null,
    include_unscored: true,
    scored: 0,
    below_minimum: 0,
    unscored: 4,
    unscored_excluded: 0,
    synthetic: false,
    pack_version: "l0-2026-10-29",
    pack_dated: "2026-10-29",
  },
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
      reach: 4,
      too_general: false,
    },
  ],
  unsearchable_queries: [],
  title_ideas: [titleIdea("orbital gardener", "not_yet_found")],
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
  unmatched_titles: [],
  ambiguous_titles: [],
  familiarity_known: false,
});

function renderDirections(
  shown: DiscoveryOut = discovery,
  unavailable?: string,
  withProfile: ProfileOut = profile,
) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onEditAnswers = vi.fn();
  const onNameRole = vi.fn();
  const view = (found: DiscoveryOut) => (
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <Directions
          workspaceId={WS}
          profile={withProfile}
          discovery={found}
          onEditAnswers={onEditAnswers}
          onNameRole={onNameRole}
          {...(unavailable === undefined ? {} : { unavailable })}
        />
        <EvidenceDrawer />
      </EvidenceProvider>
    </QueryClientProvider>
  );
  const { rerender } = render(view(shown));
  return {
    user: userEvent.setup(),
    onEditAnswers,
    onNameRole,
    rerender: (found: DiscoveryOut) => rerender(view(found)),
  };
}

const slateRoute: Route = { method: "GET", path: /\/slate$/, answer: () => slate([suggestion]) };
/** How Careerwright found the suggestion, as the web words its fact. */
const FOUND_BY =
  "What you enjoy: “repairing bicycles”. Careerwright searched for “bicycle repair”, and ESCO lists “repair bicycles” as an essential skill for this work.";
const card = async () => screen.findByRole("article", { name: "Bicycle mechanic" });

/** The slate's notes on how it searched wait in one disclosure, one step away (D-I3). */
async function openNotes(user: ReturnType<typeof userEvent.setup>, count: number) {
  const notes = await screen.findByText(
    `How Careerwright searched (${count} ${count === 1 ? "note" : "notes"})`,
  );
  await user.click(notes);
}

describe("[REC1-05][REC1-07][REC1-08][DIV1-06] the slate in words, its controls, and choosing", () => {
  it("shows why first and keeps the other detail one step away", async () => {
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([suggestion]) }]);
    const { user } = renderDirections();

    expect(await screen.findByRole("heading", { name: "Bicycle mechanic" })).toBeVisible();
    expect(screen.getByText("Why this could suit you")).toBeVisible();
    expect(screen.getByText("Try it before committing")).not.toBeVisible();
    // Never overwhelming: the notes are one step away, and each keeps its words there.
    const few = /Careerwright found only 1 occupation for Next step/;
    expect(screen.getByText(few)).not.toBeVisible();
    await openNotes(user, 3);
    expect(screen.getByText(few)).toBeVisible();
    // How the two sets were placed (Task 6g), naming no work it doesn't know.
    expect(
      screen.getByText(
        "Careerwright placed each suggestion by the training its job group usually needs: Aim higher is work that usually needs study after A-levels or similar.",
      ),
    ).toBeVisible();
    // Never shown as a suggestion, and named for what Careerwright did (W2B re-review 5; Task
    // 6d slice B: it looked in ESCO and the UK job-title index).
    expect(
      screen.getByText(
        "Titles Careerwright thought of but hasn't found in ESCO or the UK job-title index yet, so not suggested: orbital gardener.",
      ),
    ).toBeVisible();
    expect(screen.queryByRole("heading", { name: UK_TITLE_IDEAS.heading })).toBeNull();
    expect(screen.getByRole("heading", { name: "Next step" })).toBeVisible();
    expect(document.body.textContent).not.toMatch(/\d\s?(%|per ?cent)/i); // a number as a percentage
  });

  it("shows one sentence about the work and the reason, with the full account and checked quotes one step away", async () => {
    const long = {
      ...suggestion,
      workday:
        "Bicycle mechanics maintain and repair bicycles. They also inspect parts, explain repairs and test the finished work.",
    };
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([long]) }]);
    const { user } = renderDirections();
    const shown = within(await card());

    expect(shown.getByText("Bicycle mechanics maintain and repair bicycles.")).toBeVisible();
    expect(shown.getByText(long.workday)).not.toBeVisible();
    expect(shown.getByText(/mostly maintaining and repairing them/)).toBeVisible();
    expect(shown.getByText("How Careerwright found it")).not.toBeVisible();
    expect(shown.getByText("Try it before committing")).not.toBeVisible();
    expect(shown.getByText("You said:")).not.toBeVisible();
    for (const name of [
      "Balanced",
      "Closer to what I do",
      "Less familiar",
      "Broader",
      "More depth",
    ]) {
      expect(screen.queryByRole("button", { name })).toBeNull();
    }

    await user.click(shown.getByText("More about this role"));
    expect(shown.getByText(long.workday)).toBeVisible();
    expect(shown.getByText("How Careerwright found it")).toBeVisible();
    expect(shown.getByText("You said:")).toBeVisible();
    expect(shown.getByText("Try it before committing")).toBeVisible();
  });

  it("cuts a long first sentence at a word and keeps the full description available", async () => {
    const workday = `Bicycle mechanics ${"inspect and repair complicated equipment ".repeat(6)}every day.`;
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([{ ...suggestion, workday }]) }]);
    const { user } = renderDirections();
    const shown = within(await card());
    const preview = shown.getByText(/^Bicycle mechanics.*…$/);
    expect(preview.textContent?.length).toBeLessThanOrEqual(141);
    expect(workday.startsWith(preview.textContent?.slice(0, -1) ?? "")).toBe(true);
    expect(shown.getByText(workday)).not.toBeVisible();
    await user.click(shown.getByText("More about this role"));
    expect(shown.getByText(workday)).toBeVisible();
  });

  it("[DIV1-16][DIV1-12] lists Next step then Aim higher, never by direction, and says an Aim higher job group's usual training", async () => {
    // The product owner's re-test (3 November 2026): "Directions to consider" was very odd,
    // and the suggestions too basic. The API places each in a set; the web heads the two.
    const higher: SuggestionOut = {
      ...suggestion,
      concept_id: "o3",
      title: "chemist",
      family: { code: "211", label: "Physical and earth science professionals" },
      horizon: "aim_higher",
      skill_level: 4,
      direction: "less_familiar",
    };
    const close: SuggestionOut = { ...suggestion, direction: "close_to_current" };
    fakeApi([{ method: "GET", path: /\/slate$/, answer: () => slate([close, higher]) }]);
    renderDirections();

    const sets = await screen.findAllByRole("heading", { level: 3 });
    expect(sets.map((heading) => heading.textContent)).toEqual(["Next step", "Aim higher"]);
    expect(
      screen.getByText("These job groups usually need less study than Aim higher."),
    ).toBeVisible();
    expect(
      screen.getByText("These job groups usually need study after A-levels or similar."),
    ).toBeVisible();
    for (const direction of ["Directions to consider", "Close to what you do now"]) {
      expect(screen.queryByText(direction)).toBeNull();
    }
    const aim = screen.getByRole("region", { name: "Aim higher" });
    expect(within(aim).getByRole("article", { name: "Chemist" })).toBeVisible();
    // Its usual training, once under the heading (Task 6g slice B: never on every card), and
    // the closed card's line is its kind of work alone.
    expect(
      within(aim).getByText(
        "Most work in this job group usually needs a degree or equivalent training.",
      ),
    ).toBeVisible();
    expect(within(aim).getAllByText(/usually needs/)).toHaveLength(1);
    expect(
      within(aim).getByText("Kind of work: Physical and earth science professionals"),
    ).toBeVisible();
    // Next step says nothing of training.
    const next = screen.getByRole("region", { name: "Next step" });
    expect(
      within(next).getByText("Kind of work: Machinery mechanics and repairers"),
    ).not.toBeVisible();
    expect(within(next).queryByText(/usually needs/)).toBeNull();
  });

  it("[DIV1-16][DIV1-04] shows a title idea the UK job-title index lists in its set, at its place, and makes it a target through the profile's save", async () => {
    // Task 6g slice B: Muse's Aim higher idea, confirmed by the UK job-title index and placed
    // by its job group's level; one whose groups disagree stays in the list beside the slate.
    const higher: SuggestionOut = {
      ...suggestion,
      concept_id: "o3",
      title: "chemist",
      family: { code: "211", label: "Physical and earth science professionals" },
      horizon: "aim_higher",
      skill_level: 4,
    };
    const placed = titleIdea("Customer success manager", "in_uk_title_index", {
      groups: [{ code: "3339", label: "Business services agents not elsewhere classified" }],
      skill_level: 3,
      horizon: "aim_higher",
      position: 0,
    });
    const beside = titleIdea("Account manager", "in_uk_title_index", {
      groups: [
        { code: "1330", label: "ICT services managers" },
        { code: "3313", label: "Accounting associate professionals" },
      ],
    });
    const answer = { ...slate([suggestion, higher]), title_ideas: [placed, beside] };
    const sent = fakeApi([
      { method: "GET", path: /\/slate$/, answer },
      { method: "PUT", path: /\/profile$/, status: 201, answer: profile },
    ]);
    const { user } = renderDirections();

    const aim = await screen.findByRole("region", { name: "Aim higher" });
    expect(within(aim).getAllByRole("article")).toHaveLength(2);
    const [first, second] = within(aim).getAllByRole("heading", { level: 4 });
    expect([first?.textContent, second?.textContent]).toEqual([
      "Customer success manager",
      "Chemist",
    ]);
    // One training sentence for the set, for both its levels.
    expect(
      within(aim).getByText(
        "Most work in these job groups usually needs one to three years of study after A-levels or similar, or a degree or equivalent training.",
      ),
    ).toBeVisible();
    expect(
      within(aim).getByText("Kind of work: Business services agents not elsewhere classified"),
    ).toBeVisible();
    // Beside the slate: only the idea in no set.
    const list = screen.getByRole("region", { name: UK_TITLE_IDEAS.heading });
    expect(within(list).getByRole("heading", { name: "Account manager" })).toBeVisible();
    expect(within(list).queryByText("Customer success manager")).toBeNull();
    expect(screen.getByText(/and 2 titles found in the UK job-title index\./)).toBeVisible();

    await user.click(within(aim).getByRole("button", { name: /Customer success manager/ }));
    const card = within(aim).getByRole("article", { name: "Customer success manager" });
    expect(within(card).getByText(UK_TITLE_IDEAS.found)).toBeVisible();
    expect(
      within(card).getByText(
        "Careerwright thought of it from what you enjoy: “repairing bicycles”",
      ),
    ).toBeVisible();
    const make = within(card).getByRole("button", { name: /Make this a target/ });
    expect(make).toHaveClass("btn-primary");
    await user.click(make);
    const saved = (s: Sent) => s.method === "PUT" && s.path.endsWith("/profile");
    await waitFor(() => expect(sent.some(saved)).toBe(true));
    const body = sent.find(saved)?.body as {
      expected_version: number;
      profile: ProfileOut["document"];
    };
    expect(body.expected_version).toBe(2);
    expect(body.profile.target_titles).toEqual({
      state: "provided",
      value: ["Customer success manager"],
    });
  });

  it("[DIV1-16] says how the sets were placed only when a set has something in it", async () => {
    // Task 6g slice B (slice A's review, Minor 2).
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([]) }]);
    const { user } = renderDirections();

    await openNotes(user, 2);
    expect(screen.queryByText(/Careerwright placed each suggestion/)).toBeNull();
  });

  it("[PROF-14] with no work known, never says close to what they do now, offers no Closer to what I do, and never tells someone with no job yet that their work isn't known", async () => {
    const noJob = { state: "no_job_yet" as const, value: null, source_ref_id: "s3" };
    const withTarget: ProfileOut = {
      ...profile,
      document: {
        ...profile.document,
        current_role: noJob,
        target_titles: { state: "provided", value: ["Nurse"], source_ref_id: "s3" },
      },
    };
    const close = { ...suggestion, direction: "close_to_current" as const };
    let answer = () => ({ ...slate([close]), familiarity_known: true });
    fakeApi([{ method: "GET", path: /\/slate$/, answer: () => answer() }]);
    renderDirections(discovery, undefined, withTarget);

    // Close only to the role they named: never "Close to what you do now" (Task 6g: no set is
    // headed by direction at all).
    expect(await screen.findByRole("heading", { name: "Next step" })).toBeVisible();
    expect(screen.queryByText("Close to what you do now")).toBeNull();
    expect(screen.queryByRole("button", { name: "Closer to what I do" })).toBeNull();
    cleanup();

    // No role, no target: someone who said they haven't had a job is never told their work
    // isn't known.
    answer = () => slate([suggestion]);
    const nothingNamed: ProfileOut = {
      ...profile,
      document: { ...profile.document, current_role: noJob },
    };
    const { user } = renderDirections(discovery, undefined, nothingNamed);
    expect(await screen.findByRole("heading", { name: "Next step" })).toBeVisible();
    await openNotes(user, 3);
    expect(screen.queryByText(/doesn't know your (current )?work/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Closer to what I do" })).toBeNull();
    cleanup();

    // A role kept in their words does not bring back the old direction buttons.
    const working: ProfileOut = {
      ...profile,
      document: {
        ...profile.document,
        current_role: { state: "provided", value: "Baker", source_ref_id: "s2" },
      },
    };
    renderDirections(discovery, undefined, working);
    expect(await screen.findByRole("heading", { name: "Next step" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Closer to what I do" })).toBeNull();
  });

  it("[PROF-14] keeps the neutral view when the person's role changes", async () => {
    const sent = fakeApi([slateRoute]);
    const working: ProfileOut = {
      ...profile,
      document: {
        ...profile.document,
        current_role: { state: "provided", value: "Baker", source_ref_id: "s2" },
      },
    };
    const noJob: ProfileOut = {
      ...profile,
      document: {
        ...profile.document,
        current_role: { state: "no_job_yet", value: null, source_ref_id: "s3" },
      },
    };
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const view = (shown: ProfileOut) => (
      <QueryClientProvider client={queries}>
        <EvidenceProvider>
          <Directions workspaceId={WS} profile={shown} discovery={discovery} />
        </EvidenceProvider>
      </QueryClientProvider>
    );
    const { rerender } = render(view(working));
    await screen.findByRole("heading", { name: "Next step" });

    rerender(view(noJob));

    expect(screen.queryByRole("button", { name: "Closer to what I do" })).toBeNull();
    expect(
      sent
        .filter((s) => s.path.endsWith("/slate"))
        .every((s) => s.query.includes("emphasis=balanced")),
    ).toBe(true);
  });

  it("[DIV1-04][TEST1-15] lists a title idea the UK job-title index lists beside the slate, with its answers", async () => {
    const ideas: SlateOut["title_ideas"] = [
      titleIdea("Prompt engineer", "in_uk_title_index", {
        based_on: [{ field: "enjoyed_tasks", text: "writing prompts for AI tools" }],
      }),
      titleIdea("orbital gardener", "not_yet_found"),
    ];
    fakeApi([
      {
        method: "GET",
        path: /\/slate$/,
        answer: { ...slate([suggestion]), title_ideas: ideas },
      },
    ]);
    const { user } = renderDirections();

    const list = await screen.findByRole("region", { name: UK_TITLE_IDEAS.heading });
    expect(within(list).getByRole("heading", { name: "Prompt engineer" })).toBeVisible();
    expect(
      within(list).getByText(
        "Found in the UK job-title index (ONS). Not compared with your experience yet.",
      ),
    ).toBeVisible();
    expect(
      within(list).getByText(
        "Careerwright thought of it from what you enjoy: “writing prompts for AI tools”",
      ),
    ).toBeVisible();
    // An idea no list holds is never a suggestion: it is named as not yet found, in the notes.
    expect(within(list).queryByText(/orbital gardener/)).toBeNull();
    expect(screen.queryByRole("heading", { name: "orbital gardener" })).toBeNull();
    await openNotes(user, 3);
    expect(
      screen.getByText(
        "Titles Careerwright thought of but hasn't found in ESCO or the UK job-title index yet, so not suggested: orbital gardener.",
      ),
    ).toBeVisible();
  });

  it("[DIV1-07] says what the salary floor left out and why the rest was kept", async () => {
    const summary =
      "Your minimum salary of £26,000 a year (gross) is applied: 0 left out because their official pay is below it; 0 meet it; 4 kept because no reviewed UK occupation code links them to pay data. Unknown pay is never treated as below it.";
    fakeApi([
      {
        method: "GET",
        path: /\/slate$/,
        answer: {
          ...slate([suggestion]),
          salary_floor: {
            amount: { minor_units: 2_600_000, currency: "GBP" },
            period: "year",
            left_out: 0,
            meets: 0,
            kept_pay_unknown: 4,
            kept_by_reason: [{ reason: "no_reviewed_mapping", count: 4 }],
            basis: "gross",
          },
        },
      },
    ]);
    const { user } = renderDirections();

    await openNotes(user, 4);
    expect(await screen.findByText(summary)).toBeVisible();
  });

  it("[DIV1-02] counts what was found but not kept, and says what a join keeps", async () => {
    // Task W2B re-review 2, N-M2: a join's best 30 left 17 out, and the slate said nothing.
    // Re-review 3, I2: the join keeps by the share in common, not the most shared skills.
    const keeps =
      "Careerwright found 47 other occupations in ESCO that share 3 or more essential skills with “data analyst”, and keeps the 30 with the largest share of essential skills in common.";
    fakeApi([
      {
        method: "GET",
        path: /\/slate$/,
        answer: {
          ...slate([suggestion]),
          beyond_pool_limit: 17,
          notes: [
            {
              reason: "join_kept_best",
              outcome: "found_work",
              title: "data analyst",
              found: 47,
              kept: 30,
              min_shared: 3,
            },
          ],
        },
      },
    ]);
    const { user } = renderDirections();

    expect(await screen.findByText(/17 more were found but not kept\./)).toBeVisible();
    await openNotes(user, 4);
    expect(screen.getByText(keeps)).toBeVisible();
  });

  it("[DIV1-06] marks a search too general to find work alone, and never counts it as finding", async () => {
    // Task W2B re-review 3, M4: "writing reports" only added weight, yet it was listed and
    // counted as a search that found the work.
    const reports: SlateOut["queries"][number] = {
      query_id: "q2",
      text: "writing reports",
      channel: "tasks",
      based_on: [{ field: "enjoyed_tasks", text: "writing reports" }],
      hits: 1,
      reach: 217,
      too_general: true,
    };
    const shown = slate([{ ...suggestion, matched_queries: ["q1", "q2"] }]);
    fakeApi([
      {
        method: "GET",
        path: /\/slate$/,
        answer: { ...shown, queries: [...shown.queries, reports] },
      },
    ]);
    const { user } = renderDirections();

    expect(await screen.findByText(/from 4 occupations found by 1 search of ESCO\./)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Source for Bicycle mechanic" }));
    const sheet = await screen.findByRole("dialog", { name: "Where this came from" });
    const found = within(sheet)
      .getAllByRole("listitem")
      .map((item) => item.textContent);
    expect(found).toEqual([
      "“bicycle repair”, from “repairing bicycles”",
      "“writing reports”, from “writing reports” (too general to find work on its own, so it only added weight to what another search found)",
    ]);
  });

  // Task W2B re-review 4, M2: a search that reached nothing ("repairing physical objects")
  // was counted among those that found the occupations.
  const search = (
    query_id: string,
    text: string,
    reach: number,
    too_general = false,
  ): SlateOut["queries"][number] => ({
    query_id,
    text,
    channel: "tasks",
    based_on: [{ field: "enjoyed_tasks", text }],
    hits: too_general ? 1 : reach,
    reach,
    too_general,
  });
  const nothing = search("q2", "repairing physical objects", 0);
  const general = search("q3", "writing reports", 217, true);
  it.each([
    ["1 search", [nothing, general]],
    ["2 searches", [nothing, general, search("q4", "working outdoors", 12)]],
  ])("[DIV1-06] counts only the searches that reached work: %s", async (count, more) => {
    const shown = slate([suggestion]);
    fakeApi([
      {
        method: "GET",
        path: /\/slate$/,
        answer: { ...shown, queries: [...shown.queries, ...more] },
      },
    ]);
    renderDirections();

    const line = `from 4 occupations found by ${count} of ESCO.`;
    expect(await screen.findByText(line, { exact: false })).toBeVisible();
  });

  it("offers a concrete next action when a demo answer finds no work", async () => {
    fakeApi([
      {
        method: "GET",
        path: /\/slate$/,
        answer: { ...slate([]), pool_size: 0, queries: [nothing] },
      },
    ]);
    const fixture = {
      ...discovery,
      proposal: { origin: "fixture" },
    } as unknown as DiscoveryOut;
    const { user, onEditAnswers, onNameRole } = renderDirections(fixture);

    expect(
      await screen.findByRole("heading", { name: "No directions found from these answers" }),
    ).toBeVisible();
    expect(
      screen.getByText(/synthetic demo searches your words in ESCO skill names/),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Add a concrete task" }));
    expect(onEditAnswers).toHaveBeenCalledOnce();
    await user.click(screen.getByRole("button", { name: "Name a role" }));
    expect(onNameRole).toHaveBeenCalledOnce();
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
    const { user } = renderDirections();

    await user.click(await screen.findByRole("button", { name: /Make this a target/ }));
    // The POST: the card also reads the stored targets (`GET .../targets`).
    const chose = (s: Sent) => s.method === "POST" && s.path.endsWith("/targets");
    await waitFor(() => expect(sent.some(chose)).toBe(true));
    expect(sent.find(chose)?.body).toEqual({
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

  it("[UI-04] opens one suggestion at a time, whose Make this a target is the bright action", async () => {
    // Session 2: "I found the button, but it did not stand out enough. Needs to be a bright
    // colour"; "need minimum ideas per page". The rest stay a list of titles to scan.
    const surgeon: SuggestionOut = { ...suggestion, concept_id: "o3", title: "tree surgeon" };
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([suggestion, surgeon]) }]);
    const { user } = renderDirections();

    const mechanic = await screen.findByRole("article", { name: "Bicycle mechanic" });
    const tree = screen.getByRole("article", { name: "Tree surgeon" });
    const chooseFirst = within(mechanic).getByRole("button", { name: /Make this a target/ });
    expect(chooseFirst).toHaveClass("btn-primary");
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(1);
    expect(within(tree).queryByRole("button", { name: /Make this a target/ })).toBeNull();
    expect(within(tree).getByText("Kind of work: Machinery mechanics and repairers")).toBeVisible();
    // The choice comes right after the title and kind of work, before the details, so the
    // bright action is in view with a real slate (design review I3).
    const why = within(mechanic).getByText("Why this could suit you");
    expect(
      chooseFirst.compareDocumentPosition(why) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    // One is always open: its header says it can't be closed (the ARIA accordion pattern).
    const mechanicHeader = within(mechanic).getByRole("button", { name: "Bicycle mechanic" });
    expect(mechanicHeader).toHaveAttribute("aria-expanded", "true");
    expect(mechanicHeader).toHaveAttribute("aria-disabled", "true");

    const open = within(tree).getByRole("button", { name: "Tree surgeon" });
    expect(open).toHaveAttribute("aria-expanded", "false");
    expect(open).not.toHaveAttribute("aria-disabled");
    await user.click(open);

    expect(open).toHaveAttribute("aria-expanded", "true");
    expect(open).toHaveAttribute("aria-disabled", "true");
    expect(mechanicHeader).not.toHaveAttribute("aria-disabled");
    expect(within(tree).getByRole("button", { name: /Make this a target/ })).toHaveClass(
      "btn-primary",
    );
    expect(within(mechanic).queryByRole("button", { name: /Make this a target/ })).toBeNull();
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(1);
  });

  it("[UI-04] makes asking for suggestions the bright action before there are any", () => {
    fakeApi([]);
    renderDirections(null as unknown as DiscoveryOut);

    expect(screen.getByRole("button", { name: "Suggest directions" })).toHaveClass("btn-primary");
  });
});

const NOTE_PATH = "/v1/workspaces/w-dir/discoveries/d1/explanation";
const noteRequests = (sent: Sent[]) =>
  sent.filter((s) => s.method === "POST" && s.path === NOTE_PATH);
const other: SuggestionOut = {
  ...suggestion,
  concept_id: "o3",
  title: "tree surgeon",
  reasons: [
    {
      reason: "searched_through_skill",
      outcome: "found_work",
      field: "enjoyed_tasks",
      answer: "working outdoors",
      search: "working outdoors",
      skill: "work in outdoor conditions",
    },
  ],
};

describe("[REC1-11] the written why: one request per slate, its states, provenance always", () => {
  it("asks once when the slate first shows, and an exclusion never asks again", async () => {
    const sent = fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/explanation$/,
        status: 202,
        answer: { explanation_id: "e1", discovery_id: "d1", run: { status: "queued" } },
      },
    ]);
    const { user } = renderDirections(discoveryWith(null));

    expect(await within(await card()).findByText(/writing a note/)).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(/is writing a note/);
    await user.click(screen.getByRole("button", { name: "Not for me : Bicycle mechanic" }));
    await waitFor(() => expect(sent.some((s) => s.query.includes("exclude_concept"))).toBe(true));

    expect(noteRequests(sent)).toHaveLength(1);
    expect(noteRequests(sent)[0]?.body).toEqual({ expected_profile_version: 2 });
  });

  it("asks only once the person can see the slate", async () => {
    // The You chapter keeps its views mounted (fix round 1, A-I1): a hidden slate asks nothing.
    const sent = fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/explanation$/,
        status: 202,
        answer: { explanation_id: "e1", discovery_id: "d1", run: { status: "queued" } },
      },
    ]);
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const view = (shown: boolean) => (
      <QueryClientProvider client={queries}>
        <EvidenceProvider>
          <Directions
            workspaceId={WS}
            profile={profile}
            discovery={discoveryWith(null)}
            shown={shown}
          />
        </EvidenceProvider>
      </QueryClientProvider>
    );
    const { rerender } = render(view(false));

    await card();
    await waitFor(() => expect(sent.some((s) => s.path.endsWith("/slate"))).toBe(true));
    expect(noteRequests(sent)).toHaveLength(0);
    rerender(view(true));
    await waitFor(() => expect(noteRequests(sent)).toHaveLength(1));
  });

  it("[REC1-11] never sends a refused request again when the slate shows again, only by a click", async () => {
    // App review M2: a refused request (no run) was sent again each time the slate mounted:
    // on every return to Suggestions, and on every change of chapter.
    const sent = fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/explanation$/,
        status: 409,
        answer: {
          error: {
            code: "BUDGET_EXCEEDED",
            message: "not shown",
            retryable: false,
            stage: "execution",
            correlation_id: "c1",
            details: {},
          },
        },
      },
    ]);
    // One page's query client, as the shell keeps it across chapters.
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const page = () => (
      <QueryClientProvider client={queries}>
        <EvidenceProvider>
          <Directions workspaceId={WS} profile={profile} discovery={discoveryWith(null)} />
        </EvidenceProvider>
      </QueryClientProvider>
    );
    const first = render(page());
    expect(
      await within(await card()).findByText(/The spending limit for model calls is reached\./),
    ).toBeVisible();
    expect(noteRequests(sent)).toHaveLength(1);

    first.unmount(); // another chapter
    render(page()); // and back
    const again = within(await card());
    expect(await again.findByText(/The spending limit for model calls is reached\./)).toBeVisible();
    expect(noteRequests(sent)).toHaveLength(1);

    // Only the person's click sends it again.
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Try again : the written note" }));
    await waitFor(() => expect(noteRequests(sent)).toHaveLength(2));
  });

  it("shows the note first and keeps checked quotations above how Careerwright found it, one step away", async () => {
    const sent = fakeApi([slateRoute]);
    const { user } = renderDirections();

    const shown = within(await card());
    const note = shown.getByText(/mostly maintaining and repairing them/);
    const found = shown.getByText(FOUND_BY);
    expect(note).toBeVisible();
    expect(found).not.toBeVisible();
    await user.click(shown.getByText("More about this role"));
    expect(shown.getByText("You said:")).toBeVisible();
    expect(shown.getByText("ESCO's description:")).toBeVisible();
    expect(shown.getByText(/“maintain and repair bicycles”/)).toBeVisible();
    // Fix round 1 (I2): it says what was checked, and that the sentence is the model's own.
    expect(
      shown.getByText(
        /Only the quoted words were checked against them; the sentences are Careerwright's own\./,
      ),
    ).toBeVisible();
    expect(shown.queryByText(/checked word for word/)).toBeNull();
    expect(shown.getByText("How Careerwright found it")).toBeVisible();
    // The deterministic provenance stays, after the written note.
    expect(note.compareDocumentPosition(found) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(noteRequests(sent)).toHaveLength(0); // already written: nothing asked
    expect(document.body.textContent).not.toMatch(/\d\s?(%|per ?cent)/i);
  });

  it("says when the note is still being written, and labels the demo explainer's", async () => {
    fakeApi([slateRoute]);
    const { rerender } = renderDirections(discoveryWith(explanation("running")));

    expect(await within(await card()).findByText(/writing a note/)).toBeVisible();
    expect(screen.getByText(FOUND_BY)).toBeVisible();
    rerender(
      discoveryWith(explanation("complete", { ...WRITTEN, origin: "fixture" } as typeof WRITTEN)),
    );
    const writtenBy = await screen.findByText(/Written by the demo explainer \(synthetic\)/);
    expect(writtenBy).not.toBeVisible();
    await userEvent.setup().click(within(await card()).getByText("More about this role"));
    expect(writtenBy).toBeVisible();
  });

  it("shows a note that failed after a request as unavailable, and offers Suggest again", async () => {
    const sent = fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/discoveries$/,
        status: 202,
        answer: { discovery_id: "d2", run: { status: "queued" } },
      },
    ]);
    const { user } = renderDirections(discoveryWith(explanation("failed")));

    const shown = within(await card());
    expect(shown.getByText(/no written note/)).toBeVisible();
    expect(
      shown.getByText(/The reply didn't pass Careerwright's checks twice\. Nothing from it/),
    ).toBeVisible();
    expect(shown.getByText(FOUND_BY)).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(/aren't available/);
    expect(screen.getByText("These suggestions have had their one written note.")).toBeVisible();
    // It says what Suggest again does.
    expect(screen.getByText(/Suggest again makes a new set of suggestions/)).toHaveTextContent(
      /would be replaced/,
    );
    expect(screen.queryByRole("button", { name: /Try again/ })).toBeNull();
    expect(screen.queryByText(/Try again, or add the details yourself/)).toBeNull(); // not offered
    await user.click(screen.getByRole("button", { name: "Suggest again" }));

    await waitFor(() => expect(sent.some((s) => s.path.endsWith("/discoveries"))).toBe(true));
    expect(sent.find((s) => s.path.endsWith("/discoveries"))?.body).toEqual({
      expected_profile_version: 2,
    });
    expect(noteRequests(sent)).toHaveLength(0); // the note itself is never asked for again
  });

  it("offers Try again for a note that reached no model, and sends it only on the click", async () => {
    const sent = fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/explanation$/,
        status: 202,
        answer: { explanation_id: "e2", discovery_id: "d1", run: { status: "queued" } },
      },
    ]);
    const { user } = renderDirections(discoveryWith(explanation("failed", null, true)));

    await card();
    expect(screen.getByText(/No request reached the model/)).toBeVisible();
    // F10: the words point to the spending line, the control that raises the limit (Task 3b).
    expect(
      screen.getByText(
        "Careerwright stopped before spending more. Your work is kept. You can raise the limit under Model spending, in the menu at the top.",
      ),
    ).toBeVisible();
    expect(noteRequests(sent)).toHaveLength(0); // never automatic
    await user.click(screen.getByRole("button", { name: "Try again : the written note" }));

    await waitFor(() => expect(noteRequests(sent)).toHaveLength(1));
    expect(noteRequests(sent)[0]?.body).toEqual({
      expected_profile_version: 2,
      retry_failed: true,
    });
  });

  it("shows a refused request as unavailable in the error code's words", async () => {
    const sent = fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/explanation$/,
        status: 409,
        answer: {
          error: {
            code: "BUDGET_EXCEEDED",
            message: "not shown",
            retryable: false,
            stage: "execution",
            correlation_id: "c1",
            details: {},
          },
        },
      },
    ]);
    const { user } = renderDirections(discoveryWith(null));

    const shown = within(await card());
    expect(await shown.findByText(/The spending limit for model calls is reached\./)).toBeVisible();
    expect(screen.queryByText("not shown")).toBeNull(); // never the API's own message
    expect(shown.getByText(FOUND_BY)).toBeVisible();
    expect(screen.getByText("Nothing was sent to the model.")).toBeVisible();
    // Fix round 3 (R3-M6): no run existed, so the card says it was refused before one, not
    // that it failed or that something from it was not kept.
    expect(shown.getByText(/Not started/)).toBeVisible();
    expect(shown.getByText(/Careerwright didn't ask the model, so nothing was sent/)).toBeVisible();
    expect(shown.queryByText(/Failed/)).toBeNull();
    expect(shown.queryByText(/Nothing from it was kept/)).toBeNull();
    await user.click(screen.getByRole("button", { name: "Try again : the written note" }));
    // The first request was the slate's own; the click sends it again, as a plain request.
    await waitFor(() => expect(noteRequests(sent)).toHaveLength(2));
    expect(noteRequests(sent)[1]?.body).toEqual({ expected_profile_version: 2 });
  });

  it.each([
    {
      code: "INSUFFICIENT_EVIDENCE",
      status: 422,
      reason: "no_quotable_answer",
      // Neutral for both causes: no content word ("art"), or a quoted phrase such as 'odd jobs'.
      words: /No written note: Your answers can't be quoted on their own/,
      button: null,
    },
    {
      code: "LIMIT_EXCEEDED",
      status: 422,
      reason: "answers_too_long",
      words: /No written note: Your answers are too long for a written note/,
      button: null,
    },
    {
      code: "PROPOSAL_NOT_AVAILABLE",
      status: 409,
      reason: undefined,
      words: /No written note: These suggestions have no searches to explain/,
      button: "Suggest again",
    },
  ])(
    "a refusal asking again would repeat ($code) says why and offers what can work, never Try again",
    async ({ code, status, reason, words, button }) => {
      // Fix round 2 (R2-M4).
      const sent = fakeApi([
        slateRoute,
        {
          method: "POST",
          path: /\/explanation$/,
          status,
          answer: {
            error: {
              code,
              message: "not shown",
              retryable: false,
              stage: "profile",
              correlation_id: "c3",
              details: reason === undefined ? {} : { reason },
            },
          },
        },
      ]);
      renderDirections(discoveryWith(null));

      expect(await screen.findByText(words)).toBeVisible();
      expect(screen.queryByRole("button", { name: /Try again/ })).toBeNull();
      if (button === null) {
        expect(
          screen.getByText(/Edit answers directly\. Careerwright then offers Suggest again\./),
        ).toBeVisible();
        expect(screen.queryByRole("button", { name: "Suggest again" })).toBeNull();
      } else {
        expect(screen.getByRole("button", { name: button })).toBeVisible();
      }
      expect(screen.queryByText("not shown")).toBeNull();
      expect(noteRequests(sent)).toHaveLength(1); // the slate's own request, never repeated
    },
  );

  it("offers Suggest again when a try again is refused because the slate had its note", async () => {
    fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/explanation$/,
        status: 409,
        answer: {
          error: {
            code: "SLATE_ALREADY_EXPLAINED",
            message: "not shown",
            retryable: false,
            stage: "profile",
            correlation_id: "c2",
            details: {},
          },
        },
      },
    ]);
    const { user } = renderDirections(discoveryWith(explanation("failed", null, true)));

    await card();
    await user.click(screen.getByRole("button", { name: "Try again : the written note" }));

    expect(
      await screen.findByText(/No written note: These suggestions have had their one written note/),
    ).toBeVisible();
    expect(screen.getByRole("button", { name: "Suggest again" })).toBeVisible();
    expect(screen.queryByText("not shown")).toBeNull();
  });

  it("says a suggestion from a changed view has no note, and asks nothing for it", async () => {
    const sent = fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([other]) }]);
    renderDirections();

    const shown = within(await screen.findByRole("article", { name: "Tree surgeon" }));
    expect(shown.getByText(/appeared when you changed the view/)).toBeVisible();
    expect(
      shown.getByText(
        "What you enjoy: “working outdoors”. Careerwright searched for “working outdoors”, and ESCO lists “work in outdoor conditions” as an essential skill for this work.",
      ),
    ).toBeVisible();
    expect(noteRequests(sent)).toHaveLength(0);
  });

  it("asks for no note without a key, or for answers that have changed since", async () => {
    const sent = fakeApi([slateRoute]);
    renderDirections(discoveryWith(null), "Store a Meta API key to continue.");
    await card();
    // Made from earlier answers: the API's own rule (STATE-10), no longer a version compare.
    const stale = { ...discoveryWith(null), profile_version: 1, current: false } as DiscoveryOut;
    renderDirections(stale);
    await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(2));

    expect(noteRequests(sent)).toHaveLength(0);
    expect(screen.queryByText("How Careerwright found it")).toBeNull(); // nothing to set it apart from
  });
});

const skill = (id: string, label: string) => ({ skill_id: id, label, skill_type: "skill" });
const GROUP = { code: "7231", label: "Motor vehicle mechanics and repairers" };
/** The targets as stored once (`GET .../targets`): this one names occupation `conceptId`. */
const storedAs = (title?: string, conceptId?: string): TargetRecordsOut => ({
  profile_version: 3,
  targets:
    title === undefined
      ? []
      : [
          {
            key: title,
            title,
            kind: "esco",
            link: "occupation_choice",
            concept_id: conceptId ?? null,
            label_matches: 1,
            coverage: "not_covered",
            pack_target_id: null,
            on_a_list: true,
          },
        ],
});
const joinedBy = (answer: string): SuggestionOut["reasons"] => [
  {
    reason: "joined_by_shared_skills",
    outcome: "found_work",
    field: "current_role",
    answer,
    shared: 5,
  },
];
const joined: SuggestionOut = {
  ...suggestion,
  channels: ["shared_skills"],
  reasons: joinedBy("bicycle courier"),
  shared_skills: [
    skill("k1", "adjust brakes"),
    skill("k2", "fit tyres"),
    skill("k3", "replace chains"),
    skill("k4", "true wheels"),
    skill("k5", "use hand tools"),
  ],
};
/** Joined to the person's role, which they called "cycle courier" and ESCO titles "bicycle
 *  courier" (an alternative title). */
const connected: SuggestionOut = { ...joined, reasons: joinedBy("cycle courier") };

describe("[STATE-10][DIV1-10][WLD-10] the skills a suggestion shares, as a plain line, and a chosen target", () => {
  it("names the first skills it was joined by, the rest one step away (the audit's F4)", async () => {
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([joined]) }]);
    const { user } = renderDirections();

    const mechanic = await card();
    // The reason above says how they were joined; this line only names the skills (D-I2).
    const first = within(mechanic).getByText(
      "Among them: adjust brakes, fit tyres and replace chains.",
    );
    expect(first).not.toBeVisible();
    await user.click(within(mechanic).getByText("More about this role"));
    expect(first).toBeVisible();
    const rest = within(mechanic).getByText("The other 2 skills");
    expect(within(mechanic).getByText("true wheels")).not.toBeVisible();
    await user.click(rest);
    expect(within(mechanic).getByText("true wheels")).toBeVisible();
    expect(within(mechanic).getByText("use hand tools")).toBeVisible();
  });

  it("names all the skills it was joined by when there are only a few", async () => {
    const few = { ...joined, shared_skills: joined.shared_skills.slice(0, 3) };
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([few]) }]);
    const { user } = renderDirections();

    const mechanic = await card();
    await user.click(within(mechanic).getByText("More about this role"));
    expect(
      within(mechanic).getByText("Those skills: adjust brakes, fit tyres and replace chains."),
    ).toBeVisible();
    expect(within(mechanic).queryByText(/The other/)).toBeNull();
  });

  it("[MAP1-09] states the skills a suggestion shares with the role as a plain line, never as a discovery (the product owner, 1 November 2026)", async () => {
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([connected]) }]);
    const { user } = renderDirections();

    const mechanic = await card();
    await user.click(within(mechanic).getByText("More about this role"));
    expect(
      within(mechanic).getByText("Among them: adjust brakes, fit tyres and replace chains."),
    ).toBeVisible();
    expect(mechanic).not.toHaveTextContent(/unexpected|connection/i);
    // ESCO named plainly where the suggestions first name it, short enough to keep the first
    // decision in a phone's first screen (UI-12).
    expect(
      screen.getByText(
        "Occupations from ESCO, the EU's list of jobs and skills, found from your answers. Ideas to test, not a judgement of fit.",
      ),
    ).toBeVisible();
    expect(within(mechanic).getByText("true wheels")).not.toBeVisible();
    await user.click(within(mechanic).getByText("The other 2 skills"));
    expect(within(mechanic).getByText("true wheels")).toBeVisible();
  });

  it("states the join once on each card, and never calls ESCO's title the person's role (D-I2, A-M1)", async () => {
    const plain = { ...joined, concept_id: "o2", title: "bicycle repairer" };
    fakeApi([{ method: "GET", path: /\/slate$/, answer: slate([connected, plain]) }]);
    const { user } = renderDirections();

    const mechanic = await card();
    await user.click(await screen.findByRole("button", { name: /Bicycle repairer/ }));
    const repairer = await screen.findByRole("article", { name: "Bicycle repairer" });
    const joins = (shown: HTMLElement) => shown.textContent?.match(/joined/g)?.length ?? 0;
    await waitFor(() => expect(joins(repairer)).toBe(1)); // the reason that found it, once
    await user.click(within(mechanic).getByRole("button", { name: /Bicycle mechanic/ }));
    await waitFor(() => expect(joins(mechanic)).toBe(1));
    // The person said "cycle courier"; ESCO titles their role "bicycle courier". The card quotes
    // the person's words only, and never names ESCO's title as "your role".
    expect(mechanic).toHaveTextContent("“cycle courier”");
    expect(mechanic).not.toHaveTextContent("“bicycle courier”");
    expect(mechanic).not.toHaveTextContent(/your role/i);
  });

  it("[PROF-10] says a chosen target is saved, how far it is covered and what it asks for", async () => {
    const chosen: ProfileOut = {
      ...profile,
      version: 3,
      document: {
        ...profile.document,
        target_titles: { state: "provided", value: ["bicycle mechanic"], source_ref_id: "s2" },
      },
    };
    const sketch = {
      profile_version: 3,
      inputs: {},
      not_asked: [],
      steps: [],
      targets: [
        {
          title: "bicycle mechanic",
          resolution: "esco",
          occupations: [{ concept_id: "o1", title: "bicycle mechanic", isco_group: GROUP }],
          close_matches: [],
          requirements: ["adjust brakes", "fit tyres"],
          requirement_count: 9,
          regulated: false,
          coverage: "not_covered",
        },
      ],
    };
    fakeApi([
      slateRoute,
      { method: "GET", path: /\/sketch$/, answer: sketch },
      { method: "GET", path: /\/targets$/, answer: storedAs("bicycle mechanic", "o1") },
    ]);
    // Made at version 2; version 3 only added this target, chosen from it: still current.
    renderDirections(discovery, undefined, chosen);

    const mechanic = await card();
    expect(
      await within(mechanic).findByRole("heading", { name: "Saved as one of your targets" }),
    ).toBeVisible();
    // Coverage, from the target's stored record, in one plain line.
    expect(
      within(mechanic).getByText(
        "Careerwright can show the skills ESCO lists for this kind of work. It can't check skills, options or routes for it yet.",
      ),
    ).toBeVisible();
    // ESCO's list for the kind of work, never what the work "usually" asks (the PO's research).
    expect(within(mechanic).getByText("ESCO lists these for this kind of work:")).toBeVisible();
    expect(mechanic).not.toHaveTextContent(/usually/);
    expect(within(mechanic).getByText("Adjust brakes")).toBeVisible();
    expect(within(mechanic).getByText("And 7 more essential skills in ESCO.")).toBeVisible();
    expect(within(mechanic).queryByRole("button", { name: /Make this a target/ })).toBeNull();
    // Never "out of date" for the person's own choice, and Suggest again isn't pushed.
    expect(screen.queryByText("Based on your earlier answers")).toBeNull();
    expect(screen.queryByRole("button", { name: "Suggest again" })).toBeNull();
  });

  it("moves focus to the words that say the target is saved, where it was chosen", async () => {
    const state = { profile, chosen: false };
    fakeApi([
      slateRoute,
      {
        method: "POST",
        path: /\/targets$/,
        status: 201,
        answer: () => {
          state.profile = {
            ...profile,
            version: 3,
            document: {
              ...profile.document,
              target_titles: {
                state: "provided",
                value: ["bicycle mechanic"],
                source_ref_id: "s2",
              },
            },
          };
          state.chosen = true;
          return state.profile;
        },
      },
      {
        method: "GET",
        path: /\/sketch$/,
        answer: { profile_version: 3, inputs: {}, not_asked: [], steps: [], targets: [] },
      },
      {
        method: "GET",
        path: /\/targets$/,
        answer: () => (state.chosen ? storedAs("bicycle mechanic", "o1") : storedAs()),
      },
    ]);
    const { user, rerenderWith } = renderChoosing();

    await user.click(await screen.findByRole("button", { name: /Make this a target/ }));
    rerenderWith(state.profile);

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Saved as one of your targets" })).toHaveFocus(),
    );
  });

  it("still marks a slate made from earlier answers, with Suggest again as the bright action", async () => {
    fakeApi([slateRoute]);
    renderDirections({ ...discovery, current: false } as DiscoveryOut);

    expect(await screen.findByText("Based on your earlier answers")).toBeVisible();
    expect(screen.getByRole("button", { name: "Suggest again" })).toHaveClass("btn-primary");
  });

  it("[PROF-07] removes a saved suggestion from the targets in place, with Undo, and Make this a target is bright again", async () => {
    // Session W2 (finding 2): the saved box has its own Remove, through the profile's save.
    // Removing a target leaves the slate current (the API's rule), so Suggest again stays quiet.
    const targets = (titles: string[]) => ({
      state: "provided" as const,
      value: titles,
      source_ref_id: "s2",
    });
    const state = {
      profile: {
        ...profile,
        version: 3,
        document: { ...profile.document, target_titles: targets(["bicycle mechanic", "cook"]) },
      } as ProfileOut,
    };
    const held = () => state.profile.document.target_titles.value ?? [];
    const sent = fakeApi([
      slateRoute,
      {
        method: "GET",
        path: /\/sketch$/,
        answer: { profile_version: 3, inputs: {}, not_asked: [], steps: [], targets: [] },
      },
      {
        method: "GET",
        path: /\/targets$/,
        answer: () =>
          held().includes("bicycle mechanic") ? storedAs("bicycle mechanic", "o1") : storedAs(),
      },
      {
        method: "PUT",
        path: /\/profile$/,
        status: 201,
        answer: () => {
          state.profile = {
            ...state.profile,
            version: 4,
            document: { ...state.profile.document, target_titles: targets(["cook"]) },
          };
          return { ...state.profile, support_note: null };
        },
      },
      {
        method: "POST",
        path: /\/profile\/revert$/,
        status: 201,
        answer: () => {
          state.profile = {
            ...state.profile,
            version: 5,
            document: {
              ...state.profile.document,
              target_titles: targets(["bicycle mechanic", "cook"]),
            },
          };
          return state.profile;
        },
      },
    ]);
    const { user, rerenderWith } = renderChoosing(state.profile);

    const mechanic = await card();
    await within(mechanic).findByRole("heading", { name: "Saved as one of your targets" });
    await user.click(
      within(mechanic).getByRole("button", { name: "Remove Bicycle mechanic from your targets" }),
    );
    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    expect(sent.find((s) => s.method === "PUT")?.body).toMatchObject({
      expected_version: 3,
      profile: { target_titles: { state: "provided", value: ["cook"] } },
    });
    rerenderWith(state.profile);

    const removed = await within(mechanic).findByRole("heading", {
      name: "Removed “bicycle mechanic” from your targets",
    });
    await waitFor(() => expect(removed).toHaveFocus());
    const choose = await within(mechanic).findByRole("button", { name: /Make this a target/ });
    expect(choose).toHaveClass("btn-primary");
    expect(screen.queryByRole("button", { name: "Suggest again" })).toBeNull();

    await user.click(
      within(mechanic).getByRole("button", { name: "Undo removing “bicycle mechanic”" }),
    );
    await waitFor(() =>
      expect(sent.find((s) => s.path.endsWith("/profile/revert"))?.body).toEqual({
        expected_version: 4,
        to_version: 3,
      }),
    );
    rerenderWith(state.profile);
    await waitFor(() =>
      expect(
        within(mechanic).getByRole("heading", {
          name: "Undone: “bicycle mechanic” is one of your targets again",
        }),
      ).toHaveFocus(),
    );
    expect(
      await within(mechanic).findByRole("heading", { name: "Saved as one of your targets" }),
    ).toBeVisible();
  });

  it("says where to remove a target when there are already three", async () => {
    const three = ["cook", "baker", "tailor"];
    const stored: TargetRecordsOut = {
      profile_version: 2,
      targets: three.flatMap((title) => storedAs(title).targets),
    };
    fakeApi([slateRoute, { method: "GET", path: /\/targets$/, answer: stored }]);
    const full: ProfileOut = {
      ...profile,
      document: {
        ...profile.document,
        target_titles: { state: "provided", value: three, source_ref_id: "s2" },
      },
    };
    renderDirections(discovery, undefined, full);

    const choose = await within(await card()).findByRole("button", { name: /Make this a target/ });
    await waitFor(() => expect(choose).toHaveAttribute("aria-disabled", "true"));
    expect(choose).toHaveAccessibleDescription(
      "You have 3 targets, the most you can have. To add this one, remove one in What we know.",
    );
  });
});

describe("[REC1-05] an open suggestion: its title, what the work is and its kind of work told apart", () => {
  it("heads ESCO's description What the work is, at reading size, with the kind of work under it, after the choice", async () => {
    // Session W2 (finding 8): "Kind of work" read as a second title, and the description had
    // no heading. The choice still comes right after the title (D-I3).
    fakeApi([slateRoute]);
    renderDirections();

    const mechanic = await card();
    const choose = within(mechanic).getByRole("button", { name: /Make this a target/ });
    const heading = within(mechanic).getByText("What the work is");
    const description = within(mechanic).getByText(
      "Bicycle mechanics maintain and repair bicycles.",
    );
    const why = within(mechanic).getByText("Why this could suit you");
    const more = within(mechanic).getByText("More about this role");
    const kind = within(mechanic).getByText("Kind of work: Machinery mechanics and repairers");
    const follows = (first: Node, then: Node) =>
      (first.compareDocumentPosition(then) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
    expect(heading).toHaveClass("section-title");
    expect(
      follows(choose, heading) &&
        follows(heading, description) &&
        follows(description, why) &&
        follows(why, more) &&
        follows(more, kind),
    ).toBe(true);
    expect(description).not.toHaveClass("small"); // body size, never the 14 px of a note
    expect(kind).not.toBeVisible();
    await userEvent.setup().click(more);
    expect(kind).toBeVisible();
    expect(within(mechanic).getAllByText(/^Kind of work:/)).toHaveLength(1);
  });
});

/** Directions whose profile the test replaces after a choice, as the shell's query would. */
function renderChoosing(first: ProfileOut = profile) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = (shown: ProfileOut) => (
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <Directions workspaceId={WS} profile={shown} discovery={discovery} />
      </EvidenceProvider>
    </QueryClientProvider>
  );
  const { rerender } = render(view(first));
  return { user: userEvent.setup(), rerenderWith: (shown: ProfileOut) => rerender(view(shown)) };
}
