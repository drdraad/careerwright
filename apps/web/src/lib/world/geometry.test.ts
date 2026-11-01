// Horizon's geometry keeps the truth rules (plan section 4; ADR 0014 decision 4): position is
// layout only, so every destination stands at one depth in title order; unknown ground is a
// shadow trail, never absent; and every place keeps the person's light in view.
import { describe, expect, it } from "vitest";
import { CHAPTERS } from "@/lib/chapters";
import {
  type Births,
  buildScene,
  clearArea,
  HORIZON_Z,
  placeView,
  project,
  type Rect,
  type Viewport,
  ViewTween,
} from "./geometry";
import type { WorldInput } from "./model";
import { MOTION } from "./motion";

const DESKTOP: Viewport = { w: 1440, h: 900 };
const TABLET: Viewport = { w: 768, h: 1024 };
const PHONE: Viewport = { w: 390, h: 844 };
const SETTLED: Births = { ignite: -1e6, appeared: new Map() };

const world = (overrides: Partial<WorldInput> = {}): WorldInput => ({
  lit: true,
  destinations: [
    { id: "a", title: "Archivist", shared: [] },
    { id: "d", title: "Data quality analyst", shared: [] },
    { id: "s", title: "Statistician", shared: [] },
  ],
  skills: [],
  openings: 0,
  ...overrides,
});

/** The rail down the left edge, and a bar along the top (the strip or a phone's top bar). */
const RAIL = (vp: Viewport): Rect => ({ x: 0, y: 0, w: 96, h: vp.h });
const STRIP = (vp: Viewport, h: number, y = 0): Rect => ({
  x: vp.w > 760 ? 96 : 0,
  y,
  w: vp.w > 760 ? vp.w - 96 : vp.w,
  h,
});
const origin = (vp: Viewport) =>
  buildScene(world(), vp, SETTLED).nodes.find((n) => n.kind === "origin")?.p ?? [0, 0, 0];

describe("[WLD-04][UI-04] the world's layout never says more than the evidence", () => {
  it("stands every destination at one depth and height, in title order from left to right", () => {
    const scene = buildScene(world(), DESKTOP, SETTLED);
    const destinations = scene.nodes.filter((n) => n.kind === "destination");
    expect(destinations.map((n) => n.id)).toEqual([
      "destination:a",
      "destination:d",
      "destination:s",
    ]);
    expect(new Set(destinations.map((n) => n.p[2]))).toEqual(new Set([HORIZON_Z]));
    expect(new Set(destinations.map((n) => n.p[1])).size).toBe(1);
    const xs = destinations.map((n) => n.p[0]);
    expect(xs).toEqual([...xs].sort((a, b) => a - b));
  });

  it("draws the ground between the person and each destination as shadow: not known yet", () => {
    const scene = buildScene(world(), DESKTOP, SETTLED);
    // Nothing else: no trail is drawn whose meaning nothing computed.
    expect(scene.trails.map((t) => [t.id, t.state])).toEqual([
      ["shadow:a", "shadow"],
      ["shadow:d", "shadow"],
      ["shadow:s", "shadow"],
    ]);
  });

  it("joins a skill to a destination only where the two are known to share it", () => {
    const scene = buildScene(
      world({
        skills: [
          { id: "k1", label: "Check data quality", state: "usual" },
          { id: "k2", label: "Write reports", state: "said" },
        ],
        destinations: [
          { id: "a", title: "Archivist", shared: [] },
          { id: "s", title: "Statistician", shared: ["k1", "k2"] },
        ],
      }),
      DESKTOP,
      SETTLED,
    );
    const reach = scene.trails.filter((t) => t.id.startsWith("reach:"));
    expect(reach.map((t) => [t.id, t.state])).toEqual([
      ["reach:s:k1", "usual"],
      ["reach:s:k2", "said"],
    ]);
  });

  it("lights the person's light only when they have answered", () => {
    const origin = (lit: boolean) =>
      buildScene(world({ lit }), DESKTOP, SETTLED).nodes.find((n) => n.kind === "origin");
    expect(origin(false)?.state).toBe("usual");
    expect(origin(true)?.state).toBe("said");
  });

  it("draws what was there on arrival settled, and grows only what appears now", () => {
    const appeared = new Map([["destination:s", 100]]);
    const scene = buildScene(world(), DESKTOP, { ignite: -1e6, appeared });
    const birth = (id: string) => scene.nodes.find((n) => n.id === id)?.birth ?? 0;
    expect(birth("destination:a")).toBeLessThan(0);
    expect(birth("destination:s")).toBeGreaterThan(100);
  });
});

describe("[WLD-01][WLD-07][UI-09] each chapter is a place the view travels to", () => {
  it.each([DESKTOP, TABLET, PHONE])(
    "keeps the person's light in view at every place (%o)",
    (vp) => {
      const origin = buildScene(world(), vp, SETTLED).nodes.find((n) => n.kind === "origin");
      for (const chapter of CHAPTERS) {
        const p = project(origin?.p ?? [0, 0, 0], placeView(chapter.id, vp));
        expect(p.visible, chapter.id).toBe(true);
        expect(p.x, chapter.id).toBeGreaterThan(0);
        expect(p.x, chapter.id).toBeLessThan(vp.w);
        expect(p.y, chapter.id).toBeGreaterThan(0);
        expect(p.y, chapter.id).toBeLessThan(vp.h);
      }
    },
  );

  it.each([DESKTOP, TABLET, PHONE])(
    "shows every destination on the horizon at Roles (%o)",
    (vp) => {
      const scene = buildScene(world(), vp, SETTLED);
      const view = placeView("roles", vp);
      for (const node of scene.nodes.filter((n) => n.kind === "destination")) {
        const p = project(node.p, view);
        expect(p.x, node.id).toBeGreaterThan(0);
        expect(p.x, node.id).toBeLessThan(vp.w);
      }
    },
  );

  it("centres the place in the part of the world the chapter's panel leaves clear", () => {
    // The You panel spans x 128–1160 at 1440 wide: the person's light stands in what is left.
    const clear = clearArea(
      DESKTOP,
      [RAIL(DESKTOP), STRIP(DESKTOP, 65)],
      [{ x: 128, y: 89, w: 1032, h: 780 }],
    );
    expect(clear).toEqual({ left: 1160, right: 1440, top: 65, bottom: 900 });
    const p = project(origin(DESKTOP), placeView("you", DESKTOP, clear));
    expect(p.x).toBe(1300);
  });

  it("keeps a place where it rests when the panel beside it leaves it clear", () => {
    // Roles' short card, low on the left: the horizon and the person stand where they rest.
    const clear = clearArea(
      DESKTOP,
      [RAIL(DESKTOP), STRIP(DESKTOP, 65)],
      [{ x: 128, y: 545, w: 520, h: 323 }],
    );
    expect(placeView("roles", DESKTOP, clear)).toEqual(placeView("roles", DESKTOP));
  });

  it.each([
    ["tablet", TABLET, [RAIL(TABLET), STRIP(TABLET, 186)], { x: 128, y: 700, w: 520, h: 292 }],
    ["phone", PHONE, [STRIP(PHONE, 65, 0), STRIP(PHONE, 57, 65)], { x: 0, y: 500, w: 390, h: 344 }],
  ] as const)("on a %s, stands the place above the short sheet, in view", (_, vp, bars, card) => {
    const clear = clearArea(vp, bars, [card]);
    expect(clear).toBeDefined();
    const view = placeView("roles", vp, clear);
    const scene = buildScene(world(), vp, SETTLED);
    const top = bars
      .filter((bar) => bar.h < vp.h / 2)
      .reduce((y, bar) => Math.max(y, bar.y + bar.h), 0);
    for (const node of scene.nodes) {
      const p = project(node.p, view);
      expect(p.y, node.id).toBeGreaterThan(top);
      expect(p.y, node.id).toBeLessThan(card.y);
      expect(p.x, node.id).toBeGreaterThan(0);
      expect(p.x, node.id).toBeLessThan(vp.w);
    }
  });

  it.each([
    ["tablet", TABLET, [RAIL(TABLET), STRIP(TABLET, 106)]],
    ["phone", PHONE, [STRIP(PHONE, 65, 0), STRIP(PHONE, 57, 65)]],
  ] as const)(
    "on a %s, stands the person and the targets in the slim band above the You console (F7)",
    (_, vp, bars) => {
      // The console starts 144 px below the bars (globals.css): the world takes no more room
      // than what it shows, and the person's light is still in view above the console.
      const top = bars
        .filter((bar) => bar.h < vp.h / 2)
        .reduce((y, bar) => Math.max(y, bar.y + bar.h), 0);
      const panel = {
        x: vp === PHONE ? 0 : 128,
        y: top + 144,
        w: vp === PHONE ? 390 : 600,
        h: 900,
      };
      const clear = clearArea(vp, bars, [panel]);
      expect(clear?.backdrop).toBeUndefined();
      const view = placeView("you", vp, clear);
      const scene = buildScene(world(), vp, SETTLED);
      for (const node of scene.nodes) {
        const p = project(node.p, view);
        expect(p.y, node.id).toBeGreaterThan(top);
        expect(p.y, node.id).toBeLessThan(panel.y);
      }
    },
  );

  it("leaves the world as a backdrop where the panels leave no room to stand", () => {
    // A phone's You chapter fills the screen below the header.
    const clear = clearArea(PHONE, [STRIP(PHONE, 122, 0)], [{ x: 0, y: 134, w: 390, h: 710 }]);
    expect(clear?.backdrop).toBe(true);
    expect(placeView("you", PHONE, clear)).toEqual(placeView("you", PHONE));
  });

  it("stands the backdrop behind the panels, so nothing peeks out beside them unnamed", () => {
    // Task W2C: a tablet's You console, taller than the window, left of centre beside the rail.
    const panel = { x: 128, y: 130, w: 560, h: 1200 };
    const clear = clearArea(TABLET, [RAIL(TABLET), STRIP(TABLET, 106)], [panel]);
    expect(clear?.backdrop).toBe(true);
    const view = placeView("you", TABLET, clear);
    expect(view.centre).toBe(panel.x + panel.w / 2);
    const skills = ["records", "deadlines", "spreadsheets", "errors", "findings"].map((id) => ({
      id,
      label: id,
      state: "usual" as const,
    }));
    const scene = buildScene(world({ skills }), TABLET, SETTLED);
    for (const node of scene.nodes) {
      const p = project(node.p, view);
      if (p.y > panel.y) {
        expect(p.x, node.id).toBeGreaterThan(panel.x);
        expect(p.x, node.id).toBeLessThan(panel.x + panel.w);
      }
    }
  });

  it("gives every place its own view", () => {
    const views = CHAPTERS.map((chapter) => JSON.stringify(placeView(chapter.id, DESKTOP)));
    expect(new Set(views).size).toBe(CHAPTERS.length);
  });

  it("travels between places within the travel time, and cuts when the world is still", () => {
    const you = placeView("you", DESKTOP);
    const roles = placeView("roles", DESKTOP);
    const tween = new ViewTween(you, MOTION.travel);
    tween.aim(roles, 10, false);
    expect(tween.moving(10.3)).toBe(true);
    expect(tween.current(10.3)).not.toEqual(roles);
    // Arrived as soon as the travel time is up (a millisecond after, past float rounding).
    expect(tween.current(10 + MOTION.travel + 0.001)).toEqual(roles);
    expect(tween.moving(10 + MOTION.travel + 0.001)).toBe(false);

    tween.aim(you, 20, true);
    expect(tween.current(20)).toEqual(you);
    expect(tween.moving(20)).toBe(false);
  });
});
