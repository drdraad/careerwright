// The moving world: one WebGL2 canvas behind everything, drawn with three.js. It holds nothing
// unique: every node and trail it draws is in the scene, and every word is in the DOM.
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
import type { Camera as ViewCamera, Direction, Viewport } from "./direction.ts";
import { KIND_CODE, STATE_CODE, type Scene, type Vec3 } from "./scene.ts";

const PRELUDE = /* glsl */ `
precision highp float;
uniform float uTime;
uniform float uAmbient;
uniform float uLive;
uniform float uPhase;
uniform float uIgnite;
uniform float uReveal;
uniform float uKey;
uniform float uTyped;
uniform vec2 uRes;
uniform float uDpr;
uniform vec4 uCamA;
uniform vec4 uCamB;
uniform vec3 uOrigin;

const vec3 BLUE = vec3(0.25, 0.55, 1.0);
const vec3 VIOLET = vec3(0.62, 0.42, 1.0);
const vec3 TEAL = vec3(0.27, 0.97, 0.83);
const vec3 ORANGE = vec3(1.0, 0.58, 0.2);
const vec3 SHADOW = vec3(0.34, 0.40, 0.54);
const vec3 WHITE = vec3(0.93, 0.96, 1.0);

vec3 journey(float h) { return mix(BLUE, VIOLET, smoothstep(0.0, 1.0, h)); }
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
vec4 toClip(vec2 px) { return vec4(px.x / uRes.x * 2.0 - 1.0, 1.0 - px.y / uRes.y * 2.0, 0.0, 1.0); }
`;

const BACKGROUND_VERT = /* glsl */ `
in vec3 position;
void main() { gl_Position = vec4(position.xy, 0.0, 1.0); }
`;

const backgroundFrag = (d: Direction) => /* glsl */ `
${d.glsl.project}
${d.glsl.background}
out vec4 fragColor;
void main() {
  vec2 px = vec2(gl_FragCoord.x, uRes.y * uDpr - gl_FragCoord.y) / uDpr;
  fragColor = vec4(background(px), 1.0);
}
`;

const trailVert = (d: Direction) => /* glsl */ `
${d.glsl.project}
${d.glsl.sway}
in vec3 position;
in vec3 aPrev;
in vec3 aNext;
in vec4 aA; // side, t along the trail, distance from the person, hue
in vec4 aB; // birth, duration, state, chosen
in vec2 aC; // core width, changed
out float vSide;
out float vT;
out float vDist;
out float vHue;
out float vHalf;
out float vCore;
flat out vec4 vB;
flat out float vChanged;
void main() {
  float s0; float s1; float s2;
  // Sway is atmosphere: the same gentle movement for every trail, zero at both ends so the
  // lights never move.
  float envelope = sin(3.14159 * aA.y);
  vec2 a = project(aPrev, s0);
  vec2 p = project(position, s1);
  vec2 b = project(aNext, s2);
  a += sway(a, envelope);
  p += sway(p, envelope);
  b += sway(b, envelope);
  vec2 tangent = b - a;
  float len = length(tangent);
  tangent = len > 1e-4 ? tangent / len : vec2(1.0, 0.0);
  vec2 normal = vec2(-tangent.y, tangent.x);
  float core = max(aC.x * s1, 0.7);
  float half_ = core * 0.5 + max(5.0, core * 2.6);
  gl_Position = s1 > 0.0 ? toClip(p + normal * aA.x * half_) : vec4(2.0, 2.0, 2.0, 1.0);
  vSide = aA.x;
  vT = aA.y;
  vDist = aA.z;
  vHue = aA.w;
  vHalf = half_;
  vCore = core;
  vB = aB;
  vChanged = aC.y;
}
`;

const trailFrag = (d: Direction) => /* glsl */ `
${d.glsl.pulse}
in float vSide;
in float vT;
in float vDist;
in float vHue;
in float vHalf;
in float vCore;
flat in vec4 vB;
flat in float vChanged;
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
  vec3 col = vB.w > 0.5 ? TEAL : journey(vHue);
  // Declared meanings: usual is dimmer than said; shadow is drawn, dashed and dim, never absent.
  float level = 0.42;
  if (state > 0.5 && state < 1.5) level = 1.0;
  if (state > 1.5 && state < 2.5) {
    col = SHADOW;
    level = 0.5;
    float dash = step(0.42, fract(vDist * DASH_FREQ));
    core *= dash;
    glow *= 0.25 + 0.35 * dash;
  }
  if (state > 3.5 && state < 4.5) level = 0.34;
  if (state > 4.5) level = 0.2;
  float head = grow < 1.0 ? exp(-(grow - vT) * 28.0) : 0.0;
  float flare = vChanged > 0.0 ? exp(-max(uTime - vChanged, 0.0) * 2.2) * step(vChanged, uTime) : 0.0;
  float beat = state < 1.5 || (state > 3.5 && state < 4.5) ? pulse(vDist, state) * uLive : 0.0;
  float light = level * (core + glow * 0.55) + (core * 0.8 + glow * 0.6) * (head * 1.4 + beat * 0.55 + flare * 0.8);
  fragColor = vec4(col * light, 1.0);
}
`;

const nodeVert = (d: Direction) => /* glsl */ `
${d.glsl.project}
in vec3 position;
in vec3 iP;
in vec4 iA; // kind, state, size, seed
in vec4 iB; // birth, changed, selected
out vec2 vQ;
out float vPx;
flat out vec4 vA;
flat out vec4 vB;
void main() {
  // The person and the revealed destination get larger quads for their glow and flare
  // (and Horizon's column of light).
  float EXTENT = iA.x < 0.5 || (iA.x > 2.5 && iA.x < 3.5) ? 18.0 : 7.0;
  float s;
  vec2 p = project(iP, s);
  float radius = max(iA.z * s, iA.x > 4.5 ? 1.6 : 2.6);
  vQ = position.xy * EXTENT;
  vPx = radius;
  vA = iA;
  vB = iB;
  gl_Position = s > 0.0 ? toClip(p + position.xy * EXTENT * radius) : vec4(2.0, 2.0, 2.0, 1.0);
}
`;

const nodeFrag = (d: Direction) => /* glsl */ `
${d.glsl.node}
in vec2 vQ;
in float vPx;
flat in vec4 vA;
flat in vec4 vB;
out vec4 fragColor;
void main() {
  float age = uTime - vB.x;
  if (age < 0.0) discard;
  float flare = vB.y > -1e5 ? exp(-max(uTime - vB.y, 0.0) * 2.4) * step(vB.y, uTime) : 0.0;
  vec3 col = nodeLook(vQ, vA.x, vA.y, age, flare, vB.z, vA.w, vPx);
  if (vA.x < 0.5) {
    float r = length(vQ);
    // The person's light carries a wide, slow-breathing aura: atmosphere, the same at every moment.
    col += mix(BLUE, WHITE, 0.3) * exp(-r * 0.3) * (0.22 + 0.06 * sin(uAmbient * 0.9)) ;
    // Each keystroke brightens it at once (input feedback within 100 ms).
    col += WHITE * exp(-max(uTime - uKey, 0.0) * 5.0) * exp(-r * 0.45) * 0.9;
  }
  fragColor = vec4(col * smoothstep(0.0, 0.35, age), 1.0);
}
`;

const particleVert = (d: Direction) => /* glsl */ `
${d.glsl.project}
${d.glsl.particle}
in vec3 position;
in vec4 aSeed;
out float vAlpha;
void main() {
  float alpha;
  vec4 p = particle(aSeed, alpha);
  vAlpha = alpha;
  gl_PointSize = p.z * uDpr;
  gl_Position = toClip(p.xy);
}
`;

const PARTICLE_FRAG = /* glsl */ `
in float vAlpha;
out vec4 fragColor;
void main() {
  float d = length(gl_PointCoord - 0.5) * 2.0;
  float a = (1.0 - smoothstep(0.15, 1.0, d)) * vAlpha;
  fragColor = vec4(mix(BLUE, WHITE, 0.55) * a, 1.0);
}
`;

type Uniforms = {
  uTime: { value: number };
  uAmbient: { value: number };
  uLive: { value: number };
  uPhase: { value: number };
  uIgnite: { value: number };
  uReveal: { value: number };
  uKey: { value: number };
  uTyped: { value: number };
  uRes: { value: [number, number] };
  uDpr: { value: number };
  uCamA: { value: [number, number, number, number] };
  uCamB: { value: [number, number, number, number] };
  uOrigin: { value: [number, number, number] };
};

export type FrameState = {
  time: number;
  ambient: number;
  live: number;
  phase: number;
  ignite: number;
  reveal: number;
  key: number;
  /** Characters typed into the question so far (0 once answered). */
  typed: number;
  camera: ViewCamera;
};

export function webgl2Available(): boolean {
  try {
    const probe = document.createElement("canvas");
    return probe.getContext("webgl2") !== null;
  } catch {
    return false;
  }
}

export class GLWorld {
  private readonly renderer: WebGLRenderer;
  private readonly scene = new ThreeScene();
  private readonly camera = new Camera();
  private readonly uniforms: Uniforms;
  private readonly trailMaterial: RawShaderMaterial;
  private readonly nodeMaterial: RawShaderMaterial;
  private trails: Mesh | null = null;
  private nodes: Mesh | null = null;
  /** GPU time per world frame, measured with timer queries (measurement mode only). */
  private timing: {
    gl: WebGL2RenderingContext;
    elapsed: number;
    disjoint: number;
    pending: WebGLQuery[];
    samples: number[];
  } | null = null;
  private readonly dashFrequency: number;
  private readonly canvas: HTMLCanvasElement;

  constructor(canvas: HTMLCanvasElement, direction: Direction) {
    this.canvas = canvas;
    this.renderer = new WebGLRenderer({
      canvas,
      antialias: false,
      alpha: false,
      powerPreference: "high-performance",
    });
    this.renderer.setClearColor(0x03050a, 1);
    this.uniforms = {
      uTime: { value: 0 },
      uAmbient: { value: 0 },
      uLive: { value: 1 },
      uPhase: { value: 0 },
      uIgnite: { value: -1e6 },
      uReveal: { value: -1e6 },
      uKey: { value: -1e6 },
      uTyped: { value: 0 },
      uRes: { value: [1, 1] },
      uDpr: { value: 1 },
      uCamA: { value: [0, 0, 1, 0] },
      uCamB: { value: [0, 0, 0, 0] },
      uOrigin: { value: [0, 0, 0] },
    };
    this.dashFrequency = direction.id === "horizon" ? 3.2 : 0.11;
    const material = (vert: string, frag: string, additive: boolean) =>
      new RawShaderMaterial({
        glslVersion: GLSL3,
        uniforms: this.uniforms,
        vertexShader: PRELUDE + vert,
        fragmentShader: `${PRELUDE}#define DASH_FREQ ${this.dashFrequency.toFixed(3)}\n${frag}`,
        blending: additive ? AdditiveBlending : NoBlending,
        transparent: additive,
        // Screen space runs y-down, so winding flips: draw both faces rather than cull half.
        side: DoubleSide,
        depthTest: false,
        depthWrite: false,
      });

    const backdrop = new BufferGeometry();
    backdrop.setAttribute("position", new BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
    const background = new Mesh(backdrop, material(BACKGROUND_VERT, backgroundFrag(direction), false));
    background.frustumCulled = false;
    background.renderOrder = 0;
    this.scene.add(background);

    this.trailMaterial = material(trailVert(direction), trailFrag(direction), true);
    this.nodeMaterial = material(nodeVert(direction), nodeFrag(direction), true);

    const count = direction.particles;
    const seeds = new Float32Array(count * 4);
    let h = 7;
    const rand = () => {
      h = (h * 16807) % 2147483647;
      return h / 2147483647;
    };
    for (let i = 0; i < seeds.length; i++) seeds[i] = rand();
    const dust = new BufferGeometry();
    dust.setAttribute("position", new BufferAttribute(new Float32Array(count * 3), 3));
    dust.setAttribute("aSeed", new BufferAttribute(seeds, 4));
    const particles = new Points(dust, material(particleVert(direction), PARTICLE_FRAG, true));
    particles.frustumCulled = false;
    particles.renderOrder = 2;
    this.scene.add(particles);
  }

  rendererName(): string {
    const gl = this.renderer.getContext();
    const info = gl.getExtension("WEBGL_debug_renderer_info");
    return info ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER));
  }

  resize(vp: Viewport): void {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.renderer.setPixelRatio(dpr);
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
    const c = new Float32Array(vertexCount * 2);
    const index = new Uint32Array(indexCount);
    let v = 0;
    let ix = 0;
    for (const t of scene.trails) {
      const n = t.points.length;
      // Progress along a trail is by distance, so growth and colour move at an even pace.
      const along = [0];
      for (let i = 1; i < n; i++) {
        const p = t.points[i] as Vec3;
        const q = t.points[i - 1] as Vec3;
        along.push((along[i - 1] as number) + Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]));
      }
      const total = (along[n - 1] as number) || 1;
      for (let i = 0; i < n; i++) {
        const p = t.points[i] as Vec3;
        const before = t.points[Math.max(0, i - 1)] as Vec3;
        const after = t.points[Math.min(n - 1, i + 1)] as Vec3;
        const travelled = t.reach + (along[i] as number);
        const u = (along[i] as number) / total;
        const width = t.width[0] + (t.width[1] - t.width[0]) * u;
        const hue = t.hue[0] + (t.hue[1] - t.hue[0]) * u;
        for (const side of [-1, 1]) {
          pos.set(p, v * 3);
          prev.set(before, v * 3);
          next.set(after, v * 3);
          a.set([side, u, travelled, hue], v * 4);
          b.set([t.birth, t.duration, STATE_CODE[t.state], t.chosen ? 1 : 0], v * 4);
          c.set([width, t.changed], v * 2);
          v++;
        }
        if (i < n - 1) {
          const base = v - 2;
          index.set([base, base + 1, base + 2, base + 1, base + 3, base + 2], ix);
          ix += 6;
        }
      }
    }
    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new BufferAttribute(pos, 3));
    geometry.setAttribute("aPrev", new BufferAttribute(prev, 3));
    geometry.setAttribute("aNext", new BufferAttribute(next, 3));
    geometry.setAttribute("aA", new BufferAttribute(a, 4));
    geometry.setAttribute("aB", new BufferAttribute(b, 4));
    geometry.setAttribute("aC", new BufferAttribute(c, 2));
    geometry.setIndex(new BufferAttribute(index, 1));
    const mesh = new Mesh(geometry, this.trailMaterial);
    mesh.frustumCulled = false;
    mesh.renderOrder = 1;
    return mesh;
  }

  private buildNodes(scene: Scene): Mesh {
    const count = scene.nodes.length;
    const geometry = new InstancedBufferGeometry();
    geometry.setAttribute("position", new BufferAttribute(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), 3));
    geometry.setIndex([0, 1, 2, 0, 2, 3]);
    const p = new Float32Array(count * 3);
    const a = new Float32Array(count * 4);
    const b = new Float32Array(count * 4);
    scene.nodes.forEach((node, i) => {
      p.set(node.p, i * 3);
      a.set([KIND_CODE[node.kind], STATE_CODE[node.state], node.size, (i * 0.618) % 1], i * 4);
      b.set([node.birth, node.changed, node.selected ? 1 : 0, 0], i * 4);
    });
    geometry.setAttribute("iP", new InstancedBufferAttribute(p, 3));
    geometry.setAttribute("iA", new InstancedBufferAttribute(a, 4));
    geometry.setAttribute("iB", new InstancedBufferAttribute(b, 4));
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
    u.uPhase.value = frame.phase;
    u.uIgnite.value = frame.ignite;
    u.uReveal.value = frame.reveal;
    u.uKey.value = frame.key;
    u.uTyped.value = frame.typed;
    u.uCamA.value = [frame.camera[0], frame.camera[1], frame.camera[2], frame.camera[3]];
    u.uCamB.value = [frame.camera[4], frame.camera[5], frame.camera[6], frame.camera[7]];
    const timing = this.timing;
    const query = timing?.gl.createQuery() ?? null;
    if (timing && query) timing.gl.beginQuery(timing.elapsed, query);
    this.renderer.render(this.scene, this.camera);
    if (timing && query) {
      timing.gl.endQuery(timing.elapsed);
      timing.pending.push(query);
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
    this.timing = { gl, elapsed: ext.TIME_ELAPSED_EXT, disjoint: ext.GPU_DISJOINT_EXT, pending: [], samples: [] };
    return true;
  }

  /** GPU milliseconds per frame since the last call. */
  takeGpuSamples(): number[] {
    const samples = this.timing?.samples ?? [];
    if (this.timing) this.timing.samples = [];
    return samples;
  }

  private collectTimings(): void {
    const t = this.timing;
    if (!t) return;
    while (t.pending.length > 0) {
      const query = t.pending[0] as WebGLQuery;
      if (!t.gl.getQueryParameter(query, t.gl.QUERY_RESULT_AVAILABLE)) break;
      const disjoint = t.gl.getParameter(t.disjoint) as boolean;
      if (!disjoint) t.samples.push((t.gl.getQueryParameter(query, t.gl.QUERY_RESULT) as number) / 1e6);
      t.gl.deleteQuery(query);
      t.pending.shift();
    }
  }

  dispose(): void {
    this.renderer.dispose();
  }
}
