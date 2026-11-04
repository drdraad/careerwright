"use client";

import { useState } from "react";
import type { ProfileOut } from "@/generated/api";
import { describeField } from "@/lib/profile";
import { useProfileVersion, useProfileVersions, useRevertProfile } from "@/lib/queries";
import { PROFILE_FIELD_ORDER, PROFILE_FIELDS } from "@/lib/vocabulary";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";

function savedAt(value: string | null): string {
  if (value === null) return "Time unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Time unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    date,
  );
}

/** Earlier answers are read only; restoring one uses the API's versioned revert. */
export function ProfileHistory({
  workspaceId,
  profile,
}: {
  workspaceId: string;
  profile: ProfileOut;
}) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [restored, setRestored] = useState<{ from: number; as: number } | null>(null);
  const versions = useProfileVersions(workspaceId, open);
  const previous = useProfileVersion(workspaceId, selected, open);
  const revert = useRevertProfile(workspaceId);
  const older = versions.data?.filter((item) => item.version < profile.version) ?? [];
  const snapshot = previous.data?.version === selected ? previous.data : null;
  const answers =
    snapshot === null
      ? []
      : PROFILE_FIELD_ORDER.filter((name) => snapshot.document[name].state !== "unasked");

  return (
    <details className="details" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>Earlier answers</summary>
      <div className="mt-12 grid gap-12">
        {versions.isPending && <LoadingState stage="Loading earlier answers" />}
        {versions.error !== null && <RequestFailure error={versions.error} />}
        {versions.isSuccess && older.length === 0 && (
          <p className="small muted">No earlier saved answers yet.</p>
        )}
        {older.length > 0 && (
          <ol className="fact-list">
            {older.map((item) => (
              <li className="fact" key={item.version}>
                <span>
                  Version {item.version}
                  {item.created_at !== null && (
                    <>
                      <br />
                      <time dateTime={item.created_at}>{savedAt(item.created_at)}</time>
                    </>
                  )}
                </span>
                <Button
                  variant="quiet"
                  aria-expanded={selected === item.version}
                  onClick={() => {
                    setSelected(selected === item.version ? null : item.version);
                    setConfirming(false);
                    revert.reset();
                  }}
                >
                  {selected === item.version ? "Close answers" : `View version ${item.version}`}
                </Button>
              </li>
            ))}
          </ol>
        )}
        {selected !== null && previous.isPending && (
          <LoadingState stage={`Loading version ${selected}`} />
        )}
        {selected !== null && previous.error !== null && <RequestFailure error={previous.error} />}
        {snapshot !== null && (
          <section className="known-group" aria-label={`Answers in version ${snapshot.version}`}>
            <h3>Version {snapshot.version} answers</h3>
            {answers.length === 0 ? (
              <p className="small muted">No answers were saved in this version.</p>
            ) : (
              <dl className="fact-list">
                {answers.map((name) => (
                  <div className="fact" key={name}>
                    <dt>{PROFILE_FIELDS[name].label}</dt>
                    <dd>{describeField(snapshot.document[name], name)}</dd>
                  </div>
                ))}
              </dl>
            )}
            <p className="small muted">Restoring these answers keeps each answer’s saved source.</p>
            {confirming ? (
              <div className="grid gap-8">
                <p>Restore version {snapshot.version} as a new saved version?</p>
                <div className="flex flex-wrap gap-8">
                  <Button
                    variant="undo"
                    onClick={() =>
                      void revert
                        .mutateAsync({
                          expected_version: profile.version,
                          to_version: snapshot.version,
                        })
                        .then((saved) => {
                          setRestored({ from: snapshot.version, as: saved.version });
                          setSelected(null);
                          setConfirming(false);
                        })
                        .catch(() => null)
                    }
                    disabledReason={revert.isPending ? "Restoring…" : undefined}
                  >
                    Confirm restore
                  </Button>
                  <Button variant="quiet" onClick={() => setConfirming(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <Button variant="quiet" onClick={() => setConfirming(true)}>
                Restore version {snapshot.version}
              </Button>
            )}
          </section>
        )}
        {revert.error !== null && <RequestFailure error={revert.error} />}
        {restored !== null && profile.version === restored.as && (
          <p role="status">Version {restored.from} was restored as a new saved version.</p>
        )}
      </div>
    </details>
  );
}
