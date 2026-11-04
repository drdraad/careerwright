"use client";
import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import type { ComparisonOut, RouteDetail, ScheduleOut } from "@/generated/api";
import { chapterHref } from "@/lib/chapters";
import { formatDay, formatMonth } from "@/lib/dates";
import { formatMoney, formatSignedMoney, parseMoneyInput } from "@/lib/money";
import { BASELINE_KIND, NEEDED_INPUT, NOT_KNOWN, OBJECTIVE_BASIS } from "@/lib/optionWords";
import { useCurrentPlan } from "@/lib/planQueries";
import { useCheckpoint, useProfile } from "@/lib/queries";
import {
  type RouteView,
  useCachedRouteLandscapes,
  useLatestRouteSolve,
  useRequestRouteSolve,
  useRouteComparison,
  useRouteJourneyDetails,
  useRouteSchedule,
  useRouteSchedules,
} from "@/lib/routeQueries";
import { routeIdentity } from "@/lib/routeState";
import {
  FINDING,
  findingWords,
  NARROWING,
  ROUTE_CONDITION,
  ROUTE_LEAD,
  ROUTE_QUALIFICATION,
  ROUTE_VERDICT,
} from "@/lib/routeWords";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { RouteChart } from "./RouteChart";
import { RouteDetailView } from "./RouteDetailView";
import { type JourneyTarget, RouteExplorer } from "./RouteExplorer";

function londonMonth(): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/London",
    year: "numeric",
    month: "2-digit",
  }).formatToParts(new Date());
  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  if (year === undefined || month === undefined) throw new Error("Cannot read the current month");
  return `${year}-${month}`;
}

function ScheduleCard({
  schedule,
  select,
  selected,
  saved,
  detail,
}: {
  schedule: ScheduleOut;
  select(index: number): void;
  selected: boolean;
  saved: boolean;
  detail?: RouteDetail;
}) {
  return (
    <li className="grid gap-8">
      <button
        type="button"
        className="decision-route-option"
        aria-pressed={selected}
        onClick={() => select(schedule.index)}
      >
        <span className="decision-route-mode">
          <strong>Route {schedule.index + 1}</strong>
          {saved && <span>Saved plan</span>}
          {selected && <span>Viewing</span>}
        </span>
        <span className="decision-route-date">
          <strong>{formatMonth(`${schedule.readiness_month}-01`)}</strong>
          <span>{schedule.months_to_readiness}-month route</span>
          {detail?.steps.length === 1 && detail.steps[0]?.weekly_hours != null && (
            <span>
              {detail.steps[0].weekly_hours}h {detail.steps[0].kind === "work" ? "work" : "study"}
              {detail.steps[0].work_pattern
                ? ` + ${detail.steps[0].work_pattern.hours_per_week}h work`
                : ""}{" "}
              / week
            </span>
          )}
        </span>
        <span className="decision-route-cost">
          <strong>{formatSignedMoney(schedule.objective_cost)}</strong>
          <span>Modelled cost</span>
          {detail?.costs.pay_difference != null && (
            <span>
              {detail.costs.pay_difference.minor_units === 0
                ? "Keeps your stated pay"
                : `${formatSignedMoney(detail.costs.pay_difference)} pay difference`}
            </span>
          )}
        </span>
      </button>
      <details className="details small">
        <summary>Route {schedule.index + 1}: conditions and assumptions</summary>
        <div className="grid gap-8 pt-12">
          <p>{ROUTE_VERDICT[schedule.verdict]}.</p>
          <p>
            {schedule.layer === null ? "Rank not settled" : `Recorded rank F${schedule.layer}`}.
            {schedule.view_layer != null && ` F${schedule.view_layer} within this filtered view.`}
          </p>
          {schedule.conditions.map((condition) => (
            <p key={`${condition.verification}-${condition.variant_id}-${condition.instrument_id}`}>
              {ROUTE_CONDITION[condition.verification]}.
            </p>
          ))}
          {schedule.qualifications.map((qualification) => (
            <p key={qualification}>{ROUTE_QUALIFICATION[qualification]}.</p>
          ))}
        </div>
      </details>
    </li>
  );
}

function ResultLead({
  comparison,
  workspaceId,
}: {
  comparison: ComparisonOut;
  workspaceId: string;
}) {
  const stopped = comparison.coverage === "budget_truncated";
  const needsSkills = [...comparison.blocking_inputs, ...comparison.starting_violations].some(
    (finding) =>
      finding.code === "entry_requirements_not_met" ||
      finding.code === "entry_requirements_unconfirmed" ||
      finding.code === "entry_requirements_expected",
  );
  const checkSkills =
    needsSkills || comparison.readiness_unknown > 0 || comparison.feasible_without_milestone > 0;
  const nextChapter = checkSkills ? "skills" : "options";
  return (
    <section className="grid gap-8" aria-label="Route search result">
      <h2 className="section-title">{ROUTE_LEAD[comparison.lead]}</h2>
      <p className="small">
        Careerwright compared {comparison.instance.variants} ways to start across{" "}
        {comparison.instance.concepts} options and {comparison.instance.months} months.{" "}
        {comparison.schedules_total} routes reached the target in this model.
      </p>
      {comparison.schedules_total === 0 && (
        <p className="small">
          {checkSkills
            ? "Review what you can show and any requirements Careerwright could not bridge before searching again."
            : "Review the options and missing facts before searching again."}{" "}
          <Link href={chapterHref(workspaceId, nextChapter)}>
            Open {checkSkills ? "Skills" : "Options"}
          </Link>
          .
        </p>
      )}
      {comparison.schedules_total === 0 &&
        (comparison.basis.replan?.completed_variants.length ?? 0) > 0 && (
          <p className="small">
            You reported a step finished. Careerwright has not checked what it taught you. Review
            your evidence in <Link href={chapterHref(workspaceId, "skills")}>Skills</Link> before
            using this result.
          </p>
        )}
      {stopped && (
        <p className="small">
          The search stopped at its limit, so there may be other routes.
          {comparison.narrowings.length > 0 &&
            ` You could ${comparison.narrowings.map((n) => NARROWING[n]).join(", or ")}.`}
        </p>
      )}
      {[...new Set(comparison.blocking_inputs.map(findingWords))].map((words) => (
        <p key={words} className="small">
          {words}
        </p>
      ))}
      {[...new Set(comparison.starting_violations.map(findingWords))].map((words) => (
        <p key={words} className="small">
          {words}
        </p>
      ))}
      {comparison.longer_than_model.length > 0 && (
        <p className="small">
          {comparison.longer_than_model.length}{" "}
          {comparison.longer_than_model.length === 1 ? "option takes" : "options take"} longer than
          Careerwright can plan yet. Their outcomes remain unknown here.
        </p>
      )}
      {comparison.beyond_horizon.length > 0 && (
        <p className="small">
          {comparison.beyond_horizon.length}{" "}
          {comparison.beyond_horizon.length === 1 ? "option finishes" : "options finish"} after the
          months you chose for this comparison.
        </p>
      )}
      {comparison.set_aside.length > 0 && (
        <details className="details small">
          <summary>
            Why {comparison.set_aside.length}{" "}
            {comparison.set_aside.length === 1 ? "option was" : "options were"} set aside
          </summary>
          <ul className="grid gap-8 pt-12">
            {comparison.set_aside.map((item) => (
              <li key={item.variant_id}>{item.codes.map((code) => FINDING[code]).join("; ")}.</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

export function RoutesChapter({ workspaceId }: { workspaceId: string }) {
  const checkpoint = useCheckpoint(workspaceId);
  const profile = useProfile(workspaceId);
  const savedPlan = useCurrentPlan(workspaceId);
  const [focusedTarget, setFocusedTarget] = useState<string | null>(null);
  const [chosenTarget, setChosenTarget] = useState("");
  useEffect(() => {
    setChosenTarget(new URLSearchParams(window.location.search).get("target") ?? "");
  }, []);
  const targets = checkpoint.data?.targets ?? [];
  const target =
    targets.find((item) => item.target_title === chosenTarget)?.target_title ??
    targets[0]?.target_title ??
    "";
  const selectedTarget = targets.find((item) => item.target_title === target);
  const noCatalogue = selectedTarget?.label === null && selectedTarget.options.length === 0;
  const latest = useLatestRouteSolve(workspaceId, target);
  const request = useRequestRouteSolve(workspaceId);
  const [start, setStart] = useState(londonMonth);
  const [horizon, setHorizon] = useState(24);
  const [maxMonths, setMaxMonths] = useState<number | null>(null);
  const [maxCostMinor, setMaxCostMinor] = useState<number | null>(null);
  const [maxCostText, setMaxCostText] = useState("");
  const [layer, setLayer] = useState<number | null>(null);
  const [familyId, setFamilyId] = useState<string | null>(null);
  const [rerank, setRerank] = useState(false);
  const [cursors, setCursors] = useState<Array<string | null>>([null]);
  const [selections, setSelections] = useState<
    Record<
      string,
      {
        runId: string;
        index: number;
        identity: string | null;
      }
    >
  >({});
  const selection = selections[target] ?? null;
  const newest = latest.data?.latest ?? null;
  const previous = latest.data?.kept ?? null;
  const active = newest;
  const kept = previous;
  const shown = active?.run.status === "complete" ? active : kept;
  const runId = shown?.run.run_id ?? null;
  const complete = shown !== null;
  const comparison = useRouteComparison(workspaceId, runId, complete);
  const changedSince =
    (comparison.data !== undefined && Object.values(comparison.data.changed_since).some(Boolean)) ||
    (shown?.inputs_version != null &&
      checkpoint.data !== undefined &&
      shown.inputs_version !== checkpoint.data.inputs_version) ||
    (shown?.run.profile_version != null &&
      profile.data !== undefined &&
      shown.run.profile_version !== profile.data.version);
  const view: RouteView = {
    limit: 20,
    ...(cursors.at(-1) === null ? {} : { cursor: cursors.at(-1) }),
    ...(maxMonths === null ? {} : { max_months: maxMonths }),
    ...(maxCostMinor === null ? {} : { max_cost_minor: maxCostMinor }),
    ...(layer === null ? {} : { layer }),
    ...(familyId === null ? {} : { family_id: familyId }),
    rerank,
  };
  const schedules = useRouteSchedules(workspaceId, runId, view, complete);
  const journeySchedules = useRouteSchedules(workspaceId, runId, { limit: 6 }, complete);
  const journeyQueries = useRouteJourneyDetails(
    workspaceId,
    runId,
    journeySchedules.data?.items.slice(0, 6).map((item) => item.index) ?? [],
  );
  const journeyRoutes = journeyQueries.flatMap((query) => (query.data ? [query.data] : []));
  const selected =
    selection === null
      ? null
      : selection.runId === runId
        ? selection.index
        : (journeyRoutes.find((route) => routeIdentity(route) === selection.identity)?.schedule
            .index ?? null);
  const detail = useRouteSchedule(workspaceId, runId, selected);
  useEffect(() => {
    if (detail.data && runId !== null && selected !== null) {
      const identity = routeIdentity(detail.data);
      setSelections((current) =>
        current[target]?.runId === runId && current[target]?.identity === identity
          ? current
          : { ...current, [target]: { runId, index: selected, identity } },
      );
    }
  }, [detail.data, runId, selected, target]);
  const inspect = (index: number) => {
    if (runId === null) return;
    const route = journeyRoutes.find((item) => item.schedule.index === index);
    setSelections((current) => ({
      ...current,
      [target]: { runId, index, identity: route ? routeIdentity(route) : null },
    }));
    setFocusedTarget(target);
  };
  const running =
    request.isPending || active?.run.status === "queued" || active?.run.status === "running";
  const savedIndex =
    savedPlan.data?.source.solve_run_id === runId
      ? savedPlan.data.source.schedule_index
      : undefined;
  const routes: RouteDetail[] =
    detail.data &&
    !journeyRoutes.some((route) => route.schedule.index === detail.data.schedule.index)
      ? [...journeyRoutes, detail.data]
      : journeyRoutes;
  const routeStatus: JourneyTarget["status"] = running
    ? "pending"
    : changedSince || (shown && shown !== active)
      ? "stale"
      : latest.error || comparison.error || journeySchedules.error
        ? "error"
        : !latest.data
          ? "pending"
          : !shown
            ? active
              ? "error"
              : "not_searched"
            : !comparison.data
              ? "pending"
              : comparison.data.schedules_total > 0
                ? "available"
                : comparison.data.coverage !== "complete"
                  ? "limited"
                  : comparison.data.lead === "no_route_in_bounded_model"
                    ? "unsupported"
                    : "unresolved";
  const cachedLandscapes = useCachedRouteLandscapes(
    workspaceId,
    targets.map((item) => item.target_title),
  );
  const journeyTargets: JourneyTarget[] = targets.map((item) =>
    item.target_title === target
      ? {
          id: item.target_title,
          title: item.target_title,
          routes,
          status:
            routeStatus === "available" && cachedLandscapes[item.target_title]?.status === "stale"
              ? "stale"
              : routeStatus,
          scheduleCount: comparison.data?.schedules_total,
          detailStatus: journeyQueries.some((query) => query.isError)
            ? "error"
            : journeySchedules.isPending || journeyQueries.some((query) => query.isPending)
              ? "pending"
              : undefined,
          planIndex: savedIndex,
          completedSteps:
            savedIndex === undefined ? undefined : savedPlan.data?.progress?.completed_steps,
          routeSetId: runId ?? undefined,
        }
      : {
          id: item.target_title,
          title: item.target_title,
          routes: [],
          status: "unloaded",
          ...cachedLandscapes[item.target_title],
          planIndex:
            savedPlan.data?.source.solve_run_id === cachedLandscapes[item.target_title]?.routeSetId
              ? savedPlan.data?.source.schedule_index
              : undefined,
          completedSteps:
            savedPlan.data?.source.solve_run_id === cachedLandscapes[item.target_title]?.routeSetId
              ? savedPlan.data?.progress?.completed_steps
              : undefined,
        },
  );
  const blocked = checkpoint.data?.needs.filter((need) => need.effect === "blocks_a_solve") ?? [];
  const costs = comparison.data?.points.map((point) => point.objective_cost.minor_units) ?? [];
  const lowCostPounds = Math.floor(Math.min(0, ...costs) / 100);
  const highCostPounds = Math.ceil(Math.max(0, ...costs) / 100);
  const answerChapter =
    blocked[0]?.input === "direct_spend_cap" || blocked[0]?.input === "monthly_payment_cap"
      ? "you"
      : "options";

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (checkpoint.data === undefined || target === "" || blocked.length > 0 || noCatalogue) return;
    setCursors([null]);
    setMaxMonths(null);
    setMaxCostMinor(null);
    setMaxCostText("");
    setLayer(null);
    setFamilyId(null);
    setRerank(false);
    request.mutate({
      expected_inputs_version: checkpoint.data.inputs_version,
      target,
      planning_start: start,
      horizon_months: horizon,
    });
  };

  return (
    <div className="chapter-layout routes-chapter">
      <section className="chapter-reading">
        <header className="chapter-heading">
          <h1 className="page-title">Compare your routes</h1>
          <p>See what each route asks of your time and money.</p>
        </header>
        {checkpoint.data === undefined && checkpoint.error ? (
          <RequestFailure
            error={checkpoint.error}
            actions={
              <Button variant="secondary" onClick={() => void checkpoint.refetch()}>
                Try again
              </Button>
            }
          />
        ) : checkpoint.data === undefined ? (
          <LoadingState stage="Checking what the routes need" />
        ) : checkpoint.data.targets.length === 0 ? (
          <p>
            Choose a target in You before searching for routes.{" "}
            <Link href={chapterHref(workspaceId, "you")}>Open You</Link>
          </p>
        ) : latest.data === undefined && !latest.error ? (
          <LoadingState stage="Checking earlier route searches" />
        ) : (
          <>
            <details
              key={complete ? "result" : "search"}
              className="details"
              open={!complete || changedSince}
            >
              <summary>{complete ? "Change comparison" : "Set up a route search"}</summary>
              <form className="grid gap-12 pt-12" onSubmit={submit}>
                <label className="grid gap-4" htmlFor="route-target">
                  <span>Destination</span>
                  <select
                    id="route-target"
                    className="input"
                    value={target}
                    onChange={(event) => {
                      setChosenTarget(event.target.value);
                      setFocusedTarget(event.target.value);
                      setCursors([null]);
                      setFamilyId(null);
                    }}
                  >
                    {checkpoint.data.targets.map((item) => (
                      <option key={item.target_title} value={item.target_title}>
                        {item.target_title}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="grid gap-12 sm:grid-cols-2">
                  <label className="grid gap-4" htmlFor="route-start">
                    <span>Start comparing from</span>
                    <input
                      id="route-start"
                      className="input"
                      type="month"
                      min={londonMonth()}
                      value={start}
                      onChange={(event) => setStart(event.target.value)}
                      required
                    />
                  </label>
                  <label className="grid gap-4" htmlFor="route-horizon">
                    <span>Months to compare</span>
                    <input
                      id="route-horizon"
                      className="input"
                      type="number"
                      min={1}
                      max={24}
                      value={horizon}
                      onChange={(event) => setHorizon(Number(event.target.value))}
                      required
                    />
                  </label>
                </div>
                {blocked.length > 0 && (
                  <div className="grid gap-4">
                    <p>Before searching, add these answers:</p>
                    <ul>
                      {blocked.map((need) => (
                        <li key={need.input}>{NEEDED_INPUT[need.input].name}</li>
                      ))}
                    </ul>
                    <Link
                      className="btn btn-secondary"
                      href={chapterHref(workspaceId, answerChapter)}
                    >
                      Open {answerChapter === "you" ? "You" : "Options"}
                    </Link>
                  </div>
                )}
                {noCatalogue && (
                  <p className="small">
                    Careerwright has no option catalogue for this target yet. Add or research an
                    option in <Link href={chapterHref(workspaceId, "options")}>Options</Link> first.
                  </p>
                )}
                <div>
                  <Button
                    type="submit"
                    variant="primary"
                    disabledReason={
                      noCatalogue
                        ? "Add or research an option in Options first"
                        : blocked.length > 0
                          ? "Add the missing answers first"
                          : request.isPending
                            ? "Starting…"
                            : undefined
                    }
                  >
                    {active ? "Search again" : "Find routes"}
                  </Button>
                </div>
                {request.error && <RequestFailure error={request.error} />}
              </form>
            </details>
            {latest.data === undefined && latest.error ? (
              <RequestFailure
                error={latest.error}
                actions={
                  <Button variant="secondary" onClick={() => void latest.refetch()}>
                    Try again
                  </Button>
                }
              />
            ) : active !== null &&
              shown !== null &&
              shown !== active &&
              (active.run.status === "queued" || active.run.status === "running") ? (
              <p className="small">
                A new search is running. The routes below are kept from your last search.
              </p>
            ) : null}
            {shown !== null &&
              shown !== active &&
              active?.run.status !== "queued" &&
              active?.run.status !== "running" && (
                <p className="small">
                  Kept from an earlier search. Search again to use your current answers.
                </p>
              )}
            {!complete && active === null ? null : !complete &&
              (active?.run.status === "queued" || active?.run.status === "running") ? (
              <LoadingState stage="Searching for routes" />
            ) : !complete ? (
              <p>The last route search could not finish. Search again when you are ready.</p>
            ) : comparison.data === undefined && comparison.error ? (
              <RequestFailure
                error={comparison.error}
                actions={
                  <Button variant="secondary" onClick={() => void comparison.refetch()}>
                    Try again
                  </Button>
                }
              />
            ) : comparison.data === undefined ? (
              <LoadingState stage="Reading the routes" />
            ) : (
              <>
                {comparison.data.changed_since.planning_inputs ||
                comparison.data.changed_since.profile ? (
                  <p className="small">
                    Your answers changed after this search. These routes use the earlier answers;
                    search again to use what you know now.
                  </p>
                ) : null}
                {comparison.data.changed_since.capability && (
                  <p className="small" role="status">
                    Your skill evidence changed after this search. These routes use the earlier
                    assessment; search again before choosing one.
                  </p>
                )}
                {(comparison.data.changed_since.target_matrix ||
                  comparison.data.changed_since.option_pack) && (
                  <p className="small" role="status">
                    The target definition or option research changed after this search. These routes
                    use the earlier information; search again before choosing one.
                  </p>
                )}
                {comparison.data.schedules_total === 0 ? (
                  <ResultLead comparison={comparison.data} workspaceId={workspaceId} />
                ) : null}
                <details className="details small">
                  <summary>About this search and its assumptions</summary>
                  <div className="grid gap-16 pt-12">
                    {comparison.data.schedules_total > 0 && (
                      <ResultLead comparison={comparison.data} workspaceId={workspaceId} />
                    )}
                    <section className="grid gap-8" aria-label="What the comparison means">
                      <p className="small">
                        {OBJECTIVE_BASIS[comparison.data.basis.objective_basis]} over{" "}
                        {comparison.data.basis.horizon_months} months from{" "}
                        {formatMonth(`${comparison.data.basis.planning_start.slice(0, 7)}-01`)}.
                      </p>
                      <details className="details small">
                        <summary>What this comparison includes</summary>
                        <dl className="kv pt-12">
                          <dt>Cost shown</dt>
                          <dd>
                            {OBJECTIVE_BASIS[comparison.data.basis.objective_basis]}, in pounds.
                          </dd>
                          <dt>Search coverage</dt>
                          <dd>
                            {comparison.data.coverage === "complete"
                              ? "The search completed within its limits."
                              : "The search stopped at its limit; other routes may exist."}
                          </dd>
                          <dt>Options used</dt>
                          <dd>
                            Careerwright's list dated {formatDay(comparison.data.label.dated)}
                            {comparison.data.basis.synthetic ? ", with made-up demo data" : ""}.
                          </dd>
                          <dt>Search bounds</dt>
                          <dd>
                            Up to {comparison.data.limits.max_actions ?? NOT_KNOWN} actions and{" "}
                            {comparison.data.limits.max_starts_per_action ?? NOT_KNOWN} starts for
                            each, within {comparison.data.limits.max_months ?? NOT_KNOWN} months.
                            The search could stop after{" "}
                            {comparison.data.limits.max_states ?? NOT_KNOWN} possibilities or{" "}
                            {comparison.data.limits.wall_seconds ?? NOT_KNOWN} seconds.
                          </dd>
                          {comparison.data.basis.baseline && (
                            <>
                              <dt>What you'd do without this change</dt>
                              <dd>
                                {comparison.data.basis.baseline.kind === null
                                  ? "The demo's stated baseline"
                                  : BASELINE_KIND[comparison.data.basis.baseline.kind]}
                              </dd>
                              <dt>Take-home pay without the change</dt>
                              <dd>
                                {comparison.data.basis.baseline.net_income_by_month
                                  .map(
                                    (value, index) => `Month ${index + 1}: ${formatMoney(value)}`,
                                  )
                                  .join("; ")}
                              </dd>
                            </>
                          )}
                        </dl>
                      </details>
                    </section>
                  </div>
                </details>
                <div className="grid gap-24">
                  <section className="grid gap-12" aria-label="Route archive">
                    <h2 className="section-title">Routes to {target}</h2>
                    <details className="details small">
                      <summary>Filter this view</summary>
                      <p className="small pt-12">Recorded ranks do not change when you filter.</p>
                      <div className="grid gap-8 pt-12">
                        <label htmlFor="route-max-months">
                          {maxMonths === null
                            ? "Any time within this comparison"
                            : `Ready within ${maxMonths} months`}
                        </label>
                        <input
                          id="route-max-months"
                          type="range"
                          min={0}
                          max={comparison.data.basis.horizon_months}
                          value={maxMonths ?? comparison.data.basis.horizon_months}
                          onChange={(event) => {
                            setMaxMonths(Number(event.target.value));
                            setCursors([null]);
                          }}
                        />
                        <input
                          aria-label="Exact maximum months"
                          type="number"
                          className="input"
                          min={0}
                          max={comparison.data.basis.horizon_months}
                          value={maxMonths ?? ""}
                          placeholder="Any"
                          onChange={(event) => {
                            const months =
                              event.target.value === "" ? null : Number(event.target.value);
                            if (
                              months === null ||
                              (Number.isSafeInteger(months) &&
                                months >= 0 &&
                                months <= comparison.data.basis.horizon_months)
                            ) {
                              setMaxMonths(months);
                              setCursors([null]);
                            }
                          }}
                        />
                        {costs.length > 0 && (
                          <>
                            <label htmlFor="route-max-cost">
                              {maxCostMinor === null
                                ? "Any cost"
                                : `Cost up to ${formatSignedMoney({ minor_units: maxCostMinor, currency: "GBP" })}`}
                            </label>
                            <input
                              id="route-max-cost"
                              type="range"
                              min={lowCostPounds}
                              max={highCostPounds}
                              value={
                                maxCostMinor === null
                                  ? highCostPounds
                                  : Math.round(maxCostMinor / 100)
                              }
                              onChange={(event) => {
                                setMaxCostMinor(Number(event.target.value) * 100);
                                setMaxCostText(event.target.value);
                                setCursors([null]);
                              }}
                            />
                            <input
                              aria-label="Exact maximum cost in pounds"
                              type="text"
                              inputMode="decimal"
                              className="input"
                              value={maxCostText}
                              placeholder="Any"
                              onChange={(event) => {
                                const text = event.target.value;
                                const negative = /^[-−]/.test(text);
                                const parsed = parseMoneyInput(
                                  negative ? text.slice(1) : text,
                                  "GBP",
                                );
                                setMaxCostText(text);
                                setMaxCostMinor(
                                  text === ""
                                    ? null
                                    : parsed.ok
                                      ? parsed.money.minor_units * (negative ? -1 : 1)
                                      : null,
                                );
                                setCursors([null]);
                              }}
                            />
                            {maxCostText !== "" && maxCostMinor === null && (
                              <p className="small" role="alert">
                                Enter an amount in pounds and pence.
                              </p>
                            )}
                          </>
                        )}
                        <label htmlFor="route-layer">Recorded layer</label>
                        <select
                          id="route-layer"
                          className="input"
                          value={layer ?? ""}
                          onChange={(event) => {
                            setLayer(event.target.value === "" ? null : Number(event.target.value));
                            setCursors([null]);
                          }}
                        >
                          <option value="">All layers</option>
                          <option value="1">F1</option>
                          <option value="2">F2</option>
                          <option value="3">F3</option>
                        </select>
                        {comparison.data.families.length > 0 && (
                          <>
                            <label htmlFor="route-family">Similar steps</label>
                            <select
                              id="route-family"
                              className="input"
                              value={familyId ?? ""}
                              onChange={(event) => {
                                setFamilyId(event.target.value || null);
                                setCursors([null]);
                              }}
                            >
                              <option value="">All families</option>
                              {comparison.data.families.map((family) => (
                                <option key={family.family_id} value={family.family_id}>
                                  Steps like Route {family.best_schedule + 1}:{" "}
                                  {family.schedule_count}{" "}
                                  {family.schedule_count === 1 ? "route" : "routes"}
                                  {family.best_layer === null ? "" : `, best F${family.best_layer}`}
                                </option>
                              ))}
                            </select>
                            {comparison.data.families_shown < comparison.data.families_total && (
                              <p className="small muted">
                                Showing {comparison.data.families_shown} of{" "}
                                {comparison.data.families_total} groups. The archive still keeps
                                every route.
                              </p>
                            )}
                          </>
                        )}
                        <label>
                          <input
                            type="checkbox"
                            checked={rerank}
                            onChange={(event) => {
                              setRerank(event.target.checked);
                              setCursors([null]);
                            }}
                          />{" "}
                          Show ranks within this view beside recorded ranks
                        </label>
                      </div>
                    </details>
                    {schedules.data === undefined && schedules.error ? (
                      <RequestFailure error={schedules.error} />
                    ) : schedules.data === undefined ? (
                      <LoadingState stage="Loading route archive" />
                    ) : (
                      <>
                        <p className="small">
                          {schedules.data.items.length} of {schedules.data.total} routes shown. Cost
                          includes{" "}
                          {comparison.data.basis.objective_basis === "economic"
                            ? "pay you would give up"
                            : "direct spending"}
                          .
                        </p>
                        <ul className="grid gap-12">
                          {schedules.data.items.map((schedule) => (
                            <ScheduleCard
                              key={schedule.index}
                              schedule={schedule}
                              select={inspect}
                              selected={selected === schedule.index}
                              saved={savedIndex === schedule.index}
                              detail={journeyRoutes.find(
                                (route) => route.schedule.index === schedule.index,
                              )}
                            />
                          ))}
                        </ul>
                        {(cursors.length > 1 || schedules.data.next_cursor) && (
                          <div className="flex gap-8">
                            <Button
                              variant="secondary"
                              disabledReason={cursors.length === 1 ? "First page" : undefined}
                              onClick={() => setCursors((current) => current.slice(0, -1))}
                            >
                              Previous
                            </Button>
                            <Button
                              variant="secondary"
                              disabledReason={
                                schedules.data.next_cursor === null ? "Last page" : undefined
                              }
                              onClick={() => {
                                if (schedules.data.next_cursor !== null)
                                  setCursors((current) => [...current, schedules.data.next_cursor]);
                              }}
                            >
                              Next
                            </Button>
                          </div>
                        )}
                      </>
                    )}
                  </section>
                </div>
                {selected !== null &&
                  (detail.data === undefined && detail.error ? (
                    <RequestFailure error={detail.error} />
                  ) : detail.data === undefined ? (
                    <LoadingState stage="Opening this route" />
                  ) : (
                    <div className="grid gap-12">
                      <details className="details">
                        <summary>Full breakdown for Route {selected + 1}</summary>
                        <div className="pt-12">
                          <RouteDetailView detail={detail.data} />
                        </div>
                      </details>
                      {runId !== null &&
                        !changedSince &&
                        !running &&
                        !comparison.isError &&
                        shown === active && (
                          <Link
                            className="btn btn-primary"
                            href={
                              savedIndex === selected
                                ? chapterHref(workspaceId, "plan")
                                : `${chapterHref(workspaceId, "plan")}?solve_run_id=${encodeURIComponent(runId)}&schedule_index=${selected}`
                            }
                          >
                            {savedIndex === selected
                              ? "Review saved plan"
                              : "Choose this route in Plan"}
                          </Link>
                        )}
                    </div>
                  ))}
              </>
            )}
          </>
        )}
      </section>
      <aside className="chapter-landscape" aria-label="Your route landscape">
        {journeyTargets.length > 0 && (
          <RouteExplorer
            targets={journeyTargets}
            startLabel={profile.data?.document.current_role.value ?? "Your starting point"}
            activeTargetId={focusedTarget}
            onTargetChange={(id) => {
              setFocusedTarget(id);
              if (id !== null) setChosenTarget(id);
            }}
            selectedIndex={selected}
            onSelect={(_targetId, index) => inspect(index)}
          />
        )}
        {journeyQueries.some((query) => query.isError) && (
          <div className="grid gap-8">
            <p>Some route steps could not be loaded.</p>
            <Button
              variant="secondary"
              onClick={() => {
                for (const query of journeyQueries) if (query.isError) void query.refetch();
              }}
            >
              Try route details again
            </Button>
          </div>
        )}
        {comparison.data && comparison.data.schedules_total > 0 && (
          <details className="details route-comparison-chart">
            <summary>Compare time and cost</summary>
            <p className="small pt-12">
              Choose a point to inspect the same route in the landscape.
            </p>
            <RouteChart comparison={comparison.data} select={inspect} />
          </details>
        )}
      </aside>
    </div>
  );
}
