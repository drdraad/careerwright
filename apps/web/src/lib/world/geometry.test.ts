// Horizon's geometry keeps the truth rules (plan section 4; ADR 0014 decision 4): position is
// layout only, so every destination stands at one depth in title order; unknown ground is a
// shadow trail, never absent; and every place keeps the person's light in view.
import { describe, expect, it } from "vitest";
import { CHAPTERS } from "@/lib/chapters";
import {
  type Births,
  buildScene,
  HORIZON_Z,
  placeView,
  project,
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

describe("[UI-04] the world's layout never says more than the evidence", () => {
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

describe("[UI-09] each chapter is a place the view travels to", () => {
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
    // The You panel spans x 120–1160 at 1440 wide: the person's light stands in what is left.
    const clear = { left: 1160, right: 1440 };
    const origin = buildScene(world(), DESKTOP, SETTLED).nodes.find((n) => n.kind === "origin");
    const p = project(origin?.p ?? [0, 0, 0], placeView("you", DESKTOP, clear));
    expect(p.x).toBe(1300);
    // Too little room to stand in (a tablet's full-width panel): the usual view.
    expect(placeView("you", TABLET, { left: 700, right: 768 })).toEqual(placeView("you", TABLET));
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
