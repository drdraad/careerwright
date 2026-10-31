"use client";
// How Careerwright talks with you is a preference, so it lives in the account menu with the
// other settings, never on the first screen (session 2: "Starts with How Nessa talks with you -
// this is a preference, not metadata about you"; C1: "ditch the tone selection - this should be
// in preferences"). Saving it is the same expected-version command as before.
import { useId } from "react";
import type { ConversationMode } from "@/generated/api";
import { usePreferences, useSetPreferences } from "@/lib/queries";
import { CONVERSATION_MODE } from "@/lib/vocabulary";
import { RequestFailure } from "./PageState";

export function ConversationTone({ workspaceId }: { workspaceId: string }) {
  const id = useId();
  const preferences = usePreferences(workspaceId);
  const save = useSetPreferences(workspaceId);
  const current = preferences.data;
  if (current === undefined) {
    return preferences.error ? <RequestFailure error={preferences.error} /> : null;
  }
  return (
    <div className="grid gap-4">
      <label htmlFor={id} className="small">
        How Careerwright talks with you
      </label>
      <select
        id={id}
        className="select"
        value={current.conversation_mode ?? ""}
        onChange={(event) =>
          save.mutate({
            expected_version: current.version,
            entry_mode: current.entry_mode,
            conversation_mode: event.target.value as ConversationMode,
            paused: current.paused,
          })
        }
      >
        {current.conversation_mode === null && (
          <option value="" disabled>
            Choose a tone
          </option>
        )}
        {(Object.keys(CONVERSATION_MODE) as ConversationMode[]).map((mode) => (
          <option key={mode} value={mode}>
            {CONVERSATION_MODE[mode]}
          </option>
        ))}
      </select>
      {save.error !== null && <RequestFailure error={save.error} />}
    </div>
  );
}
