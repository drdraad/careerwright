"use client";
// "What we know" in brief (spec section 3): the answers so far and what is not known yet,
// each in words (Unknown, Skipped and Prefer not to say are answers, never blanks), the limits
// explained in plain words (session 2: "total spending limit and monthly payment limit - what
// do these mean??"), and the way in to edit them. `SaveNotice` says what the last decision
// saved, with Undo in its own colour (session 2, C3), wherever the person is.
import { type ReactNode, type Ref, useId } from "react";
import type { ProfileOut } from "@/generated/api";
import { describeField } from "@/lib/profile";
import { useRevertProfile } from "@/lib/queries";
import { EXPLAINED_FIELDS, PROFILE_FIELD_ORDER, PROFILE_FIELDS } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

/**
 * What the person's last decision on Careerwright's proposals did: saved a new version (which
 * may be undone while nothing newer is saved), kept none, or was undone.
 */
export type SaveOutcome =
  | { kind: "saved"; version: number }
  | { kind: "kept_none" }
  | { kind: "undone"; version: number };

const NOTICE: Record<SaveOutcome["kind"], { title: string; detail?: string }> = {
  saved: { title: "Saved to What we know" },
  kept_none: { title: "Nothing saved", detail: "You kept none of the changes." },
  undone: {
    title: "Save undone",
    detail: "Your answers are back as they were before it.",
  },
};

/** Whether the outcome still describes the answers shown (nothing newer was saved since). */
export function current(outcome: SaveOutcome | null, profile: ProfileOut): boolean {
  return outcome !== null && (outcome.kind === "kept_none" || outcome.version === profile.version);
}

/**
 * The outcome in words, and Undo while it can still apply. Undo restores the version before
 * the save, each answer with the source it had (a revert, never a direct edit).
 */
export function SaveNotice({
  workspaceId,
  profile,
  outcome,
  onUndone,
  headingRef,
}: {
  workspaceId: string;
  profile: ProfileOut;
  outcome: SaveOutcome | null;
  onUndone(restored: ProfileOut): void;
  /** Where focus lands once a decision or an undo is made, so it is never lost. */
  headingRef?: Ref<HTMLHeadingElement>;
}) {
  const revert = useRevertProfile(workspaceId);
  const titleId = useId();
  if (outcome === null || !current(outcome, profile)) return null;
  const words = NOTICE[outcome.kind];
  return (
    <section className="save-notice" data-outcome={outcome.kind} aria-labelledby={titleId}>
      <h3 id={titleId} tabIndex={-1} ref={headingRef}>
        {words.title}
      </h3>
      {words.detail !== undefined && <p className="small">{words.detail}</p>}
      {outcome.kind === "saved" && (
        <div>
          <Button
            variant="undo"
            glyph="undo"
            onClick={() =>
              void revert
                .mutateAsync({ expected_version: profile.version, to_version: outcome.version - 1 })
                .then(onUndone)
                .catch(() => null)
            }
            disabledReason={revert.isPending ? "Undoing…" : undefined}
          >
            Undo the last save
          </Button>
        </div>
      )}
      {revert.error !== null && <RequestFailure error={revert.error} />}
    </section>
  );
}

/**
 * The view's action comes first, under its heading, and the answer form it opens right under
 * it, so a phone shows the decision in its first screen however many answers there are (F7,
 * design review I3); the answers follow.
 */
export function WhatWeKnow({
  profile,
  onEdit,
  editing,
  form,
}: {
  profile: ProfileOut;
  onEdit(): void;
  editing: boolean;
  /** The answer form, while it is open. */
  form: ReactNode;
}) {
  const known = PROFILE_FIELD_ORDER.filter((name) => profile.document[name].state !== "unasked");
  const open = PROFILE_FIELD_ORDER.filter((name) => profile.document[name].state === "unasked");

  return (
    <>
      <div>
        <Button
          variant="secondary"
          aria-expanded={editing}
          aria-controls="edit-answers"
          onClick={onEdit}
        >
          {editing ? "Close the answer form" : "Edit answers directly"}
        </Button>
      </div>
      {form}
      <section className="known-group" aria-labelledby="known-answers">
        <h3 id="known-answers">Your answers</h3>
        {known.length === 0 ? (
          <p className="small muted">Nothing saved yet.</p>
        ) : (
          <dl className="fact-list">
            {known.map((name) => (
              <div key={name} className="fact">
                <dt>
                  {PROFILE_FIELDS[name].label}
                  {EXPLAINED_FIELDS.has(name) && (
                    <span className="fact-explained">{PROFILE_FIELDS[name].hint}</span>
                  )}
                </dt>
                {/* "I haven't had a job yet" is an answer like any given one (Task 6f). */}
                <dd
                  data-open={
                    profile.document[name].state !== "provided" &&
                    profile.document[name].state !== "no_job_yet"
                  }
                >
                  {describeField(profile.document[name], name)}
                </dd>
              </div>
            ))}
          </dl>
        )}
      </section>
      {open.length > 0 && (
        <section className="known-group" aria-labelledby="known-open">
          <h3 id="known-open">Not asked yet</h3>
          <p className="small muted">{open.map((name) => PROFILE_FIELDS[name].label).join(", ")}</p>
        </section>
      )}
    </>
  );
}
