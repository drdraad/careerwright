// Directions to explore (REC-1, DIV-1): a grounded slate in words with no percentage; the
// controls change the view only; a suggestion becomes a target only when chosen.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type {
  DiscoveryOut,
  ProfileOut,
  SlateExplanationOut,
  SlateOut,
  SuggestionOut,
  WorkState,
} from "@/generated/api";
import { fakeApi, type Route, type Sent } from "@/test/fakeApi";
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

function renderDirections(shown: DiscoveryOut = discovery, unavailable?: string) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = (found: DiscoveryOut) => (
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <Directions
          workspaceId={WS}
          profile={profile}
          discovery={found}
          {...(unavailable === undefined ? {} : { unavailable })}
        />
      </EvidenceProvider>
    </QueryClientProvider>
  );
  const { rerender } = render(view(shown));
  return { user: userEvent.setup(), rerender: (found: DiscoveryOut) => rerender(view(found)) };
}

const slateRoute: Route = { method: "GET", path: /\/slate$/, answer: () => slate([suggestion]) };
const card = async () => screen.findByRole("article", { name: "Bicycle mechanic" });

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
    const { user } = renderDirections();

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

const NOTE_PATH = "/v1/workspaces/w-dir/discoveries/d1/explanation";
const noteRequests = (sent: Sent[]) =>
  sent.filter((s) => s.method === "POST" && s.path === NOTE_PATH);
const other: SuggestionOut = {
  ...suggestion,
  concept_id: "o3",
  title: "tree surgeon",
  why_it_could_suit: ["What you enjoy: “working outdoors”."],
};

describe("[REC1-11] the written why: one request per slate, its states, provenance always", () => {
  it("asks once when the slate first shows, and a changed view never asks again", async () => {
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
    await user.click(screen.getByRole("button", { name: "Less familiar" }));
    await waitFor(() =>
      expect(sent.some((s) => s.query.includes("emphasis=unfamiliar"))).toBe(true),
    );
    await user.click(screen.getByRole("button", { name: "Not for me : Bicycle mechanic" }));
    await waitFor(() => expect(sent.some((s) => s.query.includes("exclude_concept"))).toBe(true));

    expect(noteRequests(sent)).toHaveLength(1);
    expect(noteRequests(sent)[0]?.body).toEqual({ expected_profile_version: 2 });
  });

  it("shows the note and each checked quotation above how Nessa found it", async () => {
    const sent = fakeApi([slateRoute]);
    renderDirections();

    const shown = within(await card());
    const note = shown.getByText(/mostly maintaining and repairing them/);
    const found = shown.getByText("What you enjoy: “repairing bicycles”.");
    expect(shown.getByText("You said:")).toBeVisible();
    expect(shown.getByText("ESCO's description:")).toBeVisible();
    expect(shown.getByText(/“maintain and repair bicycles”/)).toBeVisible();
    // Fix round 1 (I2): it says what was checked, and that the sentence is the model's own.
    expect(
      shown.getByText(
        /Only the quoted words were checked against them; the sentences are Nessa's own\./,
      ),
    ).toBeVisible();
    expect(shown.queryByText(/checked word for word/)).toBeNull();
    expect(shown.getByText("How Nessa found it")).toBeVisible();
    // The deterministic provenance stays, after the written note.
    expect(note.compareDocumentPosition(found) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(noteRequests(sent)).toHaveLength(0); // already written: nothing asked
    expect(document.body.textContent).not.toMatch(/\d\s?(%|per ?cent)/i);
  });

  it("says when the note is still being written, and labels the demo explainer's", async () => {
    fakeApi([slateRoute]);
    const { rerender } = renderDirections(discoveryWith(explanation("running")));

    expect(await within(await card()).findByText(/writing a note/)).toBeVisible();
    expect(screen.getByText("What you enjoy: “repairing bicycles”.")).toBeVisible();
    rerender(
      discoveryWith(explanation("complete", { ...WRITTEN, origin: "fixture" } as typeof WRITTEN)),
    );
    expect(await screen.findByText(/Written by the demo explainer \(synthetic\)/)).toBeVisible();
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
      shown.getByText(/The reply didn't pass Nessa's checks twice\. Nothing from it/),
    ).toBeVisible();
    expect(shown.getByText("What you enjoy: “repairing bicycles”.")).toBeVisible();
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
    expect(screen.getByText("Raise the limit or wait for the next month.")).toBeVisible();
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
    expect(shown.getByText("What you enjoy: “repairing bicycles”.")).toBeVisible();
    expect(screen.getByText("Nothing was sent to the model.")).toBeVisible();
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
      words: /No written note: Your answers are too short to quote/,
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
          screen.getByText(/Edit answers directly\. Nessa then offers Suggest again\./),
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
    expect(shown.getByText("What you enjoy: “working outdoors”.")).toBeVisible();
    expect(noteRequests(sent)).toHaveLength(0);
  });

  it("asks for no note without a key, or for answers that have changed since", async () => {
    const sent = fakeApi([slateRoute]);
    renderDirections(discoveryWith(null), "Store a Meta API key to continue.");
    await card();
    const stale = { ...discoveryWith(null), profile_version: 1 } as DiscoveryOut;
    renderDirections(stale);
    await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(2));

    expect(noteRequests(sent)).toHaveLength(0);
    expect(screen.queryByText("How Nessa found it")).toBeNull(); // nothing to set it apart from
  });
});
