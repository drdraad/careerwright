"use client";
// "What we know": the editable profile (spec section 3). Every answer has a state, so a
// missing value is never a zero. Saving is an expected-version command with an idempotency
// key (Global Constraint 7): a retry of the same change reuses its key, and a version saved
// elsewhere meanwhile is refused (409 STALE_INPUT_VERSION). Then the edits are kept, rebased
// on the latest version, and the fields that changed there are named for review: nothing is
// merged silently.
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState } from "react";
import type { ProfileOut, SourceOut } from "@/generated/api";
import { ApiError, newIdempotencyKey } from "@/lib/api";
import {
  changedFields,
  describeField,
  draftFrom,
  type FieldProblem,
  inputFrom,
  type ProfileDraft,
  problemText,
} from "@/lib/profile";
import { keys, useSaveProfile, useSources } from "@/lib/queries";
import { PROFILE_FIELD_ORDER, PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { FieldError, FieldStateSelect, ListInput, ValueInput } from "./fields";
import { RequestFailure } from "./PageState";
import { SourceEvidence } from "./SourceEvidence";

type Stale = { from: number; to: number; changed: ProfileFieldName[] };

export function ProfileEditor({
  workspaceId,
  profile,
}: {
  workspaceId: string;
  profile: ProfileOut;
}) {
  const queries = useQueryClient();
  const save = useSaveProfile(workspaceId);
  const sources = useSources(workspaceId);
  const evidence = useEvidence();
  const [base, setBase] = useState(profile);
  const [draft, setDraft] = useState<ProfileDraft>(() => draftFrom(profile.document));
  const [problems, setProblems] = useState<Partial<Record<ProfileFieldName, FieldProblem>>>({});
  const [stale, setStale] = useState<Stale | null>(null);
  const [saved, setSaved] = useState<number | null>(null);
  const attempt = useRef<{ fingerprint: string; key: string } | null>(null);
  const dirty = JSON.stringify(draft) !== JSON.stringify(draftFrom(base.document));
  const idPrefix = useId();

  // Follow versions saved elsewhere while nothing is being edited here.
  useEffect(() => {
    if (profile.version !== base.version && !dirty) {
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
    const fingerprint = JSON.stringify([base.version, result.input]);
    if (attempt.current?.fingerprint !== fingerprint) {
      attempt.current = { fingerprint, key: newIdempotencyKey() };
    }
    try {
      const stored = await save.mutateAsync({
        expectedVersion: base.version,
        profile: result.input,
        idempotencyKey: attempt.current.key,
      });
      attempt.current = null;
      setStale(null);
      setBase(stored);
      setDraft(draftFrom(stored.document));
      setSaved(stored.version);
    } catch (error) {
      if (error instanceof ApiError && error.code === "STALE_INPUT_VERSION") {
        const latest = await queries.fetchQuery<ProfileOut>({
          queryKey: keys.profile(workspaceId),
          staleTime: 0,
        });
        setStale({
          from: base.version,
          to: latest.version,
          changed: changedFields(base.document, latest.document),
        });
        setBase(latest);
      }
    }
  };

  const showSource = (name: ProfileFieldName) => {
    const field = base.document[name];
    const source: SourceOut | undefined = sources.data?.find(
      (item) => item.source_ref_id === field.source_ref_id,
    );
    evidence.open({
      title: "Where this came from",
      body: (
        <SourceEvidence
          fieldLabel={PROFILE_FIELDS[name].label}
          value={describeField(field)}
          lessPrecise={PROFILE_FIELDS[name].lessPrecise}
          source={source}
          loading={sources.isPending}
          failed={sources.isError}
        />
      ),
    });
  };

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

      {stale !== null && (
        <Alert tone="stale" title={`Version ${stale.to} was saved while you were editing`}>
          <p>
            Your edits are kept below, now based on version {stale.to}.{" "}
            {stale.changed.length > 0
              ? `Version ${stale.to} changed: ${stale.changed.map((name) => PROFILE_FIELDS[name].label).join(", ")}. Check those answers, then save again.`
              : "It changed nothing you are editing. Save again to keep your changes."}
          </p>
        </Alert>
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
                  <button
                    type="button"
                    className="btn btn-quiet"
                    aria-label={`Where ${meta.label.toLowerCase()} came from`}
                    onClick={() => showSource(name)}
                  >
                    Source
                  </button>
                )}
              </div>
              <p className="field-hint">{meta.hint}</p>
              <div className="grid items-start gap-12 sm:grid-cols-[minmax(0,14rem)_minmax(0,1fr)]">
                <FieldStateSelect
                  label={meta.label}
                  draft={field}
                  onChange={(next) => change(name, next)}
                />
                {field.state === "provided" &&
                  (meta.kind === "list" ? (
                    <ListInput
                      label={meta.label}
                      itemLabel={name === "cities" ? "Work area" : "Target role"}
                      draft={field}
                      error={error}
                      errorId={errorId}
                      onChange={(next) => change(name, next)}
                    />
                  ) : (
                    <ValueInput
                      label={meta.label}
                      kind={meta.kind}
                      draft={field}
                      error={error}
                      errorId={errorId}
                      onChange={(next) => change(name, next)}
                    />
                  ))}
              </div>
              {field.state !== "provided" && field.state !== "unasked" && (
                <p className="small muted">Less precise without it: {meta.lessPrecise}</p>
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
