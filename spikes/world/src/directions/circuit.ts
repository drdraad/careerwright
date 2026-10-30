// Circuit: cybernetic first. A precise luminous circuit on an instrument grid. Traces are routed
// at right angles with rounded corners; light travels along them as packets; the revelation is a
// lock-on. Layout is in pixels at a 900 px tall design size, relative to the person.
import { type Camera, type Direction, type Geometry, type Placed, type Viewport, skillSlots } from "../direction.ts";
import { type Vec3, seeded } from "../scene.ts";
import type { Story } from "../story.ts";

const GRID = 24;
const CORNER = 12;

const fit = (vp: Viewport): number => Math.min(vp.h, vp.w * 0.62) / 900;

/** Rounds each corner of an orthogonal route with a short arc. */
function route(corners: readonly Vec3[]): Vec3[] {
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
    for (let s = 0; s <= 6; s++) {
      const t = s / 6;
      const u = 1 - t;
      out.push([u * u * p[0] + 2 * u * t * b[0] + t * t * q[0], u * u * p[1] + 2 * u * t * b[1] + t * t * q[1], 0]);
    }
  }
  out.push(corners[corners.length - 1] as Vec3);
  return out;
}

function geometry(_vp: Viewport, story: Story): Geometry {
  const skillCount = story.role?.skills.length ?? 8;
  const slots = skillSlots(story, true);
  const skills: Placed[] = [];
  for (let i = 0; i < skillCount; i++) {
    const slot = slots[i] ?? i;
    skills.push({ p: [250, -380 + (620 * slot) / Math.max(1, skillCount - 1), 0], side: "right" });
  }
  const destCount = story.destinations.length;
  const destinations: Placed[] = [];
  for (let j = 0; j < destCount; j++) {
    destinations.push({ p: [610, -140 + (400 * j) / Math.max(1, destCount - 1), 0], side: "right" });
  }
  const unknownCount = story.connection?.unknown.length ?? 0;
  const unknown: Placed[] = [];
  for (let k = 0; k < unknownCount; k++) unknown.push({ p: [690, -290 + k * 52, 0], side: "right" });
  const revealed: Placed = { p: [810, -340, 0], side: "right" };
  return {
    origin: [0, 0, 0],
    skills,
    destinations,
    revealed,
    unknown,
    openings(dest, count) {
      return Array.from({ length: count }, (_, k) => [
        dest[0] + 190 + (k % 6) * 14,
        dest[1] - 18 + Math.floor(k / 6) * 14,
        0,
      ] as Vec3);
    },
    path(from, to, kind, i, j) {
      if (kind === "root") {
        const lane = 110 + i * 9;
        return route([from, [lane, from[1], 0], [lane, to[1], 0], to]);
      }
      if (kind === "reach") {
        const lane = 380 + j * 16 + (i % 3) * 3;
        return route([from, [lane, from[1], 0], [lane, to[1], 0], to]);
      }
      if (kind === "link") {
        const order = story.connection?.shared.indexOf(story.role?.skills[i] ?? "") ?? 0;
        const lane = 320 + order * 9;
        const high = -410 + order * 8;
        return route([from, [lane, from[1], 0], [lane, high, 0], [to[0], high, 0], to]);
      }
      if (kind === "shadow") {
        if (j === 0) {
          const lane = 40 + i * 8;
          return route([from, [lane, from[1], 0], [lane, to[1], 0], to]);
        }
        const lane = to[0] - 30 - i * 7;
        return route([from, [from[0], from[1] - 14 - i * 4, 0], [lane, from[1] - 14 - i * 4, 0], [lane, to[1], 0], to]);
      }
      const rand = seeded(`pin:${i}:${j}`);
      const turn = from[0] + 120 + rand() * 30;
      return route([from, [turn, from[1], 0], [turn, to[1], 0], to]);
    },
    widths: {
      root: [2.4, 2.0],
      reach: [1.4, 1.4],
      link: [2.0, 2.0],
      shadow: [1.2, 1.2],
      opening: [0.8, 0.8],
      fibre: [0, 0],
    },
    sizes: { origin: 9, skill: 5.5, destination: 6.5, revealed: 8, unknown: 5, opening: 2 },
  };
}

function view(vp: Viewport, story: Story): Camera {
  const k = fit(vp);
  if (story.phase === "ask") return [vp.w * 0.5, vp.h * (vp.narrow ? 0.32 : 0.38), k, 0, 0, 0, 0, 0];
  if (vp.narrow) return [vp.w * 0.06, vp.h * 0.62, k * 0.9, 0, 0, 0, 0, 0];
  return [vp.w * 0.11, vp.h * 0.6, k * 0.92, 0, 0, 0, 0, 0];
}

const GLSL = {
  project: /* glsl */ `
vec2 project(vec3 p, out float scale) { scale = uCamA.z; return uCamA.xy + p.xy * uCamA.z; }
`,
  background: /* glsl */ `
vec3 background(vec2 px) {
  vec3 col = vec3(0.009, 0.012, 0.024);
  float g = ${GRID.toFixed(1)} * uCamA.z;
  vec2 rel = (px - uCamA.xy) / g;
  vec2 near = (fract(rel + 0.5) - 0.5) * g;
  col += vec3(0.16, 0.27, 0.50) * exp(-dot(near, near) * 0.7) * 0.42;
  vec2 major = abs(fract(rel / 5.0 + 0.5) - 0.5) * 5.0 * g;
  col += vec3(0.07, 0.12, 0.25) * exp(-min(major.x, major.y) * 1.1) * 0.35;
  float band = mod(uAmbient, 10.0) / 10.0 * (uRes.y + 500.0) - 250.0;
  col += vec3(0.04, 0.09, 0.20) * exp(-pow((px.y - band) / 120.0, 2.0)) * 0.45;
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
    float boot = clamp((uTime - uIgnite) / 0.5, 0.0, 1.0);
    float ign = clamp(1.0 - (uTime - uIgnite) / 1.2, 0.0, 1.0) * step(uIgnite, uTime);
    col = WHITE * core * 1.3 + mix(BLUE, WHITE, 0.3) * (ring1 * 0.8 + ring2 * 0.45 * step(0.5, boot)) * lit;
    col += mix(BLUE, WHITE, 0.4) * exp(-r * 0.7) * 0.45 * lit + WHITE * ign * exp(-r * 0.35) * 1.3;
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
    col = mix(ORANGE, WHITE, 0.55) * term * 1.25 + ORANGE * (exp(-r * 0.85) * 0.6 + exp(-r * r * 0.2) * 0.2);
    // The revelation locks on: brackets close in on the newly lit destination, then settle.
    float close = smoothstep(0.0, 0.7, age);
    float hold = big * clamp(1.0 - (age - 1.6) / 0.6, 0.0, 1.0);
    col += mix(WHITE, ORANGE, 0.35) * brackets(q, mix(9.0, 2.6, close), aa) * hold * 1.2;
    col += ORANGE * big * exp(-r * 0.4) * clamp(1.0 - age / 1.0, 0.0, 1.0) * 1.8;
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
      <circle cx="0" cy="0" r="1.1" fill="#2b4a8a"/>
      <circle cx="${g.toFixed(2)}" cy="0" r="1.1" fill="#2b4a8a"/>
      <circle cx="0" cy="${g.toFixed(2)}" r="1.1" fill="#2b4a8a"/>
      <circle cx="${g.toFixed(2)}" cy="${g.toFixed(2)}" r="1.1" fill="#2b4a8a"/>
    </pattern>
    <pattern id="c-major" x="${ox.toFixed(1)}" y="${oy.toFixed(1)}" width="${(g * 5).toFixed(2)}" height="${(g * 5).toFixed(2)}" patternUnits="userSpaceOnUse">
      <path d="M0 0 H${(g * 5).toFixed(2)} M0 0 V${(g * 5).toFixed(2)}" stroke="#13234a" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="${vp.w}" height="${vp.h}" fill="#03050b"/>
  <rect width="${vp.w}" height="${vp.h}" fill="url(#c-major)"/>
  <rect width="${vp.w}" height="${vp.h}" fill="url(#c-dots)"/>`;
}

export const circuit: Direction = {
  id: "circuit",
  name: "Circuit",
  blurb: "A precise, glowing circuit with exact readouts.",
  font: "sora",
  particles: 900,
  geometry,
  view,
  project(p, cam) {
    return { x: cam[0] + p[0] * cam[2], y: cam[1] + p[1] * cam[2], scale: cam[2], visible: true };
  },
  glsl: GLSL,
  stillBackdrop,
};
