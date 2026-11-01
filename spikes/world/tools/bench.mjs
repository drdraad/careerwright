// WebGL library comparison: the same workload drawn by three.js, PixiJS and OGL, in headed system
// Chrome on this Mac. Needs the preview running (`pnpm preview`). Writes bench-results.json.
// Per library: rAF deltas, main-thread and GPU time per frame (3 s warm-up, 12 s sample), with
// vsync and unthrottled, the first drawn frame, and the JavaScript the page ships (raw and gzip).
import { writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { chromium } from "playwright";

const ORIGIN = "http://127.0.0.1:53300";
const LIBS = ["three", "pixi", "ogl"];

async function run(args, withBytes) {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--window-size=1440,900", ...args] });
  const version = browser.version();
  const out = {};
  for (const lib of LIBS) {
    const context = await browser.newContext({ viewport: null });
    const page = await context.newPage();
    const scripts = [];
    page.on("response", async (response) => {
      if (response.url().endsWith(".js")) scripts.push(response.body().catch(() => Buffer.alloc(0)));
    });
    await page.bringToFront();
    await page.goto(`${ORIGIN}/bench/?lib=${lib}`);
    await page.waitForFunction(() => window.__bench, null, { timeout: 60_000, polling: 500 });
    const result = await page.evaluate(() => window.__bench);
    if (withBytes) {
      const bodies = await Promise.all(scripts);
      result.js = {
        files: bodies.length,
        rawKB: Math.round(bodies.reduce((s, b) => s + b.length, 0) / 102.4) / 10,
        gzipKB: Math.round(bodies.reduce((s, b) => s + gzipSync(b).length, 0) / 102.4) / 10,
      };
    }
    out[lib] = result;
    const g = typeof result.gpu === "string" ? result.gpu : `${result.gpu.p50}/${result.gpu.p95}`;
    console.log(`${args.length ? "unthrottled" : "vsync"} ${lib}: rAF p95 ${result.frames.p95} ms, main p95 ${result.cpu.p95} ms, GPU p50/p95 ${g} ms`);
    await context.close();
  }
  await browser.close();
  return { version, out };
}

/** First frames in rotation (three rounds), so no library always pays the browser's warm-up. */
async function firstFrames() {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--window-size=1440,900"] });
  const times = Object.fromEntries(LIBS.map((l) => [l, []]));
  for (let round = 0; round < 3; round++) {
    for (const lib of round % 2 ? [...LIBS].reverse() : LIBS) {
      const context = await browser.newContext({ viewport: null });
      const page = await context.newPage();
      await page.goto(`${ORIGIN}/bench/?lib=${lib}`);
      await page.waitForFunction(() => document.body.dataset.firstFrame, null, { timeout: 20_000 });
      times[lib].push(Number(await page.evaluate(() => document.body.dataset.firstFrame)));
      await context.close();
    }
  }
  await browser.close();
  return Object.fromEntries(LIBS.map((l) => [l, { median: [...times[l]].sort((a, b) => a - b)[1], runs: times[l] }]));
}

const vsync = await run([], true);
const unthrottled = await run(["--disable-gpu-vsync", "--disable-frame-rate-limit"], false);
const first = await firstFrames();
const results = {
  date: new Date().toISOString(),
  browser: `Google Chrome ${vsync.version}`,
  vsync: vsync.out,
  unthrottled: unthrottled.out,
  firstFrameMs: first,
};
writeFileSync(new URL("../bench-results.json", import.meta.url), `${JSON.stringify(results, null, 2)}\n`);

console.log(`\n${results.browser}; renderer ${vsync.out.three.renderer}`);
console.log("| Library | JS shipped (gzip) | First frame | rAF p95 (vsync) | Main thread p95 | GPU p50 | GPU p95 | GPU p95 (unthrottled) |");
console.log("|---|---|---|---|---|---|---|---|");
for (const lib of LIBS) {
  const v = vsync.out[lib];
  const u = unthrottled.out[lib];
  console.log(
    `| ${lib} | ${v.js.gzipKB} KB (${v.js.rawKB} KB raw) | ${first[lib].median} ms (${first[lib].runs.join(", ")}) | ${v.frames.p95} ms | ${v.cpu.p95} ms | ${v.gpu.p50} ms | ${v.gpu.p95} ms | ${u.gpu.p95} ms |`,
  );
}
