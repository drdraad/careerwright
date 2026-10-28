// The conversation's state, from the API's resources only (spec section 4): a streamed reply
// is provisional until the validated turn replaces it, and the review tray turns the person's
// choices into one decision. Nothing streamed is ever saved; a limit is saved only once it is
// confirmed by name (PROF-04).
import type {
  DecideTurn,
  FailureClass,
  FieldEdit,
  PartialCompleteness,
  PartialReplyOut,
  ProposedChangeOut,
  TurnOut,
  WorkState,
} from "@/generated/api";

export type ReplyView =
  | { kind: "checked"; text: string }
  | { kind: "waiting" }
  | { kind: "streaming"; text: string; completeness: PartialCompleteness }
  | { kind: "failed"; failure: FailureClass; text: string | null };

const ENDED: ReadonlySet<WorkState> = new Set<WorkState>([
  "failed",
  "provider_unavailable",
  "cancelled",
]);

/** A run (a turn's or a discovery's) has not finished yet: queued or running. */
export function stillRunning(status: WorkState): boolean {
  return status !== "complete" && !ENDED.has(status);
}

/** The turn's run has not finished yet (queued or running). */
export function turnRunning(turn: TurnOut): boolean {
  return stillRunning(turn.run.status);
}

/** The turn's run finished without a checked reply: failed, unavailable, cancelled, or
 *  complete with nothing to show. Nothing from it was saved. */
export function turnFailed(turn: TurnOut): boolean {
  return turn.proposal === null && !turnRunning(turn);
}

/** What to show for a turn's reply: the checked reply, the reply so far, or the failure. */
export function replyView(turn: TurnOut, partial: PartialReplyOut | undefined): ReplyView {
  if (turn.proposal !== null) return { kind: "checked", text: turn.proposal.reply };
  if (turnFailed(turn)) {
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
/** The person's own answer for an edited proposal, by change ID. */
export type Edits = Record<string, FieldEdit["answer"] | undefined>;

function sameAnswer(change: ProposedChangeOut, answer: FieldEdit["answer"]): boolean {
  return (
    change.state === answer.state &&
    JSON.stringify(change.value ?? null) === JSON.stringify(answer.value ?? null)
  );
}

/** The one decision a turn gets: accepted and confirmed proposals, and the person's own
 *  answers for edited ones, saved together as one version. An edit that leaves the proposal
 *  as it was is accepted instead, so the answer keeps its source (ADR 0006 decision 7). */
export function decisionFor(
  changes: ProposedChangeOut[],
  choices: Choices,
  expectedVersion: number,
  edits: Edits = {},
): Required<DecideTurn> {
  const accepted: ProposedChangeOut[] = [];
  const edited: FieldEdit[] = [];
  for (const change of changes) {
    const choice = choices[change.change_id];
    const answer = edits[change.change_id];
    if (choice === "edit" && answer !== undefined && !sameAnswer(change, answer)) {
      edited.push({ field: change.field, answer });
    } else if (
      choice === "edit"
        ? answer !== undefined
        : choice === (change.hard_constraint ? "confirm" : "accept")
    ) {
      accepted.push(change);
    }
  }
  return {
    expected_version: expectedVersion,
    accept: accepted.map((change) => change.change_id),
    confirm_hard_constraints: accepted
      .filter((change) => change.hard_constraint)
      .map((change) => change.field),
    edits: edited,
  };
}

/** The newest turn with proposals, if they are not yet decided on; stale when the profile
 *  has moved on since its message was sent (its proposals can then only be sent again,
 *  never applied). An older turn's proposals never come back, and a stale tray gives way
 *  once a newer message has been sent. */
export function reviewable(
  turns: TurnOut[],
  profileVersion: number,
): { turn: TurnOut; stale: boolean } | null {
  for (let index = turns.length - 1; index >= 0; index -= 1) {
    const turn = turns[index];
    if (turn === undefined || turn.proposal === null) continue;
    if (turn.decision !== null || turn.proposal.changes.length === 0) return null;
    const stale = turn.profile_version !== profileVersion;
    if (stale && index < turns.length - 1) return null;
    return { turn, stale };
  }
  return null;
}
