import "@fontsource-variable/outfit";
import "@fontsource-variable/sora";
import "@fontsource-variable/unbounded";
import "@fontsource-variable/atkinson-hyperlegible-next";
import "@fontsource-variable/jetbrains-mono";
import "./styles.css";
import { runDirection } from "./app.ts";
import type { Direction } from "./direction.ts";
import { circuit } from "./directions/circuit.ts";
import { growth } from "./directions/growth.ts";
import { horizon } from "./directions/horizon.ts";

const DIRECTIONS: readonly Direction[] = [growth, horizon, circuit];

// Small drawings of each direction for the chooser (decoration; the words say what each is).
const EMBLEMS: Record<Direction["id"], string> = {
  growth: `<svg viewBox="0 0 120 80" aria-hidden="true"><g fill="none" stroke-linecap="round">
    <path d="M60 74 C56 56 34 50 18 30" stroke="#408cff" stroke-width="2"/>
    <path d="M60 74 C62 52 58 34 52 10" stroke="#6b7cff" stroke-width="2"/>
    <path d="M60 74 C70 56 88 48 104 24" stroke="#9e6bff" stroke-width="2"/>
    <path d="M40 48 C34 46 30 42 26 44" stroke="#408cff" stroke-width="1" opacity=".6"/>
    <path d="M78 52 C84 50 86 44 92 44" stroke="#9e6bff" stroke-width="1" opacity=".6"/></g>
    <circle cx="60" cy="74" r="4" fill="#edf5ff"/><circle cx="18" cy="30" r="3" fill="#ff9433"/>
    <circle cx="52" cy="10" r="3" fill="#ff9433"/><circle cx="104" cy="24" r="3" fill="#ff9433"/></svg>`,
  horizon: `<svg viewBox="0 0 120 80" aria-hidden="true"><g fill="none">
    <path d="M0 30 H120" stroke="#2a3f75" stroke-width="1"/>
    <path d="M60 30 L10 80 M60 30 L40 80 M60 30 L80 80 M60 30 L110 80 M18 50 H102 M4 64 H116" stroke="#1d2b52" stroke-width=".8"/>
    <path d="M30 72 C50 62 70 44 96 32" stroke="#408cff" stroke-width="2"/>
    <path d="M30 72 C44 60 52 42 46 32" stroke="#9e6bff" stroke-width="1.6"/></g>
    <circle cx="30" cy="72" r="4" fill="#edf5ff"/><circle cx="96" cy="31" r="3" fill="#ff9433"/>
    <circle cx="46" cy="31" r="2.6" fill="#ff9433"/><rect x="95" y="34" width="2" height="9" fill="#ff9433" opacity=".35"/></svg>`,
  circuit: `<svg viewBox="0 0 120 80" aria-hidden="true"><g fill="none" stroke-linejoin="round">
    <path d="M14 40 H34 V18 H58" stroke="#408cff" stroke-width="2"/>
    <path d="M14 40 H40 V40 H58" stroke="#6b7cff" stroke-width="2"/>
    <path d="M14 40 H34 V62 H58" stroke="#408cff" stroke-width="2"/>
    <path d="M62 18 H82 V30 H100" stroke="#9e6bff" stroke-width="1.6"/>
    <path d="M62 62 H84 V30 H100" stroke="#9e6bff" stroke-width="1.6"/>
    <rect x="58" y="14" width="8" height="8" rx="2" stroke="#408cff"/><rect x="58" y="36" width="8" height="8" rx="2" stroke="#408cff"/>
    <rect x="58" y="58" width="8" height="8" rx="2" stroke="#408cff"/>
    <path d="M96 22 h-4 v4 M108 22 h4 v4 M96 38 h-4 v-4 M108 38 h4 v-4" stroke="#45f7d4" stroke-width="1.4"/></g>
    <circle cx="14" cy="40" r="4" fill="#edf5ff"/><rect x="97" y="27" width="6" height="6" transform="rotate(45 100 30)" fill="#ff9433"/></svg>`,
};

function chooser(root: HTMLElement): void {
  document.body.classList.add("chooser-page");
  root.innerHTML = `
  <main class="chooser">
    <p class="wordmark">Careerwright</p>
    <h1>Three ways the world could feel.</h1>
    <p class="lede">Each one asks the same question and shows the same discovery. Try each for two minutes, then say which you would choose, or which mix.</p>
    <ul class="doors">
      ${DIRECTIONS.map(
        (d) => `<li><a class="door" href="?d=${d.id}">${EMBLEMS[d.id]}<span class="door-name">${d.name}</span><span class="door-blurb">${d.blurb}</span></a></li>`,
      ).join("")}
    </ul>
    <p class="spike-label">Spike: a throwaway preview for choosing a look. It is not the app, and everything in it is made up.</p>
  </main>`;
}

const root = document.getElementById("app");
if (!root) throw new Error("Missing #app");
const requested = new URLSearchParams(location.search).get("d");
const direction = DIRECTIONS.find((d) => d.id === requested);
if (direction) runDirection(root, direction, DIRECTIONS);
else chooser(root);
