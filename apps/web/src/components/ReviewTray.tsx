"use client";
// The review tray (spec section 3, STATE-06): the newest reply's proposed changes, each to
// accept, edit or skip; a limit or target is saved only once confirmed by name (PROF-04).
// Accept and Confirm are colour coded as well as worded (session 2, C3: leaf green, on a faint
// leaf tint once chosen, never a second bright fill beside the one primary action), and a limit
// says what it means in plain words. Facts the person stated and Careerwright's readings look
// different (a dashed edge, and a short tag). Edits are checked before anything is
// sent; then one decision saves the accepted proposals and the person's own answers together,
// as one version, or nothing at all (the tray and its edits stay, with the reason). Nothing
// changes until the person saves. Session W2: a list change says what it adds and removes
// against what is saved, the task answers have their hints, and Save and Keep none stay in
// view while the card is. Task W2F slice E (the product owner: "too verbose ... unnecessary
// qualifications"): each change reads in about two lines, its answer's name with only what
// changes, then its origin as a short tag and its actions; a hint (a limit's plain words
// included) is one step away, behind a button beside the answer's name.
import { useCallback, useState } from "react";
import type {
  ProfileDocument,
  ProfileOut,
  ProposedChangeOut,
  SupportNoteOut,
  TurnOut,
} from "@/generated/api";
import { ApiError } from "@/lib/api";
import { type Choice, type Choices, decisionFor, type Edits, listChange } from "@/lib/conversation";
import {
  describeValue,
  type FieldDraft,
  type FieldProblem,
  fieldDraft,
  problemText,
  readField,
} from "@/lib/profile";
import { useDecideTurn } from "@/lib/queries";
import {
  CARD_HINTED,
  EXPLAINED_FIELDS,
  FIELD_STATE,
  fieldStates,
  PROFILE_FIELDS,
  type ProfileFieldName,
  REVIEW_CARD,
} from "@/lib/vocabulary";
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
  /** The calm support panel the API sent with the decision or its refusal, when an answer
   *  typed here triggered the support screen; null otherwise. */
  onSupport(note: SupportNoteOut | null): void;
};

function proposedValue(change: ProposedChangeOut): string {
  if (change.value === null) return change.state === "provided" ? "" : FIELD_STATE[change.state];
  return describeValue(change.value, change.field as ProfileFieldName);
}

/** What a change reads as after its answer's name: only what it changes against what is saved,
 *  in plain words ("adds fixing machines, removes helping at Brownies", so an item taken back
 *  reads as removed), or, for a new answer or one that isn't a list, just its value. */
function changeWords(change: ProposedChangeOut, saved: ProfileDocument): string {
  const listed = listChange(change, saved[change.field as ProfileFieldName]);
  if (listed === null) return proposedValue(change);
  const parts = [
    ...(listed.added.length > 0 ? [REVIEW_CARD.adds(listed.added)] : []),
    ...(listed.removed.length > 0 ? [REVIEW_CARD.removes(listed.removed)] : []),
  ];
  if (change.state !== "provided") return [FIELD_STATE[change.state], ...parts].join(", ");
  return parts.length === 0 ? proposedValue(change) : parts.join(", ");
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
  onSupport,
}: Props) {
  const decide = useDecideTurn(workspaceId);
  const evidence = useEvidence();
  const changes = turn.proposal?.changes ?? [];
  const [choices, setChoices] = useState<Choices>({});
  const [drafts, setDrafts] = useState<Record<string, FieldDraft>>({});
  const [problems, setProblems] = useState<Record<string, FieldProblem>>({});
  /** The changes whose hint is open (one step away). */
  const [explained, setExplained] = useState<Record<string, boolean>>({});
  // Save and Keep none stay at the foot of the window, so whatever is focused or scrolled into
  // view must stop above them (WCAG 2.2 2.4.11): the window's scroll padding keeps the bar's own
  // height clear (`--tray-actions-height`, globals.css), as it changes when it wraps (three rows
  // at 320 px; Task W2F slice E), as the answer form's Save bar does. Measured while the bar is
  // there (a stale card has none).
  const measureBar = useCallback((element: HTMLDivElement) => {
    const root = document.documentElement;
    const measure = new ResizeObserver(() =>
      root.style.setProperty("--tray-actions-height", `${element.offsetHeight}px`),
    );
    measure.observe(element);
    return () => {
      measure.disconnect();
      root.style.removeProperty("--tray-actions-height");
    };
  }, []);
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
      .catch((error: unknown) => {
        onSupport(error instanceof ApiError ? error.supportNote : null);
        return null;
      });
    if (after !== null) {
      onSupport(after.support_note ?? null);
      onSaved(after.profile);
    }
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
              : "Careerwright's reading of what you said"}
          </span>
          <figure className="grid gap-4">
            <blockquote className="small">“{turn.message}”</blockquote>
            <figcaption className="small muted">Your message</figcaption>
          </figure>
          <p className="small">Why: {change.reason}</p>
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
      <h3 id="tray-title">{REVIEW_CARD.heading(changes.length)}</h3>
      {changes.map((change) => {
        const field = change.field as ProfileFieldName;
        const choice = choices[change.change_id];
        const editing = choice === "edit";
        const label = PROFILE_FIELDS[field].label;
        const draft = drafts[change.change_id] ?? editDraft(change);
        const problem = problems[change.change_id];
        const errorId = `edit-${change.change_id}-error`;
        const hintId = `hint-${change.change_id}`;
        const hinted = EXPLAINED_FIELDS.has(field) || CARD_HINTED.has(field);
        const open = explained[change.change_id] === true;
        const setDraft = (next: FieldDraft) =>
          setDrafts((current) => ({ ...current, [change.change_id]: next }));
        return (
          <div key={change.change_id} className="proposal" data-basis={change.basis}>
            <div className="proposal-head">
              <span className="proposal-value">
                {label}: {changeWords(change, profile.document)}
              </span>
              {hinted && (
                <Button
                  variant="icon"
                  glyph="info"
                  aria-label={REVIEW_CARD.means(label)}
                  aria-expanded={open}
                  aria-controls={hintId}
                  onClick={() =>
                    setExplained((current) => ({ ...current, [change.change_id]: !open }))
                  }
                />
              )}
            </div>
            {hinted && (
              <p id={hintId} className="small muted" hidden={!open}>
                {PROFILE_FIELDS[field].hint}
              </p>
            )}
            {editing && (
              <div className="grid gap-8">
                <FieldStateSelect
                  label={label}
                  draft={draft}
                  states={fieldStates(field)}
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
              <span className="proposal-kind">{REVIEW_CARD.origin[change.basis]}</span>
              {change.hard_constraint ? (
                <Button
                  variant="accept"
                  glyph="accept"
                  aria-pressed={choice === "confirm"}
                  onClick={() => choose(change, "confirm")}
                >
                  Confirm <span className="sr-only">{label.toLowerCase()} as a limit</span>
                </Button>
              ) : (
                <Button
                  variant="accept"
                  glyph="accept"
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
      {/* Kept in view at the foot of the screen while the card is (session W2: with three or
          more changes, Save sat below the first screen). */}
      <div ref={measureBar} className="tray-actions">
        <Button
          variant={primary ? "primary" : "secondary"}
          onClick={() => void save()}
          disabledReason={
            decide.isPending ? "Saving…" : chosen.length === 0 ? REVIEW_CARD.saveWaits : undefined
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
              .then((after) => onSaved(after.profile))
              .catch(() => null)
          }
        >
          Keep none
        </Button>
      </div>
    </section>
  );
}
