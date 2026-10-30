import "@fontsource-variable/outfit";
import "@fontsource-variable/sora";
import "@fontsource-variable/unbounded";
import "@fontsource-variable/atkinson-hyperlegible-next";
import "@fontsource-variable/jetbrains-mono";
import "./styles.css";
import { runDirection } from "./app.ts";
import { DEFAULT_FONT, type Direction } from "./direction.ts";
import { circuit } from "./directions/circuit.ts";
import { growth } from "./directions/growth.ts";
import { horizon } from "./directions/horizon.ts";

const DIRECTIONS: readonly Direction[] = [growth, horizon, circuit];

/**
 * The chooser is already a world: the person's light below, and a trail rising from it to each
 * of the three looks, drawn in that look's own way. Pointing at a look lights its trail.
 */
function chooser(root: HTMLElement): void {
  document.body.classList.add("chooser-page");
  document.documentElement.dataset.font = DEFAULT_FONT;
  // Static markup from the spike's own constants.
  root.innerHTML = `
  <svg class="chooser-world" aria-hidden="true"></svg>
  <main class="chooser">
    <p class="wordmark">Careerwright</p>
    <h1>Three ways the world could feel.</h1>
    <p class="lede">Each asks the same question and finds the same thing. Try each for two minutes, then choose one, or a mix.</p>
    <ul class="doors">
      ${DIRECTIONS.map(
        (d) => `<li><a class="door" data-door="${d.id}" href="?d=${d.id}"><span class="door-light" aria-hidden="true"></span><span class="door-name">${d.name}</span><span class="door-blurb">${d.blurb}</span></a></li>`,
      ).join("")}
    </ul>
    <p class="spike-label">Spike: a throwaway preview for choosing a look. It is not the app, and everything in it is made up.</p>
  </main>`;
  const svg = root.querySelector("svg.chooser-world") as SVGSVGElement;
  const draw = () => {
    const w = window.innerWidth;
    const h = Math.max(window.innerHeight, document.documentElement.scrollHeight);
    const ox = w / 2;
    const oy = Math.min(h - 70, window.innerHeight * 0.9);
    const trails: string[] = [];
    for (const door of root.querySelectorAll<HTMLElement>(".door")) {
      const light = door.querySelector(".door-light") as HTMLElement;
      const r = light.getBoundingClientRect();
      const x = r.left + r.width / 2 + window.scrollX;
      const y = r.top + r.height / 2 + window.scrollY;
      const id = door.dataset.door;
      let path: string;
      let mark: string;
      if (id === "growth") {
        path = `M${ox} ${oy} C${ox - 40} ${oy - 140}, ${x + 80} ${y + 160}, ${x} ${y}`;
        // Root hairs branching off near the end of the trail.
        const bx = x + (ox - x) * 0.18;
        const by = y + (oy - y) * 0.22;
        mark = `<path d="M${bx} ${by} q-30 4 -46 -14 M${bx + 14} ${by + 26} q26 -2 40 -22" class="fibre"/>
          <circle cx="${x}" cy="${y}" r="7" class="core"/>`;
      } else if (id === "horizon") {
        path = `M${ox} ${oy} L${x} ${y}`;
        mark = `<line x1="${x - 110}" y1="${y}" x2="${x + 110}" y2="${y}" class="horizon"/>
          <rect x="${x - 2}" y="${y + 9}" width="4" height="34" class="reflection"/>
          <circle cx="${x}" cy="${y}" r="7" class="core"/>`;
      } else {
        // A circuit route: straight up, a 45° run, straight across, straight up into the core.
        const sx = Math.sign(x - ox) || 1;
        const rise = Math.max(0, oy - 40 - (y + 30));
        const diag = Math.min(rise, Math.abs(x - ox));
        const y1 = oy - 40 - (rise - diag);
        path = `M${ox} ${oy} V${y1} L${ox + sx * diag} ${y + 30} H${x} V${y}`;
        mark = `<path d="M${x - 20} ${y - 12} h-6 v6 M${x + 20} ${y - 12} h6 v6 M${x - 20} ${y + 12} h-6 v-6 M${x + 20} ${y + 12} h6 v-6" class="brackets"/>
          <rect x="${x - 7}" y="${y - 7}" width="14" height="14" rx="2" class="core"/>`;
      }
      trails.push(`<g class="trail" data-trail="${id}">
        <path d="${path}" class="glow"/><path d="${path}" class="line"/><path d="${path}" class="flow"/>${mark}</g>`);
    }
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("width", String(w));
    svg.setAttribute("height", String(h));
    svg.innerHTML = `
      <defs>
        <linearGradient id="ch-trail" gradientUnits="userSpaceOnUse" x1="0" y1="${oy}" x2="0" y2="0">
          <stop offset="0" stop-color="#408cff"/><stop offset="1" stop-color="#9e6bff"/>
        </linearGradient>
        <radialGradient id="ch-you" cx="${ox}" cy="${oy}" r="160" gradientUnits="userSpaceOnUse">
          <stop offset="0" stop-color="#9cc4ff" stop-opacity="0.55"/><stop offset="1" stop-color="#9cc4ff" stop-opacity="0"/>
        </radialGradient>
        <filter id="ch-soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>
      </defs>
      ${trails.join("")}
      <circle cx="${ox}" cy="${oy}" r="160" fill="url(#ch-you)" class="you-glow"/>
      <circle cx="${ox}" cy="${oy}" r="8" fill="#edf5ff"/>`;
  };
  const light = (id: string | undefined, on: boolean) =>
    svg.querySelector(`[data-trail="${id}"]`)?.classList.toggle("lit", on);
  for (const door of root.querySelectorAll<HTMLElement>(".door")) {
    for (const [type, on] of [
      ["pointerenter", true],
      ["pointerleave", false],
      ["focus", true],
      ["blur", false],
    ] as const)
      door.addEventListener(type, () => light(door.dataset.door, on));
  }
  window.addEventListener("resize", draw);
  void document.fonts.ready.then(draw);
  draw();
}

const root = document.getElementById("app");
if (!root) throw new Error("Missing #app");
const requested = new URLSearchParams(location.search).get("d");
const direction = DIRECTIONS.find((d) => d.id === requested);
if (direction) runDirection(root, direction, DIRECTIONS);
else chooser(root);
