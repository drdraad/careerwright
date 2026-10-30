// Captures the living world's references (compositions/world.html): every place at 1440x900,
// 768x1024 and 390x844, and each honest state, with Playwright's pinned Chromium. Records the
// automatable checks (ruling R2): axe (WCAG 2.2 A/AA rules), horizontal overflow, console
// errors, both fonts loaded, the wordmark inside the rail, a visible "Synthetic demo" label,
// every name in the world inside
// the window and clear of the panels and of each other, every light in view named and every
// named light in view (the revelation's subject always), no name, gate or key over a light's
// centre, the key clear of the panels, the time and cost instrument's labels clear of each
// other and its marks, and at most one filled primary action in view. The lights and gates
// come from the drawing (window.__worldCheck); whether a name is seen comes from the page.
// Writes screenshots/*.png and screenshots/checks.md. Exits 1 if any check fails.
//   pnpm --dir docs/design run screenshots            (all)
//   pnpm --dir docs/design run screenshots routes     (one place)
import { mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { dirname, extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(root, "screenshots");
const axeSource = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

// Served over loopback HTTP so axe can read the stylesheets. Only files under docs/design.
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".ttf": "font/ttf", ".svg": "image/svg+xml", ".png": "image/png" };
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(new URL(req.url, "http://localhost").pathname)));
  if (!path.startsWith(root + sep)) return void res.writeHead(403).end();
  try {
    res.writeHead(200, { "content-type": TYPES[extname(path)] ?? "application/octet-stream" }).end(readFileSync(path));
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;

const DESKTOP = { name: "1440x900", width: 1440, height: 900 };
const TABLET = { name: "768x1024", width: 768, height: 1024 };
const PHONE = { name: "390x844", width: 390, height: 844 };
const ALL = [DESKTOP, TABLET, PHONE];
// Every place by default at the three sizes; each honest state at least once, distress and
// "not built yet" on a phone too.
const CAPTURES = [
  ...["you", "roles", "skills", "options", "routes", "plan"].map((place) => ({ place, state: "default", viewports: ALL })),
  { place: "you", state: "distress", viewports: [DESKTOP, PHONE] },
  { place: "you", state: "failed", viewports: [DESKTOP] },
  { place: "roles", state: "stale", viewports: [DESKTOP] },
  { place: "roles", state: "unknown", viewports: [DESKTOP] },
  { place: "roles", state: "three-targets", viewports: ALL },
  { place: "roles", state: "not-built", viewports: [DESKTOP, PHONE] },
  { place: "skills", state: "unknown", viewports: [DESKTOP] },
  { place: "options", state: "unknown", viewports: [DESKTOP] },
  { place: "routes", state: "failed", viewports: [DESKTOP] },
];
const only = process.argv[2];

mkdirSync(out, { recursive: true });
if (!only) for (const file of readdirSync(out)) if (file.endsWith(".png")) rmSync(join(out, file));
const browser = await chromium.launch();
const results = [];
for (const { place, state, query, name, viewports } of CAPTURES.filter((c) => !only || c.place === only)) {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1, reducedMotion: "reduce", colorScheme: "dark" });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    await page.goto(`${origin}/compositions/world.html?place=${place}&state=${state}${query ? `&${query}` : ""}`, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForFunction(() => window.__worldReady === true);
    const fonts = await page.evaluate(() => ({
      body: document.fonts.check('16px "Source Sans 3"'),
      display: document.fonts.check('600 39px "Outfit"'),
    }));
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    const labels = await page.evaluate(() => {
      const problems = [];
      const box = (e) => e.getBoundingClientRect();
      const hit = (a, b) => a.left < b.right - 0.5 && b.left < a.right - 0.5 && a.top < b.bottom - 0.5 && b.top < a.bottom - 0.5;
      const holds = (b, p) => p.x >= b.left && p.x <= b.right && p.y >= b.top && p.y <= b.bottom;
      const seen = (e) => {
        const r = box(e);
        const style = getComputedStyle(e);
        return r.width > 1 && r.height > 1 && r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight && style.visibility !== "hidden" && style.display !== "none";
      };
      // The wordmark stays inside its rail, where the rail is shown.
      const rail = document.querySelector(".rail");
      const mark = document.querySelector(".wordmark span");
      if (rail && mark && box(rail).width > 0 && (box(mark).left < box(rail).left || box(mark).right > box(rail).right)) problems.push("the wordmark leaves the rail");
      // The synthetic label is visible at every size (Global Constraint 5).
      if (![...document.querySelectorAll(".synthetic")].some((e) => e.textContent.trim() === "Synthetic demo" && seen(e))) problems.push(`no visible "Synthetic demo" label`);
      const names = [...document.querySelectorAll(".world-label")];
      const panels = [...document.querySelectorAll(".panel, .strip, .rail, .topbar")].filter((e) => box(e).width > 0);
      const key = document.querySelector(".legend");
      const keyShown = key !== null && seen(key);
      const covers = keyShown ? [...panels, key] : panels;
      names.forEach((n, i) => {
        const a = box(n);
        if (a.left < 0 || a.top < 0 || a.right > innerWidth || a.bottom > innerHeight) problems.push(`"${n.textContent}" leaves the window`);
        for (const p of covers) if (hit(a, box(p))) problems.push(`"${n.textContent}" is under a panel or the key`);
        for (const m of names.slice(i + 1)) if (hit(a, box(m))) problems.push(`"${n.textContent}" overlaps "${m.textContent}"`);
      });
      if (keyShown) for (const p of panels) if (hit(box(key), box(p))) problems.push("the key to the lights is under a panel");
      // Every light in view has its name in view; a light under a panel or out of the window
      // has none; the revelation's subject is in view and named. Nothing covers a light.
      const { lights, gates } = window.__worldCheck;
      const inWindow = (p) => p.visible && p.x >= 0 && p.y >= 0 && p.x <= innerWidth && p.y <= innerHeight;
      const inView = (p) => inWindow(p) && !panels.some((c) => holds(box(c), p));
      const nameOf = (id) => document.querySelector(`.world-label[data-for="${CSS.escape(id)}"]`);
      for (const l of [...lights, ...gates]) {
        const n = nameOf(l.name);
        if (inView(l) && n === null) problems.push(`the light "${l.id}" is in view without a name`);
        if (l.revelation && !inView(l)) problems.push(`the revelation's subject "${l.id}" is not in view`);
      }
      for (const n of names) {
        const its = [...lights, ...gates].filter((l) => l.name === n.dataset.for);
        if (its.length > 0 && !its.some(inView)) problems.push(`"${n.textContent}" names a light that is not in view`);
      }
      const centres = lights.filter(inWindow);
      for (const n of names) for (const c of centres) if (c.name !== n.dataset.for && holds(box(n), c)) problems.push(`"${n.textContent}" covers the light "${c.id}"`);
      for (const g of gates.filter(inWindow)) for (const c of centres) if (Math.abs(g.x - c.x) <= g.r && Math.abs(g.y - c.y) <= g.r) problems.push(`the gate "${g.id}" covers the light "${c.id}"`);
      if (keyShown) for (const c of centres) if (holds(box(key), c)) problems.push(`the key covers the light "${c.id}"`);
      for (const svg of document.querySelectorAll(".instrument svg")) {
        const texts = [...svg.querySelectorAll("text")];
        const marks = [...svg.querySelectorAll("circle")];
        texts.forEach((t, i) => {
          for (const u of texts.slice(i + 1)) if (hit(box(t), box(u))) problems.push(`instrument: "${t.textContent}" overlaps "${u.textContent}"`);
          for (const m of marks) if (hit(box(t), box(m))) problems.push(`instrument: "${t.textContent}" overlaps a mark`);
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
    const shown = await page.evaluate(() => document.querySelectorAll(".world-label").length);
    const file = `${place}--${name ?? state}--${viewport.name}.png`;
    await page.screenshot({ path: join(out, file) });
    results.push({ place, state, viewport: viewport.name, file, fonts, overflow, axe, errors, labels, primaries, shown });
    await context.close();
  }
}
await browser.close();
server.close();

const failed = results.filter((r) => r.axe.length || r.overflow > 0 || r.errors.length || r.labels.length || !r.fonts.body || !r.fonts.display || r.primaries > 1);
const lines = [
  "# Screenshot checks",
  "",
  "Generated by `docs/design/tools/screenshots.mjs` (Playwright 1.64.1, its pinned Chromium, reduced motion, device scale 1): the still world, as reduced motion and calm mode draw it. Automated checks only: axe-core 4.14.0 with the WCAG 2.0/2.1/2.2 A and AA rule tags, horizontal overflow, console errors, both fonts loaded, the wordmark inside the rail, a visible \"Synthetic demo\" label, every name in the world inside the window and clear of the panels, the key and each other, every light and gate in view named and no name for a light out of view (the revelation's subject always in view), no name, gate or key over a light's centre, the key clear of the panels, the time and cost instrument's labels clear of each other and its marks, and at most one filled primary action in view. The lights and gates are taken from the drawing; whether a name is seen is measured in the page. They are not a design review, a VoiceOver test or a Safari check (ruling R2).",
  "",
  `Result: **${results.length - failed.length} of ${results.length} captures pass**.`,
  "",
  "| Screenshot | Fonts loaded | Horizontal overflow | axe violations | Console errors | Names placed in the world | Label, name and light problems | Filled primaries |",
  "|---|---|---:|---|---|---:|---|---:|",
  ...results.map((r) => `| \`${r.file}\` | ${r.fonts.body && r.fonts.display ? "yes" : "**no**"} | ${r.overflow > 0 ? `**${r.overflow}px**` : "0"} | ${r.axe.length ? r.axe.map((v) => `**${v.id}** (${v.impact}, ${v.nodes}: \`${v.target}\`)`).join("; ") : "none"} | ${r.errors.length ? `**${r.errors.join("; ")}**` : "none"} | ${r.shown} | ${r.labels.length ? `**${r.labels.join("; ")}**` : "none"} | ${r.primaries > 1 ? `**${r.primaries}**` : r.primaries} |`),
  "",
];
if (!only) writeFileSync(join(out, "checks.md"), lines.join("\n"));
for (const r of failed) console.log("FAIL", r.file, JSON.stringify({ overflow: r.overflow, axe: r.axe, errors: r.errors, fonts: r.fonts, labels: r.labels, primaries: r.primaries }));
console.log(`${results.length - failed.length}/${results.length} captures pass`);
process.exit(failed.length ? 1 : 0);
