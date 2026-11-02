"use client";
// Removing a target (Task W2F; session W2, finding 2: there was no visible way). A Remove beside
// each target, in What we know's list and in a saved suggestion's box, goes through the
// profile's own save (an expected version and an idempotency key, Global Constraint 7), never a
// command of its own. What it did is said where it was done, focus goes there, and Undo (in
// orchid, session 2's C3) restores the version before it through the profile's revert. Removing
// the last target leaves the target roles Unknown (Task W2F's ruling): the person was asked and
// has none for now, so it is neither "Not asked yet" nor "Skipped". Removing a target leaves the
// suggestions current (the API's `stays_current`), so Suggest again is never pushed for it.
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState } from "react";
import type { ProfileInput, ProfileOut } from "@/generated/api";
import { ChangeKeys } from "@/lib/api";
import { inputOf } from "@/lib/profile";
import { keys, useRevertProfile, useSaveProfile } from "@/lib/queries";
import { YOUR_TARGETS } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

/** The target titles as the profile holds them: none unless the target roles are answered. */
export function targetTitles(profile: ProfileOut): string[] {
  const field = profile.document.target_titles;
  return field.state === "provided" ? (field.value ?? []) : [];
}

/** What a removal did, and where it was made (What we know's list, or one suggestion). */
type Removal = { titles: string[]; where: string; version: number; undone: boolean };

/**
 * Removing targets from `profile`, and undoing that. One per place that offers Remove; each
 * says what it did only where it was done (`where`), and only while nothing newer is saved.
 */
export function useTargetRemoval(profile: ProfileOut) {
  const id = profile.workspace_id;
  const queries = useQueryClient();
  const save = useSaveProfile(id);
  const revert = useRevertProfile(id);
  const [changes] = useState(() => new ChangeKeys());
  const [done, setDone] = useState<Removal | null>(null);
  // Where the last removal or undo was asked for: a failure is shown there.
  const [asked, setAsked] = useState<string | null>(null);
  const [focus, setFocus] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  // The button that was clicked goes with the change; focus goes to the words that say what it
  // did once they show, so it is never lost.
  useEffect(() => {
    if (focus && heading.current !== null) {
      heading.current.focus();
      setFocus(false);
    }
  });
  // A refused save (another tab saved first) shows the newer targets to remove from.
  const refresh = () => void queries.invalidateQueries({ queryKey: keys.scope(id) });

  const remove = (titles: string[], where: string) => {
    const kept = targetTitles(profile).filter((title) => !titles.includes(title));
    const targets: ProfileInput["target_titles"] =
      kept.length > 0 ? { state: "provided", value: kept } : { state: "unknown" };
    const input: ProfileInput = { ...inputOf(profile.document), target_titles: targets };
    const request = { expected_version: profile.version, profile: input };
    setAsked(where);
    revert.reset();
    save
      .mutateAsync({
        expectedVersion: profile.version,
        profile: input,
        idempotencyKey: changes.keyFor(request),
      })
      .then((stored) => {
        changes.settled();
        if (stored.version === profile.version) return; // nothing held them any more
        setDone({ titles, where, version: stored.version, undone: false });
        setFocus(true);
      })
      .catch(refresh);
  };

  const undo = (removal: Removal) => {
    setAsked(removal.where);
    save.reset();
    revert
      .mutateAsync({ expected_version: removal.version, to_version: removal.version - 1 })
      .then((restored) => {
        setDone({ ...removal, version: restored.version, undone: true });
        setFocus(true);
      })
      .catch(refresh);
  };

  /** Why Remove can't be used now, if it can't. */
  const busy = save.isPending
    ? YOUR_TARGETS.removing
    : revert.isPending
      ? YOUR_TARGETS.undoing
      : undefined;
  const failure = save.error ?? revert.error;
  return {
    remove,
    undo,
    busy,
    heading,
    /** What was done at `where`, while it still describes the targets shown. */
    shownAt: (where: string) =>
      done !== null && done.where === where && done.version === profile.version ? done : null,
    failureAt: (where: string) => (asked === where ? failure : null),
  };
}

export type TargetRemoval = ReturnType<typeof useTargetRemoval>;

/** What a removal at `where` did, with Undo while it can apply, or why it failed. */
export function RemovalNotice({
  removal,
  where,
  level: Heading,
}: {
  removal: TargetRemoval;
  where: string;
  /** The heading's level under the place it sits in. */
  level: "h4" | "h5";
}) {
  const titleId = useId();
  const shown = removal.shownAt(where);
  const failure = removal.failureAt(where);
  return (
    <>
      {shown !== null && (
        <section
          className="save-notice"
          data-outcome={shown.undone ? "undone" : "saved"}
          aria-labelledby={titleId}
        >
          <Heading id={titleId} className="font-semibold" tabIndex={-1} ref={removal.heading}>
            {shown.undone ? YOUR_TARGETS.undone(shown.titles) : YOUR_TARGETS.removed(shown.titles)}
          </Heading>
          {!shown.undone && (
            <div>
              <Button
                variant="undo"
                glyph="undo"
                onClick={() => removal.undo(shown)}
                disabledReason={removal.busy}
              >
                {YOUR_TARGETS.undo}{" "}
                <span className="sr-only">{YOUR_TARGETS.undoWhich(shown.titles)}</span>
              </Button>
            </div>
          )}
        </section>
      )}
      {failure !== null && <RequestFailure error={failure} />}
    </>
  );
}

/** Remove beside one target: says why it waits while a removal or an undo is saving. */
export function RemoveButton({
  title,
  onRemove,
  busy,
}: {
  /** The target as the person reads it here, for assistive tech. */
  title: string;
  onRemove(): void;
  busy: string | undefined;
}) {
  return (
    <Button variant="quiet" onClick={onRemove} disabledReason={busy}>
      {YOUR_TARGETS.remove} <span className="sr-only">{YOUR_TARGETS.removeWhich(title)}</span>
    </Button>
  );
}
