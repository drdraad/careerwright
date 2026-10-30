// Horizon: journey first. A dark plain under a faint horizon, like the reference image. The
// person stands in the foreground; destinations are lights on the horizon; the view travels.
// Layout is in world units: x across, y height, z depth. The camera is
// [camX, camZ, horizon y (px), focal length (px), centre x (px), eye height, 0, 0].
import { type Camera, type Direction, type Geometry, type Placed, type Viewport, skillSlots } from "../direction.ts";
import { type Vec3, cubic, seeded } from "../scene.ts";
import type { Story } from "../story.ts";

const DEG = Math.PI / 180;
const EYE = 1;
const ORIGIN_Z = 1.7;

/** Narrow screens squeeze the world sideways rather than shrinking it. */
const across = (vp: Viewport): number => Math.min(1, vp.w / vp.h / 1.6);

function geometry(vp: Viewport, story: Story): Geometry {
  const kx = across(vp);
  const origin: Vec3 = [-0.75 * kx, 0.04, ORIGIN_Z];
  const skillCount = story.role?.skills.length ?? 8;
  const slots = skillSlots(story, false);
  const skills: Placed[] = [];
  for (let i = 0; i < skillCount; i++) {
    const slot = slots[i] ?? i;
    const deg = -48 + (106 * slot) / Math.max(1, skillCount - 1);
    const near = slot % 2 === 0;
    const r = near ? 1.45 : 2.5;
    skills.push({
      p: [origin[0] + Math.sin(deg * DEG) * r * 1.25 * kx, 0.02, ORIGIN_Z + Math.cos(deg * DEG) * r],
      side: near ? "below" : "above",
    });
  }
  // Destinations line the horizon on both sides, leaving the far centre for the revelation.
  // Their order is by title; where one sits never means how near or how good it is.
  const destCount = story.destinations.length;
  const leftCount = Math.ceil(destCount / 2);
  const destinations: Placed[] = [];
  for (let j = 0; j < destCount; j++) {
    const onLeft = j < leftCount;
    const k = onLeft ? j : j - leftCount;
    const n = onLeft ? leftCount : destCount - leftCount;
    const t = n > 1 ? k / (n - 1) : 0.5;
    const x = onLeft ? -16 + 11 * t : 5 + 4.5 * t;
    destinations.push({ p: [x * kx, 0.25, 16 + (j % 2) * 2.2], side: "above" });
  }
  // What is not known yet: dark stepping stones on the ground between the person and it.
  const unknownCount = story.connection?.unknown.length ?? 0;
  const unknown: Placed[] = [];
  const depths = [5, 7.5, 12, 17];
  for (let k = 0; k < unknownCount; k++) {
    unknown.push({ p: [(2.2 + k) * kx, 0.02, depths[k] ?? 5 + k * 4], side: "right" });
  }
  return {
    origin,
    skills,
    destinations,
    revealed: { p: [1.5 * kx, 0.5, 30], side: "above" },
    unknown,
    openings(dest, count, place) {
      const rand = seeded(`horizon-openings:${place}`);
      return Array.from({ length: count }, () => [
        dest[0] + (rand() - 0.5) * 4.4 * kx,
        0.03,
        dest[2] + (rand() - 0.5) * 5,
      ] as Vec3);
    },
    path(from, to, kind, i, j) {
      const rand = seeded(`horizon:${kind}:${i}:${j}`);
      const dz = to[2] - from[2];
      if (kind === "root" || kind === "shadow") {
        const jx = (rand() - 0.5) * 0.4;
        const c1: Vec3 = [from[0] + (to[0] - from[0]) * 0.2 + jx, 0.02, from[2] + dz * 0.45];
        const c2: Vec3 = [from[0] + (to[0] - from[0]) * 0.75, 0.02, from[2] + dz * 0.8];
        return lift(cubic(from, c1, c2, to, 24), from, to);
      }
      if (kind === "opening") {
        const c: Vec3 = [(from[0] + to[0]) / 2, 0.03, (from[2] + to[2]) / 2 - 0.4];
        return lift(cubic(from, c, c, to, 8), from, to);
      }
      // Long sweeping trails: forward first, then across to the light, rising at the end.
      const sway = (rand() - 0.5) * 1.2;
      const c1: Vec3 = [from[0] + sway, 0.02, from[2] + dz * 0.42];
      const c2: Vec3 = [to[0] - sway * 0.5, 0.02, from[2] + dz * 0.78];
      return lift(cubic(from, c1, c2, to, 56), from, to);
    },
    widths: {
      root: [0.014, 0.012],
      reach: [0.011, 0.075],
      link: [0.015, 0.1],
      shadow: [0.01, 0.045],
      opening: [0.03, 0.03],
      fibre: [0, 0],
    },
    sizes: { origin: 0.032, skill: 0.026, destination: 0.21, revealed: 0.45, unknown: 0.05, opening: 0.05 },
  };
}

/** Trails run on the ground and rise to the light only at the end. */
function lift(points: Vec3[], from: Vec3, to: Vec3): Vec3[] {
  const n = points.length - 1;
  return points.map((p, i) => {
    const t = i / n;
    return [p[0], from[1] + (to[1] - from[1]) * t ** 4, p[2]] as Vec3;
  });
}

function view(vp: Viewport, story: Story): Camera {
  const kx = across(vp);
  const f = vp.h * (vp.narrow ? 0.56 : 0.62);
  if (story.phase === "ask") return [-0.75 * kx, -0.25, vp.h * 0.32, f, vp.w * 0.5, EYE, 0, 0];
  // The revelation travels a short way out across the plain, towards the newly lit destination.
  if (story.phase === "revealed") return [0.3 * kx, 0.2, vp.h * 0.35, f, vp.w * 0.46, EYE, 0, 0];
  return [0, 0, vp.h * 0.36, f, vp.w * (vp.narrow ? 0.5 : 0.46), EYE, 0, 0];
}

function project(p: Vec3, cam: Camera) {
  const d = p[2] - cam[1];
  if (d < 0.05) return { x: -1e5, y: -1e5, scale: 0, visible: false };
  const scale = cam[3] / d;
  return { x: cam[4] + (p[0] - cam[0]) * scale, y: cam[2] + (cam[5] - p[1]) * scale, scale, visible: true };
}

const GLSL = {
  project: /* glsl */ `
vec2 project(vec3 p, out float scale) {
  float d = p.z - uCamA.y;
  if (d < 0.05) { scale = 0.0; return vec2(-1e5); }
  scale = uCamA.w / d;
  return vec2(uCamB.x + (p.x - uCamA.x) * scale, uCamA.z + (uCamB.y - p.y) * scale);
}
`,
  background: /* glsl */ `
vec3 background(vec2 px) {
  float hy = uCamA.z;
  float f = uCamA.w;
  float above = hy - px.y;
  vec3 col = vec3(0.008, 0.011, 0.024);
  col += vec3(0.06, 0.10, 0.24) * exp(-abs(above) / 90.0) * 0.55;
  col += vec3(0.22, 0.16, 0.42) * exp(-abs(above) / 14.0) * 0.25;
  // The ground, computed for every pixel so its derivatives stay well defined.
  float depth = f * uCamB.y / max(px.y - hy, 0.25);
  vec2 g = vec2(uCamA.x + (px.x - uCamB.x) * depth / f, uCamA.y + depth);
  vec2 w = max(fwidth(g), vec2(1e-4));
  vec2 cell = abs(fract(g - 0.5) - 0.5) / w;
  float line = 1.0 - min(min(cell.x, cell.y), 1.0);
  if (above > 0.0) {
    vec2 c = floor(px / 46.0);
    float h = hash12(c);
    if (h > 0.82) {
      vec2 sp = (c + vec2(hash12(c + 3.1), hash12(c + 7.7))) * 46.0;
      float d = length(px - sp);
      float tw = 0.6 + 0.4 * sin(uAmbient * (0.3 + h * 0.4) + h * 50.0);
      col += WHITE * exp(-d * d * 0.8) * tw * (h - 0.8) * 3.0 * smoothstep(0.0, 90.0, above);
    }
  } else {
    float fade = exp(-depth * 0.1) * smoothstep(0.0, 3.0, -above);
    col += vec3(0.09, 0.16, 0.36) * line * 0.55 * fade;
    col += vec3(0.04, 0.06, 0.15) * exp(above / 36.0) * 0.7;
    float od = length(g - uOrigin.xz);
    col += vec3(0.10, 0.18, 0.40) * exp(-od * od * 1.2) * mix(0.35, 0.9, step(0.5, uPhase));
    float ia = uTime - uIgnite;
    if (ia > 0.0 && ia < 2.6) {
      float r = ia * 5.0;
      float ring = exp(-pow((od - r) / (0.06 + ia * 0.22), 2.0));
      col += mix(BLUE, WHITE, 0.35) * ring * (1.0 - ia / 2.6) * 0.9 * exp(-depth * 0.05);
    }
  }
  vec2 v = px / uRes - 0.5;
  col *= 1.0 - 0.45 * dot(v, v) * 1.5;
  return col;
}
`,
  particle: /* glsl */ `
vec4 particle(vec4 seed, out float alpha) {
  float span = 26.0;
  float rel = 0.35 + mod(seed.z * span - uAmbient * 0.32, span);
  float z = uCamA.y + rel;
  float x = uCamA.x + (seed.x - 0.5) * (rel * 1.9 + 2.0);
  float y = seed.y * (0.15 + rel * 0.09);
  float s;
  vec2 p = project(vec3(x, y, z), s);
  alpha = (0.25 + 0.45 * seed.w) * smoothstep(0.35, 2.2, rel) * smoothstep(span, span * 0.55, rel);
  alpha *= mix(0.45, 1.0, step(0.5, uPhase));
  return vec4(p, clamp(0.022 * s, 0.8, 3.2), 0.0);
}
`,
  node: /* glsl */ `
vec3 nodeLook(vec2 q, float kind, float state, float age, float flare, float sel, float seed, float px) {
  float r = length(q);
  float aa = 1.2 / px;
  float breathe = 0.84 + 0.16 * sin(uAmbient * 0.9 + seed * 6.283);
  float disc = 1.0 - smoothstep(1.0 - aa, 1.0 + aa, r);
  vec3 col = vec3(0.0);
  if (kind < 0.5) {
    float lit = uPhase > 0.5 ? 1.0 : 0.6;
    float ign = clamp(1.0 - (uTime - uIgnite) / 1.4, 0.0, 1.0) * step(uIgnite, uTime);
    col = WHITE * disc * 1.3 + mix(BLUE, WHITE, 0.4) * (exp(-r * r * 0.28) * 0.7 + exp(-r * 0.7) * 0.32) * breathe * lit;
    col += WHITE * ign * exp(-r * 0.3) * 1.5;
    col += mix(BLUE, WHITE, 0.3) * exp(-q.x * q.x * 0.08) * exp(-abs(q.y) * 3.0) * 0.5 * lit;
  } else if (kind < 1.5) {
    vec3 c = journey(0.35);
    if (state > 0.5) {
      col = mix(c, WHITE, 0.55) * disc * 1.2 + c * exp(-r * 0.85) * 0.75 * breathe;
    } else {
      float ring = 1.0 - smoothstep(0.17, 0.17 + aa, abs(r - 0.85));
      col = c * ring * 0.8 + c * exp(-r * 1.3) * 0.25;
    }
  } else if (kind < 3.5) {
    float big = kind > 2.5 ? 1.0 : 0.0;
    col = mix(ORANGE, WHITE, 0.6) * disc * 1.25 + ORANGE * (exp(-r * 0.8) * 0.7 + exp(-r * r * 0.15) * 0.25) * breathe;
    // Its reflection on the plain below.
    col += ORANGE * exp(-q.x * q.x * 2.5) * exp(-max(q.y - 1.0, 0.0) * 0.35) * step(1.0, q.y) * 0.32;
    // The revelation: a column of light rises from the newly lit destination, then settles.
    float rise = clamp(age / 0.5, 0.0, 1.0) * clamp(1.0 - (age - 0.6) / 1.4, 0.0, 1.0);
    col += ORANGE * big * exp(-q.x * q.x * 1.4) * step(q.y, 0.0) * exp(q.y * 0.08) * rise * 1.6;
    col += ORANGE * big * exp(-r * 0.35) * clamp(1.0 - age / 1.2, 0.0, 1.0) * 1.8;
    if (sel > 0.5) {
      float lock = 1.0 - smoothstep(0.07, 0.07 + aa, abs(r - 2.3));
      col += TEAL * lock * 1.3;
    }
  } else if (kind < 4.5) {
    float ang = atan(q.y, q.x);
    float dash = step(0.0, sin(ang * 8.0));
    float ring = 1.0 - smoothstep(0.13, 0.13 + aa, abs(r - 0.9));
    col = SHADOW * ring * dash * 0.95 + SHADOW * exp(-r * 1.5) * 0.12;
  } else {
    col = mix(WHITE, VIOLET, 0.3) * (disc * 0.75 + exp(-r * 1.4) * 0.25);
  }
  col += mix(WHITE, journey(0.35), 0.4) * flare * exp(-r * 0.55) * 1.2;
  return col;
}
`,
  pulse: /* glsl */ `
float pulse(float dist, float state) {
  float k = fract((uAmbient * 1.5 - dist) / 13.0);
  return exp(-k * 9.0) * 1.8;
}
`,
};

function stillBackdrop(vp: Viewport, cam: Camera): string {
  const hy = cam[2];
  const lines: string[] = [];
  // The plain's grid, drawn in the same perspective as the moving world.
  for (let z = Math.ceil(cam[1] + 0.6); z < cam[1] + 30; z++) {
    const p = project([0, 0, z], cam);
    if (p.y > vp.h) continue;
    const o = Math.max(0.04, 0.5 * Math.exp(-(z - cam[1]) * 0.1));
    lines.push(`<line x1="0" x2="${vp.w}" y1="${p.y.toFixed(1)}" y2="${p.y.toFixed(1)}" stroke="#20366b" stroke-opacity="${o.toFixed(2)}"/>`);
  }
  for (let x = Math.floor(cam[0] - 40); x <= cam[0] + 40; x++) {
    const near = project([x, 0, cam[1] + 0.6], cam);
    const far = project([x, 0, cam[1] + 40], cam);
    lines.push(
      `<line x1="${near.x.toFixed(1)}" y1="${near.y.toFixed(1)}" x2="${far.x.toFixed(1)}" y2="${far.y.toFixed(1)}" stroke="url(#h-fade)" stroke-opacity="0.5"/>`,
    );
  }
  const rand = seeded("stars");
  const stars = Array.from({ length: 70 }, () => {
    const x = rand() * vp.w;
    const y = rand() * (hy - 60);
    return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(0.6 + rand()).toFixed(2)}" fill="#edf5ff" opacity="${(0.25 + rand() * 0.5).toFixed(2)}"/>`;
  });
  return `
  <defs>
    <linearGradient id="h-sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#02040a"/>
      <stop offset="${(hy / vp.h - 0.06).toFixed(3)}" stop-color="#060b1c"/>
      <stop offset="${(hy / vp.h).toFixed(3)}" stop-color="#1a2350"/>
      <stop offset="${(hy / vp.h + 0.03).toFixed(3)}" stop-color="#081028"/>
      <stop offset="1" stop-color="#03050b"/>
    </linearGradient>
    <linearGradient id="h-fade" gradientUnits="userSpaceOnUse" x1="0" y1="${vp.h}" x2="0" y2="${hy}">
      <stop offset="0" stop-color="#2a4a8c"/>
      <stop offset="1" stop-color="#2a4a8c" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="${vp.w}" height="${vp.h}" fill="url(#h-sky)"/>
  ${stars.join("")}
  ${lines.join("")}`;
}

export const horizon: Direction = {
  id: "horizon",
  name: "Horizon",
  blurb: "A journey across a dark plain, towards lights on the horizon.",
  font: "unbounded",
  particles: 2200,
  geometry,
  view,
  project,
  glsl: GLSL,
  stillBackdrop,
};
