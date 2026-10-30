// Every light's name sits beside its own light, inside the window, clear of the panels over the
// world and of every other name; a name with no such spot is hidden from sight, never moved
// away from its light (spike lessons carried into Sprint W).
import { describe, expect, it } from "vitest";
import { type Box, layoutLabels } from "./labels";

const vp = { w: 1440, h: 900 };
const size = { w: 120, h: 24 };
const at = (x: number, y: number) => ({ x, y, scale: 1, visible: true });

const overlaps = (a: Box, b: Box) =>
  a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

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
    const a = spots.get("a");
    const b = spots.get("b");
    expect(a).toEqual({ x: 640, y: 400 - 14 - 24, w: 120, h: 24 });
    expect(b).toEqual({ x: 240, y: 600 + 14, w: 120, h: 24 });
  });

  it("never lets two names overlap: a crowded one steps out a row, then to its other side, or hides", () => {
    const spots = layoutLabels(
      [
        { id: "first", at: at(700, 400), size, side: "above" },
        { id: "near", at: at(710, 402), size, side: "above" },
        { id: "nearer", at: at(705, 401), size, side: "above" },
        { id: "nearest", at: at(706, 401), size, side: "above" },
        { id: "crowded", at: at(704, 400), size, side: "above" },
      ],
      [],
      vp,
    );
    const shown = [...spots.values()].filter((box): box is Box => box !== null);
    for (const [i, box] of shown.entries()) {
      for (const other of shown.slice(i + 1)) expect(overlaps(box, other)).toBe(false);
    }
    // Every placed name stays centred on its own light.
    expect(spots.get("first")).toMatchObject({ x: 640, y: 400 - 14 - 24 });
    expect(spots.get("near")).toMatchObject({ x: 650, y: 402 - 14 - 24 - 6 - 24 });
    expect(spots.get("nearer")).toMatchObject({ x: 645, y: 401 + 14 });
    expect(spots.get("nearest")).toMatchObject({ x: 646, y: 401 + 14 + 24 + 6 });
    expect(spots.get("crowded")).toBeNull();
  });

  it("keeps names clear of panels over the world and inside the window", () => {
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
    expect(spots.get("off-edge")).toBeNull();
    expect(spots.get("behind")).toBeNull();
  });
});
