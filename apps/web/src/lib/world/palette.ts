// The world's colours for the still SVG world, by token name. Each is the design token's own
// value (src/design/tokens/tokens.css); `palette.test.ts` holds the two to each other. The
// moving world's shaders carry the same values as floats (gl.ts).
export const PALETTE = {
  ground: "#03050B", // --world-ground
  horizon: "#1C2552", // --world-horizon
  person: "#EDF5FF", // --light-person
  destination: "#FF9433", // --light-destination
  destinationCore: "#FFD2A1", // --light-destination-core
  chosen: "#45F7D4", // --light-chosen
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
  chosen: "--light-chosen",
  near: "--trail-near",
  far: "--trail-far",
  shadow: "--trail-shadow",
};

const rgb = (hex: string): [number, number, number] => [
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
