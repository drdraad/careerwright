// The library comparison's workload: the busiest scene in miniature, identical for every library.
// Same shaders, same geometry, same draw order: a backdrop, 140 glowing trails, 130 lights
// (instanced) and 2,400 drifting particles, all additive. Only the library around them changes.
// The shaders carry no #version line: three.js and PixiJS add it; the OGL adapter prepends it.

export const COUNTS = { trails: 140, points: 48, lights: 130, particles: 2400 } as const;

const HEADER = /* glsl */ `
precision highp float;
uniform float uTime;
uniform vec2 uRes;
uniform float uDpr;
vec4 toClip(vec2 px) { return vec4(px.x / uRes.x * 2.0 - 1.0, 1.0 - px.y / uRes.y * 2.0, 0.0, 1.0); }
float hash12(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
float vnoise(vec2 p) {
  vec2 i = floor(p); vec2 f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x), mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y);
}
`;

export const SHADERS = {
  background: {
    vertex: `${HEADER}in vec3 position; void main() { gl_Position = vec4(position.xy, 0.0, 1.0); }`,
    fragment: `${HEADER}out vec4 fragColor;
void main() {
  vec2 px = vec2(gl_FragCoord.x, uRes.y * uDpr - gl_FragCoord.y) / uDpr;
  vec2 uv = px / uRes.y;
  float n = vnoise(uv * 2.4 + uTime * 0.004) * 0.65 + vnoise(uv * 6.0 - uTime * 0.006) * 0.35;
  vec3 col = vec3(0.01, 0.013, 0.028) + vec3(0.3, 0.4, 1.0) * pow(n, 3.0) * 0.07;
  vec2 v = px / uRes - 0.5;
  fragColor = vec4(col * (1.0 - 0.8 * dot(v, v)), 1.0);
}`,
  },
  trail: {
    vertex: `${HEADER}in vec3 position; in vec4 aData; out vec4 vData;
void main() { vData = aData; gl_Position = toClip(position.xy); }`,
    fragment: `${HEADER}in vec4 vData; out vec4 fragColor;
void main() {
  float x = abs(vData.x) * 9.0;
  float core = 1.0 - smoothstep(0.9, 2.1, x);
  float glow = exp(-x * x / 18.0);
  vec3 col = mix(vec3(0.25, 0.55, 1.0), vec3(0.62, 0.42, 1.0), smoothstep(0.0, 1.0, vData.w));
  float front = mod(uTime, 4.2) / 4.2 * 1500.0 - 60.0;
  float beat = exp(-pow((vData.z - front) / 55.0, 2.0));
  fragColor = vec4(col * (0.42 * (core + glow * 0.55) + (core + glow) * beat * 0.6), 1.0);
}`,
  },
  light: {
    vertex: `${HEADER}in vec3 position; in vec3 iP; in vec4 iA; out vec2 vQ; out vec4 vA;
void main() { vQ = position.xy * 7.0; vA = iA; gl_Position = toClip(iP.xy + position.xy * 7.0 * iA.x); }`,
    fragment: `${HEADER}in vec2 vQ; in vec4 vA; out vec4 fragColor;
void main() {
  float r = length(vQ);
  float breathe = 0.82 + 0.18 * sin(uTime * 1.05 + vA.z * 6.283);
  vec3 c = vA.y > 0.5 ? vec3(1.0, 0.58, 0.2) : vec3(0.4, 0.6, 1.0);
  float disc = 1.0 - smoothstep(0.85, 1.15, r);
  fragColor = vec4(mix(c, vec3(1.0), 0.5) * disc * 1.2 + c * (exp(-r * 0.85) * 0.65 + exp(-r * r * 0.2) * 0.25) * breathe, 1.0);
}`,
  },
  particle: {
    vertex: `${HEADER}in vec3 position; in vec4 aSeed; out float vAlpha;
void main() {
  float h = uRes.y + 60.0;
  float y = mod(aSeed.y * h - uTime * (5.0 + aSeed.z * 9.0), h) - 30.0;
  float x = aSeed.x * uRes.x + sin(uTime * 0.25 + aSeed.w * 6.283) * 14.0;
  vAlpha = 0.1 + 0.32 * aSeed.w;
  gl_PointSize = (1.0 + aSeed.z * 2.0) * uDpr;
  gl_Position = toClip(vec2(x, y));
}`,
    fragment: `${HEADER}in float vAlpha; out vec4 fragColor;
void main() {
  float d = length(gl_PointCoord - 0.5) * 2.0;
  fragColor = vec4(vec3(0.6, 0.75, 1.0) * (1.0 - smoothstep(0.15, 1.0, d)) * vAlpha, 1.0);
}`,
  },
} as const;

export type Buffers = {
  backdrop: Float32Array;
  trail: { position: Float32Array; data: Float32Array; index: Uint32Array };
  quad: { position: Float32Array; index: Uint16Array };
  lights: { p: Float32Array; a: Float32Array };
  particles: { position: Float32Array; seed: Float32Array };
};

function rand(seed: number): () => number {
  let h = seed;
  return () => {
    h = (h * 16807) % 2147483647;
    return h / 2147483647;
  };
}

/** Deterministic geometry in CSS pixels for a w by h viewport. */
export function buildBuffers(w: number, h: number): Buffers {
  const r = rand(11);
  const ox = w * 0.4;
  const oy = h * 0.85;
  const ends: [number, number][] = [];
  for (let i = 0; i < COUNTS.trails; i++) {
    const a = -Math.PI * (0.1 + 0.8 * r());
    const d = h * (0.25 + 0.55 * r());
    ends.push([ox + Math.cos(a) * d * 1.3, oy + Math.sin(a) * d]);
  }
  const n = COUNTS.points;
  const vertices = COUNTS.trails * n * 2;
  const position = new Float32Array(vertices * 3);
  const data = new Float32Array(vertices * 4);
  const index = new Uint32Array(COUNTS.trails * (n - 1) * 6);
  let v = 0;
  let ix = 0;
  ends.forEach(([ex, ey], k) => {
    const bend = (r() - 0.5) * 0.6;
    const pts: [number, number][] = [];
    for (let i = 0; i < n; i++) {
      const t = i / (n - 1);
      const s = Math.sin(t * Math.PI) * bend;
      pts.push([ox + (ex - ox) * t + (ey - oy) * s * 0.3, oy + (ey - oy) * t - (ex - ox) * s * 0.3]);
    }
    let dist = 0;
    for (let i = 0; i < n; i++) {
      const [px, py] = pts[i] as [number, number];
      const [qx, qy] = pts[Math.min(n - 1, i + 1)] as [number, number];
      const [bx, by] = pts[Math.max(0, i - 1)] as [number, number];
      if (i > 0) dist += Math.hypot(px - bx, py - by);
      const tx = qx - bx;
      const ty = qy - by;
      const tl = Math.hypot(tx, ty) || 1;
      const half = 9;
      for (const side of [-1, 1]) {
        position.set([px + (-ty / tl) * side * half, py + (tx / tl) * side * half, 0], v * 3);
        data.set([side, i / (n - 1), dist, k / COUNTS.trails], v * 4);
        v++;
      }
      if (i < n - 1) {
        const b = v - 2;
        index.set([b, b + 1, b + 2, b + 1, b + 3, b + 2], ix);
        ix += 6;
      }
    }
  });
  const lp = new Float32Array(COUNTS.lights * 3);
  const la = new Float32Array(COUNTS.lights * 4);
  for (let i = 0; i < COUNTS.lights; i++) {
    const [ex, ey] = ends[i % ends.length] as [number, number];
    lp.set([ex, ey, 0], i * 3);
    la.set([i < 14 ? 7 : 2.4, i < 14 ? 1 : 0, r(), 0], i * 4);
  }
  const seed = new Float32Array(COUNTS.particles * 4);
  for (let i = 0; i < seed.length; i++) seed[i] = r();
  return {
    backdrop: new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]),
    trail: { position, data, index },
    quad: { position: new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), index: new Uint16Array([0, 1, 2, 0, 2, 3]) },
    lights: { p: lp, a: la },
    particles: { position: new Float32Array(COUNTS.particles * 3), seed },
  };
}

export type Adapter = {
  readonly gl: WebGL2RenderingContext;
  render(seconds: number): void;
};

export type Setup = { canvas: HTMLCanvasElement; w: number; h: number; dpr: number; buffers: Buffers };
