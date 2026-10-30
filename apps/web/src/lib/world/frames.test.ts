// The frame instrumentation reports per-frame cost (the callback's own time plus GPU time)
// beside the requestAnimationFrame interval, after a warm-up (plan section 4's budgets).
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
    expect(stats).toMatchObject({ frames: 10, p50: 5, p95: 20, max: 20, over8: 3, over16: 1 });
  });

  it("pairs each frame's script time with its GPU time, newest with newest", () => {
    expect(frameCost([0.2, 0.3, 0.4], [1.5, 1.6])).toEqual([0.3 + 1.5, 0.4 + 1.6]);
    expect(frameCost([0.2], [])).toEqual([]);
  });

  it("samples only after the warm-up and stops after the sample time", () => {
    const warm = vi.fn();
    const meter = new FrameMeter(1, 2, warm);
    for (let t = 0; t <= 3500; t += 100) meter.record(t, 0.5);
    expect(warm).toHaveBeenCalledOnce();
    expect(meter.done).toBe(true);
    const result = meter.result(null);
    // Frames from just after one second to three seconds, 100 ms apart.
    expect(result.interval.p50).toBe(100);
    expect(result.interval.frames).toBeGreaterThanOrEqual(19);
    expect(result.interval.frames).toBeLessThanOrEqual(21);
    expect(result.gpu).toBe("not available");
    expect(result.cost).toBe("not available");
  });
});
