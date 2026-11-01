// The frame instrumentation reports per-frame cost (the callback's own time plus that frame's
// WebGL GPU time) beside the requestAnimationFrame interval, after a warm-up (plan section 4's
// budgets).
import { describe, expect, it, vi } from "vitest";
import { FrameMeter, frameCost, percentile, summarise } from "./frames";

describe("[UI-08] frame-time instrumentation", () => {
  it("takes nearest-rank percentiles and counts frames over each budget", () => {
    const samples = [1, 2, 3, 4, 5, 6, 7, 9, 12, 20];
    expect(
      percentile(
        [...samples].sort((a, b) => a - b),
        50,
      ),
    ).toBe(5);
    const stats = summarise(samples);
    expect(stats).toMatchObject({ frames: 10, p50: 5, p95: 20, max: 20, over8: 3, over16_7: 1 });
  });

  it("counts a steady 16.7 ms frame as within the budget, and only longer ones over it", () => {
    expect(summarise([16.7, 16.7, 16.69, 16.71]).over16_7).toBe(1);
  });

  it("pairs each frame's script time with the same frame's GPU time, by frame number", () => {
    // GPU results arrive late and one was dropped (a disjoint query): pairing by recency would
    // add frame 3's script time to frame 4's GPU time.
    const script = [
      { frame: 1, ms: 0.2 },
      { frame: 2, ms: 0.3 },
      { frame: 3, ms: 0.4 },
      { frame: 4, ms: 0.5 },
    ];
    const gpu = [
      { frame: 1, ms: 1.5 },
      { frame: 2, ms: 1.6 },
      { frame: 4, ms: 3.0 },
    ];
    expect(frameCost(script, gpu)).toEqual([0.2 + 1.5, 0.3 + 1.6, 0.5 + 3.0]);
    expect(frameCost(script, [])).toEqual([]);
  });

  it("samples only after the warm-up and stops after the sample time", () => {
    const warm = vi.fn();
    const meter = new FrameMeter(1, 2, warm);
    let frame = 0;
    for (let t = 0; t <= 3500; t += 100) meter.record(frame++, t, 0.5);
    expect(warm).toHaveBeenCalledOnce();
    expect(meter.done).toBe(true);
    const result = meter.result(null);
    // Frames from just after one second to three seconds, 100 ms apart.
    expect(result.interval.p50).toBe(100);
    expect(result.interval.frames).toBeGreaterThanOrEqual(19);
    expect(result.interval.frames).toBeLessThanOrEqual(21);
    expect(result.webglGpu).toBe("not available");
    expect(result.cost).toBe("not available");
  });
});
