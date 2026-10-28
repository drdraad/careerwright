"use client";
// "What we know": the editable profile (spec section 3). Every answer has a state, so a
// missing value is never a zero. Saving is an expected-version command with an idempotency
// key (Global Constraint 7): a retry of the same change reuses its key, and a version saved
// elsewhere meanwhile is refused (409 STALE_INPUT_VERSION). Then the form moves to the newer
// version: answers the person did not touch take its values (so saving never reverts them),
// their edits stay, and a field both changed shows the newer value beside the edit. Nothing
// is merged silently, and a newer version that cannot be loaded says so. Either notice is
// announced and takes focus, and lists each answer the newer version changed (WCAG 4.1.3).
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState } from "react";
import type { ProfileDocument, ProfileOut } from "@/generated/api";
import { ApiError, ChangeKeys } from "@/lib/api";
import {
  describeField,
  draftFrom,
  type FieldProblem,
  inputFrom,
  type ProfileDraft,
  problemText,
  rebaseDraft,
} from "@/lib/profile";
import { profileQuery, useSaveProfile } from "@/lib/queries";
import { PROFILE_FIELD_ORDER, PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { FieldSource } from "./FieldSource";
import { FieldError, FieldStateSelect, ListInput, ValueInput } from "./fields";
import { Glyph } from "./Glyph";
import { RequestFailure } from "./PageState";

type Stale =
  | {
      kind: "rebased";
      to: number;
      changed: ProfileFieldName[];
      conflicts: ProfileFieldName[];
      latest: ProfileDocument;
    }
  | { kind: "unloaded"; error: unknown };

export function ProfileEditor({
  workspaceId,
  profile,
}: {
  workspaceId: string;
  profile: ProfileOut;
}) {
  const queries = useQueryClient();
  const save = useSaveProfile(workspaceId);
  const evidence = useEvidence();
  const [base, setBase] = useState(profile);
  const [draft, setDraft] = useState<ProfileDraft>(() => draftFrom(profile.document));
  const [problems, setProblems] = useState<Partial<Record<ProfileFieldName, FieldProblem>>>({});
  const [stale, setStale] = useState<Stale | null>(null);
  const [saved, setSaved] = useState<number | null>(null);
  const [changes] = useState(() => new ChangeKeys());
  const dirty = JSON.stringify(draft) !== JSON.stringify(draftFrom(base.document));
  const idPrefix = useId();
  const notice = useRef<HTMLDivElement>(null);

  // A refused save moves focus to its notice, which is announced.
  useEffect(() => {
    if (stale !== null) notice.current?.focus();
  }, [stale]);

  // Follow newer versions saved elsewhere while nothing is being edited here (never an older
  // one: after a stale save the form is already on the newer version).
  useEffect(() => {
    if (profile.version > base.version && !dirty) {
      setBase(profile);
      setDraft(draftFrom(profile.document));
    }
  }, [profile, base.version, dirty]);

  const change = (name: ProfileFieldName, next: ProfileDraft[ProfileFieldName]) => {
    setSaved(null);
    setDraft((current) => ({ ...current, [name]: next }));
    setProblems((current) => {
      const { [name]: _dropped, ...rest } = current;
      return rest;
    });
  };

  const submit = async () => {
    const result = inputFrom(draft);
    if (!result.ok) {
      setProblems(result.problems);
      return;
    }
    setProblems({});
    const request = { expected_version: base.version, profile: result.input };
    try {
      const stored = await save.mutateAsync({
        expectedVersion: base.version,
        profile: result.input,
        idempotencyKey: changes.keyFor(request),
      });
      changes.settled();
      setStale(null);
      setBase(stored);
      setDraft(draftFrom(stored.document));
      setSaved(stored.version);
    } catch (error) {
      if (!(error instanceof ApiError && error.code === "STALE_INPUT_VERSION")) return;
      let latest: ProfileOut;
      try {
        // No silent retries here: the person sees at once that it failed and can save again.
        latest = await queries.fetchQuery({
          ...profileQuery(workspaceId),
          staleTime: 0,
          retry: false,
        });
      } catch (loadError) {
        setStale({ kind: "unloaded", error: loadError });
        return;
      }
      const rebased = rebaseDraft(draft, base.document, latest.document);
      setStale({
        kind: "rebased",
        to: latest.version,
        changed: rebased.changedThere,
        conflicts: rebased.conflicts,
        latest: latest.document,
      });
      setBase(latest);
      setDraft(rebased.draft);
    }
  };

  const showSource = (name: ProfileFieldName) =>
    evidence.open({
      title: "Where this came from",
      body: <FieldSource workspaceId={workspaceId} name={name} shown={base.document[name]} />,
    });

  const failure =
    save.error !== null &&
    !(save.error instanceof ApiError && save.error.code === "STALE_INPUT_VERSION");

  return (
    <form
      className="grid max-w-[760px] gap-16"
      noValidate
      aria-labelledby={`${idPrefix}-title`}
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-12">
        <h2 id={`${idPrefix}-title`} className="display text-25">
          What we know
        </h2>
        <p className="small muted tnum">
          {base.version === 0 ? "Nothing saved yet" : `Version ${base.version}`}
          {dirty && ", with unsaved changes"}
        </p>
      </div>
      <p className="small muted measure">
        Each answer keeps where it came from. Saving makes a new version; nothing changes until you
        save. Choose Unknown, Skip or Prefer not to say for anything you don't want to answer.
      </p>

      {stale?.kind === "rebased" && (
        <Alert
          ref={notice}
          tone="stale"
          announce
          title={`Version ${stale.to} was saved while you were editing`}
        >
          <p>
            Your edits are kept below, now based on version {stale.to}.{" "}
            {stale.changed.length > 0
              ? `Version ${stale.to} changed: ${stale.changed
                  .map(
                    (name) =>
                      `${PROFILE_FIELDS[name].label} to ${describeField(stale.latest[name])}`,
                  )
                  .join("; ")}. ${
                  stale.conflicts.length > 0
                    ? `Where you had changed an answer too, your answer is kept and version ${stale.to}'s is shown beside it. `
                    : ""
                }Check them, then save again.`
              : "It changed nothing you are editing. Save again to keep your changes."}
          </p>
        </Alert>
      )}
      {stale?.kind === "unloaded" && (
        <>
          <Alert
            ref={notice}
            tone="stale"
            announce
            title="A newer version was saved, and it couldn't be loaded"
          >
            <p>
              Your edits are kept below. Save again in a moment: Nessa loads the newer version
              first.
            </p>
          </Alert>
          <RequestFailure error={stale.error} announce={false} />
        </>
      )}
      {failure && <RequestFailure error={save.error} />}
      <p role="status" className="small">
        {saved !== null && `Saved as version ${saved}.`}
      </p>

      <div className="card grid gap-0 py-8">
        {PROFILE_FIELD_ORDER.map((name) => {
          const meta = PROFILE_FIELDS[name];
          const field = draft[name];
          const problem = problems[name];
          const errorId = `${idPrefix}-${name}-error`;
          const error = problem === undefined ? undefined : problemText(problem);
          const conflictId = `${idPrefix}-${name}-conflict`;
          const conflict = stale?.kind === "rebased" && stale.conflicts.includes(name);
          const describedBy =
            [error !== undefined && errorId, conflict && conflictId]
              .filter((id) => id !== false)
              .join(" ") || undefined;
          const stored = base.document[name];
          return (
            <section
              key={name}
              className="field first:border-t-0"
              aria-labelledby={`${idPrefix}-${name}`}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-8">
                <h3 id={`${idPrefix}-${name}`} className="field-label">
                  {meta.label}
                </h3>
                {stored.state !== "unasked" && (
                  <button type="button" className="btn btn-quiet" onClick={() => showSource(name)}>
                    Source <span className="sr-only">for {meta.label.toLowerCase()}</span>
                  </button>
                )}
              </div>
              <p className="field-hint">{meta.hint}</p>
              <div className="grid items-start gap-12 sm:grid-cols-[minmax(0,14rem)_minmax(0,1fr)]">
                <FieldStateSelect
                  label={meta.label}
                  draft={field}
                  describedBy={conflict ? conflictId : undefined}
                  onChange={(next) => change(name, next)}
                />
                {field.state === "provided" &&
                  (meta.kind === "list" ? (
                    <ListInput
                      label={meta.label}
                      itemLabel={name === "cities" ? "Work area" : "Target role"}
                      draft={field}
                      error={error}
                      describedBy={describedBy}
                      onChange={(next) => change(name, next)}
                    />
                  ) : (
                    <ValueInput
                      label={meta.label}
                      kind={meta.kind}
                      draft={field}
                      error={error}
                      describedBy={describedBy}
                      onChange={(next) => change(name, next)}
                    />
                  ))}
              </div>
              {field.state !== "provided" && field.state !== "unasked" && (
                <p className="small muted">Less precise without it: {meta.lessPrecise}</p>
              )}
              {stale?.kind === "rebased" && conflict && (
                <p id={conflictId} className="status" data-tone="stale">
                  <Glyph name="stale" />
                  <span>
                    Version {stale.to} has {describeField(stale.latest[name])} here. Saving keeps
                    your answer instead.
                  </span>
                </p>
              )}
              {error !== undefined && <FieldError id={errorId}>{error}</FieldError>}
            </section>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-12">
        <Button
          type="submit"
          variant="primary"
          disabledReason={save.isPending ? "Saving…" : dirty ? undefined : "No changes to save."}
        >
          Save changes
        </Button>
        {dirty && (
          <Button
            variant="secondary"
            onClick={() => {
              setDraft(draftFrom(base.document));
              setProblems({});
              setStale(null);
            }}
          >
            Discard changes
          </Button>
        )}
      </div>
    </form>
  );
}
