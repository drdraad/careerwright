// The You chapter against a scripted API at the network edge: the entry choice leads, a
// streamed reply is provisional until checked, the review tray saves only chosen and confirmed
// changes, explicit distress gets the support response, and one action is the primary.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type {
  PreferencesOut,
  ProfileDocument,
  ProfileOut,
  SketchOut,
  TurnOut,
  WorkspaceOut,
} from "@/generated/api";
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
      model_id: "nessa-fixture-interviewer-1",
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
    // A sure person is asked for the target and its level; suggestions stay optional.
    expect(
      await screen.findByRole("heading", {
        name: "Which role are you aiming for, and at what level?",
      }),
    ).toBeVisible();
    expect(screen.getByRole("button", { name: "Help me explore instead" })).toBeVisible();
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
    expect(screen.getByText("Nessa is still replying.")).toBeVisible(); // Send says why it waits
  });

  it("shows only the checked reply once the turn is complete", async () => {
    fakeApi(routes({ preferences: prefs("unsure"), turns: [turn("complete", proposal)] }));
    renderYou();

    expect(await screen.findByText("Thanks. I noted two things for you to review.")).toBeVisible();
    expect(screen.queryByText(/not checked yet/)).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "How many hours a week could you give to learning?" }),
    ).toBeVisible(); // one question at a time
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
    expect(within(tray).getByText(/needs your confirmation/)).toBeVisible();
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
    });
  });
});

describe("[PROF-09] explicit distress gets the support response instead of the interviewer", () => {
  it("shows the checked UK services, keeps the message, and sends it only if asked", async () => {
    const support = {
      policy: "acute_distress",
      policy_version: "support-policy-1",
      review_status: "provisional",
      message: "I'm sorry things feel this hard.",
      resources: [
        {
          name: "Samaritans",
          contact: "Call 116 123",
          when: "To talk",
          source_url: "https://www.samaritans.org/",
          checked_on: "2026-10-28",
        },
      ],
      sent_to_interviewer: false,
    };
    const sent = fakeApi(
      routes({ preferences: prefs("unsure"), turns: [] }, [
        { method: "POST", path: /\/interview\/turns$/, answer: support },
      ]),
    );
    const user = renderYou();

    await user.type(
      await screen.findByLabelText("Reply to Nessa"),
      "Some days I just want to die.",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Support is available now");
    expect(alert).toHaveTextContent("Samaritans: Call 116 123");
    expect(screen.getByLabelText("Reply to Nessa")).toHaveValue("Some days I just want to die.");
    await user.click(screen.getByRole("button", { name: "Send my message to Nessa anyway" }));
    await waitFor(() => expect(sent.filter((s) => s.method === "POST")).toHaveLength(2));
    expect(
      sent
        .filter((s) => s.method === "POST")
        .map((s) => (s.body as { send_after_support: boolean }).send_after_support),
    ).toEqual([false, true]);
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

    expect(await screen.findByText("The reply didn't pass Nessa's checks twice")).toBeVisible();
    expect(screen.getByText(/What we know is unchanged at version 1/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Try again" })).toHaveClass("btn-primary");
    expect(screen.getByRole("button", { name: "Send" })).toHaveClass("btn-secondary");
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(1);
  });
});
