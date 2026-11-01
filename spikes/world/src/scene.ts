// What the world draws, independent of how: nodes and trails, each with a state the model
// computed. Both renderers (the WebGL world and the still SVG world) draw exactly this.

export type Vec3 = readonly [number, number, number];

/**
 * The declared meanings. Everything that varies in brightness or solidity comes from one of these.
 * usual: the person's role usually needs it, not confirmed yet.
 * said: the person said they have done it.
 * shadow: not known yet.
 * opening: a made-up opening (busiest scene only).
 * fibre: atmosphere, the same for every item.
 * Separately, `chosen` marks the path to a destination the person kept in view: the only teal.
 */
export type TrailState = "usual" | "said" | "shadow" | "opening" | "fibre";

export const STATE_CODE: Record<TrailState, number> = {
  usual: 0,
  said: 1,
  shadow: 2,
  opening: 4,
  fibre: 5,
};

export type NodeKind = "origin" | "skill" | "destination" | "revealed" | "unknown" | "opening";

export const KIND_CODE: Record<NodeKind, number> = {
  origin: 0,
  skill: 1,
  destination: 2,
  revealed: 3,
  unknown: 4,
  opening: 5,
};

export type LabelSide = "left" | "right" | "above" | "below";

export type SceneNode = {
  readonly id: string;
  readonly kind: NodeKind;
  readonly state: TrailState;
  readonly p: Vec3;
  /** Pixels for screen-space directions; world units for Horizon. */
  readonly size: number;
  /** Seconds (performance clock) when it appears. */
  readonly birth: number;
  /** Seconds when its state last changed (a short flare answers the change). */
  readonly changed: number;
  readonly side: LabelSide;
  /** Selected: drawn with the lock-on ring. */
  readonly selected: boolean;
};

export type SceneTrail = {
  readonly id: string;
  readonly points: readonly Vec3[];
  readonly state: TrailState;
  readonly birth: number;
  readonly duration: number;
  /** Core width at the start and at the end (pixels, or world units for Horizon). */
  readonly width: readonly [number, number];
  /** Position along the journey from the person (0) to the horizon (1): blue to violet. */
  readonly hue: readonly [number, number];
  /** Distance travelled from the person at the trail's start (for the pulse that radiates out). */
  readonly reach: number;
  readonly chosen: boolean;
  readonly changed: number;
};

export type Scene = { readonly nodes: readonly SceneNode[]; readonly trails: readonly SceneTrail[] };

// Deterministic randomness, so the same answer always draws the same world.
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

export const dist3 = (a: Vec3, b: Vec3): number =>
  Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
