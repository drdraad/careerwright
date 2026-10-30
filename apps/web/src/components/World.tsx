"use client";
// The one persistent world behind every chapter (plan section 4, ADR 0014). It is drawn by
// WebGL2 when it may move, and as still SVG under reduced motion, calm mode, while the calm
// support panel shows, without WebGL2, or once the moving world has failed (its context lost or
// its renderer unable to start); both draw the same scene. Each chapter is a place: changing
// chapter is travel, the world stays and the view moves (a cut when still). Every light it
// draws has its words in the DOM beside it (`Your world`), so the canvas holds nothing unique;
// the key to the lights lists only what is drawn.
import { useEffect, useMemo, useRef, useState } from "react";
import type { ChapterId } from "@/lib/chapters";
import type { WorldMeasurement } from "@/lib/world/frames";
import { FrameMeter } from "@/lib/world/frames";
import {
  type Births,
  buildScene,
  type Clear,
  clearArea,
  isPhone,
  placeView,
  project,
  type Rect,
  sameView,
  type View,
  type Viewport,
  ViewTween,
} from "@/lib/world/geometry";
import { type FrameState, GLWorld, webgl2Available } from "@/lib/world/gl";
import { type Box, layoutLabels } from "@/lib/world/labels";
import { EMPTY_WORLD, type WorldInput } from "@/lib/world/model";
import { MOTION, now, TYPING_HOLD_SECONDS } from "@/lib/world/motion";
import type { Scene, Vec3 } from "@/lib/world/scene";
import { useReducedMotion } from "@/lib/world/settings";
import type { Sound } from "@/lib/world/sound";
import { StillWorld } from "./StillWorld";

export type WorldMode = "moving" | "still";

export type MeasureOptions = {
  warmupSeconds: number;
  seconds: number;
  /** Replays the ignition every this many seconds, so the sample covers staged light too. */
  igniteEverySeconds: number;
  onResult(result: WorldMeasurement): void;
};

type Props = {
  place: ChapterId;
  /** What the API computed; null while it loads (the world waits, dark, with the person's light). */
  input: WorldInput | null;
  calm: boolean;
  paused: boolean;
  /** The calm support panel is showing: the world is still while it does. */
  distress?: boolean;
  sound?: Sound;
  /** Measurement only (the busiest-scene story): samples frame costs and reports them. */
  measure?: MeasureOptions;
};

const SETTLED = -1e6;

/** The window's size, measured again when it resizes or moves to a display of another density. */
function useViewport(): Viewport | null {
  const [vp, setVp] = useState<Viewport | null>(null);
  useEffect(() => {
    const measure = () => setVp({ w: window.innerWidth, h: window.innerHeight });
    measure();
    window.addEventListener("resize", measure);
    let density: MediaQueryList | null = null;
    const watchDensity = () => {
      density?.removeEventListener("change", changed);
      density = window.matchMedia?.(`(resolution: ${window.devicePixelRatio}dppx)`) ?? null;
      density?.addEventListener("change", changed);
    };
    const changed = () => {
      measure();
      watchDensity();
    };
    watchDensity();
    return () => {
      window.removeEventListener("resize", measure);
      density?.removeEventListener("change", changed);
    };
  }, []);
  return vp;
}

/**
 * When each item first appeared during this visit, so that only what changes now grows or
 * ignites; whatever was there on arrival is drawn settled.
 */
function useBirths(input: WorldInput | null, onIgnite: () => void): Births {
  const memory = useRef<{ seen: Set<string> | null; lit: boolean; births: Births }>({
    seen: null,
    lit: false,
    births: { ignite: SETTLED, appeared: new Map() },
  });
  const [births, setBirths] = useState<Births>(memory.current.births);
  const ignite = useRef(onIgnite);
  ignite.current = onIgnite;
  useEffect(() => {
    // What arrives with the first load was there before this visit: it is drawn settled.
    if (input === null) return;
    const m = memory.current;
    const ids = [
      ...input.destinations.map((d) => `destination:${d.id}`),
      ...input.skills.map((s) => `skill:${s.id}`),
    ];
    if (m.seen === null) {
      m.seen = new Set(ids);
      m.lit = input.lit;
      return;
    }
    const t = now();
    const appeared = new Map(m.births.appeared);
    let changed = false;
    for (const id of ids) {
      if (m.seen.has(id)) continue;
      m.seen.add(id);
      appeared.set(id, t);
      changed = true;
    }
    let igniteAt = m.births.ignite;
    if (input.lit && !m.lit) {
      igniteAt = t;
      changed = true;
      ignite.current();
    }
    m.lit = input.lit;
    if (changed) {
      m.births = { ignite: igniteAt, appeared };
      setBirths(m.births);
    }
  }, [input]);
  return births;
}

type Label = {
  id: string;
  anchor: Vec3;
  side: "above" | "below";
  name: string;
  /** Plain words for what the light is and what its state means. */
  caption: string;
};

function labelsFor(scene: Scene, input: WorldInput): Label[] {
  const labels: Label[] = [];
  const origin = scene.nodes.find((n) => n.kind === "origin");
  if (origin) {
    labels.push({
      id: "origin",
      anchor: origin.p,
      side: "below",
      name: "You",
      caption: input.lit
        ? "Your light, lit by your answers"
        : "Your light comes on with your first answer",
    });
  }
  for (const destination of input.destinations) {
    const node = scene.nodes.find((n) => n.id === `destination:${destination.id}`);
    if (!node) continue;
    labels.push({
      id: node.id,
      anchor: node.p,
      side: "above",
      name: destination.title,
      caption: "A place you chose to head for. The ground between is not known yet.",
    });
  }
  return labels;
}

/** Where a person reads: the chapter's panel and the evidence drawer. */
const PANELS = "[data-world-panel]";
/** Everything over the world: the rail, the bars along the top, and the panels. */
const COVERS = "[data-covers-world]";
/** Wider than this, the key to the lights is open; narrower, it is "What the lights mean". */
const KEY_OPEN_FROM = 1100;

const rectOf = (element: Element): Rect => {
  const r = element.getBoundingClientRect();
  return { x: r.left, y: r.top, w: r.width, h: r.height };
};
const shown = (r: Rect) => r.w > 0 && r.h > 0;

/** The part of the window the place can stand in, measured from the bars and panels over it. */
function measureClear(vp: Viewport): Clear | undefined {
  const bars = [...document.querySelectorAll(`${COVERS}:not(${PANELS})`)].map(rectOf).filter(shown);
  const panels = [...document.querySelectorAll(PANELS)].map(rectOf).filter(shown);
  return clearArea(vp, bars, panels);
}

const sameClear = (a: Clear | undefined, b: Clear | undefined) =>
  a?.left === b?.left && a?.right === b?.right && a?.top === b?.top && a?.bottom === b?.bottom;

/** A name further than this from its light (CSS pixels) gets a leader line, stopping short of it. */
const LEADER_FROM = 20;
const LEADER_CLEAR = 8;
/** The key keeps this far from the window's edge and from a panel below it. */
const KEY_MARGIN = { wide: 24, narrow: 16, abovePanel: 12 };

const meets = (a: Box, b: Box) =>
  a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

/**
 * Places the key to the lights, then each light's words beside it, clear of the panels over the
 * world, the key, the other lights and each other. Words that cannot be placed, or whose light is
 * out of view or under a panel, are hidden from sight but stay in the list for assistive tech.
 * Every size is read before anything is written, so placing never forces a layout per name.
 */
function placeLabels(
  host: HTMLElement,
  key: HTMLElement | null,
  labels: readonly Label[],
  view: View,
  vp: Viewport,
): void {
  // Read.
  const covers: Box[] = [...document.querySelectorAll(COVERS)].map(rectOf).filter(shown);
  const elements = new Map<string, HTMLElement>();
  for (const element of host.querySelectorAll<HTMLElement>("[data-label]")) {
    elements.set(element.dataset.label ?? "", element);
  }
  const requests = labels.flatMap((label) => {
    const element = elements.get(label.id);
    if (element === undefined) return [];
    const size = { w: element.offsetWidth, h: element.offsetHeight };
    return [{ id: label.id, at: project(label.anchor, view), size, side: label.side }];
  });
  const keySize = key === null ? null : { w: key.offsetWidth, h: key.offsetHeight };

  // The key: bottom right, or else just above a panel at the right, clear of every light.
  let keySpot: Box | null = null;
  if (key !== null && keySize !== null && keySize.w > 0) {
    const margin = vp.w > KEY_OPEN_FROM ? KEY_MARGIN.wide : KEY_MARGIN.narrow;
    const bottoms = [
      vp.h - margin,
      ...covers.filter((c) => c.y > 1).map((c) => c.y - KEY_MARGIN.abovePanel),
    ].sort((a, b) => b - a);
    const centres = requests
      .filter((r) => r.at.visible)
      .map((r) => ({ x: r.at.x - 4, y: r.at.y - 4, w: 8, h: 8 }));
    keySpot =
      bottoms
        .map((bottom) => ({
          x: vp.w - margin - keySize.w,
          y: bottom - keySize.h,
          w: keySize.w,
          h: keySize.h,
        }))
        .find(
          (b) => b.y >= 4 && !covers.some((c) => meets(b, c)) && !centres.some((c) => meets(b, c)),
        ) ?? null;
  }
  const spots = layoutLabels(requests, covers, vp, keySpot === null ? [] : [keySpot]);

  // Write.
  if (key !== null) {
    // Unplaced, it is hidden from sight and from assistive tech (the names carry the words).
    key.dataset.placed = String(keySpot !== null);
    if (keySpot !== null) {
      key.style.right = `${Math.round(vp.w - keySpot.x - keySpot.w)}px`;
      key.style.bottom = `${Math.round(vp.h - keySpot.y - keySpot.h)}px`;
    }
  }
  for (const { id, at } of requests) {
    const element = elements.get(id);
    const spot = spots.get(id) ?? null;
    if (element === undefined) continue;
    element.dataset.shown = String(spot !== null);
    if (spot === null) continue;
    element.style.transform = `translate(${Math.round(spot.x)}px, ${Math.round(spot.y)}px)`;
    // A name a row out from its light keeps a fine leader line back to it.
    const above = spot.y + spot.h <= at.y;
    const gap = above ? at.y - (spot.y + spot.h) : spot.y - at.y;
    element.dataset.leader = gap > LEADER_FROM ? (above ? "above" : "below") : "none";
    element.style.setProperty("--leader", `${Math.round(gap - LEADER_CLEAR)}px`);
    element.style.setProperty("--leader-x", `${Math.round(at.x - spot.x)}px`);
  }
}

type Loop = {
  gl: GLWorld | null;
  tween: ViewTween;
  /** The frame passed to the renderer, reused every frame. */
  frame: FrameState;
  ambient: number;
  live: number;
  last: number;
  running: boolean;
  paused: boolean;
  lit: boolean;
  ignite: number;
  typedAt: number;
  reading: boolean;
  settle: boolean;
  /** The view the names were last placed for (copied, never the tween's own). */
  placedFor: View | null;
  birthsUntil: number;
};

export function World({
  place,
  input: loaded,
  calm,
  paused,
  distress = false,
  sound,
  measure,
}: Props) {
  const reduced = useReducedMotion();
  const vp = useViewport();
  const [capable, setCapable] = useState<boolean | null>(null);
  useEffect(() => setCapable(webgl2Available()), []);
  // The moving world failed: its context was lost or its renderer could not start. The still
  // world takes over for the rest of the visit, with the same names.
  const [failed, setFailed] = useState(false);
  const still = reduced || calm || distress || failed || capable !== true;
  const mode: WorldMode = still ? "still" : "moving";

  const births = useBirths(loaded, () => sound?.play("swell"));
  const input = loaded ?? EMPTY_WORLD;
  const scene = useMemo(
    () => (vp === null ? null : buildScene(input, vp, births)),
    [input, vp, births],
  );
  const labels = useMemo(() => (scene === null ? [] : labelsFor(scene, input)), [scene, input]);

  const canvas = useRef<HTMLCanvasElement>(null);
  const words = useRef<HTMLDivElement>(null);
  const keyRef = useRef<HTMLDetailsElement>(null);
  const [live, setLive] = useState<"running" | "still">("still");
  // Where the bars and panels leave the world in view; measured after each layout change.
  const [clear, setClear] = useState<Clear | undefined>(undefined);
  const loop = useRef<Loop | null>(null);
  if (loop.current === null && vp !== null) {
    const start = placeView(place, vp);
    loop.current = {
      gl: null,
      tween: new ViewTween(start, MOTION.travel),
      frame: { index: 0, time: 0, ambient: 0, live: 1, lit: false, ignite: SETTLED, view: start },
      ambient: 0,
      live: 1,
      last: now(),
      running: false,
      paused,
      lit: input.lit,
      ignite: births.ignite,
      typedAt: SETTLED,
      reading: false,
      settle: true,
      placedFor: null,
      birthsUntil: SETTLED,
    };
  }

  const wake = useRef<() => void>(() => {});
  const size = useRef(vp);
  size.current = vp;
  const drawn = useRef(scene);
  drawn.current = scene;
  const ready = vp !== null;

  // The moving world's renderer exists only while the world may move; resizes and scenes are
  // applied to it by the effects below. A lost context or a renderer that cannot start falls
  // back to the still world, never to a black world or a broken shell.
  useEffect(() => {
    const l = loop.current;
    const at = size.current;
    const element = canvas.current;
    if (still || !ready || element === null || l === null || at === null) return;
    let gl: GLWorld;
    try {
      gl = new GLWorld(element);
    } catch {
      setFailed(true);
      return;
    }
    const lost = (event: Event) => {
      event.preventDefault();
      setFailed(true);
    };
    element.addEventListener("webglcontextlost", lost);
    gl.resize(at);
    if (drawn.current !== null) gl.setScene(drawn.current);
    l.gl = gl;
    l.settle = true;
    l.placedFor = null;
    wake.current();
    return () => {
      element.removeEventListener("webglcontextlost", lost);
      l.gl = null;
      gl.dispose();
    };
  }, [still, ready]);

  useEffect(() => {
    const l = loop.current;
    if (l?.gl && vp) l.gl.resize(vp);
  }, [vp]);

  useEffect(() => {
    const l = loop.current;
    if (l === null || scene === null) return;
    l.gl?.setScene(scene);
    l.lit = input.lit;
    l.ignite = births.ignite;
    const newest = Math.max(births.ignite, ...births.appeared.values(), SETTLED);
    l.birthsUntil = newest + 3;
    l.settle = true;
    wake.current();
  }, [scene, input.lit, births]);

  // Travel: the view moves to the chapter's place, or cuts there when the world is still.
  useEffect(() => {
    const l = loop.current;
    if (l === null || vp === null) return;
    l.tween.aim(placeView(place, vp, clear), now(), still);
    l.settle = true;
    wake.current();
  }, [place, vp, still, clear]);

  useEffect(() => {
    const l = loop.current;
    if (l === null) return;
    l.paused = paused;
    wake.current();
  }, [paused]);

  // Ambient motion holds still while the person types, or reads the chapter's panel or the
  // evidence drawer (plan section 4); pointing at the strip or its controls is not reading.
  // When a typing hold ends the world wakes again by itself.
  useEffect(() => {
    let holdEnds = 0;
    const typed = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, [contenteditable='true']") && loop.current) {
        loop.current.typedAt = now();
        wake.current();
        window.clearTimeout(holdEnds);
        holdEnds = window.setTimeout(() => wake.current(), TYPING_HOLD_SECONDS * 1000 + 50);
      }
    };
    const pointed = (event: PointerEvent) => {
      const l = loop.current;
      if (!l) return;
      const reading = (event.target as HTMLElement | null)?.closest(PANELS) != null;
      if (reading !== l.reading) {
        l.reading = reading;
        wake.current();
      }
    };
    const visible = () => {
      if (!document.hidden) wake.current();
    };
    document.addEventListener("keydown", typed, true);
    document.addEventListener("pointerover", pointed, true);
    document.addEventListener("visibilitychange", visible);
    return () => {
      window.clearTimeout(holdEnds);
      document.removeEventListener("keydown", typed, true);
      document.removeEventListener("pointerover", pointed, true);
      document.removeEventListener("visibilitychange", visible);
    };
  }, []);

  // The frame loop. It runs while anything moves and stops when the world is at rest, paused
  // or hidden; measurement keeps it running for the whole sample.
  useEffect(() => {
    const l = loop.current;
    if (l === null || vp === null || still || scene === null) return;
    let meter: FrameMeter | null = null;
    let gpuTimed = false;
    let firstFrame: number | null = null;
    let nextIgnite = SETTLED;
    let raf = 0;
    let reported: "running" | "still" | null = null;
    if (measure && l.gl) {
      gpuTimed = l.gl.measureGpu();
      meter = new FrameMeter(measure.warmupSeconds, measure.seconds, () => l.gl?.takeGpuSamples());
      nextIgnite = now() + measure.igniteEverySeconds;
    }
    const animating = (t: number) =>
      l.tween.moving(t) || t < l.birthsUntil || t < l.ignite + MOTION.ignite + 1.5;
    const frame = (stamp: number) => {
      const gl = l.gl;
      if (gl === null || document.hidden) {
        l.running = false;
        return;
      }
      const started = performance.now();
      const t = now();
      const dt = Math.min(0.1, t - l.last);
      l.last = t;
      if (measure && t > nextIgnite) {
        l.ignite = t;
        nextIgnite = t + measure.igniteEverySeconds;
      }
      const hold = l.paused || l.reading || t - l.typedAt < TYPING_HOLD_SECONDS;
      const target = hold ? 0 : 1;
      l.live += (target - l.live) * Math.min(1, dt * (target > l.live ? 1.5 : 5));
      if (l.live < 0.002) l.live = 0;
      l.ambient += dt * l.live;
      const view = l.tween.current(t);
      const f = l.frame;
      f.index += 1;
      f.time = t;
      f.ambient = l.ambient;
      f.live = l.live;
      f.lit = l.lit;
      f.ignite = l.ignite;
      f.view = view;
      gl.render(f);
      firstFrame ??= performance.now();
      if ((l.placedFor === null || !sameView(view, l.placedFor) || l.settle) && words.current) {
        placeLabels(words.current, keyRef.current, labels, view, vp);
        l.placedFor = { ...view };
        l.settle = false;
      }
      const state = l.live > 0 ? "running" : "still";
      if (state !== reported) {
        reported = state;
        setLive(state);
      }
      if (meter) {
        meter.record(f.index, stamp, performance.now() - started);
        if (meter.done && measure) {
          const result = meter.result(gpuTimed ? gl.takeGpuSamples() : null);
          const measurement: WorldMeasurement = {
            renderer: gl.rendererName(),
            devicePixelRatio: window.devicePixelRatio,
            canvas: gl.canvasSize(),
            firstFrame,
            ...result,
          };
          meter = null;
          measure.onResult(measurement);
        }
      }
      if (meter || l.live > 0 || animating(t)) raf = requestAnimationFrame(frame);
      else l.running = false;
    };
    wake.current = () => {
      if (l.running || l.gl === null || document.hidden) return;
      l.running = true;
      l.last = now();
      raf = requestAnimationFrame(frame);
    };
    wake.current();
    return () => {
      cancelAnimationFrame(raf);
      l.running = false;
      wake.current = () => {};
    };
  }, [vp, still, scene, labels, measure]);

  // Still: words are placed once per change; nothing runs between changes.
  useEffect(() => {
    if (!still || vp === null || words.current === null) return;
    placeLabels(words.current, keyRef.current, labels, placeView(place, vp, clear), vp);
  }, [still, vp, labels, place, clear]);

  // The bars and panels over the world change as chapters load, grow and scroll, and the names
  // change size when the display face arrives: the place moves into the part they leave clear,
  // and the words move clear of them, at most once a frame.
  useEffect(() => {
    if (vp === null) return;
    let queued = 0;
    const replace = () => {
      if (queued !== 0) return;
      queued = requestAnimationFrame(() => {
        queued = 0;
        const area = measureClear(vp);
        setClear((current) => (sameClear(current, area) ? current : area));
        const l = loop.current;
        if (still && words.current) {
          placeLabels(words.current, keyRef.current, labels, placeView(place, vp, area), vp);
        } else if (l) {
          l.settle = true;
          wake.current();
        }
      });
    };
    replace();
    const changes = new MutationObserver(replace);
    changes.observe(document.body, { childList: true, subtree: true, characterData: true });
    window.addEventListener("scroll", replace, { passive: true, capture: true });
    const fonts = document.fonts;
    fonts?.addEventListener?.("loadingdone", replace);
    void fonts?.ready.then(replace);
    return () => {
      cancelAnimationFrame(queued);
      changes.disconnect();
      window.removeEventListener("scroll", replace, { capture: true });
      fonts?.removeEventListener?.("loadingdone", replace);
    };
  }, [still, vp, labels, place]);

  const legend = {
    destinations: input.destinations.length > 0,
    shadow: input.destinations.length > 0,
  };
  const view = vp === null ? null : placeView(place, vp, clear);
  const keyOpen = vp !== null && vp.w > KEY_OPEN_FROM;

  return (
    <>
      <div
        className="world"
        data-world-mode={vp === null ? "loading" : mode}
        data-place={place}
        data-motion={still ? "still" : live}
        data-distress={distress ? "true" : "false"}
        data-phone={vp !== null && isPhone(vp) ? "true" : "false"}
      >
        {!still && (
          <div className="world-layer" aria-hidden="true">
            <canvas ref={canvas} data-testid="moving-world" />
          </div>
        )}
        {still && scene !== null && view !== null && vp !== null && (
          <div className="world-layer">
            <StillWorld scene={scene} view={view} vp={vp} />
          </div>
        )}
        <aside className="world-words on-space" aria-label="Your world" ref={words}>
          <ul>
            {labels.map((label) => (
              <li
                key={label.id}
                className="world-label"
                data-label={label.id}
                data-shown="false"
                data-kind={label.id === "origin" ? "origin" : "destination"}
              >
                <span className="world-label-name">{label.name}</span>
                <span className="sr-only">: {label.caption}</span>
              </li>
            ))}
          </ul>
        </aside>
      </div>
      {(legend.destinations || legend.shadow) && (
        <details className="world-key on-reading" ref={keyRef} open={keyOpen} data-placed="false">
          <summary>What the lights mean</summary>
          <ul aria-label="What the lights mean">
            {legend.destinations && (
              <li>
                <span className="world-key-mark" data-key="destination" aria-hidden="true" />
                Warm lights: places you chose to head for
              </li>
            )}
            {legend.shadow && (
              <li>
                <span className="world-key-mark" data-key="shadow" aria-hidden="true" />
                Grey trails: not known yet
              </li>
            )}
          </ul>
        </details>
      )}
    </>
  );
}
