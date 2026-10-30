// Screenshots for session W1's package, at 1440 by 900, from the running preview (`pnpm preview`).
// Writes to docs/reviews/session-w1/: the chooser; for each direction the question, the
// revelation, and the same moment drawn still (calm mode); and a sheet of the three display faces.
import { mkdirSync } from "node:fs";
import { chromium } from "playwright";

const ORIGIN = "http://127.0.0.1:53300";
const OUT = new URL("../../../docs/reviews/session-w1/", import.meta.url);
mkdirSync(OUT, { recursive: true });
const file = (name) => new URL(name, OUT).pathname;

const browser = await chromium.launch({ channel: "chrome", headless: true });
const viewport = { width: 1440, height: 900 };

{
  const page = await browser.newPage({ viewport });
  await page.goto(`${ORIGIN}/`);
  await page.waitForTimeout(600);
  await page.screenshot({ path: file("0-chooser.png") });
  await page.close();
}

async function revealed(page, url) {
  await page.goto(url);
  await page.waitForTimeout(900);
  await page.locator("#role-input").pressSequentially("chef", { delay: 40 });
  await page.keyboard.press("Enter");
  await page.locator(".card").waitFor({ state: "visible" });
  await page.waitForTimeout(1600);
}

for (const [n, d] of [
  [1, "growth"],
  [2, "horizon"],
  [3, "circuit"],
]) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  await page.goto(`${ORIGIN}/?d=${d}`);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: file(`${n}-${d}-a-question.png`) });
  await revealed(page, `${ORIGIN}/?d=${d}`);
  await page.screenshot({ path: file(`${n}-${d}-b-revelation.png`) });
  await revealed(page, `${ORIGIN}/?d=${d}&calm=1`);
  await page.screenshot({ path: file(`${n}-${d}-c-still.png`) });
  await context.close();
}

// The three display faces, on the same words.
const crops = {};
for (const font of ["outfit", "sora", "unbounded"]) {
  const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto(`${ORIGIN}/?d=growth&font=${font}`);
  await page.waitForTimeout(700);
  const q = await page.locator(".question").boundingBox();
  const question = await page.screenshot({ clip: { x: q.x - 12, y: q.y - 12, width: Math.min(620, q.width + 24), height: q.height + 24 } });
  await page.locator("#role-input").pressSequentially("customer", { delay: 30 });
  await page.keyboard.press("Enter");
  await page.locator(".card").waitFor({ state: "visible" });
  await page.waitForTimeout(400);
  const c = await page.locator(".card").boundingBox();
  const card = await page.screenshot({ clip: { x: c.x - 2, y: c.y - 2, width: c.width + 4, height: 230 } });
  crops[font] = { question: question.toString("base64"), card: card.toString("base64") };
  await context.close();
}
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 400 } });
  const column = (font, name, note) => `
    <section><h2>${name}</h2><p>${note}</p>
    <img src="data:image/png;base64,${crops[font].question}" style="max-width:100%;display:block;margin-bottom:12px">
    <img src="data:image/png;base64,${crops[font].card}" width="344"></section>`;
  await page.setContent(`<!doctype html><html><body style="margin:0;background:#03050b;color:#c2cce2;font:15px system-ui">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;padding:24px">
    ${column("outfit", "Outfit", "Suggested, and used in all three looks. Closest to the reference image; the narrowest, so long job names wrap least.")}
    ${column("sora", "Sora", "Wider and more technical. Long names take an extra line.")}
    ${column("unbounded", "Unbounded", "Most like a game title. Needs a smaller size and still wraps most.")}
    </div></body></html>`);
  await page.waitForTimeout(300);
  await page.screenshot({ path: file("4-typefaces.png"), fullPage: true });
}

await browser.close();
console.log(`Wrote screenshots to ${OUT.pathname}`);
