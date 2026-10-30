// The You chapter's states (S2.3-S2.5, S2.7) on a scripted API at the network edge: the
// start, a reply streaming and to review, a failed reply, paused; the slate full and thin,
// with its written note written, pending and unavailable, and with a salary floor applied;
// key consent and a stored key; and the early sketch with a target. Every value is synthetic.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { Directions } from "@/components/Directions";
import { KeySetup } from "@/components/KeySetup";
import { YouChapter } from "@/components/YouChapter";
import type {
  CredentialOut,
  DiscoveryOut,
  PreferencesOut,
  ProfileOut,
  RunOut,
  SketchOut,
  SlateExplanationOut,
  SlateOut,
  SuggestionOut,
  TurnOut,
  WorkState,
  WorkspaceOut,
  WrittenExplanationOut,
} from "@/generated/api";
import { fakeApi, type Route } from "@/test/fakeApi";

const WS = "w-story";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const given = <T,>(value: T) => ({ state: "provided" as const, value, source_ref_id: "s1" });
const profile: ProfileOut = {
  workspace_id: WS,
  version: 3,
  created_by: null,
  created_at: "2027-01-01T00:00:00Z",
  document: {
    schema_version: "3",
    preferred_name: unasked,
    current_role: given("Warehouse shift supervisor"),
    cities: given(["Leeds", "Manchester"]),
    target_titles: unasked,
    weekly_study_hours: given(6),
    direct_spend_cap: { state: "prefer_not_to_say", value: null, source_ref_id: "s1" },
    monthly_payment_cap: unasked,
    enjoyed_tasks: given(["repairing physical objects", "working outdoors"]),
    confident_tasks: unasked,
    evidenced_tasks: unasked,
    work_style: { state: "skipped", value: null, source_ref_id: "s1" },
    minimum_salary: unasked,
  },
};
const workspace = (mode: WorkspaceOut["data_mode"]): WorkspaceOut => ({
  workspace_id: WS,
  name: "Story (synthetic)",
  data_mode: mode,
  synthetic: true,
  fixture: false,
  version: 1,
  last_event_seq: 0,
  created_at: "2027-01-01T00:00:00Z",
  updated_at: "2027-01-01T00:00:00Z",
});
const prefs = (entry: PreferencesOut["entry_mode"], paused = false): PreferencesOut => ({
  version: entry === null ? 0 : 1,
  entry_mode: entry,
  conversation_mode: "gentle",
  paused,
  updated_at: null,
});
const turn = (status: TurnOut["run"]["status"], proposal: TurnOut["proposal"] = null): TurnOut => ({
  turn_id: "t1",
  message_id: "m1",
  message:
    "Synthetic persona: at my last job I liked fixing the machines more than the paperwork, and I'd rather be outside.",
  profile_version: 3,
  created_at: "2027-01-01T10:00:00Z",
  run: {
    run_id: "t1",
    kind: "interview_turn",
    status,
    failure_class: status === "failed" ? "invalid_model_output" : null,
    data_mode: "demo",
    synthetic: true,
    model_id: "careerwright-fixture-interviewer-1",
    model_mode: "fixture",
    created_at: "2027-01-01T10:00:00Z",
    started_at: null,
    finished_at: null,
    attempts: [],
    output: null,
    profile_version: 3,
  },
  proposal,
  decision: null,
});
const proposal: TurnOut["proposal"] = {
  origin: "fixture",
  prompt_version: "interview-turn-2",
  profile_version: 3,
  reply:
    "Demo interviewer (synthetic): you enjoy repairing things and being outdoors. I noted both as interests to explore, not as limits.",
  changes: [
    {
      change_id: "c1",
      field: "enjoyed_tasks",
      state: "provided",
      value: ["repairing physical objects", "working outdoors", "fixing machines"],
      basis: "stated",
      message_ids: ["m1"],
      reason: "You said you liked fixing the machines.",
      hard_constraint: false,
    },
    {
      change_id: "c2",
      field: "work_style",
      state: "provided",
      value: ["practical", "outdoors"],
      basis: "inferred",
      message_ids: ["m1"],
      reason: "You said you'd rather be outside than at a desk.",
      hard_constraint: false,
    },
    {
      change_id: "c3",
      field: "minimum_salary",
      state: "provided",
      value: { amount: { minor_units: 2400000, currency: "GBP" }, period: "year", basis: "gross" },
      basis: "inferred",
      message_ids: ["m1"],
      reason: "A floor you mentioned earlier.",
      hard_constraint: true,
    },
  ],
  next_question: "Which kinds of machines did you most like fixing?",
  missing_critical_fields: [],
  ready_for_review: true,
};
const sketch: SketchOut = {
  label: "Early sketch, not a checked route",
  profile_version: 3,
  inputs: {},
  not_asked: ["target_titles"],
  targets: [],
  steps: [],
};
const suggestion = (
  title: string,
  family: string,
  direction: SuggestionOut["direction"],
): SuggestionOut => ({
  concept_id: title,
  concept_kind: "esco",
  title,
  esco_code: "0000.0",
  isco_group: { code: `${family}1`, label: `Group ${family}` },
  family: { code: family, label: `Kind of work ${family}` },
  sector: { code: family[0] ?? "9", label: "Sector" },
  direction,
  channels: ["tasks"],
  linked_evidence: [{ field: "enjoyed_tasks", text: "repairing physical objects" }],
  matched_queries: ["q1"],
  sources: [
    {
      kind: "esco",
      uri: `http://data.europa.eu/esco/occupation/${family}`,
      release: "esco-v1.2.1-en-csv",
    },
  ],
  workday: `${title} work, as ESCO describes it: a synthetic description for this story.`,
  why_it_could_suit: [
    "What you enjoy: “repairing physical objects”. Careerwright searched for “machinery repair”, and ESCO's record for this occupation matched.",
  ],
  what_might_not_suit: [
    "ESCO lists 12 essential skills, not yet compared with your experience, including: use hand tools, read technical drawings, test equipment.",
  ],
  entry_gates: ["Entry requirements aren't researched yet."],
  evidence_gaps: [
    "Pay, demand and listings in your work areas aren't researched yet. Finding no listings later would be a demand signal, not proof this work doesn't exist.",
  ],
  try_it: [
    `Talk to someone who works as a ${title} about a typical week (an informational interview).`,
  ],
});
const slate = (suggestions: SuggestionOut[]): SlateOut => ({
  discovery_id: "d1",
  profile_version: 3,
  release: {
    dataset_id: "esco-v1.2.1-en-csv",
    version: "v1.2.1",
    attribution: "This service uses the ESCO classification of the European Commission.",
    adaptation: "Adapted import.",
    sample: false,
  },
  emphasis: "balanced",
  target_size: 6,
  family_limit: 2,
  suggestions,
  fewer_reasons:
    suggestions.length < 6
      ? [
          "Only 2 occupations matched your answers closely enough to suggest. Careerwright doesn't fill the rest with weaker matches.",
        ]
      : [],
  notes: [],
  salary_floor: null,
  ai_resilience_filter: {
    minimum: null,
    include_unscored: true,
    scored: 0,
    below_minimum: 0,
    unscored: suggestions.length < 6 ? 2 : 94,
    unscored_excluded: 0,
    synthetic: false,
    pack_version: "l0-2026-10-29",
    pack_dated: "2026-10-29",
    summary: null,
  },
  pool_size: suggestions.length < 6 ? 2 : 94,
  pool_target: [60, 120],
  beyond_pool_limit: 0,
  excluded: { occupations: 0, families: 0 },
  queries: [
    {
      query_id: "q1",
      text: "machinery repair",
      channel: "tasks",
      based_on: [{ field: "enjoyed_tasks", text: "repairing physical objects" }],
      hits: 30,
    },
  ],
  unsearchable_queries: [],
  unsupported_hypotheses: [],
  not_included: [],
});
const full = [
  suggestion("agricultural machinery technician", "723", "close_to_current"),
  suggestion("warehouse manager", "432", "close_to_current"),
  suggestion("facilities technician", "311", "transferable"),
  suggestion("training coordinator", "242", "transferable"),
  suggestion("tree surgeon", "621", "less_familiar"),
  suggestion("wind turbine technician", "311", "less_familiar"),
];
// The written note (S2.7): synthetic claims quoting the story's answers and ESCO's words
// the cards show (the skill "use hand tools" and each title).
const writtenFor = (shown: SuggestionOut[]): WrittenExplanationOut => ({
  origin: "model",
  prompt_version: "slate-explanation-1",
  profile_version: 3,
  release: "esco-v1.2.1-en-csv",
  suggestions: shown.map((s, n) => ({
    concept_id: s.concept_id,
    title: s.title,
    claims: [
      {
        text: "You enjoy repairing things with your hands, and hand tools are part of the everyday work here.",
        quotations: [
          {
            source: "answer",
            answer_field: "enjoyed_tasks",
            record_part: null,
            text: "repairing physical objects",
          },
          {
            source: "esco",
            answer_field: null,
            record_part: "essential_skill",
            text: "use hand tools",
          },
        ],
      },
      ...(n % 2 === 0
        ? [
            {
              text: `You said you like being outside, which fits the way ESCO describes work as ${s.title}.`,
              quotations: [
                {
                  source: "answer" as const,
                  answer_field: "enjoyed_tasks" as const,
                  record_part: null,
                  text: "working outdoors",
                },
                {
                  source: "esco" as const,
                  answer_field: null,
                  record_part: "title" as const,
                  text: s.title,
                },
              ],
            },
          ]
        : []),
    ],
  })),
});
// A failed note either sent its request (invalid twice) or reached no model (over budget).
const noteRun = (status: WorkState, reachedNoModel: boolean) =>
  ({
    run_id: "e1",
    kind: "slate_explanation",
    status,
    failure_class:
      status === "failed" ? (reachedNoModel ? "budget_exceeded" : "invalid_model_output") : null,
  }) as unknown as RunOut;
const discoveryWith = (explanation: SlateExplanationOut | null) =>
  ({
    discovery_id: "d1",
    profile_version: 3,
    run: { status: "complete" },
    proposal: null,
    explanation,
  }) as unknown as DiscoveryOut;
const note = (
  status: WorkState,
  shown: SuggestionOut[],
  reachedNoModel: boolean,
): SlateExplanationOut => ({
  explanation_id: "e1",
  discovery_id: "d1",
  run: noteRun(status, reachedNoModel),
  can_retry: status === "failed" && reachedNoModel,
  written: status === "complete" ? writtenFor(shown) : null,
});
const stored: CredentialOut = {
  credential_id: "c1",
  provider: "meta",
  active: true,
  consented_at: "2027-01-01T00:00:00Z",
  created_by: "a1",
  created_at: "2027-01-01T00:00:00Z",
  revoked_at: null,
  replaced_by: null,
};

function Api({ routes, children }: { routes: Route[]; children: ReactNode }) {
  const [queries] = useState(() => {
    fakeApi(routes);
    return new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  });
  return <QueryClientProvider client={queries}>{children}</QueryClientProvider>;
}

const chapterRoutes = (preferences: PreferencesOut, turns: TurnOut[], reply?: object): Route[] => [
  { method: "GET", path: /\/interview\/preferences$/, answer: preferences },
  {
    method: "GET",
    path: /\/interview\/turns$/,
    answer: { items: [...turns].reverse(), next_cursor: null },
  },
  {
    method: "GET",
    path: /\/turns\/t1\/reply$/,
    answer: reply ?? {
      turn_id: "t1",
      completeness: "none",
      seq: null,
      text: null,
      updated_at: null,
    },
  },
  { method: "GET", path: /\/discoveries$/, answer: { items: [], next_cursor: null } },
  { method: "GET", path: /\/sketch$/, answer: sketch },
];

const meta: Meta = { title: "You", parameters: { surface: "reading" } };
export default meta;
type Story = StoryObj;

const you = (routes: Route[]) => () => (
  <Api routes={routes}>
    <div className="chapter chapter-you on-reading">
      <YouChapter workspace={workspace("demo")} profile={profile} />
    </div>
  </Api>
);

export const Start: Story = { render: you(chapterRoutes(prefs(null), [])) };
export const ReplyStreaming: Story = {
  render: you(
    chapterRoutes(prefs("unsure"), [turn("running")], {
      turn_id: "t1",
      completeness: "streaming",
      seq: 2,
      text: "Demo interviewer (synthetic): you enjoy repairing",
      updated_at: null,
    }),
  ),
};
export const ReplyToReview: Story = {
  render: you(chapterRoutes(prefs("unsure"), [turn("complete", proposal)])),
};
export const ReplyFailed: Story = { render: you(chapterRoutes(prefs("unsure"), [turn("failed")])) };
export const Paused: Story = {
  render: you(chapterRoutes(prefs("unsure", true), [turn("complete", proposal)])),
};

const directions =
  (shown: SuggestionOut[], status: WorkState = "complete", reachedNoModel = false) =>
  () => (
    <Api routes={[{ method: "GET", path: /\/slate$/, answer: slate(shown) }]}>
      <Directions
        workspaceId={WS}
        profile={profile}
        discovery={discoveryWith(note(status, shown, reachedNoModel))}
      />
    </Api>
  );
/** The slate with its written note: model prose, its checked quotations, then how it was found. */
export const SlateOfSix: Story = { render: directions(full) };
export const SlateThin: Story = { render: directions(full.slice(0, 2)) };
/** The note still being written: how each suggestion was found is shown meanwhile. */
export const SlateNotePending: Story = { render: directions(full, "running") };
/** The note failed its checks twice: unavailable with its failure, provenance kept, and
 *  Suggest again (the slate had its one call). */
export const SlateNoteUnavailable: Story = { render: directions(full, "failed") };
/** The note was refused before any request reached a model: Try again, on a click. */
export const SlateNoteRetry: Story = { render: directions(full, "failed", true) };
/** A confirmed salary floor (slice 7B fix round 1, review A M8): applied, with what it left
 *  out, what met it and why the rest were kept. In L0 no UK occupation mapping is reviewed,
 *  so it leaves no suggestion out, and says so. */
export const SlateWithSalaryFloor: Story = {
  render: () => (
    <Api
      routes={[
        {
          method: "GET",
          path: /\/slate$/,
          answer: {
            ...slate(full),
            salary_floor: {
              amount: { minor_units: 2_600_000, currency: "GBP" },
              period: "year",
              left_out: 0,
              meets: 0,
              kept_pay_unknown: 94,
              kept_by_reason: [{ reason: "no_reviewed_mapping", count: 94 }],
              summary:
                "Your minimum salary of £26,000 a year (gross) is applied: 0 left out because their official pay is below it; 0 meet it; 94 kept because no reviewed UK occupation code links them to pay data. Unknown pay is never treated as below it.",
            },
          },
        },
      ]}
    >
      <Directions
        workspaceId={WS}
        profile={profile}
        discovery={discoveryWith(note("complete", full, false))}
      />
    </Api>
  ),
};
/** Asking for the note was refused because no answer has a word to quote: asking again
 *  would repeat it, so the person is told to change their answers (no Try again). */
export const SlateNoteAnswersTooShort: Story = {
  render: () => (
    <Api
      routes={[
        { method: "GET", path: /\/slate$/, answer: slate(full) },
        {
          method: "POST",
          path: /\/explanation$/,
          status: 422,
          answer: {
            error: {
              code: "INSUFFICIENT_EVIDENCE",
              message: "",
              retryable: false,
              stage: "profile",
              correlation_id: "story",
              details: { reason: "no_quotable_answer" },
            },
          },
        },
      ]}
    >
      <Directions workspaceId={WS} profile={profile} discovery={discoveryWith(null)} />
    </Api>
  ),
};

const key = (credentials: CredentialOut[]) => () => (
  <Api routes={[]}>
    <KeySetup workspace={workspace("live_assisted")} credentials={credentials} primary />
  </Api>
);
export const KeyConsent: Story = { render: key([]) };
export const KeyStored: Story = { render: key([stored]) };
