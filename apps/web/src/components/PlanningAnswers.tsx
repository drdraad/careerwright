import type { NeededInput, PlanningInputsDocument } from "@/generated/api";
import { formatMoney } from "@/lib/money";
import { BASELINE_KIND, NEEDED_INPUT, OBJECTIVE_BASIS, WORK_RIGHTS } from "@/lib/optionWords";
import { Button } from "./Button";

const FIELDS = [
  "objective_basis",
  "continuation",
  "baseline",
  "opening_cash",
  "living_costs",
  "reserve",
  "weekly_availability",
  "commitments",
  "existing_debts",
  "scenario_delay_months",
  "work_rights",
] as const satisfies readonly NeededInput[];

function answer(field: (typeof FIELDS)[number], inputs: PlanningInputsDocument): string | null {
  switch (field) {
    case "objective_basis":
      return inputs.objective_basis ? OBJECTIVE_BASIS[inputs.objective_basis] : null;
    case "continuation":
      return inputs.continuation
        ? `${inputs.continuation.hours_per_week} hours a week, ${formatMoney(inputs.continuation.net_income)} take-home pay a month`
        : null;
    case "baseline":
      return inputs.baseline
        ? `${BASELINE_KIND[inputs.baseline.kind]}, ${formatMoney(inputs.baseline.net_income)} take-home pay a month`
        : null;
    case "opening_cash":
    case "living_costs":
    case "reserve":
      return inputs[field] ? formatMoney(inputs[field]) : null;
    case "weekly_availability":
      return inputs.weekly_availability === null || inputs.weekly_availability === undefined
        ? null
        : `${inputs.weekly_availability} hours a week`;
    case "commitments":
      return inputs.commitments === null || inputs.commitments === undefined
        ? null
        : inputs.commitments.length === 0
          ? "None stated"
          : `${inputs.commitments.length} listed`;
    case "existing_debts":
      return inputs.existing_debts === null || inputs.existing_debts === undefined
        ? null
        : inputs.existing_debts.length === 0
          ? "None stated"
          : `${inputs.existing_debts.length} listed`;
    case "scenario_delay_months":
      return inputs.scenario_delay_months === null || inputs.scenario_delay_months === undefined
        ? null
        : `${inputs.scenario_delay_months} months`;
    case "work_rights":
      return inputs.work_rights ? WORK_RIGHTS[inputs.work_rights] : null;
  }
}

export function PlanningAnswers({
  inputs,
  onChange,
}: {
  inputs: PlanningInputsDocument;
  onChange(field: (typeof FIELDS)[number]): void;
}) {
  const given = FIELDS.flatMap((field) => {
    const value = answer(field, inputs);
    return value === null ? [] : [{ field, value }];
  });
  if (given.length === 0) return null;
  return (
    <details>
      <summary>Your planning answers ({given.length})</summary>
      <dl className="kv pt-12">
        {given.map(({ field, value }) => (
          <div className="contents" key={field}>
            <dt>{NEEDED_INPUT[field].name}</dt>
            <dd>
              {value}{" "}
              <Button
                aria-label={`Change ${NEEDED_INPUT[field].name}`}
                onClick={() => onChange(field)}
              >
                Change
              </Button>
            </dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
