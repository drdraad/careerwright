// Where each light's words go: beside its own light (never moved away from it), inside the
// window, clear of the panels over the world and of every name already placed. Names are
// placed in priority order (the caller's order); one with no clear spot is hidden from sight.
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

const meets = (a: Box, b: Box, pad: number) =>
  a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;

export function layoutLabels(
  requests: readonly LabelRequest[],
  covers: readonly Box[],
  vp: { w: number; h: number },
): Map<string, Box | null> {
  const inside = (b: Box) =>
    b.x >= EDGE && b.y >= EDGE && b.x + b.w <= vp.w - EDGE && b.y + b.h <= vp.h - EDGE;
  const placed: Box[] = [];
  const spots = new Map<string, Box | null>();
  for (const { id, at, size, side } of requests) {
    const other = side === "above" ? "below" : "above";
    // Its own side first, then a row further out on that side, then the other side.
    const tries = [
      [side, 0],
      [side, 1],
      [other, 0],
      [other, 1],
    ] as const;
    const spot = at.visible
      ? tries
          .map(([s, row]) => {
            const out = GAP + row * (size.h + ROW);
            return {
              x: at.x - size.w / 2,
              y: s === "above" ? at.y - out - size.h : at.y + out,
              w: size.w,
              h: size.h,
            };
          })
          .find(
            (b) =>
              inside(b) &&
              !covers.some((c) => meets(b, c, 0)) &&
              !placed.some((o) => meets(b, o, APART)),
          )
      : undefined;
    if (spot !== undefined) placed.push(spot);
    spots.set(id, spot ?? null);
  }
  return spots;
}
