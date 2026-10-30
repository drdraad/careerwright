// Where each light's words go: beside its own light, inside the window, clear of the panels over
// the world, of every name already placed and of every other light. A name sits centred over its
// light, or slides along its row to stay inside the window (still over its light); a crowded one
// steps out a row at a time, then tries the other side. A light that is out of view or under a
// panel has no name in sight, and nor does one with no clear spot: its words stay in the list.
// The design references place names by the same rules (docs/design/compositions/world.js).
import type { Projected } from "./geometry";

export type Box = { x: number; y: number; w: number; h: number };

export type LabelRequest = {
  id: string;
  /** Where its light is on screen. */
  at: Projected;
  size: { w: number; h: number };
  /** The side it prefers; the other side is tried next. */
  side: "above" | "below";
};

/** Space between a light and its words, and the margin kept inside the window (CSS pixels). */
const GAP = 14;
const EDGE = 8;
/** Breathing room kept between two names, and between a name and the row beyond it. */
const APART = 4;
const ROW = 6;
/** How many rows out a name may step on each side, with a leader line back to its light. */
const ROWS = 8;
/** A light's centre, kept uncovered by every name but its own. */
const CENTRE = 4;
/** When a name slides along its row, it still reaches this far over its light. */
const OVER = 16;

const meets = (a: Box, b: Box, pad: number) =>
  a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;

const holds = (b: Box, p: { x: number; y: number }) =>
  p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h;

export function layoutLabels(
  requests: readonly LabelRequest[],
  covers: readonly Box[],
  vp: { w: number; h: number },
  /** Boxes names must also stay clear of, placed first (the key to the lights). */
  taken: readonly Box[] = [],
): Map<string, Box | null> {
  const window: Box = { x: 0, y: 0, w: vp.w, h: vp.h };
  const inside = (b: Box) =>
    b.x >= EDGE && b.y >= EDGE && b.x + b.w <= vp.w - EDGE && b.y + b.h <= vp.h - EDGE;
  const placed: Box[] = [...taken];
  const lights = requests
    .filter((r) => r.at.visible)
    .map((r) => ({
      id: r.id,
      box: { x: r.at.x - CENTRE, y: r.at.y - CENTRE, w: CENTRE * 2, h: CENTRE * 2 },
    }));
  const spots = new Map<string, Box | null>();
  for (const { id, at, size, side } of requests) {
    const seen = at.visible && holds(window, at) && !covers.some((c) => holds(c, at));
    if (!seen) {
      spots.set(id, null);
      continue;
    }
    const other = side === "above" ? "below" : "above";
    const across = (x: number) => Math.min(Math.max(x, EDGE), vp.w - EDGE - size.w);
    const tries: Box[] = [];
    for (const s of [side, other]) {
      for (let row = 0; row < ROWS; row++) {
        const out = GAP + row * (size.h + ROW);
        const y = s === "above" ? at.y - out - size.h : at.y + out;
        for (const x of [at.x - size.w / 2, at.x - size.w + OVER, at.x - OVER]) {
          tries.push({ x: across(x), y, w: size.w, h: size.h });
        }
      }
    }
    // The line from a light to its name never passes under a panel: a name never hops one.
    const leader = (b: Box): Box => {
      const top = Math.min(at.y, b.y + b.h);
      return { x: at.x, y: top, w: 1, h: Math.max(at.y, b.y) - top };
    };
    const spot = tries.find(
      (b) =>
        inside(b) &&
        !covers.some((c) => meets(b, c, 0) || meets(leader(b), c, 0)) &&
        !placed.some((o) => meets(b, o, APART)) &&
        !lights.some((l) => l.id !== id && meets(b, l.box, 0)),
    );
    if (spot !== undefined) placed.push(spot);
    spots.set(id, spot ?? null);
  }
  return spots;
}
