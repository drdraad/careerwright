"use client";

import type {
  OptionResearchEstimateOut,
  OptionResearchOut,
  SearchEmptyReason,
} from "@/generated/api";
import { formatDay } from "@/lib/dates";
import { formatUsd } from "@/lib/usd";
import { RUN_ESTIMATE } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

const STATUS: Record<OptionResearchOut["status"], string> = {
  searching: "Searching for pages about courses, apprenticeships, degrees and funding.",
  search_stopped: "The search stopped before Careerwright could check options.",
  no_pages: "This search found no page it could check for options.",
  ready_to_read: "The search finished. Careerwright is starting its page checks.",
  reading: "Checking the source pages and their stated facts.",
  completed: "Page checks finished.",
  reading_stopped: "Page checks stopped before every candidate could be checked.",
};

const EMPTY: Record<SearchEmptyReason, string> = {
  search_returned_nothing: "The search returned no pages.",
  no_candidate_proposed: "The search returned pages, but none was suitable to check.",
  all_excluded: "Every proposed page was excluded by its access rules.",
};

type Props = {
  target: string;
  cities: readonly string[];
  city: string;
  onCity(city: string): void;
  keyReady: boolean;
  canWrite: boolean;
  estimate: OptionResearchEstimateOut | null;
  estimateLoading: boolean;
  estimateError: unknown;
  research: OptionResearchOut | null;
  researchLoading: boolean;
  researchError: unknown;
  starting: boolean;
  reading: boolean;
  cancelling: boolean;
  startError: unknown;
  readError: unknown;
  cancelError: unknown;
  onStart(): void;
  onRead(): void;
  onCancel(runId: string): void;
};

function Results({ research }: { research: OptionResearchOut }) {
  if (research.records.length === 0) {
    return (
      <p className="small">
        No course or funding details were verified in the pages checked. This does not establish
        that no options exist.
      </p>
    );
  }
  return (
    <div className="grid gap-8">
      <h4 className="font-semibold">Records added to Options</h4>
      <p className="small">
        These records are not reviewed yet. Check their source and current terms before relying on
        them; Routes will qualify any route that uses them.
      </p>
      <ul className="grid gap-12">
        {research.records.map((record) => (
          <li key={record.record_id} className="card-on-reading grid gap-8 p-16">
            <h5 className="font-semibold">{record.title}</h5>
            <p className="small">
              {record.kind === "funding"
                ? "Funding"
                : record.kind === "apprenticeship"
                  ? "Apprenticeship"
                  : "Course or degree"}{" "}
              · Not reviewed yet · Read {formatDay(record.retrieved_on)}
              {record.expired ? ". This source needs a fresh check." : "."}
            </p>
            <a href={record.source_url} target="_blank" rel="noopener noreferrer nofollow">
              Open source page
            </a>
            {Object.keys(record.citations).length > 0 && (
              <details className="details small">
                <summary>Words checked on the source page</summary>
                <dl className="kv pt-12">
                  {Object.entries(record.citations).map(([field, citation]) => (
                    <div key={field} className="contents">
                      <dt>{field.replaceAll("_", " ")}</dt>
                      <dd>
                        {citation.excerpt ? `“${citation.excerpt}”` : "Source span recorded."}
                      </dd>
                    </div>
                  ))}
                </dl>
              </details>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function OptionResearchView({
  target,
  cities,
  city,
  onCity,
  keyReady,
  canWrite,
  estimate,
  estimateLoading,
  estimateError,
  research,
  researchLoading,
  researchError,
  starting,
  reading,
  cancelling,
  startError,
  readError,
  cancelError,
  onStart,
  onRead,
  onCancel,
}: Props) {
  const active = research?.status === "searching" || research?.status === "reading";
  const activeRun = research?.status === "reading" ? research.reading : research?.search;
  const canStart =
    research === null ||
    research.status === "search_stopped" ||
    research.status === "no_pages" ||
    research.status === "reading_stopped" ||
    research.status === "completed";
  const failure = research?.status === "reading_stopped" ? research.reading : research?.search;

  return (
    <section className="grid gap-12" aria-label={`Find options for ${target}`}>
      <h3 className="section-title">Find options for this role</h3>
      <p className="small">
        Careerwright can search for courses, apprenticeships, degrees and funding for {target}. It
        sends only this target title and one of your cities. Source facts become not reviewed
        records in this workspace.
      </p>
      {cities.length > 1 && (
        <label className="grid gap-4" htmlFor="option-research-city">
          City to search from
          <select
            id="option-research-city"
            className="input"
            value={city}
            onChange={(event) => onCity(event.target.value)}
          >
            {cities.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      )}
      {cities.length === 1 && <p className="small">City sent: {city}.</p>}
      {cities.length === 0 && (
        <p className="small">Add a city in You before searching for options.</p>
      )}
      {researchLoading && research === null && <p className="small">Checking earlier research…</p>}
      {researchError != null && <RequestFailure error={researchError} />}
      {research && (
        <div className="grid gap-8" aria-live="polite">
          <p className="small">{STATUS[research.status]}</p>
          {research.status === "no_pages" && (
            <p className="small">
              {research.empty_reason
                ? EMPTY[research.empty_reason]
                : "No usable page was returned."}{" "}
              This does not mean there are no options.
            </p>
          )}
          {(research.status === "ready_to_read" || research.status === "reading") && (
            <p className="small">
              {research.candidates} candidate pages, at most 5 checked. {research.pages_attempted}{" "}
              attempted; {research.pages_read} read, {research.pages_blocked} blocked,{" "}
              {research.pages_failed} failed.
            </p>
          )}
          {research.status === "reading" && (
            <progress
              max={Math.max(1, Math.min(5, research.candidates))}
              value={research.pages_attempted}
            >
              {research.pages_attempted} pages attempted
            </progress>
          )}
          {(research.status === "completed" || research.status === "reading_stopped") && (
            <p className="small">
              {research.coverage === "complete"
                ? `Checked ${research.pages_read} of ${research.candidates} candidate pages within the five-page limit.`
                : `The result is incomplete: ${research.pages_read} pages read, ${research.pages_blocked} blocked and ${research.pages_failed} failed. Unread pages are not counted as no options.`}
            </p>
          )}
          {(research.records.length > 0 ||
            research.status === "completed" ||
            research.status === "reading_stopped") && <Results research={research} />}
          {(research.status === "search_stopped" || research.status === "reading_stopped") && (
            <p className="small">
              {failure?.status === "cancelled"
                ? "You stopped this run."
                : failure?.failure_class === "budget_exceeded"
                  ? "The model spending limit stopped further checks."
                  : "The run could not finish its checks."}{" "}
              Pages left unread are not evidence that no option exists.
            </p>
          )}
          {research.status === "ready_to_read" && readError != null && (
            <Button
              variant="secondary"
              onClick={onRead}
              disabledReason={reading ? "Starting…" : undefined}
            >
              Try page checks again
            </Button>
          )}
          {active && activeRun && activeRun.cancel_requested_at == null && (
            <div>
              <Button
                variant="secondary"
                onClick={() => onCancel(activeRun.run_id)}
                disabledReason={cancelling ? "Stopping…" : undefined}
              >
                Stop research
              </Button>
            </div>
          )}
        </div>
      )}
      {canStart && (
        <div className="grid gap-8">
          {estimateLoading && estimate === null && (
            <p className="small">Checking the cost estimate…</p>
          )}
          {estimateError != null && <RequestFailure error={estimateError} />}
          {estimate && (
            <p className="small">
              {estimate.refused_scope === "run"
                ? null
                : estimate.model_mode === "fixture"
                  ? "No model charge in this workspace."
                  : `Estimated model spending: up to ${formatUsd(estimate.combined_maximum_nano_usd)} for one search and at most five page checks.${estimate.hard_maximum_nano_usd > estimate.combined_maximum_nano_usd ? ` Worker restarts could reach ${formatUsd(estimate.hard_maximum_nano_usd)}.` : ""}`}
              {estimate.refused_scope !== null &&
                ` ${RUN_ESTIMATE.refused[estimate.refused_scope]}`}
            </p>
          )}
          <div>
            <Button
              variant="secondary"
              onClick={onStart}
              disabledReason={
                cities.length === 0
                  ? "Add a city in You first"
                  : !keyReady
                    ? "Checking your Meta key…"
                    : !canWrite
                      ? "Store a Meta API key in You first"
                      : researchLoading
                        ? "Checking earlier research…"
                        : researchError != null
                          ? "Earlier research could not be loaded"
                          : estimate === null
                            ? "Wait for the cost estimate"
                            : estimate.refused_scope !== null
                              ? "The spending limit would refuse this search"
                              : starting
                                ? "Starting…"
                                : undefined
              }
            >
              {research === null ? "Find options for this role" : "Search for options again"}
            </Button>
          </div>
        </div>
      )}
      {[startError, readError, cancelError].map(
        (error, index) => error != null && <RequestFailure key={String(index)} error={error} />,
      )}
    </section>
  );
}
