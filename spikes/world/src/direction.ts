// A direction is a geometry, a view and a look. The story, the states and the words are shared:
// buildScene turns the same story into the same nodes and trails for every direction.
import {
  type LabelSide,
  type NodeKind,
  type Scene,
  type SceneNode,
  type SceneTrail,
  type TrailState,
  type Vec3,
  dist3,
} from "./scene.ts";
import { type Story, TIMING } from "./story.ts";

export type DirectionId = "growth" | "horizon" | "circuit";
export type FontId = "outfit" | "sora" | "unbounded";
/** One heading face for every look by default, so the comparison is of worlds, not lettering. */
export const DEFAULT_FONT: FontId = "outfit";

export type Viewport = { readonly w: number; readonly h: number; readonly narrow: boolean };

/** Two vec4s, passed straight to the shaders. Their meaning is the direction's own. */
export type Camera = readonly [number, number, number, number, number, number, number, number];

export type Projected = { x: number; y: number; scale: number; visible: boolean };

export type Placed = { readonly p: Vec3; readonly side: LabelSide };

export type PathKind = "root" | "reach" | "link" | "shadow" | "opening";

export type Geometry = {
  readonly origin: Vec3;
  readonly skills: readonly Placed[];
  readonly destinations: readonly Placed[];
  readonly revealed: Placed;
  readonly unknown: readonly Placed[];
  openings(dest: Vec3, count: number, place: number): Vec3[];
  /** i and j identify the trail (for lanes and seeds). */
  path(from: Vec3, to: Vec3, kind: PathKind, i: number, j: number): Vec3[];
  /** Atmosphere: fine side fibres, the same for every trail. */
  fibres?(points: readonly Vec3[], seed: number): Vec3[][];
  readonly widths: Readonly<Record<PathKind | "fibre", readonly [number, number]>>;
  readonly sizes: Readonly<Record<NodeKind, number>>;
};

export type GlslChunks = {
  /** vec2 project(vec3 p, out float scale) */
  readonly project: string;
  /** vec3 background(vec2 px) */
  readonly background: string;
  /** vec4 particle(vec4 seed, out float alpha): xy screen px, z size px */
  readonly particle: string;
  /** vec4 nodeLook(vec2 q, float kind, float state, float age, float flare, float sel, float seed) */
  readonly node: string;
  /** float pulse(float dist, float state) — ambient light travelling along the trails */
  readonly pulse: string;
  /** vec2 sway(vec2 px, float envelope) — a screen-space offset for trail points (atmosphere) */
  readonly sway: string;
};

export type Direction = {
  readonly id: DirectionId;
  readonly name: string;
  readonly blurb: string;
  readonly particles: number;
  geometry(vp: Viewport, story: Story): Geometry;
  /** Where the view rests for the story as it stands. */
  view(vp: Viewport, story: Story): Camera;
  project(p: Vec3, cam: Camera, vp: Viewport): Projected;
  readonly glsl: GlslChunks;
  /** The still world's backdrop, as SVG markup in screen pixels. */
  stillBackdrop(vp: Viewport, cam: Camera): string;
};

const OPENINGS = 100;

/**
 * Where each of the role's skills sits in the fan: the skills shared with the revealed
 * destination are seated on the side that faces it, so fewer trails cross. Layout only.
 */
export function skillSlots(story: Story, sharedFirst: boolean): number[] {
  const skills = story.role?.skills ?? [];
  const shared = new Set(story.connection?.shared ?? []);
  const inShared = skills.filter((s) => shared.has(s));
  const rest = skills.filter((s) => !shared.has(s));
  const order = sharedFirst ? [...inShared, ...rest] : [...rest, ...inShared];
  return skills.map((s) => order.indexOf(s));
}

const arcLength = (points: readonly Vec3[]): number => {
  let total = 0;
  for (let i = 1; i < points.length; i++) total += dist3(points[i - 1] as Vec3, points[i] as Vec3);
  return total;
};

/** The same story becomes the same nodes and trails, in each direction's geometry. */
export function buildScene(direction: Direction, vp: Viewport, story: Story): Scene {
  const nodes: SceneNode[] = [];
  const trails: SceneTrail[] = [];
  const role = story.role;
  const g = direction.geometry(vp, story);
  const ignite = story.igniteAt;
  const reveal = story.revealAt;
  const kept = story.kept;

  nodes.push({
    id: "origin",
    kind: "origin",
    state: role ? "said" : "usual",
    p: g.origin,
    size: g.sizes.origin,
    birth: -1e6,
    changed: ignite,
    side: "below",
    selected: false,
  });
  if (!role) return { nodes, trails };

  const shared = new Set(story.connection?.shared ?? []);
  const revealed = story.phase === "revealed" ? story.connection : null;
  const stateOf = (skill: string): TrailState => (story.said.has(skill) ? "said" : "usual");
  const changedOf = (skill: string): number => story.said.get(skill) ?? -1e6;
  const onChosenPath = (skill: string): boolean => kept !== null && revealed !== null && shared.has(skill);

  const addTrail = (
    id: string,
    points: Vec3[],
    state: TrailState,
    birth: number,
    duration: number,
    width: readonly [number, number],
    hue: readonly [number, number],
    reach: number,
    chosen: boolean,
    changed: number,
    fibreSeed: number | null,
  ): void => {
    trails.push({ id, points, state, birth, duration, width, hue, reach, chosen, changed });
    if (fibreSeed === null || !g.fibres) return;
    g.fibres(points, fibreSeed).forEach((fibre, f) => {
      trails.push({
        id: `${id}:fibre:${f}`,
        points: fibre,
        state: "fibre",
        birth: birth + duration * 0.6,
        duration: duration * 0.8,
        width: g.widths.fibre,
        hue,
        reach,
        chosen: false,
        changed: -1e6,
      });
    });
  };

  // The first trails: the skills the person's role usually needs.
  const rootLength = new Map<string, number>();
  role.skills.forEach((skill, i) => {
    const place = g.skills[i];
    if (!place) return;
    const points = g.path(g.origin, place.p, "root", i, 0);
    rootLength.set(skill, arcLength(points));
    const birth = ignite + 0.15 + i * 0.08;
    addTrail(
      `root:${skill}`,
      points,
      stateOf(skill),
      birth,
      0.65,
      g.widths.root,
      [0, 0.35],
      0,
      onChosenPath(skill),
      Math.max(changedOf(skill), onChosenPath(skill) ? (kept ?? -1e6) : -1e6),
      i,
    );
    const flare = revealed && shared.has(skill) ? reveal + [...shared].indexOf(skill) * 0.09 : -1e6;
    nodes.push({
      id: `skill:${skill}`,
      kind: "skill",
      state: stateOf(skill),
      p: place.p,
      size: g.sizes.skill,
      birth: birth + 0.6,
      changed: Math.max(changedOf(skill), flare),
      side: place.side,
      selected: false,
    });
  });

  // The first scatter of destinations. Each grows one quiet trail from the shared skill nearest
  // to it; all the skills it shares light up only when the person points at it (one idea at a
  // time), and always for the revealed destination.
  const skillIndex = (skill: string): number => role.skills.indexOf(skill);
  story.destinations.forEach((dest, j) => {
    const place = g.destinations[j];
    if (!place) return;
    const birth = ignite + 0.85 + j * 0.07;
    const pointed = story.focus === dest.role.id;
    const nearest = [...dest.shared].sort(
      (a, b) =>
        dist3(g.skills[skillIndex(a)]?.p ?? g.origin, place.p) - dist3(g.skills[skillIndex(b)]?.p ?? g.origin, place.p),
    )[0];
    dest.shared.forEach((skill) => {
      const from = g.skills[skillIndex(skill)];
      if (!from || (!pointed && skill !== nearest)) return;
      const quiet = skill === nearest;
      const points = g.path(from.p, place.p, "reach", skillIndex(skill), j);
      addTrail(
        `reach:${dest.role.id}:${skill}`,
        points,
        stateOf(skill),
        quiet ? birth : story.focusAt,
        quiet ? 0.8 : 0.35,
        g.widths.reach,
        [0.35, 1],
        rootLength.get(skill) ?? 0,
        false,
        changedOf(skill),
        null,
      );
    });
    nodes.push({
      id: `dest:${dest.role.id}`,
      kind: "destination",
      state: "usual",
      p: place.p,
      size: g.sizes.destination,
      birth: birth + 0.8,
      changed: -1e6,
      side: place.side,
      selected: false,
    });
  });

  // The revelation: a destination nobody named lights up, joined by the skills the roles share.
  if (revealed) {
    nodes.push({
      id: `revealed:${revealed.role.id}`,
      kind: "revealed",
      state: "usual",
      p: g.revealed.p,
      size: g.sizes.revealed,
      birth: reveal + 0.4,
      changed: kept ?? reveal + 0.4,
      side: g.revealed.side,
      selected: kept !== null,
    });
    revealed.shared.forEach((skill, k) => {
      const from = g.skills[skillIndex(skill)];
      if (!from) return;
      const points = g.path(from.p, g.revealed.p, "link", skillIndex(skill), 99);
      addTrail(
        `link:${skill}`,
        points,
        stateOf(skill),
        reveal + 0.6 + k * 0.08,
        0.7,
        g.widths.link,
        [0.35, 1],
        rootLength.get(skill) ?? 0,
        kept !== null,
        Math.max(changedOf(skill), kept ?? -1e6),
        null,
      );
    });
    // What is still not known: the destination's other skills, in shadow.
    revealed.unknown.forEach((skill, k) => {
      const place = g.unknown[k];
      if (!place) return;
      const birth = reveal + 1.1 + k * 0.08;
      const toward = g.path(g.origin, place.p, "shadow", k, 0);
      addTrail(`shadow-in:${skill}`, toward, "shadow", birth, 0.5, g.widths.shadow, [0, 0.7], 0, false, -1e6, null);
      const onward = g.path(place.p, g.revealed.p, "shadow", k, 1);
      addTrail(
        `shadow-on:${skill}`,
        onward,
        "shadow",
        birth + 0.2,
        0.5,
        g.widths.shadow,
        [0.7, 1],
        arcLength(toward),
        false,
        -1e6,
        null,
      );
      nodes.push({
        id: `unknown:${skill}`,
        kind: "unknown",
        state: "shadow",
        p: place.p,
        size: g.sizes.unknown,
        birth: birth + 0.3,
        changed: -1e6,
        side: place.side,
        selected: false,
      });
    });
  }

  // The busiest scene: 100 made-up openings around the destinations (measurement only).
  if (story.busy) {
    const places: Vec3[] = [...story.destinations.map((_, j) => g.destinations[j]?.p), g.revealed.p].filter(
      (p): p is Vec3 => p !== undefined,
    );
    places.forEach((place, j) => {
      const count = Math.floor(OPENINGS / places.length) + (j < OPENINGS % places.length ? 1 : 0);
      g.openings(place, count, j).forEach((p, k) => {
        const points = g.path(place, p, "opening", j, k);
        addTrail(`opening:${j}:${k}`, points, "opening", ignite + 1.6, 0.6, g.widths.opening, [1, 1], 0, false, -1e6, null);
        nodes.push({
          id: `opening:${j}:${k}`,
          kind: "opening",
          state: "opening",
          p,
          size: g.sizes.opening,
          birth: ignite + 2,
          changed: -1e6,
          side: "right",
          selected: false,
        });
      });
    });
  }

  return { nodes, trails };
}

/** Eases the view from one resting place to the next; a cut when the world is still. */
export class ViewTween {
  private from: Camera;
  private to: Camera;
  private start = -1e6;

  constructor(initial: Camera) {
    this.from = initial;
    this.to = initial;
  }

  aim(target: Camera, at: number, still: boolean): void {
    if (target.every((v, i) => v === this.to[i])) return;
    this.from = still ? target : this.current(at);
    this.to = target;
    this.start = at;
  }

  moving(at: number): boolean {
    return at - this.start < TIMING.travel;
  }

  current(at: number): Camera {
    const t = Math.min(1, Math.max(0, (at - this.start) / TIMING.travel));
    const e = t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
    return this.from.map((v, i) => v + ((this.to[i] as number) - v) * e) as unknown as Camera;
  }
}
