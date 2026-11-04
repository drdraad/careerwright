"use client";
import Link from "next/link";
import { type FormEvent, useEffect, useRef, useState } from "react";
import type {
  PlanRevisionPreview,
  PlanSnapshot,
  ReplanPayment,
  RouteDetail,
} from "@/generated/api";
import { chapterHref } from "@/lib/chapters";
import { formatDay, formatMonth, isDayInput, londonToday } from "@/lib/dates";
import { formatMoney, formatSignedMoney, parseMoneyInput } from "@/lib/money";
import { OBJECTIVE_BASIS } from "@/lib/optionWords";
import { downloadPlanCalendar, downloadPlanJson, downloadWorkspace } from "@/lib/planExport";
import {
  type PlanCandidate,
  readPlanCandidate,
  useChoosePlan,
  useCurrentPlan,
  usePlanCandidate,
  usePlanChanges,
  usePlanHistory,
  usePlanRevisionPreview,
  usePlanVersion,
  useRecordPlanProgress,
  useRequestRemainingRouteSolve,
} from "@/lib/planQueries";
import { useCheckpoint, useProfile } from "@/lib/queries";
import { useRouteComparison } from "@/lib/routeQueries";
import { ROUTE_CONDITION } from "@/lib/routeWords";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { PlanProgress } from "./PlanProgress";
import { RouteDetailView } from "./RouteDetailView";
import { RouteJourney } from "./RouteJourney";
import { SyntheticLabel } from "./Status";

function nextAction(plan: PlanSnapshot, omitOwnDetail = false) {
  const completed = plan.progress?.completed_steps ?? [];
  const stepTitle = (variantId: string, title: string) =>
    omitOwnDetail &&
    plan.route.steps.some((step) => step.variant_id === variantId && step.added_by_person)
      ? "your option"
      : title;
  if (plan.progress?.rest_until && plan.next_action === null)
    return `Rest was recorded through ${formatDay(plan.progress.rest_until)}. Review whether to resume planning.`;
  if (plan.next_action !== null) {
    const event = plan.next_action;
    const title = stepTitle(event.variant_id, event.title);
    const action =
      event.kind === "review"
        ? "Review this plan"
        : event.kind === "application_deadline"
          ? `Apply for ${title}`
          : event.kind === "start"
            ? `Check the start of ${title}`
            : `Check the finish of ${title}`;
    return `${action} on ${formatDay(event.on)}. ${event.conditional ? "This depends on a condition being met. " : ""}The date is proposed, not a booking.`;
  }
  const first = plan.route.steps.find((step) => !completed.includes(step.variant_id));
  if (!first && plan.route.steps.length > 0)
    return "You reported every step complete. Review the outcome before making another decision.";
  if (first?.start_date && first.start_date < londonToday())
    return `The proposed start date for ${stepTitle(first.variant_id, first.title ?? "your first step")} has passed. Check its current status and conditions.`;
  if (first?.start_month && first.start_month < londonToday().slice(0, 7))
    return `The planned start month for ${stepTitle(first.variant_id, first.title ?? "your first step")} has passed. Check its current status and conditions.`;
  if (first?.start_month)
    return `Check when ${stepTitle(first.variant_id, first.title ?? "your first step")} can start in ${formatMonth(`${first.start_month}-01`)}. An exact date is not known yet.`;
  if (first)
    return `Check the start date and conditions for ${stepTitle(first.variant_id, first.title ?? "your first step")}.`;
  return "No training step is needed in this model. Check current employer requirements and your evidence before applying.";
}

export function PlanContent({
  plan,
  printOmitFinancial = false,
  printOmitSensitive = false,
}: {
  plan: PlanSnapshot;
  printOmitFinancial?: boolean;
  printOmitSensitive?: boolean;
}) {
  return (
    <div
      className="grid gap-24 plan-print"
      data-print-redacted={printOmitFinancial || printOmitSensitive}
    >
      <section className="grid gap-12" aria-label="Chosen plan overview">
        <p className="small muted">
          Plan version {plan.version} · saved {formatDay(plan.selected_at)}
        </p>
        {(plan.route.basis.synthetic || plan.route.label.synthetic) && <SyntheticLabel />}
        <h2 className="section-title">{plan.target_title}</h2>
        <div className="decision-next-action">
          <h3>Your next action</h3>
          <p>{nextAction(plan)}</p>
        </div>
        {plan.route.steps.length === 0 && (
          <p className="small">
            Review what you can show in{" "}
            <Link href={chapterHref(plan.workspace_id, "skills")}>Skills</Link>, then check current
            openings in <Link href={chapterHref(plan.workspace_id, "roles")}>Roles</Link>.
            Careerwright has not found a suitable vacancy for you.
          </p>
        )}
        <p className="small">
          Choosing this route saved a plan to review. It did not apply, enrol, accept an offer or
          resign for you.
        </p>
        <dl className="figures">
          <div>
            <dt>Modelled route</dt>
            <dd>{plan.route.schedule.months_to_readiness} months</dd>
          </div>
          <div>
            <dt>{OBJECTIVE_BASIS[plan.route.basis.objective_basis]}</dt>
            <dd>{formatSignedMoney(plan.route.schedule.objective_cost)}</dd>
          </div>
        </dl>
        {plan.route.schedule.conditions.length > 0 && (
          <div className="grid gap-4 small">
            <p className="font-semibold">Before this route can go ahead</p>
            <ul className="grid gap-4">
              {plan.route.schedule.conditions.map((condition) => (
                <li key={`${condition.kind}-${condition.variant_id}-${condition.instrument_id}`}>
                  {ROUTE_CONDITION[condition.verification]}.
                </li>
              ))}
            </ul>
          </div>
        )}
        <details className="details small">
          <summary>Search coverage</summary>
          <p className="small pt-12">
            {plan.search.coverage === "complete"
              ? "The search finished within its stated limits."
              : "The search stopped at its limit; other routes may exist."}{" "}
            It compared {plan.search.instance.variants} ways to start across{" "}
            {plan.search.instance.concepts} options and {plan.search.instance.months} months.
          </p>
        </details>
        <details className="details small">
          <summary>About this saved version</summary>
          <p className="pt-12">
            This version uses answers version {plan.source.profile_version} and planning figures
            version {plan.source.inputs_version}. Later edits do not change it.
          </p>
        </details>
        {plan.route.steps.length > 0 && (
          <p className="small">
            Planning progress:{" "}
            {
              plan.route.steps.filter((step) =>
                plan.progress?.completed_steps?.includes(step.variant_id),
              ).length
            }{" "}
            of {plan.route.steps.length} steps reported complete. This does not verify skills or
            qualifications.
          </p>
        )}
      </section>
      <details className="details small">
        <summary>See the full route breakdown</summary>
        <div className="pt-12">
          <RouteDetailView detail={plan.route} />
        </div>
      </details>
      <section className="plan-redacted-print" aria-label="Plan copy with omitted details">
        {(plan.route.basis.synthetic || plan.route.label.synthetic) && <SyntheticLabel />}
        <h2>{plan.target_title}</h2>
        <p>
          Plan version {plan.version}. Next action: {nextAction(plan, printOmitSensitive)}
        </p>
        <p>
          Ready in {plan.route.schedule.months_to_readiness} months. This is a proposed plan, not an
          application or booking.
        </p>
        {!printOmitFinancial && (
          <p>
            {OBJECTIVE_BASIS[plan.route.basis.objective_basis]}:{" "}
            {formatSignedMoney(plan.route.schedule.objective_cost)}.
          </p>
        )}
        {plan.route.schedule.conditions.length > 0 && (
          <ul>
            {plan.route.schedule.conditions.map((condition) => (
              <li key={`${condition.kind}-${condition.variant_id}-${condition.instrument_id}`}>
                {ROUTE_CONDITION[condition.verification]}.
              </li>
            ))}
          </ul>
        )}
        <ol>
          {plan.route.steps.map((step) => (
            <li key={step.variant_id}>
              {printOmitSensitive && step.added_by_person
                ? "Your option"
                : (step.title ?? "Route step")}
              {step.start_date
                ? `, starts ${formatDay(step.start_date)}`
                : step.start_month
                  ? `, starts in ${formatMonth(`${step.start_month}-01`)}`
                  : ", start date not known"}
              .
            </li>
          ))}
        </ol>
        <p>
          {plan.search.coverage === "complete"
            ? "The search completed within its limits."
            : "The search stopped at its limit; other routes may exist."}
        </p>
      </section>
    </div>
  );
}

function RevisionDiff({
  current,
  preview,
}: {
  current: PlanSnapshot;
  preview: PlanRevisionPreview;
}) {
  const before = current.route.steps;
  const after = preview.proposed_route.steps;
  const name = (steps: RouteDetail["steps"], id: string) =>
    steps.find((step) => step.variant_id === id)?.title ?? "A route step";
  const difference = preview.difference;
  return (
    <section className="grid gap-8" aria-label="Proposed plan changes">
      <h2 className="section-title">What would change</h2>
      <p className="small">
        {difference.remaining_horizon_recalculated
          ? `The saved plan stays in place until you choose this route. This comparison covers ${difference.new_basis.horizon_months} remaining months from ${formatMonth(`${difference.new_basis.planning_start}-01`)}. It uses the opening cash, money already paid and future obligations you confirmed. A completion report has not been treated as proof of a skill or qualification.`
          : "The saved plan stays in place until you choose this route. This comparison covers a fresh full horizon; it has not subtracted completed work or costs already paid."}
      </p>
      <dl className="kv">
        <dt>Ready</dt>
        <dd>
          {formatMonth(`${difference.old_readiness_month}-01`)} →{" "}
          {formatMonth(`${difference.new_readiness_month}-01`)}
        </dd>
        <dt>Direct spending</dt>
        <dd>
          {formatMoney(difference.old_direct_cost)} → {formatMoney(difference.new_direct_cost)}
        </dd>
        {difference.old_economic_cost && difference.new_economic_cost && (
          <>
            <dt>Cost including pay difference</dt>
            <dd>
              {formatSignedMoney(difference.old_economic_cost)} →{" "}
              {formatSignedMoney(difference.new_economic_cost)}
            </dd>
          </>
        )}
      </dl>
      {!difference.same_accounting_basis && (
        <p className="small">
          The saved plan covers {difference.old_basis.horizon_months} months from{" "}
          {formatMonth(`${difference.old_basis.planning_start}-01`)}; this proposal covers{" "}
          {difference.new_basis.horizon_months} months from{" "}
          {formatMonth(`${difference.new_basis.planning_start}-01`)}. The costs use different
          accounting bases and are not directly comparable.
        </p>
      )}
      {(difference.added_steps.length > 0 ||
        difference.removed_steps.length > 0 ||
        difference.changed_steps.length > 0) && (
        <ul className="grid gap-4 small">
          {difference.added_steps.map((id) => (
            <li key={`add-${id}`}>Added: {name(after, id)}</li>
          ))}
          {difference.removed_steps.map((id) => (
            <li key={`remove-${id}`}>Removed: {name(before, id)}</li>
          ))}
          {difference.changed_steps.map((id) => (
            <li key={`change-${id}`}>Changed: {name(after, id)}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function CandidatePreview({
  route,
  revision,
  current,
  onConfirm,
  confirmed,
  setConfirmed,
  accountingAcknowledged,
  setAccountingAcknowledged,
  saving,
  error,
}: {
  route: RouteDetail;
  revision: PlanRevisionPreview | null;
  current: PlanSnapshot | null;
  onConfirm(): void;
  confirmed: boolean;
  setConfirmed(value: boolean): void;
  accountingAcknowledged: boolean;
  setAccountingAcknowledged(value: boolean): void;
  saving: boolean;
  error: unknown;
}) {
  const accountingRequired =
    (current?.progress?.completed_steps?.length ?? 0) > 0 && route.basis.replan == null;
  return (
    <section className="grid gap-16" aria-label="Route to choose">
      <h2 className="section-title">Review this route before choosing it</h2>
      <p className="small">
        The conditions, assumptions and figures below are the ones this saved plan will keep.
        Choosing it does not apply, enrol, accept an offer or resign for you.
      </p>
      {current && revision && <RevisionDiff current={current} preview={revision} />}
      <RouteDetailView detail={route} />
      <label className="flex items-start gap-8">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(event) => setConfirmed(event.target.checked)}
        />
        <span>I have reviewed this route's conditions, unknowns and costs.</span>
      </label>
      {accountingRequired && (
        <label className="flex items-start gap-8">
          <input
            type="checkbox"
            checked={accountingAcknowledged}
            onChange={(event) => setAccountingAcknowledged(event.target.checked)}
          />
          <span>
            I understand this is a fresh full-horizon comparison. Completed steps and costs already
            paid have not been subtracted.
          </span>
        </label>
      )}
      <div>
        <Button
          variant="primary"
          disabledReason={
            !confirmed
              ? "Review and confirm the route first"
              : accountingRequired && !accountingAcknowledged
                ? "Acknowledge the full-horizon comparison first"
                : saving
                  ? "Saving…"
                  : undefined
          }
          onClick={onConfirm}
        >
          Save this plan
        </Button>
      </div>
      {error != null && <RequestFailure error={error} />}
    </section>
  );
}

const monthNumber = (value: string) => {
  const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(value);
  return match ? Number(match[1]) * 12 + Number(match[2]) - 1 : Number.NaN;
};
const monthText = (number: number) =>
  `${Math.floor(number / 12)}-${String((number % 12) + 1).padStart(2, "0")}`;

type PaymentRow = { id: string; variantId: string; due: string; amount: string };

function RemainingReplan({ plan, workspaceId }: { plan: PlanSnapshot; workspaceId: string }) {
  const checkpoint = useCheckpoint(workspaceId);
  const request = useRequestRemainingRouteSolve(workspaceId);
  const originalEnd =
    monthNumber(plan.route.basis.planning_start) + plan.route.basis.horizon_months;
  const firstMonth = monthText(
    Math.max(monthNumber(plan.route.basis.planning_start), monthNumber(londonToday().slice(0, 7))),
  );
  const lastMonth = monthText(originalEnd - 1);
  const [start, setStart] = useState(firstMonth);
  const [cash, setCash] = useState("");
  const [paid, setPaid] = useState("");
  const [payments, setPayments] = useState<PaymentRow[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [formError, setFormError] = useState("");
  const oldIds = [
    ...new Set([
      ...(plan.progress?.completed_steps ?? []),
      ...(plan.route.basis.replan?.excluded_variants ?? []),
    ]),
  ];
  const labelFor = (id: string) =>
    plan.route.steps.find((step) => step.variant_id === id)?.title ?? "Earlier committed step";
  const unfinishedCommitment = plan.commitments?.find(
    (id) => !plan.progress?.completed_steps?.includes(id),
  );
  const remainingMonths = originalEnd - monthNumber(start);
  const updatePayment = (id: string, change: Partial<PaymentRow>) =>
    setPayments((rows) => rows.map((row) => (row.id === id ? { ...row, ...change } : row)));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setFormError("");
    const openingCash = parseMoneyInput(cash, "GBP");
    const sunkPaid = parseMoneyInput(paid, "GBP");
    if (
      checkpoint.data === undefined ||
      !confirmed ||
      !Number.isInteger(remainingMonths) ||
      remainingMonths < 1 ||
      remainingMonths > 24 ||
      start < firstMonth ||
      !openingCash.ok ||
      !sunkPaid.ok
    ) {
      setFormError("Check the start month, both amounts and the payment confirmation.");
      return;
    }
    const remainingPayments: ReplanPayment[] = [];
    for (const row of payments) {
      const amount = parseMoneyInput(row.amount, "GBP");
      if (
        !oldIds.includes(row.variantId) ||
        !isDayInput(row.due) ||
        row.due.slice(0, 7) < start ||
        !amount.ok
      ) {
        setFormError("Check every remaining payment's step, date and amount.");
        return;
      }
      remainingPayments.push({ variant_id: row.variantId, due: row.due, amount: amount.money });
    }
    if (
      new Set(remainingPayments.map((payment) => `${payment.variant_id}:${payment.due}`)).size !==
      remainingPayments.length
    ) {
      setFormError("Combine payments for the same step and date.");
      return;
    }
    request.mutate({
      expected_inputs_version: checkpoint.data.inputs_version,
      expected_plan_version: plan.version,
      target: plan.target_title,
      planning_start: start,
      horizon_months: remainingMonths,
      opening_cash: openingCash.money,
      sunk_paid: sunkPaid.money,
      remaining_payments: remainingPayments,
      all_remaining_payments_confirmed: true,
      no_ongoing_steps_confirmed: true,
    });
  };

  return (
    <details className="details plan-actions">
      <summary>Recalculate the months left</summary>
      <div className="grid gap-12 pt-12">
        <p className="small">
          Search the rest of this plan's original window, which ends after{" "}
          {formatMonth(`${lastMonth}-01`)}. Completed steps will not be repeated. A completion
          report does not verify a skill or qualification.
        </p>
        {originalEnd <= monthNumber(londonToday().slice(0, 7)) ? (
          <p>The original planning window has ended. Start a fresh comparison in Routes.</p>
        ) : unfinishedCommitment ? (
          <p>
            You recorded a commitment to {labelFor(unfinishedCommitment)} and have not reported it
            complete. Careerwright cannot carry an unfinished commitment into a recalculation.
            Review this plan manually until that step has finished.
          </p>
        ) : checkpoint.data === undefined && checkpoint.error ? (
          <RequestFailure error={checkpoint.error} />
        ) : checkpoint.data === undefined ? (
          <LoadingState stage="Checking current planning inputs" />
        ) : (
          <form className="grid gap-12" onSubmit={submit}>
            <label className="grid gap-4">
              Start of the remaining comparison
              <input
                className="input"
                type="month"
                min={firstMonth}
                max={lastMonth}
                required
                value={start}
                onChange={(event) => setStart(event.target.value)}
              />
            </label>
            <p className="small muted">
              {Number.isInteger(remainingMonths) && remainingMonths > 0
                ? `${remainingMonths} months remain through ${formatMonth(`${lastMonth}-01`)}.`
                : "Choose a month within the saved plan's original window."}
            </p>
            <label className="grid gap-4">
              Cash available at the start, in pounds
              <input
                className="input"
                inputMode="decimal"
                required
                value={cash}
                onChange={(event) => setCash(event.target.value)}
              />
            </label>
            <label className="grid gap-4">
              Money already paid for this plan, in pounds
              <input
                className="input"
                inputMode="decimal"
                required
                value={paid}
                onChange={(event) => setPaid(event.target.value)}
              />
            </label>
            <p className="small">
              Enter 0 explicitly if none. Money already paid is disclosed separately and is not
              charged again against the remaining budget.
            </p>
            <fieldset className="grid gap-8">
              <legend>Payments still due for completed or earlier committed steps</legend>
              {payments.map((row) => (
                <div key={row.id} className="grid gap-8 card-on-space p-12">
                  <label className="grid gap-4">
                    Step
                    <select
                      className="input"
                      value={row.variantId}
                      onChange={(event) => updatePayment(row.id, { variantId: event.target.value })}
                    >
                      {oldIds.map((id) => (
                        <option key={id} value={id}>
                          {labelFor(id)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="grid gap-4">
                    Due date
                    <input
                      className="input"
                      type="date"
                      min={`${start}-01`}
                      required
                      value={row.due}
                      onChange={(event) => updatePayment(row.id, { due: event.target.value })}
                    />
                  </label>
                  <label className="grid gap-4">
                    Amount in pounds
                    <input
                      className="input"
                      inputMode="decimal"
                      required
                      value={row.amount}
                      onChange={(event) => updatePayment(row.id, { amount: event.target.value })}
                    />
                  </label>
                  <Button
                    variant="quiet"
                    onClick={() => setPayments((rows) => rows.filter((item) => item.id !== row.id))}
                  >
                    Remove payment
                  </Button>
                </div>
              ))}
              {oldIds[0] !== undefined && (
                <Button
                  variant="secondary"
                  onClick={() =>
                    setPayments((rows) => [
                      ...rows,
                      { id: crypto.randomUUID(), variantId: oldIds[0] ?? "", due: "", amount: "" },
                    ])
                  }
                >
                  Add a remaining payment
                </Button>
              )}
            </fieldset>
            <p className="small">
              A payment on an unfinished step cannot yet be modelled. Keep the current plan and
              review that step manually if one is due. Payments after the remaining window still
              count toward total direct spending, but not monthly cash or payment limits.
            </p>
            <label className="flex items-start gap-8">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
              />
              <span>
                I have listed every remaining payment for finished or earlier committed steps, and
                no unfinished step is underway, committed or has a remaining payment.
              </span>
            </label>
            <Button
              type="submit"
              variant="secondary"
              disabledReason={request.isPending ? "Starting the search…" : undefined}
            >
              Search the months left
            </Button>
            {formError && <p role="alert">{formError}</p>}
            {request.error && <RequestFailure error={request.error} />}
            {request.data && (
              <p role="status">
                Remaining-month search started.{" "}
                <Link
                  href={`${chapterHref(workspaceId, "routes")}?target=${encodeURIComponent(plan.target_title)}`}
                >
                  Open Routes
                </Link>{" "}
                to review the result before saving a new plan.
              </p>
            )}
          </form>
        )}
      </div>
    </details>
  );
}

export function PlanChapter({ workspaceId }: { workspaceId: string }) {
  const current = useCurrentPlan(workspaceId);
  const profile = useProfile(workspaceId);
  const [candidate, setCandidate] = useState<PlanCandidate | null>(null);
  const [badLink, setBadLink] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [accountingAcknowledged, setAccountingAcknowledged] = useState(false);
  const [historyVersion, setHistoryVersion] = useState<number | null>(null);
  const [omitFinancial, setOmitFinancial] = useState(false);
  const [omitSensitive, setOmitSensitive] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);
  const [exportError, setExportError] = useState<unknown>(null);
  const printable = useRef<HTMLDivElement>(null);
  const plan = current.data ?? null;
  const preview = usePlanCandidate(workspaceId, candidate);
  const candidateComparison = useRouteComparison(
    workspaceId,
    candidate?.runId ?? null,
    candidate !== null,
  );
  const revision = usePlanRevisionPreview(workspaceId, candidate, plan !== null);
  const changes = usePlanChanges(workspaceId, plan !== null);
  const history = usePlanHistory(workspaceId, plan !== null);
  const older = usePlanVersion(workspaceId, historyVersion);
  const choose = useChoosePlan(workspaceId);
  const progress = useRecordPlanProgress(workspaceId);

  useEffect(() => {
    const search = window.location.search;
    const selection = readPlanCandidate(search);
    const params = new URLSearchParams(search);
    setCandidate(selection);
    setBadLink((params.has("solve_run_id") || params.has("schedule_index")) && selection === null);
  }, []);
  useEffect(() => {
    let closed: HTMLDetailsElement[] = [];
    const open = () => {
      closed = [
        ...(printable.current?.querySelectorAll<HTMLDetailsElement>("details:not([open])") ?? []),
      ];
      for (const item of closed) item.open = true;
    };
    const restore = () => {
      for (const item of closed) item.open = false;
      closed = [];
    };
    window.addEventListener("beforeprint", open);
    window.addEventListener("afterprint", restore);
    return () => {
      window.removeEventListener("beforeprint", open);
      window.removeEventListener("afterprint", restore);
      restore();
    };
  }, []);

  const save = () => {
    if (
      !confirmed ||
      ((plan?.progress?.completed_steps?.length ?? 0) > 0 &&
        preview.data?.route?.basis.replan == null &&
        !accountingAcknowledged) ||
      candidate === null ||
      preview.data?.route === null ||
      !preview.data?.route ||
      (plan !== null && revision.data?.from_version !== plan.version) ||
      current.data === undefined
    )
      return;
    choose.mutate(
      {
        expected_version: current.data?.version ?? 0,
        solve_run_id: candidate.runId,
        schedule_index: candidate.index,
        assumptions_confirmed: true,
        ...((plan?.progress?.completed_steps?.length ?? 0) > 0 &&
        preview.data.route.basis.replan == null
          ? { full_horizon_accounting_acknowledged: true }
          : {}),
      },
      {
        onSuccess: () => {
          setCandidate(null);
          setAccountingAcknowledged(false);
          window.history.replaceState({}, "", window.location.pathname);
        },
      },
    );
  };

  const runExport = async (name: string, work: () => Promise<void>) => {
    setExporting(name);
    setExportError(null);
    try {
      await work();
    } catch (error) {
      setExportError(error);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="chapter-layout plan-chapter">
      <section className="chapter-reading">
        <header className="chapter-heading">
          <h1 className="page-title">{candidate ? "Review this plan" : "Your next step"}</h1>
          <p>
            {candidate
              ? "Check the demands and conditions before saving."
              : "A proposed route, with one practical action to take next."}
          </p>
        </header>
        {current.data === undefined && current.error ? (
          <RequestFailure
            error={current.error}
            actions={
              <Button variant="secondary" onClick={() => void current.refetch()}>
                Try again
              </Button>
            }
          />
        ) : current.data === undefined ? (
          <LoadingState stage="Checking for a saved plan" />
        ) : (
          <>
            {badLink && (
              <p role="alert">
                This route link is incomplete. Open Routes and choose a route again.
              </p>
            )}
            {candidate &&
              (preview.data === undefined && preview.error ? (
                <RequestFailure error={preview.error} />
              ) : preview.data === undefined ? (
                <LoadingState stage="Opening the route to choose" />
              ) : preview.data.route === null ? (
                <p>This route search has not finished. Open Routes to check it.</p>
              ) : plan !== null && revision.data === undefined && revision.error ? (
                <RequestFailure error={revision.error} />
              ) : plan !== null && revision.data === undefined ? (
                <LoadingState stage="Comparing this route with your saved plan" />
              ) : plan !== null && revision.data?.from_version !== plan.version ? (
                <p>Your saved plan changed while this route was open. Reload before choosing it.</p>
              ) : (
                <CandidatePreview
                  route={preview.data.route}
                  revision={revision.data ?? null}
                  current={plan}
                  confirmed={confirmed}
                  setConfirmed={setConfirmed}
                  accountingAcknowledged={accountingAcknowledged}
                  setAccountingAcknowledged={setAccountingAcknowledged}
                  saving={choose.isPending}
                  error={choose.error}
                  onConfirm={save}
                />
              ))}
            {!candidate &&
              (plan === null ? (
                <p>
                  No plan has been chosen yet. Compare the computed routes, then choose one to save.{" "}
                  <Link href={chapterHref(workspaceId, "routes")}>Open Routes</Link>
                </p>
              ) : (
                <>
                  <div ref={printable}>
                    <PlanContent
                      plan={plan}
                      printOmitFinancial={omitFinancial}
                      printOmitSensitive={omitSensitive}
                    />
                  </div>
                  {changes.data?.new_solve_needed && changes.data.plan_version === plan.version && (
                    <section
                      className="grid gap-8 plan-actions"
                      aria-label="Changes since this plan"
                    >
                      <h2 className="section-title">Some answers or sources changed</h2>
                      <p className="small">
                        The saved plan stays as it was. These changes may affect unfinished steps;
                        compare routes again before choosing a revision.
                      </p>
                      <ul className="grid gap-4 small">
                        {changes.data.possibly_affected_steps.map((id) => (
                          <li key={id}>
                            {plan.route.steps.find((step) => step.variant_id === id)?.title ??
                              "A step"}{" "}
                            may need review.
                          </li>
                        ))}
                      </ul>
                      <Link href={chapterHref(workspaceId, "routes")}>Compare routes again</Link>
                    </section>
                  )}
                  {changes.error && <RequestFailure error={changes.error} />}
                  <details className="details plan-actions">
                    <summary>Update your progress</summary>
                    <div className="pt-12">
                      <PlanProgress
                        key={plan.version}
                        plan={plan}
                        onUpdate={(update) => progress.mutate(update)}
                        busy={progress.isPending}
                        error={progress.error}
                      />
                    </div>
                  </details>
                  <RemainingReplan
                    key={`replan-${plan.version}`}
                    plan={plan}
                    workspaceId={workspaceId}
                  />
                  <details className="details small plan-actions">
                    <summary>Saved plan versions</summary>
                    <div className="grid gap-12 pt-12">
                      {history.data === undefined && history.error ? (
                        <RequestFailure error={history.error} />
                      ) : history.data === undefined ? (
                        <LoadingState stage="Loading plan versions" />
                      ) : (
                        <ol className="grid gap-8">
                          {history.data.map((item) => (
                            <li key={item.version}>
                              <Button
                                variant="quiet"
                                onClick={() => setHistoryVersion(item.version)}
                              >
                                Version {item.version}: {item.target_title}, saved{" "}
                                {formatDay(item.selected_at)}
                              </Button>{" "}
                              <span className="muted">
                                {item.completed_steps} steps reported complete
                              </span>
                            </li>
                          ))}
                        </ol>
                      )}
                      {historyVersion !== null &&
                        (older.data === undefined && older.error ? (
                          <RequestFailure error={older.error} />
                        ) : older.data === undefined ? (
                          <LoadingState stage="Opening this saved version" />
                        ) : (
                          <dl className="kv">
                            <dt>Version {older.data.version}</dt>
                            <dd>{older.data.target_title}</dd>
                            <dt>Modelled route</dt>
                            <dd>{older.data.route.schedule.months_to_readiness} months</dd>
                            <dt>{OBJECTIVE_BASIS[older.data.route.basis.objective_basis]}</dt>
                            <dd>{formatSignedMoney(older.data.route.schedule.objective_cost)}</dd>
                            <dt>Steps reported complete</dt>
                            <dd>{older.data.progress?.completed_steps?.length ?? 0}</dd>
                          </dl>
                        ))}
                    </div>
                  </details>
                  <section className="grid gap-12 plan-actions" aria-label="Plan exports">
                    <h2 className="section-title">Keep or share a copy</h2>
                    <div className="flex flex-wrap gap-8">
                      <Button variant="secondary" onClick={() => window.print()}>
                        Print this plan
                      </Button>
                      <Button
                        variant="secondary"
                        disabledReason={exporting ? "A download is in progress" : undefined}
                        onClick={() =>
                          void runExport("plan", () =>
                            downloadPlanJson(workspaceId, plan.version, {
                              financial: omitFinancial,
                              sensitive: omitSensitive,
                            }),
                          )
                        }
                      >
                        Download plan JSON
                      </Button>
                      <Button
                        variant="secondary"
                        disabledReason={exporting ? "A download is in progress" : undefined}
                        onClick={() =>
                          void runExport("calendar", () =>
                            downloadPlanCalendar(workspaceId, plan.version),
                          )
                        }
                      >
                        Download proposed calendar dates
                      </Button>
                    </div>
                    <div className="grid gap-4 small">
                      <label>
                        <input
                          type="checkbox"
                          checked={omitFinancial}
                          onChange={(event) => setOmitFinancial(event.target.checked)}
                        />{" "}
                        Leave financial detail out of the plan JSON and print
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={omitSensitive}
                          onChange={(event) => setOmitSensitive(event.target.checked)}
                        />{" "}
                        Hide own option names, providers, requirements and source excerpts in the
                        plan JSON and print
                      </label>
                    </div>
                    <p className="small muted">
                      Calendar dates are proposed, and only exact dates are included. The whole
                      workspace export below includes full detail.
                    </p>
                    {exportError != null && <RequestFailure error={exportError} />}
                  </section>
                </>
              ))}
            <div className="plan-actions">
              <Button
                variant="quiet"
                disabledReason={exporting ? "A download is in progress" : undefined}
                onClick={() => void runExport("workspace", () => downloadWorkspace(workspaceId))}
              >
                Download whole workspace
              </Button>
            </div>
          </>
        )}
      </section>
      <aside className="chapter-landscape plan-actions" aria-label="Plan journey">
        {(candidate ? preview.data?.route : plan?.route) && (
          <>
            <h2>{candidate ? "Route under review" : "Your saved route"}</h2>
            <p className="small">
              {candidate
                ? "Preview only. Saving is a separate choice."
                : "Inspect a step to see its dates, conditions and sources."}
            </p>
            <RouteJourney
              routes={[(candidate ? preview.data?.route : plan?.route) as RouteDetail]}
              targetTitle={
                candidate
                  ? (preview.data?.solve.target_title ?? "Your target")
                  : (plan?.target_title ?? "Your target")
              }
              startLabel={profile.data?.document.current_role.value ?? "Your starting point"}
              selectedIndex={(candidate ? preview.data?.route : plan?.route)?.schedule.index ?? 0}
              initialExpandedIndex={(candidate ? preview.data?.route : plan?.route)?.schedule.index}
              onSelect={() => {}}
              planIndex={candidate ? undefined : plan?.source.schedule_index}
              completedSteps={candidate ? undefined : plan?.progress?.completed_steps}
              status={
                candidate
                  ? candidateComparison.isError
                    ? "error"
                    : !candidateComparison.data
                      ? "pending"
                      : Object.values(candidateComparison.data.changed_since).some(Boolean)
                        ? "stale"
                        : "available"
                  : changes.isError
                    ? "error"
                    : !changes.data || changes.data.plan_version !== plan?.version
                      ? "pending"
                      : changes.data.new_solve_needed
                        ? "stale"
                        : "available"
              }
            />
          </>
        )}
      </aside>
    </div>
  );
}
