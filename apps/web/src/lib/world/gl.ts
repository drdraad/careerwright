// The moving world: one WebGL2 canvas behind everything, drawn with three.js and raw GLSL 3
// shaders (ADR 0014 decision 2). It holds nothing unique: every light and trail it draws is in
// the scene, and every word is in the DOM. Horizon, made livelier (session W1): the same calm,
// lined-up layout as the spike's Horizon, with quiet solid trails and more life in the light.
//
// Atmosphere (the breathing horizon, the aurora, stars, mist, a few hundred motes and the light
// flowing along known trails) looks the same for every item and carries no meaning. Meaning is
// carried only by the scene's states: lit or waiting, usual or said, shadow (not known yet).
// Never overwhelming (the product owner, on the busiest scene): no shimmer travels the horizon
// and no trail sways; each trail's core is drawn at least at its measured strength (palette.ts),
// and its glow and the light flowing along it only add.
import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  Camera,
  DoubleSide,
  GLSL3,
  InstancedBufferAttribute,
  InstancedBufferGeometry,
  Mesh,
  NoBlending,
  Points,
  RawShaderMaterial,
  Scene as ThreeScene,
  WebGLRenderer,
} from "three";
import { type View, type Viewport, writeViewUniforms } from "./geometry";
import { MOTION } from "./motion";
import { PALETTE, rgb, TRAIL_OPACITY } from "./palette";
import { KIND_CODE, type Scene, STATE_CODE, type Vec3 } from "./scene";

/** Drifting motes: atmosphere, a few hundred. */
const PARTICLES = 360;

/** A token's colour as a GLSL vec3, so the shaders hold the palette's own values. */
const vec3 = (hex: string): string =>
  `vec3(${rgb(hex)
    .map((c) => (c / 255).toFixed(3))
    .join(", ")})`;
const float = (n: number): string => n.toFixed(3);

const PRELUDE = /* glsl */ `
precision highp float;
uniform float uTime;
uniform float uAmbient;
uniform float uLive;
uniform float uLit;
uniform float uIgnite;
uniform vec2 uRes;
uniform float uDpr;
uniform vec4 uCamA;
uniform vec4 uCamB;
uniform vec3 uOrigin;

// One colour, one meaning (docs/design/tokens/tokens.css): blue to violet is the journey,
// orange a destination, slate not known yet; written from the palette (palette.ts).
const vec3 BLUE = ${vec3(PALETTE.near)};
const vec3 VIOLET = ${vec3(PALETTE.far)};
const vec3 ORANGE = ${vec3(PALETTE.destination)};
const vec3 SHADOW = ${vec3(PALETTE.shadow)};
const vec3 WHITE = ${vec3(PALETTE.person)};
const float BREATHE = ${MOTION.breathe.toFixed(1)};
// Each declared state's measured strength (contrast-pairs.json).
const float USUAL = ${float(TRAIL_OPACITY.usual)};
const float SAID = ${float(TRAIL_OPACITY.said)};
const float SHADOWED = ${float(TRAIL_OPACITY.shadow)};
const float OPENING = ${float(TRAIL_OPACITY.opening)};

vec3 journey(float h) { return mix(BLUE, VIOLET, smoothstep(0.0, 1.0, h)); }
float breath(float phase) { return 0.5 + 0.5 * sin(uAmbient * 6.2832 / BREATHE + phase); }
float hash12(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
             mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y);
}
vec2 project(vec3 p, out float scale) {
  float d = p.z - uCamA.y;
  if (d < 0.05) { scale = 0.0; return vec2(-1e5); }
  scale = uCamA.w / d;
  return vec2(uCamB.x + (p.x - uCamA.x) * scale, uCamA.z + (uCamB.y - p.y) * scale);
}
vec4 toClip(vec2 px) { return vec4(px.x / uRes.x * 2.0 - 1.0, 1.0 - px.y / uRes.y * 2.0, 0.0, 1.0); }
`;

const BACKGROUND_VERT = /* glsl */ `
in vec3 position;
void main() { gl_Position = vec4(position.xy, 0.0, 1.0); }
`;

const BACKGROUND_FRAG = /* glsl */ `
out vec4 fragColor;
void main() {
  vec2 px = vec2(gl_FragCoord.x, uRes.y * uDpr - gl_FragCoord.y) / uDpr;
  float hy = uCamA.z;
  float f = uCamA.w;
  float above = hy - px.y;
  float b = breath(0.0);
  // Sky: near-black, deepening upward.
  vec3 col = mix(vec3(0.012, 0.018, 0.040), vec3(0.004, 0.006, 0.014), clamp(above / (uRes.y * 0.5), 0.0, 1.0));
  // The horizon's glow breathes slowly.
  col += vec3(0.07, 0.11, 0.26) * exp(-abs(above) / 80.0) * (0.52 + 0.14 * b);
  col += vec3(0.24, 0.18, 0.46) * exp(-abs(above) / 12.0) * (0.24 + 0.08 * b);
  if (above > 0.0) {
    // Aurora: soft curtains of blue and violet drifting above the horizon, with fine rays.
    float a = vnoise(vec2(px.x * 0.0032 + uAmbient * 0.012, uAmbient * 0.006));
    float c = vnoise(vec2(px.x * 0.009 - uAmbient * 0.018, 7.0 + above * 0.004));
    float rays = 0.75 + 0.25 * vnoise(vec2(px.x * 0.05 + uAmbient * 0.04, 3.0));
    float curtain = smoothstep(0.38, 1.0, a) * (0.55 + 0.45 * c) * rays;
    float band = exp(-pow((above - uRes.y * 0.14) / (uRes.y * 0.13), 2.0));
    col += mix(BLUE, VIOLET, c) * curtain * band * 0.13;
    // Stars, twinkling slowly.
    vec2 cell = floor(px / 46.0);
    float h = hash12(cell);
    if (h > 0.84) {
      vec2 sp = (cell + vec2(hash12(cell + 3.1), hash12(cell + 7.7))) * 46.0;
      float d = length(px - sp);
      float tw = 0.55 + 0.45 * sin(uAmbient * (0.35 + h * 0.5) + h * 50.0);
      col += WHITE * exp(-d * d * 0.8) * tw * (h - 0.82) * 3.0 * smoothstep(20.0, 120.0, above);
    }
  } else {
    // The plain: smooth dark ground, a sheen near the horizon and mist drifting towards you.
    float depth = f * uCamB.y / max(px.y - hy, 0.25);
    vec2 g = vec2(uCamA.x + (px.x - uCamB.x) * depth / f, uCamA.y + depth);
    float mist = vnoise(g * vec2(0.25, 0.12) + vec2(0.0, uAmbient * 0.05));
    float mist2 = vnoise(g * vec2(0.6, 0.3) - vec2(uAmbient * 0.03, uAmbient * 0.09));
    col = mix(vec3(0.010, 0.014, 0.030), vec3(0.020, 0.030, 0.065), exp(above / 140.0));
    col += vec3(0.05, 0.08, 0.18) * (pow(mist, 2.0) * 0.35 + pow(mist2, 3.0) * 0.18) * exp(-depth * 0.035);
    col += vec3(0.05, 0.08, 0.18) * exp(above / 26.0) * (0.75 + 0.1 * b);
    // The person's light pools on the plain around them; brighter once lit.
    float od = length(g - uOrigin.xz);
    col += vec3(0.10, 0.18, 0.40) * exp(-od * od * 1.1) * mix(0.32, 0.85 + 0.12 * breath(1.3), uLit);
    // Ignition: a ring of light runs out across the plain.
    float ia = uTime - uIgnite;
    if (ia > 0.0 && ia < 2.6) {
      float ring = exp(-pow((od - ia * 5.0) / (0.06 + ia * 0.22), 2.0));
      col += mix(BLUE, WHITE, 0.35) * ring * (1.0 - ia / 2.6) * 0.9 * exp(-depth * 0.05);
    }
  }
  vec2 v = px / uRes - 0.5;
  col *= 1.0 - 0.45 * dot(v, v) * 1.5;
  fragColor = vec4(col, 1.0);
}
`;

const TRAIL_VERT = /* glsl */ `
in vec3 position;
in vec3 aPrev;
in vec3 aNext;
in vec4 aA; // side, t along the trail, distance from the person, hue
in vec4 aB; // birth, duration, state, seed
in float aWidth;
out float vSide;
out float vT;
out float vDist;
out float vHue;
out float vHalf;
out float vCore;
flat out vec4 vB;
void main() {
  float s0; float s1; float s2;
  vec2 a = project(aPrev, s0);
  vec2 p = project(position, s1);
  vec2 b = project(aNext, s2);
  vec2 tangent = b - a;
  float len = length(tangent);
  tangent = len > 1e-4 ? tangent / len : vec2(1.0, 0.0);
  vec2 normal = vec2(-tangent.y, tangent.x);
  // A trail is still: it never sways, so a known path never looks unsettled.
  float core = max(aWidth * s1, 0.7);
  float half_ = core * 0.5 + max(5.0, core * 2.6);
  gl_Position = s1 > 0.0 ? toClip(p + normal * aA.x * half_) : vec4(2.0, 2.0, 2.0, 1.0);
  vSide = aA.x;
  vT = aA.y;
  vDist = aA.z;
  vHue = aA.w;
  vHalf = half_;
  vCore = core;
  vB = aB;
}
`;

const TRAIL_FRAG = /* glsl */ `
in float vSide;
in float vT;
in float vDist;
in float vHue;
in float vHalf;
in float vCore;
flat in vec4 vB;
out vec4 fragColor;
void main() {
  float grow = clamp((uTime - vB.x) / vB.y, 0.0, 1.0);
  if (vT > grow) discard;
  float state = vB.z;
  float x = abs(vSide) * vHalf;
  float r = vCore * 0.5;
  float core = 1.0 - smoothstep(r - 0.6, r + 0.6, x);
  float sigma = max(2.2, vCore * 1.3);
  float glow = exp(-x * x / (2.0 * sigma * sigma));
  vec3 col = journey(vHue);
  // Declared meanings, each core at its measured strength: usual is fainter than said, with
  // less glow; shadow is a quiet solid slate, never absent.
  float level = USUAL;
  float halo = 0.5;
  bool known = state < 1.5;
  if (state > 0.5 && state < 1.5) {
    level = SAID;
    halo = 1.0;
  }
  if (state > 1.5 && state < 2.5) {
    col = SHADOW;
    level = SHADOWED;
    halo = 0.25;
  }
  if (state > 3.5) {
    level = OPENING;
    halo = 0.4;
  }
  // Atmosphere, the same for every trail: a slow breath along its glow.
  float flow = 0.86 + 0.14 * sin(vDist * 2.1 - uAmbient * 1.4 + vB.w * 6.2832);
  // Light flows outward along what is known (usual or said), never along what is not.
  float pulse = 0.0;
  if (known || state > 3.5) {
    float k = fract((uAmbient * 1.6 - vDist) / 9.0);
    pulse = exp(-k * 10.0) * 1.7 * uLive;
  }
  float head = grow < 1.0 ? exp(-(grow - vT) * 28.0) : 0.0;
  // The core is added at its level over the ground, at least as bright as drawing it at that
  // opacity; glow, flow, growth and the pulse only add to it.
  float light = level * core + glow * 0.55 * halo * flow + (core * 0.8 + glow * 0.6) * (head * 1.4 + pulse * 0.55);
  fragColor = vec4(col * light, 1.0);
}
`;

const NODE_VERT = /* glsl */ `
in vec3 position;
in vec3 iP;
in vec4 iA; // kind, state, size, seed
in float iBirth;
out vec2 vQ;
out float vPx;
flat out vec4 vA;
flat out float vBirth;
void main() {
  // The person and destinations get larger quads for their glow and reflections.
  float EXTENT = iA.x < 0.5 ? 18.0 : (iA.x > 1.5 && iA.x < 2.5 ? 9.0 : 6.0);
  float s;
  vec2 p = project(iP, s);
  float radius = max(iA.z * s, iA.x > 4.5 ? 1.6 : 2.6);
  vQ = position.xy * EXTENT;
  vPx = radius;
  vA = iA;
  vBirth = iBirth;
  gl_Position = s > 0.0 ? toClip(p + position.xy * EXTENT * radius) : vec4(2.0, 2.0, 2.0, 1.0);
}
`;

const NODE_FRAG = /* glsl */ `
in vec2 vQ;
in float vPx;
flat in vec4 vA;
flat in float vBirth;
out vec4 fragColor;
void main() {
  float age = uTime - vBirth;
  if (age < 0.0) discard;
  float kind = vA.x;
  float state = vA.y;
  float seed = vA.w;
  vec2 q = vQ;
  float r = length(q);
  float aa = 1.2 / vPx;
  float disc = 1.0 - smoothstep(1.0 - aa, 1.0 + aa, r);
  float br = breath(seed * 6.2832);
  vec3 col = vec3(0.0);
  if (kind < 0.5) {
    // The person. Waiting: a small light breathing slowly. Lit: bright, with a wide aura.
    float lit = uLit;
    float ign = clamp(1.0 - (uTime - uIgnite) / 1.4, 0.0, 1.0) * step(uIgnite, uTime);
    // Waiting, the core is half the size and the aura a slow, faint breath.
    float rr = r * mix(2.0, 1.0, lit);
    float core = 1.0 - smoothstep(1.0 - aa, 1.0 + aa, rr);
    col = WHITE * core * mix(0.8, 1.35, lit);
    col += mix(BLUE, WHITE, 0.4) * (exp(-rr * rr * 0.28) * 0.7 + exp(-rr * 0.7) * 0.32) * mix(0.35, 1.0, lit) * (0.7 + 0.3 * br);
    col += mix(BLUE, WHITE, 0.3) * exp(-r * 0.3) * mix(0.06, 0.24, lit) * (0.6 + 0.4 * br);
    col += WHITE * ign * exp(-r * 0.3) * 1.6;
    // Its reflection on the plain.
    col += mix(BLUE, WHITE, 0.3) * exp(-q.x * q.x * 1.2) * exp(-max(q.y - 1.0, 0.0) * 0.3) * step(1.0, q.y) * 0.35 * mix(0.5, 1.0, lit);
  } else if (kind < 1.5) {
    // A skill: a faint ring while usual in the role, a filled light once the person said so.
    vec3 c = journey(0.3);
    if (state > 0.5) {
      col = mix(c, WHITE, 0.55) * disc * 1.2 + c * exp(-r * 0.85) * 0.75 * (0.85 + 0.15 * br);
    } else {
      float ring = 1.0 - smoothstep(0.17, 0.17 + aa, abs(r - 0.85));
      col = c * ring * 0.85 + c * exp(-r * 1.3) * 0.25;
    }
  } else if (kind < 2.5) {
    // A destination: a warm light on the horizon, breathing, with its reflection on the plain.
    float core = 1.0 - smoothstep(0.55 - aa, 0.55 + aa, r);
    col = mix(ORANGE, vec3(1.0, 0.85, 0.6), 0.45) * core * 0.95 + ORANGE * disc * 0.45
        + ORANGE * (exp(-r * 0.8) * 0.65 + exp(-r * r * 0.15) * 0.25) * (0.8 + 0.2 * br);
    float shimmer = 0.75 + 0.25 * sin(q.y * 1.7 - uAmbient * 2.2 + seed * 9.0);
    col += ORANGE * exp(-q.x * q.x * 2.5) * exp(-max(q.y - 1.0, 0.0) * 0.32) * step(1.0, q.y) * 0.34 * shimmer;
  } else {
    // An opening near a destination.
    col = mix(WHITE, VIOLET, 0.3) * (disc * 0.75 + exp(-r * 1.4) * 0.25);
  }
  fragColor = vec4(col * smoothstep(0.0, 0.35, age), 1.0);
}
`;

const PARTICLE_VERT = /* glsl */ `
in vec3 position;
in vec4 aSeed;
out float vAlpha;
out float vWarm;
void main() {
  // Motes drift across the plain towards you and rise a little: travel, as atmosphere.
  float span = 26.0;
  float rel = 0.35 + mod(aSeed.z * span - uAmbient * 0.34, span);
  float z = uCamA.y + rel;
  float x = uCamA.x + (aSeed.x - 0.5) * (rel * 1.9 + 2.0) + sin(uAmbient * 0.3 + aSeed.w * 20.0) * 0.12;
  float y = aSeed.y * (0.15 + rel * 0.09) + 0.04 * sin(uAmbient * 0.5 + aSeed.x * 30.0);
  float s;
  vec2 p = project(vec3(x, y, z), s);
  float twinkle = 0.7 + 0.3 * sin(uAmbient * (1.0 + aSeed.w) + aSeed.z * 40.0);
  vAlpha = (0.25 + 0.45 * aSeed.w) * smoothstep(0.35, 2.2, rel) * smoothstep(span, span * 0.55, rel) * twinkle;
  vAlpha *= mix(0.5, 1.0, uLit);
  vWarm = step(0.93, aSeed.w);
  gl_PointSize = clamp(0.022 * s, 0.8, 3.2) * uDpr;
  gl_Position = toClip(p);
}
`;

const PARTICLE_FRAG = /* glsl */ `
in float vAlpha;
in float vWarm;
out vec4 fragColor;
void main() {
  float d = length(gl_PointCoord - 0.5) * 2.0;
  float a = (1.0 - smoothstep(0.15, 1.0, d)) * vAlpha;
  fragColor = vec4(mix(mix(BLUE, WHITE, 0.55), mix(VIOLET, WHITE, 0.5), vWarm) * a, 1.0);
}
`;

type Uniforms = {
  uTime: { value: number };
  uAmbient: { value: number };
  uLive: { value: number };
  uLit: { value: number };
  uIgnite: { value: number };
  uRes: { value: [number, number] };
  uDpr: { value: number };
  uCamA: { value: [number, number, number, number] };
  uCamB: { value: [number, number, number, number] };
  uOrigin: { value: [number, number, number] };
};

export type FrameState = {
  /** The frame's number, so its GPU time can be paired with its main-thread time. */
  index: number;
  /** Seconds on the page's clock. */
  time: number;
  /** The ambient clock: it advances only while ambient motion runs. */
  ambient: number;
  /** How much ambient motion there is, 0 (still) to 1. */
  live: number;
  lit: boolean;
  /** When the person's light was lit in this visit. */
  ignite: number;
  view: View;
};

/** Whether this browser offers WebGL2; the probe's context is released at once. */
export function webgl2Available(): boolean {
  try {
    const probe = document.createElement("canvas").getContext("webgl2");
    if (probe === null) return false;
    probe.getExtension("WEBGL_lose_context")?.loseContext();
    return true;
  } catch {
    return false;
  }
}

/** One frame's WebGL GPU time (the world's passes only, not the page's compositing). */
export type GpuSample = { frame: number; ms: number };

type Timing = {
  gl: WebGL2RenderingContext;
  elapsed: number;
  disjoint: number;
  pending: { query: WebGLQuery; frame: number }[];
  samples: GpuSample[];
};

export class GLWorld {
  private readonly renderer: WebGLRenderer;
  private readonly scene = new ThreeScene();
  private readonly camera = new Camera();
  private readonly uniforms: Uniforms;
  private readonly trailMaterial: RawShaderMaterial;
  private readonly nodeMaterial: RawShaderMaterial;
  private trails: Mesh | null = null;
  private nodes: Mesh | null = null;
  private timing: Timing | null = null;
  /** The backdrop's and the motes' geometry and materials, released with the world. */
  private readonly fixed: { dispose(): void }[] = [];

  constructor(private readonly canvas: HTMLCanvasElement) {
    this.renderer = new WebGLRenderer({
      canvas,
      antialias: false,
      alpha: false,
      powerPreference: "high-performance",
    });
    this.renderer.setClearColor(0x03050b, 1);
    this.uniforms = {
      uTime: { value: 0 },
      uAmbient: { value: 0 },
      uLive: { value: 1 },
      uLit: { value: 0 },
      uIgnite: { value: -1e6 },
      uRes: { value: [1, 1] },
      uDpr: { value: 1 },
      uCamA: { value: [0, 0, 1, 1] },
      uCamB: { value: [0, 0, 0, 0] },
      uOrigin: { value: [0, 0, 0] },
    };
    const material = (vert: string, frag: string, additive: boolean) =>
      new RawShaderMaterial({
        glslVersion: GLSL3,
        uniforms: this.uniforms,
        vertexShader: PRELUDE + vert,
        fragmentShader: PRELUDE + frag,
        blending: additive ? AdditiveBlending : NoBlending,
        transparent: additive,
        // Screen space runs y-down, so winding flips: draw both faces rather than cull half.
        side: DoubleSide,
        depthTest: false,
        depthWrite: false,
      });

    const backdrop = new BufferGeometry();
    backdrop.setAttribute(
      "position",
      new BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3),
    );
    const backdropMaterial = material(BACKGROUND_VERT, BACKGROUND_FRAG, false);
    const background = new Mesh(backdrop, backdropMaterial);
    background.frustumCulled = false;
    background.renderOrder = 0;
    this.scene.add(background);

    this.trailMaterial = material(TRAIL_VERT, TRAIL_FRAG, true);
    this.nodeMaterial = material(NODE_VERT, NODE_FRAG, true);

    const seeds = new Float32Array(PARTICLES * 4);
    let h = 7;
    for (let i = 0; i < seeds.length; i++) {
      h = (h * 16807) % 2147483647;
      seeds[i] = h / 2147483647;
    }
    const dust = new BufferGeometry();
    dust.setAttribute("position", new BufferAttribute(new Float32Array(PARTICLES * 3), 3));
    dust.setAttribute("aSeed", new BufferAttribute(seeds, 4));
    const dustMaterial = material(PARTICLE_VERT, PARTICLE_FRAG, true);
    const particles = new Points(dust, dustMaterial);
    particles.frustumCulled = false;
    particles.renderOrder = 2;
    this.scene.add(particles);
    this.fixed.push(backdrop, backdropMaterial, dust, dustMaterial);
  }

  /** The WebGL renderer string, for measurement reports. */
  rendererName(): string {
    const gl = this.renderer.getContext();
    const info = gl.getExtension("WEBGL_debug_renderer_info");
    return info
      ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL))
      : String(gl.getParameter(gl.RENDERER));
  }

  canvasSize(): [number, number] {
    return [this.canvas.width, this.canvas.height];
  }

  resize(vp: Viewport): void {
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(vp.w, vp.h, false);
    this.uniforms.uRes.value = [vp.w, vp.h];
    this.uniforms.uDpr.value = this.canvas.width / vp.w;
  }

  setScene(scene: Scene): void {
    const origin = scene.nodes.find((n) => n.kind === "origin");
    if (origin) this.uniforms.uOrigin.value = [...origin.p];
    this.replace("trails", this.buildTrails(scene));
    this.replace("nodes", this.buildNodes(scene));
  }

  private replace(which: "trails" | "nodes", mesh: Mesh): void {
    const old = this[which];
    if (old) {
      this.scene.remove(old);
      old.geometry.dispose();
    }
    this.scene.add(mesh);
    this[which] = mesh;
  }

  private buildTrails(scene: Scene): Mesh {
    let vertexCount = 0;
    let indexCount = 0;
    for (const t of scene.trails) {
      vertexCount += t.points.length * 2;
      indexCount += (t.points.length - 1) * 6;
    }
    const pos = new Float32Array(vertexCount * 3);
    const prev = new Float32Array(vertexCount * 3);
    const next = new Float32Array(vertexCount * 3);
    const a = new Float32Array(vertexCount * 4);
    const b = new Float32Array(vertexCount * 4);
    const width = new Float32Array(vertexCount);
    const index = new Uint32Array(indexCount);
    let v = 0;
    let ix = 0;
    scene.trails.forEach((t, n) => {
      const count = t.points.length;
      // Progress along a trail is by distance, so growth and colour move at an even pace.
      const along = [0];
      for (let i = 1; i < count; i++) {
        const p = t.points[i] as Vec3;
        const q = t.points[i - 1] as Vec3;
        along.push((along[i - 1] as number) + Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]));
      }
      const total = (along[count - 1] as number) || 1;
      const seed = (n * 0.618) % 1;
      for (let i = 0; i < count; i++) {
        const p = t.points[i] as Vec3;
        const before = t.points[Math.max(0, i - 1)] as Vec3;
        const after = t.points[Math.min(count - 1, i + 1)] as Vec3;
        const u = (along[i] as number) / total;
        for (const side of [-1, 1]) {
          pos.set(p, v * 3);
          prev.set(before, v * 3);
          next.set(after, v * 3);
          a.set(
            [side, u, t.reach + (along[i] as number), t.hue[0] + (t.hue[1] - t.hue[0]) * u],
            v * 4,
          );
          b.set([t.birth, t.duration, STATE_CODE[t.state], seed], v * 4);
          width[v] = t.width[0] + (t.width[1] - t.width[0]) * u;
          v++;
        }
        if (i < count - 1) {
          const base = v - 2;
          index.set([base, base + 1, base + 2, base + 1, base + 3, base + 2], ix);
          ix += 6;
        }
      }
    });
    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new BufferAttribute(pos, 3));
    geometry.setAttribute("aPrev", new BufferAttribute(prev, 3));
    geometry.setAttribute("aNext", new BufferAttribute(next, 3));
    geometry.setAttribute("aA", new BufferAttribute(a, 4));
    geometry.setAttribute("aB", new BufferAttribute(b, 4));
    geometry.setAttribute("aWidth", new BufferAttribute(width, 1));
    geometry.setIndex(new BufferAttribute(index, 1));
    const mesh = new Mesh(geometry, this.trailMaterial);
    mesh.frustumCulled = false;
    mesh.renderOrder = 1;
    return mesh;
  }

  private buildNodes(scene: Scene): Mesh {
    const count = scene.nodes.length;
    const geometry = new InstancedBufferGeometry();
    geometry.setAttribute(
      "position",
      new BufferAttribute(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), 3),
    );
    geometry.setIndex([0, 1, 2, 0, 2, 3]);
    const p = new Float32Array(count * 3);
    const a = new Float32Array(count * 4);
    const birth = new Float32Array(count);
    scene.nodes.forEach((node, i) => {
      p.set(node.p, i * 3);
      a.set([KIND_CODE[node.kind], STATE_CODE[node.state], node.size, (i * 0.618) % 1], i * 4);
      birth[i] = node.birth;
    });
    geometry.setAttribute("iP", new InstancedBufferAttribute(p, 3));
    geometry.setAttribute("iA", new InstancedBufferAttribute(a, 4));
    geometry.setAttribute("iBirth", new InstancedBufferAttribute(birth, 1));
    geometry.instanceCount = count;
    const mesh = new Mesh(geometry, this.nodeMaterial);
    mesh.frustumCulled = false;
    mesh.renderOrder = 3;
    return mesh;
  }

  render(frame: FrameState): void {
    const u = this.uniforms;
    u.uTime.value = frame.time;
    u.uAmbient.value = frame.ambient;
    u.uLive.value = frame.live;
    u.uLit.value = frame.lit ? 1 : 0;
    u.uIgnite.value = frame.ignite;
    writeViewUniforms(frame.view, u.uCamA.value, u.uCamB.value);
    const timing = this.timing;
    const query = timing?.gl.createQuery() ?? null;
    if (timing && query) timing.gl.beginQuery(timing.elapsed, query);
    this.renderer.render(this.scene, this.camera);
    if (timing && query) {
      timing.gl.endQuery(timing.elapsed);
      timing.pending.push({ query, frame: frame.index });
      this.collectTimings();
    }
  }

  /** Starts GPU timing; false when the browser offers no timer queries. */
  measureGpu(): boolean {
    const gl = this.renderer.getContext() as WebGL2RenderingContext;
    const ext = gl.getExtension("EXT_disjoint_timer_query_webgl2") as {
      TIME_ELAPSED_EXT: number;
      GPU_DISJOINT_EXT: number;
    } | null;
    if (!ext) return false;
    this.timing = {
      gl,
      elapsed: ext.TIME_ELAPSED_EXT,
      disjoint: ext.GPU_DISJOINT_EXT,
      pending: [],
      samples: [],
    };
    return true;
  }

  /** Each frame's WebGL GPU milliseconds since the last call, by frame number. */
  takeGpuSamples(): GpuSample[] {
    const samples = this.timing?.samples ?? [];
    if (this.timing) this.timing.samples = [];
    return samples;
  }

  private collectTimings(): void {
    const t = this.timing;
    if (!t) return;
    while (t.pending.length > 0) {
      const { query, frame } = t.pending[0] as { query: WebGLQuery; frame: number };
      if (!t.gl.getQueryParameter(query, t.gl.QUERY_RESULT_AVAILABLE)) break;
      const disjoint = t.gl.getParameter(t.disjoint) as boolean;
      if (!disjoint) {
        const ns = t.gl.getQueryParameter(query, t.gl.QUERY_RESULT) as number;
        t.samples.push({ frame, ms: ns / 1e6 });
      }
      t.gl.deleteQuery(query);
      t.pending.shift();
    }
  }

  dispose(): void {
    for (const mesh of [this.trails, this.nodes]) mesh?.geometry.dispose();
    for (const item of this.fixed) item.dispose();
    this.trailMaterial.dispose();
    this.nodeMaterial.dispose();
    this.renderer.dispose();
    // Release the context itself (browsers hold only a few, and calm mode can come and go),
    // unless the browser has already taken it.
    if (!this.renderer.getContext().isContextLost()) this.renderer.forceContextLoss();
  }
}
