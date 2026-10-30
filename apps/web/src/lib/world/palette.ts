// The world's colours and trail strengths, by token name. Each is the design token's own value
// (src/design/tokens/tokens.css); `tokens.test.ts` holds the two to each other. The still SVG
// world draws with them, and the moving world's shaders are written from them (gl.ts).
import type { TrailState } from "./scene";

export const PALETTE = {
  ground: "#03050B", // --world-ground
  horizon: "#1C2552", // --world-horizon
  person: "#EDF5FF", // --light-person
  destination: "#FF9433", // --light-destination
  destinationCore: "#FFD2A1", // --light-destination-core
  near: "#408CFF", // --trail-near
  far: "#9E6BFF", // --trail-far
  shadow: "#6F7EA3", // --trail-shadow
} as const;

export const PALETTE_TOKENS: Record<keyof typeof PALETTE, string> = {
  ground: "--world-ground",
  horizon: "--world-horizon",
  person: "--light-person",
  destination: "--light-destination",
  destinationCore: "--light-destination-core",
  near: "--trail-near",
  far: "--trail-far",
  shadow: "--trail-shadow",
};

/**
 * How strongly each trail's core is drawn: the opacity the design references measure it at
 * (contrast-pairs.json composites each one as drawn; 3:1 or more over the ground and the
 * horizon's glow). Said trails are drawn at full strength; an opening's trail as a usual one.
 */
export const TRAIL_OPACITY: Record<TrailState, number> = {
  usual: 0.85,
  said: 1,
  shadow: 0.9,
  opening: 0.85,
};

export const TRAIL_OPACITY_TOKENS: Partial<Record<TrailState, string>> = {
  usual: "--trail-opacity-usual",
  shadow: "--trail-opacity-shadow",
  opening: "--trail-opacity-usual",
};

export const rgb = (hex: string): [number, number, number] => [
  Number.parseInt(hex.slice(1, 3), 16),
  Number.parseInt(hex.slice(3, 5), 16),
  Number.parseInt(hex.slice(5, 7), 16),
];

const smooth = (t: number): number => t * t * (3 - 2 * t);

/** The journey's colour at `h`, from the person (0, blue) to the horizon (1, violet). */
export function journey(h: number): string {
  const t = smooth(Math.min(1, Math.max(0, h)));
  const a = rgb(PALETTE.near);
  const b = rgb(PALETTE.far);
  return `rgb(${a.map((c, i) => Math.round(c + ((b[i] as number) - c) * t)).join(",")})`;
}
