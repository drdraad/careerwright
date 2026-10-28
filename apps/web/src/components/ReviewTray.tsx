"use client";
// The review tray (spec section 3, STATE-06): the newest reply's proposed changes, each to
// accept, edit or skip; a limit or target is saved only once confirmed by name (PROF-04).
// Facts the person stated and Nessa's readings look different (a dashed edge). One decision
// saves the chosen ones as a new version; an edited value is then saved as a direct edit,
// through the same command. Nothing changes until the person saves.
import { useState } from "react";
import type {
  DecisionResult,
  ProfileDocument,
  ProfileOut,
  ProposedChangeOut,
  TurnOut,
} from "@/generated/api";
import { ApiError } from "@/lib/api";
import { type Choice, type Choices, decisionFor } from "@/lib/conversation";
import { describeValue, draftFrom, type FieldDraft, fieldDraft, inputFrom } from "@/lib/profile";
import { useDecideTurn, useWriteProfile } from "@/lib/queries";
import { PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { AnswerControl } from "./fields";
import { RequestFailure } from "./PageState";

type Props = {
  workspaceId: string;
  profile: ProfileOut;
  turn: TurnOut;
  /** The profile moved on after the message was sent: its proposals can't be applied. */
  stale: boolean;
  primary: boolean;
  onResend(message: string): void;
  onSaved(before: ProfileDocument, after: ProfileOut): void;
};

function kindOf(change: ProposedChangeOut): string {
  if (change.hard_constraint) return "A limit or target: needs your confirmation";
  return change.basis === "stated" ? "You said" : "Nessa's reading, not a fact until you accept it";
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

export function ReviewTray({
  workspaceId,
  profile,
  turn,
  stale,
  primary,
  onResend,
  onSaved,
}: Props) {
  const decide = useDecideTurn(workspaceId);
  const write = useWriteProfile(workspaceId);
  const evidence = useEvidence();
  const changes = turn.proposal?.changes ?? [];
  const [choices, setChoices] = useState<Choices>({});
  const [edits, setEdits] = useState<Record<string, FieldDraft>>({});
  const chosen = changes.filter(
    (c) => choices[c.change_id] !== undefined && choices[c.change_id] !== "skip",
  );

  const choose = (change: ProposedChangeOut, choice: Choice) =>
    setChoices((current) => ({
      ...current,
      [change.change_id]: current[change.change_id] === choice ? undefined : choice,
    }));

  const startEdit = (change: ProposedChangeOut) => {
    const proposed = {
      state: change.state,
      value: change.value,
      source_ref_id: null,
    } as ProfileDocument[ProfileFieldName];
    setEdits((current) => ({ ...current, [change.change_id]: fieldDraft(proposed) }));
    setChoices((current) => ({ ...current, [change.change_id]: "edit" }));
  };

  const save = async () => {
    const before = profile.document;
    let result: DecisionResult;
    try {
      result = await decide.mutateAsync({
        turnId: turn.turn_id,
        body: decisionFor(changes, choices, profile.version),
      });
    } catch {
      return;
    }
    let after = result.profile;
    const edited = changes.filter((c) => choices[c.change_id] === "edit");
    if (edited.length > 0) {
      const draft = draftFrom(after.document);
      for (const change of edited) {
        const edit = edits[change.change_id];
        if (edit !== undefined) draft[change.field as ProfileFieldName] = edit;
      }
      const input = inputFrom(draft);
      if (!input.ok) return; // the inline field shows the problem; the decision is kept
      try {
        after = await write.mutateAsync({ expected_version: after.version, profile: input.input });
      } catch {
        return;
      }
    }
    onSaved(before, after);
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
          <Button variant="secondary" onClick={() => onResend(turn.message)}>
            Send it again
          </Button>
        </div>
      </section>
    );
  }

  const failure = decide.error ?? write.error;
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
              <AnswerControl
                name={field}
                draft={
                  edits[change.change_id] ??
                  fieldDraft({
                    state: "provided",
                    value: null,
                    source_ref_id: null,
                  } as ProfileDocument[ProfileFieldName])
                }
                onChange={(next) =>
                  setEdits((current) => ({ ...current, [change.change_id]: next }))
                }
              />
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
            decide.isPending || write.isPending
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
                body: {
                  expected_version: profile.version,
                  accept: [],
                  confirm_hard_constraints: [],
                },
              })
              .catch(() => null)
          }
        >
          Keep none
        </Button>
      </div>
      <p className="small muted">
        Skipped changes are not saved. Every saved answer keeps where it came from.
      </p>
    </section>
  );
}
