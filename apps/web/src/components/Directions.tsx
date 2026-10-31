"use client";
// Directions to explore (spec section 4, REC-1 and DIV-1; S2.4): a varied slate of career
// hypotheses, each an ESCO occupation found from the person's own answers, with why it could
// suit them, what might not, and a low-cost way to try it. No match percentage, ever. The
// controls change the view only: they are never saved and never become limits. A suggestion
// becomes a target only when the person chooses it. One suggestion is open at a time (session
// 2: "minimum ideas per page"), the rest a list of titles to scan, and the open one's "Make
// this a target" is the view's one bright primary action ("I found the button, but it did
// not stand out enough. Needs to be a bright colour"), as asking for suggestions is before
// there are any.
//
// "Why this could suit you" may also carry a written note (S2.7, ADR 0007 decision 12): one
// model run per slate, asked for once when the person first sees the slate (the page keeps
// every request, so a view or chapter change never asks again), whose every quotation the
// API checked against the person's answers or ESCO's record. It is shown above how Careerwright
// found the suggestion, never instead of it; pending, failed and not-covered states say so.
//
// Never overwhelming (session 2): the slate's notes on how it searched wait in one disclosure
// under the count line, and the open suggestion's choice comes right after its title.
import { type Ref, useEffect, useId, useRef, useState } from "react";
import type {
  ConnectionOut,
  Direction,
  DiscoveryOut,
  Emphasis,
  ErrorCode,
  NotIncludedOut,
  ProfileOut,
  ProposalOrigin,
  SharedSkillOut,
  SlateExplanationOut,
  SlateOut,
  SuggestionOut,
  TargetRecordOut,
  WrittenWhyOut,
} from "@/generated/api";
import { ApiError } from "@/lib/api";
import { listLimit } from "@/lib/bounds";
import { stillRunning } from "@/lib/conversation";
import {
  type SlateControls,
  useChooseTarget,
  useNoteRequests,
  useSketch,
  useSlate,
  useSubmitDiscovery,
  useTargets,
} from "@/lib/queries";
import {
  ADDED_WEIGHT_ONLY,
  ANSWER_SOURCE,
  aiFilterWords,
  DIRECTION,
  EMPHASIS,
  ERROR_STATEMENT,
  FAILURE_CLASS,
  fewerReason,
  floorWords,
  NOT_INCLUDED,
  NOTE_CARD,
  NOTE_RECOVERY,
  NOTE_REFUSAL_CODE,
  NOTE_REFUSAL_REASON,
  type NoteRefusalWords,
  RECORD_PART,
  SUGGESTION_WORDS,
  slateNote,
  suggestionReason,
  suggestionWords,
  titleIdeasListed,
  titleIdeasWords,
  UK_TITLE_IDEAS,
} from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { useEvidence } from "./EvidenceDrawer";
import { Glyph } from "./Glyph";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { TargetCoverageLine, TargetRequirements } from "./SketchCard";
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
              {query.too_general && ` (${ADDED_WEIGHT_ONLY})`}
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

/** What the person can do about a missing note: try the note again (its run reached no
 *  model), send a refused request again, suggest again (the slate had its one call, or it
 *  is no longer the current one), or change the answers first (a refusal asking again would
 *  only repeat). */
type Recovery = "retry" | "resend" | "suggest_again" | "edit_answers";

/** What the slate's written note holds for one suggestion. */
type WrittenState =
  | { kind: "none" } // never asked for (an earlier discovery, changed answers, no key)
  | { kind: "pending" }
  | { kind: "written"; why: WrittenWhyOut; origin: ProposalOrigin }
  | { kind: "not_covered" } // a view showed it that the note was not written for
  | {
      kind: "unavailable";
      reason: string;
      action: string;
      recovery: Recovery;
      /** Whether a run existed (it failed) or the request was refused before any run. */
      ran: boolean;
    };

/** A request for the note that the API refused, in its error code's words; `recovery` is
 *  set when asking again could only repeat the refusal. */
type Refusal = {
  title: string;
  action: string;
  code: ErrorCode | null;
  recovery?: NoteRefusalWords["recovery"];
};

// Only the quoted words are checked against a source; the sentences are the writer's own.
const WRITTEN_BY: Record<ProposalOrigin, string> = {
  model:
    "Written by Careerwright from your answers and ESCO's record. Only the quoted words were checked against them; the sentences are Careerwright's own.",
  fixture:
    "Written by the demo explainer (synthetic). Only the quoted words were checked against your answers and ESCO's record; the sentences are the explainer's own.",
};

/** The note's state for one suggestion: `asked` once the slate asked for it, `sending` while
 *  a request is on its way, and `refused` the last request the API turned down. */
function writtenState(
  suggestion: SuggestionOut,
  explanation: SlateExplanationOut | null,
  { asked, sending, refused }: { asked: boolean; sending: boolean; refused: Refusal | null },
): WrittenState {
  if (sending || (explanation !== null && stillRunning(explanation.run.status))) {
    return { kind: "pending" };
  }
  if (explanation?.written) {
    const why = explanation.written.suggestions.find((s) => s.concept_id === suggestion.concept_id);
    return why === undefined
      ? { kind: "not_covered" }
      : { kind: "written", why, origin: explanation.written.origin };
  }
  if (refused !== null) {
    const recovery: Recovery =
      refused.recovery ??
      (explanation === null ? "resend" : explanation.can_retry ? "retry" : "suggest_again");
    return {
      kind: "unavailable",
      reason: refused.title,
      action: refused.action,
      recovery,
      ran: explanation !== null, // a refused Try again follows a run that failed
    };
  }
  if (explanation === null) return asked ? { kind: "pending" } : { kind: "none" };
  const failure = FAILURE_CLASS[explanation.run.failure_class ?? "unknown_failure"];
  // Once a request was sent, the failure's own advice (which may say "try again") would
  // mislead: the slate has had its call.
  return explanation.can_retry
    ? {
        kind: "unavailable",
        reason: failure.title,
        action: failure.action,
        recovery: "retry",
        ran: true,
      }
    : {
        kind: "unavailable",
        reason: failure.title,
        action: NOTE_RECOVERY.spent,
        recovery: "suggest_again",
        ran: true,
      };
}

function WrittenNote({ state }: { state: WrittenState }) {
  if (state.kind === "none") return null;
  if (state.kind === "pending") {
    return <StatusBadge state="running" detail="writing a note from your answers and ESCO" />;
  }
  if (state.kind === "unavailable") {
    const words = state.ran ? NOTE_CARD.failed : NOTE_CARD.refused;
    return (
      <div className="grid gap-4">
        <StatusBadge state={state.ran ? "failed" : "notStarted"} detail={words.detail} />
        <p className="small">
          {state.reason}. {words.after}
        </p>
      </div>
    );
  }
  if (state.kind === "not_covered") {
    return (
      <p className="small muted">
        Careerwright wrote notes for your first set of suggestions; this one appeared when you
        changed the view, so it has none.
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

/** How many of the skills a suggestion was joined by are named on its card; the rest are one
 *  step away (the audit's F4). */
const FIRST_SKILLS = 3;

const listed = (items: string[]) =>
  items.length < 2 ? items.join("") : `${items.slice(0, -1).join(", ")} and ${items.at(-1)}`;

/** The skills a suggestion was joined by, under the reason that says how it was joined (the
 *  API's, which quotes the person's own words): the first few named, the rest one step away.
 *  The join is said once, by that reason (D-I2). On the slate's unexpected connection, what
 *  Careerwright hasn't checked yet is said with them; its light in the world is Task M's. */
function JoinedBy({ skills, connection }: { skills: SharedSkillOut[]; connection: boolean }) {
  if (skills.length === 0) return null;
  const rest = skills.slice(FIRST_SKILLS);
  const first = listed(skills.slice(0, FIRST_SKILLS).map((s) => s.label));
  return (
    <div className="grid gap-4">
      <p className="small">
        {SUGGESTION_WORDS.skillsNamed(first, rest.length > 0)}
        {connection && ` ${SUGGESTION_WORDS.notCompared}`}
      </p>
      {rest.length > 0 && (
        <details className="details">
          <summary>{SUGGESTION_WORDS.otherSkills(rest.length)}</summary>
          <ul className="plain-list mt-8">
            {rest.map((skill) => (
              <li key={skill.skill_id}>{skill.label}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

/** A suggestion that is one of the person's targets: said where it was chosen, with how far
 *  Careerwright can cover it and what it usually asks for (STATE-10; PROF-10). */
function TargetSaved({
  workspaceId,
  conceptId,
  headingRef,
}: {
  workspaceId: string;
  conceptId: string;
  headingRef: Ref<HTMLHeadingElement>;
}) {
  const sketch = useSketch(workspaceId);
  const headingId = useId();
  const target = sketch.data?.targets.find(
    (t) => t.resolution === "esco" && t.occupations[0]?.concept_id === conceptId,
  );
  return (
    <section className="target-saved grid gap-8" aria-labelledby={headingId}>
      <h5 id={headingId} className="status font-semibold" tabIndex={-1} ref={headingRef}>
        <Glyph name="accept" />
        <span>{SUGGESTION_WORDS.chosen}</span>
      </h5>
      {sketch.data === undefined ? (
        sketch.error ? (
          <RequestFailure
            error={sketch.error}
            actions={
              <Button variant="secondary" onClick={() => void sketch.refetch()}>
                Try again
              </Button>
            }
          />
        ) : (
          <LoadingState stage="Loading what this work usually asks for" lines={1} />
        )
      ) : (
        target !== undefined && (
          <>
            <TargetCoverageLine target={target} />
            <TargetRequirements target={target} />
          </>
        )
      )}
    </section>
  );
}

function SuggestionCard({
  workspaceId,
  suggestion,
  slate,
  targets,
  written,
  open,
  primary,
  connection,
  focusSaved,
  onSavedFocused,
  onOpen,
  onChoose,
  onExcludeTitle,
  onExcludeFamily,
  choosing,
}: {
  workspaceId: string;
  suggestion: SuggestionOut;
  slate: SlateOut;
  /** The person's targets as stored once, each with the occupation it names. */
  targets: TargetRecordOut[];
  written: WrittenState;
  /** Shown in full, with its actions; the others show their title and kind of work. */
  open: boolean;
  /** Whether "Make this a target" is the view's one bright primary action. */
  primary: boolean;
  /** The slate's unexpected connection, when this suggestion is it. */
  connection: ConnectionOut | null;
  /** Just chosen as a target: focus goes to the words that say it is saved. */
  focusSaved: boolean;
  onSavedFocused(): void;
  onOpen(): void;
  onChoose(): void;
  onExcludeTitle(): void;
  onExcludeFamily(): void;
  choosing: boolean;
}) {
  const evidence = useEvidence();
  const title = sentence(suggestion.title);
  // A target names this occupation by its stored record, never by comparing titles.
  const already = targets.some((t) => t.concept_id === suggestion.concept_id);
  const full = targets.length >= listLimit("target_titles");
  const words = suggestionWords(suggestion);
  const body = useId();
  const saved = useRef<HTMLHeadingElement>(null);
  // The choice is replaced by the words that say it is saved; focus follows once they show.
  useEffect(() => {
    if (focusSaved && saved.current !== null) {
      saved.current.focus();
      onSavedFocused();
    }
  });
  return (
    <article
      className="card suggestion"
      data-open={open}
      aria-labelledby={`s-${suggestion.concept_id}`}
    >
      {connection !== null && <p className="suggestion-kicker">{SUGGESTION_WORDS.connection}</p>}
      <h4 id={`s-${suggestion.concept_id}`}>
        <button
          type="button"
          className="suggestion-toggle"
          aria-expanded={open}
          // Only an open suggestion's details are in the page.
          aria-controls={open ? body : undefined}
          // One is always open, so the open one's header can't close it (the ARIA accordion
          // pattern): it says so rather than doing nothing.
          aria-disabled={open || undefined}
          onClick={open ? undefined : onOpen}
        >
          {title}
          <Glyph name={open ? "expand" : "collapse"} />
        </button>
      </h4>
      <p className="small muted">Kind of work: {suggestion.family.label}</p>
      {open && (
        <div id={body} className="grid gap-12">
          {/* The choice first, so its bright action is in view with a real slate; what the
              work is and why it could suit you follow (D-I3). Once chosen, the choice gives
              way to the words that say so, with what the work usually asks for (STATE-10). */}
          {already && (
            <TargetSaved
              workspaceId={workspaceId}
              conceptId={suggestion.concept_id}
              headingRef={saved}
            />
          )}
          <div className="flex flex-wrap items-center gap-8">
            {!already && (
              <Button
                variant={primary ? "primary" : "secondary"}
                onClick={onChoose}
                disabledReason={
                  full
                    ? `You have ${listLimit("target_titles")} targets: remove one first.`
                    : choosing
                      ? "Saving…"
                      : undefined
                }
              >
                Make this a target <span className="sr-only">: {title}</span>
              </Button>
            )}
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
          <p className="small">{suggestion.workday}</p>
          <div className="grid gap-8">
            <p className="section-title">Why this could suit you</p>
            <WrittenNote state={written} />
            <div className="grid gap-4">
              {written.kind !== "none" && <p className="small muted">How Careerwright found it</p>}
              <ul className="plain-list">
                {suggestion.reasons.map(suggestionReason).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <JoinedBy skills={suggestion.shared_skills} connection={connection !== null} />
            </div>
          </div>
          <div className="grid gap-4">
            <p className="section-title">What might not suit you</p>
            <ul className="plain-list">
              {[...words.mightNot, words.entryGate].map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
          <div className="grid gap-4">
            <p className="section-title">Try it before committing</p>
            <ul className="plain-list">
              {words.tryIt.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
          <p className="small muted">{words.evidenceGap}</p>
        </div>
      )}
    </article>
  );
}

/** The slate's notes on how it searched, one step away (session 2's "never overwhelming"):
 *  each keeps its words, none is dropped, and the count says how many wait inside. */
function SearchNotes({ lines }: { lines: string[] }) {
  if (lines.length === 0) return null;
  return (
    <details className="details">
      <summary>
        How Careerwright searched ({lines.length} {lines.length === 1 ? "note" : "notes"})
      </summary>
      <ul className="plain-list mt-8">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </details>
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
function refusal(error: unknown): Refusal | null {
  if (error === null) return null;
  if (error instanceof ApiError && error.body !== null) {
    const { code, details } = error.body;
    const reason = details?.reason;
    // A refusal that asking again would only repeat gets its own words and what can work.
    const fixed =
      typeof reason === "string" && Object.hasOwn(NOTE_REFUSAL_REASON, reason)
        ? NOTE_REFUSAL_REASON[reason as keyof typeof NOTE_REFUSAL_REASON]
        : NOTE_REFUSAL_CODE[code];
    if (fixed !== undefined) return { ...fixed, code };
    const words = ERROR_STATEMENT[code];
    return { title: words.title, action: words.action, code };
  }
  return {
    title: "Careerwright's service isn't reachable",
    action: "Nothing you saved is lost. Try again in a moment.",
    code: null,
  };
}

/** Once, above the cards: why the note is missing and the one thing to do about it. */
function NoteRecovery({
  state,
  onTryAgain,
  onSuggestAgain,
  tryBlocked,
  suggestBlocked,
}: {
  state: Extract<WrittenState, { kind: "unavailable" }>;
  onTryAgain(): void;
  onSuggestAgain(): void;
  tryBlocked?: string | undefined;
  suggestBlocked?: string | undefined;
}) {
  const { recovery } = state;
  // Changing the answers is done in "What we know"; the chapter then offers Suggest again,
  // so no button here could work yet.
  const action =
    recovery === "edit_answers" ? undefined : recovery === "suggest_again" ? (
      <Button variant="secondary" onClick={onSuggestAgain} disabledReason={suggestBlocked}>
        Suggest again
      </Button>
    ) : (
      <Button variant="secondary" onClick={onTryAgain} disabledReason={tryBlocked}>
        Try again <span className="sr-only">: the written note</span>
      </Button>
    );
  return (
    <Alert
      tone="error"
      announce={false}
      title={`No written note: ${state.reason}`}
      actions={action}
    >
      <p>{state.action}</p>
      <p>
        {recovery === "suggest_again"
          ? NOTE_RECOVERY.suggestAgain
          : recovery === "retry"
            ? NOTE_RECOVERY.retry
            : NOTE_RECOVERY.resend}
      </p>
    </Alert>
  );
}

const NOTE_ANNOUNCEMENT: Record<WrittenState["kind"], string> = {
  none: "",
  pending: "Careerwright is writing a note on why each suggestion could suit you.",
  written: "Careerwright's written notes are shown beside the suggestions.",
  not_covered: "Careerwright's written notes are shown beside the suggestions.",
  unavailable:
    "Careerwright's written notes aren't available. How each suggestion was found is shown.",
};

function Slate({
  workspaceId,
  profile,
  discovery,
  canWrite,
  shown,
  choosePrimary,
  onSuggestAgain,
  suggestBlocked,
}: {
  workspaceId: string;
  profile: ProfileOut;
  discovery: DiscoveryOut;
  /** Whether a written note may be asked for (a key is stored, or the workspace is a demo). */
  canWrite: boolean;
  /** Whether the person can see the slate (its view is the one open). */
  shown: boolean;
  /** Whether choosing the open suggestion is the view's one primary action (not while
   *  "Suggest again" is, for changed answers). */
  choosePrimary: boolean;
  /** A new discovery: a new set of suggestions, with a note of its own. */
  onSuggestAgain(): void;
  suggestBlocked?: string | undefined;
}) {
  const [controls, setControls] = useState<SlateControls>(NO_CONTROLS);
  // The suggestion shown in full; by default the first one listed.
  const [opened, setOpened] = useState<string | null>(null);
  // The suggestion just made a target: focus goes to the words that say it is saved.
  const [chosen, setChosen] = useState<string | null>(null);
  const slate = useSlate(workspaceId, discovery.discovery_id, controls);
  const targetRecords = useTargets(workspaceId);
  const choose = useChooseTarget(workspaceId);
  const notes = useNoteRequests(workspaceId, discovery.discovery_id);
  const explanation = discovery.explanation ?? null;
  const suggested = slate.data !== undefined && slate.data.suggestions.length > 0;
  // One request per slate, when the person first sees it for the current answers: a view
  // change, a change of chapter or a refresh never asks again here (the page keeps every
  // request), and the API answers any repeat with the same run.
  const wanted = canWrite && shown && suggested && explanation === null && discovery.current;
  const { askOnce } = notes;
  useEffect(() => {
    if (wanted) askOnce({ expected_profile_version: profile.version });
  }, [wanted, profile.version, askOnce]);
  const flags = { asked: notes.asked, sending: notes.sending, refused: refusal(notes.error) };
  const noteFor = (suggestion: SuggestionOut) => writtenState(suggestion, explanation, flags);
  // Only ever by the person's click: a retry of a run that reached no model, or a refused
  // request sent again (never automatic).
  const tryAgain = (retry: boolean) =>
    notes.askAgain({
      expected_profile_version: profile.version,
      ...(retry ? { retry_failed: true } : {}),
    });
  const targets = targetRecords.data?.targets ?? [];
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
  const named = profile.document.target_titles;
  const familiarityKnown =
    profile.document.current_role.state === "provided" ||
    (named.state === "provided" && (named.value ?? []).length > 0);
  const excluded = controls.excludeConcepts.length + controls.excludeFamilies.length;
  // Only a search that reached work found the pool: one too general to find work on its own
  // only added weight, and one that reached nothing found none.
  const finding = data.queries.filter((query) => !query.too_general && query.reach > 0).length;
  const first = data.suggestions[0];
  const note: WrittenState = first === undefined ? { kind: "none" } : noteFor(first);
  // As listed: grouped by direction. The open one, or the first listed once it is not shown.
  const listed = ORDER.flatMap((direction) =>
    data.suggestions.filter((s) => s.direction === direction),
  );
  const open = listed.some((s) => s.concept_id === opened) ? opened : listed[0]?.concept_id;
  return (
    <div className="grid gap-16">
      <p className="sr-only" role="status">
        {NOTE_ANNOUNCEMENT[note.kind]}
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
        found by {finding} {finding === 1 ? "search" : "searches"} of ESCO
        {data.release.sample ? " (test sample)" : ""}.
        {data.beyond_pool_limit > 0 && ` ${data.beyond_pool_limit} more were found but not kept.`}
        {excluded > 0 &&
          ` Your exclusions removed ${data.excluded.occupations + data.excluded.families}.`}
      </p>
      <SearchNotes
        lines={[
          ...data.fewer_reasons.map(fewerReason),
          ...data.notes.map(slateNote),
          ...(data.salary_floor ? [floorWords(data.salary_floor)] : []),
          ...[aiFilterWords(data.ai_resilience_filter), titleIdeasWords(data.title_ideas)].filter(
            (line): line is string => line !== null,
          ),
          ...(familiarityKnown
            ? []
            : [
                "Careerwright doesn't know your current work yet, so it can't say which " +
                  "directions are close to it.",
              ]),
        ]}
      />
      {note.kind === "unavailable" && (
        <NoteRecovery
          state={note}
          onTryAgain={() => tryAgain(note.recovery === "retry")}
          onSuggestAgain={onSuggestAgain}
          tryBlocked={canWrite ? undefined : "Store a Meta API key first."}
          suggestBlocked={suggestBlocked}
        />
      )}
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
                workspaceId={workspaceId}
                suggestion={suggestion}
                slate={data}
                targets={targets}
                written={noteFor(suggestion)}
                open={suggestion.concept_id === open}
                primary={choosePrimary}
                connection={
                  data.connection?.concept_id === suggestion.concept_id ? data.connection : null
                }
                focusSaved={chosen === suggestion.concept_id}
                onSavedFocused={() => setChosen(null)}
                onOpen={() => setOpened(suggestion.concept_id)}
                choosing={choose.isPending}
                onChoose={() =>
                  choose.mutate(
                    {
                      expected_version: profile.version,
                      concept_id: suggestion.concept_id,
                      discovery_id: discovery.discovery_id,
                    },
                    { onSuccess: () => setChosen(suggestion.concept_id) },
                  )
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
      <UkTitleIdeas ideas={titleIdeasListed(data.title_ideas)} />
      <NotShown items={data.not_included} />
      <p className="small muted">{data.release.attribution}</p>
    </div>
  );
}

/** Title ideas the UK job-title index lists (Task 6d slice B; ADR 0015 decision 2): each a
 *  suggestion in its own short list beside the slate, never in it, with the answers it came
 *  from. Nothing about it is compared with the person's experience yet. */
function UkTitleIdeas({ ideas }: { ideas: SlateOut["title_ideas"] }) {
  if (ideas.length === 0) return null;
  return (
    <section className="suggestions" aria-labelledby="uk-title-ideas">
      <h3 id="uk-title-ideas" className="section-title">
        {UK_TITLE_IDEAS.heading}
      </h3>
      {ideas.map((idea) => (
        <article key={idea.title} className="suggestion grid gap-8">
          <h4 className="font-semibold">{idea.title}</h4>
          <p className="small">{UK_TITLE_IDEAS.found}</p>
          <ul className="plain-list small">
            {idea.based_on.map((answer) => (
              <li key={`${answer.field}:${answer.text}`}>
                {UK_TITLE_IDEAS.from} {ANSWER_SOURCE[answer.field].toLowerCase()}: “{answer.text}”
              </li>
            ))}
          </ul>
        </article>
      ))}
    </section>
  );
}

/**
 * Whether a new set of suggestions is wanted (none yet, one that failed, or one made from
 * earlier answers and not running) and why one can't start now, if it can't. "Show me
 * suggestions" in the conversation and this view's own button follow the same rule.
 */
export function suggestionStart(
  profile: ProfileOut,
  discovery: DiscoveryOut | null,
  unavailable: string | undefined,
  starting: boolean,
): { wanted: boolean; blocked: string | undefined } {
  const hasEvidence = EVIDENCE.some((name) => profile.document[name].state === "provided");
  const blocked =
    unavailable ??
    (!hasEvidence
      ? "Tell Careerwright what you do now, what you enjoy or what you can do first."
      : starting
        ? "Starting…"
        : undefined);
  const wanted =
    discovery === null ||
    (!stillRunning(discovery.run.status) &&
      (!discovery.current || discovery.run.status !== "complete"));
  return { wanted, blocked };
}

export function Directions({
  workspaceId,
  profile,
  discovery,
  unavailable,
  shown = true,
  submit: shared,
  headingRef,
}: {
  workspaceId: string;
  profile: ProfileOut;
  discovery: DiscoveryOut | null;
  /** Why discovery can't run yet (no key stored), if it can't. */
  unavailable?: string;
  /** Whether the person can see it: the written note is asked for only once they can. */
  shown?: boolean;
  /** The chapter's own request for suggestions, so "Show me suggestions" and this view share
   *  one (its "Starting…" included). */
  submit?: ReturnType<typeof useSubmitDiscovery>;
  /** Where focus lands when the person is brought here ("Help me explore instead"). */
  headingRef?: Ref<HTMLHeadingElement>;
}) {
  const own = useSubmitDiscovery(workspaceId);
  const submit = shared ?? own;
  const start = () => submit.mutate({ expected_profile_version: profile.version });
  const { blocked } = suggestionStart(profile, discovery, unavailable, submit.isPending);
  const running = discovery !== null && stillRunning(discovery.run.status);
  // Made from earlier answers: something besides the targets chosen from it changed since
  // (the API's rule, STATE-10). Choosing a suggestion never makes its own slate out of date.
  const stale = discovery !== null && !discovery.current;

  return (
    <section className="grid gap-16" aria-labelledby="directions-title">
      <h2 id="directions-title" className="display text-25" tabIndex={-1} ref={headingRef}>
        Directions to explore
      </h2>
      <p className="small muted measure">
        Occupations from ESCO, found from your own answers. Ideas to test, not a judgement of fit:
        no score or percentage.
      </p>
      {discovery === null || (stale && !running) ? (
        <>
          {stale && (
            <Alert tone="stale" title="Based on your earlier answers">
              <p>Your answers have changed since. Suggest again to use the latest ones.</p>
            </Alert>
          )}
          <div>
            <Button variant="primary" onClick={start} disabledReason={blocked}>
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
              // The one action, unless "Suggest again" (for changed answers) is shown above.
              <Button
                variant={stale ? "secondary" : "primary"}
                onClick={start}
                disabledReason={blocked}
              >
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
          shown={shown}
          choosePrimary={!stale}
          onSuggestAgain={start}
          suggestBlocked={blocked}
        />
      )}
    </section>
  );
}
