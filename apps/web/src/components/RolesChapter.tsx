"use client";

import Link from "next/link";
import { useState } from "react";
import type {
  JobOut,
  JobPage,
  OccupationEvidenceOut,
  OccupationOut,
  ProfileOut,
  TargetRecordOut,
} from "@/generated/api";
import { chapterHref } from "@/lib/chapters";
import { useChooseTarget, useLatestDiscovery, useSlate, useTargets } from "@/lib/queries";
import { useOccupation, useOccupationEvidence, useRoleJobs } from "@/lib/roleQueries";
import { EMPTY_REASON, ESCO_NAMED } from "@/lib/vocabulary";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";

const controls = { emphasis: "balanced" as const, excludeConcepts: [], excludeFamilies: [] };
const currency = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

function pay(job: JobOut): string {
  const salary = job.salary;
  if (salary === null || salary.basis === "unknown") return "Pay not stated";
  const low = salary.minimum_minor_units;
  const high = salary.maximum_minor_units;
  const amount =
    low != null && high != null
      ? low === high
        ? currency.format(low / 100)
        : `${currency.format(low / 100)}–${currency.format(high / 100)}`
      : low != null
        ? `From ${currency.format(low / 100)}`
        : high != null
          ? `Up to ${currency.format(high / 100)}`
          : "Amount not stated";
  const period = salary.period === null ? "period not stated" : `per ${salary.period}`;
  const basis = salary.basis === "predicted" ? "Provider estimate" : "Advertised";
  return `${basis} ${amount}, ${period}`;
}

function lane(job: JobOut): "Advertised pay" | "Predicted pay" | "Pay unknown" {
  if (job.salary === null || job.salary.basis === "unknown") return "Pay unknown";
  return job.salary.basis === "predicted" ? "Predicted pay" : "Advertised pay";
}

function Listing({
  job,
  selected,
  onSelect,
}: {
  job: JobOut;
  selected: boolean;
  onSelect?(): void;
}) {
  const source = job.copies.find((copy) => copy.source_url !== null);
  const area = [...new Set(job.locations.map((place) => place.label))].join(", ");
  return (
    <li className="card grid gap-4" data-selected={selected}>
      <div>
        {onSelect ? (
          <Button variant="quiet" aria-pressed={selected} onClick={onSelect}>
            {job.title}
          </Button>
        ) : (
          <strong>{job.title}</strong>
        )}
        {selected && <span className="small muted"> · Selected advert</span>}
      </div>
      <span className="small">
        {job.employer ?? "Employer not stated"}
        {area ? ` · ${area}` : " · Area not stated"}
      </span>
      <span className="small">{pay(job)}</span>
      <span className="small muted">
        {job.exemplar ? "Your example advert, not a live vacancy" : job.freshness.label}
        {job.employment_type?.toLowerCase().includes("apprenticeship") ? " · Apprenticeship" : ""}
        {source ? ` · ${source.provider} · captured ${source.retrieved_at.slice(0, 10)}` : ""}
      </span>
      {source?.source_url && (
        <a href={source.source_url} target="_blank" rel="noopener noreferrer nofollow">
          Open source advert
        </a>
      )}
    </li>
  );
}

function mapAreas(jobs: JobOut[]) {
  const areas = new Map<string, Map<string, JobOut[]>>();
  for (const job of jobs) {
    const names = new Set(job.locations.map((place) => place.label));
    if (names.size === 0) names.add("Area not stated");
    for (const area of names) {
      let employers = areas.get(area);
      if (!employers) {
        employers = new Map();
        areas.set(area, employers);
      }
      const employer = job.employer ?? "Employer not stated";
      let openings = employers.get(employer);
      if (!openings) {
        openings = [];
        employers.set(employer, openings);
      }
      openings.push(job);
    }
  }
  return [...areas]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([area, employers]) => ({
      area,
      employers: [...employers]
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([employer, openings]) => ({ employer, openings })),
    }));
}

/** One set of filters drives both the opening list and the pay lens. */
export function Openings({ data }: { data: JobPage }) {
  const [title, setTitle] = useState("");
  const [area, setArea] = useState("");
  const [employer, setEmployer] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<"list" | "map" | "pay">("list");
  const areas = mapAreas(data.items).map((group) => group.area);
  const employers = [
    ...new Set(data.items.map((job) => job.employer ?? "Employer not stated")),
  ].sort();
  const shown = data.items.filter(
    (job) =>
      job.title.toLocaleLowerCase().includes(title.trim().toLocaleLowerCase()) &&
      (!area ||
        job.locations.some((place) => place.label === area) ||
        (area === "Area not stated" && job.locations.length === 0)) &&
      (!employer || (job.employer ?? "Employer not stated") === employer),
  );
  const selected = shown.find((job) => job.job_id === selectedId) ?? shown[0];
  return (
    <section className="grid gap-12" aria-labelledby="roles-openings">
      <div className="grid gap-4">
        <h2 id="roles-openings" className="section-title">
          Openings and examples
        </h2>
        <p className="small muted">
          {data.total_jobs} vacancies in this workspace; {data.exemplars} examples you added. These
          have not been checked for fit with a selected role.
        </p>
        <p className="small">Pay and AI evidence have not been reviewed for this release.</p>
      </div>
      {data.items.length === 0 ? (
        <p className="small">
          {data.empty_reason
            ? `${EMPTY_REASON[data.empty_reason].title}. ${EMPTY_REASON[data.empty_reason].detail}`
            : "No adverts have been collected yet. This does not mean there are no vacancies."}
        </p>
      ) : (
        <>
          <div className="opening-filters">
            <label className="grid gap-4">
              <span className="small">Find a title in these openings</span>
              <input
                className="input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </label>
            {areas.length > 0 && (
              <label className="grid gap-4">
                <span className="small">Area</span>
                <select
                  className="input"
                  value={area}
                  onChange={(event) => setArea(event.target.value)}
                >
                  <option value="">All areas</option>
                  {areas.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {employers.length > 0 && (
              <label className="grid gap-4">
                <span className="small">Employer</span>
                <select
                  className="input"
                  value={employer}
                  onChange={(event) => setEmployer(event.target.value)}
                >
                  <option value="">All employers</option>
                  {employers.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          <fieldset className="flex flex-wrap gap-8">
            <legend className="small">Openings view</legend>
            <Button
              variant="secondary"
              aria-pressed={view === "list"}
              onClick={() => setView("list")}
            >
              List
            </Button>
            <Button
              variant="secondary"
              aria-pressed={view === "map"}
              onClick={() => setView("map")}
            >
              Opportunity map
            </Button>
            <Button
              variant="secondary"
              aria-pressed={view === "pay"}
              onClick={() => setView("pay")}
            >
              Pay lens
            </Button>
          </fieldset>
          <p className="small muted" aria-live="polite">
            Showing {shown.length} of {data.items.length} loaded adverts.
          </p>
          {shown.length === 0 ? (
            <p>No openings match these filters.</p>
          ) : view === "list" ? (
            <ul className="grid gap-8">
              {shown.map((job) => (
                <Listing
                  key={job.job_id}
                  job={job}
                  selected={job.job_id === selected?.job_id}
                  onSelect={() => setSelectedId(job.job_id)}
                />
              ))}
            </ul>
          ) : view === "pay" ? (
            <div className="grid gap-16">
              {(["Advertised pay", "Predicted pay", "Pay unknown"] as const).map((name) => {
                const jobs = shown.filter((job) => lane(job) === name);
                return (
                  <section key={name} className="grid gap-8" aria-label={name}>
                    <h3 className="section-title">
                      {name} ({jobs.length})
                    </h3>
                    {jobs.length > 0 && (
                      <ul className="grid gap-8">
                        {jobs.map((job) => (
                          <Listing
                            key={job.job_id}
                            job={job}
                            selected={job.job_id === selected?.job_id}
                            onSelect={() => setSelectedId(job.job_id)}
                          />
                        ))}
                      </ul>
                    )}
                  </section>
                );
              })}
            </div>
          ) : (
            <section className="grid gap-12" aria-label="Opportunity map">
              <p className="small muted">
                Areas in collected adverts and your examples lead to employers and listings. Each
                branch shows loaded records, not distance or commute time. A listing in more than
                one area appears in each branch. Industry is not recorded for these adverts.
              </p>
              <ul className="grid gap-12">
                {mapAreas(shown).map((group) => (
                  <li key={group.area} className="card grid gap-8">
                    <div className="flex flex-wrap items-center gap-8">
                      <span className="small muted">Area</span>
                      <Button
                        variant="secondary"
                        aria-pressed={area === group.area}
                        onClick={() => setArea(area === group.area ? "" : group.area)}
                      >
                        {group.area}
                      </Button>
                      <span className="small muted">
                        {group.employers.reduce((count, item) => count + item.openings.length, 0)}{" "}
                        loaded adverts
                      </span>
                    </div>
                    <ul
                      className="grid gap-8 pl-16"
                      style={{ borderInlineStart: "1px solid var(--line-reading-hairline)" }}
                    >
                      {group.employers.map((item) => (
                        <li key={item.employer} className="grid gap-4">
                          <div className="flex flex-wrap items-center gap-8">
                            <span className="small muted">Employer</span>
                            <Button
                              variant="secondary"
                              aria-pressed={employer === item.employer}
                              onClick={() =>
                                setEmployer(employer === item.employer ? "" : item.employer)
                              }
                            >
                              {item.employer}
                            </Button>
                            <span className="small muted">{item.openings.length}</span>
                          </div>
                          <ul
                            className="grid gap-4 pl-16"
                            style={{ borderInlineStart: "1px solid var(--line-reading-hairline)" }}
                          >
                            {item.openings.map((job) => (
                              <li key={job.job_id}>
                                <Button
                                  variant="quiet"
                                  aria-pressed={selected?.job_id === job.job_id}
                                  onClick={() => setSelectedId(job.job_id)}
                                >
                                  {job.title}
                                </Button>
                              </li>
                            ))}
                          </ul>
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
              {selected && (
                <section className="grid gap-8" aria-label="Selected opening">
                  <h3 className="section-title">Selected opening</h3>
                  <ul>
                    <Listing job={selected} selected />
                  </ul>
                </section>
              )}
            </section>
          )}
          {data.next_cursor && (
            <p className="small muted">More adverts exist; this view shows the newest 100.</p>
          )}
        </>
      )}
    </section>
  );
}

function Evidence({ evidence }: { evidence: OccupationEvidenceOut }) {
  const benchmarks = evidence.modelled_pay?.benchmarks ?? [];
  const assessment = evidence.ai_resilience;
  const payMissing = {
    no_reviewed_mapping: "There is no reviewed link from this occupation to a UK pay group yet.",
    no_work_area: "Add a work area in You to see a regional pay benchmark.",
    not_published: "The regional pay benchmark is not published for this group.",
  };
  return (
    <section className="grid gap-12" aria-label="Role evidence">
      <h3 className="section-title">Evidence and unknowns</h3>
      {benchmarks.length === 0 ? (
        <p className="small">
          No modelled pay benchmark is available.{" "}
          {evidence.modelled_pay_unavailable
            ? payMissing[evidence.modelled_pay_unavailable]
            : "The reason is not known yet."}
        </p>
      ) : (
        benchmarks.map((benchmark) => {
          const median = benchmark.statistics.find((stat) => stat.statistic === "median");
          return (
            <p key={`${benchmark.soc_code}-${benchmark.region_code}`} className="small">
              {benchmark.soc_title} (SOC {benchmark.soc_code}) in {benchmark.region_name}:{" "}
              {median?.amount
                ? currency.format(median.amount.minor_units / 100)
                : "median withheld"}{" "}
              {benchmark.period.toLowerCase()} median for full-time jobs. This is the group's ONS
              ASHE figure, not pay for this exact title.
            </p>
          );
        })
      )}
      {assessment.state === "published_range" &&
      assessment.lower !== null &&
      assessment.upper !== null ? (
        <p className="small">
          AI Resilience Score: experimental {assessment.lower}–{assessment.upper} out of 10 over
          five years; higher means more resilient. This is a scenario range for the occupation
          group, not a prediction for you. Evidence quality:{" "}
          {assessment.evidence_quality ?? "not stated"}. Pack dated {assessment.pack_dated}.
          {assessment.synthetic && ` ${assessment.synthetic_label ?? "Synthetic fixture range."}`}
        </p>
      ) : (
        <p className="small">
          AI Resilience Score: unscored. No reviewed range is available for this occupation.
        </p>
      )}
      <p className="small">
        AI exposure evidence:{" "}
        {evidence.ai_evidence.state === "no_evidence"
          ? "not enough evidence yet"
          : evidence.ai_evidence.ilo
            ? `ILO evidence for ISCO group ${evidence.ai_evidence.ilo.isco_code}; this does not assess this exact role`
            : "matched task evidence exists, but no occupation-level exposure figure is held"}
        .
      </p>
      <p className="small">Outlook: not enough evidence yet.</p>
      {evidence.releases.length > 0 && (
        <details className="place-more">
          <summary>Sources and dates</summary>
          <ul className="grid gap-4 pt-12">
            {evidence.releases.map((release) => (
              <li key={release.dataset_id} className="small">
                <a href={release.source_url} target="_blank" rel="noopener noreferrer">
                  {release.dataset}
                </a>{" "}
                · {release.version} · imported {release.imported_at.slice(0, 10)} ·{" "}
                {release.attribution}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

export function RoleCard({
  title,
  target,
  occupation,
  evidence,
  occupationState,
  evidenceState,
}: {
  title: string;
  target?: TargetRecordOut;
  occupation?: OccupationOut;
  evidence?: OccupationEvidenceOut;
  occupationState?: "loading" | "failed";
  evidenceState?: "loading" | "failed";
}) {
  return (
    <section className="grid gap-16" aria-label={`${title} role details`}>
      <div className="grid gap-8">
        <h2 className="display text-25">{title}</h2>
        {target && (
          <p className="small">
            Your chosen target ·{" "}
            {target.coverage === "pack_target"
              ? "A reviewed route pack is available"
              : "No reviewed route pack for this title yet"}
          </p>
        )}
        {occupation ? (
          <>
            <p className="small">
              {occupation.description || "No workday description is held yet."}
            </p>
            {occupation.alternative_labels.length > 0 && (
              <p className="small muted">
                Also called: {occupation.alternative_labels.slice(0, 6).join(", ")}.
              </p>
            )}
            <p className="small muted">
              {ESCO_NAMED} · {occupation.isco_groups.at(-1)?.label ?? "Work group not known"}
            </p>
            {occupation.skills.length > 0 && (
              <details className="place-more">
                <summary>Skills this kind of work lists</summary>
                <p className="small pt-12">
                  These are listed for the occupation. Careerwright has not checked whether you have
                  them.
                </p>
                <ul className="grid gap-4 pt-12">
                  {occupation.skills.slice(0, 12).map((skill) => (
                    <li key={skill.skill_id} className="small">
                      {skill.preferred_label}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </>
        ) : occupationState ? (
          <p className="small">
            {occupationState === "loading"
              ? "Loading this role's workday and skills…"
              : "This role's workday and skills could not be loaded."}
          </p>
        ) : (
          <p className="small">
            Careerwright cannot show a checked workday or skills for this title until it names one
            occupation in ESCO.
          </p>
        )}
      </div>
      {evidence ? (
        <Evidence evidence={evidence} />
      ) : evidenceState ? (
        <p className="small">
          {evidenceState === "loading"
            ? "Loading pay and AI evidence…"
            : "Pay and AI evidence could not be loaded."}
        </p>
      ) : (
        <p className="small">
          Pay and AI evidence for this role are not known here yet. Outlook: not enough evidence
          yet.
        </p>
      )}
    </section>
  );
}

export function RolesChapter({
  workspaceId,
  profile,
}: {
  workspaceId: string;
  profile: ProfileOut;
}) {
  const targets = useTargets(workspaceId);
  const discovery = useLatestDiscovery(workspaceId);
  const ready = discovery.data?.run.status === "complete" && discovery.data.proposal !== null;
  const slate = useSlate(workspaceId, discovery.data?.discovery_id ?? "", controls, ready);
  const jobs = useRoleJobs(workspaceId);
  const choose = useChooseTarget(workspaceId);
  const [selected, setSelected] = useState<string | null>(null);
  const selectedTargets = targets.data?.targets ?? [];
  const suggestions = slate.data?.suggestions ?? [];
  const chosenTarget = selectedTargets.find(
    (target) => target.concept_id === selected || target.key === selected,
  );
  const chosenSuggestion = suggestions.find((suggestion) => suggestion.concept_id === selected);
  const selectedTarget = chosenTarget ?? (chosenSuggestion ? undefined : selectedTargets[0]);
  const selectedSuggestion = selectedTarget ? undefined : (chosenSuggestion ?? suggestions[0]);
  const conceptId = selectedTarget?.concept_id ?? selectedSuggestion?.concept_id ?? null;
  const occupation = useOccupation(conceptId);
  const evidence = useOccupationEvidence(workspaceId, conceptId);
  const firstError = [targets, discovery, jobs].find(
    (query) => query.error && query.data === undefined,
  );
  if (firstError)
    return (
      <div className="chapter-reading">
        <h1 className="page-title">Roles</h1>
        <RequestFailure
          error={firstError.error}
          actions={<Button onClick={() => void firstError.refetch()}>Try again</Button>}
        />
      </div>
    );
  if (!targets.data || (!discovery.data && discovery.isPending) || !jobs.data)
    return (
      <div className="chapter-reading">
        <h1 className="page-title">Roles</h1>
        <LoadingState stage="Loading roles and openings" />
      </div>
    );
  const title = selectedTarget?.title ?? selectedSuggestion?.title;
  return (
    <div className="chapter-layout">
      <div className="chapter-reading">
        <header className="chapter-heading">
          <h1 className="page-title">Roles</h1>
          <p>Explore the work behind a role, then check real openings.</p>
        </header>
        {selectedTargets.length === 0 && (
          <section className="card grid gap-8" aria-label="Choose a target role">
            <h2 className="section-title">Choose a role to work toward</h2>
            <p>
              Start in You: name a role, or explore suggestions from what you have told
              Careerwright.
            </p>
            <div>
              <Link
                className={`btn btn-${suggestions.length ? "secondary" : "primary"}`}
                href={chapterHref(workspaceId, "you")}
              >
                Choose a role in You
              </Link>
            </div>
          </section>
        )}
        {selectedTargets.length > 0 && (
          <section className="grid gap-8" aria-label="Your target roles">
            <h2 className="section-title">Your chosen roles</h2>
            <div className="flex flex-wrap gap-8">
              {selectedTargets.map((target) => (
                <Button
                  key={target.key}
                  variant="secondary"
                  aria-pressed={selectedTarget?.key === target.key}
                  onClick={() => setSelected(target.concept_id ?? target.key)}
                >
                  {target.title}
                </Button>
              ))}
            </div>
          </section>
        )}
        {selectedTarget && (
          <div>
            <Link className="btn btn-primary" href={chapterHref(workspaceId, "skills")}>
              Review skills for this role
            </Link>
          </div>
        )}
        {title && (
          <section className="grid gap-16" aria-label="Selected role">
            {!selectedTarget && selectedSuggestion && (
              <div>
                <Button
                  variant="primary"
                  onClick={() =>
                    choose.mutate({
                      expected_version: profile.version,
                      concept_id: selectedSuggestion.concept_id,
                      discovery_id: discovery.data?.discovery_id,
                    })
                  }
                  disabledReason={
                    choose.isPending
                      ? "Saving…"
                      : !discovery.data?.current
                        ? "Refresh suggestions in You first."
                        : undefined
                  }
                >
                  Choose this role
                </Button>
                {choose.error && <RequestFailure error={choose.error} />}
              </div>
            )}
            <RoleCard
              title={title}
              target={selectedTarget}
              occupation={occupation.data}
              evidence={evidence.data}
              occupationState={
                conceptId === null
                  ? undefined
                  : occupation.error
                    ? "failed"
                    : occupation.isPending
                      ? "loading"
                      : undefined
              }
              evidenceState={
                conceptId === null
                  ? undefined
                  : evidence.error
                    ? "failed"
                    : evidence.isPending
                      ? "loading"
                      : undefined
              }
            />
            {occupation.error && <RequestFailure error={occupation.error} />}
            {evidence.error && <RequestFailure error={evidence.error} />}
          </section>
        )}
        {suggestions.length > 0 && (
          <section className="grid gap-8" aria-labelledby="roles-other">
            <h2 id="roles-other" className="section-title">
              Other directions to explore
            </h2>
            {!discovery.data?.current && (
              <p className="small muted">
                These suggestions use earlier answers. Refresh them in You before choosing.
              </p>
            )}
            <ul className="grid gap-8">
              {suggestions
                .filter(
                  (suggestion) =>
                    !selectedTargets.some((target) => target.concept_id === suggestion.concept_id),
                )
                .map((suggestion) => (
                  <li key={suggestion.concept_id} className="card grid gap-4">
                    <strong>{suggestion.title}</strong>
                    <span className="small muted">
                      {suggestion.family.label} ·{" "}
                      {suggestion.horizon === "next_step" ? "Next step" : "Aim higher"}
                    </span>
                    <span className="small">{suggestion.workday}</span>
                    <span className="small">
                      Shared skills:{" "}
                      {suggestion.shared_skills.length
                        ? suggestion.shared_skills.map((skill) => skill.label).join(", ")
                        : "not established yet"}
                      .
                    </span>
                    <div>
                      <Button
                        variant="secondary"
                        onClick={() => setSelected(suggestion.concept_id)}
                      >
                        Explore this role
                      </Button>
                    </div>
                  </li>
                ))}
            </ul>
          </section>
        )}
        {slate.error ? <RequestFailure error={slate.error} /> : null}
      </div>
      <aside className="chapter-landscape roles-landscape" aria-label="Collected openings">
        <Openings data={jobs.data} />
        {jobs.data.total_jobs === 0 && selectedTarget && (
          <p className="small">
            Check current vacancies on employers' own sites. When you find one, add its requirements
            in <Link href={chapterHref(workspaceId, "skills")}>Skills</Link> to compare with what
            you can show. No live opening has been checked here.
          </p>
        )}
      </aside>
    </div>
  );
}
