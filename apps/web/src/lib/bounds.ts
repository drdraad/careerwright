// Input bounds the API publishes in its schema, read from the generated client so the UI
// never restates them (the form's checks and the hint text use the same numbers).
import * as schemas from "@/generated/api/schemas.gen";
import type { ProfileFieldName } from "./vocabulary";

type PublishedSchema = {
  readonly $ref?: string;
  readonly type?: string;
  readonly maxItems?: number;
  readonly anyOf?: readonly PublishedSchema[];
  readonly properties?: Readonly<Record<string, PublishedSchema>>;
};

/** How many entries a list field takes: the bound the API publishes (`maxItems` on the
 * field's input schema; spec BND-1 for cities and targets), 0 for a field that is not a list. */
export function listLimit(name: ProfileFieldName): number {
  const field: PublishedSchema = schemas.ProfileInputSchema.properties[name];
  const input = (schemas as Record<string, PublishedSchema>)[
    `${field.$ref?.split("/").pop()}Schema`
  ];
  const array = input?.properties?.value?.anyOf?.find((option) => option.type === "array");
  return array?.maxItems ?? 0;
}
