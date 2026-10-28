"use client";
// The fixture-driven route preview (S1.5). Every number is the TRACE-01 fixture's own; the
// layers are the ones the fixture states. Nothing is computed here, and the page says plainly
// that Nessa's route search does not exist yet: this is not the production solver's output.
//
// A card or the phone sheet can be read with everything above it scrolled away, so each keeps
// its own qualification: a conditional route says "Conditional" beside its readiness, with
// the condition (V-01, S0-V03), and the sheet leads with the route's name, condition,
// readiness and both costs (V-04). Computed routes (Task 14) keep the same rule.
import { useState } from "react";
import type { Money } from "@/generated/api";
import type { RoutePreview as Preview, PreviewRoute } from "@/lib/fixtures/trace";
import { formatMoney, formatSignedMoney } from "@/lib/money";
import { Alert } from "./Alert";
import { useEvidence } from "./EvidenceDrawer";
import { StatusBadge, SyntheticLabel } from "./Status";

type Complete = Extract<Preview, { state: "complete" }>;

const longDate = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const monthOnly = new Intl.DateTimeFormat("en-GB", { month: "long", timeZone: "UTC" });
const monthYear = new Intl.DateTimeFormat("en-GB", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const shortMonth = new Intl.DateTimeFormat("en-GB", {
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

const LAYER_NAME: Record<number, string> = { 1: "Best trade-offs found" };

/** The condition every route shares, if the data gives them all the same one. */
function sharedCondition(routes: PreviewRoute[]): string | null {
  const first = routes[0]?.condition ?? null;
  return first !== null && routes.every((route) => route.condition === first) ? first : null;
}

function monthLabel(planningStart: string, index: number): string {
  const start = new Date(`${planningStart}T00:00:00Z`);
  return shortMonth.format(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + index, 1));
}

function months(n: number): string {
  return `${n} month${n === 1 ? "" : "s"}`;
}

function SourceDetails({ preview }: { preview: Complete }) {
  return (
    <>
      <SyntheticLabel text="Synthetic fixture" />
      <p className="small">{preview.source.purpose}.</p>
      <dl className="kv">
        <dt>Source</dt>
        <dd>{preview.source.label}</dd>
        <dt>File</dt>
        <dd>{preview.source.locator}</dd>
        <dt>SHA-256</dt>
        <dd className="text-12">{preview.source.sha256}</dd>
        <dt>Data as of</dt>
        <dd>{longDate.format(new Date(`${preview.source.dataAsOf}T00:00:00Z`))}</dd>
      </dl>
      <p className="small">
        The layers are the ones this fixture states. Nessa's own route search, which will compute
        them, is not part of this build.
      </p>
    </>
  );
}

function MonthlyList({
  title,
  values,
  planningStart,
}: {
  title: string;
  values: Money[];
  planningStart: string;
}) {
  return (
    <div className="grid gap-4">
      <p className="section-title">{title}</p>
      <dl className="kv">
        {values.map((value, index) => (
          <div key={monthLabel(planningStart, index)} className="contents">
            <dt>{monthLabel(planningStart, index)}</dt>
            <dd>{formatMoney(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/** What fits in the phone sheet's peek: the fixture label, the condition and the figures. */
function RouteLead({ route }: { route: PreviewRoute }) {
  return (
    // biome-ignore lint/a11y/useSemanticElements: a group of facts, not a form fieldset
    <div role="group" aria-label={`Route ${route.letter} at a glance`} className="grid gap-8">
      <SyntheticLabel text="Synthetic fixture route" />
      {route.condition !== null && (
        <StatusBadge state="conditional" detail={`ready only ${route.condition}`} />
      )}
      <dl className="figures">
        <div>
          <dt>Ready in</dt>
          <dd>{months(route.timeMonths)}</dd>
        </div>
        <div>
          <dt>Economic cost</dt>
          <dd>{formatSignedMoney(route.economicCost)}</dd>
        </div>
        <div>
          <dt>Direct spending</dt>
          <dd>{formatMoney(route.directSpend)}</dd>
        </div>
      </dl>
    </div>
  );
}

function RouteDetails({ route, preview }: { route: PreviewRoute; preview: Complete }) {
  const selected = route.letter === preview.selected.letter;
  return (
    <>
      <RouteLead route={route} />
      <dl className="kv">
        <dt>Dates</dt>
        <dd>
          {longDate.format(new Date(`${route.start}T00:00:00Z`))} to{" "}
          {longDate.format(new Date(`${route.finish}T00:00:00Z`))}
        </dd>
        <dt>Layer</dt>
        <dd>{route.layer === 1 ? "Best trade-offs found (layer 1)" : `Layer ${route.layer}`}</dd>
      </dl>
      <MonthlyList
        title="Payments by month"
        values={route.paymentsByMonth}
        planningStart={preview.planningStart}
      />
      <MonthlyList
        title="Take-home pay by month"
        values={route.incomeByMonth}
        planningStart={preview.planningStart}
      />
      {selected && (
        <div className="grid gap-4">
          <p className="section-title">The fixture's selected route</p>
          <p className="small">
            Its print snapshot states a peak monthly payment of{" "}
            {formatMoney(preview.selected.peakMonthlyPayment)} and a minimum prefunded cash balance
            of {formatMoney(preview.selected.lowestBalance)}.
          </p>
        </div>
      )}
      <p className="small muted">
        From {preview.source.locator}, synthetic test data. Not a route Nessa computed for you.
      </p>
    </>
  );
}

function RouteCard({
  route,
  open,
  selected,
}: {
  route: PreviewRoute;
  open: (route: PreviewRoute) => void;
  selected: boolean;
}) {
  return (
    <li>
      <button
        type="button"
        className="card-on-space route-card"
        data-selected={selected}
        aria-haspopup="dialog"
        aria-expanded={selected}
        onClick={() => open(route)}
      >
        <span className="route-letter" data-layer={route.layer} aria-hidden="true">
          {route.letter}
        </span>
        <span className="grid gap-4">
          <span className="font-semibold">Route {route.letter}</span>
          {route.condition === null ? (
            <span className="small tnum">Ready in {months(route.timeMonths)}</span>
          ) : (
            <StatusBadge
              state="conditional"
              detail={`ready in ${months(route.timeMonths)}, ${route.condition}`}
            />
          )}
          <span className="small tnum">
            {formatSignedMoney(route.economicCost)} economic cost, {formatMoney(route.directSpend)}{" "}
            direct spending
          </span>
          {route.layer > 1 && <span className="small text-fg-muted">Layer {route.layer}</span>}
        </span>
      </button>
    </li>
  );
}

export function RoutePreview({ preview }: { preview: Preview }) {
  const evidence = useEvidence();
  const [inspected, setInspected] = useState<string | null>(null);
  const shown = evidence.evidence === null ? null : inspected;
  if (preview.state === "failed") {
    return (
      <Alert tone="error" title="The fixture route preview couldn't be loaded">
        <p>
          {preview.reason === "checksum_mismatch"
            ? `${preview.locator} does not match the pinned fixture pack, so it is not shown.`
            : preview.reason === "missing"
              ? `${preview.locator} was not found where the web server expects the fixture pack.`
              : `${preview.locator} is not the synthetic fixture the preview expects.`}{" "}
          Nothing else is affected.
        </p>
      </Alert>
    );
  }
  const openRoute = (route: PreviewRoute) => {
    setInspected(route.key);
    evidence.open({
      title: `Route ${route.letter}`,
      body: <RouteDetails route={route} preview={preview} />,
    });
  };
  const openSource = () => {
    setInspected(null);
    evidence.open({ title: "Where this came from", body: <SourceDetails preview={preview} /> });
  };
  const layers = [...new Set(preview.routes.map((route) => route.layer))].sort((a, b) => a - b);
  const shared = sharedCondition(preview.routes);
  const start = new Date(`${preview.planningStart}T00:00:00Z`);
  const end = new Date(start);
  end.setUTCMonth(end.getUTCMonth() + preview.horizonMonths - 1);
  const sameYear = start.getUTCFullYear() === end.getUTCFullYear();

  // V-03: on a phone the first route card is in the first view. The synthetic notice stays
  // first and whole; the cost basis and horizon are one line, their definitions a disclosure.
  return (
    <div className="grid gap-16 sm:gap-24">
      <Alert
        tone="neutral"
        glyph="synthetic"
        title="Fixture preview: not your routes"
        announce={false}
        actions={
          <button type="button" className="btn btn-secondary" onClick={openSource}>
            Where this came from
          </button>
        }
      >
        <p>
          Synthetic {preview.traceId} routes from the supplied fixture pack. Nessa's route search
          isn't built yet, so none was computed from your profile.
        </p>
      </Alert>

      <section className="grid gap-8" aria-label="What's being compared">
        <p className="small">
          Economic cost against the fixture's baseline, over the same{" "}
          {months(preview.horizonMonths)} for every route (
          {sameYear ? monthOnly.format(start) : monthYear.format(start)} to {monthYear.format(end)}
          ).
        </p>
        <details className="details small">
          <summary>What's being compared</summary>
          <dl className="grid gap-12 pt-12 sm:grid-cols-3">
            <div className="grid gap-4">
              <dt className="text-fg-muted">Cost shown</dt>
              <dd>Economic cost: fees plus pay lost against the fixture's baseline</dd>
            </div>
            <div className="grid gap-4">
              <dt className="text-fg-muted">Horizon</dt>
              <dd>
                {months(preview.horizonMonths)} for every route, {monthYear.format(start)} to{" "}
                {monthYear.format(end)}
              </dd>
            </div>
            <div className="grid gap-4">
              <dt className="text-fg-muted">Where</dt>
              <dd>{preview.region}</dd>
            </div>
          </dl>
          {shared !== null && (
            <p className="pt-12">
              <StatusBadge
                state="conditional"
                detail={`every route here is ready only ${shared}`}
              />
            </p>
          )}
        </details>
      </section>

      {layers.map((layer) => (
        <section key={layer} className="grid gap-12" aria-labelledby={`layer-${layer}`}>
          <h2 id={`layer-${layer}`} className="flex items-center gap-8 section-title">
            <span className="layer-mark" data-layer={layer} aria-hidden="true" />
            {LAYER_NAME[layer] ?? `Layer ${layer}`}
            {layer > 1 && (
              <span className="small font-normal text-fg-muted">
                bettered by at least one route above
              </span>
            )}
          </h2>
          <ul className="grid gap-12 lg:grid-cols-2">
            {preview.routes
              .filter((route) => route.layer === layer)
              .map((route) => (
                <RouteCard
                  key={route.key}
                  route={route}
                  open={openRoute}
                  selected={shown === route.key}
                />
              ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
