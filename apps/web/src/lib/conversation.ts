// The conversation's state, from the API's resources only (spec section 4): a streamed reply
// is provisional until the validated turn replaces it, and the review tray turns the person's
// choices into one decision. Nothing streamed is ever saved; a limit is saved only once it is
// confirmed by name (PROF-04).
import type {
  DecideTurn,
  FailureClass,
  PartialCompleteness,
  PartialReplyOut,
  ProposedChangeOut,
  TurnOut,
} from "@/generated/api";

export type ReplyView =
  | { kind: "checked"; text: string }
  | { kind: "waiting" }
  | { kind: "streaming"; text: string; completeness: PartialCompleteness }
  | { kind: "failed"; failure: FailureClass; text: string | null };

const ENDED = new Set(["failed", "provider_unavailable", "cancelled"]);

/** What to show for a turn's reply: the checked reply, the reply so far, or the failure. */
export function replyView(turn: TurnOut, partial: PartialReplyOut | undefined): ReplyView {
  if (turn.proposal !== null) return { kind: "checked", text: turn.proposal.reply };
  if (ENDED.has(turn.run.status)) {
    return {
      kind: "failed",
      failure: turn.run.failure_class ?? "unknown_failure",
      text: partial?.text ?? null,
    };
  }
  if (partial?.text) {
    return { kind: "streaming", text: partial.text, completeness: partial.completeness };
  }
  return { kind: "waiting" };
}

/** Per proposal: accepted, confirmed (a limit or target, by name), edited or skipped. */
export type Choice = "accept" | "confirm" | "edit" | "skip";
export type Choices = Record<string, Choice | undefined>;

/** The one decision a turn gets. An edited proposal is not accepted: the edit is saved as a
 *  direct edit afterwards, through the same command (ADR 0006 decision 7). */
export function decisionFor(
  changes: ProposedChangeOut[],
  choices: Choices,
  expectedVersion: number,
): DecideTurn {
  const accepted = changes.filter((change) => {
    const choice = choices[change.change_id];
    return change.hard_constraint ? choice === "confirm" : choice === "accept";
  });
  return {
    expected_version: expectedVersion,
    accept: accepted.map((change) => change.change_id),
    confirm_hard_constraints: accepted
      .filter((change) => change.hard_constraint)
      .map((change) => change.field),
  };
}

/** The newest turn with proposals not yet decided on; stale when the profile has moved on
 *  since its message was sent (its proposals can then only be sent again, never applied). */
export function reviewable(
  turns: TurnOut[],
  profileVersion: number,
): { turn: TurnOut; stale: boolean } | null {
  for (let index = turns.length - 1; index >= 0; index -= 1) {
    const turn = turns[index];
    if (turn === undefined || turn.decision !== null || turn.proposal === null) continue;
    if (turn.proposal.changes.length === 0) return null;
    return { turn, stale: turn.profile_version !== profileVersion };
  }
  return null;
}
