"use client";
// Directions to explore (spec section 4, REC-1 and DIV-1; S2.4): a varied slate of career
// hypotheses, each an ESCO occupation found from the person's own answers, with why it could
// suit them, what might not, and a low-cost way to try it. No match percentage, ever. The
// controls change the view only: they are never saved and never become limits. A suggestion
// becomes a target only when the person chooses it.
import { useState } from "react";
import type {
  Direction,
  DiscoveryOut,
  Emphasis,
  NotIncludedOut,
  ProfileOut,
  SlateOut,
  SuggestionOut,
} from "@/generated/api";
import { listLimit } from "@/lib/bounds";
import { type SlateControls, useChooseTarget, useSlate, useSubmitDiscovery } from "@/lib/queries";
import { DIRECTION, EMPHASIS, FAILURE_CLASS, NOT_INCLUDED } from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";

const EVIDENCE = [
  "current_role",
  "target_titles",
  "enjoyed_tasks",
  "confident_tasks",
  "evidenced_tasks",
  "work_style",
] as const;
const ORDER: Direction[] = ["close_to_current", "transferable", "less_familiar"];
const TERMINAL = new Set(["complete", "failed", "provider_unavailable", "cancelled"]);
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

function SuggestionCard({
  suggestion,
  slate,
  targets,
  onChoose,
  onExcludeTitle,
  onExcludeFamily,
  choosing,
}: {
  suggestion: SuggestionOut;
  slate: SlateOut;
  targets: string[];
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
      <div className="grid gap-4">
        <p className="section-title">Why this could suit you</p>
        <ul className="plain-list">
          {suggestion.why_it_could_suit.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
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

function Slate({
  workspaceId,
  profile,
  discovery,
}: {
  workspaceId: string;
  profile: ProfileOut;
  discovery: DiscoveryOut;
}) {
  const [controls, setControls] = useState<SlateControls>(NO_CONTROLS);
  const slate = useSlate(workspaceId, discovery.discovery_id, controls);
  const choose = useChooseTarget(workspaceId);
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
  return (
    <div className="grid gap-16">
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
  const running = discovery !== null && !TERMINAL.has(discovery.run.status);
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
        TERMINAL.has(discovery.run.status) && (
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
        <Slate workspaceId={workspaceId} profile={profile} discovery={discovery} />
      )}
    </section>
  );
}
