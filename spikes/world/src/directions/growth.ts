// Growth: organic first. A network of roots and nerves grown from the person. Before the first
// answer the light is a seed whose tendrils reach further with every keystroke; after it, roots
// grow and sway gently, and a pulse beats outward through them like a signal along nerves.
import { type Camera, type Direction, type Geometry, type Placed, type Viewport, skillSlots } from "../direction.ts";
import { type LabelSide, type Vec3, cubic, seeded } from "../scene.ts";
import type { Story } from "../story.ts";

const DEG = Math.PI / 180;

const unit = (vp: Viewport): number => Math.min(vp.h, vp.w * 0.62);

const polar = (deg: number, rx: number, ry: number): Vec3 => [
  Math.cos(deg * DEG) * rx,
  Math.sin(deg * DEG) * ry,
  0,
];

const sideFor = (deg: number): LabelSide => (deg < -112 ? "left" : deg > -68 ? "right" : "above");

function organic(from: Vec3, to: Vec3, seed: number, bend: number, outward: boolean): Vec3[] {
  const rand = seeded(`growth:${seed}:${from[0].toFixed(1)}:${to[0].toFixed(1)}`);
  const dx = to[0] - from[0];
  const dy = to[1] - from[1];
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const w1 = (rand() - 0.5) * bend * len;
  const w2 = (rand() - 0.5) * bend * len;
  let c1: Vec3 = [from[0] + dx * 0.33 + nx * w1, from[1] + dy * 0.33 + ny * w1, 0];
  let c2: Vec3 = [from[0] + dx * 0.72 + nx * w2, from[1] + dy * 0.72 + ny * w2, 0];
  if (outward) {
    // Leave the skill heading away from the person and arrive from the person's side, as a
    // root or nerve would, so the network reads as grown from the person.
    const fl = Math.hypot(from[0], from[1]) || 1;
    const tl = Math.hypot(to[0], to[1]) || 1;
    c1 = [from[0] + (from[0] / fl) * len * 0.3, from[1] + (from[1] / fl) * len * 0.3, 0];
    c2 = [to[0] - (to[0] / tl) * len * 0.3 + nx * w2 * 0.5, to[1] - (to[1] / tl) * len * 0.3 + ny * w2 * 0.5, 0];
  }
  const steps = Math.max(10, Math.min(48, Math.round(len / 12)));
  const phase = rand() * Math.PI * 2;
  const wobble = Math.min(10, len * 0.025);
  return cubic(from, c1, c2, to, steps).map((p, i) => {
    const t = i / steps;
    const w = Math.sin(t * Math.PI * 3 + phase) * wobble * Math.sin(t * Math.PI);
    return [p[0] + nx * w, p[1] + ny * w, 0];
  });
}

function geometry(vp: Viewport, story: Story): Geometry {
  const u = unit(vp);
  const skillCount = story.role?.skills.length ?? 8;
  const slots = skillSlots(story, false);
  const skills: Placed[] = [];
  for (let i = 0; i < skillCount; i++) {
    const slot = slots[i] ?? i;
    const deg = -152 + (138 * slot) / Math.max(1, skillCount - 1);
    const k = slot % 2 === 0 ? 1 : 1.36;
    skills.push({ p: polar(deg, 0.29 * u * 1.12 * k, 0.29 * u * k), side: sideFor(deg) });
  }
  const destCount = story.destinations.length;
  const destinations: Placed[] = [];
  for (let j = 0; j < destCount; j++) {
    const deg = -168 + (58 * j) / Math.max(1, destCount - 1);
    destinations.push({ p: polar(deg, 0.62 * u, 0.66 * u), side: j === 0 ? "above" : "left" });
  }
  // What is not known yet hangs just beyond the revealed destination, in shadow.
  const revealed: Placed = { p: polar(-62, 0.6 * u, 0.7 * u), side: "left" };
  const unknownCount = story.connection?.unknown.length ?? 0;
  const unknown: Placed[] = [];
  for (let k = 0; k < unknownCount; k++) {
    const dx = (-0.15 + (0.3 * k) / Math.max(1, unknownCount - 1)) * u;
    unknown.push({ p: [revealed.p[0] + dx, revealed.p[1] - 0.15 * u, 0], side: "above" });
  }
  return {
    origin: [0, 0, 0],
    skills,
    destinations,
    revealed,
    unknown,
    openings(dest, count, place) {
      const rand = seeded(`growth-openings:${place}`);
      const base = Math.atan2(dest[1], dest[0]);
      return Array.from({ length: count }, (_, k) => {
        const a = base + (k / count - 0.5) * 2.2 + (rand() - 0.5) * 0.15;
        const r = 34 + rand() * 46 + (k % 3) * 10;
        return [dest[0] + Math.cos(a) * r, dest[1] + Math.sin(a) * r, 0] as Vec3;
      });
    },
    path(from, to, kind, i, j) {
      const seed = i * 31 + j * 7 + (kind === "root" ? 0 : kind === "reach" ? 1000 : 2000);
      if (kind === "root") return organic(from, to, seed, 0.35, false);
      if (kind === "reach" || kind === "link") return organic(from, to, seed, 0.3, true);
      return organic(from, to, seed, 0.25, false);
    },
    fibres(points, seed) {
      const rand = seeded(`fibres:${seed}`);
      const out: Vec3[][] = [];
      for (const at of [0.38, 0.6, 0.8]) {
        const idx = Math.floor(at * (points.length - 1));
        const p = points[idx] as Vec3;
        const q = points[Math.min(points.length - 1, idx + 1)] as Vec3;
        const ang = Math.atan2(q[1] - p[1], q[0] - p[0]) + (rand() < 0.5 ? -1 : 1) * (0.5 + rand() * 0.4);
        const len = u * (0.035 + rand() * 0.05);
        const end: Vec3 = [p[0] + Math.cos(ang) * len, p[1] + Math.sin(ang) * len, 0];
        out.push(organic(p, end, seed * 13 + Math.round(at * 100), 0.5, false));
      }
      return out;
    },
    widths: {
      root: [3.6, 1.6],
      reach: [1.5, 1.0],
      link: [2.4, 1.5],
      shadow: [1.3, 1.3],
      opening: [0.8, 0.6],
      fibre: [1.0, 0.3],
    },
    sizes: { origin: 9, skill: 5.5, destination: 7, revealed: 9, unknown: 5, opening: 2.2 },
  };
}

function view(vp: Viewport, story: Story): Camera {
  // Before the first answer the seed sits left of centre, with the question beside it.
  if (story.phase === "ask") return [vp.w * (vp.narrow ? 0.5 : 0.3), vp.h * (vp.narrow ? 0.3 : 0.52), 1, 0, 0, 0, 0, 0];
  if (vp.narrow) return [vp.w * 0.5, vp.h * 0.62, 0.62, 0, 0, 0, 0, 0];
  // The revelation shifts the view a little, making room for its card: the world stays.
  if (story.phase === "revealed") return [vp.w * 0.39, vp.h * 0.89, 0.94, 0, 0, 0, 0, 0];
  return [vp.w * 0.45, vp.h * 0.87, 1, 0, 0, 0, 0, 0];
}

const GLSL = {
  project: /* glsl */ `
vec2 project(vec3 p, out float scale) { scale = uCamA.z; return uCamA.xy + p.xy * uCamA.z; }
`,
  sway: /* glsl */ `
vec2 sway(vec2 px, float envelope) {
  return vec2(sin(px.y * 0.013 + uAmbient * 0.7), cos(px.x * 0.011 + uAmbient * 0.55)) * 2.8 * envelope;
}
`,
  background: /* glsl */ `
vec3 background(vec2 px) {
  vec2 uv = px / uRes.y;
  vec3 col = vec3(0.010, 0.013, 0.028);
  float n = vnoise(uv * 2.4 + vec2(uAmbient * 0.004, -uAmbient * 0.002)) * 0.65
          + vnoise(uv * 6.0 - vec2(uAmbient * 0.006, 0.0)) * 0.35;
  col += mix(BLUE, VIOLET, clamp(uv.x * 0.6, 0.0, 1.0)) * pow(n, 3.0) * 0.07;
  vec2 o = uCamA.xy;
  float d = length(px - o) / uRes.y;
  float lit = mix(0.35, 1.0, step(0.5, uPhase));
  col += vec3(0.06, 0.13, 0.28) * exp(-d * d * 7.0) * 0.5 * lit;
  float ia = uTime - uIgnite;
  if (ia > 0.0 && ia < 1.8) {
    float r = ia * uRes.y * 0.75;
    float w = 4.0 + ia * 26.0;
    float ring = exp(-pow((length(px - o) - r) / w, 2.0));
    col += mix(WHITE, BLUE, 0.5) * ring * 0.32 * (1.0 - ia / 1.8);
  }
  vec2 v = px / uRes - 0.5;
  col *= 1.0 - 0.5 * dot(v, v) * 1.6;
  return col;
}
`,
  particle: /* glsl */ `
vec4 particle(vec4 seed, out float alpha) {
  float t = uAmbient;
  float h = uRes.y + 60.0;
  float speed = 5.0 + seed.z * 9.0;
  float y = mod(seed.y * h - t * speed, h) - 30.0;
  float x = seed.x * uRes.x + sin(t * 0.25 + seed.w * 6.283) * 14.0;
  alpha = (0.1 + 0.32 * seed.w) * (0.65 + 0.35 * sin(t * (0.3 + seed.z * 0.5) + seed.x * 40.0));
  alpha *= mix(0.5, 1.0, step(0.5, uPhase));
  return vec4(x, y, 1.0 + seed.z * 2.0, 0.0);
}
`,
  node: /* glsl */ `
vec3 nodeLook(vec2 q, float kind, float state, float age, float flare, float sel, float seed, float px) {
  float r = length(q);
  float aa = 1.2 / px;
  float breathe = 0.82 + 0.18 * sin(uAmbient * 1.05 + seed * 6.283);
  float disc = 1.0 - smoothstep(1.0 - aa, 1.0 + aa, r);
  vec3 col = vec3(0.0);
  if (kind < 0.5) {
    float lit = uPhase > 0.5 ? 1.0 : 0.6;
    float ign = clamp(1.0 - (uTime - uIgnite) / 1.4, 0.0, 1.0) * step(uIgnite, uTime);
    col = WHITE * disc * 1.3
        + mix(BLUE, WHITE, 0.4) * (exp(-r * r * 0.3) * 0.7 + exp(-r * 0.75) * 0.3) * breathe * lit;
    col += WHITE * ign * exp(-r * 0.35) * 1.4;
    // The seed's tendrils: before the first answer they reach a little further with every
    // keystroke, then give way to the roots. Atmosphere: they carry no state.
    float seedTime = 1.0 - step(0.5, uPhase);
    if (seedTime > 0.0) {
      float reach = 3.2 + min(uTyped, 14.0) * 0.75;
      float a = atan(q.y, q.x);
      float tendrils = 0.0;
      for (int i = 0; i < 7; i++) {
        float fi = float(i);
        float bend = 0.32 * sin(r * 0.55 + uAmbient * 0.6 + fi * 1.7);
        float d = mod(a - (fi * 0.8976 + 0.3 + bend) + 3.14159, 6.28318) - 3.14159;
        float across = abs(d) * r * px;
        float along = smoothstep(1.0, 1.8, r) * (1.0 - smoothstep(reach - 1.6, reach, r));
        tendrils += exp(-across * across * 0.35) * along * (1.0 - r / (reach + 1.0));
      }
      col += mix(BLUE, VIOLET, clamp(r / 12.0, 0.0, 1.0)) * tendrils * 0.9 * seedTime;
    }
  } else if (kind < 1.5) {
    vec3 c = journey(0.35);
    if (state > 0.5) {
      col = mix(c, WHITE, 0.55) * disc * 1.2 + c * exp(-r * 0.9) * 0.7 * breathe;
    } else {
      float ring = 1.0 - smoothstep(0.16, 0.16 + aa, abs(r - 0.85));
      col = c * ring * 0.75 + c * exp(-r * 1.3) * 0.22;
    }
  } else if (kind < 3.5) {
    // Destinations are warm orange lights, as in the reference image: a hot core, never white.
    float big = kind > 2.5 ? 1.0 : 0.0;
    float core = 1.0 - smoothstep(0.55 - aa, 0.55 + aa, r);
    col = mix(ORANGE, vec3(1.0, 0.85, 0.6), 0.45) * core * 0.95 + ORANGE * disc * 0.45
        + ORANGE * (exp(-r * 0.8) * 0.6 + exp(-r * r * 0.18) * 0.3) * breathe;
    // The revealed destination keeps a steady wider glow once settled: it stands out by light.
    col += ORANGE * big * exp(-r * 0.32) * 0.35;
    col += ORANGE * big * exp(-r * 0.4) * clamp(1.0 - age / 1.2, 0.0, 1.0) * 2.0;
    if (sel > 0.5) {
      float lock = 1.0 - smoothstep(0.07, 0.07 + aa, abs(r - 2.3));
      col += TEAL * lock * 1.3;
    }
  } else if (kind < 4.5) {
    float ang = atan(q.y, q.x);
    float dash = step(0.0, sin(ang * 8.0));
    float ring = 1.0 - smoothstep(0.12, 0.12 + aa, abs(r - 0.9));
    col = SHADOW * ring * dash * 0.9 + SHADOW * exp(-r * 1.5) * 0.12;
  } else {
    col = mix(WHITE, VIOLET, 0.3) * (disc * 0.7 + exp(-r * 1.4) * 0.25);
  }
  col += mix(WHITE, journey(0.35), 0.4) * flare * exp(-r * 0.55) * 1.2;
  return col;
}
`,
  pulse: /* glsl */ `
float pulse(float dist, float state) {
  float front = mod(uAmbient, 4.2) / 4.2 * 1500.0 - 60.0;
  return exp(-pow((dist - front) / 55.0, 2.0)) * 1.6;
}
`,
};

function stillBackdrop(vp: Viewport, cam: Camera): string {
  const [ox, oy] = cam;
  return `
  <defs>
    <radialGradient id="g-origin-glow" cx="${ox}" cy="${oy}" r="${vp.h * 0.55}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#0f2246" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#03050a" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g-vignette" cx="50%" cy="50%" r="75%">
      <stop offset="0.55" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.55"/>
    </radialGradient>
  </defs>
  <rect width="${vp.w}" height="${vp.h}" fill="#03050b"/>
  <rect width="${vp.w}" height="${vp.h}" fill="url(#g-origin-glow)"/>
  <rect width="${vp.w}" height="${vp.h}" fill="url(#g-vignette)"/>`;
}

export const growth: Direction = {
  id: "growth",
  name: "Growth",
  blurb: "A living network of roots and nerves, grown from you.",
  particles: 1600,
  geometry,
  view,
  project(p, cam) {
    return { x: cam[0] + p[0] * cam[2], y: cam[1] + p[1] * cam[2], scale: cam[2], visible: true };
  },
  glsl: GLSL,
  stillBackdrop,
};
