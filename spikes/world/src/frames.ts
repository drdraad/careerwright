// Frame-time measurement for the spike's report: requestAnimationFrame deltas in the busiest
// scene, after a warm-up, plus the first drawn world frame.

export type FrameStats = {
  frames: number;
  seconds: number;
  p50: number;
  p95: number;
  p99: number;
  max: number;
  over8: number;
  over16: number;
};

export const percentile = (sorted: readonly number[], p: number): number => {
  if (sorted.length === 0) return Number.NaN;
  const i = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[i] as number;
};

export function summarise(deltas: readonly number[]): FrameStats {
  const sorted = [...deltas].sort((a, b) => a - b);
  const round = (n: number) => Math.round(n * 100) / 100;
  return {
    frames: deltas.length,
    seconds: round(deltas.reduce((s, d) => s + d, 0) / 1000),
    p50: round(percentile(sorted, 50)),
    p95: round(percentile(sorted, 95)),
    p99: round(percentile(sorted, 99)),
    max: round(sorted[sorted.length - 1] ?? Number.NaN),
    over8: deltas.filter((d) => d > 8).length,
    over16: deltas.filter((d) => d > 16.7).length,
  };
}

/** Samples rAF deltas for `seconds` after `warmup` seconds, then resolves. */
export function sampleFrames(warmup: number, seconds: number, onWarm: () => void): Promise<FrameStats> {
  return new Promise((resolve) => {
    const deltas: number[] = [];
    let last = -1;
    let start = -1;
    let warm = false;
    const tick = (t: number) => {
      if (start < 0) start = t;
      if (t - start > warmup * 1000) {
        if (!warm) {
          warm = true;
          onWarm();
        } else deltas.push(t - last);
      }
      last = t;
      if (t - start < (warmup + seconds) * 1000) requestAnimationFrame(tick);
      else resolve(summarise(deltas));
    };
    requestAnimationFrame(tick);
  });
}
