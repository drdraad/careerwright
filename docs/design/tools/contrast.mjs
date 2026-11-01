// Measures WCAG 2.2 contrast for every pair in tokens/contrast-pairs.json, resolving the
// colours from the :root block of tokens/tokens.css, and writes tokens/contrast-report.md.
// A glass background (#RRGGBBAA) is composited over each backdrop the pair names in `over`
// (the world's darkest ground and its brightest light), and every composite is measured. A
// foreground drawn translucent (a trail at its declared strength) names that strength in
// `alpha`, a number or an opacity token, and is composited over the background before it is
// measured: the colour as drawn, not the token at full strength.
// Exits 1 if any pair is below its threshold or a token cannot be resolved.
//   pnpm --dir docs/design run contrast
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const css = readFileSync(join(root, "tokens/tokens.css"), "utf8");
const config = JSON.parse(readFileSync(join(root, "tokens/contrast-pairs.json"), "utf8"));
const THRESHOLD = { text: 4.5, "non-text": 3.0 };

function rootDeclarations(source) {
  const block = source.match(/:root\s*\{([\s\S]*?)\n\}/);
  if (!block) throw new Error("tokens.css has no :root block");
  const declarations = new Map();
  for (const [, name, value] of block[1].matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    declarations.set(name, value.trim());
  }
  return declarations;
}

/** A token's colour as { hex: "#RRGGBB", alpha: 0–1 }. */
function resolve(name, declarations, seen = new Set()) {
  if (seen.has(name)) throw new Error(`circular token reference at ${name}`);
  seen.add(name);
  const value = declarations.get(name);
  if (value === undefined) throw new Error(`token ${name} is not defined in :root`);
  const reference = value.match(/^var\((--[a-z0-9-]+)\)$/);
  if (reference) return resolve(reference[1], declarations, seen);
  const colour = value.match(/^#([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?$/);
  if (!colour) throw new Error(`token ${name} is not a #RRGGBB or #RRGGBBAA colour: ${value}`);
  return { hex: `#${colour[1].toUpperCase()}`, alpha: colour[2] ? parseInt(colour[2], 16) / 255 : 1 };
}

/** A pair's `alpha`: a number, or an opacity token such as --trail-opacity-shadow. */
function strength(alpha, declarations) {
  if (alpha === undefined) return 1;
  const value = typeof alpha === "number" ? alpha : Number(declarations.get(alpha));
  if (!(value > 0 && value <= 1)) throw new Error(`alpha ${alpha} is not an opacity between 0 and 1`);
  return value;
}

function opaque(name, declarations) {
  const colour = resolve(name, declarations);
  if (colour.alpha !== 1) throw new Error(`token ${name} must be opaque here`);
  return colour.hex;
}

function channels(hex) {
  return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
}

/** Source-over compositing in sRGB, as browsers blend, rounded to 8 bits. */
function composite(top, alpha, bottom) {
  const mixed = channels(top).map((c, i) => Math.round((c * alpha + channels(bottom)[i] * (1 - alpha)) * 255));
  return `#${mixed.map((c) => c.toString(16).padStart(2, "0")).join("").toUpperCase()}`;
}

// WCAG 2.x relative luminance (sRGB). 0.04045 is the IEC sRGB threshold; WCAG notes the
// older 0.03928 makes no difference at 8-bit precision.
function luminance(hex) {
  const [r, g, b] = channels(hex).map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

function lab(hex) {
  const lin = channels(hex).map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  const [r, g, b] = lin;
  const xyz = [
    (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047,
    0.2126 * r + 0.7152 * g + 0.0722 * b,
    (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883,
  ].map((t) => (t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116));
  return [116 * xyz[1] - 16, 500 * (xyz[0] - xyz[1]), 200 * (xyz[1] - xyz[2])];
}

function deltaE76(a, b) {
  const [la, lb] = [lab(a), lab(b)];
  return Math.hypot(la[0] - lb[0], la[1] - lb[1], la[2] - lb[2]);
}

// Floor to two decimals so a ratio of 4.496 is never displayed as a passing 4.50.
const floor2 = (x) => (Math.floor(x * 100) / 100).toFixed(2);

const declarations = rootDeclarations(css);
const rows = [];
let measured = 0;
let failures = 0;
for (const pair of config.pairs) {
  const required = THRESHOLD[pair.kind];
  if (required === undefined) throw new Error(`unknown kind ${pair.kind}`);
  const fg = opaque(pair.fg, declarations);
  const alpha = strength(pair.alpha, declarations);
  const bg = resolve(pair.bg, declarations);
  if (bg.alpha < 1 && !pair.over?.length) throw new Error(`${pair.bg} is translucent: name its backdrops in "over"`);
  if (bg.alpha === 1 && pair.over?.length) throw new Error(`${pair.bg} is opaque: "over" means nothing for it`);
  const backdrops = bg.alpha < 1 ? pair.over : [null];
  for (const backdrop of backdrops) {
    const seen = backdrop === null ? bg.hex : composite(bg.hex, bg.alpha, opaque(backdrop, declarations));
    const drawn = alpha < 1 ? composite(fg, alpha, seen) : fg;
    const ratio = contrast(drawn, seen);
    const pass = ratio >= required;
    measured += 1;
    if (!pass) failures += 1;
    const background = backdrop === null
      ? `\`${pair.bg}\` ${bg.hex}`
      : `\`${pair.bg}\` ${bg.hex} at ${Math.round(bg.alpha * 100)}% over \`${backdrop}\` = ${seen}`;
    const foreground = alpha < 1
      ? `\`${pair.fg}\` ${fg} at ${Math.round(alpha * 100)}%${typeof pair.alpha === "string" ? ` (\`${pair.alpha}\`)` : ""} = ${drawn}`
      : `\`${pair.fg}\` ${fg}`;
    rows.push(`| ${foreground} | ${background} | ${pair.use} | ${floor2(ratio)}:1 | ${required.toFixed(1)}:1 | ${pass ? "pass" : "**FAIL**"} |`);
  }
}

const distinct = [];
for (const status of config.distinctness.status) {
  for (const meaning of config.distinctness.meaning) {
    const d = deltaE76(opaque(status, declarations), opaque(meaning, declarations));
    distinct.push({ status, meaning, d });
  }
}
distinct.sort((a, b) => a.d - b.d);

// The decision hues (accept, undo) against every hue that already says something: the status
// and meaning hues, and each other.
const decisions = config.distinctness.decision ?? [];
const decided = [];
for (const [i, decision] of decisions.entries()) {
  for (const other of [...config.distinctness.status, ...config.distinctness.meaning, ...decisions.slice(i + 1)]) {
    decided.push({ decision, other, d: deltaE76(opaque(decision, declarations), opaque(other, declarations)) });
  }
}
decided.sort((a, b) => a.d - b.d);

const report = [
  "# Contrast report",
  "",
  "Generated by `docs/design/tools/contrast.mjs` from `tokens.css` and `contrast-pairs.json`. Do not edit by hand; re-run `pnpm --dir docs/design run contrast` after any token change.",
  "",
  "Method: WCAG 2.2 relative luminance and contrast ratio, (L1 + 0.05) / (L2 + 0.05), on sRGB colours. A glass background is composited over each backdrop its pair names (source-over, 8-bit), and each composite is a row: the world's darkest ground and the brightest light anything in it reaches, white. A foreground the world draws translucent (a trail at its declared strength) is composited over that background first, so the ratio is the colour as drawn. One recorded exception: while the calm support panel shows, the world is a dimmed, still backdrop and its trails may fall below 3:1 (every name and state stays in the list beside it); nothing else is exempt. Ratios are floored to two decimals. Thresholds: 4.5:1 for text (SC 1.4.3), 3:1 for non-text components, focus indicators and meaningful graphics (SC 1.4.11).",
  "",
  `Result: **${measured - failures} of ${measured} measurements pass** (${config.pairs.length} pairs)${failures ? `; ${failures} fail` : ""}.`,
  "",
  "| Foreground | Background | Used for | Ratio | Required | Result |",
  "|---|---|---|---:|---:|---|",
  ...rows,
  "",
  "## Status hues versus the world's meaning hues (informational)",
  "",
  "CIE76 ΔE between each status hue and each hue that carries a meaning in the world (destination orange, sea-glass, the journey's blue and violet), smallest first. Status is always carried by a glyph and words as well; this shows no status borrows a meaning's hue.",
  "",
  "| Status token | Meaning token | ΔE76 |",
  "|---|---|---:|",
  ...distinct.map((x) => `| \`${x.status}\` | \`${x.meaning}\` | ${x.d.toFixed(1)} |`),
  "",
  ...(decided.length === 0
    ? []
    : [
        "## Decision hues versus every other hue (informational)",
        "",
        "CIE76 ΔE between each decision hue (accepting a proposed change, undoing a save) and each status and meaning hue, and each other, smallest first. Each decision is carried by its words and glyph as well.",
        "",
        "| Decision token | Other token | ΔE76 |",
        "|---|---|---:|",
        ...decided.map((x) => `| \`${x.decision}\` | \`${x.other}\` | ${x.d.toFixed(1)} |`),
        "",
      ]),
];
writeFileSync(join(root, "tokens/contrast-report.md"), report.join("\n"));
console.log(`${measured - failures}/${measured} measurements pass (${config.pairs.length} pairs); smallest status/meaning ΔE76 ${distinct[0].d.toFixed(1)} (${distinct[0].status} vs ${distinct[0].meaning})${decided.length ? `; smallest decision ΔE76 ${decided[0].d.toFixed(1)} (${decided[0].decision} vs ${decided[0].other})` : ""}`);
for (const row of rows.filter((r) => r.includes("FAIL"))) console.log(row);
process.exit(failures ? 1 : 0);
