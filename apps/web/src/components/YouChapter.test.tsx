// The You chapter against a scripted API at the network edge: the entry choice leads, a
// streamed reply is provisional until checked, the review tray saves only chosen and confirmed
// changes, a message with a risk stem is sent with the support panel beside it, and one action
// is the primary.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type {
  DiscoveryOut,
  PreferencesOut,
  ProfileDocument,
  ProfileOut,
  SketchOut,
  SlateOut,
  SuggestionOut,
  SupportNoteOut,
  TurnOut,
  WorkspaceOut,
} from "@/generated/api";
import { useProfile } from "@/lib/queries";
import { fakeApi, type Route } from "@/test/fakeApi";
import { EvidenceProvider } from "./EvidenceDrawer";
import { YouChapter } from "./YouChapter";

const WS = "w-you";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const answers: ProfileDocument = {
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
  label: "Early sketch, not a checked route",
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

function renderYou() {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <YouChapter workspace={workspace} profile={profile} />
      </EvidenceProvider>
    </QueryClientProvider>,
  );
  return userEvent.setup();
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
  why_it_could_suit: ["What you enjoy: “repairing bicycles”."],
  what_might_not_suit: [],
  entry_gates: [],
  evidence_gaps: [],
  try_it: [],
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
      summary: null,
    },
    pool_size: 2,
    pool_target: [60, 120],
    beyond_pool_limit: 0,
    excluded: { occupations: 0, families: 0 },
    queries: [],
    unsearchable_queries: [],
    unsupported_hypotheses: [],
    not_included: [],
    unmatched_titles: [],
    ambiguous_titles: [],
    connection: null,
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
      within(answersShown).getByText(/The most you'd spend on the whole change, all added up/),
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
      name: "What would you most like to be different about your working life?",
    });
    await waitFor(() => expect(question).toHaveFocus());
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
  const decided = (state: Live): Route => ({
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
      return { turn_id: "t1", decision: {}, profile: state.profile };
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

    await user.click(await screen.findByRole("button", { name: "Help me explore" }));

    const question = await screen.findByRole("heading", {
      name: "What would you most like to be different about your working life?",
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

    await user.click(await screen.findByRole("button", { name: "Help me explore" }));
    expect(await screen.findByRole("alert")).toBeVisible();
    // Later the choice arrives some other way (another tab): focus must not jump.
    state.preferences = prefs("unsure");
    await queries.invalidateQueries();
    const question = await screen.findByRole("heading", {
      name: "What would you most like to be different about your working life?",
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

  it("is Send when nothing waits, the tray's Save while reviewing, and Send at the entry", async () => {
    fakeApi(routes({ preferences: prefs(null), turns: [] }));
    renderYou();
    await screen.findByRole("button", { name: "Help me explore" });
    // Chat is immediate (session 2): Send is the one action; the two equal choices are quick
    // answers, neither pushed.
    expect(screen.getByRole("button", { name: "Help me explore" })).toHaveClass("btn-secondary");
    expect(screen.getByRole("button", { name: "I know my direction" })).toHaveClass(
      "btn-secondary",
    );
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-primary");
    expect(count()).toBe(1);

    cleanup();
    fakeApi(routes({ preferences: prefs("unsure"), turns: [] }));
    renderYou();
    await screen.findByRole("button", { name: "Send" });
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-primary");
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
