// What the world draws, independent of how: nodes and trails, each with a state that has a
// declared meaning (plan section 4). Both renderers, the moving WebGL world and the still SVG
// world, draw exactly this, so the still world carries every state the moving one does.

export type Vec3 = readonly [number, number, number];

/**
 * The declared meanings. Everything that varies in brightness or solidity comes from one of these.
 * - usual: the person's role usually needs it, not confirmed yet (display only, ADR 0014).
 * - said: the person said they have done it.
 * - shadow: not known yet. Drawn as a quiet solid slate trail, never absent and never zero.
 * - opening: an opening around a destination (the Roles place, and the busiest scene).
 */
export type TrailState = "usual" | "said" | "shadow" | "opening";

export const STATE_CODE: Record<TrailState, number> = {
  usual: 0,
  said: 1,
  shadow: 2,
  opening: 4,
};

export type NodeKind = "origin" | "skill" | "destination" | "opening";

export const KIND_CODE: Record<NodeKind, number> = {
  origin: 0,
  skill: 1,
  destination: 2,
  opening: 5,
};

export type SceneNode = {
  readonly id: string;
  readonly kind: NodeKind;
  /** For the origin: "said" once the person's light is lit, "usual" while it waits. */
  readonly state: TrailState;
  readonly p: Vec3;
  /** World units. */
  readonly size: number;
  /** Seconds on the world clock when it appears. */
  readonly birth: number;
};

export type SceneTrail = {
  readonly id: string;
  readonly points: readonly Vec3[];
  readonly state: TrailState;
  /** Seconds on the world clock when it starts to grow, and how long growing takes. */
  readonly birth: number;
  readonly duration: number;
  /** Core width at the start and at the end (world units). */
  readonly width: readonly [number, number];
  /** Position along the journey from the person (0) to the horizon (1): blue to violet. */
  readonly hue: readonly [number, number];
  /** Distance travelled from the person at the trail's start (light flows outward from it). */
  readonly reach: number;
};

export type Scene = {
  readonly nodes: readonly SceneNode[];
  readonly trails: readonly SceneTrail[];
};

/** Deterministic randomness, so the same world is always drawn the same way. */
export function seeded(seed: string): () => number {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
  return () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
}

export function cubic(a: Vec3, b: Vec3, c: Vec3, d: Vec3, steps: number): Vec3[] {
  const out: Vec3[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const u = 1 - t;
    const w0 = u * u * u;
    const w1 = 3 * u * u * t;
    const w2 = 3 * u * t * t;
    const w3 = t * t * t;
    out.push([
      w0 * a[0] + w1 * b[0] + w2 * c[0] + w3 * d[0],
      w0 * a[1] + w1 * b[1] + w2 * c[1] + w3 * d[1],
      w0 * a[2] + w1 * b[2] + w2 * c[2] + w3 * d[2],
    ]);
  }
  return out;
}
