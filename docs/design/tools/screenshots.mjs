// Captures every composition state at 1440x900 and 390x844 with Playwright's pinned
// Chromium, and records the automatable checks (ruling R2): axe (WCAG 2.2 A/AA rules),
// horizontal overflow, console errors, font loading, chart label collisions, at most one
// filled primary action in view (S0-V08) and, on the phone, the open sheet's clearance: the
// first list card starts above it (S0-V07) and no control brought into view by focus is
// under it or the reply field (S0-V02). Writes screenshots/*.png and screenshots/checks.md.
// Exits 1 if any check fails.
//   pnpm --dir docs/design run screenshots            (all)
//   pnpm --dir docs/design run screenshots conversation   (one composition)
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { dirname, extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(root, "screenshots");
const axeSource = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

// Pages are served over loopback HTTP rather than file:// so that axe can read the
// stylesheets (file:// blocks its requests). Only files under docs/design are served.
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".ttf": "font/ttf", ".svg": "image/svg+xml", ".png": "image/png" };
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(new URL(req.url, "http://localhost").pathname)));
  if (!path.startsWith(root + sep)) return void res.writeHead(403).end();
  try {
    const body = readFileSync(path);
    res.writeHead(200, { "content-type": TYPES[extname(path)] ?? "application/octet-stream" }).end(body);
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;

const COMPOSITIONS = ["conversation", "opportunity-map", "route-comparison"];
const STATES = ["default", "unknown", "failure"];
const VIEWPORTS = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "390x844", width: 390, height: 844 },
];
const only = process.argv[2];
// How much of the first list card must show above a phone's open sheet: its letter or
// title line (12 px padding and one 24 px line, rounded up).
const FIRST_CARD_CLEAR_PX = 40;

mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const results = [];
for (const composition of COMPOSITIONS.filter((c) => !only || c === only)) {
  for (const state of STATES) {
    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport, deviceScaleFactor: 1, reducedMotion: "reduce", colorScheme: "dark" });
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
      const url = `${origin}/compositions/${composition}.html?state=${state}`;
      await page.goto(url, { waitUntil: "load" });
      await page.evaluate(() => document.fonts.ready);
      const fonts = await page.evaluate(() => ({
        body: document.fonts.check('16px "Source Sans 3"'),
        display: document.fonts.check('31px "Newsreader"'),
      }));
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      // Long-label check for charts marked data-check-labels: no text box may leave the
      // viewBox or overlap another text box or a data mark (circle).
      const labels = await page.evaluate(() => {
        const problems = [];
        for (const svg of document.querySelectorAll("svg[data-check-labels]")) {
          if (!svg.getBoundingClientRect().width) continue;
          const vb = svg.viewBox.baseVal;
          const box = (n) => n.getBBox();
          const texts = [...svg.querySelectorAll("text")].filter((t) => t.getAttribute("aria-hidden") !== "skip-check");
          const marks = [...svg.querySelectorAll("circle[data-mark]")];
          const hit = (a, b, pad = 1) => a.x < b.x + b.width - pad && b.x < a.x + a.width - pad && a.y < b.y + b.height - pad && b.y < a.y + a.height - pad;
          texts.forEach((t, i) => {
            const a = box(t);
            if (a.x < vb.x || a.y < vb.y || a.x + a.width > vb.x + vb.width || a.y + a.height > vb.y + vb.height) problems.push(`${svg.id}: "${t.textContent}" leaves the viewBox`);
            for (const u of texts.slice(i + 1)) if (hit(a, box(u))) problems.push(`${svg.id}: "${t.textContent}" overlaps "${u.textContent}"`);
            for (const m of marks) if (hit(a, box(m))) problems.push(`${svg.id}: "${t.textContent}" overlaps a mark`);
          });
        }
        return problems;
      });
      await page.addScriptTag({ content: axeSource });
      const axe = await page.evaluate(async () => {
        const r = await window.axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] } });
        return r.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, target: v.nodes[0]?.target?.join(" ") }));
      });
      const primaries = await page.evaluate(() => [...document.querySelectorAll(".btn-primary")].filter((b) => b.getClientRects().length).length);
      const file = `${composition}--${state}--${viewport.name}.png`;
      await page.screenshot({ path: join(out, file) });
      // Phone sheet clearance, measured after the screenshot because focusing scrolls.
      const sheet = await page.evaluate((clear) => {
        const sheet = [...document.querySelectorAll(".drawer, .role-card, .journey")].find((e) => e.getClientRects().length && getComputedStyle(e).position === "fixed");
        if (!sheet) return { firstCardClear: true, covered: [] };
        const top = sheet.getBoundingClientRect().top;
        const first = [...document.querySelectorAll(".route-card, .listing-card")].find((e) => e.getClientRects().length);
        const firstCardClear = !first || first.getBoundingClientRect().top + clear <= top;
        const covered = [];
        for (const control of document.querySelectorAll("main button, main a, main input, main select, main textarea, main summary")) {
          if (!control.getClientRects().length || sheet.contains(control)) continue;
          control.focus();
          const b = control.getBoundingClientRect();
          const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
          if (!hit || !(control === hit || control.contains(hit))) covered.push(`"${(control.textContent || control.placeholder || control.tagName).trim().slice(0, 40)}"`);
        }
        return { firstCardClear, covered };
      }, FIRST_CARD_CLEAR_PX);
      results.push({ composition, state, viewport: viewport.name, file, fonts, overflow, axe, errors, labels, primaries, ...sheet });
      await context.close();
    }
  }
}
await browser.close();
server.close();

const failed = results.filter((r) => r.axe.length || r.overflow > 0 || r.errors.length || r.labels.length || !r.fonts.body || !r.fonts.display || r.primaries > 1 || !r.firstCardClear || r.covered.length);
const lines = [
  "# Screenshot checks",
  "",
  `Generated by \`docs/design/tools/screenshots.mjs\` (Playwright 1.64.1, its pinned Chromium, reduced motion, device scale 1). Automated checks only: axe-core 4.14.0 with the WCAG 2.0/2.1/2.2 A and AA rule tags, horizontal overflow, console errors, font loading, chart label collisions (text leaving its chart or overlapping another label or a data mark), at most one filled primary action in view, and, where a phone sheet is open, that the first list card starts at least ${FIRST_CARD_CLEAR_PX} px above it and that no control brought into view by focus is covered at its centre (by the sheet or the reply field). They are not a design review, a VoiceOver test or a Safari check (ruling R2).`,
  "",
  `Result: **${results.length - failed.length} of ${results.length} captures pass**.`,
  "",
  "| Screenshot | Fonts loaded | Horizontal overflow | axe violations | Console errors | Label collisions | Filled primaries | First card above the sheet | Covered after focus |",
  "|---|---|---:|---|---|---|---:|---|---|",
  ...results.map((r) => `| \`${r.file}\` | ${r.fonts.body && r.fonts.display ? "yes" : "**no**"} | ${r.overflow > 0 ? `**${r.overflow}px**` : "0"} | ${r.axe.length ? r.axe.map((v) => `**${v.id}** (${v.impact}, ${v.nodes}: \`${v.target}\`)`).join("; ") : "none"} | ${r.errors.length ? `**${r.errors.join("; ")}**` : "none"} | ${r.labels.length ? `**${r.labels.length}**` : "none"} | ${r.primaries > 1 ? `**${r.primaries}**` : r.primaries} | ${r.firstCardClear ? "yes" : "**no**"} | ${r.covered.length ? `**${r.covered.join(", ")}**` : "none"} |`),
  "",
];
if (!only) writeFileSync(join(out, "checks.md"), lines.join("\n"));
for (const r of failed) console.log("FAIL", r.file, JSON.stringify({ overflow: r.overflow, axe: r.axe, errors: r.errors, fonts: r.fonts, labels: r.labels, primaries: r.primaries, firstCardClear: r.firstCardClear, covered: r.covered }));
console.log(`${results.length - failed.length}/${results.length} captures pass`);
process.exit(failed.length ? 1 : 0);
