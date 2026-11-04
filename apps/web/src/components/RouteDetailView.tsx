"use client";
import type {
  Citation,
  Condition,
  Finding,
  Liability,
  Money,
  RouteDetail,
  RouteStep,
  ScenarioCheck,
  SignedMoney,
  StepQualification,
} from "@/generated/api";
import { formatDay, formatMonth } from "@/lib/dates";
import { formatMoney, formatSignedMoney } from "@/lib/money";
import {
  ACTION_KIND,
  AWARD_STATE,
  ELIGIBILITY_STATUS,
  FEE_LOAN_KIND,
  INSTRUMENT_KIND,
  NOT_KNOWN,
  OBJECTIVE_BASIS,
  RECORD_STATE,
  SUPPLIED_FACT,
  suppliedLabel,
} from "@/lib/optionWords";
import {
  findingWords,
  ROUTE_CONDITION,
  ROUTE_QUALIFICATION,
  ROUTE_VERDICT,
} from "@/lib/routeWords";
import { useEvidence } from "./EvidenceDrawer";
import { StatusBadge, SyntheticLabel } from "./Status";

const money = (value: Money | null) => (value === null ? NOT_KNOWN : formatMoney(value));
const signed = (value: SignedMoney | null) =>
  value === null ? NOT_KNOWN : formatSignedMoney(value);
const month = (value: string | null) => (value === null ? NOT_KNOWN : formatMonth(`${value}-01`));
const day = (value: string | null) => (value === null ? NOT_KNOWN : formatDay(value));
const findingKey = (finding: Finding) =>
  `${finding.code}-${finding.month}-${finding.variant_id}-${finding.amount}-${finding.limit}`;

const STEP_QUALIFICATION: Record<StepQualification, string> = {
  proposed_record: "This record has not been reviewed",
  accepted_assumption: "Uses an assumption you accepted",
  own_option: "This is an option you added, not reviewed",
  supplied_figures: `Uses ${suppliedLabel}`,
  synthetic: "Uses made-up demo data",
};

const RECORD: Record<RouteStep["records"][number]["record"], string> = {
  concept: "Step",
  offering: "Course or job",
  support: "Funding",
  fee_loan: "Fee loan",
};

const PAYMENT: Record<RouteStep["payments"][number]["kind"], string> = {
  fee: "Fee",
  instalment: "Instalment",
  extra: "Other payment",
};

const SCENARIO: Record<ScenarioCheck["scenario"], string> = {
  base: "As planned",
  delay: "If the start is delayed",
  no_award: "Without a funding award",
  no_offer: "Without a job offer",
};

const GATE: Record<Condition["kind"], string> = {
  offer: "A job offer must be accepted",
  award: "Funding must be awarded",
  application: "A place must be confirmed",
  loan: "A loan must be approved and repaid later",
};

function EvidenceBody({ citations }: { citations: Citation[] }) {
  return (
    <ol className="grid gap-12">
      {citations.map((citation) => (
        <li
          key={`${citation.basis}-${citation.claim_id}-${citation.source_id}-${citation.locator}-${citation.excerpt}`}
          className="grid gap-4"
        >
          <p className="small font-semibold">
            {citation.basis === "person"
              ? "What you supplied"
              : citation.basis === "fixture"
                ? "Made-up demo data"
                : "Source page"}
          </p>
          {citation.excerpt !== null && citation.excerpt !== undefined && (
            <blockquote className="small">“{citation.excerpt}”</blockquote>
          )}
          {citation.locator && <p className="small">Where: {citation.locator}</p>}
          {citation.retrieved_on && (
            <p className="small">Careerwright read this on {formatDay(citation.retrieved_on)}</p>
          )}
          {citation.source_url && (
            <a href={citation.source_url} target="_blank" rel="noopener noreferrer nofollow">
              Open source page
            </a>
          )}
        </li>
      ))}
    </ol>
  );
}

function StepCard({ step }: { step: RouteStep }) {
  const evidence = useEvidence();
  const title = step.title ?? ACTION_KIND[step.kind];
  const start = step.start_date
    ? formatDay(step.start_date)
    : step.start_month
      ? month(step.start_month)
      : "Start not known yet";
  const finish = step.finish_date
    ? formatDay(step.finish_date)
    : step.finish_month
      ? month(step.finish_month)
      : "finish not known yet";
  return (
    <li className="card-on-reading grid gap-8 p-16">
      <div className="flex flex-wrap items-start justify-between gap-8">
        <div>
          <h4 className="font-semibold">{title}</h4>
          <p className="small muted">{ACTION_KIND[step.kind]}</p>
        </div>
        {step.sources.length > 0 && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() =>
              evidence.open({
                title: `Evidence for ${title}`,
                body: <EvidenceBody citations={step.sources} />,
              })
            }
          >
            See evidence
          </button>
        )}
      </div>
      <p className="small">
        {start} to {finish}
        {step.provider ? ` · ${step.provider}` : ""}
      </p>
      {step.weekly_hours !== null && <p className="small">{step.weekly_hours} hours a week</p>}
      {step.payments.map((payment) => (
        <p
          key={`${payment.kind}-${payment.month}-${payment.due}-${payment.amount.minor_units}`}
          className="small"
        >
          {PAYMENT[payment.kind]}: {formatMoney(payment.amount)}
          {payment.due
            ? ` on ${formatDay(payment.due)}`
            : payment.month
              ? ` in ${month(payment.month)}`
              : ""}
        </p>
      ))}
      {step.fee_loan !== null && (
        <p className="small">
          {FEE_LOAN_KIND[step.fee_loan.kind]}: amount paid to the provider{" "}
          {money(step.fee_loan.amount)}. This is a loan to repay later. Your eligibility answer:{" "}
          {ELIGIBILITY_STATUS[step.fee_loan.eligibility]}. Application:{" "}
          {AWARD_STATE[step.fee_loan.application]}.
        </p>
      )}
      {step.supports.map((support) => (
        <p key={support.instrument_id} className="small">
          {INSTRUMENT_KIND[support.kind]}: amount paid to the {support.paid_to}{" "}
          {money(support.amount)}. Your eligibility answer:{" "}
          {ELIGIBILITY_STATUS[support.eligibility]}. Award: {AWARD_STATE[support.award]}.
        </p>
      ))}
      {step.work_pattern !== null && (
        <p className="small">
          Work while doing this: {step.work_pattern.hours_per_week} hours a week,{" "}
          {formatMoney(step.work_pattern.net_income)} take-home pay a month.
        </p>
      )}
      {step.wage !== null && (
        <p className="small">
          After an accepted offer: {formatMoney(step.wage)} take-home pay a month.
        </p>
      )}
      {step.application_deadline && (
        <p className="small">Apply by {formatDay(step.application_deadline)}.</p>
      )}
      {step.qualified_by.length > 0 && (
        <ul className="grid gap-4 small">
          {step.qualified_by.map((reason) => (
            <li key={reason}>{STEP_QUALIFICATION[reason]}.</li>
          ))}
        </ul>
      )}
      {step.supplied.length > 0 && (
        <p className="small">
          Your figures, not checked:{" "}
          {step.supplied.map((fact) => SUPPLIED_FACT[fact].toLowerCase()).join(", ")}.
        </p>
      )}
      {step.records.length > 0 && (
        <p className="small muted">
          {step.records
            .map((record) => `${RECORD[record.record]}: ${RECORD_STATE[record.review_state]}`)
            .join(" · ")}
          {step.as_of ? ` · Page read ${formatDay(step.as_of)}` : ""}
        </p>
      )}
    </li>
  );
}

function Timeline({ detail }: { detail: RouteDetail }) {
  if (detail.months.length === 0 || detail.steps.length === 0)
    return <p className="small">No dated steps in this result.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="small tnum min-w-max">
        <caption className="sr-only">When each step is active in the monthly model</caption>
        <thead>
          <tr>
            <th scope="col" className="pr-12 text-left">
              Step
            </th>
            {detail.months.map((row) => (
              <th key={row.month} scope="col" className="px-4 text-center">
                {month(row.month)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {detail.steps.map((step) => (
            <tr key={step.variant_id}>
              <th scope="row" className="pr-12 text-left font-normal">
                {step.title ?? ACTION_KIND[step.kind]}
              </th>
              {detail.months.map((row) => (
                <td key={row.month} className="px-4 text-center">
                  <span aria-hidden="true">
                    {step.active_months.includes(row.month) ? "●" : "·"}
                  </span>
                  <span className="sr-only">
                    {step.active_months.includes(row.month) ? "Active" : "Not active"}
                  </span>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MonthTable({ detail }: { detail: RouteDetail }) {
  const economic = detail.basis.objective_basis === "economic";
  return (
    <div className="overflow-x-auto">
      <table className="small tnum min-w-max">
        <caption className="sr-only">Money in each month of this route</caption>
        <thead>
          <tr>
            {[
              "Month",
              "Cash at start",
              "Early receipts",
              "Take-home pay",
              ...(economic
                ? ["Pay if you followed your other path", "Pay difference from that path"]
                : []),
              "You pay",
              "Paid to provider",
              "Funding",
              "Living costs",
              "Debt repayments",
              "Lowest cash before late receipts",
              "Late receipts",
              "Cash at end",
            ].map((heading) => (
              <th key={heading} scope="col" className="px-8 text-left">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {detail.months.map((row) => (
            <tr key={row.month}>
              <th scope="row" className="px-8 text-left">
                {month(row.month)}
              </th>
              <td className="px-8">{signed(row.opening)}</td>
              <td className="px-8">{money(row.early_receipts)}</td>
              <td className="px-8">{money(row.route_income)}</td>
              {economic && <td className="px-8">{money(row.baseline_income)}</td>}
              {economic && <td className="px-8">{signed(row.pay_difference)}</td>}
              <td className="px-8">{money(row.payments)}</td>
              <td className="px-8">{money(row.paid_to_provider)}</td>
              <td className="px-8">{money(row.support)}</td>
              <td className="px-8">{formatMoney(row.living)}</td>
              <td className="px-8">{formatMoney(row.debt_service)}</td>
              <td className="px-8">{signed(row.lower_bound)}</td>
              <td className="px-8">{money(row.later_receipts)}</td>
              <td className="px-8">{signed(row.closing)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Liabilities({ title, items }: { title: string; items: Liability[] }) {
  if (items.length === 0) return null;
  return (
    <div className="grid gap-4">
      <h4 className="font-semibold">{title}</h4>
      <ul className="grid gap-4 small">
        {items.map((item) => (
          <li key={`${item.variant_id}-${item.due}-${item.amount.minor_units}`}>
            {formatMoney(item.amount)}
            {item.due ? ` due ${day(item.due)}` : ", due date not known yet"}.
          </li>
        ))}
      </ul>
    </div>
  );
}

function Scenario({
  check,
  objectiveBasis,
}: {
  check: ScenarioCheck;
  objectiveBasis: RouteDetail["basis"]["objective_basis"];
}) {
  return (
    <li className="grid gap-4">
      <h4 className="font-semibold">{SCENARIO[check.scenario]}</h4>
      <p className="small">
        {check.same_as_base ? "Same result as the route above." : ROUTE_VERDICT[check.verdict]}
      </p>
      {!check.same_as_base && (
        <p className="small">
          Ready:{" "}
          {check.months_to_readiness === null ? NOT_KNOWN : `${check.months_to_readiness} months`};{" "}
          {OBJECTIVE_BASIS[objectiveBasis]}: {signed(check.objective_cost)}.
        </p>
      )}
      {check.findings.length > 0 && (
        <ul className="grid gap-4 small">
          {check.findings.map((finding) => (
            <li key={findingKey(finding)}>{findingWords(finding)}</li>
          ))}
        </ul>
      )}
    </li>
  );
}

export function RouteDetailView({ detail }: { detail: RouteDetail }) {
  const { schedule, costs } = detail;
  return (
    <section className="grid gap-16" aria-labelledby="selected-route-title">
      <div className="grid gap-8">
        <div className="flex flex-wrap items-center gap-8">
          <h2 id="selected-route-title" className="section-title">
            Route {schedule.index + 1}
          </h2>
          {(detail.basis.synthetic || detail.label.synthetic) && <SyntheticLabel />}
        </div>
        <p className="small">{ROUTE_VERDICT[schedule.verdict]}.</p>
        <dl className="figures">
          <div>
            <dt>Ready in</dt>
            <dd>{schedule.months_to_readiness} months</dd>
          </div>
          <div>
            <dt>{OBJECTIVE_BASIS[detail.basis.objective_basis]}</dt>
            <dd>{formatSignedMoney(schedule.objective_cost)}</dd>
          </div>
        </dl>
        {schedule.conditions.length > 0 && (
          <div className="grid gap-4">
            {schedule.conditions.map((condition) => (
              <StatusBadge
                key={`${condition.kind}-${condition.variant_id}-${condition.instrument_id}`}
                state="conditional"
                detail={ROUTE_CONDITION[condition.verification]}
              />
            ))}
          </div>
        )}
        {schedule.qualifications.length > 0 && (
          <ul className="grid gap-4 small">
            {schedule.qualifications.map((reason) => (
              <li key={reason}>{ROUTE_QUALIFICATION[reason]}.</li>
            ))}
          </ul>
        )}
        {costs.loans_to_repay.map((loan) => (
          <p
            key={`${loan.variant_id}-${loan.kind}-${loan.due}-${loan.amount?.minor_units}`}
            className="small"
          >
            {loan.kind ? FEE_LOAN_KIND[loan.kind] : "Fee loan"}: amount paid straight to the
            provider {money(loan.amount)}. This is a loan you repay later, not your own spending or
            a grant.
            {loan.conditional ? " It still needs approval." : ""} Repayment:{" "}
            {money(loan.repayment ?? null)}.
          </p>
        ))}
      </div>

      <details className="details small">
        <summary>How this route fits together</summary>
        <div className="grid gap-16 pt-12">
          <Timeline detail={detail} />
          {detail.gates.length > 0 && (
            <div className="grid gap-4">
              <h3 className="section-title">What must happen first</h3>
              <ul className="grid gap-4">
                {detail.gates.map((gate) => (
                  <li key={`${gate.kind}-${gate.variant_id}-${gate.instrument_id}-${gate.month}`}>
                    {GATE[gate.kind]}
                    {gate.month ? ` before ${month(gate.month)}` : ""}.
                  </li>
                ))}
              </ul>
            </div>
          )}
          {detail.waits.length > 0 && (
            <div className="grid gap-4">
              <h3 className="section-title">Time spent waiting</h3>
              <ul className="grid gap-4">
                {detail.waits.map((wait) => (
                  <li key={`${wait.first_month}-${wait.last_month}`}>
                    {wait.months} {wait.months === 1 ? "month" : "months"}, from{" "}
                    {month(wait.first_month)} to {month(wait.last_month)}.
                  </li>
                ))}
              </ul>
            </div>
          )}
          {detail.milestones.length > 0 && (
            <div className="grid gap-4">
              <h3 className="section-title">Milestones</h3>
              <ul className="grid gap-4">
                {detail.milestones.map((milestone) => (
                  <li key={`${milestone.kind}-${milestone.month}`}>
                    {milestone.kind === "readiness"
                      ? "Skills readiness point"
                      : "Check assessed completion"}{" "}
                    in {month(milestone.month)}.
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </details>

      <details className="details small">
        <summary>Steps and evidence</summary>
        <div className="grid gap-12 pt-12">
          <p>
            Catalogue: {detail.label.name}, dated {formatDay(detail.label.dated)}. Options you added
            are marked below.
          </p>
          <ol className="grid gap-12">
            {detail.steps.map((step) => (
              <StepCard key={step.variant_id} step={step} />
            ))}
          </ol>
        </div>
      </details>

      <details className="details small">
        <summary>Money month by month</summary>
        <div className="grid gap-16 pt-12">
          <dl className="kv">
            <dt>What you'd pay out</dt>
            <dd>{money(costs.direct_cost)}</dd>
            {detail.basis.objective_basis === "economic" && (
              <>
                <dt>Pay difference from what you'd do instead</dt>
                <dd>{signed(costs.pay_difference)}</dd>
                <dt>Total cost, including that pay difference</dt>
                <dd>{signed(costs.economic_cost)}</dd>
              </>
            )}
            <dt>Most you'd pay in one month</dt>
            <dd>{money(costs.peak_monthly_payment)}</dd>
            <dt>Lowest cash before late receipts</dt>
            <dd>{signed(costs.minimum_prefunded_cash)}</dd>
            <dt>Cash you said you want to keep</dt>
            <dd>{money(costs.reserve)}</dd>
          </dl>
          <MonthTable detail={detail} />
          <Liabilities title="Due before this plan starts" items={detail.before_start} />
          <Liabilities title="Due after the months shown" items={detail.beyond_horizon} />
          <Liabilities title="Payments without a known date" items={detail.unscheduled} />
        </div>
      </details>

      {(detail.scenarios.length > 0 || detail.self_paid !== null) && (
        <details className="details small">
          <summary>What could change</summary>
          <ul className="grid gap-12 pt-12">
            {detail.scenarios.map((scenario) => (
              <Scenario
                key={scenario.scenario}
                check={scenario}
                objectiveBasis={detail.basis.objective_basis}
              />
            ))}
            {detail.self_paid !== null && (
              <li className="grid gap-4">
                <h4 className="font-semibold">If you pay the fee yourself</h4>
                <p>
                  {ROUTE_VERDICT[detail.self_paid.verdict]}. What you'd pay out:{" "}
                  {money(detail.self_paid.direct_cost)}.
                </p>
                {detail.self_paid.findings.map((finding) => (
                  <p key={findingKey(finding)}>{findingWords(finding)}</p>
                ))}
              </li>
            )}
          </ul>
        </details>
      )}
    </section>
  );
}
