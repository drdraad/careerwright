// Horizon: a smooth dark plain under a glowing horizon (the product owner's choice at session
// W1, made livelier). The person stands in the foreground; destinations are lights along the
// horizon; each chapter is a place the view travels to. Layout is in world units: x across,
// y height, z depth.
//
// Position is layout only (VIS-1, ADR 0014 decision 4): every destination stands at the same
// depth, in title order, so where a light sits never means how near, likely or good it is.
import type { ChapterId } from "@/lib/chapters";
import type { WorldInput } from "./model";
import { cubic, type Scene, type SceneNode, type SceneTrail, seeded, type Vec3 } from "./scene";

export type Viewport = { readonly w: number; readonly h: number };

/** Below this width the world is the backdrop behind phone sheets (plan section 4). */
export const PHONE_MAX = 760;

export const isPhone = (vp: Viewport): boolean => vp.w <= PHONE_MAX;

/** Where the eye is and how it looks: a pinhole camera on the plain, always facing the horizon. */
export type View = {
  /** Eye position across and along the plain (world units). */
  readonly x: number;
  readonly z: number;
  /** Eye height above the plain (world units). */
  readonly eye: number;
  /** Where the horizon and the view's centre fall on screen (CSS pixels). */
  readonly horizon: number;
  readonly centre: number;
  /** Focal length (CSS pixels per world unit at depth 1). */
  readonly focal: number;
};

export type Projected = { x: number; y: number; scale: number; visible: boolean };

export const ORIGIN: Vec3 = [0, 0.04, 1.7];
/** Every destination stands this far out. */
export const HORIZON_Z = 17;
const DESTINATION_Y = 0.25;
const SKILL_RADIUS = 2.05;

/** Narrow screens squeeze the world sideways rather than shrinking it. */
const across = (vp: Viewport): number => Math.min(1, vp.w / vp.h / 1.6);

export function project(p: Vec3, view: View): Projected {
  const d = p[2] - view.z;
  if (d < 0.05) return { x: -1e5, y: -1e5, scale: 0, visible: false };
  const scale = view.focal / d;
  return {
    x: view.centre + (p[0] - view.x) * scale,
    y: view.horizon + (view.eye - p[1]) * scale,
    scale,
    visible: true,
  };
}

/** The span of the window (CSS pixels across) that the chapter's panels leave clear. */
export type Clear = { readonly left: number; readonly right: number };

/** Narrower than this, a clear span is no place to stand: the view keeps its usual centre. */
const MIN_CLEAR = 240;

/**
 * Where the view rests at each place. Where the chapter's panels leave a clear span wide
 * enough, the place's focus stands in its middle; otherwise desktop views keep it right of
 * the panel's usual place, and phone views sit behind the sheets.
 */
export function placeView(place: ChapterId, vp: Viewport, clear?: Clear): View {
  const view = restingView(place, vp);
  if (clear === undefined || clear.right - clear.left < MIN_CLEAR) return view;
  return { ...view, centre: (clear.left + clear.right) / 2 };
}

function restingView(place: ChapterId, vp: Viewport): View {
  const { w, h } = vp;
  const phone = isPhone(vp);
  const right = phone ? 0.5 : 0.7;
  switch (place) {
    case "you":
      // Close to the person, standing on the plain; the horizon far off.
      return { x: 0, z: 0.25, eye: 0.62, horizon: h * 0.36, centre: w * right, focal: h * 0.6 };
    case "roles":
      // Looking out to the horizon, where the destinations stand, with the person below.
      return {
        x: 0,
        z: -1,
        eye: 1,
        horizon: h * 0.4,
        centre: w * (phone ? 0.5 : 0.62),
        focal: h * 1.0,
      };
    case "skills":
      // Low along the ground between the person and the destinations.
      return {
        x: 0,
        z: -0.4,
        eye: 0.42,
        horizon: h * 0.3,
        centre: w * (phone ? 0.5 : 0.64),
        focal: h * 0.8,
      };
    case "options":
      // Raised over the middle ground, looking across the dark stretches.
      return {
        x: 0,
        z: -1.2,
        eye: 2.4,
        horizon: h * 0.22,
        centre: w * (phone ? 0.5 : 0.64),
        focal: h * 0.8,
      };
    case "routes":
      // High and wide: whole journeys from the person to the horizon.
      return {
        x: 0,
        z: -2.6,
        eye: 3.2,
        horizon: h * 0.2,
        centre: w * (phone ? 0.5 : 0.66),
        focal: h * 0.72,
      };
    case "plan":
      // Behind the person, looking down the path ahead.
      return {
        x: 0,
        z: -0.6,
        eye: 0.9,
        horizon: h * 0.34,
        centre: w * (phone ? 0.5 : 0.64),
        focal: h * 0.66,
      };
  }
}

/** The view's uniforms for the shaders: [x, z, horizon, focal] and [centre, eye, 0, 0]. */
export function viewUniforms(
  view: View,
): [[number, number, number, number], [number, number, number, number]] {
  return [
    [view.x, view.z, view.horizon, view.focal],
    [view.centre, view.eye, 0, 0],
  ];
}

const WIDTHS = {
  root: [0.016, 0.013],
  reach: [0.012, 0.06],
  shadow: [0.011, 0.05],
  opening: [0.03, 0.03],
} as const;

const SIZES = { origin: 0.034, skill: 0.026, destination: 0.22, opening: 0.05 } as const;

/** Trails run on the ground and rise to the light only at the end. */
function lift(points: Vec3[], from: Vec3, to: Vec3): Vec3[] {
  const n = points.length - 1;
  return points.map((p, i) => [p[0], from[1] + (to[1] - from[1]) * (i / n) ** 4, p[2]] as Vec3);
}

/** A long sweeping trail across the plain: forward first, then across to the light. */
function sweep(from: Vec3, to: Vec3, seed: string, steps = 56): Vec3[] {
  const rand = seeded(seed);
  const dz = to[2] - from[2];
  const sway = (rand() - 0.5) * 1.1;
  const c1: Vec3 = [from[0] + (to[0] - from[0]) * 0.15 + sway, 0.02, from[2] + dz * 0.42];
  const c2: Vec3 = [to[0] - sway * 0.4, 0.02, from[2] + dz * 0.8];
  return lift(cubic(from, c1, c2, to, steps), from, to);
}

export type Births = {
  /** When the person's light was lit in this visit (far past if it was lit on arrival). */
  readonly ignite: number;
  /** When each item first appeared in this visit, by id; absent means it was there on arrival. */
  readonly appeared: ReadonlyMap<string, number>;
};

const SETTLED = -1e6;

/** The world for what the API computed, in Horizon's geometry. */
export function buildScene(input: WorldInput, vp: Viewport, births: Births): Scene {
  const kx = across(vp);
  const origin: Vec3 = [ORIGIN[0], ORIGIN[1], ORIGIN[2]];
  const nodes: SceneNode[] = [];
  const trails: SceneTrail[] = [];
  const bornAt = (id: string) => births.appeared.get(id) ?? SETTLED;

  nodes.push({
    id: "origin",
    kind: "origin",
    state: input.lit ? "said" : "usual",
    p: origin,
    size: SIZES.origin,
    birth: SETTLED,
  });

  // Destinations stand on one line at the horizon, in title order, spread wide enough that
  // their names do not crowd it.
  const n = input.destinations.length;
  const spacing = Math.min(6.5, 22 / Math.max(1, n)) * kx;
  const destinationAt = (j: number): Vec3 => [
    (j - (n - 1) / 2) * spacing,
    DESTINATION_Y,
    HORIZON_Z,
  ];

  // Skills sit on one arc around the person, every one at the same distance.
  const skillCount = input.skills.length;
  const skillAt = (i: number): Vec3 => {
    const deg = skillCount > 1 ? -55 + (110 * i) / (skillCount - 1) : 0;
    const rad = (deg * Math.PI) / 180;
    return [
      origin[0] + Math.sin(rad) * SKILL_RADIUS * 1.15 * kx,
      0.02,
      origin[2] + Math.cos(rad) * SKILL_RADIUS,
    ];
  };

  input.skills.forEach((skill, i) => {
    const p = skillAt(i);
    const id = `skill:${skill.id}`;
    const birth = Math.max(bornAt(id), births.ignite + 0.15 + i * 0.08);
    const points = lift(
      cubic(
        origin,
        [origin[0] + (p[0] - origin[0]) * 0.2, 0.02, origin[2] + (p[2] - origin[2]) * 0.45],
        [origin[0] + (p[0] - origin[0]) * 0.75, 0.02, origin[2] + (p[2] - origin[2]) * 0.8],
        p,
        24,
      ),
      origin,
      p,
    );
    trails.push({
      id: `root:${skill.id}`,
      points,
      state: skill.state,
      birth,
      duration: 0.65,
      width: WIDTHS.root,
      hue: [0, 0.3],
      reach: 0,
    });
    nodes.push({ id, kind: "skill", state: skill.state, p, size: SIZES.skill, birth: birth + 0.6 });
  });

  input.destinations.forEach((destination, j) => {
    const p = destinationAt(j);
    const id = `destination:${destination.id}`;
    const birth = Math.max(bornAt(id), births.ignite + 0.85 + j * 0.07);
    // The ground between the person and the destination is not known yet: a quiet shadow
    // trail, solid and unbranched (session W1: the dashed lines were "a bit too noisy").
    trails.push({
      id: `shadow:${destination.id}`,
      points: sweep(origin, p, `shadow:${destination.id}`),
      state: "shadow",
      birth,
      duration: 0.8,
      width: WIDTHS.shadow,
      hue: [0.1, 1],
      reach: 0,
    });
    // Each skill the destination shares with the person reaches out to it, in its own state.
    input.skills.forEach((skill, i) => {
      if (!destination.shared.includes(skill.id)) return;
      trails.push({
        id: `reach:${destination.id}:${skill.id}`,
        points: sweep(skillAt(i), p, `reach:${destination.id}:${skill.id}`, 40),
        state: skill.state,
        birth: birth + 0.1,
        duration: 0.8,
        width: WIDTHS.reach,
        hue: [0.3, 1],
        reach: SKILL_RADIUS,
      });
    });
    nodes.push({
      id,
      kind: "destination",
      state: "usual",
      p,
      size: SIZES.destination,
      birth: birth + 0.8,
    });
  });

  // Openings around the destinations, spread evenly between them.
  if (input.openings > 0 && n > 0) {
    for (let j = 0; j < n; j++) {
      const place = destinationAt(j);
      const count = Math.floor(input.openings / n) + (j < input.openings % n ? 1 : 0);
      const rand = seeded(`openings:${j}`);
      for (let k = 0; k < count; k++) {
        const p: Vec3 = [place[0] + (rand() - 0.5) * 4.4 * kx, 0.03, place[2] + (rand() - 0.5) * 5];
        const c: Vec3 = [(place[0] + p[0]) / 2, 0.03, (place[2] + p[2]) / 2 - 0.4];
        const birth = births.ignite + 1.6;
        trails.push({
          id: `opening:${j}:${k}`,
          points: lift(cubic(place, c, c, p, 8), place, p),
          state: "opening",
          birth,
          duration: 0.6,
          width: WIDTHS.opening,
          hue: [1, 1],
          reach: 0,
        });
        nodes.push({
          id: `opening:${j}:${k}`,
          kind: "opening",
          state: "opening",
          p,
          size: SIZES.opening,
          birth: birth + 0.4,
        });
      }
    }
  }

  return { nodes, trails };
}

/** Eases the view from one resting place to the next: travel, or a cut when the world is still. */
export class ViewTween {
  private from: View;
  private to: View;
  private start = SETTLED;

  constructor(
    initial: View,
    private readonly seconds: number,
  ) {
    this.from = initial;
    this.to = initial;
  }

  /** Aims at a new resting view; `still` cuts straight to it. */
  aim(target: View, at: number, still: boolean): void {
    const same = (Object.keys(target) as (keyof View)[]).every((k) => target[k] === this.to[k]);
    if (same && !still) return;
    this.from = still ? target : this.current(at);
    this.to = target;
    this.start = still ? SETTLED : at;
  }

  moving(at: number): boolean {
    return at - this.start < this.seconds;
  }

  current(at: number): View {
    const t = Math.min(1, Math.max(0, (at - this.start) / this.seconds));
    // The travel easing (--ease-travel): slow away, quick across, slow to rest.
    const e = t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
    const mix = (k: keyof View) => this.from[k] + (this.to[k] - this.from[k]) * e;
    return {
      x: mix("x"),
      z: mix("z"),
      eye: mix("eye"),
      horizon: mix("horizon"),
      centre: mix("centre"),
      focal: mix("focal"),
    };
  }
}
