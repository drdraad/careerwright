// Every light's name sits beside its own light, inside the window, clear of the panels over the
// world, of every other name and of every other light; a light out of view or under a panel has
// no name in sight, and a name with no spot left is hidden from sight, never moved away from its
// light (spike lessons carried into Sprint W; the W2A review's names at tablet and phone).
import { describe, expect, it } from "vitest";
import { type Box, type LabelRequest, LEADER_FROM, layoutLabels } from "./labels";

const vp = { w: 1440, h: 900 };
const size = { w: 120, h: 24 };
const at = (x: number, y: number) => ({ x, y, scale: 1, visible: true });

const overlaps = (a: Box, b: Box) =>
  a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
/** Still over its own light: the light's x is inside the name's span. */
const over = (box: Box | null | undefined, x: number) =>
  box != null && box.x <= x && x <= box.x + box.w;

describe("[UI-07] the world's words are placed beside their lights", () => {
  it("puts a name above or below its own light, centred on it", () => {
    const spots = layoutLabels(
      [
        { id: "a", at: at(700, 400), size, side: "above" },
        { id: "b", at: at(300, 600), size, side: "below" },
      ],
      [],
      vp,
    );
    expect(spots.get("a")).toEqual({ x: 640, y: 400 - 14 - 24, w: 120, h: 24 });
    expect(spots.get("b")).toEqual({ x: 240, y: 600 + 14, w: 120, h: 24 });
  });

  it("never lets two names overlap: a crowded one slides along its row, steps out a row where its line stays clear, or takes the other side, still over its light", () => {
    const lights = [
      ["first", 700, 400],
      ["slides", 800, 400],
      ["steps", 770, 380],
      ["beside", 705, 401],
    ] as const;
    const spots = layoutLabels(
      lights.map(([id, x, y]) => ({ id, at: at(x, y), size, side: "above" as const })),
      [],
      vp,
    );
    const shown = [...spots.values()].filter((box): box is Box => box !== null);
    expect(shown).toHaveLength(lights.length);
    for (const [i, box] of shown.entries()) {
      for (const other of shown.slice(i + 1)) expect(overlaps(box, other)).toBe(false);
    }
    for (const [id, x] of lights) expect(over(spots.get(id), x), id).toBe(true);
    // The first is centred on its light; the next slides along the same row; the third steps
    // out a row, its line passing between the two names below it; the last, whose line up
    // would cross the first name, takes the other side.
    expect(spots.get("first")).toMatchObject({ x: 640, y: 400 - 14 - 24 });
    expect(spots.get("slides")).toMatchObject({ x: 800 - 16, y: 400 - 14 - 24 });
    expect(spots.get("steps")).toMatchObject({ x: 710, y: 380 - 14 - 30 - 24 });
    expect(spots.get("beside")).toMatchObject({ x: 645, y: 401 + 14 });
  });

  it("keeps names clear of panels over the world and inside the window, sliding in from an edge", () => {
    const panel: Box = { x: 600, y: 300, w: 400, h: 90 };
    const spots = layoutLabels(
      [
        { id: "under-panel", at: at(700, 400), size, side: "above" },
        { id: "off-edge", at: at(1430, 450), size, side: "above" },
        { id: "behind", at: { x: 0, y: 0, scale: 0, visible: false }, size, side: "above" },
      ],
      [panel],
      vp,
    );
    const moved = spots.get("under-panel");
    expect(moved).not.toBeNull();
    expect(moved && overlaps(moved, panel)).toBe(false);
    expect(moved?.y).toBeGreaterThan(400);
    const edge = spots.get("off-edge");
    expect(edge && edge.x + edge.w).toBeLessThanOrEqual(vp.w - 8);
    expect(over(edge, 1430)).toBe(true);
    expect(spots.get("behind")).toBeNull();
  });

  it("hides the name of a light that a panel covers: no name for a light the person cannot see", () => {
    const sheet: Box = { x: 0, y: 500, w: 390, h: 344 };
    const spots = layoutLabels(
      [
        { id: "under-sheet", at: at(195, 600), size, side: "above" },
        { id: "above-sheet", at: at(195, 300), size, side: "above" },
      ],
      [sheet],
      { w: 390, h: 844 },
    );
    expect(spots.get("under-sheet")).toBeNull();
    expect(spots.get("above-sheet")).not.toBeNull();
  });

  // W2A re-review, Minor 1: a line that crosses another light or name could join a name to the
  // wrong light.
  it.each([
    [
      "a name below the light it would cross",
      [
        { id: "first", at: at(690, 420), size, side: "above" },
        { id: "second", at: at(700, 425), size, side: "above" },
      ],
    ],
    [
      "a light between a name and its own",
      [
        { id: "a", at: at(700, 300), size, side: "below" },
        { id: "b", at: at(700, 340), size, side: "above" },
      ],
    ],
  ] as const)("never draws a line from a name across another light or name (%s)", (_, requests) => {
    const spots = layoutLabels(requests as readonly LabelRequest[], [], vp);
    for (const { id, at: light } of requests) {
      const spot = spots.get(id);
      expect(spot, id).toBeTruthy();
      if (!spot) continue;
      const above = spot.y + spot.h <= light.y;
      const gap = above ? light.y - (spot.y + spot.h) : spot.y - light.y;
      if (gap <= LEADER_FROM) continue;
      const line: Box = { x: light.x, y: above ? spot.y + spot.h : light.y, w: 1, h: gap };
      for (const other of requests.filter((r) => r.id !== id)) {
        const centre = { x: other.at.x - 4, y: other.at.y - 4, w: 8, h: 8 };
        expect(overlaps(line, centre), `${id}'s line crosses ${other.id}'s light`).toBe(false);
        const name = spots.get(other.id);
        if (name)
          expect(overlaps(line, name), `${id}'s line crosses ${other.id}'s name`).toBe(false);
      }
    }
  });

  it("never covers another light's centre, or the key", () => {
    const key: Box = { x: 600, y: 330, w: 200, h: 40 };
    const spots = layoutLabels(
      [
        { id: "a", at: at(700, 400), size, side: "above" },
        { id: "b", at: at(700, 460), size, side: "above" },
      ],
      [],
      vp,
      [key],
    );
    const a = spots.get("a");
    const b = spots.get("b");
    expect(a).not.toBeNull();
    expect(b).not.toBeNull();
    expect(a && overlaps(a, key)).toBe(false);
    expect(b && overlaps(b, key)).toBe(false);
    // b's name does not sit over a's light at (700, 400).
    expect(b && b.x <= 700 && 700 <= b.x + b.w && b.y <= 400 && 400 <= b.y + b.h).toBe(false);
  });

  it("hides a name whose every line would cross the key or another light, rather than cross it", () => {
    const key: Box = { x: 600, y: 330, w: 200, h: 40 };
    const spots = layoutLabels(
      [
        { id: "boxed in", at: at(700, 400), size, side: "above" },
        { id: "below it", at: at(700, 440), size, side: "above" },
      ],
      [],
      vp,
      [key],
    );
    expect(spots.get("boxed in")).toBeNull();
    expect(spots.get("below it")).not.toBeNull();
  });
});
