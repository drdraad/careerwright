"use client";
// The review tray (spec section 3, STATE-06): the newest reply's proposed changes, each to
// accept, edit or skip; a limit or target is saved only once confirmed by name (PROF-04).
// Facts the person stated and Nessa's readings look different (a dashed edge). Edits are
// checked before anything is sent; then one decision saves the accepted proposals and the
// person's own answers together, as one version, or nothing at all (the tray and its edits
// stay, with the reason). Nothing changes until the person saves.
import { useState } from "react";
import type { ProfileDocument, ProfileOut, ProposedChangeOut, TurnOut } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { type Choice, type Choices, decisionFor, type Edits } from "@/lib/conversation";
import {
  describeValue,
  type FieldDraft,
  type FieldProblem,
  fieldDraft,
  problemText,
  readField,
} from "@/lib/profile";
import { useDecideTurn } from "@/lib/queries";
import { PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { AnswerControl, FieldError, FieldStateSelect } from "./fields";
import { RequestFailure } from "./PageState";

type Props = {
  workspaceId: string;
  profile: ProfileOut;
  turn: TurnOut;
  /** The profile moved on after the message was sent: its proposals can't be applied. */
  stale: boolean;
  primary: boolean;
  /** Why the message can't be sent again now (paused, no key, a reply on its way), if so. */
  resendBlocked: string | undefined;
  onResend(message: string): void;
  onSaved(after: ProfileOut): void;
};

function kindOf(change: ProposedChangeOut): string {
  const basis =
    change.basis === "stated" ? "You said" : "Nessa's reading, not a fact until you accept it";
  return change.hard_constraint ? `A limit or target: needs your confirmation. ${basis}` : basis;
}

function proposedValue(change: ProposedChangeOut): string {
  if (change.value === null) {
    return {
      provided: "",
      unknown: "Unknown",
      skipped: "Skipped",
      prefer_not_to_say: "Prefer not to say",
    }[change.state];
  }
  return describeValue(change.value);
}

/** Where an edit starts: the proposal's own answer, or an empty answer to type into when
 *  the proposal was Unknown, Skipped or Prefer not to say. */
function editDraft(change: ProposedChangeOut): FieldDraft {
  const proposed = {
    state: change.state,
    value: change.value,
    source_ref_id: null,
  } as ProfileDocument[ProfileFieldName];
  const draft = fieldDraft(proposed);
  return change.state === "provided" ? draft : { ...draft, state: "provided" };
}

export function ReviewTray({
  workspaceId,
  profile,
  turn,
  stale,
  primary,
  resendBlocked,
  onResend,
  onSaved,
}: Props) {
  const decide = useDecideTurn(workspaceId);
  const evidence = useEvidence();
  const changes = turn.proposal?.changes ?? [];
  const [choices, setChoices] = useState<Choices>({});
  const [drafts, setDrafts] = useState<Record<string, FieldDraft>>({});
  const [problems, setProblems] = useState<Record<string, FieldProblem>>({});
  const chosen = changes.filter(
    (c) => choices[c.change_id] !== undefined && choices[c.change_id] !== "skip",
  );

  const choose = (change: ProposedChangeOut, choice: Choice) =>
    setChoices((current) => ({
      ...current,
      [change.change_id]: current[change.change_id] === choice ? undefined : choice,
    }));

  const startEdit = (change: ProposedChangeOut) => {
    setDrafts((current) => ({
      ...current,
      [change.change_id]: current[change.change_id] ?? editDraft(change),
    }));
    setChoices((current) => ({ ...current, [change.change_id]: "edit" }));
  };

  const save = async () => {
    const answers: Edits = {};
    const found: Record<string, FieldProblem> = {};
    for (const change of changes) {
      const draft = drafts[change.change_id];
      if (choices[change.change_id] !== "edit" || draft === undefined) continue;
      const read = readField(change.field as ProfileFieldName, draft);
      if (read.ok) answers[change.change_id] = read.input;
      else found[change.change_id] = read.problem;
    }
    setProblems(found);
    if (Object.keys(found).length > 0) return; // nothing is sent until every edit is valid
    const after = await decide
      .mutateAsync({
        turnId: turn.turn_id,
        body: decisionFor(changes, choices, profile.version, answers),
      })
      .catch(() => null);
    if (after !== null) onSaved(after.profile);
  };

  const showSource = (change: ProposedChangeOut) =>
    evidence.open({
      title: "Where this came from",
      body: (
        <div className="grid gap-12">
          <p className="proposal-value">
            {PROFILE_FIELDS[change.field as ProfileFieldName].label}: {proposedValue(change)}
          </p>
          <span className="status" data-tone="unknown">
            {change.basis === "stated"
              ? "You said this; not verified"
              : "Nessa's reading of what you said"}
          </span>
          <figure className="grid gap-4">
            <blockquote className="small">“{turn.message}”</blockquote>
            <figcaption className="small muted">Your message</figcaption>
          </figure>
          <p className="small">Why: {change.reason}</p>
          <p className="small muted">
            Saving creates profile version {profile.version + 1}. Nothing changes until you save.
          </p>
        </div>
      ),
    });

  if (stale) {
    return (
      <section className="known-group" aria-labelledby="tray-title">
        <h3 id="tray-title">To review</h3>
        <p className="small">
          Your answers changed after you sent “{turn.message}”, so its {changes.length} proposed
          changes can't be applied to them. Send it again to get proposals for your latest answers.
        </p>
        <div>
          <Button
            variant="secondary"
            onClick={() => onResend(turn.message)}
            disabledReason={resendBlocked}
          >
            Send it again
          </Button>
        </div>
      </section>
    );
  }

  const failure = decide.error;
  return (
    <section className="known-group" aria-labelledby="tray-title">
      <h3 id="tray-title">
        To review: {changes.length} {changes.length === 1 ? "change" : "changes"} from your last
        message
      </h3>
      {changes.map((change) => {
        const field = change.field as ProfileFieldName;
        const choice = choices[change.change_id];
        const editing = choice === "edit";
        const label = PROFILE_FIELDS[field].label;
        const draft = drafts[change.change_id] ?? editDraft(change);
        const problem = problems[change.change_id];
        const errorId = `edit-${change.change_id}-error`;
        const setDraft = (next: FieldDraft) =>
          setDrafts((current) => ({ ...current, [change.change_id]: next }));
        return (
          <div
            key={change.change_id}
            className="proposal"
            data-basis={change.basis}
            data-chosen={choice === "accept" || choice === "confirm" || editing}
          >
            <span className="proposal-kind">{kindOf(change)}</span>
            <span className="proposal-value">
              {label}: {proposedValue(change)}
            </span>
            {editing && (
              <div className="grid gap-8">
                <FieldStateSelect
                  label={label}
                  draft={draft}
                  describedBy={problem ? errorId : undefined}
                  onChange={setDraft}
                />
                {draft.state === "provided" && (
                  <AnswerControl
                    name={field}
                    draft={draft}
                    error={problem ? problemText(problem) : undefined}
                    describedBy={problem ? errorId : undefined}
                    onChange={setDraft}
                  />
                )}
                {problem && <FieldError id={errorId}>{problemText(problem)}</FieldError>}
              </div>
            )}
            <div className="proposal-actions">
              {change.hard_constraint ? (
                <Button
                  variant="secondary"
                  aria-pressed={choice === "confirm"}
                  onClick={() => choose(change, "confirm")}
                >
                  Confirm <span className="sr-only">{label.toLowerCase()} as a limit</span>
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  aria-pressed={choice === "accept"}
                  onClick={() => choose(change, "accept")}
                >
                  Accept <span className="sr-only">{label.toLowerCase()}</span>
                </Button>
              )}
              <Button
                variant="secondary"
                aria-pressed={editing}
                onClick={() => (editing ? choose(change, "edit") : startEdit(change))}
              >
                Edit <span className="sr-only">{label.toLowerCase()}</span>
              </Button>
              <Button
                variant="quiet"
                aria-pressed={choice === "skip"}
                onClick={() => choose(change, "skip")}
              >
                Skip <span className="sr-only">{label.toLowerCase()}</span>
              </Button>
              <Button variant="quiet" onClick={() => showSource(change)}>
                Source <span className="sr-only">for {label.toLowerCase()}</span>
              </Button>
            </div>
          </div>
        );
      })}
      {failure !== null && (
        <RequestFailure
          error={failure}
          announce={!(failure instanceof ApiError && failure.code === "STALE_INPUT_VERSION")}
        />
      )}
      <div className="flex flex-wrap items-center gap-8">
        <Button
          variant={primary ? "primary" : "secondary"}
          onClick={() => void save()}
          disabledReason={
            decide.isPending
              ? "Saving…"
              : chosen.length === 0
                ? "Accept, confirm or edit at least one first."
                : undefined
          }
        >
          Save {chosen.length > 0 ? chosen.length : ""} to What we know
        </Button>
        <Button
          variant="quiet"
          onClick={() =>
            void decide
              .mutateAsync({
                turnId: turn.turn_id,
                body: decisionFor(changes, {}, profile.version),
              })
              .catch(() => null)
          }
        >
          Keep none
        </Button>
      </div>
      <p className="small muted">
        Skipped changes are not saved. Every saved answer keeps where it came from; an answer you
        edit is saved as yours.
      </p>
    </section>
  );
}
