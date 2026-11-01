// @vitest-environment node
// The moving world's timings and the still world's colours are the design tokens' own values
// (src/design/tokens/tokens.css, the mirror of docs/design/tokens): one source of truth.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { MOTION } from "./motion";
import { PALETTE, PALETTE_TOKENS, TRAIL_OPACITY, TRAIL_OPACITY_TOKENS } from "./palette";

const css = readFileSync(
  fileURLToPath(new URL("../../design/tokens/tokens.css", import.meta.url)),
  "utf8",
);
const root = css.match(/:root\s*\{([\s\S]*?)\n\}/)?.[1] ?? "";
const declarations = new Map(
  [...root.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)].map(([, name, value]) => [
    name as string,
    (value as string).trim(),
  ]),
);

function token(name: string): string {
  const value = declarations.get(name);
  if (value === undefined) throw new Error(`${name} is not a token`);
  const reference = value.match(/^var\((--[a-z0-9-]+)\)$/);
  return reference ? token(reference[1] as string) : value;
}

describe("[UI-04][UI-05] the world uses the design tokens", () => {
  it.each([
    ["travel", "--motion-travel"],
    ["grow", "--motion-grow"],
    ["ignite", "--motion-ignite"],
    ["breathe", "--motion-breathe"],
  ] as const)("times %s with %s", (key, name) => {
    expect(`${Math.round(MOTION[key] * 1000)}ms`).toBe(token(name));
  });

  it.each(Object.entries(PALETTE_TOKENS))("colours %s with %s", (key, name) => {
    expect(PALETTE[key as keyof typeof PALETTE].toUpperCase()).toBe(token(name).toUpperCase());
  });

  // The contrast tool measures each trail at its token's strength: the world draws it so.
  it.each(Object.entries(TRAIL_OPACITY_TOKENS))("draws %s trails at %s", (key, name) => {
    expect(TRAIL_OPACITY[key as keyof typeof TRAIL_OPACITY]).toBe(Number(token(name as string)));
  });

  it("draws said trails at full strength", () => {
    expect(TRAIL_OPACITY.said).toBe(1);
  });
});
