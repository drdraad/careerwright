import type { ComparisonOut, PointOut } from "@/generated/api";
import { formatSignedMoney } from "@/lib/money";
import { OBJECTIVE_BASIS } from "@/lib/optionWords";
import { comparatorWords } from "@/lib/routeWords";

const WIDTH = 640;
const HEIGHT = 300;
const LEFT = 64;
const TOP = 24;
const PLOT_WIDTH = WIDTH - LEFT - 24;
const PLOT_HEIGHT = HEIGHT - TOP - 48;

const pointLabel = (point: PointOut) =>
  `Point ${point.point_id}: ${point.months_to_readiness} months, ${formatSignedMoney(point.objective_cost)}, ${point.layer === null ? "rank not settled" : `F${point.layer}`}, ${point.schedule_count} ${point.schedule_count === 1 ? "route" : "routes"}`;

/** The solver's points, positioned for display only. Its layers and costs are never recomputed. */
export function RouteChart({
  comparison,
  select,
}: {
  comparison: ComparisonOut;
  select(index: number): void;
}) {
  const points = comparison.points;
  if (points.length === 0) return null;
  const costs = points.map((point) => point.objective_cost.minor_units);
  const low = Math.min(0, ...costs);
  const high = Math.max(0, ...costs);
  const span = Math.max(1, high - low);
  const x = (months: number) => LEFT + (months / comparison.basis.horizon_months) * PLOT_WIDTH;
  const y = (cost: number) => TOP + ((high - cost) / span) * PLOT_HEIGHT;
  return (
    <section className="grid gap-12" aria-label="Routes by time and cost">
      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full min-w-[320px]"
          role="img"
          aria-label={`Routes by months until ready and ${OBJECTIVE_BASIS[comparison.basis.objective_basis].toLowerCase()}`}
        >
          <title>Routes by time and cost; choose a point from the list below</title>
          <path
            d={`M${LEFT} ${TOP} V${TOP + PLOT_HEIGHT} H${LEFT + PLOT_WIDTH}`}
            fill="none"
            stroke="currentColor"
            opacity="0.65"
          />
          <text x={LEFT} y={HEIGHT - 12} fill="currentColor" fontSize="12">
            0 months
          </text>
          <text
            x={LEFT + PLOT_WIDTH}
            y={HEIGHT - 12}
            textAnchor="end"
            fill="currentColor"
            fontSize="12"
          >
            {comparison.basis.horizon_months} months
          </text>
          <text x={LEFT - 6} y={TOP + 4} textAnchor="end" fill="currentColor" fontSize="12">
            {formatSignedMoney({ minor_units: high, currency: "GBP" })}
          </text>
          <text
            x={LEFT - 6}
            y={TOP + PLOT_HEIGHT}
            textAnchor="end"
            fill="currentColor"
            fontSize="12"
          >
            {formatSignedMoney({ minor_units: low, currency: "GBP" })}
          </text>
          {points.map((point) => {
            const cx = x(point.months_to_readiness);
            const cy = y(point.objective_cost.minor_units);
            return point.layer === 1 ? (
              <circle key={point.point_id} cx={cx} cy={cy} r="6" fill="currentColor">
                <title>{pointLabel(point)}</title>
              </circle>
            ) : point.layer === 2 ? (
              <circle
                key={point.point_id}
                cx={cx}
                cy={cy}
                r="6"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <title>{pointLabel(point)}</title>
              </circle>
            ) : (
              <rect
                key={point.point_id}
                x={cx - 5}
                y={cy - 5}
                width="10"
                height="10"
                fill="none"
                stroke="currentColor"
                opacity="0.7"
              >
                <title>{pointLabel(point)}</title>
              </rect>
            );
          })}
        </svg>
      </div>
      <p className="small muted">
        {comparison.points_shown} of {comparison.points_total} points shown. Filled circles are F1,
        open circles F2, and squares F3 or still unranked.
        {!comparison.layers_exact &&
          " Ranks are only among routes found before the search stopped."}
      </p>
      <details className="details small">
        <summary>Choose a point by its exact time and cost</summary>
        <ol className="grid gap-8 pt-12">
          {points.map((point) => (
            <li key={point.point_id}>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={point.schedules.length === 0}
                onClick={() => {
                  const first = point.schedules[0];
                  if (first !== undefined) select(first);
                }}
              >
                {pointLabel(point)}
              </button>
              {point.comparator && (
                <p className="small muted">{comparatorWords(point.comparator)}</p>
              )}
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}
