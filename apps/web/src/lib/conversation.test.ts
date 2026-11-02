import { describe, expect, it } from "vitest";
import type {
  PartialReplyOut,
  ProfileDocument,
  ProposalOut,
  ProposedChangeOut,
  RunOut,
  TurnOut,
} from "@/generated/api";
import {
  asksRoleOrExplore,
  type Choices,
  decisionFor,
  listChange,
  questionAsks,
  replyView,
  reviewable,
  turnFailed,
  turnRunning,
} from "./conversation";

function run(status: RunOut["status"], failure: RunOut["failure_class"] = null): RunOut {
  return {
    run_id: "t1",
    kind: "interview_turn",
    status,
    failure_class: failure,
    data_mode: "live_assisted",
    synthetic: true,
    model_id: "muse-spark-1.3-contributor",
    model_mode: "contributor",
    created_at: "2027-01-01T10:00:00Z",
    started_at: null,
    finished_at: null,
    attempts: [],
    output: null,
    profile_version: 1,
  };
}

function change(id: string, field: ProposedChangeOut["field"], hard = false): ProposedChangeOut {
  return {
    change_id: id,
    field,
    state: "provided",
    value: field === "cities" ? ["Leeds"] : "Shift supervisor",
    basis: "stated",
    message_ids: ["m1"],
    reason: "You said so.",
    hard_constraint: hard,
  };
}

function turn(status: RunOut["status"], changes: ProposedChangeOut[] = []): TurnOut {
  return {
    turn_id: "t1",
    message_id: "m1",
    message: "I could work in Leeds.",
    profile_version: 1,
    created_at: "2027-01-01T10:00:00Z",
    run: run(status, status === "failed" ? "invalid_model_output" : null),
    proposal:
      status === "complete"
        ? {
            origin: "model",
            prompt_version: "interview-turn-2",
            profile_version: 1,
            reply: "Checked reply.",
            changes,
            next_question: "Which role?",
            asks_about: null,
            missing_critical_fields: [],
            ready_for_review: true,
          }
        : null,
    decision: null,
  };
}

const partial = (completeness: PartialReplyOut["completeness"], text: string | null) => ({
  turn_id: "t1",
  completeness,
  seq: 1,
  text,
  updated_at: "2027-01-01T10:00:01Z",
});

describe("[MODEL-03] a streamed reply reads as provisional until the checked reply replaces it", () => {
  it("shows the validated reply once the turn is complete, never the partial", () => {
    expect(replyView(turn("complete"), partial("superseded", null))).toEqual({
      kind: "checked",
      text: "Checked reply.",
    });
  });

  it("shows the reply so far while it streams, marked not checked", () => {
    expect(replyView(turn("running"), partial("streaming", "Thanks, I"))).toEqual({
      kind: "streaming",
      text: "Thanks, I",
      completeness: "streaming",
    });
    expect(replyView(turn("queued"), partial("none", null))).toEqual({ kind: "waiting" });
    // A stopped reply is not final: the run goes on and may stream again.
    expect(replyView(turn("running"), partial("stopped", "Thanks"))).toEqual({
      kind: "streaming",
      text: "Thanks",
      completeness: "stopped",
    });
  });

  it("keeps a failed turn's partial text visible as not saved, with the failure", () => {
    expect(replyView(turn("failed"), partial("incomplete", "Thanks, I noted"))).toEqual({
      kind: "failed",
      failure: "invalid_model_output",
      text: "Thanks, I noted",
    });
    expect(replyView(turn("failed"), undefined)).toEqual({
      kind: "failed",
      failure: "invalid_model_output",
      text: null,
    });
  });
});

describe("[STATE-06][PROF-04] the review tray saves only what the person chose", () => {
  const changes = [change("c1", "current_role"), change("c2", "cities", true)];

  it("applies a limit only once it is confirmed by name", () => {
    const accepted: Choices = { c1: "accept", c2: "accept" };
    const confirmed: Choices = { c1: "accept", c2: "confirm" };

    expect(decisionFor(changes, accepted, 1)).toEqual({
      expected_version: 1,
      accept: ["c1"],
      confirm_hard_constraints: [],
      edits: [],
    });
    expect(decisionFor(changes, confirmed, 1)).toEqual({
      expected_version: 1,
      accept: ["c1", "c2"],
      confirm_hard_constraints: ["cities"],
      edits: [],
    });
  });

  it("sends an edited proposal's new answer in the same decision, not as an acceptance", () => {
    const edits = { c1: { state: "provided" as const, value: "Night manager" } };

    expect(decisionFor(changes, { c1: "edit", c2: "confirm" }, 1, edits)).toEqual({
      expected_version: 1,
      accept: ["c2"],
      confirm_hard_constraints: ["cities"],
      edits: [{ field: "current_role", answer: { state: "provided", value: "Night manager" } }],
    });
    expect(decisionFor(changes, { c1: "edit", c2: "skip" }, 1, edits).accept).toEqual([]);
  });

  it("accepts an edit that leaves the proposal as it was, so its source is kept", () => {
    const unchanged = {
      c1: { state: "provided" as const, value: "Shift supervisor" },
      c2: { state: "provided" as const, value: ["Leeds"] },
    };

    expect(decisionFor(changes, { c1: "edit", c2: "edit" }, 1, unchanged)).toEqual({
      expected_version: 1,
      accept: ["c1", "c2"],
      confirm_hard_constraints: ["cities"],
      edits: [],
    });
  });

  it("reviews the newest turn with proposals, and calls it stale on a newer profile", () => {
    const pending = turn("complete", changes);
    const decided = {
      ...turn("complete", changes),
      turn_id: "t0",
      decision: {} as TurnOut["decision"],
    };

    expect(reviewable([decided, pending], 1)).toEqual({ turn: pending, stale: false });
    expect(reviewable([decided, pending], 2)).toEqual({ turn: pending, stale: true });
    expect(reviewable([decided], 1)).toBeNull();
    expect(reviewable([turn("complete", [])], 1)).toBeNull(); // nothing proposed
  });

  it("never brings back an older tray, and hides a stale one once a newer message is sent", () => {
    const older = { ...turn("complete", changes), turn_id: "t0" };
    const decided = { ...turn("complete", changes), decision: {} as TurnOut["decision"] };
    const resent = { ...turn("running"), turn_id: "t2" };

    expect(reviewable([older, decided], 2)).toBeNull(); // B-M10
    expect(reviewable([older, resent], 2)).toBeNull(); // B-I2: the resend is under way
  });
});

describe("[STATE-06] a list change reads as what it adds and removes against what is saved", () => {
  // Session W2: a list proposal is the whole list and replaces the saved one, so a thing taken
  // back could stay, or a saved one go, unseen.
  const saved = (value: string[]) => ({ state: "provided" as const, value, source_ref_id: "s1" });
  const proposed = (
    field: ProposedChangeOut["field"],
    value: ProposedChangeOut["value"],
    state: ProposedChangeOut["state"] = "provided",
  ): ProposedChangeOut => ({ ...change("c1", field), state, value });

  it("names each item added and each item removed, in the person's words and order", () => {
    expect(
      listChange(
        proposed("enjoyed_tasks", ["helping at Brownies", "fixing machines"]),
        saved(["working outdoors", "helping at Brownies"]),
      ),
    ).toEqual({ added: ["fixing machines"], removed: ["working outdoors"] });
    // Words that differ only in case are a different answer, as saving would store them.
    expect(listChange(proposed("cities", ["leeds"]), saved(["Leeds"]))).toEqual({
      added: ["leeds"],
      removed: ["Leeds"],
    });
  });

  it("removes every saved item when the list is answered another way", () => {
    expect(
      listChange(proposed("enjoyed_tasks", null, "skipped"), saved(["working outdoors"])),
    ).toEqual({ added: [], removed: ["working outdoors"] });
  });

  it("reads a qualification with its status, so a status change is a removal and an addition", () => {
    const held = {
      state: "provided" as const,
      value: [{ name: "Maths GCSE", status: "expected" as const }],
      source_ref_id: "s1",
    };
    expect(
      listChange(proposed("qualifications", [{ name: "Maths GCSE", status: "achieved" }]), held),
    ).toEqual({
      added: ["Maths GCSE (achieved)"],
      removed: ["Maths GCSE (expected, not achieved yet)"],
    });
  });

  it("says nothing more for a list with nothing saved yet, or an answer that isn't a list", () => {
    const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
    expect(listChange(proposed("enjoyed_tasks", ["fixing machines"]), unasked)).toBeNull();
    expect(
      listChange(proposed("current_role", "Night manager"), {
        state: "provided",
        value: "Shift supervisor",
        source_ref_id: "s1",
      }),
    ).toBeNull();
  });
});

describe("[MODEL-03] run states come from the generated enum, in one place", () => {
  it("tells a turn still running from one that ended with or without a checked reply", () => {
    expect(turnRunning(turn("queued"))).toBe(true);
    expect(turnRunning(turn("running"))).toBe(true);
    expect(turnFailed(turn("failed"))).toBe(true);
    expect(turnFailed({ ...turn("complete"), proposal: null })).toBe(true); // no checked reply
    expect(turnFailed(turn("complete"))).toBe(false);
    expect(turnRunning(turn("complete"))).toBe(false);
  });
});

const SRC = "8d1f6f8e-46a1-5c2b-9d0e-3f7a1b2c4d5e";
const unasked = { state: "unasked", value: null, source_ref_id: null } as const;
const known = { state: "unknown", value: null, source_ref_id: SRC } as const;
const blank: ProfileDocument = {
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
  enjoyed_tasks: unasked,
  confident_tasks: unasked,
  evidenced_tasks: unasked,
  work_style: unasked,
  minimum_salary: unasked,
};
const earlyAnswers: ProfileDocument = {
  ...blank,
  current_role: known,
  cities: known,
  weekly_study_hours: known,
  direct_spend_cap: known,
};

describe("[STATE-09] what the question in view asks about, and the role-or-explore question", () => {
  it("knows the opening's and the demo interviewer's questions, never a model's", () => {
    const asked = (asks: ProposalOut["asks_about"]): TurnOut => ({
      ...turn("complete"),
      proposal: { ...(turn("complete").proposal as ProposalOut), asks_about: asks },
    });
    expect(questionAsks(undefined, "sure")).toBe("target_titles");
    expect(questionAsks(undefined, "unsure")).toBe("open");
    expect(questionAsks(undefined, null)).toBeNull(); // typed before choosing
    expect(questionAsks(asked("cities"), "unsure")).toBe("cities");
    expect(questionAsks(asked(null), "unsure")).toBeNull();
  });

  it("offers suggestions or naming a role at the demo's role question, and live at its stage", () => {
    expect(asksRoleOrExplore("target_titles", true, "unsure", blank)).toBe(true);
    expect(asksRoleOrExplore("target_titles", true, null, blank)).toBe(true);
    // A sure person's opening asks for the target itself: no exploring offered.
    expect(asksRoleOrExplore("target_titles", true, "sure", blank)).toBe(false);
    expect(asksRoleOrExplore("cities", true, "unsure", earlyAnswers)).toBe(false);
    // Live: once the four early answers are given (Unknown counts) and no target is.
    expect(asksRoleOrExplore(null, false, "unsure", earlyAnswers)).toBe(true);
    expect(asksRoleOrExplore(null, false, "unsure", { ...earlyAnswers, cities: unasked })).toBe(
      false,
    );
    expect(
      asksRoleOrExplore(null, false, "unsure", { ...earlyAnswers, target_titles: known }),
    ).toBe(false);
  });

  it("[PROF-14] offers Show me suggestions in a live interview with no current role at all", () => {
    // Task 6f: "Show me suggestions" never waits for a current-role answer.
    expect(
      asksRoleOrExplore(null, false, "unsure", { ...earlyAnswers, current_role: unasked }),
    ).toBe(true);
  });
});
