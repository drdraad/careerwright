// Frame-time instrumentation for the world (plan section 4's budgets, ruled as per-frame cost:
// main-thread work in the frame callback plus the frame's WebGL GPU time, with the
// requestAnimationFrame interval reported beside them). Used only when the world is asked to
// measure. WebGL GPU time covers the world's own passes, not the compositor's work on the
// page's glass over the canvas; the unthrottled interval is the whole pipeline's cost.
import type { GpuSample } from "./gl";

export type FrameStats = {
  frames: number;
  p50: number;
  p95: number;
  p99: number;
  max: number;
  /** Samples above 8 ms (the M4 headroom) and above 16.7 ms (the M1 budget). */
  over8: number;
  over16_7: number;
};

/** The M1 budget: one frame at 60 Hz. */
const BUDGET_MS = 16.7;
/** The headroom kept on the faster machine measured: half the budget. */
const HEADROOM_MS = 8;

export const percentile = (sorted: readonly number[], p: number): number => {
  if (sorted.length === 0) return Number.NaN;
  const i = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[i] as number;
};

export function summarise(samples: readonly number[]): FrameStats {
  const sorted = [...samples].sort((a, b) => a - b);
  const round = (n: number) => Math.round(n * 100) / 100;
  return {
    frames: samples.length,
    p50: round(percentile(sorted, 50)),
    p95: round(percentile(sorted, 95)),
    p99: round(percentile(sorted, 99)),
    max: round(sorted[sorted.length - 1] ?? Number.NaN),
    over8: samples.filter((d) => d > HEADROOM_MS).length,
    over16_7: samples.filter((d) => d > BUDGET_MS).length,
  };
}

/** One frame's main-thread time (ms) in its callback, by frame number. */
export type ScriptSample = { frame: number; ms: number };

/**
 * Per-frame cost: each frame's callback time plus that same frame's WebGL GPU time, paired by
 * frame number (GPU results arrive a frame or two late). Frames without both are left out.
 */
export function frameCost(script: readonly ScriptSample[], gpu: readonly GpuSample[]): number[] {
  const gpuByFrame = new Map(gpu.map((s) => [s.frame, s.ms]));
  return script.flatMap((s) => {
    const g = gpuByFrame.get(s.frame);
    return g === undefined ? [] : [s.ms + g];
  });
}

export type WorldMeasurement = {
  renderer: string;
  devicePixelRatio: number;
  canvas: [number, number];
  /** Milliseconds from navigation start to the first drawn world frame. */
  firstFrame: number | null;
  interval: FrameStats;
  script: FrameStats;
  /** The world's WebGL passes only (timer queries). */
  webglGpu: FrameStats | "not available";
  cost: FrameStats | "not available";
};

/** Collects samples while measuring; the world loop calls it once per frame. */
export class FrameMeter {
  private intervals: number[] = [];
  private scripts: ScriptSample[] = [];
  private last = -1;
  private started = -1;
  private warm = false;
  done = false;

  constructor(
    private readonly warmupSeconds: number,
    private readonly seconds: number,
    private readonly onWarm: () => void,
  ) {}

  /** `at` is the frame's rAF timestamp (ms); `script` the callback's own time (ms). */
  record(frame: number, at: number, script: number): void {
    if (this.done) return;
    if (this.started < 0) this.started = at;
    const elapsed = at - this.started;
    if (elapsed > this.warmupSeconds * 1000) {
      if (!this.warm) {
        this.warm = true;
        this.onWarm();
      } else {
        this.intervals.push(at - this.last);
        this.scripts.push({ frame, ms: script });
      }
    }
    this.last = at;
    if (elapsed > (this.warmupSeconds + this.seconds) * 1000) this.done = true;
  }

  result(
    gpu: readonly GpuSample[] | null,
  ): Omit<WorldMeasurement, "renderer" | "devicePixelRatio" | "canvas" | "firstFrame"> {
    const cost = gpu === null ? [] : frameCost(this.scripts, gpu);
    return {
      interval: summarise(this.intervals),
      script: summarise(this.scripts.map((s) => s.ms)),
      webglGpu:
        gpu === null || gpu.length === 0 ? "not available" : summarise(gpu.map((s) => s.ms)),
      cost: cost.length === 0 ? "not available" : summarise(cost),
    };
  }
}
