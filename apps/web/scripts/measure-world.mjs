// Measures the world's frame costs in its busiest scene (plan section 4's budgets). Per the
// Sprint W ruling, the budget is per-frame cost: main-thread work in the frame callback plus
// that same frame's WebGL GPU time (timer queries, paired by frame number); the
// requestAnimationFrame interval is reported beside it, since a 120 Hz display floors it at
// 8.33 ms. WebGL GPU time covers the world's own passes only, not the compositor's work on the
// page's glass; the unthrottled interval is the whole pipeline's cost. Runs the static
// Storybook's "World / Busiest scene" story (synthetic: 100 openings, 12 skills, 5
// destinations, the motes, travel every 3 s and the ignition every 4 s) three ways in Google
// Chrome on this machine: headed at the display's refresh, headed unthrottled, and headless (a
// 60 Hz frame clock). Writes the results, with the commit, device, browser and renderer, as JSON.
//
// The two headed runs open a browser window on this machine's screen: warn the person at the
// screen first, and never run it from a check (`make check`, `make acceptance`).
//   pnpm run build-storybook && node scripts/measure-world.mjs <out.json>
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const out = process.argv[2];
if (!out) throw new Error("usage: node scripts/measure-world.mjs <out.json>");
const STATIC = fileURLToPath(new URL("../storybook-static/", import.meta.url));
if (!existsSync(join(STATIC, "index.json")))
  throw new Error("run `pnpm run build-storybook` first");
const TYPES = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".ttf": "font/ttf",
};
const server = createServer((request, response) => {
  const path = normalize(decodeURIComponent(new URL(request.url ?? "/", "http://x").pathname));
  const file = join(STATIC, path === "/" ? "index.html" : path);
  if (!file.startsWith(STATIC) || !existsSync(file)) return void response.writeHead(404).end();
  response
    .writeHead(200, { "content-type": TYPES[extname(file)] ?? "application/octet-stream" })
    .end(readFileSync(file));
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const story = `http://127.0.0.1:${server.address().port}/iframe.html?id=world--busiest-scene&viewMode=story&measure=1`;

const sh = (cmd, args) => {
  try {
    return execFileSync(cmd, args, { encoding: "utf8" }).trim();
  } catch {
    return "unknown";
  }
};
const device = {
  model: sh("sysctl", ["-n", "hw.model"]),
  chip: sh("sysctl", ["-n", "machdep.cpu.brand_string"]),
  memoryGB: Math.round(Number(sh("sysctl", ["-n", "hw.memsize"])) / 2 ** 30),
  os: `macOS ${sh("sw_vers", ["-productVersion"])}`,
};

const RUNS = [
  { name: "headed, vsync (display refresh)", headless: false, args: [] },
  {
    name: "headed, unthrottled",
    headless: false,
    args: ["--disable-gpu-vsync", "--disable-frame-rate-limit"],
  },
  { name: "headless, 60 Hz frame clock", headless: true, args: ["--use-angle=metal"] },
];

const results = [];
for (const run of RUNS) {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: run.headless,
    args: run.args,
  });
  // A Retina display draws the canvas at twice the CSS pixels, as the target Mac does.
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    reducedMotion: "no-preference",
  });
  await page.goto(story);
  await page.waitForFunction(() => window.__careerwrightWorldFrames !== undefined, undefined, {
    timeout: 60_000,
  });
  const measured = await page.evaluate(() => window.__careerwrightWorldFrames);
  results.push({
    run: run.name,
    browser: `Google Chrome ${browser.version()}`,
    viewport: "1440x900 at device scale 2",
    ...measured,
  });
  await browser.close();
}
server.close();

const commit = sh("git", ["rev-parse", "HEAD"]);
const dirty = sh("git", ["status", "--porcelain", "--", "src", "scripts"]) !== "";
const report = {
  measuredAt: new Date().toISOString(),
  commit: dirty ? `${commit} (with uncommitted changes)` : commit,
  scene: {
    story: "World / Busiest scene",
    synthetic: true,
    contents:
      "Invented for measurement, never shown in the app: 100 openings and their trails, 12 skills, 5 destinations, 360 motes; travel every 3 s; ignition every 4 s; warm-up 3 s, then 12 s",
  },
  costIs: "main-thread time in the frame callback plus the same frame's WebGL GPU time",
  device,
  results,
};
writeFileSync(out, `${JSON.stringify(report, null, 2)}\n`);
for (const r of results) {
  const cost =
    typeof r.cost === "string"
      ? r.cost
      : `p50 ${r.cost.p50} / p95 ${r.cost.p95} / max ${r.cost.max} ms`;
  const gpu = typeof r.webglGpu === "string" ? r.webglGpu : `p95 ${r.webglGpu.p95} ms`;
  console.log(
    `${r.run}: interval p95 ${r.interval.p95} ms; script p95 ${r.script.p95} ms; WebGL GPU time ${gpu}; per-frame cost ${cost}; ${r.renderer}`,
  );
}
