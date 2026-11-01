// Library comparison page: ?lib=three|pixi|ogl. Draws the same workload with the chosen library,
// warms up 3 s, then samples 12 s: rAF deltas, main-thread time per frame and GPU time per frame
// (timer queries). Results land in window.__bench for tools/bench.mjs.
import { summarise } from "../src/frames.ts";
import { type Adapter, type Setup, buildBuffers } from "./scene.ts";

const LOADERS: Record<string, () => Promise<{ create(setup: Setup): Promise<Adapter> }>> = {
  three: () => import("./three.ts"),
  pixi: () => import("./pixi.ts"),
  ogl: () => import("./ogl.ts"),
};

declare global {
  interface Window {
    __bench: unknown;
  }
}

const lib = new URLSearchParams(location.search).get("lib") ?? "three";
const canvas = document.querySelector("canvas") as HTMLCanvasElement;
const label = document.querySelector("p") as HTMLParagraphElement;
label.textContent = `Spike library comparison: ${lib}. Synthetic shapes only.`;
const w = window.innerWidth;
const h = window.innerHeight;
const dpr = Math.min(window.devicePixelRatio || 1, 2);
const load = LOADERS[lib];
if (!load) throw new Error(`Unknown library ${lib}`);
const adapter = await load().then((m) => m.create({ canvas, w, h, dpr, buffers: buildBuffers(w, h) }));
const gl = adapter.gl;
const info = gl.getExtension("WEBGL_debug_renderer_info");
const renderer = info ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)) : "unknown";
const timer = gl.getExtension("EXT_disjoint_timer_query_webgl2") as {
  TIME_ELAPSED_EXT: number;
  GPU_DISJOINT_EXT: number;
} | null;

const WARMUP = 3000;
const SAMPLE = 12000;
const deltas: number[] = [];
const cpu: number[] = [];
const gpu: number[] = [];
const pending: WebGLQuery[] = [];
let firstFrame: number | null = null;
let start = -1;
let last = -1;

function collect(sampling: boolean): void {
  while (timer && pending.length > 0) {
    const q = pending[0] as WebGLQuery;
    if (!gl.getQueryParameter(q, gl.QUERY_RESULT_AVAILABLE)) break;
    if (sampling && !gl.getParameter(timer.GPU_DISJOINT_EXT)) gpu.push((gl.getQueryParameter(q, gl.QUERY_RESULT) as number) / 1e6);
    gl.deleteQuery(q);
    pending.shift();
  }
}

function tick(t: number): void {
  if (start < 0) start = t;
  const sampling = t - start > WARMUP;
  const began = performance.now();
  const q = timer ? gl.createQuery() : null;
  if (timer && q) gl.beginQuery(timer.TIME_ELAPSED_EXT, q);
  adapter.render(t / 1000);
  if (timer && q) {
    gl.endQuery(timer.TIME_ELAPSED_EXT);
    pending.push(q);
  }
  collect(sampling);
  if (firstFrame === null) {
    firstFrame = performance.now();
    document.body.dataset.firstFrame = String(Math.round(firstFrame));
  }
  if (sampling) {
    cpu.push(performance.now() - began);
    if (last >= 0) deltas.push(t - last);
  }
  last = t;
  if (t - start < WARMUP + SAMPLE) requestAnimationFrame(tick);
  else
    window.__bench = {
      lib,
      renderer,
      dpr,
      css: [w, h],
      firstFrame,
      frames: summarise(deltas),
      cpu: summarise(cpu),
      gpu: timer && gpu.length > 0 ? summarise(gpu) : "not available",
    };
}
requestAnimationFrame(tick);
