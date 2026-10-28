import { describe, expect, it } from "vitest";
import type { PartialReplyOut, ProposedChangeOut, RunOut, TurnOut } from "@/generated/api";
import {
  type Choices,
  decisionFor,
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
