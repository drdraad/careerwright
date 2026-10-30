// The spike's own acceptance check, against the running preview (`pnpm preview` or `make spike-world`).
// For each direction it plays the first ten seconds and checks, in a real browser:
// - the first answer changes the world within ten seconds and the revelation's sentence and
//   evidence are in the DOM;
// - the words are the same moving, with the system's reduced-motion setting, and in calm mode;
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

  // Keyboard: say a skill was done, keep the destination in view, undo.
  const page = moving.page;
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
  if ((await pause.textContent()) === "Play motion") pass("the pause control is visible and works");
  else fail("pause control did not toggle");

  for (const run of [moving, still, calm]) {
    if (run.foreign.length) fail(`requests left 127.0.0.1: ${run.foreign.join(", ")}`);
    if (run.errors.length) fail(`page errors: ${run.errors.join(" / ")}`);
  }
  if (![moving, still, calm].some((r) => r.foreign.length)) pass("no request left 127.0.0.1");
  for (const run of [moving, still, calm]) await run.context.close();
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
