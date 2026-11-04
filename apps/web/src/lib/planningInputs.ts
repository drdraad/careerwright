// The person's planning inputs as the web writes them back (Task 12b, screens half; ADR 0013
// decision 11 and its Task 12b amendment). The API replaces the whole document on each write,
// with an expected version, so every change starts from the stored document, keeps every other
// answer, and sends only what a client may send: no schema version, and no record of who made a
// decision or added an option (the API keeps those while an entry is unchanged). Pure.
import type {
  OfferingFigures,
  PlanningInputsDocument,
  PlanningInputsIn,
  VariantInputs,
} from "@/generated/api";
import type { Figure } from "./figures";

/** The stored document as its client sends it back. */
export function submitted(document: PlanningInputsDocument): PlanningInputsIn {
  const { schema_version: _version, outcome_decisions, own_options, ...stated } = document;
  const inputs: PlanningInputsIn = { ...stated };
  if (outcome_decisions !== undefined) {
    inputs.outcome_decisions = outcome_decisions.map(
      ({ recorded_by: _by, recorded_at: _at, ...decision }) => decision,
    );
  }
  if (own_options !== undefined) {
    inputs.own_options = own_options.map(
      ({ recorded_by: _by, recorded_at: _at, ...option }) => option,
    );
  }
  return inputs;
}

function figured(figures: OfferingFigures, figure: Figure): OfferingFigures {
  switch (figure.fact) {
    case "start_date":
      return { ...figures, start: { on: figure.on, basis: figure.basis } };
    case "finish_date":
      return { ...figures, finish: figure.on };
    case "weekly_hours":
      return { ...figures, weekly_hours: figure.hours };
    case "cost":
      return { ...figures, cost: figure.money };
  }
}

/** One of the person's own figures for an offering, beside any others they gave for it. */
export function withFigure(
  inputs: PlanningInputsIn,
  offeringId: string,
  figure: Figure,
): PlanningInputsIn {
  const figures = inputs.offering_figures ?? [];
  const at = figures.findIndex((f) => f.offering_id === offeringId);
  const next =
    at === -1
      ? [...figures, figured({ offering_id: offeringId }, figure)]
      : figures.map((f, i) => (i === at ? figured(f, figure) : f));
  return { ...inputs, offering_figures: next };
}

/** What the person confirmed for one option, changed in the parts given, the rest kept. */
export function withVariant(
  inputs: PlanningInputsIn,
  variantId: string,
  change: Omit<Partial<VariantInputs>, "variant_id">,
): PlanningInputsIn {
  const variants = inputs.variants ?? [];
  const at = variants.findIndex((v) => v.variant_id === variantId);
  const next =
    at === -1
      ? [...variants, { variant_id: variantId, ...change }]
      : variants.map((v, i) => (i === at ? { ...v, ...change } : v));
  return { ...inputs, variants: next };
}

/** An option left out of the route search, or brought back into it. */
export function withExcluded(
  inputs: PlanningInputsIn,
  variantId: string,
  excluded: boolean,
): PlanningInputsIn {
  const others = (inputs.excluded_variants ?? []).filter((id) => id !== variantId);
  return { ...inputs, excluded_variants: excluded ? [...others, variantId] : others };
}
