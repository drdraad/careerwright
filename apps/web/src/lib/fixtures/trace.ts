// The fixture adapter for the route preview (S1.5): reads the supplied TRACE-01 worked trace
// and hands the shell labelled, synthetic content. It satisfies the contract a live adapter
// will: a failure is a typed `failed` result, never an empty preview, and the content keeps
// its synthetic origin (file, SHA-256, data date) everywhere it is shown.
//
// Nothing here calculates. Layers are the fixture's stated expectation (`expected.fronts`),
// costs and dates are the fixture's numbers: route ranks and affordability are computed by
// deterministic Python, and the solver that will do so does not exist yet (Sprint 6).
import type { Money, WorkState } from "@/generated/api";
import type { SignedMoney } from "@/lib/money";

/**
 * The readiness states the fixture pack uses, in words (spec RDY-1). `null` means ready
 * without a condition. A state not listed here is refused as malformed rather than guessed.
 */
const READINESS: Record<string, string | null> = {
  conditional_on_assessed_completion: "ready only once its assessed report is passed",
  ready: null,
};

export const TRACE_LOCATOR = "fixtures/m0/worked_trace.json";
/** fixtures/README.md: the supplied pack is byte-identical and pinned by hash. */
export const TRACE_SHA256 = "05f72958c99765684156d091c421e822855bb0150f220ad97a3b6c97db1895a5";

export type FixtureSource = {
  label: string;
  locator: string;
  sha256: string;
  dataAsOf: string;
  purpose: string;
};

export type PreviewRoute = {
  /** Namespaced so TRACE-01 routes can never collide with DIRECTAI ones. */
  key: string;
  letter: string;
  timeMonths: number;
  /** Signed: fees plus pay lost against the baseline can be negative (a gain). */
  economicCost: SignedMoney;
  directSpend: Money;
  paymentsByMonth: Money[];
  incomeByMonth: Money[];
  /** 1, 2 or 3: the layer the fixture states for this route. */
  layer: number;
  /** The route's readiness condition in words, from its readiness state; null if none. */
  condition: string | null;
  start: string;
  finish: string;
};

export type RoutePreview =
  | {
      state: Extract<WorkState, "complete">;
      source: FixtureSource;
      traceId: string;
      targetTitle: string;
      region: string;
      planningStart: string;
      horizonMonths: number;
      routes: PreviewRoute[];
      /** The fixture's own selected route and the figures its print snapshot states. */
      selected: { letter: string; peakMonthlyPayment: Money; lowestBalance: Money };
    }
  | {
      state: Extract<WorkState, "failed">;
      reason: "missing" | "checksum_mismatch" | "not_synthetic" | "malformed";
      locator: string;
    };

type TraceRoute = {
  id: string;
  time_months: number;
  direct_spend_minor: number;
  economic_cost_minor: number;
  income_by_month_minor: number[];
  payments_by_month_minor: number[];
  readiness_status: string;
  actual_start_date: string;
  actual_finish_date: string;
};

type Trace = {
  id: string;
  synthetic: boolean;
  currency: string;
  data_as_of: string;
  purpose: string;
  planning_start: string;
  comparison_horizon_months: number;
  target: { title: string };
  routes: TraceRoute[];
  expected: {
    fronts: string[][];
    selected_route: string;
    print_snapshot: {
      region: string;
      peak_monthly_payment_minor: number;
      minimum_prefunded_cash_minor: number;
    };
  };
};

const failed = (reason: Extract<RoutePreview, { state: "failed" }>["reason"]): RoutePreview => ({
  state: "failed",
  reason,
  locator: TRACE_LOCATOR,
});

const gbp = (minor: number): Money => ({ minor_units: minor, currency: "GBP" });

function isWholeNonNegative(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function isWhole(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value);
}

/** Maps verified file bytes (already hash-checked) to the preview, or a typed failure. */
export function previewFromTrace(text: string, sha256: string): RoutePreview {
  if (sha256 !== TRACE_SHA256) return failed("checksum_mismatch");
  let trace: Trace;
  try {
    trace = JSON.parse(text) as Trace;
  } catch {
    return failed("malformed");
  }
  if (trace.synthetic !== true || trace.currency !== "GBP") return failed("not_synthetic");
  const layerOf = new Map<string, number>();
  for (const [index, front] of (trace.expected?.fronts ?? []).entries()) {
    for (const letter of front) {
      if (layerOf.has(letter)) return failed("malformed");
      layerOf.set(letter, index + 1);
    }
  }
  const routes: PreviewRoute[] = [];
  for (const route of trace.routes ?? []) {
    const layer = layerOf.get(route.id);
    const payments = [
      route.direct_spend_minor,
      ...route.payments_by_month_minor,
      ...route.income_by_month_minor,
    ];
    if (
      layer === undefined ||
      !payments.every(isWholeNonNegative) ||
      !isWhole(route.economic_cost_minor) ||
      !Object.hasOwn(READINESS, route.readiness_status)
    ) {
      return failed("malformed");
    }
    routes.push({
      key: `${trace.id}/${route.id}`,
      letter: route.id,
      timeMonths: route.time_months,
      economicCost: { minor_units: route.economic_cost_minor, currency: "GBP" },
      directSpend: gbp(route.direct_spend_minor),
      paymentsByMonth: route.payments_by_month_minor.map(gbp),
      incomeByMonth: route.income_by_month_minor.map(gbp),
      layer,
      condition: READINESS[route.readiness_status] ?? null,
      start: route.actual_start_date,
      finish: route.actual_finish_date,
    });
  }
  if (routes.length === 0 || routes.length !== layerOf.size) return failed("malformed");
  const snapshot = trace.expected.print_snapshot;
  return {
    state: "complete",
    source: {
      label: `${trace.id} worked trace`,
      locator: TRACE_LOCATOR,
      sha256,
      dataAsOf: trace.data_as_of,
      purpose: trace.purpose,
    },
    traceId: trace.id,
    targetTitle: trace.target.title,
    region: snapshot.region,
    planningStart: trace.planning_start,
    horizonMonths: trace.comparison_horizon_months,
    routes,
    selected: {
      letter: trace.expected.selected_route,
      peakMonthlyPayment: gbp(snapshot.peak_monthly_payment_minor),
      lowestBalance: gbp(snapshot.minimum_prefunded_cash_minor),
    },
  };
}
