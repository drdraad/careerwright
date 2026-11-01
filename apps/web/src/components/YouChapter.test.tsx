// The You chapter against a scripted API at the network edge: the entry choice leads, a
// streamed reply is provisional until checked, the review tray saves only chosen and confirmed
// changes, a message with a risk stem is sent with the support panel beside it, and one action
// is the primary.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type {
  DiscoveryOut,
  OriginOut,
  PreferencesOut,
  ProfileDocument,
  ProfileOut,
  SketchOut,
  SlateOut,
  SuggestionOut,
  SupportNoteOut,
  TitleMatchesOut,
  TurnOut,
  WorkspaceOut,
} from "@/generated/api";
import { useProfile } from "@/lib/queries";
import { FIRST_QUESTION } from "@/lib/vocabulary";
import { fakeApi, type Route, type Sent } from "@/test/fakeApi";
import { EvidenceProvider } from "./EvidenceDrawer";
import { YouChapter } from "./YouChapter";

const WS = "w-you";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const answers: ProfileDocument = {
  schema_version: "4",
  work_status: unasked,
  qualifications: unasked,
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
};
const profile: ProfileOut = {
  workspace_id: WS,
  version: 1,
  document: answers,
  created_by: null,
  created_at: "2027-01-01T00:00:00Z",
};
const workspace: WorkspaceOut = {
  workspace_id: WS,
  name: "Demo (synthetic)",
  data_mode: "demo",
  synthetic: true,
  fixture: false,
  version: 1,
  last_event_seq: 0,
  created_at: "2027-01-01T00:00:00Z",
  updated_at: "2027-01-01T00:00:00Z",
};
const prefs = (entry: PreferencesOut["entry_mode"]): PreferencesOut => ({
  version: entry === null ? 0 : 1,
  entry_mode: entry,
  conversation_mode: null,
  paused: false,
  updated_at: null,
});
const sketch: SketchOut = {
  profile_version: 1,
  inputs: {},
  not_asked: [],
  targets: [],
  steps: [],
};

function turn(status: TurnOut["run"]["status"], proposal: TurnOut["proposal"] = null): TurnOut {
  return {
    turn_id: "t1",
    message_id: "m1",
    message: "Synthetic: I'm a shift supervisor and could work in Leeds.",
    profile_version: 1,
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
      profile_version: 1,
    },
    proposal,
    decision: null,
  };
}

const proposal: TurnOut["proposal"] = {
  origin: "fixture",
  prompt_version: "interview-turn-2",
  profile_version: 1,
  reply: "Thanks. I noted two things for you to review.",
  changes: [
    {
      change_id: "c1",
      field: "current_role",
      state: "provided",
      value: "shift supervisor",
      basis: "stated",
      message_ids: ["m1"],
      reason: "You said what you do.",
      hard_constraint: false,
    },
    {
      change_id: "c2",
      field: "cities",
      state: "provided",
      value: ["Leeds"],
      basis: "inferred",
      message_ids: ["m1"],
      reason: "You named this city.",
      hard_constraint: true,
    },
  ],
  next_question: "How many hours a week could you give to learning?",
  asks_about: null,
  missing_critical_fields: ["weekly_study_hours"],
  ready_for_review: true,
};

function routes(
  state: { preferences: PreferencesOut; turns: TurnOut[] },
  extra: Route[] = [],
): Route[] {
  return [
    ...extra,
    { method: "GET", path: /\/interview\/preferences$/, answer: () => state.preferences },
    {
      method: "GET",
      path: /\/interview\/turns$/,
      answer: () => ({ items: [...state.turns].reverse(), next_cursor: null }),
    },
    { method: "GET", path: /\/discoveries$/, answer: { items: [], next_cursor: null } },
    { method: "GET", path: /\/sketch$/, answer: sketch },
  ];
}

function renderYou(shown: ProfileOut = profile, where: WorkspaceOut = workspace) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <YouChapter workspace={where} profile={shown} />
      </EvidenceProvider>
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

/** The first question comes first (Task 6d slice B): "Skip for now" goes on to how to start,
 *  saving nothing, as a person who'd rather not say would. */
async function skipFirstQuestion(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole("button", { name: "Skip for now" }));
}

/** The chapter reading its profile from the (scripted) API, as the workspace shell does. */
function LiveProfile() {
  const current = useProfile(WS);
  return current.data === undefined ? null : (
    <YouChapter workspace={workspace} profile={current.data} />
  );
}

function renderLive() {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <LiveProfile />
      </EvidenceProvider>
    </QueryClientProvider>,
  );
  return { user: userEvent.setup(), queries };
}

const unknownHours: TurnOut["proposal"] = {
  ...(proposal as NonNullable<TurnOut["proposal"]>),
  changes: [
    {
      change_id: "c3",
      field: "weekly_study_hours",
      state: "unknown",
      value: null,
      basis: "stated",
      message_ids: ["m1"],
      reason: "You said you don't know yet.",
      hard_constraint: true,
    },
  ],
};

/** The API's support panel (`careerwright.profile.safety.SUPPORT_NOTE`, one of its resources). */
const panel: SupportNoteOut = {
  policy_version: "support-policy-7",
  review_status:
    "accepted for L0 at session 1 (human gate H-12); the three phrasings added on 2026-10-28 " +
    "are not yet reviewed as built",
  message:
    "If anything you mentioned is about how you are feeling, support is available any time, " +
    "from people trained to help. Your message was sent to Careerwright as usual.",
  resources: [
    {
      name: "Samaritans",
      contact: "Call 116 123",
      when: "To talk",
      source_url: "https://www.samaritans.org/",
      checked_on: "2026-10-28",
    },
  ],
};

/** The API's panel beside the first question's title field (`SUPPORT_NOTE_TITLE`). */
const titlePanel: SupportNoteOut = {
  ...panel,
  policy_version: "support-policy-9",
  message:
    "If anything you typed is about how you are feeling, support is available any time, " +
    "from people trained to help. Careerwright keeps it as your job title only if you choose " +
    "to. You can also type again or skip this question.",
};

type Live = { preferences: PreferencesOut; turns: TurnOut[]; profile: ProfileOut };

/** The filled primary actions in the view shown (the other views stay mounted, hidden). */
function visiblePrimaries(): number {
  return [...document.querySelectorAll(".btn-primary")].filter(
    (b) => b.closest("[hidden]") === null,
  ).length;
}

/** A finished discovery whose note is written, so the slate asks for nothing. */
const discovered = {
  discovery_id: "d1",
  profile_version: 1,
  current: true,
  run: { status: "complete" },
  proposal: null,
  explanation: {
    explanation_id: "e1",
    discovery_id: "d1",
    run: { status: "complete", failure_class: null },
    can_retry: false,
    written: null,
  },
} as unknown as DiscoveryOut;

const suggestionNamed = (id: string, title: string): SuggestionOut => ({
  concept_id: id,
  concept_kind: "esco",
  title,
  esco_code: "7231.1",
  isco_group: { code: "7231", label: "Motor vehicle mechanics and repairers" },
  family: { code: "723", label: "Machinery mechanics and repairers" },
  sector: { code: "7", label: "Craft and related trades workers" },
  direction: "less_familiar",
  channels: ["tasks"],
  linked_evidence: [{ field: "enjoyed_tasks", text: "repairing bicycles" }],
  matched_queries: ["q1"],
  sources: [{ kind: "esco", uri: `http://data.europa.eu/esco/occupation/${id}`, release: "esco" }],
  workday: `${title} work.`,
  reasons: [
    {
      reason: "searched_through_skill",
      outcome: "found_work",
      field: "enjoyed_tasks",
      answer: "repairing bicycles",
      search: "repairing bicycles",
      skill: "repair bicycles",
    },
  ],
  essential_skill_count: 0,
  essential_skills: [],
  regulated: null,
  different_kind_of_work: false,
  shared_skills: [],
});

/** The slate for `discovered`, less whatever the view excludes (`exclude_concept`). */
function slateFor(query: string): SlateOut {
  const all = [suggestionNamed("o1", "bicycle mechanic"), suggestionNamed("o2", "cycle courier")];
  return {
    discovery_id: "d1",
    profile_version: 1,
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
    suggestions: all.filter((s) => !query.includes(`exclude_concept=${s.concept_id}`)),
    fewer_reasons: [],
    notes: [],
    salary_floor: null,
    ai_resilience_filter: {
      minimum: null,
      include_unscored: true,
      scored: 0,
      below_minimum: 0,
      unscored: 2,
      unscored_excluded: 0,
      synthetic: false,
      pack_version: "l0-2026-10-29",
      pack_dated: "2026-10-29",
    },
    pool_size: 2,
    pool_target: [60, 120],
    beyond_pool_limit: 0,
    excluded: { occupations: 0, families: 0 },
    queries: [],
    unsearchable_queries: [],
    title_ideas: [],
    not_included: [],
    unmatched_titles: [],
    ambiguous_titles: [],
    familiarity_known: false, // no role or target given
  } as SlateOut;
}

function liveRoutes(state: Live, extra: Route[] = []): Route[] {
  return [
    ...extra,
    { method: "GET", path: /\/profile$/, answer: () => state.profile },
    ...routes(state),
  ];
}

describe("[PROF-08][REC1-10] the chapter leads with how to start", () => {
  it("asks first whether the person knows their direction, and saves the choice", async () => {
    const state = { preferences: prefs(null), turns: [] as TurnOut[] };
    const sent = fakeApi(
      routes(state, [
        {
          method: "PUT",
          path: /\/interview\/preferences$/,
          answer: (request) => {
            state.preferences = { ...prefs("sure") };
            return { ...state.preferences, ...(request.body as object) };
          },
        },
      ]),
    );
    const user = renderYou();
    await skipFirstQuestion(user);

    await user.click(await screen.findByRole("button", { name: "I know my direction" }));

    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    expect(sent.find((s) => s.method === "PUT")?.body).toEqual({
      expected_version: 0,
      entry_mode: "sure",
      conversation_mode: null,
      paused: false,
    });
    // A sure person is asked for the target and its level; suggestions stay optional, in their
    // own view.
    expect(
      await screen.findByRole("heading", {
        name: "Which role are you aiming for, and at what level?",
      }),
    ).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Suggestions" }));
    expect(screen.getByRole("button", { name: "Help me explore instead" })).toBeVisible();
  });

  it("says in one line what Careerwright is for, before the entry choice, at the start only", async () => {
    // Session 2, the start page: "It's for inputing information about yourself and your job
    // preferences, not sure".
    fakeApi(routes({ preferences: prefs(null), turns: [] }));
    const user = renderYou();
    const words =
      "Careerwright helps you find work that could suit you, see what it would take, and plan a route you can afford.";
    // Task 6d slice B: the first question now comes first, and the line leads it too.
    const leading = await screen.findByText(words);
    const first = screen.getByRole("heading", { name: FIRST_QUESTION });
    expect(leading.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    await skipFirstQuestion(user);
    const purpose = await screen.findByText(words);
    const choice = screen.getByRole("heading", { name: "How would you like to start?" });
    expect(purpose).toBeVisible();
    expect(purpose.compareDocumentPosition(choice) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    cleanup();
    fakeApi(routes({ preferences: prefs("unsure"), turns: [] }));
    renderYou();
    await screen.findByRole("group", { name: "Example replies" });
    expect(screen.queryByText(/Careerwright helps you find work/)).toBeNull();
  });

  it("[PROF-08] has the reply field from the first screen, and no tone setting in the chapter", async () => {
    // Session 2: "Chat should be immediate"; "ditch the tone selection - this should be in
    // preferences" (it is in the account menu, `ConversationTone`).
    const state = { preferences: prefs(null), turns: [] as TurnOut[] };
    const sent = fakeApi(
      routes(state, [
        {
          method: "POST",
          path: /\/interview\/turns$/,
          status: 202,
          answer: { ...turn("queued"), support_note: null },
        },
      ]),
    );
    const user = renderYou();
    await skipFirstQuestion(user);

    expect(
      await screen.findByRole("heading", { name: "How would you like to start?" }),
    ).toBeVisible();
    expect(screen.queryByLabelText("How Careerwright talks with you")).toBeNull();
    await user.type(screen.getByLabelText("Reply to Careerwright"), "I fix bikes.");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    expect(sent.find((s) => s.method === "POST")?.body).toEqual({
      expected_profile_version: 1,
      message: "I fix bikes.",
    });
  });
});

describe("[UI-06][UI-04] one idea per view: the conversation, what we know and the suggestions", () => {
  it("opens on the conversation, moves between views as tabs, and shows one view at a time", async () => {
    fakeApi(routes({ preferences: prefs("unsure"), turns: [] }));
    const user = renderYou();

    const conversation = await screen.findByRole("tab", { name: "Conversation" });
    expect(conversation).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel", { name: "Conversation" })).toContainElement(
      screen.getByLabelText("Reply to Careerwright"),
    );
    expect(screen.queryByRole("heading", { name: "What we know" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Directions to explore" })).toBeNull();
    // Every tab points at its own view, which stays in the page, hidden while not shown.
    for (const name of ["Conversation", "What we know", "Suggestions"]) {
      const tab = screen.getByRole("tab", { name });
      expect(document.getElementById(tab.getAttribute("aria-controls") ?? "")).toHaveAttribute(
        "aria-labelledby",
        tab.id,
      );
    }

    // Arrow keys move between the tabs (and the view follows); Home and End reach the ends.
    conversation.focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "What we know" })).toHaveFocus();
    expect(screen.getByRole("heading", { name: "What we know" })).toBeVisible();
    expect(screen.getByLabelText("Reply to Careerwright")).not.toBeVisible();
    await user.keyboard("{End}");
    expect(screen.getByRole("tab", { name: "Suggestions" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(await screen.findByRole("heading", { name: "Directions to explore" })).toBeVisible();
    await user.keyboard("{Home}");
    expect(conversation).toHaveFocus();
    expect(screen.getByLabelText("Reply to Careerwright")).toBeVisible();
  });

  it("[UI-12] puts What we know's action under its heading, before the answers, and opens the form right under it (D-I3)", async () => {
    fakeApi(routes({ preferences: prefs("unsure"), turns: [] }));
    const user = renderYou();
    await user.click(await screen.findByRole("tab", { name: "What we know" }));
    const follows = (first: Node, then: Node) =>
      (first.compareDocumentPosition(then) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;

    const edit = screen.getByRole("button", { name: "Edit answers directly" });
    const shown = screen.getByRole("region", { name: "Your answers" });
    expect(follows(screen.getByRole("heading", { name: "What we know" }), edit)).toBe(true);
    expect(follows(edit, shown)).toBe(true);
    await user.click(edit);
    const form = await screen.findByRole("form", { name: "Edit your answers" });
    expect(follows(edit, form) && follows(form, shown)).toBe(true);
  });

  it("explains the two limits in plain words where they are shown", async () => {
    // Session 2: "total spending limit and monthly payment limit - what do these mean??"
    const limited: ProfileOut = {
      ...profile,
      document: {
        ...answers,
        direct_spend_cap: {
          state: "provided",
          value: { minor_units: 150_000, currency: "GBP" },
          source_ref_id: "s1",
        },
        monthly_payment_cap: {
          state: "provided",
          value: { minor_units: 25_000, currency: "GBP" },
          source_ref_id: "s1",
        },
      },
    };
    // A reply proposing a new monthly limit: the tray says what it means too (app review M4).
    const monthly: TurnOut["proposal"] = {
      ...(proposal as NonNullable<TurnOut["proposal"]>),
      changes: [
        {
          change_id: "c4",
          field: "monthly_payment_cap",
          state: "provided",
          value: { minor_units: 20_000, currency: "GBP" },
          basis: "stated",
          message_ids: ["m1"],
          reason: "You named a monthly amount.",
          hard_constraint: true,
        },
      ],
    };
    fakeApi(routes({ preferences: prefs("unsure"), turns: [turn("complete", monthly)] }));
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queries}>
        <EvidenceProvider>
          <YouChapter workspace={workspace} profile={limited} initialView="known" />
        </EvidenceProvider>
      </QueryClientProvider>,
    );

    const answersShown = await screen.findByRole("region", { name: "Your answers" });
    expect(within(answersShown).getByText("Total spending limit")).toBeVisible();
    expect(
      within(answersShown).getByText(/The most you'd spend on your next step, all added up/),
    ).toBeVisible();
    expect(
      within(answersShown).getByText(/The most you could pay out in any one month/),
    ).toBeVisible();

    await userEvent.setup().click(screen.getByRole("tab", { name: "Conversation" }));
    const tray = await screen.findByRole("region", { name: /To review: 1 change/ });
    expect(within(tray).getByText("Monthly payment limit: £200")).toBeVisible();
    expect(within(tray).getByText(/The most you could pay out in any one month/)).toBeVisible();
  });
});

describe("[UI-06] moving between the views keeps what the person typed or chose", () => {
  it("keeps a typed reply, the tray's choices, the answer form's edits and the slate's picks", async () => {
    // App review I1: each view unmounted when another opened, and took these with it.
    const sent = fakeApi(
      routes({ preferences: prefs("unsure"), turns: [turn("complete", proposal)] }, [
        {
          method: "GET",
          path: /\/discoveries$/,
          answer: { items: [discovered], next_cursor: null },
        },
        { method: "GET", path: /\/slate$/, answer: (request) => slateFor(request.query) },
      ]),
    );
    const user = renderYou();

    await user.type(await screen.findByLabelText("Reply to Careerwright"), "Half a thought");
    const tray = screen.getByRole("region", { name: /To review: 2 changes/ });
    await user.click(within(tray).getByRole("button", { name: "Accept current role" }));

    await user.click(screen.getByRole("tab", { name: "What we know" }));
    await user.click(screen.getByRole("button", { name: "Edit answers directly" }));
    await user.selectOptions(
      await screen.findByLabelText("How you answer weekly study hours"),
      "unknown",
    );
    expect(screen.getByText("Unsaved changes")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Suggestions" }));
    await user.click(await screen.findByRole("button", { name: "Not for me : Bicycle mechanic" }));
    await waitFor(() =>
      expect(screen.queryByRole("article", { name: "Bicycle mechanic" })).toBeNull(),
    );

    await user.click(screen.getByRole("tab", { name: "Conversation" }));
    expect(screen.getByLabelText("Reply to Careerwright")).toHaveValue("Half a thought");
    expect(screen.getByRole("button", { name: "Accept current role" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: /Save 1 to What we know/ })).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "What we know" }));
    expect(screen.getByLabelText("How you answer weekly study hours")).toHaveValue("unknown");
    expect(screen.getByText("Unsaved changes")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Suggestions" }));
    expect(screen.queryByRole("article", { name: "Bicycle mechanic" })).toBeNull();
    expect(screen.getByRole("article", { name: "Cycle courier" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Clear exclusions" })).toBeVisible();
    expect(sent.filter((s) => s.method !== "GET")).toHaveLength(0); // moving saved nothing
  });

  it("moves focus to the answer form when the person adds the details themselves", async () => {
    // App review I2: the button's view closed and focus fell to the page.
    fakeApi(routes({ preferences: prefs("unsure"), turns: [turn("failed")] }));
    const user = renderYou();

    await user.click(await screen.findByRole("button", { name: "Add the details yourself" }));

    expect(screen.getByRole("tab", { name: "What we know" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Edit your answers" })).toHaveFocus(),
    );
  });
});

describe("[UI-04][UI-06] one decision at a time, and Resume while paused", () => {
  it("asks the next question only once the tray is decided, under what the decision did", async () => {
    const state: Live = {
      preferences: prefs("unsure"),
      turns: [turn("complete", proposal)],
      profile,
    };
    fakeApi(
      liveRoutes(state, [
        {
          method: "POST",
          path: /\/turns\/t1\/decision$/,
          status: 201,
          answer: () => {
            state.profile = { ...state.profile, version: 2 };
            state.turns = [{ ...turn("complete", proposal), decision: {} as TurnOut["decision"] }];
            return { turn_id: "t1", decision: {}, profile: state.profile };
          },
        },
      ]),
    );
    const { user } = renderLive();
    const tray = await screen.findByRole("region", { name: /To review: 2 changes/ });
    const next = { name: "How many hours a week could you give to learning?" };
    expect(screen.queryByRole("heading", next)).toBeNull();

    await user.click(within(tray).getByRole("button", { name: "Accept current role" }));
    await user.click(within(tray).getByRole("button", { name: /Save 1 to What we know/ }));

    const saved = await screen.findByRole("heading", { name: "Saved to What we know" });
    const question = await screen.findByRole("heading", next);
    expect(saved.compareDocumentPosition(question) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("makes Resume the one primary action while paused, and keeps focus with the change", async () => {
    // App review M7: while paused, the bright action was a Send that couldn't send.
    const state = { preferences: prefs("unsure"), turns: [] as TurnOut[] };
    const sent = fakeApi(
      routes(state, [
        {
          method: "PUT",
          path: /\/interview\/preferences$/,
          answer: (request) => {
            const body = request.body as { paused: boolean };
            state.preferences = {
              ...state.preferences,
              version: state.preferences.version + 1,
              paused: body.paused,
            };
            return state.preferences;
          },
        },
      ]),
    );
    const user = renderYou();

    await user.click(await screen.findByRole("button", { name: "Pause the interview" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Paused" })).toHaveFocus());
    const resume = screen.getByRole("button", { name: "Resume the interview" });
    expect(resume).toHaveClass("btn-primary");
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-secondary");
    expect(visiblePrimaries()).toBe(1);

    await user.click(resume);
    const question = await screen.findByRole("heading", {
      name: "What would you like your working life to be like?",
    });
    await waitFor(() => expect(question).toHaveFocus());
    // Back to answering: Send is bright once there is something to send (F17).
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-secondary");
    await user.type(screen.getByRole("textbox", { name: "Reply to Careerwright" }), "Hello");
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-primary");
    expect(sent.filter((s) => s.method === "PUT").map((s) => s.body)).toEqual([
      { expected_version: 1, entry_mode: "unsure", conversation_mode: null, paused: true },
      { expected_version: 2, entry_mode: "unsure", conversation_mode: null, paused: false },
    ]);
  });
});

describe("[MODEL-03] the reply streams as provisional and the checked reply replaces it", () => {
  it("shows the reply so far, marked not checked, while the turn runs", async () => {
    fakeApi(
      routes({ preferences: prefs("unsure"), turns: [turn("running")] }, [
        {
          method: "GET",
          path: /\/turns\/t1\/reply$/,
          answer: {
            turn_id: "t1",
            completeness: "streaming",
            seq: 2,
            text: "Thanks, I noted",
            updated_at: null,
          },
        },
      ]),
    );
    renderYou();

    expect(await screen.findByText("Writing a reply, not checked yet")).toBeVisible();
    expect(screen.getByText("Thanks, I noted")).toBeVisible();
    expect(screen.getByText("Careerwright is still replying.")).toBeVisible(); // Send says why it waits
  });

  it("shows only the checked reply once the turn is complete", async () => {
    // Its proposals already decided, so the next question is the one thing asked (D-I4).
    const decided = { ...turn("complete", proposal), decision: {} as TurnOut["decision"] };
    fakeApi(routes({ preferences: prefs("unsure"), turns: [decided] }));
    renderYou();

    expect(await screen.findByText("Thanks. I noted two things for you to review.")).toBeVisible();
    expect(screen.queryByText(/not checked yet/)).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "How many hours a week could you give to learning?" }),
    ).toBeVisible(); // one question at a time
    // Said once, at the start: not under every question (session 2: "too much helper text").
    expect(screen.queryByText(/or say Skip, Unknown or Prefer not to say/)).toBeNull();
  });
});

describe("[STATE-06][PROF-04] the review tray saves only what the person chose and confirmed", () => {
  it("applies a limit only once confirmed by name, and styles a reading apart from a fact", async () => {
    const sent = fakeApi(
      routes({ preferences: prefs("unsure"), turns: [turn("complete", proposal)] }, [
        {
          method: "POST",
          path: /\/turns\/t1\/decision$/,
          status: 201,
          answer: { turn_id: "t1", decision: {}, profile: { ...profile, version: 2 } },
        },
      ]),
    );
    const user = renderYou();
    const tray = await screen.findByRole("region", { name: /To review: 2 changes/ });

    const reading = within(tray).getByText("Work areas: Leeds").closest(".proposal");
    expect(reading).toHaveAttribute("data-basis", "inferred");
    expect(within(tray).getByText(/not a fact until you accept it/)).toBeVisible();
    // Procedural helper lines are gone (session 2: "too much helper text"); the limit's
    // Confirm names it, and Save says why while it can't save.
    expect(within(tray).queryByText(/needs your confirmation/)).toBeNull();
    expect(within(tray).queryByText(/Skipped changes are not saved/)).toBeNull();
    expect(within(tray).getByText("Accept, confirm or edit at least one first.")).toBeVisible();
    // One decision at a time: the next question waits until the tray is decided (D-I4).
    expect(screen.queryByRole("heading", { name: /How many hours a week/ })).toBeNull();
    await user.click(within(tray).getByRole("button", { name: "Accept current role" }));
    await user.click(within(tray).getByRole("button", { name: "Confirm work areas as a limit" }));
    const save = within(tray).getByRole("button", { name: /Save 2 to What we know/ });
    expect(save).toHaveClass("btn-primary"); // the one primary action while reviewing
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-secondary");
    await user.click(save);

    await waitFor(() => expect(sent.some((s) => s.path.endsWith("/decision"))).toBe(true));
    expect(sent.find((s) => s.path.endsWith("/decision"))?.body).toEqual({
      expected_version: 1,
      accept: ["c1", "c2"],
      confirm_hard_constraints: ["cities"],
      edits: [],
    });
  });
});

describe("[STATE-06] an edit in the tray is checked first and saved with the decision", () => {
  const decided = (state: Live, support_note: SupportNoteOut | null = null): Route => ({
    method: "POST",
    path: /\/turns\/t1\/decision$/,
    status: 201,
    answer: () => {
      state.profile = { ...state.profile, version: 2 };
      state.turns = [
        {
          ...turn("complete", state.turns[0]?.proposal ?? null),
          decision: {} as TurnOut["decision"],
        },
      ];
      return { turn_id: "t1", decision: {}, profile: state.profile, support_note };
    },
  });

  it("shows an invalid edit's problem and sends nothing", async () => {
    const state: Live = {
      preferences: prefs("unsure"),
      turns: [turn("complete", proposal)],
      profile,
    };
    const sent = fakeApi(liveRoutes(state, [decided(state)]));
    const { user } = renderLive();
    const tray = await screen.findByRole("region", { name: /To review: 2 changes/ });

    await user.click(within(tray).getByRole("button", { name: "Edit current role" }));
    await user.clear(within(tray).getByLabelText("Current role"));
    await user.click(within(tray).getByRole("button", { name: /Save 1 to What we know/ }));

    expect(await within(tray).findByText(/Enter an answer/)).toBeVisible();
    expect(sent.some((s) => s.path.endsWith("/decision"))).toBe(false);
  });

  it("keeps what was typed when an Unknown proposal is edited, and saves it in one request", async () => {
    const state: Live = {
      preferences: prefs("unsure"),
      turns: [turn("complete", unknownHours)],
      profile,
    };
    const sent = fakeApi(liveRoutes(state, [decided(state)]));
    const { user } = renderLive();
    const tray = await screen.findByRole("region", { name: /To review: 1 change/ });

    await user.click(within(tray).getByRole("button", { name: "Edit weekly study hours" }));
    await user.type(within(tray).getByLabelText(/Weekly study hours, hours a week/), "6");
    await user.click(within(tray).getByRole("button", { name: /Save 1 to What we know/ }));

    await waitFor(() => expect(sent.some((s) => s.path.endsWith("/decision"))).toBe(true));
    expect(sent.filter((s) => s.method !== "GET")).toHaveLength(1); // decision and edit together
    expect(sent.find((s) => s.path.endsWith("/decision"))?.body).toEqual({
      expected_version: 1,
      accept: [],
      confirm_hard_constraints: [],
      edits: [{ field: "weekly_study_hours", answer: { state: "provided", value: 6 } }],
    });
  });

  it("[PROF-09] shows the calm support panel beside the save when an answer typed in the review step triggers the screen", async () => {
    // The product owner's "every place a person types" (31 October 2026). The words are the
    // web tests' existing fixture; the panel is the API's.
    const state: Live = {
      preferences: prefs("unsure"),
      turns: [turn("complete", proposal)],
      profile,
    };
    const entryPanel: SupportNoteOut = {
      ...panel,
      policy_version: "support-policy-9",
      message:
        "If anything you typed is about how you are feeling, support is available any time, " +
        "from people trained to help. Your answers were saved as usual.",
    };
    const sent = fakeApi(liveRoutes(state, [decided(state, entryPanel)]));
    const { user } = renderLive();
    const tray = await screen.findByRole("region", { name: /To review: 2 changes/ });

    await user.click(within(tray).getByRole("button", { name: "Edit current role" }));
    await user.clear(within(tray).getByLabelText("Current role"));
    await user.type(
      within(tray).getByLabelText("Current role"),
      "I volunteer on a suicide prevention helpline.",
    );
    await user.click(within(tray).getByRole("button", { name: /Save 1 to What we know/ }));

    const shown = await screen.findByRole("region", { name: "Support is available" });
    expect(shown).toHaveTextContent("Your answers were saved as usual.");
    expect(await screen.findByRole("heading", { name: "Saved to What we know" })).toBeVisible();
    expect(sent.filter((s) => s.path.endsWith("/decision"))).toHaveLength(1);
    // Kept until the person dismisses it; focus goes to what the save did.
    await user.click(within(shown).getByRole("button", { name: /Dismiss/ }));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
    expect(screen.getByRole("heading", { name: "Saved to What we know" })).toHaveFocus();
  });

  it("keeps the edit and says why when saving fails", async () => {
    const state: Live = {
      preferences: prefs("unsure"),
      turns: [turn("complete", proposal)],
      profile,
    };
    fakeApi(
      liveRoutes(state, [
        {
          method: "POST",
          path: /\/turns\/t1\/decision$/,
          status: 503,
          answer: {
            error: {
              code: "STORE_UNAVAILABLE",
              message: "The database is unavailable.",
              retryable: true,
              stage: "storage",
              correlation_id: "c1",
              details: {},
            },
          },
        },
      ]),
    );
    const { user } = renderLive();
    const tray = await screen.findByRole("region", { name: /To review: 2 changes/ });

    await user.click(within(tray).getByRole("button", { name: "Edit current role" }));
    const field = within(tray).getByLabelText("Current role");
    await user.clear(field);
    await user.type(field, "Night manager");
    await user.click(within(tray).getByRole("button", { name: /Save 1 to What we know/ }));

    expect(await within(tray).findByRole("alert")).toBeVisible();
    expect(within(tray).getByLabelText("Current role")).toHaveValue("Night manager");
  });
});

describe("[STATE-06][PROF-01] undo restores the earlier answers with their sources", () => {
  it("reverts to the version before the save, then says so and returns focus", async () => {
    const state: Live = {
      preferences: prefs("unsure"),
      turns: [turn("complete", proposal)],
      profile,
    };
    const sent = fakeApi(
      liveRoutes(state, [
        {
          method: "POST",
          path: /\/turns\/t1\/decision$/,
          status: 201,
          answer: () => {
            state.profile = { ...state.profile, version: 2 };
            state.turns = [{ ...turn("complete", proposal), decision: {} as TurnOut["decision"] }];
            return { turn_id: "t1", decision: {}, profile: state.profile };
          },
        },
        {
          method: "POST",
          path: /\/profile\/revert$/,
          status: 201,
          answer: () => {
            state.profile = { ...state.profile, version: 3 };
            return state.profile;
          },
        },
      ]),
    );
    const { user } = renderLive();
    const tray = await screen.findByRole("region", { name: /To review: 2 changes/ });
    const accept = within(tray).getByRole("button", { name: "Accept current role" });
    // Session 2, C3: accept and undo are colour coded as well as worded; accept fills once chosen.
    expect(accept).toHaveClass("btn-accept");
    expect(accept).toHaveAttribute("aria-pressed", "false");
    await user.click(accept);
    expect(accept).toHaveAttribute("aria-pressed", "true");
    await user.click(within(tray).getByRole("button", { name: /Save 1 to What we know/ }));

    // B-I4: the save is announced and focus lands on the notice that says what it did, right
    // where the decision was made, not on nothing.
    const saved = await screen.findByRole("heading", { name: "Saved to What we know" });
    await waitFor(() => expect(saved).toHaveFocus());
    expect(screen.getByTestId("you-announcer")).toHaveTextContent("Saved to What we know.");
    const undo = await screen.findByRole("button", { name: "Undo the last save" });
    expect(undo).toHaveClass("btn-undo");
    await user.click(undo);

    await waitFor(() => expect(sent.some((s) => s.path.endsWith("/profile/revert"))).toBe(true));
    expect(sent.find((s) => s.path.endsWith("/profile/revert"))?.body).toEqual({
      expected_version: 2,
      to_version: 1,
    });
    expect(sent.some((s) => s.method === "PUT" && s.path.endsWith("/profile"))).toBe(false);
    await waitFor(() =>
      expect(screen.getByTestId("you-announcer")).toHaveTextContent(
        "Save undone: your answers are back as they were before it.",
      ),
    );
    await waitFor(() => expect(screen.getByRole("heading", { name: "Save undone" })).toHaveFocus());
    expect(screen.queryByRole("button", { name: "Undo the last save" })).toBeNull();
  });
});

describe("[DIV1-13][DIV1-14] the start: the first question, which is closest, then how to start", () => {
  const named = (title: string, version: number): ProfileOut => ({
    ...profile,
    version,
    document: {
      ...answers,
      current_role: { state: "provided", value: title, source_ref_id: "s-role" },
    },
  });
  const origin = (
    title: string,
    kind: "ons" | "own_words",
    decision: "not_yet" | "none_of_these" | null,
  ): OriginOut =>
    ({
      profile_version: 2,
      capability_version: 0,
      role: {
        text: title,
        state: "not_in_esco",
        chosen: false,
        occupation: null,
        choices: [],
        kind,
        uk_groups: kind === "ons" ? [{ code: "2221", label: "Nursing professionals" }] : [],
        closest:
          decision === null
            ? null
            : {
                decision,
                chosen: null,
                groups: [
                  {
                    group: { code: "2221", label: "Nursing professionals" },
                    occupations: [{ concept_id: "c2", title: "specialist nurse", esco_uri: "u2" }],
                  },
                ],
              },
      },
      usual_skills: [],
      destinations: [],
      fewer_reasons: [],
      salary_floor: null,
    }) as unknown as OriginOut;
  const titles = (q: string, matches: TitleMatchesOut["matches"], partial = false) =>
    ({
      query: q,
      matches,
      total: 0,
      uk_total: matches.length,
      limit: 8,
      partial,
    }) as unknown as TitleMatchesOut;

  it("asks which ESCO occupation is closest after a UK title, and None of these goes on with what isn't known", async () => {
    let decision: "not_yet" | "none_of_these" = "not_yet";
    const state: Live = { preferences: prefs(null), turns: [], profile };
    const sent = fakeApi(
      liveRoutes(state, [
        {
          method: "GET",
          path: /\/taxonomy\/titles$/,
          answer: titles("Registered nurse", [
            { source: "uk_title_index", title: "Registered nurse", soc_codes: [], isco_groups: [] },
          ]),
        },
        {
          method: "POST",
          path: /\/origin\/role\/title$/,
          status: 201,
          answer: () => {
            state.profile = named("Registered nurse", 2);
            return state.profile;
          },
        },
        {
          method: "GET",
          path: /\/origin$/,
          answer: () => origin("Registered nurse", "ons", decision),
        },
        {
          method: "POST",
          path: /\/origin\/role\/closest$/,
          status: 201,
          answer: () => {
            decision = "none_of_these";
            return state.profile;
          },
        },
      ]),
    );
    const { user } = renderLive();

    await user.type(
      await screen.findByRole("combobox", { name: "Your job title" }),
      "Registered nurse",
    );
    await user.click(await screen.findByRole("option", { name: /UK job title \(ONS\)/ }));
    const asked = await screen.findByRole("heading", { name: "Which of these is closest?" });
    await waitFor(() => expect(asked).toHaveFocus());
    expect(screen.getByRole("button", { name: "specialist nurse" })).toBeVisible();

    await user.click(screen.getByRole("button", { name: "None of these is my job" }));
    const start = await screen.findByRole("heading", { name: "How would you like to start?" });
    await waitFor(() => expect(start).toHaveFocus());
    expect(
      screen.getByText(
        "Careerwright found “Registered nurse” in the UK job-title index and keeps it as your role, in your words. What this work asks for isn't known yet.",
      ),
    ).toBeVisible();
    expect(sent.find((s) => s.path.endsWith("/origin/role/closest"))?.body).toEqual({
      expected_version: 2,
      concept_id: null,
    });
  });

  it("[STATE-11] goes on to how to start after “I haven't had a job yet”, which the role shows as an answer, never asked again", async () => {
    const state: Live = { preferences: prefs(null), turns: [], profile };
    const sent = fakeApi(
      liveRoutes(state, [
        {
          method: "POST",
          path: /\/origin\/role\/no-job-yet$/,
          status: 201,
          answer: () => {
            state.profile = {
              ...profile,
              version: profile.version + 1,
              document: {
                ...profile.document,
                current_role: { state: "no_job_yet", value: null, source_ref_id: "s-none" },
              },
            };
            return state.profile;
          },
        },
      ]),
    );
    const { user } = renderLive();

    await user.click(await screen.findByRole("button", { name: "I haven't had a job yet" }));
    const start = await screen.findByRole("heading", { name: "How would you like to start?" });
    await waitFor(() => expect(start).toHaveFocus());
    // Never the job question again, and no role line that talks about work.
    expect(screen.queryByRole("combobox", { name: "Your job title" })).toBeNull();
    expect(document.body.textContent).not.toMatch(/what this work asks for/i);
    expect(sent.filter((s) => s.method === "POST").map((s) => s.path)).toEqual([
      `/v1/workspaces/${WS}/origin/role/no-job-yet`,
    ]);
    // No origin is asked for: there is no role to join from.
    expect(sent.some((s) => s.path.endsWith("/origin"))).toBe(false);
  });

  it("goes back from which is closest to the title field, to fix a wrongly picked title", async () => {
    // Design review M-4, its first part: there was no way back from the closest question.
    const state: Live = { preferences: prefs(null), turns: [], profile };
    const sent = fakeApi(
      liveRoutes(state, [
        {
          method: "GET",
          path: /\/taxonomy\/titles$/,
          answer: (s: Sent) => {
            const q = new URLSearchParams(s.query).get("q") ?? "";
            const title = q.startsWith("D") ? "Doula" : "Registered nurse";
            return titles(q, [{ source: "uk_title_index", title, soc_codes: [], isco_groups: [] }]);
          },
        },
        {
          method: "POST",
          path: /\/origin\/role\/title$/,
          status: 201,
          answer: (s: Sent) => {
            const body = s.body as { title: string };
            state.profile = named(body.title, state.profile.version + 1);
            return state.profile;
          },
        },
        {
          method: "GET",
          path: /\/origin$/,
          answer: () => origin(String(state.profile.document.current_role.value), "ons", "not_yet"),
        },
      ]),
    );
    const { user } = renderLive();

    await user.type(
      await screen.findByRole("combobox", { name: "Your job title" }),
      "Registered nurse",
    );
    await user.click(await screen.findByRole("option", { name: /UK job title \(ONS\)/ }));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Which of these is closest?" })).toHaveFocus(),
    );
    await user.click(screen.getByRole("button", { name: "Change my job title" }));

    const again = await screen.findByRole("heading", {
      name: "What do you do now, or what did you do last?",
    });
    await waitFor(() => expect(again).toHaveFocus());
    const field = screen.getByRole("combobox", { name: "Your job title" });
    expect(field).toHaveValue("Registered nurse"); // the title to fix, kept to edit
    await user.clear(field);
    await user.type(field, "Doula");
    await user.click(await screen.findByRole("option", { name: /^Doula\s*,\s*UK job title/ }));

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Which of these is closest?" })).toHaveFocus(),
    );
    expect(screen.getByText(/Careerwright found “Doula” in the UK job-title index/)).toBeVisible();
    expect(sent.filter((s) => s.path.endsWith("/origin/role/title")).map((s) => s.body)).toEqual([
      { expected_version: 1, title: "Registered nurse" },
      { expected_version: 2, title: "Doula" },
    ]);
  });

  it("while fixing a title, names the way back to which is closest for what it does", async () => {
    // Design re-review R-M4: after "Change my job title", "Skip for now" went back to the
    // closest question, skipping nothing.
    const state: Live = { preferences: prefs(null), turns: [], profile };
    fakeApi(
      liveRoutes(state, [
        {
          method: "GET",
          path: /\/taxonomy\/titles$/,
          answer: titles("Registered nurse", [
            { source: "uk_title_index", title: "Registered nurse", soc_codes: [], isco_groups: [] },
          ]),
        },
        {
          method: "POST",
          path: /\/origin\/role\/title$/,
          status: 201,
          answer: () => {
            state.profile = named("Registered nurse", 2);
            return state.profile;
          },
        },
        {
          method: "GET",
          path: /\/origin$/,
          answer: () => origin("Registered nurse", "ons", "not_yet"),
        },
      ]),
    );
    const { user } = renderLive();

    await user.type(
      await screen.findByRole("combobox", { name: "Your job title" }),
      "Registered nurse",
    );
    await user.click(await screen.findByRole("option", { name: /UK job title \(ONS\)/ }));
    await user.click(await screen.findByRole("button", { name: "Change my job title" }));
    await screen.findByRole("heading", { name: "What do you do now, or what did you do last?" });

    expect(screen.queryByRole("button", { name: "Skip for now" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Back to “Which of these is closest?”" }));
    const closest = await screen.findByRole("heading", { name: "Which of these is closest?" });
    await waitFor(() => expect(closest).toHaveFocus());
  });

  it("keeps the first question's support panel until the person dismisses it, after another title or a skip", async () => {
    // Design re-review R-M2: the panel lived inside the first question, so saving another
    // title, or "Skip for now", took it away undismissed and the world moved again. The words
    // are the support tests' own (`FirstQuestion.test.tsx`).
    const risk = "I volunteer on a suicide prevention helpline.";
    const state: Live = { preferences: prefs(null), turns: [], profile };
    fakeApi(
      liveRoutes(state, [
        {
          method: "GET",
          path: /\/taxonomy\/titles$/,
          answer: (s: Sent) => {
            const q = new URLSearchParams(s.query).get("q") ?? "";
            return q === risk ? { ...titles(q, []), support_note: titlePanel } : titles(q, []);
          },
        },
        {
          method: "POST",
          path: /\/origin\/role\/title$/,
          status: 201,
          answer: () => {
            state.profile = named("Bookkeeping assistant", 2);
            return state.profile;
          },
        },
        {
          method: "GET",
          path: /\/origin$/,
          answer: () => origin("Bookkeeping assistant", "own_words", null),
        },
        {
          method: "PUT",
          path: /\/interview\/preferences$/,
          answer: () => {
            state.preferences = prefs("unsure");
            return state.preferences;
          },
        },
      ]),
    );
    const { user } = renderLive();
    const panel = () => screen.getByRole("region", { name: "Support is available" });

    const field = await screen.findByRole("combobox", { name: "Your job title" });
    await user.type(field, risk);
    await screen.findByRole("region", { name: "Support is available" });
    await user.clear(field);
    await user.type(field, "Bookkeeping assistant");
    await user.click(
      await screen.findByRole("option", { name: "Use my own words: “Bookkeeping assistant”" }),
    );
    const start = await screen.findByRole("heading", { name: "How would you like to start?" });
    expect(panel()).toBeVisible(); // after another title, still there
    // Once the start is done, it sits where the message panel does, above the reply field.
    await user.click(screen.getByRole("button", { name: "Help me explore" }));
    await screen.findByRole("heading", {
      name: "What would you like your working life to be like?",
    });
    expect(panel()).toBeVisible();
    expect(
      panel().compareDocumentPosition(
        screen.getByRole("textbox", { name: "Reply to Careerwright" }),
      ) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).not.toBe(0);
    await user.click(within(panel()).getByRole("button", { name: "Dismiss the support note" }));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
    expect(screen.getByRole("textbox", { name: "Reply to Careerwright" })).toHaveFocus();
    expect(start).not.toBeInTheDocument();
  });

  it("keeps the first question's support panel after Skip for now, until dismissed", async () => {
    const risk = "I volunteer on a suicide prevention helpline.";
    const state: Live = { preferences: prefs(null), turns: [], profile };
    fakeApi(
      liveRoutes(state, [
        {
          method: "GET",
          path: /\/taxonomy\/titles$/,
          answer: { ...titles(risk, []), support_note: titlePanel },
        },
      ]),
    );
    const { user } = renderLive();

    await user.type(await screen.findByRole("combobox", { name: "Your job title" }), risk);
    await screen.findByRole("region", { name: "Support is available" });
    await user.click(screen.getByRole("button", { name: "Skip for now" }));
    const start = await screen.findByRole("heading", { name: "How would you like to start?" });
    const panel = screen.getByRole("region", { name: "Support is available" });
    expect(panel).toBeVisible();
    // No title is in a field any more, so there is nothing to keep: only Dismiss.
    expect(within(panel).queryByRole("button", { name: "Keep it as my job title" })).toBeNull();
    await user.click(within(panel).getByRole("button", { name: "Dismiss the support note" }));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
    expect(start).toHaveFocus();
  });

  it("never moves focus later when saving the first answer failed (N-M6)", async () => {
    // Design review M-8: the start remembered it was leaving the question after a failed save,
    // so a role that arrived later by another path moved focus unasked.
    const state: Live = { preferences: prefs(null), turns: [], profile };
    fakeApi(
      liveRoutes(state, [
        {
          method: "GET",
          path: /\/taxonomy\/titles$/,
          answer: titles("Registered nurse", [
            { source: "uk_title_index", title: "Registered nurse", soc_codes: [], isco_groups: [] },
          ]),
        },
        {
          method: "POST",
          path: /\/origin\/role\/title$/,
          status: 409,
          answer: {
            error: {
              code: "STALE_INPUT_VERSION",
              message: "",
              retryable: false,
              stage: "profile",
              correlation_id: "c1",
              details: { current_version: 2 },
            },
          },
        },
        {
          method: "GET",
          path: /\/origin$/,
          answer: () => origin("Registered nurse", "ons", null),
        },
      ]),
    );
    const { user, queries } = renderLive();

    const field = await screen.findByRole("combobox", { name: "Your job title" });
    await user.type(field, "Registered nurse");
    await user.click(await screen.findByRole("option", { name: /UK job title \(ONS\)/ }));
    // It says why, and stays on the question.
    expect(await screen.findByText("This changed since you loaded it")).toBeVisible();
    // The role arrives by another path (another tab saved it): focus stays where it is.
    state.profile = named("Registered nurse", 2);
    await act(() => queries.invalidateQueries());
    const start = await screen.findByRole("heading", { name: "How would you like to start?" });
    expect(start).not.toHaveFocus();
  });

  it("keeps the person's own words and says what isn't known yet, asking for no other job", async () => {
    const state: Live = { preferences: prefs(null), turns: [], profile };
    fakeApi(
      liveRoutes(state, [
        { method: "GET", path: /\/taxonomy\/titles$/, answer: titles("Bookkeeping assistant", []) },
        {
          method: "POST",
          path: /\/origin\/role\/title$/,
          status: 201,
          answer: () => {
            state.profile = named("Bookkeeping assistant", 2);
            return state.profile;
          },
        },
        {
          method: "GET",
          path: /\/origin$/,
          answer: () => origin("Bookkeeping assistant", "own_words", null),
        },
      ]),
    );
    const { user } = renderLive();

    await user.type(
      await screen.findByRole("combobox", { name: "Your job title" }),
      "Bookkeeping assistant",
    );
    await user.click(
      await screen.findByRole("option", { name: "Use my own words: “Bookkeeping assistant”" }),
    );
    expect(
      await screen.findByRole("heading", { name: "How would you like to start?" }),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Careerwright keeps “Bookkeeping assistant” as your role, in your words. It couldn't match it in ESCO or the UK job-title index, so what this work asks for isn't known yet.",
      ),
    ).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Which of these is closest?" })).toBeNull();
  });
});

describe("[UI-06] each new reply is announced once, and focus follows the first task", () => {
  it("moves focus to the first question once the person chooses how to start", async () => {
    const state = { preferences: prefs(null), turns: [] as TurnOut[] };
    fakeApi(
      routes(state, [
        {
          method: "PUT",
          path: /\/interview\/preferences$/,
          answer: () => {
            state.preferences = prefs("unsure");
            return state.preferences;
          },
        },
      ]),
    );
    const user = renderYou();
    await skipFirstQuestion(user);
    // The skip moves focus on to how to start (Task 6d slice B).
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "How would you like to start?" })).toHaveFocus(),
    );

    await user.click(await screen.findByRole("button", { name: "Help me explore" }));

    const question = await screen.findByRole("heading", {
      name: "What would you like your working life to be like?",
    });
    await waitFor(() => expect(question).toHaveFocus());
  });

  it("says nothing on load, then announces every new checked reply", async () => {
    const state: Live = {
      preferences: prefs("unsure"),
      turns: [turn("complete", proposal)],
      profile,
    };
    fakeApi(liveRoutes(state));
    const { queries } = renderLive();
    await screen.findByText("Thanks. I noted two things for you to review.");
    const announcer = screen.getByTestId("you-announcer");
    expect(announcer).toHaveTextContent(/^$/); // an old reply is not news

    const second = {
      ...turn("complete", { ...unknownHours, reply: "Thanks, noted." } as TurnOut["proposal"]),
      turn_id: "t2",
    };
    state.turns = [{ ...turn("complete", proposal), decision: {} as TurnOut["decision"] }, second];
    await queries.invalidateQueries();
    await waitFor(() =>
      expect(announcer).toHaveTextContent("Careerwright replied: 1 change to review."),
    );

    const third = {
      ...turn("complete", { ...proposal, reply: "Good." } as TurnOut["proposal"]),
      turn_id: "t3",
    };
    state.turns = [
      ...state.turns.slice(0, 1),
      { ...second, decision: {} as TurnOut["decision"] },
      third,
    ];
    await queries.invalidateQueries();
    await waitFor(() =>
      expect(announcer).toHaveTextContent("Careerwright replied: 2 changes to review."),
    );
  });
});

describe("[STATE-06][PROF-08] sending a stale tray's message again goes through the send path", () => {
  const stale = { ...turn("complete", proposal), profile_version: 0 };

  it("sends once, says when it can't, and shows the support panel the API sends", async () => {
    const state: Live = { preferences: prefs("unsure"), turns: [stale], profile };
    let release: () => void = () => undefined;
    const sent = fakeApi(
      liveRoutes(state, [
        {
          method: "POST",
          path: /\/interview\/turns$/,
          status: 202,
          answer: async () => {
            await new Promise<void>((resolve) => {
              release = resolve;
            });
            return { ...turn("queued"), turn_id: "t2", support_note: panel };
          },
        },
      ]),
    );
    const { user } = renderLive();
    const again = await screen.findByRole("button", { name: "Send it again" });

    await user.click(again);
    await user.click(again); // still sending: no second request
    release();

    expect(await screen.findByRole("region", { name: "Support is available" })).toBeVisible();
    expect(sent.filter((s) => s.method === "POST")).toHaveLength(1);
    expect(sent.find((s) => s.method === "POST")?.body).toEqual({
      expected_profile_version: 1,
      message: stale.message,
    });
  });

  it("can't send while paused, and says so", async () => {
    const state: Live = {
      preferences: { ...prefs("unsure"), paused: true },
      turns: [stale],
      profile,
    };
    const sent = fakeApi(liveRoutes(state));
    const { user } = renderLive();

    const again = await screen.findByRole("button", { name: "Send it again" });
    expect(again).toHaveAttribute("aria-disabled", "true"); // focusable, with its reason
    expect(screen.getAllByText("Paused: resume to send.").length).toBeGreaterThan(0);
    await user.click(again);
    expect(sent.some((s) => s.method === "POST")).toBe(false);
  });
});

describe("[PROF-09] a message with a risk stem is sent as usual, with the support panel", () => {
  it("sends it at once, announces the panel without moving focus, and lets it be dismissed", async () => {
    const sent = fakeApi(
      routes({ preferences: prefs("unsure"), turns: [] }, [
        {
          method: "POST",
          path: /\/interview\/turns$/,
          status: 202,
          answer: { ...turn("queued"), support_note: panel },
        },
      ]),
    );
    const user = renderYou();

    const field = await screen.findByLabelText("Reply to Careerwright");
    await user.type(field, "I volunteer on a suicide prevention helpline.");
    await user.click(screen.getByRole("button", { name: "Send" }));

    // One request, the message as typed, nothing to confirm: no hold, no extra click.
    const shown = await screen.findByRole("region", { name: "Support is available" });
    const posts = sent.filter((s) => s.method === "POST");
    expect(posts.map((s) => s.body)).toEqual([
      { expected_profile_version: 1, message: "I volunteer on a suicide prevention helpline." },
    ]);
    expect(field).toHaveValue(""); // it was sent
    expect(screen.queryByRole("alert")).toBeNull(); // calm: not an alert
    expect(shown).toHaveTextContent("Samaritans: Call 116 123");
    expect(shown).toHaveTextContent("sent to Careerwright as usual");
    expect(shown).toHaveTextContent("checked on their own websites on 28 October 2026");
    // Session 1 accepted the panel; its review state is not for someone who may be in distress.
    expect(shown).not.toHaveTextContent(/provisional|reviewed/);
    // No career question this turn: the question steps aside while the panel is shown.
    expect(screen.queryByRole("heading", { name: /What would you most like/ })).toBeNull();
    // Announced politely; focus left where it was (re-review 2, I-4).
    expect(screen.getByTestId("you-announcer")).toHaveTextContent(
      "Your message was sent. Support information is shown above the reply field.",
    );
    expect(screen.getByRole("button", { name: "Send" })).toHaveFocus(); // not moved to the panel
    await user.click(within(shown).getByRole("button", { name: "Dismiss the support note" }));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
    expect(field).toHaveFocus(); // M-1: back to the reply field, not lost
  });

  it("shows the panel with a refused send too, and says the message was not sent", async () => {
    // Re-review 4, I-2: the API screens the message before anything can refuse it.
    const notSent = {
      ...panel,
      message:
        "If anything you mentioned is about how you are feeling, support is available any " +
        "time, from people trained to help. Your message was not sent; the reason is shown below.",
    };
    fakeApi(
      routes({ preferences: prefs("unsure"), turns: [] }, [
        {
          method: "POST",
          path: /\/interview\/turns$/,
          status: 402,
          answer: {
            error: {
              code: "BUDGET_EXCEEDED",
              message: "This call would exceed the run spend limit for your key.",
              retryable: false,
              stage: "spend",
              correlation_id: "c1",
              details: { scope: "run" },
            },
            support_note: notSent,
          },
        },
      ]),
    );
    const user = renderYou();

    const field = await screen.findByLabelText("Reply to Careerwright");
    await user.type(field, "I volunteer on a suicide prevention helpline.");
    await user.click(screen.getByRole("button", { name: "Send" }));

    const shown = await screen.findByRole("region", { name: "Support is available" });
    expect(shown).toHaveTextContent("Your message was not sent");
    expect(shown).toHaveTextContent("Samaritans: Call 116 123");
    expect(await screen.findByText(/The spending limit for model calls/)).toBeVisible();
    expect(field).toHaveValue("I volunteer on a suicide prevention helpline."); // kept
    expect(screen.getByTestId("you-announcer")).toHaveTextContent(
      "Your message was not sent. Support information is shown above the reply field.",
    );
  });
});

describe("[UI-06] focus moves to the question only when the entry choice is saved", () => {
  it("does not move focus later if saving the choice failed", async () => {
    const state = { preferences: prefs(null), turns: [] as TurnOut[] };
    fakeApi(
      routes(state, [
        {
          method: "PUT",
          path: /\/interview\/preferences$/,
          status: 503,
          answer: {
            error: {
              code: "STORE_UNAVAILABLE",
              message: "The database is unavailable.",
              retryable: true,
              stage: "storage",
              correlation_id: "c4",
              details: {},
            },
          },
        },
      ]),
    );
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queries}>
        <EvidenceProvider>
          <YouChapter workspace={workspace} profile={profile} />
        </EvidenceProvider>
      </QueryClientProvider>,
    );
    const user = userEvent.setup();
    await skipFirstQuestion(user);

    await user.click(await screen.findByRole("button", { name: "Help me explore" }));
    expect(await screen.findByRole("alert")).toBeVisible();
    // Later the choice arrives some other way (another tab): focus must not jump.
    state.preferences = prefs("unsure");
    await queries.invalidateQueries();
    const question = await screen.findByRole("heading", {
      name: "What would you like your working life to be like?",
    });
    expect(question).not.toHaveFocus();
  });
});

describe("[UI-06][STATE-01] a failed reply says why and keeps one primary action", () => {
  it("offers Try again as the primary action and saves nothing", async () => {
    fakeApi(
      routes({ preferences: prefs("unsure"), turns: [turn("failed")] }, [
        {
          method: "GET",
          path: /\/turns\/t1\/reply$/,
          answer: {
            turn_id: "t1",
            completeness: "incomplete",
            seq: 1,
            text: "Thanks",
            updated_at: null,
          },
        },
      ]),
    );
    renderYou();

    expect(
      await screen.findByText("The reply didn't pass Careerwright's checks twice"),
    ).toBeVisible();
    expect(screen.getByText(/What we know is unchanged\./)).toBeVisible();
    expect(screen.queryByText(/version/i)).toBeNull(); // plain words (D-M5)
    expect(screen.getByRole("button", { name: "Try again" })).toHaveClass("btn-primary");
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-secondary");
    expect(visiblePrimaries()).toBe(1);
    // MODEL-03: what streamed before the failure stays visible, marked not saved.
    expect(await screen.findByText("Thanks")).toBeVisible();
    expect(screen.getByText("Stopped: not checked, nothing saved")).toBeVisible();
  });
});

describe("[UI-04][S0-V08] one filled primary action in each state of the chapter", () => {
  const count = visiblePrimaries;

  it("is the entry choice at the start, Send once there is something to send, and the tray's Save while reviewing", async () => {
    fakeApi(routes({ preferences: prefs(null), turns: [] }));
    const start = renderYou();
    // The first question has no bright action of its own: its titles are a list to pick from.
    await screen.findByRole("heading", { name: FIRST_QUESTION });
    expect(count()).toBe(0);
    await skipFirstQuestion(start);
    await screen.findByRole("button", { name: "Help me explore" });
    // Until the first answer the bright action is the entry choice, never Send on an empty
    // field (the audit's F17): the two equal choices together, edged in the action colour,
    // neither filled over the other.
    expect(screen.getByRole("button", { name: "Help me explore" })).toHaveClass("btn-choice");
    expect(screen.getByRole("button", { name: "I know my direction" })).toHaveClass("btn-choice");
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-secondary");
    expect(count()).toBe(0);
    // Chat is still immediate (session 2): typed first, Send is the one bright action.
    await start.type(screen.getByRole("textbox", { name: "Reply to Careerwright" }), "Hello");
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-primary");
    expect(count()).toBe(1);

    cleanup();
    fakeApi(routes({ preferences: prefs("unsure"), turns: [] }));
    const opened = renderYou();
    await screen.findByRole("button", { name: "Send" });
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-secondary");
    expect(count()).toBe(0);
    await opened.type(screen.getByRole("textbox", { name: "Reply to Careerwright" }), "Hello");
    expect(count()).toBe(1);

    cleanup();
    fakeApi(routes({ preferences: prefs("unsure"), turns: [turn("complete", proposal)] }));
    const user = renderYou();
    await screen.findByRole("region", { name: /To review/ });
    expect(count()).toBe(1);

    await user.click(screen.getByRole("tab", { name: "What we know" }));
    expect(count()).toBe(0); // reading what we know: nothing to decide
    await user.click(screen.getByRole("button", { name: "Edit answers directly" }));
    expect(await screen.findByRole("button", { name: "Save changes" })).toBeVisible();
    expect(count()).toBe(1); // the form's Save while it is open
  });
});

/** A decided demo turn whose next question asks about `asks` (the API's `asks_about`). */
const asking = (
  asks: NonNullable<TurnOut["proposal"]>["asks_about"],
  question: string,
): TurnOut => ({
  ...turn("complete", {
    ...(proposal as NonNullable<TurnOut["proposal"]>),
    changes: [],
    next_question: question,
    asks_about: asks,
  }),
});
const ROLE_QUESTION = "Do you have a role in mind, or would you like to explore?";
const keyStored: Route = {
  method: "GET",
  path: /\/credentials$/,
  answer: {
    items: [
      {
        credential_id: "c1",
        provider: "meta",
        active: true,
        consented_at: "2027-01-01T00:00:00Z",
        created_by: "a1",
        created_at: "2027-01-01T00:00:00Z",
        revoked_at: null,
        replaced_by: null,
      },
    ],
  },
};
const sendsTurn = { method: "POST", path: /\/interview\/turns$/, status: 202, answer: {} };
const withEvidence: ProfileOut = {
  ...profile,
  document: {
    ...answers,
    current_role: { state: "provided", value: "warehouse supervisor", source_ref_id: "s1" },
  },
};

describe("[STATE-09] the demo conversation never loops: example replies and two ways on", () => {
  it("offers the opening question's example replies and sends one in a tap", async () => {
    const sent = fakeApi(routes({ preferences: prefs("unsure"), turns: [] }, [sendsTurn]));
    const user = renderYou();

    const examples = await screen.findByRole("group", { name: "Example replies" });
    expect(
      within(examples)
        .getAllByRole("button")
        .map((b) => b.textContent),
    ).toEqual(["I help run a youth football team", "Skip"]); // one that isn't a job (Task 6f)
    await user.click(within(examples).getByRole("button", { name: "Skip" }));

    await waitFor(() =>
      expect(sent.filter((s) => s.method === "POST").map((s) => s.body)).toEqual([
        { expected_profile_version: 1, message: "Skip" },
      ]),
    );
  });

  it("offers each demo question's own examples, read from what it asks about", async () => {
    fakeApi(
      routes({
        preferences: prefs("unsure"),
        turns: [asking("cities", "Which English cities could you work in? Name up to three.")],
      }),
    );
    renderYou();

    const examples = await screen.findByRole("group", { name: "Example replies" });
    expect(
      within(examples)
        .getAllByRole("button")
        .map((b) => b.textContent),
    ).toEqual(["Leeds", "Skip"]);
  });

  it("offers no examples for a model's question: a live interview reads free text", async () => {
    const live = { ...workspace, data_mode: "live_assisted" as const };
    fakeApi(
      routes({ preferences: prefs("unsure"), turns: [asking(null, "What draws you to it?")] }, [
        keyStored,
      ]),
    );
    renderYou(profile, live);

    await screen.findByRole("heading", { name: "What draws you to it?" });
    expect(screen.queryByRole("group", { name: "Example replies" })).toBeNull();
  });

  it("asks a role or suggestions with two buttons: suggestions opens and starts them, focus with it", async () => {
    const sent = fakeApi(
      routes({ preferences: prefs("unsure"), turns: [asking("target_titles", ROLE_QUESTION)] }, [
        { method: "POST", path: /\/discoveries$/, status: 202, answer: {} },
      ]),
    );
    const user = renderYou(withEvidence);

    await screen.findByRole("heading", { name: ROLE_QUESTION });
    expect(screen.queryByRole("group", { name: "Example replies" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Show me suggestions" }));

    expect(screen.getByRole("tab", { name: "Suggestions" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Directions to explore" })).toHaveFocus(),
    );
    await waitFor(() =>
      expect(
        sent
          .filter((s) => s.method === "POST" && s.path.endsWith("/discoveries"))
          .map((s) => s.body),
      ).toEqual([{ expected_profile_version: 1 }]),
    );
    // Nothing else was written: no answer, no target.
    expect(sent.filter((s) => s.method !== "GET" && !s.path.endsWith("/discoveries"))).toEqual([]);
  });

  it("opens the answer form at the target roles, ready to type, for Name a role", async () => {
    const sent = fakeApi(
      routes({ preferences: prefs("unsure"), turns: [asking("target_titles", ROLE_QUESTION)] }),
    );
    const user = renderYou(withEvidence);

    await user.click(await screen.findByRole("button", { name: "Name a role" }));

    expect(screen.getByRole("tab", { name: "What we know" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await waitFor(() =>
      expect(screen.getByRole("textbox", { name: "Target role 1" })).toHaveFocus(),
    );
    expect(sent.filter((s) => s.method !== "GET")).toEqual([]); // nothing saved by itself
  });

  it("offers the same two in a live interview once the early answers are given and no target", async () => {
    const live = { ...workspace, data_mode: "live_assisted" as const };
    const given = { state: "unknown" as const, value: null, source_ref_id: "s1" };
    const early: ProfileOut = {
      ...profile,
      document: {
        ...answers,
        current_role: given,
        cities: given,
        weekly_study_hours: given,
        direct_spend_cap: given,
      },
    };
    fakeApi(
      routes({ preferences: prefs("unsure"), turns: [asking(null, "Is there a role you want?")] }, [
        keyStored,
      ]),
    );
    renderYou(early, live);

    await screen.findByRole("heading", { name: "Is there a role you want?" });
    expect(screen.getByRole("button", { name: "Show me suggestions" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Name a role" })).toBeVisible();
  });

  it("keeps keyboard focus when an example reply is tapped: it moves to the reply field (A-I2)", async () => {
    const sent = fakeApi(routes({ preferences: prefs("unsure"), turns: [] }, [sendsTurn]));
    const user = renderYou();

    const examples = await screen.findByRole("group", { name: "Example replies" });
    await user.click(within(examples).getByRole("button", { name: "Skip" }));

    // The tapped button goes while the message is sent; focus never falls to the page.
    await waitFor(() => expect(screen.getByLabelText("Reply to Careerwright")).toHaveFocus());
    await waitFor(() =>
      expect(sent.filter((s) => s.method === "POST").map((s) => s.body)).toEqual([
        { expected_profile_version: 1, message: "Skip" },
      ]),
    );
  });

  it("opens target entry once for Name a role: a later opening changes no answer, and saving goes through (A-I3)", async () => {
    const sent = fakeApi(
      routes({ preferences: prefs("unsure"), turns: [asking("target_titles", ROLE_QUESTION)] }, [
        { method: "PUT", path: /\/profile$/, answer: { ...withEvidence, version: 2 } },
      ]),
    );
    const user = renderYou(withEvidence);

    await user.click(await screen.findByRole("button", { name: "Name a role" }));
    await waitFor(() =>
      expect(screen.getByRole("textbox", { name: "Target role 1" })).toHaveFocus(),
    );
    // The person changes their mind: the form closes, and later opens to change something else.
    await user.click(screen.getByRole("button", { name: "Close the answer form" }));
    expect(screen.queryByRole("heading", { name: "Edit your answers" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Edit answers directly" }));

    expect(await screen.findByLabelText("How you answer target roles")).toHaveValue("unasked");
    expect(screen.queryByRole("textbox", { name: "Target role 1" })).toBeNull();
    expect(screen.getByRole("button", { name: "Close the answer form" })).toHaveFocus();
    await user.selectOptions(screen.getByLabelText("How you answer weekly study hours"), "unknown");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    const saved = sent.find((s) => s.method === "PUT")?.body as {
      profile: Record<string, { state: string }>;
    };
    expect(saved.profile.target_titles?.state).toBe("unasked");
    expect(saved.profile.weekly_study_hours?.state).toBe("unknown");
  });

  it("says Careerwright covers England for now, before the first answer only (BND1-02)", async () => {
    fakeApi(routes({ preferences: prefs(null), turns: [] }));
    renderYou();
    expect(await screen.findByText("Careerwright covers England for now.")).toBeVisible();

    cleanup();
    fakeApi(routes({ preferences: prefs("unsure"), turns: [turn("complete", proposal)] }));
    renderYou();
    await screen.findByRole("region", { name: /To review/ });
    expect(screen.queryByText("Careerwright covers England for now.")).toBeNull();
  });
});

describe("[UI-06] focus follows a sure person who asks to explore instead", () => {
  it("moves focus to the suggestions that replace Help me explore instead", async () => {
    const state = { preferences: prefs("sure"), turns: [] as TurnOut[] };
    fakeApi(
      routes(state, [
        {
          method: "PUT",
          path: /\/interview\/preferences$/,
          answer: () => {
            state.preferences = { ...state.preferences, version: 2, entry_mode: "unsure" };
            return state.preferences;
          },
        },
      ]),
    );
    const user = renderYou(withEvidence);
    await user.click(await screen.findByRole("tab", { name: "Suggestions" }));

    await user.click(screen.getByRole("button", { name: "Help me explore instead" }));

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Directions to explore" })).toHaveFocus(),
    );
  });
});
