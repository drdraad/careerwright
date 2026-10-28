"use client";
// "What we know" in brief (spec section 3): the answers so far and what is not known yet,
// each in words (Unknown, Skipped and Prefer not to say are answers, never blanks), with
// the way in to edit them and to undo the last save from the conversation.
import type { ProfileOut } from "@/generated/api";
import { describeField } from "@/lib/profile";
import { useRevertProfile } from "@/lib/queries";
import { PROFILE_FIELD_ORDER, PROFILE_FIELDS } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

/** The version the last save from the conversation created. */
export type LastSave = { version: number };

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
  onUndone(restored: ProfileOut): void;
  onEdit(): void;
  editing: boolean;
}) {
  const revert = useRevertProfile(workspaceId);
  const known = PROFILE_FIELD_ORDER.filter((name) => profile.document[name].state !== "unasked");
  const open = PROFILE_FIELD_ORDER.filter((name) => profile.document[name].state === "unasked");
  // Undo restores the version before the last save, each answer with the source it had (a
  // revert, never a direct edit), while nothing newer has been saved.
  const undoable = lastSave !== null && lastSave.version === profile.version;

  return (
    <>
      {undoable && lastSave !== null && (
        <div className="known-group">
          <p className="small">Saved as version {lastSave.version}.</p>
          <div>
            <Button
              variant="secondary"
              onClick={() =>
                void revert
                  .mutateAsync({
                    expected_version: profile.version,
                    to_version: lastSave.version - 1,
                  })
                  .then(onUndone)
                  .catch(() => null)
              }
              disabledReason={revert.isPending ? "Undoing…" : undefined}
            >
              Undo the last save
            </Button>
          </div>
          {revert.error !== null && <RequestFailure error={revert.error} />}
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
