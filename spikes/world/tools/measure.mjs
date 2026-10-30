// Frame-time measurement for the spike, on this Mac, in system Google Chrome, headed (real GPU).
// Needs the preview running (`pnpm preview`). Writes measurements.json and prints a table.
//
// For each direction, the busiest scene (100 made-up openings, their trails, ambient particles,
// the revelation replayed every 4 s with its travel): warm up 3 s, then sample
// requestAnimationFrame deltas for 12 s. Two runs:
//   vsync:       Chrome as people use it. Deltas cannot fall below the display's refresh interval.
//   unthrottled: --disable-gpu-vsync --disable-frame-rate-limit, so deltas show what a frame costs.
// First frame: navigation start to the first drawn world frame, on the normal entry (median of 3).
// Key to frame: from a keystroke's handler to the end of the frame that answers it.
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
    const probe = await page.evaluate(() => ({
      ...window.__spike,
      dpr: window.devicePixelRatio,
      css: [window.innerWidth, window.innerHeight],
      canvas: [document.querySelector("canvas.world")?.width, document.querySelector("canvas.world")?.height],
    }));
    results[direction] = probe;
    const { frames, cpu, gpu } = probe.stats;
    console.log(
      `${label} ${direction}: rAF p50 ${frames.p50} / p95 ${frames.p95} ms over ${frames.frames} frames; CPU p95 ${cpu.p95} ms; GPU p95 ${gpu.p95 ?? gpu} ms`,
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
      await page.locator("#role-input").pressSequentially("care", { delay: 120 });
      await page.waitForTimeout(200);
      keys.push(...(await page.evaluate(() => window.__spike.keyToFrame)));
      await context.close();
    }
    out[direction] = {
      firstFrameMs: Math.round(median(times)),
      firstFrameRuns: times.map((t) => Math.round(t)),
      keyToFrameMs: { median: median(keys), max: Math.max(...keys), samples: keys.length },
    };
    console.log(`first frame ${direction}: ${out[direction].firstFrameMs} ms; key to frame max ${out[direction].keyToFrameMs.max} ms`);
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
  method: "rAF deltas, 3 s warm-up then 12 s sample, headed system Chrome",
  vsync: vsync.results,
  unthrottled: unthrottled.results,
  first,
};
writeFileSync(new URL("../measurements.json", import.meta.url), `${JSON.stringify(measured, null, 2)}\n`);

console.log(`\n${device.cpu}, ${device.memoryGB} GB, ${device.model}, macOS ${device.os}; ${measured.browser}`);
console.log(`Renderer: ${vsync.results.growth.renderer}; ${vsync.results.growth.css.join("x")} CSS px at ${vsync.results.growth.dpr}x`);
console.log(
  "| Direction | Run | Frames | rAF p50 | rAF p95 | > 16.7 ms | Main thread p95 | GPU p50 | GPU p95 | First frame | Key to frame (max) |",
);
console.log("|---|---|---|---|---|---|---|---|---|---|---|");
for (const d of DIRECTIONS) {
  for (const [name, r] of [["vsync", vsync.results[d]], ["unthrottled", unthrottled.results[d]]]) {
    const { frames, cpu, gpu } = r.stats;
    const g = typeof gpu === "string" ? { p50: gpu, p95: gpu } : gpu;
    const tail = name === "vsync" ? `${first[d].firstFrameMs} ms | ${first[d].keyToFrameMs.max} ms` : " | ";
    console.log(
      `| ${d} | ${name} | ${frames.frames} | ${frames.p50} | ${frames.p95} | ${frames.over16} | ${cpu.p95} | ${g.p50} | ${g.p95} | ${tail} |`,
    );
  }
}
