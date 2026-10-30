// The spike's own acceptance check, against the running preview (`pnpm preview` or `make spike-world`).
// For each direction it plays the first ten seconds and checks, in a real browser:
// - the first answer changes the world within ten seconds and the revelation's sentence and
//   evidence are in the DOM;
// - the words are the same moving, with the system's reduced-motion setting, and in calm mode;
// - words stay shown, with no entry animation replaying, after calm mode or the system's reduced
//   motion setting is turned on and off again;
// - teal appears only on selection, the kept path and the primary action;
// - pointing at a destination (keyboard focus) shows what it shares;
// - after the first answer and after the revelation, at three window sizes, every skill and
//   destination is inside the window, visible, not covered, focusable, and next to its own light
//   (or joined to it by a leader line);
// - pointing at a destination's light itself shows what it shares;
// - the chooser's motion has a pause control;
// - picking a skill and keeping the destination in view work from the keyboard;
// - no request leaves 127.0.0.1.
// Usage: node tools/check.mjs [--headed]
import { chromium } from "playwright";

const ORIGIN = "http://127.0.0.1:53300";
const DIRECTIONS = ["growth", "horizon", "circuit"];
const headed = process.argv.includes("--headed");
const failures = [];
const fail = (message) => {
  failures.push(message);
  console.log(`  FAIL ${message}`);
};
const pass = (message) => console.log(`  ok   ${message}`);

const browser = await chromium.launch({ channel: "chrome", headless: !headed });

async function play(direction, { reducedMotion = "no-preference", calm = false } = {}) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion });
  const page = await context.newPage();
  const foreign = [];
  const errors = [];
  page.on("request", (r) => {
    if (!r.url().startsWith(`${ORIGIN}/`) && !r.url().startsWith("data:")) foreign.push(r.url());
  });
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  await page.goto(`${ORIGIN}/?d=${direction}${calm ? "&calm=1" : ""}`);
  const started = Date.now();
  await page.locator("#role-input").pressSequentially("chef", { delay: 60 });
  await page.keyboard.press("Enter");
  await page.locator(".skills .node-label").first().waitFor({ state: "visible" });
  const changedAfter = Date.now() - started;
  await page.locator(".card").waitFor({ state: "visible", timeout: 10_000 });
  const revealedAfter = Date.now() - started;
  await page.waitForTimeout(800);
  const words = await page.evaluate(() => {
    const text = (s) => [...document.querySelectorAll(s)].map((e) => e.textContent.trim()).join(" | ");
    return {
      console: text(".console"),
      labels: text(".world-words li, .origin-label"),
      card: text(".card"),
      legend: text(".legend"),
      footer: text(".data-label, .spike-label"),
    };
  });
  const mode = await page.evaluate(() => window.__spike.mode);
  return { context, page, foreign, errors, changedAfter, revealedAfter, words, mode };
}

for (const direction of DIRECTIONS) {
  console.log(`\n${direction}`);
  const moving = await play(direction);
  const still = await play(direction, { reducedMotion: "reduce" });
  const calm = await play(direction, { calm: true });

  if (moving.mode === "moving" && still.mode === "still" && calm.mode === "still")
    pass("draws moving by default, still with reduced motion and in calm mode");
  else fail(`modes were ${moving.mode}, ${still.mode}, ${calm.mode}`);

  if (moving.changedAfter < 10_000) pass(`first answer changed the world after ${moving.changedAfter} ms (typing included)`);
  else fail(`world changed only after ${moving.changedAfter} ms`);
  pass(`revelation card shown after ${moving.revealedAfter} ms (typing included)`);

  const card = moving.words.card;
  if (card.includes("Chefs and firefighters share 5 essential skills.")) pass("revelation sentence is in the DOM");
  else fail(`revelation sentence missing: ${card}`);
  const why = await moving.page.locator("#why").textContent();
  if (["Work fast to tight deadlines", "Stay calm under pressure", "Lead a small team", "Follow safety rules", "Look after equipment"].every((s) => why.includes(s)) && why.includes("Code counted"))
    pass("its evidence (the five shared skills and where they come from) is in the DOM, one step away");
  else fail(`evidence incomplete: ${why}`);
  if (card.includes("Not a job offer") && card.includes("Not known yet")) pass("the card says what is uncertain and that it is not a job offer");
  else fail("card lacks its uncertainty or its honesty line");
  if (moving.words.footer.includes("Made-up example data") && moving.words.footer.includes("Spike")) pass("made-up data and the spike are labelled on screen");
  else fail("labels missing");

  for (const [name, other] of [["reduced motion", still], ["calm mode", calm]]) {
    const same = Object.keys(moving.words).every((k) => moving.words[k] === other.words[k]);
    if (same) pass(`the words are identical with ${name}`);
    else
      fail(
        `words differ with ${name}: ${Object.keys(moving.words)
          .filter((k) => moving.words[k] !== other.words[k])
          .join(", ")}`,
      );
  }

  const page = moving.page;

  // Teal means selection, the kept path and the primary action only: before anything is kept,
  // the primary button is the only element (or pseudo-element) painted teal.
  const teal = await page.evaluate(() => {
    const hits = [];
    for (const el of document.querySelectorAll("body *")) {
      for (const pseudo of [null, "::before", "::after"]) {
        const s = getComputedStyle(el, pseudo);
        const paint = [s.color, s.backgroundColor, s.backgroundImage, s.borderTopColor, s.borderLeftColor, s.outlineColor, s.boxShadow].join(" ");
        if (paint.includes("69, 247, 212") && el.offsetParent !== null && s.display !== "none" && s.content !== "none")
          hits.push(`${el.className || el.tagName}${pseudo ?? ""}`);
      }
    }
    return [...new Set(hits)];
  });
  if (teal.length === 1 && teal[0].startsWith("primary")) pass("teal is spent only on the primary action");
  else fail(`teal also used on: ${teal.join(", ")}`);

  // Words stay readable through every change of mode: no label waits for an entry animation.
  const wordsShown = () =>
    page.evaluate(() =>
      [...document.querySelectorAll(".world-words li")].every(
        (li) => li.getAnimations().length === 0 && Number(getComputedStyle(li).opacity) >= 0.59,
      ),
    );
  await page.locator('[data-control="calm"]').click();
  await page.locator('[data-control="calm"]').click();
  await page.waitForTimeout(150);
  if (await wordsShown()) pass("every word stays shown after calm mode is turned on and off");
  else fail("words vanished after calm mode was turned off");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.waitForTimeout(150);
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.waitForTimeout(150);
  if (await wordsShown()) pass("every word stays shown after reduced motion is turned on and off");
  else fail("words vanished after reduced motion was turned off");

  // Pointing at a destination (here by keyboard focus) shows what it shares without pressing it;
  // only a click pins it (aria-pressed).
  const place = page.locator(".places [data-kind='dest'] .place-toggle").first();
  await place.focus();
  await page.waitForTimeout(150);
  const pointed = await place.evaluate((b) => ({
    id: b.dataset.place,
    pointing: window.__spike.pointing,
    pressed: b.getAttribute("aria-pressed"),
    caption: getComputedStyle(b.querySelector(".state")).clipPath,
  }));
  if (pointed.pointing === pointed.id && pointed.pressed === "false" && pointed.caption === "none")
    pass("focusing a destination shows how many skills it shares, without pressing it");
  else fail(`focusing did not show the destination's skills: ${JSON.stringify(pointed)}`);
  await place.click();
  const pinnedState = await place.getAttribute("aria-pressed");
  await place.click();
  const unpinnedState = await place.getAttribute("aria-pressed");
  if (pinnedState === "true" && unpinnedState === "false") pass("clicking a destination pins it (pressed) and clicking again unpins it");
  else fail(`pinning: pressed after click ${pinnedState}, after second click ${unpinnedState}`);
  await place.blur();

  // Keyboard: say a skill was done, keep the destination in view, undo.
  const toggle = page.locator('.skill-toggle[data-skill="calm"]');
  await toggle.focus();
  await page.keyboard.press("Enter");
  await page.waitForTimeout(150);
  if ((await page.locator('.skill-toggle[data-skill="calm"]').getAttribute("aria-pressed")) === "true")
    pass("a skill can be marked as done from the keyboard");
  else fail("skill toggle did not change");
  await page.locator(".keep").focus();
  await page.keyboard.press("Enter");
  await page.waitForTimeout(150);
  if ((await page.locator(".places [data-kind='revealed']").getAttribute("data-selected")) === "true" && (await page.locator(".undo").isVisible()))
    pass("the destination can be kept in view, with undo, from the keyboard");
  else fail("keep in view did not take");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(150);
  if (await page.locator(".keep").isVisible()) pass("undo works");
  else fail("undo did not restore");

  const pause = page.locator('[data-control="pause"]');
  await pause.click();
  if ((await pause.getAttribute("aria-pressed")) === "true" && (await pause.textContent()) === "Pause motion")
    pass("the pause control is visible and works (fixed label, pressed state)");
  else fail("pause control did not toggle");

  for (const run of [moving, still, calm]) {
    if (run.foreign.length) fail(`requests left 127.0.0.1: ${run.foreign.join(", ")}`);
    if (run.errors.length) fail(`page errors: ${run.errors.join(" / ")}`);
  }
  if (![moving, still, calm].some((r) => r.foreign.length)) pass("no request left 127.0.0.1");
  for (const run of [moving, still, calm]) await run.context.close();
}

// Every skill and destination stays reachable and reads as belonging to its own light.
const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 1280, height: 800 },
  { width: 1728, height: 1080 },
];

function layoutProblems(page) {
  return page.evaluate(() => {
    const W = window.innerWidth;
    const H = window.innerHeight;
    const layout = window.__spike.layout;
    const problems = layout ? [] : ["the page does not expose where its lights are"];
    for (const light of layout?.lights ?? [])
      if (light.x < 0 || light.x > W || light.y < 0 || light.y > H) problems.push(`${light.id}: light outside the window`);
    for (const li of document.querySelectorAll(".skills li, .places li")) {
      const id = li.dataset.node;
      const r = li.getBoundingClientRect();
      if (getComputedStyle(li).visibility === "hidden" || r.width === 0) {
        problems.push(`${id}: hidden`);
        continue;
      }
      if (r.left < 0 || r.top < 0 || r.right > W || r.bottom > H) problems.push(`${id}: outside the window`);
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      if (!hit || !li.contains(hit)) problems.push(`${id}: covered by ${hit?.className || hit?.tagName}`);
      const button = li.querySelector("button");
      button?.focus();
      if (!button || document.activeElement !== button) problems.push(`${id}: not focusable`);
      button?.blur();
      if (!layout) continue;
      const own = layout.lights.find((l) => l.id === id);
      if (!own) {
        problems.push(`${id}: no light`);
        continue;
      }
      // The label's anchor is its point nearest its own light (where its glyph sits): it must be
      // within 30 px of that light and nearer to it than to any other, unless a leader joins them.
      const ax = Math.min(Math.max(own.x, r.left), r.right);
      const ay = Math.min(Math.max(own.y, r.top), r.bottom);
      const mine = Math.hypot(ax - own.x, ay - own.y);
      const nearest = layout.lights
        .filter((l) => l.id !== id)
        .map((l) => ({ id: l.id, d: Math.hypot(ax - l.x, ay - l.y) }))
        .sort((a, b) => a.d - b.d)[0];
      if (!layout.leaders.includes(id) && (mine > 30 || (nearest && nearest.d <= mine)))
        problems.push(`${id}: anchor ${Math.round(mine)} px from its light, ${Math.round(nearest?.d ?? 0)} px from ${nearest?.id}, no leader`);
    }
    return problems;
  });
}

console.log("\nlayout: every skill and destination reachable and by its own light");
for (const direction of DIRECTIONS) {
  for (const viewport of VIEWPORTS) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/?d=${direction}`);
    await page.locator("#role-input").pressSequentially("chef", { delay: 30 });
    await page.keyboard.press("Enter");
    await page.waitForTimeout(2000);
    const grown = await layoutProblems(page);
    await page.locator(".card").waitFor({ state: "visible", timeout: 10_000 });
    await page.waitForTimeout(1200);
    const revealed = await layoutProblems(page);
    const where = `${direction} at ${viewport.width}x${viewport.height}`;
    if (grown.length === 0 && revealed.length === 0) pass(`${where}: after the answer and after the revelation`);
    else fail(`${where}: after the answer [${grown.join("; ")}], after the revelation [${revealed.join("; ")}]`);
    if (viewport.width === 1440) {
      // Pointing at a destination's light, not its name, shows what it shares.
      const light = await page.evaluate(() => window.__spike.layout?.lights.find((l) => l.id.startsWith("dest:")));
      if (light) {
        await page.mouse.move(light.x, light.y);
        await page.waitForTimeout(200);
        const pointing = await page.evaluate(() => window.__spike.pointing);
        if (`dest:${pointing}` === light.id) pass(`${direction}: pointing at an orange light shows what it shares`);
        else fail(`${direction}: pointing at the light of ${light.id} did nothing (pointing: ${pointing})`);
      } else fail(`${direction}: the page does not expose where its lights are`);
    }
    await context.close();
  }
}

// The chooser's ambient motion has a visible pause control (reduced motion stops it as well).
{
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${ORIGIN}/`);
  await page.waitForTimeout(400);
  const pause = page.locator('[data-control="pause"]');
  console.log("\nchooser motion");
  if ((await pause.count()) === 1 && (await pause.isVisible())) {
    await pause.click();
    const states = await page.evaluate(() => document.getAnimations().map((a) => a.playState));
    if (states.length > 0 && states.every((s) => s === "paused") && (await pause.getAttribute("aria-pressed")) === "true")
      pass("the chooser's motion pauses from a visible control");
    else fail(`the chooser's animations after pausing: ${states.join(", ")}`);
  } else fail("the chooser has no visible pause control");
  await context.close();
}

// The chooser and the busiest scene make no foreign request either.
{
  const context = await browser.newContext();
  const page = await context.newPage();
  const foreign = [];
  page.on("request", (r) => {
    if (!r.url().startsWith(`${ORIGIN}/`) && !r.url().startsWith("data:")) foreign.push(r.url());
  });
  await page.goto(`${ORIGIN}/`);
  await page.waitForTimeout(500);
  for (const d of DIRECTIONS) {
    await page.goto(`${ORIGIN}/?d=${d}&scene=busy`);
    await page.waitForTimeout(800);
  }
  console.log("\nchooser and busiest scenes");
  if (foreign.length) fail(`requests left 127.0.0.1: ${foreign.join(", ")}`);
  else pass("no request left 127.0.0.1");
  await context.close();
}

await browser.close();
console.log(failures.length ? `\n${failures.length} failed` : "\nall passed");
process.exit(failures.length ? 1 : 0);
