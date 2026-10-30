// Frame-time instrumentation for the world (plan section 4's budgets, ruled as per-frame cost:
// main-thread work in the frame callback plus GPU time, with the requestAnimationFrame interval
// reported beside them). Used only when the world is asked to measure.

export type FrameStats = {
  frames: number;
  p50: number;
  p95: number;
  p99: number;
  max: number;
  /** Samples above 8 ms (the M4 headroom) and above 16.7 ms (the M1 budget). */
  over8: number;
  over16: number;
};

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
    over8: samples.filter((d) => d > 8).length,
    over16: samples.filter((d) => d > 16.7).length,
  };
}

/** Per-frame cost: the frame callback's own time (ms) plus that frame's GPU time when known. */
export function frameCost(script: readonly number[], gpu: readonly number[]): number[] {
  if (gpu.length === 0) return [];
  const n = Math.min(script.length, gpu.length);
  // GPU results arrive a frame or two late, so pair the most recent samples of each.
  const s = script.slice(script.length - n);
  const g = gpu.slice(gpu.length - n);
  return s.map((value, i) => value + (g[i] as number));
}

export type WorldMeasurement = {
  renderer: string;
  devicePixelRatio: number;
  canvas: [number, number];
  /** Milliseconds from navigation start to the first drawn world frame. */
  firstFrame: number | null;
  interval: FrameStats;
  script: FrameStats;
  gpu: FrameStats | "not available";
  cost: FrameStats | "not available";
};

/** Collects samples while measuring; the world loop calls it once per frame. */
export class FrameMeter {
  private intervals: number[] = [];
  private scripts: number[] = [];
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
  record(at: number, script: number): void {
    if (this.done) return;
    if (this.started < 0) this.started = at;
    const elapsed = at - this.started;
    if (elapsed > this.warmupSeconds * 1000) {
      if (!this.warm) {
        this.warm = true;
        this.onWarm();
      } else {
        this.intervals.push(at - this.last);
        this.scripts.push(script);
      }
    }
    this.last = at;
    if (elapsed > (this.warmupSeconds + this.seconds) * 1000) this.done = true;
  }

  result(
    gpu: readonly number[] | null,
  ): Omit<WorldMeasurement, "renderer" | "devicePixelRatio" | "canvas" | "firstFrame"> {
    const cost = gpu === null ? [] : frameCost(this.scripts, gpu);
    return {
      interval: summarise(this.intervals),
      script: summarise(this.scripts),
      gpu: gpu === null || gpu.length === 0 ? "not available" : summarise(gpu),
      cost: cost.length === 0 ? "not available" : summarise(cost),
    };
  }
}
