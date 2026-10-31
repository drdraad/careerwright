"use client";
// How Careerwright talks with you is a preference, so it lives in the account menu with the
// other settings, never on the first screen (session 2: "Starts with How Nessa talks with you -
// this is a preference, not metadata about you"; C1: "ditch the tone selection - this should be
// in preferences"). It is this workspace's preference, and its heading says so in the product
// owner's word. While none is chosen the interviewer keeps it practical, so that is what it
// shows. Saving it is the same expected-version command as before, and says when it is saved.
import { useId } from "react";
import type { ConversationMode } from "@/generated/api";
import { usePreferences, useSetPreferences } from "@/lib/queries";
import { CONVERSATION_MODE } from "@/lib/vocabulary";
import { RequestFailure } from "./PageState";

/** The tone the interviewer uses until the person chooses one (`profile/preferences.py`). */
const DEFAULT_TONE: ConversationMode = "practical";

export function ConversationTone({ workspaceId }: { workspaceId: string }) {
  const id = useId();
  const preferences = usePreferences(workspaceId);
  const save = useSetPreferences(workspaceId);
  const current = preferences.data;
  if (current === undefined) {
    return preferences.error ? <RequestFailure error={preferences.error} /> : null;
  }
  return (
    <section className="grid gap-4" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`} className="small font-semibold">
        Preferences for this workspace
      </h2>
      <label htmlFor={id} className="small">
        How Careerwright talks with you
      </label>
      <select
        id={id}
        className="select"
        value={current.conversation_mode ?? DEFAULT_TONE}
        onChange={(event) =>
          save.mutate({
            expected_version: current.version,
            entry_mode: current.entry_mode,
            conversation_mode: event.target.value as ConversationMode,
            paused: current.paused,
          })
        }
      >
        {(Object.keys(CONVERSATION_MODE) as ConversationMode[]).map((mode) => (
          <option key={mode} value={mode}>
            {CONVERSATION_MODE[mode]}
            {mode === DEFAULT_TONE ? " (the default)" : ""}
          </option>
        ))}
      </select>
      <p role="status" className="small muted">
        {save.isSuccess && "Saved."}
      </p>
      {save.error !== null && <RequestFailure error={save.error} />}
    </section>
  );
}
