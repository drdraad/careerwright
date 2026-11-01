// One direction, running: the exact DOM layer (every word and control) over the world layer
// (WebGL when moving, SVG when still). The words are the same in every direction and mode.
// One idea at a time: what just changed speaks; everything else stays quiet until the person
// points at it or focuses it.
import { DATA_LABEL, ROLES, type Role, skillLabel } from "./data.ts";
import {
  type Camera,
  DEFAULT_FONT,
  type Direction,
  type FontId,
  ViewTween,
  type Viewport,
  buildScene,
} from "./direction.ts";
import { sampleFrames, summarise } from "./frames.ts";
import { GLWorld, webgl2Available } from "./gl.ts";
import { connectionSentence, matchRoles } from "./model.ts";
import type { Scene, SceneNode } from "./scene.ts";
import { Sound } from "./sound.ts";
import { drawStill } from "./still.ts";
import { Story, TIMING, now } from "./story.ts";

export const FONTS: Record<FontId, string> = {
  outfit: "Outfit",
  sora: "Sora",
  unbounded: "Unbounded",
};

type SpikeProbe = {
  direction: string;
  mode: "moving" | "still";
  renderer: string;
  firstFrame: number | null;
  /** Milliseconds from an input's handler (a keystroke or a skill picked) to the end of the frame that answers it. */
  inputToFrame: number[];
  stats: unknown;
  /** Where the lights are on screen and which labels have leader lines (for tools/check.mjs). */
  layout: { lights: { id: string; x: number; y: number }[]; leaders: string[] } | null;
  /** The destination the person is pointing at or has focused, if any. */
  pointing: string | null;
};

declare global {
  interface Window {
    __spike: SpikeProbe;
  }
}

const params = new URLSearchParams(location.search);

const lowerFirst = (s: string): string => (/^[A-Z]{2}/.test(s) ? s : s.charAt(0).toLowerCase() + s.slice(1));

const STATE_WORDS = {
  usual: "usual in your role, not confirmed yet",
  said: "you said you've done this",
} as const;

function el<K extends keyof HTMLElementTagNameMap>(tag: K, className?: string, text?: string): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// Static markup from the spike's own constants; nothing the person types is ever put into HTML.
const SKELETON = (d: Direction, all: readonly Direction[]) => `
<canvas class="world" aria-hidden="true"></canvas>
<div class="still-world" aria-hidden="true"></div>
<svg class="leaders" aria-hidden="true"></svg>
<header class="top">
  <a class="wordmark" href="./">Careerwright</a>
  <nav class="directions" aria-label="Looks to try">
    ${all.map((x) => `<a href="?d=${x.id}"${x.id === d.id ? ' aria-current="page"' : ""}>${x.name}</a>`).join("")}
  </nav>
  <div class="controls">
    <button type="button" class="control" data-control="pause" aria-pressed="false">Pause motion</button>
    <button type="button" class="control" data-control="calm" aria-pressed="false">Calm mode</button>
    <button type="button" class="control" data-control="sound" aria-pressed="false">Sound</button>
  </div>
</header>
<main class="stage">
  <section class="console" aria-labelledby="question">
    <h1 id="question" class="question">What do you do now, or what did you do last?</h1>
    <div class="ask">
      <div class="combo">
        <input id="role-input" class="role-input" type="text" role="combobox" aria-expanded="false"
          aria-controls="role-options" aria-autocomplete="list" autocomplete="off" spellcheck="false"
          aria-labelledby="question" aria-describedby="ask-hint" placeholder="Start typing a job title">
      </div>
      <ul id="role-options" class="options" role="listbox" aria-label="Matching jobs" hidden></ul>
      <p id="ask-hint" class="hint">Try chef, care worker or electrician.</p>
    </div>
    <div class="answered" hidden>
      <p class="you-role"></p>
      <p class="answer-line"></p>
      <p class="prompt">Pick any you've used, and it lights up.</p>
      <button type="button" class="quiet start-again">Start again</button>
    </div>
  </section>
  <ul class="legend" aria-label="What the lights mean">
    <li data-legend="usual"><span class="glyph glyph-usual" aria-hidden="true"></span>Faint ring: usual in your role, not confirmed yet</li>
    <li data-legend="said" hidden><span class="glyph glyph-said" aria-hidden="true"></span>Bright: you said you've done it</li>
    <li data-legend="shadow" hidden><span class="glyph glyph-shadow" aria-hidden="true"></span>Dashed: not known yet</li>
  </ul>
  <section class="world-words" aria-label="Your world">
    <p class="node-label origin-label" data-node="origin" data-shown="1">You</p>
    <ul class="skills" aria-label="Skills your job usually needs"></ul>
    <ul class="places" aria-label="Places you could head for"></ul>
    <ul class="unknowns" aria-label="Not known yet"></ul>
  </section>
  <aside class="card" aria-labelledby="card-title" hidden>
    <h2 id="card-title" class="card-kicker">An unexpected connection</h2>
    <p class="card-sentence"></p>
    <p class="card-reason"></p>
    <p class="card-unknown"></p>
    <p class="card-honest">A place you could head for. Not a job offer.</p>
    <button type="button" class="quiet why-toggle" aria-expanded="false" aria-controls="why">Why?</button>
    <div id="why" class="why" hidden>
      <p>Both jobs list these as essential:</p>
      <ul class="why-list"></ul>
      <p class="why-unknown"></p>
      <p class="why-source">Where this comes from: the made-up example list in this preview. Code counted the skills both jobs list. Nothing was guessed.</p>
    </div>
    <div class="card-actions">
      <button type="button" class="primary keep"></button>
      <button type="button" class="undo" hidden>Undo</button>
    </div>
  </aside>
  <p class="status" role="status" aria-live="polite"></p>
</main>
<footer class="bottom">
  <p class="data-label">${DATA_LABEL}</p>
  <div class="spike">
    <p class="spike-label">Spike: a throwaway preview for choosing a look. Not the app.</p>
    <details class="spike-tools">
      <summary>Spike tools</summary>
      <fieldset class="font-choice">
        <legend>Heading typeface</legend>
        ${Object.entries(FONTS)
          .map(
            ([id, name]) =>
              `<label><input type="radio" name="font" value="${id}"${id === DEFAULT_FONT ? " checked" : ""}> ${name}</label>`,
          )
          .join("")}
      </fieldset>
      <button type="button" class="quiet busy-toggle" aria-pressed="false">Busiest scene: 100 made-up openings</button>
      <p class="mode-note"></p>
    </details>
  </div>
</footer>
<pre class="measure-readout" hidden></pre>
`;

export function runDirection(root: HTMLElement, direction: Direction, all: readonly Direction[]): void {
  document.body.classList.add(`dir-${direction.id}`);
  root.innerHTML = SKELETON(direction, all);
  const $ = <T extends Element>(selector: string): T => {
    const found = root.querySelector<T>(selector);
    if (!found) throw new Error(`Missing ${selector}`);
    return found;
  };

  const story = new Story();
  const sound = new Sound(direction.id);
  const canvas = $<HTMLCanvasElement>("canvas.world");
  const stillHost = $<HTMLDivElement>(".still-world");
  const leaders = $<SVGSVGElement>("svg.leaders");
  const input = $<HTMLInputElement>(".role-input");
  const options = $<HTMLUListElement>(".options");
  const status = $<HTMLParagraphElement>(".status");
  const card = $<HTMLElement>(".card");
  const keep = $<HTMLButtonElement>(".keep");
  const undo = $<HTMLButtonElement>(".undo");
  const whyToggle = $<HTMLButtonElement>(".why-toggle");
  const why = $<HTMLDivElement>(".why");
  const pauseButton = $<HTMLButtonElement>('[data-control="pause"]');
  const calmButton = $<HTMLButtonElement>('[data-control="calm"]');
  const soundButton = $<HTMLButtonElement>('[data-control="sound"]');
  const busyButton = $<HTMLButtonElement>(".busy-toggle");
  const modeNote = $<HTMLParagraphElement>(".mode-note");
  const readout = $<HTMLPreElement>(".measure-readout");
  const lists = {
    skills: $<HTMLUListElement>(".skills"),
    places: $<HTMLUListElement>(".places"),
    unknowns: $<HTMLUListElement>(".unknowns"),
  };
  const originLabel = $<HTMLParagraphElement>(".origin-label");

  const measuring = params.get("measure") === "1";
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const hasGL = webgl2Available();
  let calm = params.get("calm") === "1";
  let paused = false;
  let gl: GLWorld | null = null;
  let still = true;
  let scene: Scene = { nodes: [], trails: [] };
  let vp = viewport();
  const tween = new ViewTween(direction.view(vp, story));
  let ambient = 0;
  let live = 1;
  let lastFrame = 0;
  let running = false;
  let lastTyped = -1e6;
  let keystroke = -1e6;
  let inputAt = -1e6;
  let answeredInput = -1e6;
  let scriptSamples: number[] = [];
  let reading = false;
  let lastCamera: Camera | null = null;
  let settleNeeded = true;
  let leadersShown = false;
  let revealTimer = 0;
  let cardTimer = 0;
  let activeOption = -1;
  let matches: Role[] = [];
  /** A destination the person clicked to keep its shared skills showing (touch has no hover). */
  let pinned: string | null = null;
  window.__spike = {
    direction: direction.id,
    mode: "moving",
    renderer: "",
    firstFrame: null,
    inputToFrame: [],
    stats: null,
    layout: null,
    pointing: null,
  };

  setFont((params.get("font") as FontId | null) ?? DEFAULT_FONT);

  function viewport(): Viewport {
    return { w: window.innerWidth, h: window.innerHeight, narrow: window.innerWidth < 760 };
  }

  function setFont(font: FontId): void {
    if (!(font in FONTS)) return;
    document.documentElement.dataset.font = font;
    document.documentElement.style.setProperty("--font-display", `"${FONTS[font]} Variable", system-ui, sans-serif`);
    const radio = root.querySelector<HTMLInputElement>(`input[name="font"][value="${font}"]`);
    if (radio) radio.checked = true;
  }

  // ---- Moving or still -------------------------------------------------------------------

  function shouldBeStill(): boolean {
    return reducedMotion.matches || calm || !hasGL;
  }

  function applyMode(): void {
    still = shouldBeStill();
    document.body.classList.toggle("is-still", still);
    window.__spike.mode = still ? "still" : "moving";
    calmButton.setAttribute("aria-pressed", String(calm || reducedMotion.matches));
    calmButton.disabled = reducedMotion.matches;
    calmButton.title = reducedMotion.matches ? "Your computer asks for less motion, so the world is drawn still." : "";
    pauseButton.disabled = still;
    pauseButton.setAttribute("aria-pressed", String(paused || still));
    pauseButton.title = still ? "Motion is already off." : "";
    modeNote.textContent = !hasGL
      ? "This browser can't draw the moving world, so it is drawn still."
      : still
        ? "The world is drawn still: the same lights and words, without motion."
        : "";
    // Words never wait for an entry animation after a change of mode: whatever is in the world
    // is shown at once.
    for (const li of labelFor.values()) li.dataset.shown = "1";
    if (still) {
      gl?.dispose();
      gl = null;
      canvas.hidden = true;
      stillHost.hidden = false;
      tween.aim(direction.view(vp, story), now(), true);
      drawStillWorld();
      placeLabels(direction.view(vp, story), true);
    } else {
      stillHost.hidden = true;
      canvas.hidden = false;
      if (!gl) {
        gl = new GLWorld(canvas, direction);
        gl.resize(vp);
        gl.setScene(scene);
        window.__spike.renderer = gl.rendererName();
      }
      settleNeeded = true;
      lastCamera = null;
      wake();
    }
  }

  function drawStillWorld(): void {
    stillHost.innerHTML = drawStill(direction, vp, direction.view(vp, story), scene);
    if (window.__spike.firstFrame === null)
      requestAnimationFrame(() => {
        window.__spike.firstFrame ??= performance.now();
      });
  }

  // ---- Scene and labels -----------------------------------------------------------------

  /** Redraws the world for the story as it stands; words are re-placed unless only a pointer moved. */
  function rebuild(resettle = true): void {
    scene = buildScene(direction, vp, story);
    gl?.setScene(scene);
    syncLabels();
    updateLegend();
    tween.aim(direction.view(vp, story), now(), still);
    if (resettle) settleNeeded = true;
    if (still) {
      drawStillWorld();
      if (resettle) placeLabels(direction.view(vp, story), true);
    } else {
      if (resettle) {
        placeLabels(tween.current(now()));
        lastCamera = null;
      }
      wake();
    }
  }

  const labelFor = new Map<string, HTMLLIElement>();

  /** Creates a label once; later syncs update it in place, so focus and hover survive. */
  function ensureLabel(list: HTMLUListElement, node: SceneNode, create: () => HTMLElement[]): HTMLLIElement {
    let li = labelFor.get(node.id);
    if (!li) {
      li = el("li", "node-label");
      li.dataset.node = node.id;
      li.dataset.side = node.side;
      li.append(...create());
      const delay = node.birth - now();
      if (still || delay <= 0) li.dataset.shown = "1";
      else {
        // The entry animation plays once; after it, or after any change of mode, it never replays.
        li.style.setProperty("--delay", `${delay.toFixed(2)}s`);
        li.addEventListener(
          "animationend",
          () => {
            if (li) li.dataset.shown = "1";
          },
          { once: true },
        );
      }
      list.append(li);
      labelFor.set(node.id, li);
    }
    return li;
  }

  function syncLabels(): void {
    const seen = new Set<string>();
    const revealedPhase = story.phase === "revealed";
    const shared = new Set(story.connection?.shared ?? []);
    for (const node of scene.nodes) {
      const [kind, key] = node.id.split(":") as [string, string | undefined];
      if (!key) continue;
      if (kind === "skill") {
        const li = ensureLabel(lists.skills, node, () => {
          const button = el("button", "skill-toggle");
          button.type = "button";
          button.dataset.skill = key;
          button.append(el("span", "name", skillLabel(key)), el("span", "state"));
          return [button];
        });
        const said = node.state === "said";
        const button = li.querySelector("button");
        button?.setAttribute("aria-pressed", String(said));
        const state = li.querySelector(".state");
        if (state) state.textContent = STATE_WORDS[said ? "said" : "usual"];
        li.dataset.state = node.state;
        // After the revelation, only the skills the two jobs share keep speaking.
        li.dataset.voice = !revealedPhase || shared.has(key) ? "speak" : "quiet";
        seen.add(node.id);
      } else if (kind === "dest" || kind === "revealed") {
        const dest =
          kind === "dest" ? story.destinations.find((d) => d.role.id === key) : (story.connection ?? undefined);
        if (!dest) continue;
        const li = ensureLabel(lists.places, node, () => {
          const button = el("button", "place-toggle");
          button.type = "button";
          button.dataset.place = key;
          button.append(el("span", "name", dest.role.title), el("span", "state", `${dest.shared.length} shared skills`));
          return [button];
        });
        li.dataset.kind = kind;
        li.dataset.selected = String(node.selected);
        // Pressed means pinned by a click; pointing and focus only show, they do not press.
        li.querySelector("button")?.setAttribute("aria-pressed", String(pinned === key));
        li.dataset.voice = kind === "revealed" || story.focus === key ? "speak" : "quiet";
        if (kind === "revealed") li.dataset.caption = "1";
        seen.add(node.id);
      }
    }
    // The shadowed skills share one label, on the middle one; their names are behind Why?.
    const unknowns = scene.nodes.filter((n) => n.kind === "unknown");
    const middle = unknowns[Math.floor(unknowns.length / 2)];
    const found = story.connection;
    if (middle && found) {
      const li = ensureLabel(lists.unknowns, middle, () => [
        el("span", "name", "Not known yet"),
        el("span", "state", `${found.unknown.length} more skills ${lowerFirst(found.role.plural)} need`),
      ]);
      li.dataset.voice = "speak";
      li.dataset.caption = "1";
      seen.add(middle.id);
    }
    for (const [id, li] of labelFor) {
      if (!seen.has(id)) {
        li.remove();
        labelFor.delete(id);
      }
    }
  }

  /** Each legend line appears when its state first appears in the world. */
  function updateLegend(): void {
    const show = (name: string, on: boolean) => {
      const line = root.querySelector<HTMLLIElement>(`[data-legend="${name}"]`);
      if (line) line.hidden = !on;
    };
    show("usual", story.phase !== "ask");
    show("said", story.said.size > 0);
    show("shadow", story.phase === "revealed");
  }

  function placeLabels(cam: Camera, settle = false): void {
    const nodes = new Map(scene.nodes.map((n) => [n.id, n]));
    const place = (elm: HTMLElement, node: SceneNode | undefined) => {
      if (!node) return;
      const p = direction.project(node.p, cam, vp);
      const onScreen = p.visible && p.x > -40 && p.x < vp.w + 40 && p.y > -40 && p.y < vp.h + 40;
      elm.style.visibility = onScreen ? "" : "hidden";
      elm.style.transform = `translate3d(${p.x.toFixed(1)}px, ${p.y.toFixed(1)}px, 0)`;
      elm.style.setProperty("--r", `${Math.max(3, node.size * p.scale).toFixed(1)}px`);
    };
    const origin = nodes.get("origin");
    place(originLabel, origin);
    if (origin) {
      // The question sits by the person's light before the first answer.
      const p = direction.project(origin.p, cam, vp);
      root.style.setProperty("--ox", `${p.x.toFixed(1)}px`);
      root.style.setProperty("--oy", `${p.y.toFixed(1)}px`);
    }
    for (const [id, li] of labelFor) place(li, nodes.get(id));
    window.__spike.layout = {
      lights: scene.nodes
        .filter((n) => n.kind !== "opening")
        .map((n) => {
          const p = direction.project(n.p, cam, vp);
          return { id: n.id, x: p.x, y: p.y };
        }),
      leaders: settle ? [] : (window.__spike.layout?.leaders ?? []),
    };
    if (settle) settleLabels(cam, nodes);
    else if (leadersShown) {
      leaders.replaceChildren();
      leadersShown = false;
      window.__spike.layout.leaders = [];
    }
  }

  type Box = { x0: number; y0: number; x1: number; y1: number };
  const SIDES = ["right", "left", "above", "below", "above-right", "above-left", "below-right", "below-left"] as const;
  type Side = (typeof SIDES)[number];

  function boxFor(side: Side, x: number, y: number, w: number, h: number, gap: number): Box {
    const d = gap * 0.7;
    switch (side) {
      case "right":
        return { x0: x + gap, y0: y - h / 2, x1: x + gap + w, y1: y + h / 2 };
      case "left":
        return { x0: x - gap - w, y0: y - h / 2, x1: x - gap, y1: y + h / 2 };
      case "above":
        return { x0: x - w / 2, y0: y - gap - h, x1: x + w / 2, y1: y - gap };
      case "below":
        return { x0: x - w / 2, y0: y + gap, x1: x + w / 2, y1: y + gap + h };
      case "above-right":
        return { x0: x + d, y0: y - d - h, x1: x + d + w, y1: y - d };
      case "above-left":
        return { x0: x - d - w, y0: y - d - h, x1: x - d, y1: y - d };
      case "below-right":
        return { x0: x + d, y0: y + d, x1: x + d + w, y1: y + d + h };
      case "below-left":
        return { x0: x - d - w, y0: y + d, x1: x - d, y1: y + d + h };
    }
  }

  const REACHES = [1, 2.2, 3.6];
  const overlap = (a: Box, b: Box): number =>
    Math.max(0, Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0)) * Math.max(0, Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0));

  /**
   * Chooses each label's place so that words do not cover panels, lights or each other. A label
   * placed away from its light gets a fine leader line back to it, so no word floats free. Runs
   * only when the view is at rest; the label's preferred side wins ties.
   */
  function settleLabels(cam: Camera, nodes: Map<string, SceneNode>): void {
    const panels = [".console", ".card", ".legend", ".wordmark", ".directions", ".controls", ".data-label", ".spike"]
      .map((s) => root.querySelector<HTMLElement>(s))
      .filter((e): e is HTMLElement => !!e && e.offsetParent !== null && !e.hidden)
      .map((e) => {
        const r = e.getBoundingClientRect();
        return { x0: r.left - 6, y0: r.top - 6, x1: r.right + 6, y1: r.bottom + 6 };
      });
    const lights: { id: string; x: number; y: number; box: Box }[] = [];
    for (const n of scene.nodes) {
      if (n.kind === "opening") continue;
      const p = direction.project(n.p, cam, vp);
      const r = Math.max(3, n.size * p.scale) + 5;
      lights.push({ id: n.id, x: p.x, y: p.y, box: { x0: p.x - r, y0: p.y - r, x1: p.x + r, y1: p.y + r } });
    }
    /** Distance from a light's centre to the nearest point of a box (0 inside it). */
    const reachOf = (box: Box, x: number, y: number) =>
      Math.hypot(Math.max(box.x0 - x, 0, x - box.x1), Math.max(box.y0 - y, 0, y - box.y1));
    const order = [...labelFor.entries()].sort(([a], [b]) => rank(a) - rank(b));
    const placed: Box[] = [];
    const lines: string[] = [];
    const led: string[] = [];
    for (const [id, li] of order) {
      const node = nodes.get(id);
      if (!node) continue;
      const p = direction.project(node.p, cam, vp);
      const gap = Math.max(3, node.size * p.scale) + 8;
      const w = li.offsetWidth;
      const h = li.offsetHeight;
      let best: { box: Box; score: number; mine: number } | null = null;
      for (const reach of REACHES) {
        for (const side of [node.side, ...SIDES.filter((s) => s !== node.side)]) {
          const box = boxFor(side, p.x, p.y, w, h, gap * reach);
          const outside =
            Math.max(0, 8 - box.x0) +
            Math.max(0, box.x1 - (vp.w - 8)) +
            Math.max(0, 60 - box.y0) +
            Math.max(0, box.y1 - (vp.h - 8));
          let score = outside * h * 4 + (side === node.side ? 0 : 300) + (reach - 1) * 450;
          for (const b of panels) score += overlap(box, b) * 3;
          for (const b of placed) score += overlap(box, b) * 5;
          // A word must read as belonging to its own light. Its anchor (the point nearest its
          // light, where its glyph sits) must never be as near to another light.
          const mine = reachOf(box, p.x, p.y);
          const ax = Math.min(Math.max(p.x, box.x0), box.x1);
          const ay = Math.min(Math.max(p.y, box.y0), box.y1);
          for (const l of lights) {
            if (l.id === id) continue;
            score += overlap(box, l.box);
            if (Math.hypot(ax - l.x, ay - l.y) <= mine + 6) score += 4000;
          }
          if (!best || score < best.score) best = { box, score, mine };
        }
      }
      if (!best) continue;
      const { box } = best;
      // The label's own offset from its light; its text and glyph turn towards the light.
      li.style.translate = `${(box.x0 - p.x).toFixed(1)}px ${(box.y0 - p.y).toFixed(1)}px`;
      li.dataset.align = box.x1 <= p.x ? "end" : box.x0 >= p.x ? "start" : "centre";
      placed.push(box);
      // Any label not right beside its light gets a fine leader line back to it.
      if (best.mine > gap + 6 && li.style.visibility !== "hidden") {
        const tx = Math.min(Math.max(p.x, box.x0), box.x1);
        const ty = Math.min(Math.max(p.y, box.y0), box.y1);
        const len = Math.hypot(tx - p.x, ty - p.y) || 1;
        const sx = p.x + ((tx - p.x) / len) * (gap - 4);
        const sy = p.y + ((ty - p.y) / len) * (gap - 4);
        lines.push(`<line x1="${sx.toFixed(1)}" y1="${sy.toFixed(1)}" x2="${tx.toFixed(1)}" y2="${ty.toFixed(1)}"/>`);
        led.push(id);
      }
    }
    leaders.innerHTML = lines.join("");
    leadersShown = lines.length > 0;
    if (window.__spike.layout) window.__spike.layout.leaders = led;
  }

  const rank = (id: string): number =>
    id.startsWith("revealed") ? 0 : id.startsWith("dest") ? 1 : id.startsWith("skill") ? 2 : 3;

  // ---- The loop --------------------------------------------------------------------------

  function animating(t: number): boolean {
    return (
      t < keystroke + 1.2 ||
      t < story.igniteAt + 3 ||
      story.isRevealing(t) ||
      t < story.revealAt + TIMING.revealLength + 1 ||
      t < (story.kept ?? -1e6) + 2 ||
      t < story.focusAt + 0.6 ||
      [...story.said.values()].some((s) => t < s + 2) ||
      tween.moving(t)
    );
  }

  function wake(): void {
    if (running || still || !gl) return;
    running = true;
    lastFrame = now();
    requestAnimationFrame(frame);
  }

  function frame(): void {
    if (still || !gl) {
      running = false;
      return;
    }
    const started = performance.now();
    const t = now();
    const dt = Math.min(0.1, t - lastFrame);
    lastFrame = t;
    const typing = document.activeElement === input && t - lastTyped < 1.5;
    const hold = paused || typing || reading || story.isRevealing(t);
    const target = hold ? 0 : 1;
    live += (target - live) * Math.min(1, dt * (target > live ? 1.5 : 5));
    ambient += dt * live;
    const camera = tween.current(t);
    gl.render({
      time: t,
      ambient,
      live,
      phase: story.phase === "ask" ? 0 : story.phase === "grown" ? 1 : 2,
      ignite: story.igniteAt,
      reveal: story.revealAt,
      key: keystroke,
      typed: story.phase === "ask" ? input.value.length : 0,
      camera,
    });
    if (window.__spike.firstFrame === null) window.__spike.firstFrame = performance.now();
    if (inputAt > answeredInput) {
      window.__spike.inputToFrame.push(Math.round((now() - inputAt) * 10000) / 10);
      answeredInput = inputAt;
    }
    const moved = !lastCamera || camera.some((v, i) => v !== lastCamera?.[i]);
    const settle = settleNeeded && !tween.moving(t);
    if (moved || settle) {
      placeLabels(camera, settle);
      lastCamera = camera;
      if (settle) settleNeeded = false;
    }
    // Script time inside this frame callback (not style, layout, paint or compositing).
    if (measuring) scriptSamples.push(performance.now() - started);
    if (measuring || !paused || live > 0.002 || animating(t)) requestAnimationFrame(frame);
    else running = false;
  }

  // ---- Story events ----------------------------------------------------------------------

  function say(message: string): void {
    status.textContent = "";
    requestAnimationFrame(() => {
      status.textContent = message;
    });
  }

  /** The console becomes the person's side of the conversation: their answer, and its echo. */
  function showAnswered(role: Role): string {
    root.classList.add("is-answered");
    $<HTMLDivElement>(".ask").hidden = true;
    $<HTMLDivElement>(".answered").hidden = false;
    $<HTMLParagraphElement>(".you-role").textContent = role.title;
    const line = `${role.plural} usually need these ${role.skills.length} skills.`;
    $<HTMLParagraphElement>(".answer-line").textContent = line;
    return line;
  }

  function answer(role: Role): void {
    window.clearTimeout(revealTimer);
    window.clearTimeout(cardTimer);
    closeOptions();
    pinned = null;
    story.answer(role);
    card.hidden = true;
    sound.play("ignite");
    say(`Your light is on. ${showAnswered(role)}`);
    rebuild();
    if (story.connection) revealTimer = window.setTimeout(reveal, TIMING.revealDelay * 1000);
  }

  function reveal(): void {
    story.reveal();
    sound.play("reveal");
    fillCard();
    rebuild();
    const settle = still ? 0 : TIMING.revealLength * 0.85;
    cardTimer = window.setTimeout(showCard, settle * 1000);
  }

  function showCard(): void {
    window.clearTimeout(cardTimer);
    if (story.phase !== "revealed" || !card.hidden) return;
    card.hidden = false;
    settleNeeded = true;
    if (still) placeLabels(direction.view(vp, story), true);
    else wake();
    const role = story.role;
    const found = story.connection;
    if (role && found) say(`An unexpected connection. ${connectionSentence(role, found)}`);
  }

  function fillCard(): void {
    const role = story.role;
    const found = story.connection;
    if (!role || !found) return;
    $<HTMLParagraphElement>(".card-sentence").textContent = connectionSentence(role, found);
    $<HTMLParagraphElement>(".card-reason").textContent =
      `A field you didn't name (${lowerFirst(found.role.field)}), joined to yours by skills, not job titles.`;
    $<HTMLParagraphElement>(".card-unknown").textContent =
      found.unknown.length === 0
        ? `Nothing else ${lowerFirst(found.role.plural)} need is unknown in this list.`
        : `Not known yet: ${found.unknown.length} more skills ${lowerFirst(found.role.plural)} need.`;
    $<HTMLParagraphElement>(".why-unknown").textContent =
      found.unknown.length === 0
        ? ""
        : `Not known yet: ${found.unknown.map((s) => lowerFirst(skillLabel(s))).join(", ")}.`;
    const list = $<HTMLUListElement>(".why-list");
    list.replaceChildren(
      ...found.shared.map((s) => {
        const li = el("li");
        li.append(
          el("span", "name", skillLabel(s)),
          el("span", "state", story.said.has(s) ? "You said you've done this" : "Usual in your role, not confirmed yet"),
        );
        return li;
      }),
    );
    keep.textContent = `Keep ${lowerFirst(found.role.title)} in view`;
    keep.hidden = story.kept !== null;
    undo.hidden = story.kept === null;
  }

  function reset(): void {
    window.clearTimeout(revealTimer);
    window.clearTimeout(cardTimer);
    pinned = null;
    story.reset();
    root.classList.remove("is-answered");
    $<HTMLDivElement>(".ask").hidden = false;
    $<HTMLDivElement>(".answered").hidden = true;
    card.hidden = true;
    why.hidden = true;
    whyToggle.setAttribute("aria-expanded", "false");
    whyToggle.textContent = "Why?";
    busyButton.setAttribute("aria-pressed", "false");
    input.value = "";
    say("");
    rebuild();
    input.focus();
  }

  function point(destination: string | null): void {
    if (story.point(destination ?? pinned)) rebuild(false);
    window.__spike.pointing = story.focus;
  }

  /** A click on a destination's light or name pins its shared skills on (touch has no hover). */
  function pin(destination: string): void {
    pinned = pinned === destination ? null : destination;
    story.point(pinned ?? destination);
    window.__spike.pointing = story.focus;
    rebuild(false);
  }

  /** The destination whose light is under the pointer, if any: the lights live in the world layer. */
  function lightAt(x: number, y: number): { id: string; revealed: boolean } | null {
    if (story.phase === "ask") return null;
    const cam = still ? direction.view(vp, story) : tween.current(now());
    let best: { id: string; revealed: boolean } | null = null;
    let nearest = Number.POSITIVE_INFINITY;
    for (const n of scene.nodes) {
      if (n.kind !== "destination" && n.kind !== "revealed") continue;
      const p = direction.project(n.p, cam, vp);
      const d = Math.hypot(p.x - x, p.y - y);
      if (d <= Math.max(22, n.size * p.scale * 3) && d < nearest) {
        nearest = d;
        best = { id: n.id.split(":")[1] ?? "", revealed: n.kind === "revealed" };
      }
    }
    return best;
  }

  // ---- The question and its type-ahead ---------------------------------------------------

  function closeOptions(): void {
    options.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    activeOption = -1;
  }

  function renderOptions(): void {
    const q = input.value;
    matches = matchRoles(q, ROLES);
    options.replaceChildren();
    if (!q.trim()) return closeOptions();
    if (matches.length === 0) {
      const li = el("li", "no-match", "Nothing in the example list starts like that yet.");
      li.setAttribute("role", "option");
      li.setAttribute("aria-disabled", "true");
      li.id = "role-none";
      options.append(li);
    }
    matches.forEach((role, i) => {
      const li = el("li", "option", role.title);
      li.id = `role-${role.id}`;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", String(i === activeOption));
      li.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        answer(role);
      });
      options.append(li);
    });
    options.hidden = false;
    input.setAttribute("aria-expanded", "true");
    if (activeOption >= 0 && matches[activeOption])
      input.setAttribute("aria-activedescendant", `role-${matches[activeOption]?.id}`);
    else input.removeAttribute("aria-activedescendant");
  }

  input.addEventListener("input", () => {
    lastTyped = now();
    activeOption = matchRoles(input.value, ROLES).length > 0 ? 0 : -1;
    renderOptions();
    // Feedback within 100 ms: the person's light answers each keystroke.
    keystroke = now();
    inputAt = keystroke;
    wake();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (matches.length === 0) return;
      const step = event.key === "ArrowDown" ? 1 : -1;
      activeOption = (activeOption + step + matches.length) % matches.length;
      renderOptions();
    } else if (event.key === "Enter") {
      event.preventDefault();
      const chosen = matches[activeOption >= 0 ? activeOption : 0];
      if (chosen) answer(chosen);
      else if (input.value.trim())
        say(`Nothing in this example list matches "${input.value.trim()}". Try a shorter job title, like "chef" or "nurse".`);
    } else if (event.key === "Escape") {
      closeOptions();
    }
  });

  input.addEventListener("blur", () => window.setTimeout(closeOptions, 120));

  // ---- Controls ---------------------------------------------------------------------------

  root.addEventListener("click", (event) => {
    const target = event.target as HTMLElement;
    const skill = target.closest<HTMLButtonElement>(".skill-toggle");
    if (skill?.dataset.skill) {
      const id = skill.dataset.skill;
      story.toggleSaid(id);
      inputAt = now();
      sound.play("touch");
      say(story.said.has(id) ? `${skillLabel(id)}: you said you've done this.` : `${skillLabel(id)}: back to not confirmed yet.`);
      fillCard();
      rebuild();
      return;
    }
    if (target.closest(".start-again")) return reset();
    if (target.closest('[data-node^="revealed"]')) {
      if (card.hidden) showCard();
      keep.focus();
      return;
    }
    const place = target.closest<HTMLButtonElement>(".place-toggle");
    if (place?.dataset.place) pin(place.dataset.place);
  });

  // Pointing at a destination, its light or its name, or focusing its name, shows the skills it
  // shares; moving away hides them again (unless a click pinned them).
  const placeOf = (event: Event): string | null =>
    (event.target as HTMLElement).closest<HTMLElement>(".place-toggle")?.dataset.place ?? null;
  const inWorld = (target: EventTarget | null): boolean =>
    target === canvas || (target instanceof Node && stillHost.contains(target));
  window.addEventListener("pointermove", (event) => {
    const name = placeOf(event);
    const light = !name && inWorld(event.target) ? lightAt(event.clientX, event.clientY) : null;
    document.body.classList.toggle("over-light", light !== null);
    point(name ?? light?.id ?? null);
  });
  window.addEventListener("click", (event) => {
    if (!inWorld(event.target)) return;
    const light = lightAt(event.clientX, event.clientY);
    if (!light) return;
    if (light.revealed) {
      if (card.hidden) showCard();
      keep.focus();
    } else pin(light.id);
  });
  lists.places.addEventListener("focusin", (event) => point(placeOf(event)));
  lists.places.addEventListener("focusout", () => point(null));

  keep.addEventListener("click", () => {
    const found = story.connection;
    if (!found) return;
    story.keep();
    fillCard();
    rebuild();
    say(`${found.role.title} is in view. Its path is lit.`);
    undo.focus();
  });

  undo.addEventListener("click", () => {
    story.undoKeep();
    fillCard();
    rebuild();
    say("Undone. Nothing is kept in view.");
    keep.focus();
  });

  whyToggle.addEventListener("click", () => {
    const open = why.hidden;
    why.hidden = !open;
    whyToggle.setAttribute("aria-expanded", String(open));
    whyToggle.textContent = open ? "Hide why" : "Why?";
    // The card changed size: words in the world move out from under it.
    settleNeeded = true;
    if (still) placeLabels(direction.view(vp, story), true);
    else wake();
  });

  pauseButton.addEventListener("click", () => {
    paused = !paused;
    applyMode();
  });

  calmButton.addEventListener("click", () => {
    calm = !calm;
    applyMode();
  });

  soundButton.addEventListener("click", () => {
    sound.setEnabled(!sound.enabled);
    soundButton.setAttribute("aria-pressed", String(sound.enabled));
  });

  busyButton.addEventListener("click", () => {
    if (story.phase !== "revealed") {
      const chef = ROLES.find((r) => r.id === "chef") as Role;
      answer(chef);
      window.clearTimeout(revealTimer);
      story.reveal(now() - TIMING.revealLength);
      fillCard();
      showCard();
    }
    story.busy = !story.busy;
    busyButton.setAttribute("aria-pressed", String(story.busy));
    rebuild();
  });

  root.addEventListener("change", (event) => {
    const target = event.target as HTMLInputElement;
    if (target.name === "font") {
      setFont(target.value as FontId);
      settleNeeded = true;
      if (still) placeLabels(direction.view(vp, story), true);
      else wake();
    }
  });

  for (const panel of [card, $<HTMLElement>(".console")]) {
    panel.addEventListener("pointerenter", () => {
      reading = true;
    });
    panel.addEventListener("pointerleave", () => {
      reading = false;
    });
  }

  // Any input completes a revelation at once.
  const complete = () => {
    if (!story.isRevealing()) return;
    story.completeReveal();
    showCard();
    rebuild();
  };
  window.addEventListener("keydown", complete, true);
  window.addEventListener("pointerdown", complete, true);

  reducedMotion.addEventListener("change", applyMode);
  window.addEventListener("resize", () => {
    vp = viewport();
    gl?.resize(vp);
    rebuild();
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) wake();
  });

  // ---- Start --------------------------------------------------------------------------

  scene = buildScene(direction, vp, story);
  applyMode();
  rebuild();

  if (params.get("scene") === "busy") {
    const chef = ROLES.find((r) => r.id === "chef") as Role;
    story.preset(chef, { busy: true, kept: true });
    showAnswered(chef);
    busyButton.setAttribute("aria-pressed", "true");
    fillCard();
    showCard();
    rebuild();
  } else if (!measuring) {
    input.focus();
  }

  if (measuring) {
    // Replay the revelation's staging every 4 s so the sample covers revelation and travel too.
    window.setInterval(() => {
      story.replayReveal();
      rebuild();
    }, 4000);
    // applyMode() created the world above; TypeScript cannot see that through the closure.
    const world = gl as GLWorld | null;
    const gpuTimed = world?.measureGpu() ?? false;
    const warm = () => {
      scriptSamples = [];
      world?.takeGpuSamples();
    };
    void sampleFrames(3, 12, warm).then((frames) => {
      const gpu = world?.takeGpuSamples() ?? [];
      const stats = {
        frames,
        script: summarise(scriptSamples),
        gpu: gpuTimed && gpu.length > 0 ? summarise(gpu) : "not available",
      };
      window.__spike.stats = stats;
      readout.hidden = false;
      readout.textContent = JSON.stringify({ ...window.__spike, stats }, null, 2);
    });
  }
}
