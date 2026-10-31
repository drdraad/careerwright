// The You chapter's states (S2.3-S2.5, S2.7, SW.4) on a scripted API at the network edge: the
// start, a reply streaming and to review (one with a limit to confirm), a failed reply,
// paused; its other views, what we know and the suggestions; a save with Undo and an undo; the
// slate full and thin, with its written note written, pending and unavailable, and with a
// salary floor applied; key consent and a stored key; and the early sketch with a target.
// Every value is synthetic.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { Directions } from "@/components/Directions";
import { KeySetup } from "@/components/KeySetup";
import { SaveNotice } from "@/components/WhatWeKnow";
import { YouChapter, type YouView } from "@/components/YouChapter";
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
  asks_about: null,
  missing_critical_fields: [],
  ready_for_review: true,
};
const sketch: SketchOut = {
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
  reasons: [
    {
      reason: "searched_through_skill",
      outcome: "found_work",
      field: "enjoyed_tasks",
      answer: "repairing physical objects",
      search: "repair equipment",
      skill: "repair equipment on site",
    },
  ],
  essential_skill_count: 12,
  essential_skills: ["use hand tools", "read technical drawings", "test equipment"],
  regulated: false,
  different_kind_of_work: false,
  shared_skills: [],
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
  fewer_reasons: suggestions.length < 6 ? [{ reason: "few_matched", count: 2 }] : [],
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
      reach: 30,
      too_general: false,
    },
  ],
  unsearchable_queries: [],
  title_ideas: [],
  not_included: [],
  unmatched_titles: [],
  ambiguous_titles: [],
  connection: null,
  // The stories' role joins work by shared skills, so its kind of work is known.
  familiarity_known: true,
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
    current: true,
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

const you =
  (routes: Route[], view: YouView = "conversation", shown: ProfileOut = profile) =>
  () => (
    <Api routes={routes}>
      <div className="chapter chapter-you on-reading">
        <YouChapter workspace={workspace("demo")} profile={shown} initialView={view} />
      </div>
    </Api>
  );

/** P01-like limits, so "What we know" and the tray explain both in plain words. */
const withLimits: ProfileOut = {
  ...profile,
  document: {
    ...profile.document,
    target_titles: given(["Data quality analyst"]),
    direct_spend_cap: given({ minor_units: 150_000, currency: "GBP" as const }),
    monthly_payment_cap: given({ minor_units: 25_000, currency: "GBP" as const }),
  },
};
const limitProposal: TurnOut["proposal"] = {
  origin: "fixture",
  prompt_version: "interview-turn-2",
  profile_version: 3,
  reply: "Demo interviewer (synthetic): I noted 2 things for you to review.",
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
      change_id: "c3",
      field: "direct_spend_cap",
      state: "provided",
      value: { minor_units: 60_000, currency: "GBP" },
      basis: "inferred",
      message_ids: ["m1"],
      reason: "You said you could spend up to £600.",
      hard_constraint: true,
    },
  ],
  next_question: "How many hours a week could you give to learning?",
  asks_about: null,
  missing_critical_fields: ["weekly_study_hours"],
  ready_for_review: true,
};

// The start (Task 6d slice B): the first question leads; then "Which of these is closest?" for a
// UK job title; then how to start, with what isn't known yet for a title kept in the person's
// own words.
const roleNamed = (title: string): ProfileOut => ({
  ...profile,
  document: { ...profile.document, current_role: given(title) },
});
const originOf = (title: string, kind: "ons" | "own_words", closest: boolean) => ({
  method: "GET",
  path: /\/origin$/,
  answer: {
    profile_version: 3,
    capability_version: 0,
    release: { dataset_id: "esco-v1.2.1-en-csv", sample: false },
    role: {
      text: title,
      state: "not_in_esco",
      chosen: false,
      occupation: null,
      choices: [],
      kind,
      uk_groups: closest ? [{ code: "2221", label: "Nursing professionals" }] : [],
      closest: closest
        ? {
            decision: "not_yet",
            chosen: null,
            groups: [
              {
                group: { code: "2221", label: "Nursing professionals" },
                occupations: [
                  { concept_id: "c1", title: "advanced nurse practitioner", esco_uri: "u1" },
                  {
                    concept_id: "c2",
                    title: "nurse responsible for general care",
                    esco_uri: "u2",
                  },
                  { concept_id: "c3", title: "specialist nurse", esco_uri: "u3" },
                ],
              },
            ],
          }
        : null,
    },
    usual_skills: [],
    destinations: [],
    fewer_reasons: [],
    connection: null,
    salary_floor: null,
  },
});
const unanswered: ProfileOut = {
  ...profile,
  document: { ...profile.document, current_role: unasked },
};
export const Start: Story = {
  render: you(chapterRoutes(prefs(null), []), "conversation", unanswered),
};
export const StartWhichIsClosest: Story = {
  render: you(
    [originOf("Registered nurse", "ons", true), ...chapterRoutes(prefs(null), [])],
    "conversation",
    roleNamed("Registered nurse"),
  ),
};
export const StartInOwnWords: Story = {
  render: you(
    [originOf("Bookkeeping assistant", "own_words", false), ...chapterRoutes(prefs(null), [])],
    "conversation",
    roleNamed("Bookkeeping assistant"),
  ),
};
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
/** A limit to confirm: Accept and Confirm in leaf green, the limit explained in plain words. */
export const ReplyWithALimit: Story = {
  render: you(chapterRoutes(prefs("unsure"), [turn("complete", limitProposal)])),
};
/** What we know, its own view: the answers, the limits explained, the early sketch. */
export const WhatWeKnowView: Story = {
  render: you(chapterRoutes(prefs("unsure"), []), "known", withLimits),
};
/** The suggestions, their own view: one open, its "Make this a target" the bright action. */
export const SuggestionsView: Story = {
  render: you(
    [
      ...chapterRoutes(prefs("unsure"), []).filter((route) => !route.path.test("/discoveries")),
      {
        method: "GET",
        path: /\/discoveries$/,
        answer: { items: [discoveryWith(note("complete", full, false))], next_cursor: null },
      },
      { method: "GET", path: /\/slate$/, answer: slate(full) },
    ],
    "suggestions",
  ),
};
/** After a decision on the tray: what it saved, with Undo in orchid; then what undo did. */
export const SavedWithUndo: Story = {
  render: () => (
    <Api routes={[]}>
      <div className="chapter chapter-you on-reading grid gap-16">
        <SaveNotice
          workspaceId={WS}
          profile={profile}
          outcome={{ kind: "saved", version: profile.version }}
          onUndone={() => {}}
        />
        <SaveNotice
          workspaceId={WS}
          profile={profile}
          outcome={{ kind: "undone", version: profile.version }}
          onUndone={() => {}}
        />
      </div>
    </Api>
  ),
};

/** A decided demo turn whose next question asks about `asks` (Task W2E, STATE-09). */
const asking = (
  asks: NonNullable<TurnOut["proposal"]>["asks_about"],
  question: string,
): TurnOut => ({
  ...turn("complete", {
    ...(proposal as NonNullable<TurnOut["proposal"]>),
    reply: "Demo interviewer (synthetic): Thank you.",
    changes: [],
    next_question: question,
    asks_about: asks,
  }),
});
/** A demo question with its one-tap example replies. */
export const DemoQuestionWithExamples: Story = {
  render: you(
    chapterRoutes(prefs("unsure"), [
      asking("cities", "Which English cities could you work in? Name up to three."),
    ]),
  ),
};
/** "Do you have a role in mind, or would you like to explore?": two ways on, which open
 *  existing views and commit nothing. */
export const RoleOrExplore: Story = {
  render: you(
    chapterRoutes(prefs("unsure"), [
      asking("target_titles", "Do you have a role in mind, or would you like to explore?"),
    ]),
  ),
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
const skill = (id: string, label: string) => ({ skill_id: id, label, skill_type: "skill" });
const joinedSkills = [
  skill("k1", "manage warehouse operations"),
  skill("k2", "plan work schedules"),
  skill("k3", "supervise staff"),
  skill("k4", "ensure health and safety"),
  skill("k5", "use logistics software"),
];
/** Joined to the person's role by shared skills: the first few named, the rest one step away;
 *  the slate's unexpected connection is shown in words on its own suggestion (Task W2E). */
const joined = full.map((shown, i) =>
  i < 2
    ? {
        ...shown,
        channels: ["shared_skills" as const],
        reasons: [
          {
            reason: "joined_by_shared_skills" as const,
            outcome: "found_work" as const,
            field: "current_role" as const,
            answer: "warehouse supervisor",
            shared: 5,
          },
        ],
        shared_skills: joinedSkills,
      }
    : shown,
);
export const SlateJoinedBySkillsWithAConnection: Story = {
  render: () => (
    <Api
      routes={[
        {
          method: "GET",
          path: /\/slate$/,
          answer: {
            ...slate(joined),
            connection: {
              concept_id: joined[0]?.concept_id ?? "",
              title: joined[0]?.title ?? "",
              role_title: "warehouse supervisor",
              shared_skill_count: 5,
              shared_skills: joinedSkills,
            },
          },
        },
      ]}
    >
      <Directions
        workspaceId={WS}
        profile={profile}
        discovery={discoveryWith(note("complete", joined, false))}
      />
    </Api>
  ),
};
/** A suggestion made a target from this slate: confirmed in place with what it usually asks
 *  for, and the slate still current (STATE-10). */
export const SlateTargetChosen: Story = {
  render: () => (
    <Api
      routes={[
        { method: "GET", path: /\/slate$/, answer: slate(full) },
        {
          method: "GET",
          path: /\/sketch$/,
          answer: {
            ...sketch,
            not_asked: [],
            targets: [
              {
                title: "agricultural machinery technician",
                resolution: "esco",
                occupations: [
                  {
                    concept_id: "agricultural machinery technician",
                    title: "agricultural machinery technician",
                    isco_group: { code: "7231", label: "Group 723" },
                  },
                ],
                close_matches: [],
                requirements: ["repair agricultural machinery", "use hand tools", "test equipment"],
                requirement_count: 12,
                regulated: false,
                coverage: "not_covered",
              },
            ],
          },
        },
        {
          method: "GET",
          path: /\/targets$/,
          answer: {
            profile_version: 4,
            targets: [
              {
                key: "agricultural machinery technician",
                title: "agricultural machinery technician",
                kind: "esco",
                link: "occupation_choice",
                concept_id: "agricultural machinery technician",
                label_matches: 1,
                coverage: "not_covered",
                pack_target_id: null,
              },
            ],
          },
        },
      ]}
    >
      <Directions
        workspaceId={WS}
        profile={{
          ...profile,
          version: 4,
          document: {
            ...profile.document,
            target_titles: given(["agricultural machinery technician"]),
          },
        }}
        discovery={discoveryWith(note("complete", full, false))}
      />
    </Api>
  ),
};
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
              basis: "gross",
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
