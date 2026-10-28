"use client";
// "What we know" in brief (spec section 3): the answers so far and what is not known yet,
// each in words (Unknown, Skipped and Prefer not to say are answers, never blanks), with
// the way in to edit them and to undo the last save from the conversation.
import type { ProfileDocument, ProfileOut } from "@/generated/api";
import { describeField, inputOf } from "@/lib/profile";
import { useWriteProfile } from "@/lib/queries";
import { PROFILE_FIELD_ORDER, PROFILE_FIELDS } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

export type LastSave = { before: ProfileDocument; version: number };

export function WhatWeKnow({
  workspaceId,
  profile,
  lastSave,
  onUndone,
  onEdit,
  editing,
}: {
  workspaceId: string;
  profile: ProfileOut;
  lastSave: LastSave | null;
  onUndone(): void;
  onEdit(): void;
  editing: boolean;
}) {
  const write = useWriteProfile(workspaceId);
  const known = PROFILE_FIELD_ORDER.filter((name) => profile.document[name].state !== "unasked");
  const open = PROFILE_FIELD_ORDER.filter((name) => profile.document[name].state === "unasked");
  // Undo restores the answers from before the last save, as a direct edit, while nothing
  // newer has been saved.
  const undoable = lastSave !== null && lastSave.version === profile.version;

  return (
    <>
      {undoable && lastSave !== null && (
        <div className="known-group" aria-live="polite">
          <p className="small">Saved as version {lastSave.version}.</p>
          <div>
            <Button
              variant="secondary"
              onClick={() =>
                void write
                  .mutateAsync({
                    expected_version: profile.version,
                    profile: inputOf(lastSave.before),
                  })
                  .then(onUndone)
                  .catch(() => null)
              }
              disabledReason={write.isPending ? "Undoing…" : undefined}
            >
              Undo the last save
            </Button>
          </div>
          {write.error !== null && <RequestFailure error={write.error} />}
        </div>
      )}
      <section className="known-group" aria-labelledby="known-answers">
        <h3 id="known-answers">
          Answers{profile.version > 0 ? `, version ${profile.version}` : ""}
        </h3>
        {known.length === 0 ? (
          <p className="small muted">Nothing saved yet.</p>
        ) : (
          <dl className="fact-list">
            {known.map((name) => (
              <div key={name} className="fact">
                <dt>{PROFILE_FIELDS[name].label}</dt>
                <dd data-open={profile.document[name].state !== "provided"}>
                  {describeField(profile.document[name])}
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
    </>
  );
}
