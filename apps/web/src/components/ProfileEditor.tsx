"use client";
// "What we know", edited directly (spec section 3). Every answer has a state, so a
// missing value is never a zero. Saving is an expected-version command with an idempotency
// key (Global Constraint 7): a retry of the same change reuses its key, and a version saved
// elsewhere meanwhile is refused (409 STALE_INPUT_VERSION). Then the form moves to the newer
// version: answers the person did not touch take its values (so saving never reverts them),
// their edits stay, and a field both changed shows the newer value beside the edit. Nothing
// is merged silently, and a newer version that cannot be loaded says so. Either notice is
// announced and takes focus, and lists each answer the newer version changed (WCAG 4.1.3).
// The words never say "version" (session 2's plain words, Task W2C fix round 1): the person
// sees their answers and the newer answers, never a number. An entry with a listed risk word
// is saved as usual and the API's calm support panel shows above Save changes, or beside a
// refused save (the product owner's decision, 2026-10-31); like a message's, it stays until
// dismissed or the next save.
import { useQueryClient } from "@tanstack/react-query";
import { type Ref, useEffect, useId, useRef, useState } from "react";
import type { ProfileDocument, ProfileOut, SupportNoteOut } from "@/generated/api";
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
import {
  fieldStates,
  PROFILE_FIELD_ORDER,
  PROFILE_FIELDS,
  type ProfileFieldName,
} from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { FieldSource } from "./FieldSource";
import { AnswerControl, FieldError, FieldStateSelect } from "./fields";
import { Glyph } from "./Glyph";
import { RequestFailure } from "./PageState";
import { SupportNote } from "./SupportNote";

const SUPPORT_SHOWN = "Support information is shown above Save changes.";

type Stale =
  | {
      kind: "rebased";
      changed: ProfileFieldName[];
      conflicts: ProfileFieldName[];
      latest: ProfileDocument;
    }
  | { kind: "unloaded"; error: unknown };

export function ProfileEditor({
  workspaceId,
  profile,
  headingRef,
  openTargets = false,
  onTargetsOpened,
}: {
  workspaceId: string;
  profile: ProfileOut;
  /** Where focus can land when the form is opened from elsewhere, so it is never lost. */
  headingRef?: Ref<HTMLHeadingElement>;
  /** A request ("Name a role") to open the target roles ready to type: a change to the draft
   *  only, saved like any other by the person. Applied once: the form tells the chapter, which
   *  clears it, so a later opening of the form changes nothing (app review I3). */
  openTargets?: boolean;
  onTargetsOpened?(): void;
}) {
  const queries = useQueryClient();
  const save = useSaveProfile(workspaceId);
  const evidence = useEvidence();
  const [base, setBase] = useState(profile);
  const [draft, setDraft] = useState<ProfileDraft>(() => draftFrom(profile.document));
  const [problems, setProblems] = useState<Partial<Record<ProfileFieldName, FieldProblem>>>({});
  const [stale, setStale] = useState<Stale | null>(null);
  const [saved, setSaved] = useState(false);
  // The calm panel the API sent with the last save, saved or refused; never stored.
  const [support, setSupport] = useState<SupportNoteOut | null>(null);
  const [changes] = useState(() => new ChangeKeys());
  const dirty = JSON.stringify(draft) !== JSON.stringify(draftFrom(base.document));
  const idPrefix = useId();
  const notice = useRef<HTMLDivElement>(null);
  const saveButton = useRef<HTMLButtonElement>(null);

  // A refused save moves focus to its notice, which is announced.
  useEffect(() => {
    if (stale !== null) notice.current?.focus();
  }, [stale]);

  // "Name a role": the target roles answered, ready to type, whatever they were, and focus in
  // their first box once it shows.
  const form = useRef<HTMLFormElement>(null);
  const [focusTargets, setFocusTargets] = useState(false);
  useEffect(() => {
    if (!openTargets) return;
    setDraft((current) =>
      current.target_titles.state === "provided"
        ? current
        : { ...current, target_titles: { ...current.target_titles, state: "provided" } },
    );
    setFocusTargets(true);
    onTargetsOpened?.();
  }, [openTargets, onTargetsOpened]);
  useEffect(() => {
    if (!focusTargets) return;
    const box = form.current?.querySelector<HTMLInputElement>("[data-field='target_titles'] input");
    if (box) {
      box.focus();
      setFocusTargets(false);
    }
  });

  // Follow newer versions saved elsewhere while nothing is being edited here (never an older
  // one: after a stale save the form is already on the newer version).
  useEffect(() => {
    if (profile.version > base.version && !dirty) {
      setBase(profile);
      setDraft(draftFrom(profile.document));
    }
  }, [profile, base.version, dirty]);

  const change = (name: ProfileFieldName, next: ProfileDraft[ProfileFieldName]) => {
    setSaved(false);
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
      setSaved(true);
      setSupport(stored.support_note ?? null);
    } catch (error) {
      setSupport(error instanceof ApiError ? error.supportNote : null);
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
      ref={form}
      className="grid max-w-[760px] gap-16"
      noValidate
      aria-labelledby={`${idPrefix}-title`}
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-12">
        <h2 id={`${idPrefix}-title`} className="display text-25" tabIndex={-1} ref={headingRef}>
          Edit your answers
        </h2>
        {dirty && <p className="small muted">Unsaved changes</p>}
      </div>
      <p className="small muted measure">Unknown, Skipped and Prefer not to say are answers too.</p>

      {stale?.kind === "rebased" && (
        <Alert
          ref={notice}
          tone="stale"
          announce
          title="Your answers changed while you were editing"
        >
          <p>
            Your edits are kept below, on top of the newer answers.{" "}
            {stale.changed.length > 0
              ? `The newer answers changed: ${stale.changed
                  .map(
                    (name) =>
                      `${PROFILE_FIELDS[name].label} to ${describeField(stale.latest[name], name)}`,
                  )
                  .join("; ")}. ${
                  stale.conflicts.length > 0
                    ? "Where you had changed an answer too, your answer is kept and the newer one is shown beside it. "
                    : ""
                }Check them, then save again.`
              : "They changed nothing you are editing. Save again to keep your changes."}
          </p>
        </Alert>
      )}
      {stale?.kind === "unloaded" && (
        <>
          <Alert
            ref={notice}
            tone="stale"
            announce
            title="Your answers changed elsewhere, and the newer ones couldn't be loaded"
          >
            <p>
              Your edits are kept below. Save again in a moment: Careerwright loads the newer
              answers first.
            </p>
          </Alert>
          <RequestFailure error={stale.error} announce={false} />
        </>
      )}
      {failure && <RequestFailure error={save.error} />}
      <p role="status" className="small">
        {[saved && "Saved.", support !== null && SUPPORT_SHOWN].filter(Boolean).join(" ")}
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
              data-field={name}
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
                  states={fieldStates(name)}
                  describedBy={conflict ? conflictId : undefined}
                  onChange={(next) => change(name, next)}
                />
                {field.state === "provided" && (
                  <AnswerControl
                    name={name}
                    draft={field}
                    error={error}
                    describedBy={describedBy}
                    onChange={(next) => change(name, next)}
                  />
                )}
              </div>
              {/* "I haven't had a job yet" is a full answer, never a gap (Task 6f). */}
              {field.state !== "provided" &&
                field.state !== "unasked" &&
                field.state !== "no_job_yet" && (
                  <p className="small muted">Less precise without it: {meta.lessPrecise}</p>
                )}
              {stale?.kind === "rebased" && conflict && (
                <p id={conflictId} className="status" data-tone="stale">
                  <Glyph name="stale" />
                  <span>
                    The newer answers have {describeField(stale.latest[name], name)} here. Saving
                    keeps your answer instead.
                  </span>
                </p>
              )}
              {error !== undefined && <FieldError id={errorId}>{error}</FieldError>}
            </section>
          );
        })}
      </div>

      {support !== null && (
        <SupportNote
          note={support}
          onDismiss={() => {
            setSupport(null);
            saveButton.current?.focus(); // the button goes; focus is never lost
          }}
        />
      )}
      {/* Kept in view at the foot of the window while the form is open (session W2, finding 9:
          Save was some 3,400 px down). */}
      <div className="form-save flex flex-wrap items-center gap-12">
        <Button
          ref={saveButton}
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
