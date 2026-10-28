"use client";
// Directions to explore (spec section 4, REC-1 and DIV-1; S2.4): a varied slate of career
// hypotheses, each an ESCO occupation found from the person's own answers, with why it could
// suit them, what might not, and a low-cost way to try it. No match percentage, ever. The
// controls change the view only: they are never saved and never become limits. A suggestion
// becomes a target only when the person chooses it.
//
// "Why this could suit you" may also carry a written note (S2.7, ADR 0007 decision 12): one
// model run per slate, asked for once when the slate first shows, whose every quotation the
// API checked against the person's answers or ESCO's record. It is shown above how Nessa
// found the suggestion, never instead of it; pending, failed and not-covered states say so.
import { useEffect, useRef, useState } from "react";
import type {
  Direction,
  DiscoveryOut,
  Emphasis,
  NotIncludedOut,
  ProfileOut,
  ProposalOrigin,
  SlateExplanationOut,
  SlateOut,
  SuggestionOut,
  WrittenWhyOut,
} from "@/generated/api";
import { ApiError } from "@/lib/api";
import { listLimit } from "@/lib/bounds";
import { stillRunning } from "@/lib/conversation";
import {
  type SlateControls,
  useChooseTarget,
  useSlate,
  useSubmitDiscovery,
  useSubmitExplanation,
} from "@/lib/queries";
import {
  DIRECTION,
  EMPHASIS,
  ERROR_STATEMENT,
  FAILURE_CLASS,
  NOT_INCLUDED,
  RECORD_PART,
} from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { StatusBadge } from "./Status";

const EVIDENCE = [
  "current_role",
  "target_titles",
  "enjoyed_tasks",
  "confident_tasks",
  "evidenced_tasks",
  "work_style",
] as const;
const ORDER: Direction[] = ["close_to_current", "transferable", "less_familiar"];
const sentence = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const NO_CONTROLS: SlateControls = {
  emphasis: "balanced",
  excludeConcepts: [],
  excludeFamilies: [],
};

function Source({ suggestion, slate }: { suggestion: SuggestionOut; slate: SlateOut }) {
  const queries = slate.queries.filter((q) => suggestion.matched_queries.includes(q.query_id));
  return (
    <div className="grid gap-12">
      <p className="proposal-value">{sentence(suggestion.title)}</p>
      <p className="small">
        ESCO occupation {suggestion.esco_code}, ISCO-08 {suggestion.isco_group.code}{" "}
        {suggestion.isco_group.label}.
      </p>
      <p className="small">
        Source: <span className="break-all">{suggestion.sources[0]?.uri}</span>
      </p>
      <div className="grid gap-4">
        <p className="section-title">Found by these searches</p>
        <ul className="plain-list">
          {queries.map((query) => (
            <li key={query.query_id}>
              “{query.text}”, from {query.based_on.map((item) => `“${item.text}”`).join(", ")}
            </li>
          ))}
        </ul>
      </div>
      <p className="small muted">
        {slate.release.attribution} {slate.release.adaptation}
      </p>
    </div>
  );
}

/** What the slate's written note holds for one suggestion. */
type WrittenState =
  | { kind: "none" } // never asked for (an earlier discovery, changed answers, no key)
  | { kind: "pending" }
  | { kind: "written"; why: WrittenWhyOut; origin: ProposalOrigin }
  | { kind: "not_covered" } // a view showed it that the note was not written for
  | { kind: "unavailable"; reason: string };

const WRITTEN_BY: Record<ProposalOrigin, string> = {
  model:
    "Written by Nessa from your answers and ESCO's record. Each quotation was checked word for word against its source.",
  fixture:
    "Written by the demo explainer (synthetic). Each quotation was checked word for word against its source.",
};

/** The note's state for one suggestion: `asked` while the request is on its way or before
 *  the discovery shows it; `refused` names a request the API turned down. */
function writtenState(
  suggestion: SuggestionOut,
  explanation: SlateExplanationOut | null,
  asked: boolean,
  refused: string | null,
): WrittenState {
  if (explanation === null) {
    if (refused !== null) return { kind: "unavailable", reason: refused };
    return asked ? { kind: "pending" } : { kind: "none" };
  }
  if (stillRunning(explanation.run.status)) return { kind: "pending" };
  if (explanation.written === null) {
    return {
      kind: "unavailable",
      reason: FAILURE_CLASS[explanation.run.failure_class ?? "unknown_failure"].title,
    };
  }
  const why = explanation.written.suggestions.find((s) => s.concept_id === suggestion.concept_id);
  return why === undefined
    ? { kind: "not_covered" }
    : { kind: "written", why, origin: explanation.written.origin };
}

function WrittenNote({ state }: { state: WrittenState }) {
  if (state.kind === "none") return null;
  if (state.kind === "pending") {
    return <StatusBadge state="running" detail="writing a note from your answers and ESCO" />;
  }
  if (state.kind === "unavailable") {
    return (
      <div className="grid gap-4">
        <StatusBadge state="failed" detail="no written note" />
        <p className="small">
          {state.reason}. Nothing from it was kept; how Nessa found this suggestion is below.
        </p>
      </div>
    );
  }
  if (state.kind === "not_covered") {
    return (
      <p className="small muted">
        Nessa wrote notes for your first set of suggestions; this one appeared when you changed the
        view, so it has none. How Nessa found it is below.
      </p>
    );
  }
  return (
    <div className="written-why">
      {state.why.claims.map((claim) => (
        <div key={claim.text} className="grid gap-4">
          <p>{claim.text}</p>
          <ul className="quotations">
            {claim.quotations.map((quotation) => (
              <li key={`${quotation.source}:${quotation.text}`}>
                <span className="quote-source">
                  {quotation.source === "answer"
                    ? "You said"
                    : RECORD_PART[quotation.record_part ?? "description"]}
                  :
                </span>{" "}
                “{quotation.text}”
              </li>
            ))}
          </ul>
        </div>
      ))}
      <p className="small muted">{WRITTEN_BY[state.origin]}</p>
    </div>
  );
}

function SuggestionCard({
  suggestion,
  slate,
  targets,
  written,
  onChoose,
  onExcludeTitle,
  onExcludeFamily,
  choosing,
}: {
  suggestion: SuggestionOut;
  slate: SlateOut;
  targets: string[];
  written: WrittenState;
  onChoose(): void;
  onExcludeTitle(): void;
  onExcludeFamily(): void;
  choosing: boolean;
}) {
  const evidence = useEvidence();
  const title = sentence(suggestion.title);
  const already = targets.some(
    (t) => t.toLocaleLowerCase("en-GB") === suggestion.title.toLocaleLowerCase("en-GB"),
  );
  const full = targets.length >= listLimit("target_titles");
  return (
    <article className="card suggestion" aria-labelledby={`s-${suggestion.concept_id}`}>
      <h4 id={`s-${suggestion.concept_id}`}>{title}</h4>
      <p className="small muted">Kind of work: {suggestion.family.label}</p>
      <p className="small">{suggestion.workday}</p>
      <div className="grid gap-8">
        <p className="section-title">Why this could suit you</p>
        <WrittenNote state={written} />
        <div className="grid gap-4">
          {written.kind !== "none" && <p className="small muted">How Nessa found it</p>}
          <ul className="plain-list">
            {suggestion.why_it_could_suit.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="grid gap-4">
        <p className="section-title">What might not suit you</p>
        <ul className="plain-list">
          {[...suggestion.what_might_not_suit, ...suggestion.entry_gates].map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>
      <div className="grid gap-4">
        <p className="section-title">Try it before committing</p>
        <ul className="plain-list">
          {suggestion.try_it.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>
      <p className="small muted">{suggestion.evidence_gaps.join(" ")}</p>
      <div className="flex flex-wrap items-center gap-8">
        <Button
          variant="secondary"
          onClick={onChoose}
          disabledReason={
            already
              ? "Already one of your targets."
              : full
                ? `You have ${listLimit("target_titles")} targets: remove one first.`
                : choosing
                  ? "Saving…"
                  : undefined
          }
        >
          Make this a target <span className="sr-only">: {title}</span>
        </Button>
        <Button variant="quiet" onClick={onExcludeTitle}>
          Not for me <span className="sr-only">: {title}</span>
        </Button>
        <Button variant="quiet" onClick={onExcludeFamily}>
          Exclude this kind of work <span className="sr-only">: {suggestion.family.label}</span>
        </Button>
        <Button
          variant="quiet"
          onClick={() =>
            evidence.open({
              title: "Where this came from",
              body: <Source suggestion={suggestion} slate={slate} />,
            })
          }
        >
          Source <span className="sr-only">for {title}</span>
        </Button>
      </div>
    </article>
  );
}

function NotShown({ items }: { items: NotIncludedOut[] }) {
  if (items.length === 0) return null;
  return (
    <details className="details">
      <summary>Show why something wasn't included ({items.length})</summary>
      <ul className="plain-list mt-8">
        {items.map((item) => (
          <li key={item.concept_id}>
            {sentence(item.title)}: {NOT_INCLUDED[item.reason]}
            {item.duplicate_of_title ? ` (${sentence(item.duplicate_of_title)})` : ""}
          </li>
        ))}
      </ul>
    </details>
  );
}

/** Why a request for the written note was refused, in the error code's words. */
function refusal(error: unknown): string | null {
  if (error === null) return null;
  return error instanceof ApiError && error.body !== null
    ? ERROR_STATEMENT[error.body.code].title
    : "Nessa's service isn't reachable";
}

const NOTE_ANNOUNCEMENT: Record<WrittenState["kind"], string> = {
  none: "",
  pending: "Nessa is writing a note on why each suggestion could suit you.",
  written: "Nessa's written notes are shown beside the suggestions.",
  not_covered: "Nessa's written notes are shown beside the suggestions.",
  unavailable: "Nessa's written notes aren't available. How each suggestion was found is shown.",
};

function Slate({
  workspaceId,
  profile,
  discovery,
  canWrite,
}: {
  workspaceId: string;
  profile: ProfileOut;
  discovery: DiscoveryOut;
  /** Whether a written note may be asked for (a key is stored, or the workspace is a demo). */
  canWrite: boolean;
}) {
  const [controls, setControls] = useState<SlateControls>(NO_CONTROLS);
  const slate = useSlate(workspaceId, discovery.discovery_id, controls);
  const choose = useChooseTarget(workspaceId);
  const explain = useSubmitExplanation(workspaceId);
  const explanation = discovery.explanation ?? null;
  const asked = useRef<string | null>(null);
  const shown = slate.data !== undefined && slate.data.suggestions.length > 0;
  // One request per slate, when it first shows for the current answers: a view change, a
  // remount or a refresh never asks again (and the API answers a repeat with the same run).
  const wanted =
    canWrite && shown && explanation === null && discovery.profile_version === profile.version;
  const askForNote = explain.mutate;
  useEffect(() => {
    if (!wanted || asked.current === discovery.discovery_id) return;
    asked.current = discovery.discovery_id;
    askForNote({
      discoveryId: discovery.discovery_id,
      body: { expected_profile_version: profile.version },
    });
  }, [wanted, discovery.discovery_id, profile.version, askForNote]);
  const requested = asked.current === discovery.discovery_id;
  const refused = requested ? refusal(explain.error) : null;
  const noteFor = (suggestion: SuggestionOut) =>
    writtenState(suggestion, explanation, requested, refused);
  const targets =
    profile.document.target_titles.state === "provided"
      ? (profile.document.target_titles.value ?? [])
      : [];
  if (slate.data === undefined) {
    return slate.error ? (
      <RequestFailure
        error={slate.error}
        actions={
          <Button variant="secondary" onClick={() => void slate.refetch()}>
            Try again
          </Button>
        }
      />
    ) : (
      <LoadingState stage="Ranking the occupations ESCO returned" lines={2} />
    );
  }
  const data = slate.data;
  const familiarityKnown = profile.document.current_role.state === "provided" || targets.length > 0;
  const excluded = controls.excludeConcepts.length + controls.excludeFamilies.length;
  const first = data.suggestions[0];
  const note = first === undefined ? "none" : noteFor(first).kind;
  return (
    <div className="grid gap-16">
      <p className="sr-only" role="status">
        {NOTE_ANNOUNCEMENT[note]}
      </p>
      <fieldset className="segmented">
        <legend className="sr-only">Which directions to show</legend>
        {(Object.keys(EMPHASIS) as Emphasis[]).map((emphasis) => (
          <Button
            key={emphasis}
            variant="secondary"
            aria-pressed={controls.emphasis === emphasis}
            onClick={() => setControls((current) => ({ ...current, emphasis }))}
          >
            {EMPHASIS[emphasis]}
          </Button>
        ))}
      </fieldset>
      <p className="small muted">
        {data.suggestions.length} of up to {data.target_size}, from {data.pool_size} occupations
        found by {data.queries.length} searches of ESCO{data.release.sample ? " (test sample)" : ""}
        .
        {data.beyond_pool_limit > 0 &&
          ` ${data.beyond_pool_limit} more were found than the pool holds.`}
        {excluded > 0 &&
          ` Your exclusions removed ${data.excluded.occupations + data.excluded.families}.`}
      </p>
      {[...data.fewer_reasons, ...data.notes, ...data.limits_not_applied].map((line) => (
        <p key={line} className="small">
          {line}
        </p>
      ))}
      {excluded > 0 && (
        <div>
          <Button
            variant="quiet"
            onClick={() =>
              setControls((current) => ({ ...current, excludeConcepts: [], excludeFamilies: [] }))
            }
          >
            Clear exclusions
          </Button>
        </div>
      )}
      {!familiarityKnown && (
        <p className="small muted">
          Nessa doesn't know your current work yet, so it can't say which directions are close to
          it.
        </p>
      )}
      {ORDER.map((direction) => {
        const group = data.suggestions.filter((s) => s.direction === direction);
        if (group.length === 0) return null;
        return (
          <section key={direction} className="suggestions" aria-labelledby={`dir-${direction}`}>
            <h3 id={`dir-${direction}`} className="section-title">
              {direction === "less_familiar" && !familiarityKnown
                ? "Directions to consider"
                : DIRECTION[direction]}
            </h3>
            {group.map((suggestion) => (
              <SuggestionCard
                key={suggestion.concept_id}
                suggestion={suggestion}
                slate={data}
                targets={targets}
                written={noteFor(suggestion)}
                choosing={choose.isPending}
                onChoose={() =>
                  choose.mutate({
                    expected_version: profile.version,
                    concept_id: suggestion.concept_id,
                    discovery_id: discovery.discovery_id,
                  })
                }
                onExcludeTitle={() =>
                  setControls((current) => ({
                    ...current,
                    excludeConcepts: [...current.excludeConcepts, suggestion.concept_id],
                  }))
                }
                onExcludeFamily={() =>
                  setControls((current) => ({
                    ...current,
                    excludeFamilies: [...current.excludeFamilies, suggestion.family.code],
                  }))
                }
              />
            ))}
          </section>
        );
      })}
      {choose.error !== null && <RequestFailure error={choose.error} />}
      {data.unsupported_hypotheses.length > 0 && (
        <p className="small muted">
          Titles Nessa thought of that ESCO doesn't list, so not suggested:{" "}
          {data.unsupported_hypotheses.join(", ")}.
        </p>
      )}
      <NotShown items={data.not_included} />
      <p className="small muted">{data.release.attribution}</p>
    </div>
  );
}

export function Directions({
  workspaceId,
  profile,
  discovery,
  unavailable,
}: {
  workspaceId: string;
  profile: ProfileOut;
  discovery: DiscoveryOut | null;
  /** Why discovery can't run yet (no key stored), if it can't. */
  unavailable?: string;
}) {
  const submit = useSubmitDiscovery(workspaceId);
  const hasEvidence = EVIDENCE.some((name) => profile.document[name].state === "provided");
  const start = () => submit.mutate({ expected_profile_version: profile.version });
  const blocked =
    unavailable ??
    (!hasEvidence
      ? "Tell Nessa what you do now, what you enjoy or what you can do first."
      : submit.isPending
        ? "Starting…"
        : undefined);
  const running = discovery !== null && stillRunning(discovery.run.status);
  const stale = discovery !== null && discovery.profile_version < profile.version;

  return (
    <section className="grid gap-16" aria-labelledby="directions-title">
      <h2 id="directions-title" className="display text-25">
        Directions to explore
      </h2>
      <p className="small muted measure">
        Up to six occupations from ESCO, found from your own answers and chosen to differ from each
        other. They are ideas to test, not a judgement of fit: no score or percentage.
      </p>
      {discovery === null || (stale && !running) ? (
        <>
          {stale && (
            <Alert
              tone="stale"
              title={`Based on your answers at version ${discovery?.profile_version}`}
            >
              <p>Your answers have changed since. Suggest again to use the latest ones.</p>
            </Alert>
          )}
          <div>
            <Button variant="secondary" onClick={start} disabledReason={blocked}>
              {discovery === null ? "Suggest directions" : "Suggest again"}
            </Button>
          </div>
        </>
      ) : null}
      {running && (
        <LoadingState stage="Searching ESCO for occupations that fit your answers" lines={2} />
      )}
      {discovery !== null &&
        discovery.run.status !== "complete" &&
        !stillRunning(discovery.run.status) && (
          <Alert
            tone={discovery.run.status === "provider_unavailable" ? "stale" : "error"}
            title={FAILURE_CLASS[discovery.run.failure_class ?? "unknown_failure"].title}
            actions={
              <Button variant="secondary" onClick={start} disabledReason={blocked}>
                Try again
              </Button>
            }
          >
            <p>{FAILURE_CLASS[discovery.run.failure_class ?? "unknown_failure"].action}</p>
          </Alert>
        )}
      {submit.error !== null && <RequestFailure error={submit.error} />}
      {discovery !== null && discovery.run.status === "complete" && (
        <Slate
          workspaceId={workspaceId}
          profile={profile}
          discovery={discovery}
          canWrite={unavailable === undefined}
        />
      )}
    </section>
  );
}
