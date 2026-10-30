// Circuit: cybernetic first, and alive. The person is a powered core on a board of faint
// micro-traces; the skills their job usually needs are pads on a ring around it, all at the same
// distance; destinations are terminals on one outer arc, all at the same distance, so position
// means nothing. Traces run at right angles and 45° like a circuit board, light travels along
// them as packets, and the revelation locks on with closing brackets. Layout is in pixels at a
// 900 px tall design size, relative to the core.
import { type Camera, type Direction, type Geometry, type Placed, type Viewport, skillSlots } from "../direction.ts";
import type { LabelSide, Vec3 } from "../scene.ts";
import type { Story } from "../story.ts";

const DEG = Math.PI / 180;
const GRID = 24;
const CORNER = 10;
const RING = 205;
const ARC = 470;
/** Terminal slots on the outer arc, top to bottom; the revelation always takes the second. */
const SLOT_ANGLES = [-62, -40, -18, 4, 26, 48];
const REVEALED_SLOT = 1;

const fit = (vp: Viewport): number => Math.min(vp.h, vp.w * 0.62) / 900;
const snap = (v: number): number => Math.round(v / (GRID / 2)) * (GRID / 2);
const at = (deg: number, r: number): Vec3 => [snap(Math.cos(deg * DEG) * r), snap(Math.sin(deg * DEG) * r), 0];
const sideFor = (deg: number): LabelSide => {
  const a = ((deg % 360) + 360) % 360;
  if (a > 225 && a < 315) return "above";
  if (a > 45 && a < 135) return "below";
  return a >= 135 && a <= 225 ? "left" : "right";
};

/** Rounds each corner of a route with a short arc. */
function round(corners: readonly Vec3[]): Vec3[] {
  const out: Vec3[] = [corners[0] as Vec3];
  for (let i = 1; i < corners.length - 1; i++) {
    const a = corners[i - 1] as Vec3;
    const b = corners[i] as Vec3;
    const c = corners[i + 1] as Vec3;
    const l1 = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const l2 = Math.hypot(c[0] - b[0], c[1] - b[1]);
    if (l1 < 0.5 || l2 < 0.5) continue;
    const r = Math.min(CORNER, l1 / 2, l2 / 2);
    const p: Vec3 = [b[0] - ((b[0] - a[0]) / l1) * r, b[1] - ((b[1] - a[1]) / l1) * r, 0];
    const q: Vec3 = [b[0] + ((c[0] - b[0]) / l2) * r, b[1] + ((c[1] - b[1]) / l2) * r, 0];
    for (let s = 0; s <= 5; s++) {
      const t = s / 5;
      const u = 1 - t;
      out.push([u * u * p[0] + 2 * u * t * b[0] + t * t * q[0], u * u * p[1] + 2 * u * t * b[1] + t * t * q[1], 0]);
    }
  }
  out.push(corners[corners.length - 1] as Vec3);
  return out;
}

/**
 * A circuit-board route: a straight run, a 45° run, a straight run. `bias` (0..1) chooses how much
 * of the straight distance comes first, which keeps neighbouring traces in separate lanes.
 */
function octilinear(a: Vec3, b: Vec3, bias: number): Vec3[] {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const sx = Math.sign(dx) || 1;
  const sy = Math.sign(dy) || 1;
  const adx = Math.abs(dx);
  const ady = Math.abs(dy);
  if (adx >= ady) {
    const first = (adx - ady) * bias;
    const p1: Vec3 = [a[0] + sx * first, a[1], 0];
    const p2: Vec3 = [p1[0] + sx * ady, b[1], 0];
    return round([a, p1, p2, b]);
  }
  const first = (ady - adx) * bias;
  const p1: Vec3 = [a[0], a[1] + sy * first, 0];
  const p2: Vec3 = [b[0], p1[1] + sy * adx, 0];
  return round([a, p1, p2, b]);
}

function geometry(_vp: Viewport, story: Story): Geometry {
  const skillCount = story.role?.skills.length ?? 8;
  const shared = story.connection?.shared.length ?? 0;
  const slots = skillSlots(story, true);
  const facing = SLOT_ANGLES[REVEALED_SLOT] as number;
  const step = 360 / Math.max(1, skillCount);
  const skills: Placed[] = [];
  for (let i = 0; i < skillCount; i++) {
    const slot = slots[i] ?? i;
    const deg = facing + (slot - (shared - 1) / 2) * step;
    skills.push({ p: at(deg, RING), side: sideFor(deg) });
  }
  const free = SLOT_ANGLES.filter((_, k) => k !== REVEALED_SLOT);
  const destinations: Placed[] = story.destinations.map((_, j) => {
    const deg = free[j] ?? (free[free.length - 1] as number);
    return { p: at(deg, ARC), side: "right" };
  });
  const revealed: Placed = { p: at(facing, ARC), side: "right" };
  const unknownCount = story.connection?.unknown.length ?? 0;
  const unknown: Placed[] = [];
  for (let k = 0; k < unknownCount; k++) {
    unknown.push({ p: at(facing + (k - (unknownCount - 1) / 2) * 9, 320), side: "right" });
  }
  return {
    origin: [0, 0, 0],
    skills,
    destinations,
    revealed,
    unknown,
    openings(dest, count) {
      const angle = Math.atan2(dest[1], dest[0]);
      return Array.from({ length: count }, (_, k) => {
        const r = ARC + 48 + (k % 3) * 22;
        const a = angle + (Math.floor(k / 3) - (count / 3 - 1) / 2) * 0.035;
        return [snap(Math.cos(a) * r), snap(Math.sin(a) * r), 0] as Vec3;
      });
    },
    path(from, to, kind, i, j) {
      if (kind === "root") return octilinear(from, to, 0.5);
      if (kind === "reach") return octilinear(from, to, 0.25 + ((i + j) % 4) * 0.15);
      if (kind === "link") return octilinear(from, to, 0.2 + (i % 5) * 0.14);
      if (kind === "shadow") return octilinear(from, to, 0.6);
      return octilinear(from, to, 0.5);
    },
    widths: {
      root: [2.6, 2.0],
      reach: [1.4, 1.4],
      link: [2.0, 2.0],
      shadow: [1.2, 1.2],
      opening: [0.8, 0.8],
      fibre: [0, 0],
    },
    sizes: { origin: 9, skill: 5.5, destination: 7, revealed: 8.5, unknown: 5, opening: 2 },
  };
}

function view(vp: Viewport, story: Story): Camera {
  const k = fit(vp);
  if (story.phase === "ask") return [vp.w * (vp.narrow ? 0.5 : 0.28), vp.h * (vp.narrow ? 0.3 : 0.5), k, 0, 0, 0, 0, 0];
  if (vp.narrow) return [vp.w * 0.3, vp.h * 0.6, k * 0.55, 0, 0, 0, 0, 0];
  return [vp.w * 0.27, vp.h * 0.56, k * 0.92, 0, 0, 0, 0, 0];
}

const GLSL = {
  project: /* glsl */ `
vec2 project(vec3 p, out float scale) { scale = uCamA.z; return uCamA.xy + p.xy * uCamA.z; }
`,
  sway: /* glsl */ `
vec2 sway(vec2 px, float envelope) { return vec2(0.0); }
`,
  background: /* glsl */ `
float segment(vec2 p, vec2 a, vec2 b) {
  vec2 pa = p - a;
  vec2 ba = b - a;
  return length(pa - ba * clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0));
}
vec3 background(vec2 px) {
  vec3 col = vec3(0.009, 0.012, 0.024);
  float g = ${GRID.toFixed(1)} * uCamA.z;
  vec2 rel = (px - uCamA.xy) / g;
  vec2 near = (fract(rel + 0.5) - 0.5) * g;
  col += vec3(0.16, 0.27, 0.50) * exp(-dot(near, near) * 0.7) * 0.28;
  // The board: faint micro-traces at right angles and 45°, one per cell where the hash says so.
  float cellSize = g * 2.0;
  vec2 cell = floor((px - uCamA.xy) / cellSize);
  vec2 local = (px - uCamA.xy) - (cell + 0.5) * cellSize;
  float h = hash12(cell);
  float trace = 1e3;
  if (h > 0.45) {
    vec2 dir = h > 0.85 ? vec2(1.0, 1.0) : h > 0.7 ? vec2(1.0, -1.0) : h > 0.58 ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    trace = segment(local, -dir * cellSize * 0.5, dir * cellSize * 0.5);
  }
  float band = mod(uAmbient, 10.0) / 10.0 * (uRes.y + 500.0) - 250.0;
  float scan = exp(-pow((px.y - band) / 120.0, 2.0));
  col += vec3(0.10, 0.17, 0.34) * exp(-trace * trace * 0.6) * (0.16 + 0.35 * scan);
  col += vec3(0.04, 0.09, 0.20) * scan * 0.3;
  float od = length(px - uCamA.xy) / uRes.y;
  col += vec3(0.05, 0.11, 0.24) * exp(-od * od * 9.0) * mix(0.3, 0.8, step(0.5, uPhase));
  float ia = uTime - uIgnite;
  if (ia > 0.0 && ia < 1.6) {
    vec2 d = abs(px - uCamA.xy);
    float sq = max(d.x, d.y);
    float r = ia * uRes.y * 0.9;
    col += mix(BLUE, WHITE, 0.4) * exp(-pow((sq - r) / 5.0, 2.0)) * 0.4 * (1.0 - ia / 1.6);
  }
  vec2 v = px / uRes - 0.5;
  col *= 1.0 - 0.4 * dot(v, v) * 1.5;
  return col;
}
`,
  particle: /* glsl */ `
vec4 particle(vec4 seed, out float alpha) {
  float g = ${GRID.toFixed(1)} * uCamA.z;
  vec2 base = uCamA.xy + floor((seed.xy * uRes - uCamA.xy) / g + 0.5) * g;
  float ph = uAmbient * (0.22 + seed.z * 0.3) + seed.w * 6.283;
  alpha = pow(max(0.0, sin(ph)), 14.0) * 0.85 * mix(0.4, 1.0, step(0.5, uPhase));
  return vec4(base, 2.6, 0.0);
}
`,
  node: /* glsl */ `
float box(vec2 q) { vec2 a = abs(q); return max(a.x, a.y); }
float brackets(vec2 q, float b, float aa) {
  vec2 a = abs(q);
  float line = 1.0 - smoothstep(0.09, 0.09 + aa, abs(max(a.x, a.y) - b));
  return line * step(b * 0.58, min(a.x, a.y));
}
vec3 nodeLook(vec2 q, float kind, float state, float age, float flare, float sel, float seed, float px) {
  float aa = 1.2 / px;
  float sq = box(q);
  float diamond = abs(q.x) + abs(q.y);
  float r = length(q);
  vec3 col = vec3(0.0);
  if (kind < 0.5) {
    float lit = uPhase > 0.5 ? 1.0 : 0.6;
    float core = 1.0 - smoothstep(0.9 - aa, 0.9 + aa, sq);
    float ring1 = 1.0 - smoothstep(0.07, 0.07 + aa, abs(sq - 1.8));
    float ring2 = 1.0 - smoothstep(0.06, 0.06 + aa, abs(sq - 2.9));
    float ign = clamp(1.0 - (uTime - uIgnite) / 1.2, 0.0, 1.0) * step(uIgnite, uTime);
    col = WHITE * core * 1.3 + mix(BLUE, WHITE, 0.3) * (ring1 * 0.8 + ring2 * 0.45) * lit;
    col += mix(BLUE, WHITE, 0.4) * exp(-r * 0.7) * 0.45 * lit + WHITE * ign * exp(-r * 0.35) * 1.3;
    // Before the first answer the core sits in a socket with four stub traces; each keystroke
    // sends a packet out along them, and they brighten as the answer takes shape.
    float socket = 1.0 - step(0.5, uPhase);
    if (socket > 0.0) {
      vec2 a = abs(q);
      float len = 6.0 + min(uTyped, 14.0) * 0.6;
      float stub = max(
        (1.0 - smoothstep(0.08, 0.08 + aa, a.y)) * step(3.0, a.x) * step(a.x, len),
        (1.0 - smoothstep(0.08, 0.08 + aa, a.x)) * step(3.0, a.y) * step(a.y, len)
      );
      float along = max(a.x, a.y);
      float sent = uTime - uKey;
      float packet = sent > 0.0 && sent < 0.9 ? exp(-pow((along - 3.0 - sent * 16.0) / 0.5, 2.0)) : 0.0;
      col += journey(0.3) * stub * (0.35 + min(uTyped, 14.0) * 0.03 + packet * 2.0) * socket;
    }
  } else if (kind < 1.5) {
    vec3 c = journey(0.35);
    if (state > 0.5) {
      col = mix(c, WHITE, 0.55) * (1.0 - smoothstep(0.9 - aa, 0.9 + aa, sq)) * 1.25 + c * exp(-r * 0.85) * 0.7;
    } else {
      float ring = 1.0 - smoothstep(0.14, 0.14 + aa, abs(sq - 0.85));
      float dot_ = 1.0 - smoothstep(0.25 - aa, 0.25 + aa, sq);
      col = c * (ring * 0.85 + dot_ * 0.5) + c * exp(-r * 1.4) * 0.2;
    }
  } else if (kind < 3.5) {
    float big = kind > 2.5 ? 1.0 : 0.0;
    float term = 1.0 - smoothstep(1.15 - aa, 1.15 + aa, diamond);
    float hot = 1.0 - smoothstep(0.55 - aa, 0.55 + aa, diamond);
    col = mix(ORANGE, vec3(1.0, 0.85, 0.6), 0.45) * hot * 0.95 + ORANGE * term * 0.5
        + ORANGE * (exp(-r * 0.85) * 0.6 + exp(-r * r * 0.2) * 0.2);
    // The revelation locks on: brackets close in on the newly lit destination, then settle into
    // a steady glow that singles it out by light.
    float close = smoothstep(0.0, 0.7, age);
    float hold = big * clamp(1.0 - (age - 1.6) / 0.6, 0.0, 1.0);
    col += mix(WHITE, ORANGE, 0.35) * brackets(q, mix(9.0, 2.6, close), aa) * hold * 1.2;
    col += ORANGE * big * (exp(-r * 0.4) * clamp(1.0 - age / 1.0, 0.0, 1.0) * 1.8 + exp(-r * 0.4) * 0.4);
    if (sel > 0.5) col += TEAL * brackets(q, 2.6, aa) * 1.4;
  } else if (kind < 4.5) {
    float edge = 1.0 - smoothstep(0.12, 0.12 + aa, abs(sq - 0.9));
    float dash = step(0.0, sin((q.x + q.y) * 7.0));
    col = SHADOW * edge * dash * 0.95 + SHADOW * exp(-r * 1.5) * 0.1;
  } else {
    col = mix(WHITE, VIOLET, 0.3) * ((1.0 - smoothstep(1.0 - aa, 1.0 + aa, sq)) * 0.75 + exp(-r * 1.4) * 0.2);
  }
  col += mix(WHITE, journey(0.35), 0.4) * flare * exp(-r * 0.55) * 1.2;
  return col;
}
`,
  pulse: /* glsl */ `
float pulse(float dist, float state) {
  float k = mod(dist - uAmbient * 110.0, 170.0);
  return smoothstep(0.0, 2.0, k) * (1.0 - smoothstep(10.0, 14.0, k)) * 2.2;
}
`,
};

function stillBackdrop(vp: Viewport, cam: Camera): string {
  const g = GRID * cam[2];
  const ox = ((cam[0] % g) + g) % g;
  const oy = ((cam[1] % g) + g) % g;
  return `
  <defs>
    <pattern id="c-dots" x="${ox.toFixed(1)}" y="${oy.toFixed(1)}" width="${g.toFixed(2)}" height="${g.toFixed(2)}" patternUnits="userSpaceOnUse">
      <circle cx="0" cy="0" r="1" fill="#22407a"/>
      <circle cx="${g.toFixed(2)}" cy="0" r="1" fill="#22407a"/>
      <circle cx="0" cy="${g.toFixed(2)}" r="1" fill="#22407a"/>
      <circle cx="${g.toFixed(2)}" cy="${g.toFixed(2)}" r="1" fill="#22407a"/>
    </pattern>
    <pattern id="c-board" x="${ox.toFixed(1)}" y="${oy.toFixed(1)}" width="${(g * 6).toFixed(2)}" height="${(g * 6).toFixed(2)}" patternUnits="userSpaceOnUse">
      <path d="M0 ${g} H${g * 2} M${g * 3} ${g * 4} L${g * 5} ${g * 6} M${g * 4} 0 V${g * 2} M${g} ${g * 3} L${g * 2} ${g * 2}" stroke="#13254f" stroke-width="1.2" fill="none"/>
    </pattern>
  </defs>
  <rect width="${vp.w}" height="${vp.h}" fill="#03050b"/>
  <rect width="${vp.w}" height="${vp.h}" fill="url(#c-board)"/>
  <rect width="${vp.w}" height="${vp.h}" fill="url(#c-dots)"/>`;
}

export const circuit: Direction = {
  id: "circuit",
  name: "Circuit",
  blurb: "A living circuit: exact, glowing, powered by you.",
  particles: 900,
  geometry,
  view,
  project(p, cam) {
    return { x: cam[0] + p[0] * cam[2], y: cam[1] + p[1] * cam[2], scale: cam[2], visible: true };
  },
  glsl: GLSL,
  stillBackdrop,
};
