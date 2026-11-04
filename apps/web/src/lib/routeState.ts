import type { RouteDetail, RouteStep } from "@/generated/api";

export type RouteResultStatus =
  | "unloaded"
  | "not_searched"
  | "pending"
  | "stale"
  | "error"
  | "limited"
  | "unresolved"
  | "unsupported"
  | "available";

export const RESULT_STATUS: Record<RouteResultStatus, string> = {
  unloaded: "Open to check saved results",
  not_searched: "Routes not searched yet",
  pending: "Checking routes",
  stale: "Saved results need updating",
  error: "Routes could not be checked",
  limited: "Search stopped before a route was established",
  unresolved: "Route support not established; planning facts still needed",
  unsupported: "No supported route found in this monthly model",
  available: "Supported route found",
};

export const stepIdentity = (step: RouteStep) =>
  JSON.stringify([
    step.variant_id,
    step.start_date,
    step.finish_date,
    step.start_month,
    step.finish_month,
  ]);

export const routeIdentity = (route: RouteDetail) =>
  JSON.stringify([
    route.schedule.route,
    route.steps.map((step) => [stepIdentity(step), step.title]).sort(),
  ]);

export function stepMissingFacts(step: RouteStep): string[] {
  return [
    step.title === null ? "Step name unknown" : null,
    step.kind === "learning" && step.provider === null ? "Provider unknown" : null,
    !step.start_date && !step.start_month ? "Start date unknown" : null,
    !step.finish_date && !step.finish_month ? "Finish date unknown" : null,
    step.weekly_hours === null ? "Weekly hours unknown" : null,
    step.grants.length > 0 && step.usable_month === null ? "Outcome timing unknown" : null,
    step.kind !== "work" && step.payments.length === 0 && !step.recurring
      ? "Payments unknown"
      : null,
    step.payments.some((payment) => !payment.month && !payment.due) ? "Payment date unknown" : null,
    step.recurring && (step.recurring.count === null || step.recurring.at_least)
      ? "Full payment total unknown"
      : null,
    step.kind === "work" && step.wage === null ? "Net pay unknown" : null,
    step.fee_loan && step.fee_loan.amount === null ? "Loan amount unknown" : null,
    step.supports.some((support) => support.amount === null && !support.covers_fees_in_full)
      ? "Funding amount unknown"
      : null,
  ].filter((fact): fact is string => fact !== null);
}

export function routeMissingFacts(route: RouteDetail): string[] {
  return Array.from(
    new Set([
      ...route.steps.flatMap(stepMissingFacts),
      ...(route.costs.direct_cost === null ? ["Total spending unknown"] : []),
      ...(route.basis.objective_basis === "economic" && route.costs.economic_cost === null
        ? ["Earnings difference unknown"]
        : []),
      ...(route.schedule.verdict === "unresolved" ||
      route.schedule.qualifications.includes("readiness_not_assessed")
        ? ["Readiness not assessed"]
        : []),
      ...(route.schedule.qualifications.includes("missing_outcome_level")
        ? ["Taught skill level unknown"]
        : []),
      ...(route.schedule.qualifications.includes("planned_outcome_assumption")
        ? ["Planned skill outcome still an assumption"]
        : []),
      ...(route.schedule.qualifications.includes("open_conflict")
        ? ["Evidence still disagrees"]
        : []),
      ...(route.gates.some((gate) => gate.month === null) ? ["Gate date unknown"] : []),
      ...(route.schedule.conditions.some(
        (condition) =>
          !route.gates.some(
            (gate) =>
              gate.kind === condition.kind &&
              gate.variant_id === condition.variant_id &&
              gate.instrument_id === condition.instrument_id,
          ),
      )
        ? ["Gate timing not recorded"]
        : []),
      ...(route.costs.loans_to_repay.some((loan) => loan.repayment === null)
        ? ["Loan repayment unknown"]
        : []),
    ]),
  );
}

export const planningState = (route: RouteDetail) =>
  routeMissingFacts(route).length ? "partial" : "complete";

export function targetRouteState(routes: RouteDetail[], status?: RouteResultStatus) {
  if (status && status !== "available") return status;
  if (!routes.length) return status === "available" ? "pending" : "not_searched";
  return routes.some((route) => planningState(route) === "complete") ? "complete" : "partial";
}

export function routeStateWords(state: ReturnType<typeof targetRouteState>) {
  return state === "complete"
    ? "Planning information complete"
    : state === "partial"
      ? "Planning facts still needed"
      : RESULT_STATUS[state];
}
