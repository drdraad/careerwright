// Frame-time measurement for the spike, on this Mac, in system Google Chrome, headed (real GPU).
// Needs the preview running (`pnpm preview`). Writes measurements.json and prints a table.
//
// For each direction, the busiest scene (100 made-up openings, their trails, ambient particles,
// the revelation replayed every 4 s with its travel): warm up 3 s, then sample for 12 s:
//   frame interval: requestAnimationFrame deltas, the whole pipeline as the page experiences it;
//   script time:    time spent inside the frame callback (our JavaScript and the WebGL calls), not
//                   style, layout, paint or compositing;
//   GPU time:       the WebGL draw of the world, from EXT_disjoint_timer_query_webgl2 (not the
//                   compositing of the words over it).
// Two runs: vsync (Chrome as people use it; an interval cannot fall below the display's refresh)
// and unthrottled (--disable-gpu-vsync --disable-frame-rate-limit: its interval is the
// whole-pipeline cost of a frame).
// First frame: navigation start to the first drawn world frame, for the normal entry (median of
// 3) and for the busiest scene (its vsync load).
// Input to frame: from an input's handler to the end of the frame callback that answers it, for
// keystrokes on the normal entry and for skills picked in the busiest scene.
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { chromium } from "playwright";

const ORIGIN = "http://127.0.0.1:53300";
const DIRECTIONS = ["growth", "horizon", "circuit"];
const sh = (cmd, args) => execFileSync(cmd, args, { encoding: "utf8" }).trim();

const device = {
  cpu: sh("sysctl", ["-n", "machdep.cpu.brand_string"]),
  memoryGB: Number(sh("sysctl", ["-n", "hw.memsize"])) / 1024 ** 3,
  model: sh("sysctl", ["-n", "hw.model"]),
  os: sh("sw_vers", ["-productVersion"]),
};

const median = (xs) => {
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
};

async function run(label, args) {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: false,
    args: ["--window-size=1440,900", "--window-position=0,0", ...args],
  });
  const version = browser.version();
  const results = {};
  for (const direction of DIRECTIONS) {
    const context = await browser.newContext({ viewport: null });
    const page = await context.newPage();
    await page.bringToFront();
    await page.goto(`${ORIGIN}/?d=${direction}&scene=busy&measure=1`);
    await page.waitForFunction(() => window.__spike?.stats, null, { timeout: 60_000, polling: 500 });
    // Feedback in the busiest scene: pick five skills, one at a time.
    await page.evaluate(() => {
      window.__spike.inputToFrame = [];
    });
    for (const toggle of (await page.locator(".skill-toggle").all()).slice(0, 5)) {
      await toggle.click();
      await page.waitForTimeout(250);
    }
    const probe = await page.evaluate(() => ({
      ...window.__spike,
      dpr: window.devicePixelRatio,
      css: [window.innerWidth, window.innerHeight],
      canvas: [document.querySelector("canvas.world")?.width, document.querySelector("canvas.world")?.height],
    }));
    results[direction] = probe;
    const { frames, script, gpu } = probe.stats;
    console.log(
      `${label} ${direction}: interval p50 ${frames.p50} / p95 ${frames.p95} ms over ${frames.frames} frames; script p95 ${script.p95} ms; GPU p95 ${gpu.p95 ?? gpu} / p99 ${gpu.p99 ?? gpu} ms; input to frame ${probe.inputToFrame.join(", ")} ms`,
    );
    await context.close();
  }
  await browser.close();
  return { version, results };
}

async function firstFrames() {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--window-size=1440,900"] });
  const out = {};
  for (const direction of DIRECTIONS) {
    const times = [];
    const keys = [];
    for (let i = 0; i < 3; i++) {
      const context = await browser.newContext({ viewport: null });
      const page = await context.newPage();
      await page.bringToFront();
      await page.goto(`${ORIGIN}/?d=${direction}`);
      await page.waitForFunction(() => window.__spike?.firstFrame !== null, null, { timeout: 10_000 });
      times.push(await page.evaluate(() => window.__spike.firstFrame));
      await page.locator("#role-input").pressSequentially("care worker", { delay: 120 });
      await page.waitForTimeout(200);
      keys.push(...(await page.evaluate(() => window.__spike.inputToFrame)));
      await context.close();
    }
    const sorted = [...keys].sort((a, b) => a - b);
    out[direction] = {
      firstFrameMs: Math.round(median(times)),
      firstFrameRuns: times.map((t) => Math.round(t)),
      keystrokeToFrameMs: {
        median: median(keys),
        p95: sorted[Math.max(0, Math.ceil(sorted.length * 0.95) - 1)],
        max: Math.max(...keys),
        count: keys.length,
        samples: keys,
      },
    };
    console.log(`first frame ${direction}: ${out[direction].firstFrameMs} ms; keystroke to frame max ${out[direction].keystrokeToFrameMs.max} ms`);
  }
  await browser.close();
  return out;
}

const vsync = await run("vsync", []);
const unthrottled = await run("unthrottled", ["--disable-gpu-vsync", "--disable-frame-rate-limit"]);
const first = await firstFrames();

const measured = {
  date: new Date().toISOString(),
  device,
  browser: `Google Chrome ${vsync.version}`,
  scene: "busiest: 100 made-up openings with their trails, all destinations, the kept path, ambient particles; revelation (and its travel) replayed every 4 s; 1440x900 window",
  method:
    "3 s warm-up then 12 s; frame interval = rAF deltas; script = time inside the frame callback; GPU = WebGL draw (timer queries); headed system Chrome",
  vsync: vsync.results,
  unthrottled: unthrottled.results,
  first,
};
writeFileSync(new URL("../measurements.json", import.meta.url), `${JSON.stringify(measured, null, 2)}\n`);

console.log(`\n${device.cpu}, ${device.memoryGB} GB, ${device.model}, macOS ${device.os}; ${measured.browser}`);
console.log(`Renderer: ${vsync.results.growth.renderer}; ${vsync.results.growth.css.join("x")} CSS px at ${vsync.results.growth.dpr}x`);
console.log(
  "| Direction | Run | Frames | Interval p50 | Interval p95 | Intervals ≥ 16.7 ms | Script p95 | GPU p50 | GPU p95 | GPU p99 | GPU frames > 8 ms |",
);
console.log("|---|---|---|---|---|---|---|---|---|---|---|");
for (const d of DIRECTIONS) {
  for (const [name, r] of [["vsync", vsync.results[d]], ["unthrottled", unthrottled.results[d]]]) {
    const { frames, script, gpu } = r.stats;
    const g = typeof gpu === "string" ? { p50: gpu, p95: gpu, p99: gpu, over8: gpu } : gpu;
    console.log(
      `| ${d} | ${name} | ${frames.frames} | ${frames.p50} | ${frames.p95} | ${frames.over16} | ${script.p95} | ${g.p50} | ${g.p95} | ${g.p99} | ${g.over8} |`,
    );
  }
}
console.log(
  "\n| Direction | First frame, normal entry (median of 3) | First frame, busiest scene | Keystroke to frame, normal entry (median / p95 / max, n) | Skill picked to frame, busiest scene (max of 5) |",
);
console.log("|---|---|---|---|---|");
for (const d of DIRECTIONS) {
  const busy = vsync.results[d];
  const k = first[d].keystrokeToFrameMs;
  console.log(
    `| ${d} | ${first[d].firstFrameMs} ms | ${Math.round(busy.firstFrame)} ms | ${k.median} / ${k.p95} / ${k.max} ms, ${k.count} | ${Math.max(...busy.inputToFrame)} ms |`,
  );
}
